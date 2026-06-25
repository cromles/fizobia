from __future__ import annotations

from app.investment.hub import InvestmentHub

_hub: InvestmentHub | None = None


def get_investment_hub() -> InvestmentHub:
    global _hub
    if _hub is None:
        _hub = InvestmentHub()
        _hub.seed_demo_liquidity()
        _hub.seed_demo_metrics()
    return _hub
