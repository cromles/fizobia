from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class AgentCapability(BaseModel):
    name: str = Field(..., description="Ajanın spesifik yetenek adı. Örn: 'pdf_text_extraction'")
    description: str = Field(..., description="Yetenek açıklaması. Semantik eşleşme için kritik.")
    input_schema: Dict[str, Any] = Field(..., description="Ajanın kabul ettiği JSON şeması.")
    output_schema: Dict[str, Any] = Field(..., description="Ajanın ürettiği çıktı JSON şeması.")


class AgentManifest(BaseModel):
    agent_id: str = Field(..., description="Evrensel benzersiz ajan kimliği (UUID veya Domain)")
    endpoint: str = Field(..., description="Ajanın canlı API adresi")
    cost_per_token: float = Field(default=0.0, description="1000 token başına maliyet (USD)")
    reliability_score: float = Field(
        default=1.0,
        ge=0.0,
        le=1.0,
        description="Ajanın başarı oranı",
    )
    capabilities: List[AgentCapability]


class TaskNode(BaseModel):
    task_id: str
    agent_id: str
    endpoint: str
    capability_name: str
    input_data: Dict[str, Any]
    input_schema: Dict[str, Any] = Field(default_factory=dict)
    output_schema: Dict[str, Any] = Field(default_factory=dict)
    depends_on: List[str] = Field(
        default_factory=list,
        description="Bu görevin çalışması için bitmesi gereken diğer task_id'ler",
    )


class ExecutionPlan(BaseModel):
    plan_id: str
    graph: List[TaskNode]


class MismatchKind(str, Enum):
    MISSING_REQUIRED_FIELD = "missing_required_field"
    TYPE_INCOMPATIBLE = "type_incompatible"
    STRUCTURAL = "structural"


class SchemaMismatch(BaseModel):
    field_path: str
    kind: MismatchKind
    expected: Optional[str] = None
    received: Optional[str] = None
    message: str


class AdaptationResult(BaseModel):
    success: bool
    data: Dict[str, Any] = Field(default_factory=dict)
    applied_mappings: Dict[str, str] = Field(default_factory=dict)
    mismatches: List[SchemaMismatch] = Field(default_factory=list)
    error: Optional[str] = None


class ExecutionResult(BaseModel):
    plan_id: str
    task_results: Dict[str, Any] = Field(default_factory=dict)
    proof_of_execution: Dict[str, bool] = Field(default_factory=dict)


class RegisterAgentRequest(BaseModel):
    manifest: AgentManifest


class CompilePlanRequest(BaseModel):
    user_goal: str
    initial_data: Dict[str, Any] = Field(default_factory=dict)


class ExecutePlanRequest(BaseModel):
    plan: ExecutionPlan


class RunGoalRequest(BaseModel):
    user_goal: str
    initial_data: Dict[str, Any] = Field(default_factory=dict)


class AnnounceRequest(BaseModel):
    manifest: AgentManifest
    ttl: int = Field(default=60, ge=10, le=3600)
