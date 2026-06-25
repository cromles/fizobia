from __future__ import annotations

from dataclasses import dataclass
from typing import Dict

from app.workers.market_pulse import AGENT_ID as MARKET_PULSE_ID, DISPLAY_NAME as MARKET_PULSE_NAME
from app.workers.sentiment_radar import AGENT_ID as SENTIMENT_RADAR_ID, DISPLAY_NAME as SENTIMENT_RADAR_NAME


@dataclass(frozen=True)
class LiveWorkerSpec:
    service_id: str
    agent_id: str
    display_name: str
    api_tag: str
    data_source: str
    x402_js_handler: str
    task_hint: str
    payment_hint: str
    analyze_path: str
    discover_path: str


LIVE_WORKERS: Dict[str, LiveWorkerSpec] = {
    MARKET_PULSE_ID: LiveWorkerSpec(
        service_id="market-pulse",
        agent_id=MARKET_PULSE_ID,
        display_name=MARKET_PULSE_NAME,
        api_tag="CoinGecko",
        data_source="coingecko",
        x402_js_handler="tryX402MarketPulse",
        task_hint="Piyasa verisi hazır — x402 ile dene",
        payment_hint="Ödeme → gerçek CoinGecko analizi → %65 havuza",
        analyze_path="/hub/x402/market-pulse/analyze",
        discover_path="/hub/x402/market-pulse",
    ),
    SENTIMENT_RADAR_ID: LiveWorkerSpec(
        service_id="sentiment-radar",
        agent_id=SENTIMENT_RADAR_ID,
        display_name=SENTIMENT_RADAR_NAME,
        api_tag="Fear & Greed + NLP",
        data_source="alternative.me+fng+lexicon",
        x402_js_handler="tryX402SentimentRadar",
        task_hint="Haber sentiment hazır — x402 ile dene",
        payment_hint="Ödeme → Fear&Greed + metin analizi → %65 havuza",
        analyze_path="/hub/x402/sentiment-radar/analyze",
        discover_path="/hub/x402/sentiment-radar",
    ),
}

LIVE_WORKER_IDS = frozenset(LIVE_WORKERS.keys())
