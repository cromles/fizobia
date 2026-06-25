from __future__ import annotations

import uuid
from typing import List, Optional

from app.adapters.schema_utils import can_bridge_schemas, data_satisfies_schema
from app.planning.decomposer import GoalDecomposer
from app.planning.factory import create_decomposer
from app.matching.factory import create_matcher
from app.matching.semantic_matcher import SemanticCapabilityMatcher
from app.protocol.schemas import AgentManifest, ExecutionPlan, TaskNode
from app.registry.agent_registry import AgentRegistry, RegisteredCapability


class PlanCompiler:
    MAX_CHAIN_LENGTH = 8
    MIN_CONNECTIVITY_SCORE = 0.2

    def __init__(
        self,
        matcher: Optional[SemanticCapabilityMatcher] = None,
        decomposer: Optional[GoalDecomposer] = None,
    ):
        self.matcher = matcher or create_matcher()
        self.decomposer = decomposer or create_decomposer()

    @staticmethod
    def _to_manifest(item: RegisteredCapability) -> AgentManifest:
        return AgentManifest(
            agent_id=item.agent_id,
            endpoint=item.endpoint,
            reliability_score=item.reliability_score,
            cost_per_token=item.cost_per_token,
            capabilities=[item.capability],
        )

    def _make_task(self, item: RegisteredCapability, input_data: dict) -> TaskNode:
        return TaskNode(
            task_id=f"task_{uuid.uuid4().hex[:12]}",
            agent_id=item.agent_id,
            endpoint=item.endpoint,
            capability_name=item.capability.name,
            input_data=input_data,
            input_schema=item.capability.input_schema,
            output_schema=item.capability.output_schema,
            depends_on=[],
        )

    async def _resolve_capability(
        self,
        need: str,
        capabilities: List[RegisteredCapability],
    ) -> tuple[RegisteredCapability, float] | None:
        async_match = getattr(self.matcher, "find_best_capability_async", None)
        if callable(async_match):
            return await async_match(need, capabilities)
        return self.matcher.find_best_capability(need, capabilities)

    async def _score_goal(
        self,
        user_goal: str,
        item: RegisteredCapability,
    ) -> float:
        manifest = self._to_manifest(item)
        async_score = getattr(self.matcher, "score_goal_to_capability_async", None)
        if callable(async_score):
            return await async_score(user_goal, item.capability, manifest)
        return self.matcher.score_goal_to_capability(
            user_goal, item.capability, manifest
        )

    async def _pick_start_capability(
        self,
        user_goal: str,
        initial_data: dict,
        capabilities: List[RegisteredCapability],
    ) -> Optional[RegisteredCapability]:
        ranked: List[tuple[float, RegisteredCapability]] = []
        for item in capabilities:
            goal_score = await self._score_goal(user_goal, item)
            if data_satisfies_schema(initial_data, item.capability.input_schema):
                ranked.append((goal_score + 0.25, item))
            elif goal_score > 0.35:
                ranked.append((goal_score, item))

        if not ranked:
            return None
        ranked.sort(key=lambda pair: pair[0], reverse=True)
        return ranked[0][1]

    async def _pick_next_capability(
        self,
        user_goal: str,
        current_output_schema: dict,
        capabilities: List[RegisteredCapability],
        used_names: set[str],
    ) -> Optional[RegisteredCapability]:
        best_score = 0.0
        best_item: Optional[RegisteredCapability] = None

        for item in capabilities:
            if item.capability.name in used_names:
                continue
            if not can_bridge_schemas(current_output_schema, item.capability.input_schema):
                continue

            goal_score = await self._score_goal(user_goal, item)
            connectivity = 1.0 if goal_score > 0 else self.MIN_CONNECTIVITY_SCORE
            total = (goal_score * 0.6 + connectivity * 0.4) * item.reliability_score
            if total > best_score:
                best_score = total
                best_item = item

        return best_item

    async def compile_plan(
        self,
        user_goal: str,
        initial_data: dict,
        registry: AgentRegistry,
    ) -> ExecutionPlan:
        capabilities = registry.list_capabilities()
        if not capabilities:
            return ExecutionPlan(plan_id=f"plan_{uuid.uuid4().hex[:12]}", graph=[])

        needs = await self.decomposer.extract_capability_needs(user_goal, capabilities)
        graph: List[TaskNode] = []
        used_names: set[str] = set()

        for need in needs:
            match = await self._resolve_capability(need, capabilities)
            if match is None:
                continue
            item, _ = match
            if item.capability.name in used_names:
                continue
            task = self._make_task(item, initial_data if not graph else {})
            if graph:
                task.depends_on.append(graph[-1].task_id)
            graph.append(task)
            used_names.add(item.capability.name)

        if not graph:
            starter = await self._pick_start_capability(user_goal, initial_data, capabilities)
            if starter is None:
                raise ValueError(
                    f"Kritik Hata: '{user_goal}' hedefi için uygun başlangıç ajanı bulunamadı!"
                )
            first = self._make_task(starter, initial_data)
            graph.append(first)
            used_names.add(starter.capability.name)

            current_schema = starter.capability.output_schema
            while len(graph) < self.MAX_CHAIN_LENGTH:
                nxt = await self._pick_next_capability(
                    user_goal, current_schema, capabilities, used_names
                )
                if nxt is None:
                    break
                task = self._make_task(nxt, {})
                task.depends_on.append(graph[-1].task_id)
                graph.append(task)
                used_names.add(nxt.capability.name)
                current_schema = nxt.capability.output_schema

        return ExecutionPlan(plan_id=f"plan_{uuid.uuid4().hex[:12]}", graph=graph)
