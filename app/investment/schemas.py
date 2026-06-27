from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field


class RevenueSource(str, Enum):
    MESH_TASK = "mesh_task"
    X402 = "x402"
    EXTERNAL = "external"


class PartnershipMode(str, Enum):
    PASSIVE = "passive"
    OPERATOR = "operator"


class AgentClass(str, Enum):
    FETCHER = "fetcher"
    TRANSFORMER = "transformer"
    SYNTHESIZER = "synthesizer"
    ANALYST = "analyst"
    VALIDATOR = "validator"
    ORCHESTRATOR = "orchestrator"


class RevenueSplitConfig(BaseModel):
    """Gelir dağılımı — toplam %100."""

    staking_share: float = Field(default=0.65, ge=0.0, le=1.0, description="Staking ve altyapı havuzu")
    platform_share: float = Field(default=0.10, ge=0.0, le=1.0, description="Veridag platform payı")
    operator_share: float = Field(default=0.25, ge=0.0, le=1.0, description="Ajan operatörü")

    def validate_total(self) -> None:
        total = self.staking_share + self.platform_share + self.operator_share
        if abs(total - 1.0) > 1e-6:
            raise ValueError(f"Gelir payları toplamı %100 olmalı, mevcut: {total * 100:.2f}%")


class BondingCurveParams(BaseModel):
    base_price: float = Field(default=0.01, gt=0, description="İlk token fiyatı (USDC)")
    slope: float = Field(default=0.000001, ge=0, description="Arz arttıkça fiyat eğimi")


class AgentInvestmentProfile(BaseModel):
    agent_id: str
    display_name: str
    agent_class: AgentClass
    mission: str
    token_symbol: str
    contract_address: Optional[str] = None
    long_description: str = Field(
        default="",
        description="Yatırımcıya yönelik detaylı ajan açıklaması",
    )
    investment_thesis: str = Field(
        default="",
        description="Neden bu ajana yatırım yapılmalı",
    )
    use_cases: List[str] = Field(default_factory=list)
    staking_covers: str = Field(
        default="GPU/sunucu kirası, LLM API token maliyetleri ve ağ bant genişliği.",
    )
    risk_level: str = Field(default="orta", description="düşük | orta | yüksek")
    partnership_mode: PartnershipMode = Field(
        default=PartnershipMode.PASSIVE,
        description="passive = mesh sizin adınıza çalışır; operator = kendi agent'ınızı çalıştırırsınız",
    )


class AgentHealthMetrics(BaseModel):
    success_rate: float = Field(default=1.0, ge=0.0, le=1.0)
    avg_latency_ms: float = Field(default=0.0, ge=0.0)
    total_calls: int = Field(default=0, ge=0)
    successful_calls: int = Field(default=0, ge=0)


class FinancialReport(BaseModel):
    total_revenue_usd: float = Field(default=0.0, ge=0.0)
    volume_24h_usd: float = Field(default=0.0, ge=0.0)
    estimated_apy: float = Field(default=0.0, description="Yıllık tahmini getiri (%) — yalnızca gerçek 24s gelir")
    staking_pool_tvl_usd: float = Field(default=0.0, ge=0.0)
    token_price_usdc: float = Field(default=0.01, gt=0)
    apy_verified: bool = Field(default=False, description="Son 24s gerçek gelir + stake var")
    real_revenue_events: int = Field(default=0, ge=0)


class StakingPool(BaseModel):
    agent_id: str
    token_symbol: str
    total_staked_usdc: float = Field(default=0.0, ge=0.0)
    total_supply: float = Field(default=0.0, ge=0.0)
    reserve_usdc: float = Field(default=0.0, ge=0.0)
    rewards_accrued_usdc: float = Field(default=0.0, ge=0.0)
    curve: BondingCurveParams = Field(default_factory=BondingCurveParams)
    contract_address: Optional[str] = None


class StakePosition(BaseModel):
    investor_id: str = Field(..., description="Cüzdan adresi veya yatırımcı kimliği")
    agent_id: str
    shares: float = Field(default=0.0, ge=0.0)
    staked_usdc: float = Field(default=0.0, ge=0.0)
    rewards_claimed_usdc: float = Field(default=0.0, ge=0.0)
    rewards_pending_usdc: float = Field(default=0.0, ge=0.0)


class RevenueEvent(BaseModel):
    event_id: str
    agent_id: str
    task_id: str
    gross_usd: float
    staking_usd: float
    platform_usd: float
    operator_usd: float
    latency_ms: float
    success: bool
    created_at: datetime = Field(default_factory=datetime.utcnow)
    tx_hash: Optional[str] = None
    source: RevenueSource = Field(default=RevenueSource.MESH_TASK)
    payer: Optional[str] = Field(default=None, description="x402 ödeyen cüzdan")


class LedgerEntry(BaseModel):
    entry_id: str
    agent_id: str
    investor_id: Optional[str] = None
    action: str
    amount_usdc: float
    shares_delta: float = 0.0
    tx_hash: str
    created_at: datetime = Field(default_factory=datetime.utcnow)


class AgentIdentityCard(BaseModel):
    """The Hub yatırımcı paneli — ajan kimlik kartı."""

    profile: AgentInvestmentProfile
    health: AgentHealthMetrics
    finance: FinancialReport
    pool: StakingPool


class StakeRequest(BaseModel):
    investor_id: str
    agent_id: str
    amount_usdc: float = Field(..., gt=0)
    asset: str = Field(default="USDC", description="USDC | USDT | OAM")
    tx_hash: Optional[str] = Field(default=None, description="On-chain stake işlem hash'i")


class UnstakeRequest(BaseModel):
    investor_id: str
    agent_id: str
    shares: float = Field(..., gt=0)
    tx_hash: Optional[str] = Field(default=None, description="On-chain unstake işlem hash'i")


class ClaimRewardsRequest(BaseModel):
    investor_id: str
    agent_id: str
    tx_hash: Optional[str] = Field(default=None, description="On-chain claim işlem hash'i")


class PassiveStakeRequest(StakeRequest):
    """Pasif ortaklık — Olas'tan fark: agent'ı siz çalıştırmazsınız, mesh 7/24 çalışır."""

    partnership_mode: PartnershipMode = Field(default=PartnershipMode.PASSIVE)


class X402RevenueRequest(BaseModel):
    agent_id: str
    amount_usdc: float = Field(..., gt=0)
    payer: Optional[str] = None
    tx_hash: Optional[str] = None
    task_id: Optional[str] = None
    network: str = Field(default="x402")
    asset: str = Field(default="USDC")
    payment_protocol: str = Field(default="x402")
