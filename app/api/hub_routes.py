from __future__ import annotations

from typing import Any, Dict, List

from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse

from app.core.router import OpenAgentMeshRouter
from app.investment.factory import get_investment_hub
from app.investment.schemas import (
    ClaimRewardsRequest,
    RevenueSplitConfig,
    StakeRequest,
    UnstakeRequest,
)
from app.protocol.schemas import AgentManifest

router = APIRouter(prefix="/hub", tags=["The Hub"])


def _mesh() -> OpenAgentMeshRouter:
    from app.api.main import router_mesh

    return router_mesh


@router.get("", response_class=HTMLResponse)
@router.get("/", response_class=HTMLResponse)
async def hub_dashboard() -> str:
    hub = get_investment_hub()
    mesh = _mesh()
    cards = hub.list_identity_cards(mesh.list_agents())
    split = hub.split

    card_html = ""
    for card in cards:
        p = card.profile
        h = card.health
        f = card.finance
        pool = card.pool
        success_pct = h.success_rate * 100
        calls_display = _format_number(h.total_calls)
        card_html += f"""
        <article class="agent-card" data-agent="{p.agent_id}">
          <header>
            <div class="agent-title">
              <h2>{p.display_name}</h2>
              <span class="badge class-{p.agent_class.value}">{_class_label(p.agent_class.value)}</span>
            </div>
            <span class="token">{p.token_symbol}</span>
          </header>
          <p class="mission">{p.mission}</p>
          <div class="metrics-grid">
            <div class="metric">
              <span class="label">Başarı Oranı</span>
              <span class="value green">%{success_pct:.1f}</span>
            </div>
            <div class="metric">
              <span class="label">Ort. Yanıt</span>
              <span class="value">{h.avg_latency_ms:.0f}ms</span>
            </div>
            <div class="metric">
              <span class="label">Toplam Çağrı</span>
              <span class="value">{calls_display}</span>
            </div>
            <div class="metric">
              <span class="label">Token Fiyatı</span>
              <span class="value">${f.token_price_usdc:.4f}</span>
            </div>
          </div>
          <div class="finance-panel">
            <h3>Canlı Finansal Rapor</h3>
            <div class="finance-row">
              <span>Toplam Ağ Getirisi</span><strong>${f.total_revenue_usd:,.2f}</strong>
            </div>
            <div class="finance-row">
              <span>Son 24s Hacim</span><strong>${f.volume_24h_usd:,.2f}</strong>
            </div>
            <div class="finance-row highlight">
              <span>Tahmini APY</span><strong class="apy">%{f.estimated_apy:.1f}</strong>
            </div>
            <div class="finance-row">
              <span>Havuz TVL</span><strong>${f.staking_pool_tvl_usd:,.2f}</strong>
            </div>
            <div class="contract">
              <span>Sözleşme:</span>
              <code>{pool.contract_address or '—'}</code>
            </div>
          </div>
          <div class="stake-panel">
            <input type="text" class="wallet" placeholder="Cüzdan adresi (0x...)" />
            <div class="stake-actions">
              <input type="number" class="amount" placeholder="USDC miktarı" min="1" step="1" />
              <button onclick="stake('{p.agent_id}', this)">Stake</button>
              <button class="secondary" onclick="claim('{p.agent_id}', this)">Ödül Al</button>
            </div>
            <p class="stake-hint">Kilitlediğiniz USDC karşılığında {p.token_symbol} alırsınız. Bonding curve ile fiyat dinamiktir.</p>
          </div>
        </article>"""

    return f"""<!DOCTYPE html>
<html lang="tr">
<head>
  <meta charset="utf-8"/>
  <title>The Hub — Veridag Yatırım Paneli</title>
  <style>
    :root {{
      --bg: #0a0f1a; --card: #111827; --border: #1f2937;
      --text: #e5e7eb; --muted: #9ca3af; --accent: #22d3ee;
      --green: #34d399; --gold: #fbbf24; --purple: #a78bfa;
    }}
    * {{ box-sizing: border-box; }}
    body {{ font-family: 'Segoe UI', system-ui, sans-serif; margin: 0; background: var(--bg); color: var(--text); }}
    .topbar {{ background: linear-gradient(135deg, #0f172a, #1e1b4b); padding: 1.5rem 2rem; border-bottom: 1px solid var(--border); }}
    .topbar h1 {{ margin: 0; font-size: 1.6rem; color: var(--accent); }}
    .topbar p {{ margin: 0.4rem 0 0; color: var(--muted); font-size: 0.95rem; }}
    .split-bar {{ display: flex; gap: 1rem; margin-top: 1rem; flex-wrap: wrap; }}
    .split-chip {{ background: #1e293b; padding: 0.4rem 0.8rem; border-radius: 6px; font-size: 0.85rem; }}
    .split-chip strong {{ color: var(--gold); }}
    .container {{ max-width: 1400px; margin: 0 auto; padding: 2rem; }}
    .grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(380px, 1fr)); gap: 1.5rem; }}
    .agent-card {{ background: var(--card); border: 1px solid var(--border); border-radius: 12px; padding: 1.25rem; }}
    .agent-card header {{ display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 0.75rem; }}
    .agent-title h2 {{ margin: 0; font-size: 1.15rem; }}
    .badge {{ display: inline-block; margin-top: 0.3rem; padding: 0.15rem 0.5rem; border-radius: 4px; font-size: 0.75rem; background: #312e81; color: #c4b5fd; }}
    .class-fetcher {{ background: #064e3b; color: #6ee7b7; }}
    .class-synthesizer {{ background: #78350f; color: #fcd34d; }}
    .class-transformer {{ background: #1e3a5f; color: #7dd3fc; }}
    .class-analyst {{ background: #4c1d95; color: #c4b5fd; }}
    .token {{ font-family: monospace; color: var(--gold); font-size: 0.9rem; }}
    .mission {{ color: var(--muted); font-size: 0.9rem; line-height: 1.5; min-height: 3rem; }}
    .metrics-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 0.6rem; margin: 1rem 0; }}
    .metric {{ background: #0f172a; padding: 0.6rem; border-radius: 8px; }}
    .metric .label {{ display: block; font-size: 0.75rem; color: var(--muted); }}
    .metric .value {{ font-size: 1.1rem; font-weight: 600; }}
    .green {{ color: var(--green); }}
    .finance-panel {{ background: #0f172a; border-radius: 8px; padding: 0.9rem; margin: 0.75rem 0; }}
    .finance-panel h3 {{ margin: 0 0 0.6rem; font-size: 0.85rem; color: var(--muted); text-transform: uppercase; letter-spacing: 0.05em; }}
    .finance-row {{ display: flex; justify-content: space-between; padding: 0.3rem 0; font-size: 0.9rem; }}
    .finance-row.highlight {{ border-top: 1px solid var(--border); margin-top: 0.4rem; padding-top: 0.6rem; }}
    .apy {{ color: var(--green); font-size: 1.2rem; }}
    .contract {{ margin-top: 0.5rem; font-size: 0.75rem; color: var(--muted); }}
    .contract code {{ color: #7dd3fc; word-break: break-all; }}
    .stake-panel {{ margin-top: 0.75rem; }}
    .wallet, .amount {{ width: 100%; padding: 0.5rem; margin-bottom: 0.5rem; border-radius: 6px; border: 1px solid var(--border); background: #0f172a; color: var(--text); }}
    .stake-actions {{ display: flex; gap: 0.5rem; }}
    button {{ flex: 1; padding: 0.55rem; border: none; border-radius: 6px; background: var(--accent); color: #0f172a; font-weight: 600; cursor: pointer; }}
    button.secondary {{ background: #374151; color: var(--text); }}
    button:hover {{ opacity: 0.9; }}
    .stake-hint {{ font-size: 0.75rem; color: var(--muted); margin: 0.5rem 0 0; }}
    nav {{ margin-top: 0.8rem; }}
    nav a {{ color: var(--accent); margin-right: 1rem; text-decoration: none; }}
    .toast {{ position: fixed; bottom: 1.5rem; right: 1.5rem; background: #065f46; padding: 0.8rem 1.2rem; border-radius: 8px; display: none; }}
  </style>
</head>
<body>
  <div class="topbar">
    <h1>The Hub <span style="color:var(--muted);font-weight:400">— Veridag Yatırım Paneli</span></h1>
    <p>Token tabanlı staking · Bonding curve · Gerçek zamanlı kâr payı</p>
    <div class="split-bar">
      <span class="split-chip">Staking & Altyapı: <strong>%{split.staking_share * 100:.0f}</strong></span>
      <span class="split-chip">Veridag Platform: <strong>%{split.platform_share * 100:.0f}</strong></span>
      <span class="split-chip">Ajan Operatörü: <strong>%{split.operator_share * 100:.0f}</strong></span>
    </div>
    <nav>
      <a href="/">← OAM Dashboard</a>
      <a href="/hub/agents">JSON API</a>
      <a href="/docs">API Docs</a>
    </nav>
  </div>
  <div class="container">
    <div class="grid">{card_html or '<p>Henüz yatırıma açık ajan yok.</p>'}</div>
  </div>
  <div class="toast" id="toast"></div>
  <script>
    function showToast(msg) {{
      const t = document.getElementById('toast');
      t.textContent = msg;
      t.style.display = 'block';
      setTimeout(() => t.style.display = 'none', 4000);
    }}
    function getWallet(btn) {{
      return btn.closest('.agent-card').querySelector('.wallet').value.trim();
    }}
    function getAmount(btn) {{
      return parseFloat(btn.closest('.agent-card').querySelector('.amount').value);
    }}
    async function stake(agentId, btn) {{
      const investor_id = getWallet(btn);
      const amount = getAmount(btn);
      if (!investor_id || !amount) {{ showToast('Cüzdan ve miktar gerekli'); return; }}
      const res = await fetch('/hub/stake', {{
        method: 'POST',
        headers: {{'Content-Type': 'application/json'}},
        body: JSON.stringify({{investor_id, agent_id: agentId, amount_usdc: amount}})
      }});
      const data = await res.json();
      showToast(res.ok ? `Stake başarılı: ${{data.shares?.toFixed(4)}} pay` : (data.detail || 'Hata'));
      if (res.ok) setTimeout(() => location.reload(), 1500);
    }}
    async function claim(agentId, btn) {{
      const investor_id = getWallet(btn);
      if (!investor_id) {{ showToast('Cüzdan adresi gerekli'); return; }}
      const res = await fetch('/hub/claim', {{
        method: 'POST',
        headers: {{'Content-Type': 'application/json'}},
        body: JSON.stringify({{investor_id, agent_id: agentId}})
      }});
      const data = await res.json();
      showToast(res.ok ? `Ödül alındı: $${{data.claimed_usdc?.toFixed(4)}}` : (data.detail || 'Hata'));
    }}
  </script>
</body>
</html>"""


