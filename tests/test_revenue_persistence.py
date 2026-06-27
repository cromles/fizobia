"""Gelir defteri kalıcılık testleri."""

from __future__ import annotations

import importlib
from pathlib import Path

import app.investment.factory as hub_factory
from app.investment.revenue import RevenueLedger
from app.investment.schemas import RevenueSource


def test_revenue_persists_across_reload(tmp_path: Path, monkeypatch):
    store = tmp_path / "revenue.jsonl"
    monkeypatch.setenv("OAM_HUB_REVENUE_STORE", str(store))

    import app.config as config_mod

    importlib.reload(config_mod)
    import app.investment.persistence as persistence_mod
    import app.investment.revenue as revenue_mod

    importlib.reload(persistence_mod)
    importlib.reload(revenue_mod)

    ledger = revenue_mod.RevenueLedger()
    ledger.record_external_revenue(
        "oam.analyst.market.local",
        "x402_test_1",
        0.05,
        source=RevenueSource.X402,
    )
    assert store.exists()

    ledger2 = revenue_mod.RevenueLedger()
    assert ledger2.external_revenue_total("oam.analyst.market.local") == 0.05
    assert ledger2.real_event_count("oam.analyst.market.local") == 1


def test_demo_events_excluded_from_real_totals(tmp_path: Path, monkeypatch):
    store = tmp_path / "revenue.jsonl"
    monkeypatch.setenv("OAM_HUB_REVENUE_STORE", str(store))

    import app.config as config_mod

    importlib.reload(config_mod)
    import app.investment.revenue as revenue_mod

    importlib.reload(revenue_mod)

    ledger = revenue_mod.RevenueLedger()
    ledger.record_task_revenue("oam.fetcher.web.local", "demo_0", 100.0)
    ledger.record_external_revenue("oam.fetcher.web.local", "x402_real", 0.10)

    assert ledger.total_revenue("oam.fetcher.web.local", real_only=True) == 0.10
    assert ledger.total_revenue("oam.fetcher.web.local", real_only=False) == 100.10
