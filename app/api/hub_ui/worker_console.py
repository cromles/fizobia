from __future__ import annotations

from app.mesh.agent_catalog import REVENUE_CORE_AGENT_IDS, agent_label
from app.mesh.worker_catalog import AGENT_TOKEN_META, WORKER_LIVE_ROUTES
from app.api.hub_ui.helpers import esc
from app.mesh.agent_catalog import AGENT_API_TAG, AGENT_MISSION


def render_worker_picker_items() -> str:
    parts: list[str] = []
    for index, agent_id in enumerate(REVENUE_CORE_AGENT_IDS):
        token = AGENT_TOKEN_META.get(agent_id, {})
        symbol = esc(str(token.get("symbol", "TKN")))
        supply = int(token.get("fixed_supply", 1_000_000))
        name = esc(agent_label(agent_id))
        api = esc(AGENT_API_TAG.get(agent_id, ""))
        mission = esc(AGENT_MISSION.get(agent_id, ""))
        active = " active" if index == 0 else ""
        parts.append(
            f"""
<button type="button" class="worker-pick-item{active}" data-agent="{esc(agent_id)}"
  data-route="{esc(WORKER_LIVE_ROUTES.get(agent_id, ''))}"
  data-output="{esc(str(token.get('output', '')))}"
  onclick="selectWorker('{esc(agent_id)}', this)">
  <span class="worker-pick-head">
    <strong>{name}</strong>
    <span class="worker-pick-token">{symbol}</span>
  </span>
  <span class="worker-pick-api">{api}</span>
  <span class="worker-pick-mission">{mission}</span>
  <span class="worker-pick-supply">Sabit arz: {supply:,} · gerçek veri</span>
</button>"""
        )
    return "".join(parts)