@router.get("/agents")
async def list_agent_cards() -> JSONResponse:
    hub = get_investment_hub()
    cards = hub.list_identity_cards(_mesh().list_agents())
    return JSONResponse([c.model_dump() for c in cards])


@router.get("/agents/{agent_id}")
async def get_agent_card(agent_id: str) -> JSONResponse:
    hub = get_investment_hub()
    manifest = _mesh().registry.get(agent_id)
    reliability = manifest.reliability_score if manifest else 1.0
    card = hub.build_identity_card(agent_id, reliability)
    if card is None:
        raise HTTPException(status_code=404, detail="Ajan bulunamadı")
    return JSONResponse(card.model_dump())


@router.get("/revenue/config")
async def revenue_config() -> RevenueSplitConfig:
    return get_investment_hub().split


@router.get("/revenue/events")
async def revenue_events(agent_id: str | None = None, limit: int = 50) -> JSONResponse:
    events = get_investment_hub().revenue.list_events(agent_id=agent_id, limit=limit)
    return JSONResponse([e.model_dump() for e in events])


@router.get("/pools")
async def list_pools() -> JSONResponse:
    pools = get_investment_hub().pools.list_pools()
    return JSONResponse([p.model_dump() for p in pools])


@router.post("/stake")
async def stake(request: StakeRequest) -> Dict[str, Any]:
    hub = get_investment_hub()
    manifest = _mesh().registry.get(request.agent_id)
    if manifest is None:
        raise HTTPException(status_code=404, detail="Ajan kayıtlı değil")
    hub.ensure_agent(manifest)
    try:
        position = hub.pools.stake(request.investor_id, request.agent_id, request.amount_usdc)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    ledger = hub.pools.list_ledger(request.agent_id, limit=1)
    return {
        "staked": True,
        "shares": position.shares,
        "staked_usdc": position.staked_usdc,
        "token_price": hub.pools.token_price(request.agent_id),
        "tx_hash": ledger[-1].tx_hash if ledger else None,
    }


