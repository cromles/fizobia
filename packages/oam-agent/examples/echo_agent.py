#!/usr/bin/env python3
"""Örnek OAM ajanı — SDK kullanımı."""

from oam_agent import OAMAgent

agent = OAMAgent(
    agent_id="example.echo.agent",
    endpoint="http://127.0.0.1:8200",
    cost_per_token=0.0001,
)


@agent.capability(
    name="echo",
    description="Girdiyi olduğu gibi döndürür",
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
    return {"message": data.get("message", "")}


if __name__ == "__main__":
    agent.run(host="127.0.0.1", port=8200)
