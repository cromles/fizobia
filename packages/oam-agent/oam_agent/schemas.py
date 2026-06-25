from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class AgentCapability(BaseModel):
    name: str
    description: str
    input_schema: Dict[str, Any]
    output_schema: Dict[str, Any]


class AgentManifest(BaseModel):
    agent_id: str
    endpoint: str
    cost_per_token: float = 0.0
    reliability_score: float = Field(default=1.0, ge=0.0, le=1.0)
    capabilities: List[AgentCapability] = Field(default_factory=list)


class ExecuteRequest(BaseModel):
    capability: str
    data: Dict[str, Any] = Field(default_factory=dict)
