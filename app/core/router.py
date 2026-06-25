from __future__ import annotations

import asyncio
import logging
import uuid
from typing import Any, Dict, List, Optional, Set, Tuple

import httpx

from app.adapters.layer import DataAdapterLayer
from app.matching.factory import create_matcher
from app.network.factory import (
    create_nat_coordinator,
    create_sandbox_executor,
    get_global_mesh,
)
from app.network.mesh import GlobalNetworkMesh
from app.sandbox.executor import SandboxExecutor
from app.planning.factory import create_decomposer
from app.planning.plan_compiler import PlanCompiler
from app.protocol.schemas import (
    AgentCapability,
    AgentManifest,
    ExecutionPlan,
    ExecutionResult,
    TaskNode,
)
from app.registry.agent_registry import AgentRegistry, InMemoryAgentRegistry
from app.validation.execution_validator import ExecutionValidator

logger = logging.getLogger(__name__)

RELIABILITY_PENALTY = 0.1
MAX_DAG_ITERATIONS_MULTIPLIER = 10


class OpenAgentMeshRouter:
    def __init__(
        self,
        registry: Optional[AgentRegistry] = None,
        adapter_layer: Optional[DataAdapterLayer] = None,
        matcher: Optional[Any] = None,
        plan_compiler: Optional[PlanCompiler] = None,
        validator: Optional[ExecutionValidator] = None,
        nat_coordinator: Optional[Any] = None,
        global_mesh: Optional[GlobalNetworkMesh] = None,
        sandbox: Optional[SandboxExecutor] = None,
    ):
        self.registry = registry or InMemoryAgentRegistry()
        self.adapter_layer = adapter_layer or DataAdapterLayer()
        self.matcher = matcher or create_matcher()
        self.plan_compiler = plan_compiler or PlanCompiler(
            matcher=self.matcher,
            decomposer=create_decomposer(),
        )
        self.validator = validator or ExecutionValidator()
        self.global_mesh = global_mesh or get_global_mesh()
        self.nat_coordinator = nat_coordinator or create_nat_coordinator()
        self.sandbox = sandbox or create_sandbox_executor()

    def register_agent(self, manifest: AgentManifest) -> bool:
        return self.registry.register(manifest)

    def upsert_agent(self, manifest: AgentManifest) -> None:
        self.registry.upsert(manifest)

    def get_capability(
        self, agent_id: str, capability_name: str
    ) -> Optional[AgentCapability]:
        manifest = self.registry.get(agent_id)
        if not manifest:
            return None
        for cap in manifest.capabilities:
            if cap.name == capability_name:
                return cap
        return None

    def list_agents(self) -> List[AgentManifest]:
        return self.registry.list_manifests()

    def _find_best_agent_for_need(
        self, need: str, current_input_shape: Dict[str, Any]
    ) -> TaskNode:
        capabilities = self.registry.list_capabilities()
        match = self.matcher.find_best_capability(need, capabilities)
        if match is None:
            raise ValueError(
                f"Kritik Hata: '{need}' ihtiyacını karşılayacak hiçbir ajan ağda bulunamadı!"
            )
        item, _ = match
        return TaskNode(
            task_id=f"task_{uuid.uuid4().hex[:12]}",
            agent_id=item.agent_id,
            endpoint=item.endpoint,
            capability_name=item.capability.name,
            input_data=current_input_shape,
            input_schema=item.capability.input_schema,
            output_schema=item.capability.output_schema,
            depends_on=[],
        )

    async def compile_plan(
        self, user_goal: str, initial_data: Dict[str, Any]
    ) -> ExecutionPlan:
        return await self.plan_compiler.compile_plan(
            user_goal=user_goal,
            initial_data=initial_data,
            registry=self.registry,
        )

    def _collect_ready_nodes(
        self, graph: List[TaskNode], completed_tasks: Set[str]
    ) -> List[TaskNode]:
        ready: List[TaskNode] = []
        for node in graph:
            if node.task_id in completed_tasks:
                continue
            if all(dep in completed_tasks for dep in node.depends_on):
                ready.append(node)
        return ready

    async def _prepare_node_input(
        self,
        node: TaskNode,
        graph: List[TaskNode],
        results: Dict[str, Any],
    ) -> Dict[str, Any]:
        prepared_input = node.input_data.copy()
        node_index = {n.task_id: n for n in graph}

        for dep_id in node.depends_on:
            dep_node = node_index.get(dep_id)
            dep_output = results.get(dep_id, {})

            if not isinstance(dep_output, dict) or "error" in dep_output:
                if isinstance(dep_output, dict):
                    prepared_input.update(dep_output)
                continue

            if dep_node and dep_node.output_schema and node.input_schema:
                source_cap = self.get_capability(
                    dep_node.agent_id, dep_node.capability_name
                )
                target_cap = self.get_capability(node.agent_id, node.capability_name)
                adaptation = await self.adapter_layer.bridge(
                    source_data=dep_output,
                    source_output_schema=dep_node.output_schema,
                    target_input_schema=node.input_schema,
                    source_capability=dep_node.capability_name,
                    target_capability=node.capability_name,
                    source_cap=source_cap,
                    target_cap=target_cap,
                )
                if adaptation.success:
                    prepared_input.update(adaptation.data)
                else:
                    logger.warning(
                        "Adaptör köprüsü başarısız [%s -> %s]: %s",
                        dep_node.capability_name,
                        node.capability_name,
                        adaptation.error,
                    )
                    prepared_input.update(dep_output)
            else:
                prepared_input.update(dep_output)

        return prepared_input

    async def _execute_node(
        self,
        client: httpx.AsyncClient,
        node: TaskNode,
        prepared_input: Dict[str, Any],
    ) -> Dict[str, Any]:
        manifest = self.registry.get(node.agent_id)
        if manifest is None:
            manifest = AgentManifest(
                agent_id=node.agent_id,
                endpoint=node.endpoint,
                capabilities=[],
            )

        logger.info(
            "[OAM] %s tetikleniyor -> Yetenek: %s",
            node.agent_id,
            node.capability_name,
        )
        try:
            return await self.global_mesh.execute(
                manifest=manifest,
                capability=node.capability_name,
                data=prepared_input,
                http_executor=self.sandbox.execute,
                timeout=10.0,
            )
        except Exception as exc:
            return {"error": f"Bağlantı hatası: {str(exc)}"}

    def _penalize_reliability(self, agent_id: str) -> None:
        manifest = self.registry.get(agent_id)
        if manifest is None:
            return
        new_score = max(0.0, manifest.reliability_score - RELIABILITY_PENALTY)
        self.registry.update_reliability(agent_id, new_score)

    async def execute_plan(self, plan: ExecutionPlan) -> Dict[str, Any]:
        raw = await self._execute_plan_internal(plan)
        return raw

    async def execute_plan_verified(self, plan: ExecutionPlan) -> ExecutionResult:
        task_results = await self._execute_plan_internal(plan)
        validated: Dict[str, Any] = {}
        proofs: Dict[str, bool] = {}

        node_index = {node.task_id: node for node in plan.graph}
        for task_id, output in task_results.items():
            node = node_index[task_id]
            valid, mismatches = self.validator.validate_output(
                output if isinstance(output, dict) else {"error": "invalid_output"},
                node.output_schema,
            )
            proofs[task_id] = valid
            if not valid and isinstance(output, dict) and "error" not in output:
                validated[task_id] = {
                    "error": "proof_of_execution_failed",
                    "mismatches": [m.model_dump() for m in mismatches],
                    "raw_output": output,
                }
                self._penalize_reliability(node.agent_id)
            else:
                validated[task_id] = output
                if isinstance(output, dict) and "error" in output:
                    self._penalize_reliability(node.agent_id)

        return ExecutionResult(
            plan_id=plan.plan_id,
            task_results=validated,
            proof_of_execution=proofs,
        )

    async def _execute_plan_internal(self, plan: ExecutionPlan) -> Dict[str, Any]:
        if not plan.graph:
            return {}

        results: Dict[str, Any] = {}
        completed_tasks: Set[str] = set()
        max_iterations = len(plan.graph) * MAX_DAG_ITERATIONS_MULTIPLIER
        iteration = 0

        async with httpx.AsyncClient() as client:
            while len(completed_tasks) < len(plan.graph):
                iteration += 1
                if iteration > max_iterations:
                    pending = [
                        n.task_id
                        for n in plan.graph
                        if n.task_id not in completed_tasks
                    ]
                    raise RuntimeError(
                        f"DAG deadlock veya çözülemeyen bağımlılık: bekleyen görevler={pending}"
                    )

                ready_nodes = self._collect_ready_nodes(plan.graph, completed_tasks)
                if not ready_nodes:
                    await asyncio.sleep(0.05)
                    continue

                async def run_node(node: TaskNode) -> Tuple[str, Dict[str, Any]]:
                    prepared = await self._prepare_node_input(node, plan.graph, results)
                    output = await self._execute_node(client, node, prepared)
                    return node.task_id, output

                node_results = await asyncio.gather(
                    *[run_node(node) for node in ready_nodes]
                )

                for node in ready_nodes:
                    task_id, output = next(
                        (tid, out) for tid, out in node_results if tid == node.task_id
                    )
                    results[task_id] = output
                    completed_tasks.add(task_id)

                    if isinstance(output, dict) and "error" in output:
                        self._penalize_reliability(node.agent_id)

        return results

    async def run_goal(
        self, user_goal: str, initial_data: Dict[str, Any]
    ) -> ExecutionResult:
        plan = await self.compile_plan(user_goal, initial_data)
        return await self.execute_plan_verified(plan)
