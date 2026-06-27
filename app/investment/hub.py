from __future__ import annotations

import time
from typing import Dict, List, Optional

from app.investment.metrics import MetricsCollector, _RevenuePoint
from app.investment.revenue import RevenueLedger
from app.investment.schemas import (
    AgentClass,
    AgentHealthMetrics,
    AgentIdentityCard,
    AgentInvestmentProfile,
    FinancialReport,
    RevenueSource,
    RevenueSplitConfig,
    StakingPool,
)
from app.investment.seed import DEFAULT_PROFILES
from app.investment.staking import StakingPoolManager
from app.config import settings
from app.mesh.agent_catalog import agent_label
from app.mesh.qualified_agents import is_hub_qualified
from app.protocol.schemas import AgentManifest


class InvestmentHub:
    """
    The Hub — yatırımcı paneli ve token ekonomisi koordinatörü.
    %65 Staking | %10 Veridag | %25 Operatör
    """

    def __init__(
        self,
        split: RevenueSplitConfig | None = None,
    ) -> None:
        self.split = split or RevenueSplitConfig()
        self.metrics = MetricsCollector()
        self.revenue = RevenueLedger(self.split)
        self.pools = StakingPoolManager()
        self._profiles: Dict[str, AgentInvestmentProfile] = dict(DEFAULT_PROFILES)

    def register_profile(self, profile: AgentInvestmentProfile) -> None:
        self._profiles[profile.agent_id] = profile
        self.pools.ensure_pool(profile.agent_id, profile.token_symbol)

    def ensure_agent(self, manifest: AgentManifest) -> AgentInvestmentProfile:
        if manifest.agent_id in self._profiles:
            profile = self._profiles[manifest.agent_id]
            self.pools.ensure_pool(profile.agent_id, profile.token_symbol)
            return profile

        agent_class = _infer_class(manifest)
        token_symbol = _token_symbol(manifest.agent_id)
        profile = AgentInvestmentProfile(
            agent_id=manifest.agent_id,
            display_name=agent_label(manifest.agent_id),
            agent_class=agent_class,
            mission=_mission_from_manifest(manifest),
            token_symbol=token_symbol,
        )
        self.register_profile(profile)
        return profile

    def record_execution(
        self,
        manifest: AgentManifest,
        task_id: str,
        *,
        success: bool,
        latency_ms: float,
    ) -> None:
        profile = self.ensure_agent(manifest)
        gross = _estimate_task_revenue(manifest)

        if not success:
            gross *= 0.1

        event = self.revenue.record_task_revenue(
            agent_id=manifest.agent_id,
            task_id=task_id,
            gross_usd=gross,
            latency_ms=latency_ms,
            success=success,
        )
        self.metrics.record_execution(
            manifest.agent_id,
            success=success,
            latency_ms=latency_ms,
            revenue_usd=gross if success else 0.0,
        )
        if success and event.staking_usd > 0:
            self.pools.distribute_staking_rewards(manifest.agent_id, event.staking_usd)
            if settings.onchain_enabled:
                from app.investment.onchain import fund_pool_rewards

                try:
                    fund_pool_rewards(manifest.agent_id, event.staking_usd)
                except Exception:
                    pass

    def record_external_revenue(
        self,
        manifest: AgentManifest,
        task_id: str,
        gross_usd: float,
        *,
        source: RevenueSource = RevenueSource.X402,
        tx_hash: str | None = None,
        payer: str | None = None,
    ) -> None:
        """x402 veya harici ödeme kanalından gelen gerçek USDC geliri."""
        profile = self.ensure_agent(manifest)
        event = self.revenue.record_external_revenue(
            profile.agent_id,
            task_id,
            gross_usd,
            source=source,
            tx_hash=tx_hash,
            payer=payer,
        )
        self.metrics.record_execution(
            profile.agent_id,
            success=True,
            latency_ms=0.0,
            revenue_usd=gross_usd,
        )
        if event.staking_usd > 0:
            self.pools.distribute_staking_rewards(profile.agent_id, event.staking_usd)
            if settings.onchain_enabled:
                from app.investment.onchain import fund_pool_rewards

                try:
                    fund_pool_rewards(profile.agent_id, event.staking_usd)
                except Exception:
                    pass

    def build_identity_card(
        self,
        agent_id: str,
        reliability_score: float = 1.0,
    ) -> Optional[AgentIdentityCard]:
        profile = self._profiles.get(agent_id)
        pool = self.pools.get_pool(agent_id)
        if profile is None or pool is None:
            return None

        health = self.metrics.get_health(agent_id, reliability_score)
        total_revenue = self.revenue.total_revenue(agent_id, real_only=True)
        volume_24h = self.metrics.volume_24h(agent_id)
        token_price = self.pools.token_price(agent_id)
        staking_tvl = pool.total_staked_usdc

        daily_staking = self.revenue.staking_revenue_24h(agent_id, real_only=True)
        apy = 0.0
        apy_verified = False
        if staking_tvl > 0 and daily_staking > 0:
            apy = (daily_staking * 365 / staking_tvl) * 100
            apy_verified = True

        finance = FinancialReport(
            total_revenue_usd=round(total_revenue, 4),
            volume_24h_usd=round(volume_24h, 4),
            estimated_apy=round(min(apy, 999.0), 2) if apy_verified else 0.0,
            staking_pool_tvl_usd=round(staking_tvl, 4),
            token_price_usdc=round(token_price, 6),
            apy_verified=apy_verified,
            real_revenue_events=self.revenue.real_event_count(agent_id),
        )

        return AgentIdentityCard(
            profile=profile,
            health=health,
            finance=finance,
            pool=pool,
        )

    def list_identity_cards(
        self,
        manifests: List[AgentManifest],
        *,
        include_hidden: bool = False,
    ) -> List[AgentIdentityCard]:
        cards: List[AgentIdentityCard] = []
        for manifest in manifests:
            if not include_hidden and not is_hub_qualified(manifest.agent_id):
                continue
            self.ensure_agent(manifest)
            card = self.build_identity_card(manifest.agent_id, manifest.reliability_score)
            if card:
                cards.append(card)
        return cards

    def seed_demo_liquidity(self) -> None:
        """Demo yatırım verisi — panelde anlamlı APY/TVL göstermek için."""
        seeds = {
            "oam.fetcher.local": 1250.0,
            "oam.synthesizer.local": 890.0,
            "oam.transformer.local": 310.0,
            "example.echo.agent": 75.0,
        }
        for agent_id, amount in seeds.items():
            if agent_id in self._profiles:
                profile = self._profiles[agent_id]
                self.pools.ensure_pool(agent_id, profile.token_symbol)
                try:
                    self.pools.stake("demo_investor_0x7a3f", agent_id, amount)
                except ValueError:
                    pass

    def seed_demo_metrics(self) -> None:
        """Panelde gösterilecek örnek ağ metrikleri ve gelir geçmişi."""
        demos = [
            ("oam.fetcher.local", 1_200_000, 320.0, 2450.0, 85.0),
            ("oam.synthesizer.local", 450_000, 480.0, 980.0, 42.0),
            ("oam.transformer.local", 890_000, 180.0, 520.0, 28.0),
            ("example.echo.agent", 12_000, 45.0, 35.0, 5.0),
        ]
        for agent_id, calls, latency, total_rev, vol_24h in demos:
            if agent_id not in self._profiles:
                continue
            runtime = self.metrics._agents[agent_id]
            runtime.total_calls = calls
            runtime.successful_calls = int(calls * 0.994)
            runtime.total_latency_ms = calls * latency
            runtime.revenue_points = [
                _RevenuePoint(
                    amount_usd=vol_24h / max(calls // 1000, 1),
                    timestamp=time.time(),
                )
                for _ in range(min(calls // 1000, 100))
            ]
            for i in range(min(50, calls // 10000 or 1)):
                self.revenue.record_task_revenue(
                    agent_id=agent_id,
                    task_id=f"demo_{i}",
                    gross_usd=total_rev / max(calls // 100, 1),
                    latency_ms=latency,
                    success=True,
                )


def _infer_class(manifest: AgentManifest) -> AgentClass:
    caps = " ".join(c.name + " " + c.description for c in manifest.capabilities).lower()
    if "fetch" in caps or "çek" in caps or "tara" in caps:
        return AgentClass.FETCHER
    if "synth" in caps or "özet" in caps or "sentez" in caps:
        return AgentClass.SYNTHESIZER
    if "transform" in caps or "dönüştür" in caps:
        return AgentClass.TRANSFORMER
    if "analiz" in caps or "analyst" in caps:
        return AgentClass.ANALYST
    if "valid" in caps or "doğrula" in caps:
        return AgentClass.VALIDATOR
    return AgentClass.ORCHESTRATOR


def _token_symbol(agent_id: str) -> str:
    parts = agent_id.replace(".", "-").split("-")
    prefix = "".join(p[:3].upper() for p in parts if p)[:6]
    return f"{prefix}-TKN"


def _mission_from_manifest(manifest: AgentManifest) -> str:
    from app.mesh.agent_catalog import AGENT_MISSION

    if manifest.agent_id in AGENT_MISSION:
        return AGENT_MISSION[manifest.agent_id]
    if manifest.capabilities:
        return manifest.capabilities[0].description
    return f"{agent_label(manifest.agent_id)} — mesh görevleri."


def _estimate_task_revenue(manifest: AgentManifest) -> float:
    """cost_per_token = 1000 token başına USD → mikro görev tahmini."""
    base = manifest.cost_per_token / 1000.0
    return max(base, 0.0002)
