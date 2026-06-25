import pytest
from fastapi.testclient import TestClient

from oam_agent import OAMAgent


@pytest.fixture
def echo_agent() -> OAMAgent:
    agent = OAMAgent(
        agent_id="sdk.echo",
        endpoint="http://127.0.0.1:8200",
    )

    @agent.capability(
        name="echo",
        description="echo",
        input_schema={
            "type": "object",
            "properties": {"message": {"type": "string"}},
            "required": ["message"],
        },
        output_schema={
            "type": "object",
            "properties": {"message": {"type": "string"}},
            "required": ["message"],
        },
    )
    async def echo_handler(data: dict) -> dict:
        return {"message": data["message"]}

    return agent


def test_sdk_manifest_endpoint(echo_agent: OAMAgent):
    client = TestClient(echo_agent.app)
    response = client.get("/manifest")
    assert response.status_code == 200
    body = response.json()
    assert body["agent_id"] == "sdk.echo"
    assert body["capabilities"][0]["name"] == "echo"


def test_sdk_execute_endpoint(echo_agent: OAMAgent):
    client = TestClient(echo_agent.app)
    response = client.post(
        "/execute",
        json={"capability": "echo", "data": {"message": "oam"}},
    )
    assert response.status_code == 200
    assert response.json()["message"] == "oam"
