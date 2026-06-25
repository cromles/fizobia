"""Gerçek dış API kullanan dijital işçiler."""

from app.workers.market_pulse import AGENT_ID as MARKET_PULSE_ID
from app.workers.registry import LIVE_WORKER_IDS, LIVE_WORKERS
from app.workers.sentiment_radar import AGENT_ID as SENTIMENT_RADAR_ID

__all__ = [
    "LIVE_WORKERS",
    "LIVE_WORKER_IDS",
    "MARKET_PULSE_ID",
    "SENTIMENT_RADAR_ID",
]
