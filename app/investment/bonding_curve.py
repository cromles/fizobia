from __future__ import annotations

import math

from app.investment.schemas import BondingCurveParams


class BondingCurve:
    """
    Dinamik değerlenme — arz arttıkça token fiyatı yükselir.
    price(s) = base_price + slope * s
    """

    def __init__(self, params: BondingCurveParams | None = None) -> None:
        self.params = params or BondingCurveParams()

    def price_at_supply(self, supply: float) -> float:
        return self.params.base_price + self.params.slope * max(supply, 0.0)

    def mint_shares(self, current_supply: float, usdc_amount: float) -> tuple[float, float]:
        """USDC yatırımı karşılığında basılacak pay miktarı."""
        if usdc_amount <= 0:
            return 0.0, 0.0

        base = self.params.base_price
        slope = self.params.slope
        a = slope / 2.0
        b = base + slope * current_supply

        if a < 1e-12:
            shares = usdc_amount / b if b > 0 else 0.0
        else:
            discriminant = b * b + 2.0 * slope * usdc_amount
            shares = (-b + math.sqrt(max(discriminant, 0.0))) / slope

        avg_price = usdc_amount / shares if shares > 0 else self.price_at_supply(current_supply)
        return shares, avg_price

    def burn_value(self, current_supply: float, shares: float) -> float:
        """Pay yakımı karşılığında iade edilecek USDC."""
        if shares <= 0 or current_supply <= 0:
            return 0.0
        shares = min(shares, current_supply)
        base = self.params.base_price
        slope = self.params.slope
        supply_before = current_supply
        return base * shares + slope * (supply_before * shares - (shares**2) / 2.0)
