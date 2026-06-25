from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from app.protocol.schemas import AgentManifest


class SignalType(str, Enum):
    OFFER = "offer"
    ANSWER = "answer"
    ICE_CANDIDATE = "ice_candidate"
    PING = "ping"
    REGISTER = "register"


class SignalMessage(BaseModel):
    type: SignalType
    from_peer: str
    to_peer: str
    payload: Dict[str, Any] = Field(default_factory=dict)


class PeerNetworkRecord(BaseModel):
    """NAT arkasındaki ajanın hem lokal hem küresel erişim bilgisi."""

    agent_id: str
    manifest: AgentManifest
    local_endpoint: str
    public_endpoint: Optional[str] = None
    ice_candidates: List[str] = Field(default_factory=list)
    nat_type: str = Field(default="unknown", description="full_cone | symmetric | unknown")


class PublicAnnounceRequest(BaseModel):
    manifest: AgentManifest
    local_endpoint: str
    public_endpoint: Optional[str] = None
    ice_candidates: List[str] = Field(default_factory=list)
    nat_type: str = "unknown"
    ttl: int = Field(default=120, ge=10, le=3600)


class StunConfigResponse(BaseModel):
    stun_servers: List[str]
    signaling_url: str
    turn_servers: List[str] = Field(default_factory=list)
    protocol: str = "OAM-NAT-v2"
    tunnel_url: Optional[str] = None
    webrtc_available: bool = False
