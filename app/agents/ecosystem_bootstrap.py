"""Ekosistem bootstrap — kurucular + medya + sermaye ajanlarını mesh'e birleştirir."""

from __future__ import annotations

import logging

from app.agents.extended_builtins import EXTENDED_MANIFESTS
from app.agents.founder_bootstrap import bootstrap_founder_agents
from app.core.router import OpenAgentMeshRouter
from app.discovery.base import PeerDiscovery
from app.mesh.ecosystem_registry import ECOSYSTEM_GROWTH_IDS_SET, ECOSYSTEM_STACK_AGENT_IDS
from app.mesh.founders import FOUNDER_BOOTSTRAP_ORDER
from app.mesh.growth_protocol import get_growth_protocol
from app.mesh.organism import activate_ecosystem_divisions, broadcast_organism_manifest
from app.mesh.agent_dialogue import get_dialogue_bus
from app.mesh.founders import ORCHESTRATOR_ID
from app.mesh.hierarchy import FOUNDER_OPERATOR_ID

logger = logging.getLogger(__name__)


def _ecosystem_manifests():
    ids = set(ECOSYSTEM_STACK_AGENT_IDS)
    return [m for m in EXTENDED_MANIFESTS if m.agent_id in ids]


def bootstrap_ecosystem_agents(router: OpenAgentMeshRouter, discovery: PeerDiscovery) -> int:
    """Kurucu yığın + medya/sermaye bölümünü kaydet ve birleştir."""
    from app.investment.factory import get_investment_hub

    # Kurucu çekirdek + growth seed
    bootstrap_founder_agents(router, discovery)

    hub = get_investment_hub()
    growth = get_growth_protocol()
    joined = 0

    for manifest in EXTENDED_MANIFESTS:
        if manifest.agent_id not in ECOSYSTEM_GROWTH_IDS_SET:
            continue
        if manifest.agent_id in FOUNDER_BOOTSTRAP_ORDER:
            continue
        result = growth.join_agent(manifest)
        if result.get("accepted"):
            hub.ensure_agent(manifest)
            joined += 1
            logger.info("Ekosistem ajanı katıldı: %s", manifest.agent_id)

    activate_ecosystem_divisions()
    broadcast_organism_manifest(force=True)

    bus = get_dialogue_bus()
    bus.broadcast(
        FOUNDER_OPERATOR_ID,
        (
            f"Ekosistem birleşti — {len(ECOSYSTEM_STACK_AGENT_IDS)} ajan tek aile altında. "
            "Medya dalgası aktif; sermaye radarı açık. Kendi ekosistemimizi inşa ediyoruz."
        ),
        intent="ecosystem_assembled",
        thread_id="organism_wave",
    )
    bus.say(
        ORCHESTRATOR_ID,
        "oam.mesh.workers",
        "Tüm bölümler hazır — mesh proof ve ekosistem birleştirme pipeline'ları açık.",
        intent="ecosystem_ready",
        thread_id="organism_wave",
    )

    growth._emit(
        "ecosystem_assembled",
        f"Ekosistem birleşti — {len(ECOSYSTEM_STACK_AGENT_IDS)} ajan",
        agent_id=ORCHESTRATOR_ID,
        detail={
            "stack_agents": list(ECOSYSTEM_STACK_AGENT_IDS),
            "media_joined": joined,
        },
    )

    return len(_ecosystem_manifests())