@router.post("/unstake")
async def unstake(request: UnstakeRequest) -> Dict[str, Any]:
    hub = get_investment_hub()
    try:
        usdc_out = hub.pools.unstake(request.investor_id, request.agent_id, request.shares)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"unstaked": True, "usdc_returned": usdc_out}


@router.post("/claim")
async def claim_rewards(request: ClaimRewardsRequest) -> Dict[str, Any]:
    claimed = get_investment_hub().pools.claim_rewards(request.investor_id, request.agent_id)
    return {"claimed_usdc": claimed}


@router.get("/positions/{investor_id}")
async def list_positions(investor_id: str) -> JSONResponse:
    positions = get_investment_hub().pools.list_positions(investor_id)
    return JSONResponse([p.model_dump() for p in positions])


def _class_label(agent_class: str) -> str:
    labels = {
        "fetcher": "Veri Çekici",
        "transformer": "Transformer",
        "synthesizer": "Sentezleyici",
        "analyst": "Analist",
        "validator": "Doğrulayıcı",
        "orchestrator": "Orkestratör",
    }
    return labels.get(agent_class, agent_class)


def _format_number(n: int) -> str:
    if n >= 1_000_000:
        return f"{n / 1_000_000:.1f}M"
    if n >= 1_000:
        return f"{n / 1_000:.1f}K"
    return str(n)
