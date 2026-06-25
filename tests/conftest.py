"""Test ortamı — arka plan görevleri kapat (discovery sync, hub live loop)."""

from __future__ import annotations

import os

# app.config yüklenmeden önce
os.environ.setdefault("OAM_DISCOVERY_SYNC_INTERVAL", "0")
os.environ.setdefault("OAM_HUB_LIVE_INTERVAL", "0")
