from __future__ import annotations

from typing import Optional

from app.api.hub_ui.helpers import (
    card_tone_class,
    class_icon,
    class_label,
    department_label,
    esc,
    format_num,
)
from app.config import settings
from app.investment.schemas import AgentIdentityCard
from app.mesh.departments import primary_department
from app.protocol.schemas import AgentManifest
from app.workers.registry import LIVE_WORKERS, LiveWorkerSpec


def _x402_price(spec: LiveWorkerSpec) -> float:
    if spec.service_id == "market-pulse":
        return settings.x402_market_pulse_price_usd
    if spec.service_id == "sentiment-radar":
        return settings.x402_sentiment_radar_price_usd
    return 0.05


def render_agent_card(
    card: AgentIdentityCard,
    index: int,
    manifest: Optional[AgentManifest],
    *,
    live_spec: Optional[LiveWorkerSpec] = None,
) -> str:
    """Sade, renkli ajan kartı — detaylar modalda."""
    p = card.profile
    h = card.health
    f = card.finance
    pool = card.pool
    agent_id = esc(p.agent_id)
    dept = primary_department(p.agent_id)
    dept_esc = esc(dept)
    dept_label = esc(department_label(dept))
    tone = card_tone_class(dept)
    variant = index % 4
    contract = esc(pool.contract_address or "")
    is_live = live_spec is not None

    live_badge = (
        '<span class="wc-live-pill"><span class="pulse-dot"></span> Canlı</span>'
        if is_live
        else ""
    )
    x402_btn = ""
    if live_spec:
        price = _x402_price(live_spec)
        x402_btn = (
            f'<button type="button" class="btn-x402 btn-x402-sm" '
            f'onclick="{live_spec.x402_js_handler}(\'{agent_id}\', this)">'
            f'Dene · ${price:.2f}</button>'
        )

    return f"""
<article class="worker-card {tone} wc-variant-{variant}{' is-live-worker' if is_live else ''}"
  style="--i:{index}"
  data-agent="{agent_id}"
  data-token="{esc(p.token_symbol)}"
  data-pool="{contract}"
  data-class="{esc(p.agent_class.value)}"
  data-department="{dept_esc}">
  <header class="wc-head-simple">
    <div class="wc-avatar class-{esc(p.agent_class.value)}">
      <span class="wc-icon">{class_icon(p.agent_class.value)}</span>
    </div>
    <div class="wc-title-simple">
      <h3>{esc(p.display_name)}</h3>
      <div class="wc-meta-row">
        <span class="tag dept-tag dept-{dept_esc}">{dept_label}</span>
        {live_badge}
      </div>
    </div>
    <div class="wc-apy-badge">%{f.estimated_apy:.0f} APY</div>
  </header>

  <p class="wc-mission-simple">{esc(p.mission)}</p>

  <div class="wc-stats-simple">
    <span>TVL <strong>${format_num(f.staking_pool_tvl_usd)}</strong></span>
    <span>Başarı <strong>{h.success_rate * 100:.0f}%</strong></span>
    <span class="wc-status-inline">
      <span class="status-dot standby"></span>
      <span class="status-label">Hazır</span>
    </span>
  </div>

  <div class="wc-stake wc-stake-simple">
    <div class="stake-input-wrap">
      <span class="currency">$</span>
      <input type="number" class="amount" placeholder="100" min="1" step="1" inputmode="decimal" />
    </div>
    <button type="button" class="btn-stake" onclick="stake('{agent_id}', this)">
      <span class="btn-text">Ortak Ol</span>
      <span class="btn-loader"></span>
    </button>
  </div>
  <div class="wc-actions-row">
    <button type="button" class="btn-claim-sm" onclick="claim('{agent_id}', this)">Ödül Al</button>
    <button type="button" class="btn-unstake-sm" onclick="unstake('{agent_id}', this)">Çek</button>
    {x402_btn}
    <button type="button" class="btn-detail-sm" onclick="openAgentDetail('{agent_id}')">Detay</button>
  </div>
</article>"""


def render_featured_worker_card(
    card: AgentIdentityCard,
    manifest: Optional[AgentManifest],
    spec: LiveWorkerSpec,
) -> str:
    return render_agent_card(card, 0, manifest, live_spec=spec)


def render_worker_card(
    card: AgentIdentityCard,
    index: int,
    manifest: Optional[AgentManifest],
    *,
    compact: bool = False,
) -> str:
    live_spec = LIVE_WORKERS.get(card.profile.agent_id)
    return render_agent_card(card, index, manifest, live_spec=live_spec)
