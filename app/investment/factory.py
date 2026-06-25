from __future__ import annotations

from app.config import settings
from app.investment.hub import InvestmentHub

_hub: InvestmentHub | None = None


def get_investment_hub() -> InvestmentHub:
    global _hub
    if _hub is None:
        _hub = InvestmentHub()
        if settings.hub_demo_mode:
            _hub.seed_demo_liquidity()
            _hub.seed_demo_metrics()
        if settings.onchain_enabled:
            from app.investment.onchain import apply_pool_addresses

            apply_pool_addresses(_hub)
    return _hub
