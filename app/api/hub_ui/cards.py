from __future__ import annotations

from typing import Optional

from app.api.hub_ui.helpers import (
    capabilities_list,
    class_icon,
    class_label,
    esc,
    format_num,
    risk_label,
)
from app.investment.schemas import AgentIdentityCard
from app.protocol.schemas import AgentManifest


def render_worker_card(
    card: AgentIdentityCard,
    index: int,
    manifest: Optional[AgentManifest],
) -> str:
    p = card.profile
    h = card.health
    f = card.finance
    pool = card.pool
    delay = 0.05 + index * 0.06
    agent_id = esc(p.agent_id)
    contract = esc(pool.contract_address or "")
    caps = capabilities_list(manifest)
    cost = manifest.cost_per_token if manifest else 0

    return f"""
<article class="worker-card" style="--i:{index};--delay:{delay}s"
  data-agent="{agent_id}"
  data-token="{esc(p.token_symbol)}"
  data-pool="{contract}"
  data-class="{esc(p.agent_class.value)}">
  <div class="wc-shine"></div>
  <div class="wc-orbit"></div>

  <header class="wc-head">
    <div class="wc-avatar class-{esc(p.agent_class.value)}">
      <span class="wc-icon">{class_icon(p.agent_class.value)}</span>
      <span class="wc-pulse"></span>
    </div>
    <div class="wc-title">
      <h3>{esc(p.display_name)}</h3>
      <div class="wc-tags">
        <span class="tag class">{class_label(p.agent_class.value)}</span>
        <span class="tag risk-{esc(p.risk_level)}">{risk_label(p.risk_level)} risk</span>
      </div>
    </div>
    <div class="wc-status">
      <span class="status-dot standby"></span>
      <span class="status-label">Bağlanıyor</span>
    </div>
  </header>

  <p class="wc-mission">{esc(p.mission)}</p>

  <div class="wc-metrics">
    <div class="wc-metric highlight">
      <span class="wc-m-label">APY</span>
      <span class="wc-m-value apy" data-apy="{f.estimated_apy:.2f}">%{f.estimated_apy:.1f}</span>
    </div>
    <div class="wc-metric">
      <span class="wc-m-label">TVL</span>
      <span class="wc-m-value">${format_num(f.staking_pool_tvl_usd)}</span>
    </div>
    <div class="wc-metric">
      <span class="wc-m-label">24s</span>
      <span class="wc-m-value">${format_num(f.volume_24h_usd)}</span>
    </div>
    <div class="wc-metric">
      <span class="wc-m-label">Başarı</span>
      <span class="wc-m-value">{h.success_rate * 100:.0f}%</span>
    </div>
  </div>

  <div class="wc-task" data-live-task>
    <span class="task-pulse"></span>
    <span class="task-text">Görev bekleniyor…</span>
  </div>

  <div class="wc-stake">
    <div class="stake-input-wrap">
      <span class="currency">$</span>
      <input type="number" class="amount" placeholder="100" min="1" step="1" inputmode="decimal" />
      <span class="token-tag">{esc(p.token_symbol)}</span>
    </div>
    <div class="stake-actions">
      <button type="button" class="btn-stake" onclick="stake('{agent_id}', this)">
        <span class="btn-glow"></span>
        <span class="btn-text">Ortak Ol</span>
        <span class="btn-loader"></span>
      </button>
      <button type="button" class="btn-claim" onclick="claim('{agent_id}', this)">Ödül Al</button>
    </div>
  </div>

  <button type="button" class="wc-expand" onclick="toggleWorkerDetail(this)" aria-expanded="false">
    <span>Detaylar</span>
    <svg width="12" height="12" viewBox="0 0 12 12"><path d="M2 4l4 4 4-4" fill="none" stroke="currentColor" stroke-width="1.5"/></svg>
  </button>

  <div class="wc-detail" hidden>
    <p class="wc-desc">{esc(p.long_description or p.mission)}</p>
    <div class="wc-detail-grid">
      <div><span>Gelir</span><strong>${f.total_revenue_usd:,.2f}</strong></div>
      <div><span>Token</span><strong>${f.token_price_usdc:.4f}</strong></div>
      <div><span>Çağrı</span><strong>{format_num(h.total_calls)}</strong></div>
      <div><span>Gecikme</span><strong>{h.avg_latency_ms:.0f}ms</strong></div>
    </div>
    {f'<ul class="wc-caps">{caps}</ul>' if caps else ''}
    <p class="wc-thesis">{esc(p.investment_thesis or '')}</p>
    <p class="wc-covers"><em>Staking karşılar:</em> {esc(p.staking_covers)}</p>
    <code class="wc-contract" title="{contract}">{contract[:16]}…</code>
  </div>
</article>"""
