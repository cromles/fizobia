"""Homeostazi — organizma enerji dengesi ve hayatta kalma modları."""

from __future__ import annotations

import time
from typing import Any, Dict, List, Tuple

from app.mesh.cellular_taxonomy import (
    CELL_BRAIN,
    CELL_MUSCLE,
    CELL_SENSORY,
    PIPELINE_CELL_USAGE,
    SENSORY_AGENT_IDS,
)

MODE_NORMAL = "normal"
MODE_CONSERVE = "conserve"
MODE_HUNT = "hunt"
MODE_CRITICAL = "critical"

DEFAULT_ENERGY_USD = 25.0
HUNT_THRESHOLD = 0.30
CONSERVE_THRESHOLD = 0.50
CRITICAL_THRESHOLD = 0.10

_energy_usd: float = DEFAULT_ENERGY_USD
_peak_energy_usd: float = DEFAULT_ENERGY_USD
_hitl_required: bool = False
_last_mode: str = MODE_NORMAL
_directives: List[str] = []


def organism_energy() -> float:
    return round(_energy_usd, 6)


def energy_ratio() -> float:
    if _peak_energy_usd <= 0:
        return 0.0
    return max(0.0, min(1.0, _energy_usd / _peak_energy_usd))


def compute_mode() -> str:
    global _last_mode, _directives, _hitl_required
    ratio = energy_ratio()
    if ratio <= CRITICAL_THRESHOLD:
        _last_mode = MODE_CRITICAL
        _hitl_required = True
        _directives = [
            "Kritik enerji — tüm kas hücreleri durduruldu.",
            "Human-in-the-loop gerekli — sermaye veya gelir ekle.",
            "Yalnızca bağışıklık ve beyin dinleme modunda.",
        ]
    elif ratio <= HUNT_THRESHOLD:
        _last_mode = MODE_HUNT
        _hitl_required = False
        _directives = [
            "Enerji düşük — kas hücreleri yavaşlatıldı.",
            "Duyu hücreleri fırsat avı modunda — daha sık tarama.",
            "Beyin: düşük maliyetli mesh proof öncelikli.",
        ]
    elif ratio <= CONSERVE_THRESHOLD:
        _last_mode = MODE_CONSERVE
        _hitl_required = False
        _directives = [
            "Tasarruf modu — arena ve ağır üretim kısıtlı.",
            "Eylem hücreleri onay sonrası çalışır.",
        ]
    else:
        _last_mode = MODE_NORMAL
        _hitl_required = False
        _directives = [
            "Denge normal — tüm hücre tipleri çalışabilir.",
        ]
    return _last_mode


def credit_energy(amount_usd: float, *, reason: str = "revenue") -> float:
    global _energy_usd, _peak_energy_usd, _hitl_required
    if amount_usd <= 0:
        return _energy_usd
    _energy_usd += amount_usd
    _peak_energy_usd = max(_peak_energy_usd, _energy_usd)
    if _energy_usd > CRITICAL_THRESHOLD * _peak_energy_usd:
        _hitl_required = False
    compute_mode()
    return _energy_usd


def debit_energy(amount_usd: float, *, reason: str = "metabolism") -> float:
    global _energy_usd
    if amount_usd <= 0:
        return _energy_usd
    _energy_usd = max(0.0, _energy_usd - amount_usd)
    compute_mode()
    return _energy_usd


def sync_energy_from_revenue(total_revenue_usd: float) -> None:
    """Hub gelir verisinden organizma enerjisini güncelle (üst sınır korunur)."""
    global _energy_usd, _peak_energy_usd
    if total_revenue_usd <= 0:
        return
    target = DEFAULT_ENERGY_USD + total_revenue_usd * 0.65
    _energy_usd = max(_energy_usd, min(target, _peak_energy_usd))
    _peak_energy_usd = max(_peak_energy_usd, _energy_usd)
    compute_mode()


def check_pipeline_allowed(pipeline: str) -> Tuple[bool, str]:
    """Homeostazi kuralları — pipeline çalışabilir mi."""
    mode = compute_mode()
    cells = PIPELINE_CELL_USAGE.get(pipeline, (CELL_BRAIN, CELL_MUSCLE))

    if mode == MODE_CRITICAL:
        return False, "Organizma kritik enerji — Human-in-the-loop gerekli"

    if mode == MODE_HUNT and CELL_MUSCLE in cells:
        if pipeline in ("arena", "ecosystem_assembly"):
            return False, "Av modu — ağır kas pipeline'ları durduruldu; duyu+fırsat öncelikli"

    if mode == MODE_CONSERVE and pipeline == "arena":
        return False, "Tasarruf modu — arena kapalı"

    return True, "ok"


def cell_type_allowed(cell_type: str) -> bool:
    mode = compute_mode()
    if mode == MODE_CRITICAL:
        return cell_type in (CELL_BRAIN, CELL_SENSORY)
    if mode == MODE_HUNT and cell_type == CELL_MUSCLE:
        return False
    if mode == MODE_CONSERVE and cell_type == CELL_MUSCLE:
        return pipeline_muscle_light_only()
    return True


def pipeline_muscle_light_only() -> bool:
    return _last_mode == MODE_CONSERVE


def sensory_boost_interval_multiplier() -> float:
    """Düşük enerjide duyu hücreleri daha sık çalışsın."""
    mode = compute_mode()
    if mode == MODE_HUNT:
        return 0.5
    if mode == MODE_CONSERVE:
        return 0.75
    return 1.0


def get_homeostasis_status() -> Dict[str, Any]:
    mode = compute_mode()
    return {
        "mode": mode,
        "energy_usd": organism_energy(),
        "peak_energy_usd": round(_peak_energy_usd, 6),
        "energy_ratio": round(energy_ratio(), 4),
        "hitl_required": _hitl_required,
        "directives": list(_directives),
        "thresholds": {
            "hunt_below_ratio": HUNT_THRESHOLD,
            "conserve_below_ratio": CONSERVE_THRESHOLD,
            "critical_below_ratio": CRITICAL_THRESHOLD,
        },
        "sensory_agents_active": list(SENSORY_AGENT_IDS),
        "sensory_scan_multiplier": sensory_boost_interval_multiplier(),
        "updated_at": time.time(),
    }


def reset_homeostasis() -> None:
    global _energy_usd, _peak_energy_usd, _hitl_required, _last_mode, _directives
    _energy_usd = DEFAULT_ENERGY_USD
    _peak_energy_usd = DEFAULT_ENERGY_USD
    _hitl_required = False
    _last_mode = MODE_NORMAL
    _directives = []
