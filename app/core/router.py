from __future__ import annotations

import asyncio
import logging
import uuid
from typing import Any, Dict, List, Optional, Set, Tuple

import httpx

from app.adapters.layer import DataAdapterLayer
from app.protocol.schemas import AgentCapability, AgentManifest, ExecutionPlan, TaskNode

logger = logging.getLogger(__name__)

RELIABILITY_PENALTY = 0.1
MAX_DAG_ITERATIONS_MULTIPLIER = 10


class OpenAgentMeshRouter:
    def __init__(self, adapter_layer: Optional[DataAdapterLayer] = None):
        # Canlı sistemde bu hafıza Redis veya dağıtık bir DHT olacak
        self.registry: Dict[str, AgentManifest] = {}
        self.adapter_layer = adapter_layer or DataAdapterLayer()

    def register_agent(self, manifest: AgentManifest) -> bool:
        if manifest.agent_id in self.registry:
            return False
        self.registry[manifest.agent_id] = manifest
        return True

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

    def _find_best_agent_for_need(
        self, need: str, current_input_shape: Dict[str, Any]
    ) -> TaskNode:
        """
        Gelişmiş eşleşme katmanı: İhtiyaca en uygun ajanı ve onun girdi şemasını doğrular.
        """
        best: Optional[Tuple[float, TaskNode]] = None

        for agent_id, manifest in self.registry.items():
            for cap in manifest.capabilities:
                score = self._match_score(need, cap)
                if score <= 0:
                    continue

                candidate = TaskNode(
                    task_id=f"task_{uuid.uuid4().hex[:12]}",
                    agent_id=agent_id,
                    endpoint=manifest.endpoint,
                    capability_name=cap.name,
                    input_data=current_input_shape,
                    input_schema=cap.input_schema,
                    output_schema=cap.output_schema,
                    depends_on=[],
                )
                if best is None or score > best[0]:
                    best = (score, candidate)

        if best is None:
            raise ValueError(
                f"Kritik Hata: '{need}' ihtiyacını karşılayacak hiçbir ajan ağda bulunamadı!"
            )
        return best[1]

    @staticmethod
    def _match_score(need: str, capability: AgentCapability) -> float:
        need_lower = need.lower()
        if capability.name.lower() == need_lower:
            return 1.0
        if need_lower in capability.name.lower():
            return 0.8
        if need_lower in capability.description.lower():
            return 0.6
        return 0.0

    async def compile_plan(
        self, user_goal: str, initial_data: Dict[str, Any]
    ) -> ExecutionPlan:
        """
        Doğal dil hedefini analiz eder ve ajanların yetenek matrisine göre DAG oluşturur.
        """
        execution_graph: List[TaskNode] = []

        if "analiz" in user_goal.lower():
            step1 = self._find_best_agent_for_need("data_fetcher", initial_data)
            execution_graph.append(step1)

            step2 = self._find_best_agent_for_need("synthesizer", {})
            step2.depends_on.append(step1.task_id)
            execution_graph.append(step2)

        return ExecutionPlan(plan_id=f"plan_{uuid.uuid4().hex[:12]}", graph=execution_graph)

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
                prepared_input.update(dep_output if isinstance(dep_output, dict) else {})
                continue

            if dep_node and dep_node.output_schema and node.input_schema:
                adaptation = await self.adapter_layer.bridge(
                    source_data=dep_output,
                    source_output_schema=dep_node.output_schema,
                    target_input_schema=node.input_schema,
                    source_capability=dep_node.capability_name,
                    target_capability=node.capability_name,
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
        logger.info(
            "[OAM] %s tetikleniyor -> Yetenek: %s",
            node.agent_id,
            node.capability_name,
        )
        try:
            response = await client.post(
                f"{node.endpoint.rstrip('/')}/execute",
                json={"capability": node.capability_name, "data": prepared_input},
                timeout=10.0,
            )
            if response.status_code == 200:
                return response.json()
            return {"error": f"Agent HTTP {response.status_code}"}
        except Exception as exc:
            return {"error": f"Bağlantı hatası: {str(exc)}"}

    def _penalize_reliability(self, agent_id: str) -> None:
        manifest = self.registry.get(agent_id)
        if manifest is None:
            return
        manifest.reliability_score = max(
            0.0, manifest.reliability_score - RELIABILITY_PENALTY
        )

    async def execute_plan(self, plan: ExecutionPlan) -> Dict[str, Any]:
        """
        Oluşturulan görev ağacını (DAG) asenkron olarak ve bağımlılık sırasına göre yürütür.
        Hazır düğümler paralel tetiklenir; adaptör katmanı bağımlılık çıktılarını dönüştürür.
        """
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
