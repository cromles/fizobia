import pytest
from pydantic import ValidationError

from app.protocol.schemas import (
    AgentCapability,
    AgentManifest,
    ExecutionPlan,
    TaskNode,
)


def test_reliability_score_bounds():
    with pytest.raises(ValidationError):
        AgentManifest(
            agent_id="agent-1",
            endpoint="http://localhost:8000",
            reliability_score=1.5,
            capabilities=[],
        )


def test_task_node_defaults():
    node = TaskNode(
        task_id="t1",
        agent_id="a1",
        endpoint="http://localhost",
        capability_name="fetch",
        input_data={"query": "test"},
    )
    assert node.depends_on == []
    assert node.input_schema == {}


def test_execution_plan_roundtrip():
    plan = ExecutionPlan(
        plan_id="plan-1",
        graph=[
            TaskNode(
                task_id="t1",
                agent_id="a1",
                endpoint="http://localhost",
                capability_name="fetch",
                input_data={},
            )
        ],
    )
    restored = ExecutionPlan.model_validate(plan.model_dump())
    assert restored.plan_id == "plan-1"
    assert len(restored.graph) == 1
