from __future__ import annotations

import uuid
from typing import Dict, List, Optional, Tuple

from app.investment.bonding_curve import BondingCurve
from app.investment.schemas import (
    BondingCurveParams,
    LedgerEntry,
    StakePosition,
    StakingPool,
)


class StakingPoolManager:
    """Ajan likidite havuzları — stake, unstake, ödül dağıtımı."""

    def __init__(self) -> None:
        self._pools: Dict[str, StakingPool] = {}
        self._positions: Dict[Tuple[str, str], StakePosition] = {}
        self._ledger: List[LedgerEntry] = []

    def ensure_pool(
        self,
        agent_id: str,
        token_symbol: str,
        curve: BondingCurveParams | None = None,
    ) -> StakingPool:
        if agent_id not in self._pools:
            contract = f"0xpool{uuid.uuid4().hex[:40]}"
            self._pools[agent_id] = StakingPool(
                agent_id=agent_id,
                token_symbol=token_symbol,
                curve=curve or BondingCurveParams(),
                contract_address=contract,
            )
        return self._pools[agent_id]

    def get_pool(self, agent_id: str) -> Optional[StakingPool]:
        return self._pools.get(agent_id)

    def list_pools(self) -> List[StakingPool]:
        return list(self._pools.values())

    def token_price(self, agent_id: str) -> float:
        pool = self._pools.get(agent_id)
        if pool is None or pool.total_supply <= 0:
            return pool.curve.base_price if pool else 0.01
        curve = BondingCurve(pool.curve)
        return curve.price_at_supply(pool.total_supply)

    def stake(self, investor_id: str, agent_id: str, amount_usdc: float) -> StakePosition:
        pool = self._pools.get(agent_id)
        if pool is None:
            raise ValueError(f"Havuz bulunamadı: {agent_id}")

        curve = BondingCurve(pool.curve)
        shares, _ = curve.mint_shares(pool.total_supply, amount_usdc)

        pool.total_staked_usdc += amount_usdc
        pool.reserve_usdc += amount_usdc
        pool.total_supply += shares

        key = (investor_id, agent_id)
        position = self._positions.get(key)
        if position is None:
            position = StakePosition(investor_id=investor_id, agent_id=agent_id)
            self._positions[key] = position

        position.shares += shares
        position.staked_usdc += amount_usdc

        self._ledger.append(
            LedgerEntry(
                entry_id=uuid.uuid4().hex,
                agent_id=agent_id,
                investor_id=investor_id,
                action="stake",
                amount_usdc=amount_usdc,
                shares_delta=shares,
                tx_hash=f"0x{uuid.uuid4().hex}",
            )
        )
        return position

    def unstake(self, investor_id: str, agent_id: str, shares: float) -> float:
        pool = self._pools.get(agent_id)
        key = (investor_id, agent_id)
        position = self._positions.get(key)
        if pool is None or position is None:
            raise ValueError("Pozisyon bulunamadı")
        if shares > position.shares:
            raise ValueError("Yetersiz pay")

        curve = BondingCurve(pool.curve)
        usdc_out = curve.burn_value(pool.total_supply, shares)

        pool.total_supply -= shares
        pool.reserve_usdc = max(0.0, pool.reserve_usdc - usdc_out)
        pool.total_staked_usdc = max(0.0, pool.total_staked_usdc - usdc_out)
        position.shares -= shares
        position.staked_usdc = max(0.0, position.staked_usdc - usdc_out)

        self._ledger.append(
            LedgerEntry(
                entry_id=uuid.uuid4().hex,
                agent_id=agent_id,
                investor_id=investor_id,
                action="unstake",
                amount_usdc=usdc_out,
                shares_delta=-shares,
                tx_hash=f"0x{uuid.uuid4().hex}",
            )
        )
        return usdc_out

    def distribute_staking_rewards(self, agent_id: str, amount_usdc: float) -> None:
        """Staking havuzuna gelen %65 payı yatırımcılara oransal dağıt."""
        pool = self._pools.get(agent_id)
        if pool is None or amount_usdc <= 0 or pool.total_supply <= 0:
            return

        pool.rewards_accrued_usdc += amount_usdc
        for (investor_id, pos_agent_id), position in self._positions.items():
            if pos_agent_id != agent_id or position.shares <= 0:
                continue
            share_ratio = position.shares / pool.total_supply
            reward = amount_usdc * share_ratio
            position.rewards_pending_usdc += reward

    def claim_rewards(self, investor_id: str, agent_id: str) -> float:
        key = (investor_id, agent_id)
        position = self._positions.get(key)
        if position is None:
            return 0.0
        claimed = position.rewards_pending_usdc
        position.rewards_pending_usdc = 0.0
        position.rewards_claimed_usdc += claimed

        if claimed > 0:
            self._ledger.append(
                LedgerEntry(
                    entry_id=uuid.uuid4().hex,
                    agent_id=agent_id,
                    investor_id=investor_id,
                    action="claim_rewards",
                    amount_usdc=claimed,
                    tx_hash=f"0x{uuid.uuid4().hex}",
                )
            )
        return claimed

    def get_position(self, investor_id: str, agent_id: str) -> Optional[StakePosition]:
        return self._positions.get((investor_id, agent_id))

    def list_positions(self, investor_id: str) -> List[StakePosition]:
        return [p for (inv, _), p in self._positions.items() if inv == investor_id]

    def list_ledger(self, agent_id: str | None = None, limit: int = 50) -> List[LedgerEntry]:
        entries = self._ledger
        if agent_id:
            entries = [e for e in entries if e.agent_id == agent_id]
        return entries[-limit:]
