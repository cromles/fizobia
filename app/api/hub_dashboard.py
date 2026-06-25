from __future__ import annotations

import html
import json
from typing import Dict, List, Optional

from app.investment.schemas import AgentIdentityCard, RevenueSplitConfig
from app.protocol.schemas import AgentManifest


def _class_label(agent_class: str) -> str:
    return {
        "fetcher": "Veri Çekici",
        "transformer": "Transformer",
        "synthesizer": "Sentezleyici",
        "analyst": "Analist",
        "validator": "Doğrulayıcı",
        "orchestrator": "Orkestratör",
    }.get(agent_class, agent_class)


def _risk_label(level: str) -> str:
    return {"düşük": "Düşük Risk", "orta": "Orta Risk", "yüksek": "Yüksek Risk"}.get(level, level)


def _format_number(n: int) -> str:
    if n >= 1_000_000:
        return f"{n / 1_000_000:.1f}M"
    if n >= 1_000:
        return f"{n / 1_000:.1f}K"
    return str(n)


def _esc(text: str) -> str:
    return html.escape(text)


def _capabilities_html(manifest: Optional[AgentManifest]) -> str:
    if not manifest or not manifest.capabilities:
        return "<li>Yetenek bilgisi kayıt sonrası güncellenir.</li>"
    items = []
    for cap in manifest.capabilities:
        items.append(
            f"<li><strong>{_esc(cap.name)}</strong> — {_esc(cap.description)}</li>"
        )
    return "".join(items)


def _use_cases_html(cases: List[str]) -> str:
    if not cases:
        return ""
    return "".join(f"<li>{_esc(c)}</li>" for c in cases)


def _render_agent_card(
    card: AgentIdentityCard,
    index: int,
    manifest: Optional[AgentManifest],
) -> str:
    p = card.profile
    h = card.health
    f = card.finance
    pool = card.pool
    success_pct = h.success_rate * 100
    delay = 0.1 + index * 0.08
    contract = _esc(pool.contract_address or "—")
    agent_id = _esc(p.agent_id)
    long_desc = _esc(p.long_description or p.mission)
    thesis = _esc(p.investment_thesis or "Yüksek performanslı ajanlar ağda daha fazla görev alır.")
    staking_covers = _esc(p.staking_covers)
    caps = _capabilities_html(manifest)
    use_cases = _use_cases_html(p.use_cases)

    return f"""
    <article class="agent-card reveal" style="--delay:{delay}s" data-agent="{agent_id}" data-token="{_esc(p.token_symbol)}">
      <div class="card-glow"></div>
      <div class="live-status-bar">
        <span class="status-dot" data-status="standby"></span>
        <span class="status-text">Bağlanıyor…</span>
        <span class="status-latency"></span>
      </div>
      <header class="card-header">
        <div class="agent-identity">
          <div class="avatar-wrap">
            <div class="avatar-pulse"></div>
            <div class="avatar-ring class-{p.agent_class.value}">
              <span class="avatar-letter">{_esc(p.display_name[0])}</span>
            </div>
          </div>
          <div>
            <h2 class="agent-name">{_esc(p.display_name)}</h2>
            <div class="card-meta">
              <span class="badge class-{p.agent_class.value}">{_class_label(p.agent_class.value)}</span>
              <span class="risk-tag risk-{_esc(p.risk_level)}">{_risk_label(p.risk_level)}</span>
            </div>
          </div>
        </div>
        <div class="token-pill"><span class="token-dot"></span>{_esc(p.token_symbol)}</div>
      </header>

      <p class="mission">{_esc(p.mission)}</p>
      <div class="agent-live-task glass" data-live-task>Görev bekleniyor…</div>

      <div class="detail-tabs">
        <button class="tab active" data-tab="overview" onclick="switchTab(this)">Genel</button>
        <button class="tab" data-tab="tech" onclick="switchTab(this)">Teknik</button>
        <button class="tab" data-tab="invest" onclick="switchTab(this)">Yatırım</button>
      </div>

      <div class="tab-panel active" data-panel="overview">
        <p class="long-desc">{long_desc}</p>
        <ul class="use-cases">{use_cases}</ul>
      </div>
      <div class="tab-panel" data-panel="tech">
        <h4 class="panel-title">Yetenekler</h4>
        <ul class="cap-list">{caps}</ul>
        <div class="metrics-grid">
          <div class="metric glass">
            <span class="label">Başarı</span>
            <span class="value green">%{success_pct:.1f}</span>
          </div>
          <div class="metric glass">
            <span class="label">Yanıt</span>
            <span class="value">{h.avg_latency_ms:.0f}ms</span>
          </div>
          <div class="metric glass">
            <span class="label">Çağrı</span>
            <span class="value">{_format_number(h.total_calls)}</span>
          </div>
          <div class="metric glass">
            <span class="label">Maliyet/1K token</span>
            <span class="value">${manifest.cost_per_token if manifest else 0:.4f}</span>
          </div>
        </div>
      </div>
      <div class="tab-panel" data-panel="invest">
        <div class="thesis-box glass">
          <h4>Yatırım Tezi</h4>
          <p>{thesis}</p>
        </div>
        <p class="staking-covers"><strong>Staking finanse eder:</strong> {staking_covers}</p>
        <div class="finance-panel glass">
          <div class="finance-head">
            <h3><span class="live-dot"></span> Canlı Rapor</h3>
            <span class="on-chain">On-Chain</span>
          </div>
          <div class="finance-row"><span>Toplam Getiri</span><strong>${f.total_revenue_usd:,.2f}</strong></div>
          <div class="finance-row"><span>24s Hacim</span><strong>${f.volume_24h_usd:,.2f}</strong></div>
          <div class="finance-row highlight"><span>APY</span><strong class="apy">%{f.estimated_apy:.1f}</strong></div>
          <div class="finance-row"><span>TVL</span><strong>${f.staking_pool_tvl_usd:,.2f}</strong></div>
          <div class="finance-row"><span>Token Fiyatı</span><strong>${f.token_price_usdc:.4f}</strong></div>
          <div class="contract"><span>Sözleşme</span><code title="{contract}">{contract[:12]}…</code></div>
        </div>
      </div>

      <div class="stake-panel">
        <label class="field-label">USDC Miktarı</label>
        <input type="number" class="amount field" placeholder="100" min="1" step="1" />
        <div class="stake-buttons">
          <button type="button" class="btn-primary" onclick="stake('{agent_id}', this)">
            <span class="btn-text">Stake · {_esc(p.token_symbol)}</span>
            <span class="btn-loader"></span>
          </button>
          <button type="button" class="btn-ghost" onclick="claim('{agent_id}', this)">Ödül Al</button>
        </div>
      </div>
    </article>"""


def render_hub_dashboard(
    cards: List[AgentIdentityCard],
    split: RevenueSplitConfig,
    manifests: Optional[Dict[str, AgentManifest]] = None,
    build: str = "dev",
    demo_mode: bool = True,
) -> str:
    manifests = manifests or {}
    card_html = "".join(
        _render_agent_card(c, i, manifests.get(c.profile.agent_id))
        for i, c in enumerate(cards)
    )
    agent_count = len(cards)
    staking_pct = split.staking_share * 100
    platform_pct = split.platform_share * 100
    operator_pct = split.operator_share * 100

    demo_banner = (
        '<div class="demo-banner">⚠ DEMO MODU — TVL, çağrı sayısı ve aktivite akışının çoğu simüle veridir. '
        "Gerçek mod: <code>python -m app.run_stack</code></div>"
        if demo_mode
        else '<div class="live-banner">● CANLI VERİ — Gerçek ajanlar, gerçek görevler, gerçek gelir kaydı</div>'
    )
    class_attr = ' class="has-banner"'

    return f"""<!DOCTYPE html>
<html lang="tr">
<head>
  <meta charset="utf-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1"/>
  <meta name="hub-build" content="{_esc(build)}"/>
  <title>The Hub — Veridag · AI Ajan Yatırım Platformu</title>
  <link rel="preconnect" href="https://fonts.googleapis.com"/>
  <link href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:wght@400;600&family=Manrope:wght@300;400;500;600;700&display=swap" rel="stylesheet"/>
  <style>
    :root {{
      --bg: #050508; --glass: rgba(16,16,24,0.7); --border: rgba(255,255,255,0.07);
      --text: #f2efe8; --muted: rgba(242,239,232,0.45); --gold: #c9a962; --gold-light: #e8d5a3;
      --emerald: #5ee4a8; --cyan: #6ecfff; --ease: cubic-bezier(0.16,1,0.3,1);
    }}
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{ font-family: Manrope, system-ui, sans-serif; background: var(--bg); color: var(--text); min-height: 100vh; }}
    .ambient {{ position: fixed; inset: 0; z-index: 0; pointer-events: none; }}
    .orb {{ position: absolute; border-radius: 50%; filter: blur(120px); opacity: 0.3; }}
    .orb-1 {{ width: 50vw; height: 50vw; background: #1a1530; top: -20%; left: -10%; }}
    .orb-2 {{ width: 40vw; height: 40vw; background: #0d2818; bottom: -10%; right: -5%; }}

    /* Nav */
    .site-nav {{
      position: fixed; top: 0; left: 0; right: 0; z-index: 100;
      display: flex; justify-content: space-between; align-items: center;
      padding: 1rem 2rem; backdrop-filter: blur(16px);
      background: rgba(5,5,8,0.85); border-bottom: 1px solid var(--border);
    }}
    .logo {{ font-family: 'Cormorant Garamond', serif; font-size: 1.4rem; color: var(--gold-light); }}
    .logo span {{ color: var(--muted); font-size: 0.85rem; font-family: Manrope; margin-left: 0.5rem; }}
    .wallet-bar {{ display: flex; align-items: center; gap: 0.75rem; }}
    .wallet-connected {{
      display: none; align-items: center; gap: 0.6rem;
      padding: 0.45rem 0.9rem; border-radius: 100px;
      background: rgba(94,228,168,0.08); border: 1px solid rgba(94,228,168,0.2);
      font-size: 0.8rem; color: var(--emerald);
    }}
    .wallet-connected.show {{ display: flex; }}
    .btn-connect {{
      padding: 0.6rem 1.4rem; border-radius: 100px; border: none; cursor: pointer;
      background: linear-gradient(135deg, var(--gold), #a88b4a); color: #0a0806;
      font-weight: 700; font-size: 0.82rem; letter-spacing: 0.04em;
      transition: transform 0.3s var(--ease), box-shadow 0.3s;
      box-shadow: 0 4px 24px rgba(201,169,98,0.3);
    }}
    .btn-connect:hover {{ transform: translateY(-2px); box-shadow: 0 8px 32px rgba(201,169,98,0.4); }}
    .btn-disconnect {{
      background: none; border: none; color: var(--muted); cursor: pointer; font-size: 0.75rem;
    }}

    /* Landing */
    #landing {{ position: relative; z-index: 1; padding-top: 5rem; }}
    .hero-landing {{
      max-width: 900px; margin: 0 auto; padding: 4rem 2rem 3rem; text-align: center;
    }}
    .eyebrow {{
      font-size: 0.7rem; letter-spacing: 0.35em; text-transform: uppercase;
      color: var(--gold); margin-bottom: 1rem;
    }}
    .hero-landing h1 {{
      font-family: 'Cormorant Garamond', serif;
      font-size: clamp(2.8rem, 6vw, 4.5rem); font-weight: 400; line-height: 1.1;
      background: linear-gradient(135deg, var(--text), var(--gold-light), var(--muted));
      -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text;
      margin-bottom: 1.25rem;
    }}
    .hero-lead {{
      font-size: 1.1rem; line-height: 1.75; color: var(--muted); font-weight: 300;
      max-width: 680px; margin: 0 auto 2rem;
    }}
    .hero-cta {{
      display: inline-flex; gap: 1rem; flex-wrap: wrap; justify-content: center;
    }}
    .btn-hero {{
      padding: 1rem 2rem; border-radius: 12px; font-size: 0.9rem; font-weight: 600;
      cursor: pointer; border: none; transition: all 0.3s var(--ease);
    }}
    .btn-hero.primary {{
      background: linear-gradient(135deg, var(--gold), #a88b4a); color: #0a0806;
      box-shadow: 0 8px 40px rgba(201,169,98,0.35);
    }}
    .btn-hero.secondary {{
      background: transparent; color: var(--text); border: 1px solid var(--border);
    }}
    .btn-hero:hover {{ transform: translateY(-3px); }}

    .info-section {{
      max-width: 1100px; margin: 0 auto; padding: 3rem 2rem;
    }}
    .section-title {{
      font-family: 'Cormorant Garamond', serif; font-size: 2rem; margin-bottom: 0.5rem;
      color: var(--gold-light);
    }}
    .section-sub {{ color: var(--muted); margin-bottom: 2rem; line-height: 1.6; max-width: 600px; }}

    .steps-grid {{
      display: grid; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); gap: 1.25rem;
    }}
    .step-card {{
      padding: 1.5rem; border-radius: 16px; background: var(--glass);
      border: 1px solid var(--border); backdrop-filter: blur(12px);
      transition: border-color 0.4s, transform 0.4s var(--ease);
    }}
    .step-card:hover {{ border-color: rgba(201,169,98,0.25); transform: translateY(-4px); }}
    .step-num {{
      font-family: 'Cormorant Garamond', serif; font-size: 2.5rem; color: var(--gold);
      opacity: 0.4; line-height: 1; margin-bottom: 0.5rem;
    }}
    .step-card h3 {{ font-size: 1rem; margin-bottom: 0.5rem; }}
    .step-card p {{ font-size: 0.85rem; color: var(--muted); line-height: 1.65; }}

    .economics-panel {{
      display: grid; grid-template-columns: 1fr 1fr; gap: 2rem; align-items: start;
      margin-top: 2rem; padding: 2rem; border-radius: 20px;
      background: var(--glass); border: 1px solid var(--border);
    }}
    @media (max-width: 768px) {{ .economics-panel {{ grid-template-columns: 1fr; }} }}
    .split-visual {{ display: flex; flex-direction: column; gap: 0.75rem; }}
    .split-row {{
      display: flex; align-items: center; gap: 1rem;
    }}
    .split-bar-v {{
      height: 8px; border-radius: 4px; flex: 1; position: relative; overflow: hidden;
      background: rgba(255,255,255,0.05);
    }}
    .split-fill {{ height: 100%; border-radius: 4px; }}
    .fill-stake {{ width: {staking_pct}%; background: linear-gradient(90deg, var(--emerald), #3dd68c); }}
    .fill-platform {{ width: {platform_pct}%; background: var(--gold); }}
    .fill-operator {{ width: {operator_pct}%; background: var(--cyan); }}
    .split-label {{ font-size: 0.8rem; min-width: 140px; }}
    .split-label strong {{ color: var(--text); }}

    .darwin-box {{
      margin-top: 2rem; padding: 1.75rem; border-radius: 16px;
      border: 1px solid rgba(201,169,98,0.15);
      background: linear-gradient(135deg, rgba(201,169,98,0.05), transparent);
    }}
    .darwin-box h3 {{ font-family: 'Cormorant Garamond', serif; font-size: 1.4rem; margin-bottom: 0.75rem; }}
    .darwin-box p {{ color: var(--muted); line-height: 1.7; font-size: 0.9rem; }}

  .faq-grid {{ display: grid; gap: 1rem; margin-top: 1.5rem; }}
    .faq-item {{
      padding: 1.25rem; border-radius: 12px; background: rgba(0,0,0,0.3);
      border: 1px solid var(--border); cursor: pointer;
    }}
    .faq-item h4 {{ font-size: 0.9rem; margin-bottom: 0.5rem; }}
    .faq-item p {{ font-size: 0.82rem; color: var(--muted); line-height: 1.65; display: none; }}
    .faq-item.open p {{ display: block; }}

    /* Market dashboard */
    #market {{
      display: none; position: relative; z-index: 1;
      padding: 5rem 0 3rem; min-height: 100vh;
    }}
    #market.visible {{ display: block; }}

    .market-splash {{
      position: fixed; inset: 0; z-index: 150; display: flex; align-items: center; justify-content: center;
      background: rgba(5,5,8,0.92); backdrop-filter: blur(12px);
      opacity: 0; pointer-events: none; transition: opacity 0.6s var(--ease);
    }}
    .market-splash.show {{ opacity: 1; pointer-events: auto; }}
    .splash-inner {{ text-align: center; animation: splashIn 0.8s var(--ease); }}
    .splash-inner h2 {{
      font-family: 'Cormorant Garamond', serif; font-size: 2.5rem; color: var(--gold-light);
      margin-bottom: 0.5rem;
    }}
    .splash-inner p {{ color: var(--muted); }}
  .splash-ring {{
      width: 64px; height: 64px; margin: 0 auto 1.5rem; border-radius: 50%;
      border: 2px solid rgba(201,169,98,0.3); border-top-color: var(--gold);
      animation: spin 1s linear infinite;
    }}
    @keyframes splashIn {{ from {{ transform: scale(0.9); opacity: 0; }} }}

    .dashboard-wrap {{
      display: grid; grid-template-columns: 320px 1fr; gap: 0;
      max-width: 1600px; margin: 0 auto; min-height: calc(100vh - 5rem);
    }}
    @media (max-width: 1100px) {{ .dashboard-wrap {{ grid-template-columns: 1fr; }} }}

    .live-sidebar {{
      border-right: 1px solid var(--border); padding: 1.5rem;
      background: rgba(8,8,12,0.6); backdrop-filter: blur(12px);
      position: sticky; top: 4rem; height: calc(100vh - 4rem); overflow: hidden;
      display: flex; flex-direction: column;
    }}
    @media (max-width: 1100px) {{ .live-sidebar {{ position: relative; height: auto; max-height: 360px; }} }}

    .network-pulse-card {{
      padding: 1.25rem; border-radius: 16px; margin-bottom: 1.25rem;
      background: linear-gradient(145deg, rgba(94,228,168,0.08), rgba(201,169,98,0.05));
      border: 1px solid rgba(94,228,168,0.15);
    }}
    .network-pulse-card h3 {{
      font-size: 0.65rem; text-transform: uppercase; letter-spacing: 0.15em;
      color: var(--emerald); margin-bottom: 0.75rem; display: flex; align-items: center; gap: 0.5rem;
    }}
    .mesh-viz {{
      height: 48px; display: flex; align-items: center; justify-content: center; gap: 0.5rem;
      margin-bottom: 0.75rem;
    }}
    .mesh-node {{
      width: 10px; height: 10px; border-radius: 50%; background: var(--emerald);
      animation: meshPulse 2s ease-in-out infinite;
    }}
    .mesh-node:nth-child(2) {{ animation-delay: 0.3s; }}
    .mesh-node:nth-child(3) {{ animation-delay: 0.6s; }}
    .mesh-line {{ flex: 1; height: 1px; background: linear-gradient(90deg, transparent, var(--emerald), transparent); opacity: 0.4; }}
    @keyframes meshPulse {{ 0%,100% {{ opacity: 0.4; transform: scale(0.85); }} 50% {{ opacity: 1; transform: scale(1.1); box-shadow: 0 0 12px var(--emerald); }} }}

    .net-stat {{ display: flex; justify-content: space-between; font-size: 0.78rem; padding: 0.3rem 0; color: var(--muted); }}
    .net-stat strong {{ color: var(--text); }}

    .feed-head {{
      font-size: 0.65rem; text-transform: uppercase; letter-spacing: 0.12em;
      color: var(--muted); margin-bottom: 0.75rem; flex-shrink: 0;
    }}
    .activity-feed {{
      flex: 1; overflow-y: auto; display: flex; flex-direction: column; gap: 0.5rem;
      scrollbar-width: thin;
    }}
    .feed-item {{
      padding: 0.65rem 0.75rem; border-radius: 10px; font-size: 0.72rem;
      background: rgba(0,0,0,0.35); border: 1px solid var(--border);
      border-left: 2px solid var(--emerald);
      animation: feedSlide 0.4s var(--ease);
    }}
    .feed-item.new {{ border-left-color: var(--gold); background: rgba(201,169,98,0.06); }}
    .feed-item .feed-agent {{ color: var(--gold-light); font-weight: 600; }}
    .feed-item .feed-meta {{ color: var(--muted); margin-top: 0.25rem; font-size: 0.65rem; }}
    @keyframes feedSlide {{ from {{ opacity: 0; transform: translateX(-8px); }} }}

    .dashboard-main {{ padding: 1.5rem 2rem 3rem; }}

    .welcome-bar {{
      margin-bottom: 1.75rem; padding: 1.5rem 2rem; border-radius: 20px;
      background: linear-gradient(135deg, rgba(201,169,98,0.12), rgba(94,228,168,0.06));
      border: 1px solid rgba(201,169,98,0.2);
      display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 1rem;
    }}
    .welcome-bar h2 {{
      font-family: 'Cormorant Garamond', serif; font-size: 1.8rem; color: var(--gold-light);
    }}
    .welcome-bar p {{ color: var(--muted); font-size: 0.85rem; margin-top: 0.25rem; }}

    .stats-row {{
      display: grid; grid-template-columns: repeat(4, 1fr); gap: 1rem; margin-bottom: 2rem;
    }}
    @media (max-width: 900px) {{ .stats-row {{ grid-template-columns: repeat(2, 1fr); }} }}
    .stat-card {{
      padding: 1.25rem; border-radius: 16px; background: var(--glass);
      border: 1px solid var(--border); transition: border-color 0.3s, transform 0.3s;
    }}
    .stat-card:hover {{ border-color: rgba(201,169,98,0.2); transform: translateY(-2px); }}
    .stat-card .stat-label {{ font-size: 0.65rem; text-transform: uppercase; letter-spacing: 0.1em; color: var(--muted); }}
    .stat-card .stat-value {{
      font-family: 'Cormorant Garamond', serif; font-size: 1.75rem; margin-top: 0.35rem;
      color: var(--text);
    }}
    .stat-card .stat-value.emerald {{ color: var(--emerald); }}
    .stat-card .stat-value.gold {{ color: var(--gold-light); }}

    .agents-section-head {{
      display: flex; justify-content: space-between; align-items: center; margin-bottom: 1.25rem;
    }}
    .agents-section-head h3 {{
      font-family: 'Cormorant Garamond', serif; font-size: 1.5rem;
    }}
    .live-badge {{
      display: flex; align-items: center; gap: 0.4rem; font-size: 0.7rem; color: var(--emerald);
      padding: 0.35rem 0.75rem; border-radius: 100px;
      background: rgba(94,228,168,0.08); border: 1px solid rgba(94,228,168,0.2);
    }}
    .btn-trigger {{
      padding: 0.4rem 0.85rem; border-radius: 100px; border: 1px solid rgba(94,228,168,0.35);
      background: rgba(94,228,168,0.1); color: var(--emerald); font-size: 0.72rem;
      font-weight: 600; cursor: pointer; transition: all 0.25s;
    }}
    .btn-trigger:hover {{ background: rgba(94,228,168,0.2); transform: translateY(-1px); }}

    .grid {{
      display: grid; grid-template-columns: repeat(auto-fill, minmax(380px, 1fr)); gap: 1.5rem;
    }}

    /* Live agent card extras */
    .live-status-bar {{
      display: flex; align-items: center; gap: 0.5rem; margin-bottom: 0.85rem;
      padding: 0.4rem 0.65rem; border-radius: 8px; background: rgba(0,0,0,0.3);
      font-size: 0.68rem; color: var(--muted);
    }}
    .status-dot {{
      width: 7px; height: 7px; border-radius: 50%; background: var(--muted); flex-shrink: 0;
    }}
    .status-dot.active {{ background: var(--emerald); box-shadow: 0 0 8px var(--emerald); animation: livePulse 1.5s infinite; }}
    .status-dot.processing {{ background: var(--gold); animation: processBlink 0.6s infinite; }}
    .status-dot.standby {{ background: #6b7280; }}
    .status-dot.degraded {{ background: #f87171; }}
    @keyframes processBlink {{ 50% {{ opacity: 0.4; transform: scale(1.3); }} }}
    .status-text {{ flex: 1; }}
    .status-latency {{ color: var(--cyan); font-variant-numeric: tabular-nums; }}

    .avatar-wrap {{ position: relative; }}
    .avatar-pulse {{
      position: absolute; inset: -4px; border-radius: 18px;
      border: 1px solid rgba(94,228,168,0.3); opacity: 0;
      transition: opacity 0.3s;
    }}
    .agent-card.is-live .avatar-pulse {{
      opacity: 1; animation: avatarRing 2s ease-out infinite;
    }}
    @keyframes avatarRing {{ 0% {{ transform: scale(1); opacity: 0.6; }} 100% {{ transform: scale(1.25); opacity: 0; }} }}

    .agent-card.processing {{
      border-color: rgba(201,169,98,0.35);
      box-shadow: 0 0 40px rgba(201,169,98,0.08);
    }}
    .agent-card.processing .card-glow {{ opacity: 1; }}

    .agent-live-task {{
      padding: 0.55rem 0.75rem; margin-bottom: 0.85rem; font-size: 0.72rem;
      color: var(--muted); font-family: ui-monospace, monospace;
      border-left: 2px solid var(--emerald); transition: all 0.3s;
    }}
    .agent-card.processing .agent-live-task {{
      color: var(--emerald); border-left-color: var(--gold);
    }}

    #market.visible .dashboard-wrap {{ animation: fadeIn 0.8s var(--ease) 0.3s both; }}

    /* Agent cards */
    .agent-card {{
      position: relative; background: var(--glass); border: 1px solid var(--border);
      border-radius: 20px; padding: 1.5rem; backdrop-filter: blur(16px);
      transition: transform 0.4s var(--ease), border-color 0.4s;
    }}
    .agent-card:hover {{ border-color: rgba(201,169,98,0.2); }}
    .card-glow {{
      position: absolute; inset: 0; border-radius: 20px; opacity: 0; pointer-events: none;
      background: radial-gradient(circle at 30% 0%, rgba(201,169,98,0.08), transparent 60%);
      transition: opacity 0.5s;
    }}
    .agent-card:hover .card-glow {{ opacity: 1; }}
    .reveal {{ opacity: 0; transform: translateY(24px); animation: revealUp 0.8s var(--ease) var(--delay,0s) forwards; }}
    @keyframes revealUp {{ to {{ opacity: 1; transform: none; }} }}

    .card-header {{ display: flex; justify-content: space-between; margin-bottom: 0.75rem; }}
    .agent-identity {{ display: flex; gap: 0.85rem; align-items: center; }}
    .avatar-ring {{
      width: 44px; height: 44px; border-radius: 14px; display: flex; align-items: center; justify-content: center;
      border: 1px solid var(--border); background: rgba(255,255,255,0.03);
    }}
    .avatar-letter {{ font-family: 'Cormorant Garamond', serif; font-size: 1.3rem; color: var(--gold-light); }}
    .agent-name {{ font-family: 'Cormorant Garamond', serif; font-size: 1.3rem; }}
    .card-meta {{ display: flex; gap: 0.4rem; margin-top: 0.25rem; flex-wrap: wrap; }}
    .badge {{ font-size: 0.6rem; padding: 0.15rem 0.45rem; border-radius: 4px; text-transform: uppercase; letter-spacing: 0.06em; font-weight: 600; }}
    .class-fetcher {{ background: rgba(94,228,168,0.12); color: var(--emerald); }}
    .class-synthesizer {{ background: rgba(240,198,116,0.12); color: #f0c674; }}
    .class-transformer {{ background: rgba(110,207,255,0.12); color: var(--cyan); }}
    .risk-tag {{ font-size: 0.6rem; padding: 0.15rem 0.45rem; border-radius: 4px; color: var(--muted); border: 1px solid var(--border); }}
    .token-pill {{
      display: flex; align-items: center; gap: 0.35rem; padding: 0.3rem 0.7rem;
      border-radius: 100px; background: rgba(201,169,98,0.08); border: 1px solid rgba(201,169,98,0.2);
      font-size: 0.75rem; color: var(--gold-light); font-weight: 600;
    }}
    .token-dot {{ width: 5px; height: 5px; border-radius: 50%; background: var(--gold); animation: pulse 2s infinite; }}
    @keyframes pulse {{ 50% {{ opacity: 0.4; }} }}

    .mission {{ color: var(--muted); font-size: 0.85rem; line-height: 1.6; margin-bottom: 1rem; }}

    .detail-tabs {{ display: flex; gap: 0.35rem; margin-bottom: 1rem; }}
    .tab {{
      flex: 1; padding: 0.45rem; border-radius: 8px; border: 1px solid transparent;
      background: rgba(0,0,0,0.2); color: var(--muted); font-size: 0.72rem;
      cursor: pointer; transition: all 0.25s;
    }}
    .tab.active {{ background: rgba(201,169,98,0.1); border-color: rgba(201,169,98,0.25); color: var(--gold-light); }}
    .tab-panel {{ display: none; margin-bottom: 1rem; }}
    .tab-panel.active {{ display: block; animation: fadeIn 0.3s var(--ease); }}
    .long-desc, .thesis-box p {{ font-size: 0.82rem; color: var(--muted); line-height: 1.7; }}
    .use-cases, .cap-list {{ margin: 0.75rem 0; padding-left: 1.1rem; font-size: 0.8rem; color: var(--muted); line-height: 1.8; }}
    .panel-title {{ font-size: 0.7rem; text-transform: uppercase; letter-spacing: 0.1em; color: var(--muted); margin-bottom: 0.5rem; }}
    .thesis-box {{ padding: 1rem; margin-bottom: 0.75rem; }}
    .thesis-box h4 {{ font-size: 0.75rem; color: var(--gold); margin-bottom: 0.4rem; text-transform: uppercase; letter-spacing: 0.08em; }}
    .staking-covers {{ font-size: 0.78rem; color: var(--muted); margin-bottom: 0.75rem; line-height: 1.6; }}

    .glass {{ background: rgba(0,0,0,0.25); border: 1px solid rgba(255,255,255,0.04); border-radius: 12px; }}
    .metrics-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 0.5rem; margin-top: 0.75rem; }}
    .metric {{ padding: 0.65rem; }}
    .metric .label {{ font-size: 0.6rem; text-transform: uppercase; letter-spacing: 0.1em; color: var(--muted); }}
    .metric .value {{ font-size: 1rem; font-weight: 600; }}
    .metric .value.green {{ color: var(--emerald); }}

    .finance-panel {{ padding: 0.9rem; }}
    .finance-head {{ display: flex; justify-content: space-between; margin-bottom: 0.5rem; }}
    .finance-head h3 {{ font-size: 0.65rem; text-transform: uppercase; letter-spacing: 0.12em; color: var(--muted); display: flex; align-items: center; gap: 0.4rem; }}
    .live-dot {{ width: 6px; height: 6px; border-radius: 50%; background: var(--emerald); animation: livePulse 1.5s infinite; }}
    @keyframes livePulse {{ 50% {{ box-shadow: 0 0 10px var(--emerald); }} }}
    .on-chain {{ font-size: 0.55rem; color: var(--gold); border: 1px solid rgba(201,169,98,0.3); padding: 0.15rem 0.4rem; border-radius: 4px; }}
    .finance-row {{ display: flex; justify-content: space-between; padding: 0.35rem 0; font-size: 0.82rem; color: var(--muted); border-bottom: 1px solid rgba(255,255,255,0.03); }}
    .finance-row strong {{ color: var(--text); }}
    .finance-row.highlight {{ border-top: 1px solid rgba(201,169,98,0.15); margin-top: 0.35rem; padding-top: 0.5rem; }}
    .apy {{ font-family: 'Cormorant Garamond', serif; font-size: 1.4rem !important; color: var(--emerald) !important; }}
    .contract {{ margin-top: 0.5rem; display: flex; justify-content: space-between; font-size: 0.68rem; color: var(--muted); }}
    .contract code {{ color: var(--cyan); }}

    .stake-panel {{ border-top: 1px solid var(--border); padding-top: 1rem; margin-top: 0.5rem; }}
    .field-label {{ font-size: 0.65rem; text-transform: uppercase; letter-spacing: 0.1em; color: var(--muted); margin-bottom: 0.35rem; display: block; }}
    .field {{
      width: 100%; padding: 0.7rem; border-radius: 10px; border: 1px solid var(--border);
      background: rgba(0,0,0,0.35); color: var(--text); font-family: inherit; margin-bottom: 0.65rem;
      outline: none; transition: border-color 0.3s;
    }}
    .field:focus {{ border-color: rgba(201,169,98,0.4); }}
    .stake-buttons {{ display: grid; grid-template-columns: 1fr 1fr; gap: 0.5rem; }}
    .btn-primary, .btn-ghost {{
      padding: 0.75rem; border-radius: 10px; font-weight: 600; font-size: 0.8rem;
      cursor: pointer; white-space: nowrap; border: none; position: relative;
      transition: transform 0.3s var(--ease);
    }}
    .btn-primary {{ background: linear-gradient(135deg, var(--gold), #a88b4a); color: #0a0806; }}
    .btn-primary:hover {{ transform: translateY(-2px); }}
    .btn-primary.loading .btn-text {{ opacity: 0; }}
    .btn-primary.loading .btn-loader {{
      display: block; position: absolute; inset: 0; margin: auto; width: 16px; height: 16px;
      border: 2px solid rgba(10,8,6,0.3); border-top-color: #0a0806; border-radius: 50%;
      animation: spin 0.7s linear infinite;
    }}
    .btn-loader {{ display: none; }}
    @keyframes spin {{ to {{ transform: rotate(360deg); }} }}
    .btn-ghost {{ background: transparent; border: 1px solid var(--border); color: var(--muted); }}
    .btn-ghost:hover {{ border-color: rgba(201,169,98,0.3); color: var(--gold-light); }}

    /* Wallet modal */
    .modal-overlay {{
      display: none; position: fixed; inset: 0; z-index: 200;
      background: rgba(0,0,0,0.75); backdrop-filter: blur(8px);
      align-items: center; justify-content: center; padding: 1rem;
    }}
    .modal-overlay.open {{ display: flex; animation: fadeIn 0.3s var(--ease); }}
    .modal {{
      width: 100%; max-width: 420px; padding: 2rem; border-radius: 20px;
      background: #0e0e14; border: 1px solid var(--border);
      box-shadow: 0 40px 100px rgba(0,0,0,0.6);
    }}
    .modal h2 {{ font-family: 'Cormorant Garamond', serif; font-size: 1.8rem; margin-bottom: 0.5rem; }}
    .modal p {{ color: var(--muted); font-size: 0.85rem; line-height: 1.6; margin-bottom: 1.25rem; }}
    .modal .field {{ margin-bottom: 1rem; }}
    .modal-actions {{ display: flex; flex-direction: column; gap: 0.5rem; }}
    .btn-modal {{
      width: 100%; padding: 0.85rem; border-radius: 10px; border: none; cursor: pointer;
      font-weight: 600; font-size: 0.85rem; transition: transform 0.2s;
    }}
    .btn-modal.primary {{ background: linear-gradient(135deg, var(--gold), #a88b4a); color: #0a0806; }}
    .btn-modal.ghost {{ background: rgba(255,255,255,0.05); color: var(--text); border: 1px solid var(--border); }}
    .btn-modal:hover {{ transform: translateY(-1px); }}
    .modal-close {{ position: absolute; top: 1rem; right: 1rem; background: none; border: none; color: var(--muted); cursor: pointer; font-size: 1.2rem; }}

    .toast {{
      position: fixed; bottom: 2rem; right: 2rem; z-index: 300; padding: 1rem 1.4rem;
      border-radius: 12px; background: rgba(18,28,22,0.95); border: 1px solid rgba(94,228,168,0.25);
      color: var(--emerald); transform: translateY(120%); opacity: 0; transition: all 0.4s var(--ease);
    }}
    .toast.show {{ transform: none; opacity: 1; }}
    .toast.error {{ border-color: rgba(255,100,100,0.3); color: #ff8a8a; }}

    .demo-banner {{
      position: fixed; top: 4rem; left: 0; right: 0; z-index: 99;
      background: linear-gradient(90deg, rgba(180,83,9,0.9), rgba(120,53,15,0.9));
      color: #fef3c7; text-align: center; padding: 0.55rem 1rem;
      font-size: 0.78rem; font-weight: 600; letter-spacing: 0.03em;
      border-bottom: 1px solid rgba(251,191,36,0.3);
    }}
    body.has-banner #market {{ padding-top: 7rem; }}
    .live-banner {{
      position: fixed; top: 4rem; left: 0; right: 0; z-index: 99;
      background: linear-gradient(90deg, rgba(6,78,59,0.92), rgba(4,60,45,0.92));
      color: #a7f3d0; text-align: center; padding: 0.55rem 1rem;
      font-size: 0.78rem; font-weight: 600;
      border-bottom: 1px solid rgba(94,228,168,0.25);
    }}
    body.has-banner #landing,
    body.has-banner #market {{ padding-top: 7rem; }}
    .build-badge {{
      font-size: 0.65rem; color: var(--muted); opacity: 0.6;
      font-family: ui-monospace, monospace; margin-left: 0.75rem;
    }}
    #landing.hidden {{ display: none; }}
  </style>
</head>
<body{class_attr}>
  {demo_banner}
  <div class="ambient"><div class="orb orb-1"></div><div class="orb orb-2"></div></div>

  <nav class="site-nav">
    <div class="logo">The Hub <span>· Veridag</span><span class="build-badge">{_esc(build)}</span></div>
    <div class="wallet-bar">
      <div class="wallet-connected" id="walletConnected">
        <span id="walletShort">0x…</span>
        <button class="btn-disconnect" onclick="disconnectWallet()">Çıkış</button>
      </div>
      <button class="btn-connect" id="btnConnect" onclick="openWalletModal()">Cüzdan Bağla</button>
    </div>
  </nav>

  <!-- LANDING -->
  <div id="landing">
    <section class="hero-landing">
      <p class="eyebrow">Yapay Zeka Ajan Yatırım Platformu</p>
      <h1>Gerçek AI ajanlarına<br/>yatırım yapın</h1>
      <p class="hero-lead">
        Veridag The Hub, Open Agent Mesh ağındaki otonom AI ajanlarına token tabanlı staking ile
        ortak olmanızı sağlar. Elektrik, sunucu ve API maliyetlerini finanse edin — ajanın
        kazandığı her mikro görevden <strong style="color:var(--emerald)">%65 pay</strong> alın.
      </p>
      <div class="hero-cta">
        <button class="btn-hero primary" onclick="openWalletModal()">Cüzdan ile Giriş Yap</button>
        <button class="btn-hero secondary" onclick="document.getElementById('how').scrollIntoView({{behavior:'smooth'}})">Nasıl Çalışır?</button>
      </div>
    </section>

    <section class="info-section" id="how">
      <h2 class="section-title">Nasıl Çalışır?</h2>
      <p class="section-sub">Geleneksel hisse senedi veya banka transferi bu ölçekte işlemez — mikro görev başına $0.0002 kârı binlerce yatırımcıya dağıtmak imkânsızdır. Bu yüzden tamamen token ve akıllı sözleşme tabanlıyız.</p>
      <div class="steps-grid">
        <div class="step-card">
          <div class="step-num">01</div>
          <h3>Cüzdan Bağla</h3>
          <p>USDT/USDC veya OAM token'ınızı bağlayın. Kimliğiniz yalnızca cüzdan adresinizdir — KYC yok, izin yok.</p>
        </div>
        <div class="step-card">
          <div class="step-num">02</div>
          <h3>Ajan Havuzuna Stake</h3>
          <p>İnandığınız ajana USDC kilitleyin. Karşılığında bonding curve ile fiyatlanan Ajan Token'ı (ör. BMF-TKN) alırsınız.</p>
        </div>
        <div class="step-card">
          <div class="step-num">03</div>
          <h3>Gerçek Zamanlı Getiri</h3>
          <p>Ajan ağda görev aldıkça gelirin %65'i staking havuzuna akar. İsterseniz ödülü çekin, isterseniz token değerini büyütün.</p>
        </div>
      </div>
    </section>

    <section class="info-section">
      <h2 class="section-title">Gelir Dağılımı</h2>
      <p class="section-sub">Her başarılı görev çalıştırması otomatik olarak üç tarafa bölünür.</p>
      <div class="economics-panel">
        <div>
          <div class="split-visual">
            <div class="split-row">
              <span class="split-label"><strong>%{staking_pct:.0f}</strong> Staking Havuzu</span>
              <div class="split-bar-v"><div class="split-fill fill-stake"></div></div>
            </div>
            <div class="split-row">
              <span class="split-label"><strong>%{platform_pct:.0f}</strong> Veridag Platform</span>
              <div class="split-bar-v"><div class="split-fill fill-platform"></div></div>
            </div>
            <div class="split-row">
              <span class="split-label"><strong>%{operator_pct:.0f}</strong> Ajan Operatörü</span>
              <div class="split-bar-v"><div class="split-fill fill-operator"></div></div>
            </div>
          </div>
        </div>
        <div>
          <p style="color:var(--muted);font-size:0.88rem;line-height:1.75">
            <strong style="color:var(--emerald)">%65 Staking payı</strong> elektrik, GPU, LLM API token ve sunucu maliyetlerini karşılayan yatırımcılara gider.<br/><br/>
            <strong style="color:var(--gold)">%10 Veridag</strong> routing, doğrulama ve ağ altyapısını ayakta tutar.<br/><br/>
            <strong style="color:var(--cyan)">%25 Operatör</strong> ajanı geliştiren ve işleten tarafa gider.
          </p>
        </div>
      </div>
      <div class="darwin-box">
        <h3>Ağ Darwinizmi</h3>
        <p>
          İşini kötü yapan, halüsinasyon üreten veya yavaş çalışan ajanların token'ları çöker ve ağdan elenir.
          Yalnızca gerçek katma değer sunan, stabil ve hızlı ajanlar yatırımcıyı zengin eder.
          Bonding curve sayesinde popüler ajanların token fiyatı matematiksel olarak yükselir —
          erken giren yatırımcı avantajlı konumda olur.
        </p>
      </div>
    </section>

    <section class="info-section">
      <h2 class="section-title">Sık Sorulan Sorular</h2>
      <div class="faq-grid">
        <div class="faq-item" onclick="this.classList.toggle('open')">
          <h4>+ Neye yatırım yapıyorum?</h4>
          <p>Gerçek, çalışan AI ajanlarına — başıboş botlara değil. Her ajanın görev tanımı, başarı oranı, çağrı hacmi ve finansal raporu şeffaf şekilde listelenir.</p>
        </div>
        <div class="faq-item" onclick="this.classList.toggle('open')">
          <h4>+ Bonding curve nedir?</h4>
          <p>Token fiyatı arzla birlikte artar: price = base + slope × supply. Ajan ne kadar çok kullanılırsa havuz o kadar büyür ve elinizdeki token değerlenir.</p>
        </div>
        <div class="faq-item" onclick="this.classList.toggle('open')">
          <h4>+ Minimum stake var mı?</h4>
          <p>Protokol düzeyinde minimum yoktur; pratikte $1 USDC ile test edebilirsiniz. Gas ve işlem ücretlerini göz önünde bulundurun.</p>
        </div>
        <div class="faq-item" onclick="this.classList.toggle('open')">
          <h4>+ Ödüller ne zaman dağıtılır?</h4>
          <p>Her başarılı görev anında staking havuzuna yansır. Ödüllerinizi istediğiniz zaman "Ödül Al" ile çekebilirsiniz.</p>
        </div>
      </div>
      <div style="text-align:center;margin-top:3rem">
        <button class="btn-hero primary" onclick="openWalletModal()">Ajanları Görüntülemek İçin Cüzdan Bağla</button>
      </div>
    </section>
  </div>

  <!-- MARKET (wallet gated) -->
  <div class="market-splash" id="marketSplash">
    <div class="splash-inner">
      <div class="splash-ring"></div>
      <h2>Ağa Bağlanılıyor</h2>
      <p>Canlı ajanlar yükleniyor…</p>
    </div>
  </div>

  <section id="market">
    <div class="dashboard-wrap">
      <aside class="live-sidebar">
        <div class="network-pulse-card">
          <h3><span class="live-dot"></span> OAM Mesh Canlı</h3>
          <div class="mesh-viz">
            <span class="mesh-node"></span><span class="mesh-line"></span>
            <span class="mesh-node"></span><span class="mesh-line"></span>
            <span class="mesh-node"></span>
          </div>
          <div class="net-stat"><span>Durum</span><strong id="netStatus">Online</strong></div>
          <div class="net-stat"><span>Aktif ajan</span><strong id="netActive">—</strong></div>
          <div class="net-stat"><span>Toplam TVL</span><strong id="netTvl">—</strong></div>
          <div class="net-stat"><span>Toplam çağrı</span><strong id="netCalls">—</strong></div>
        </div>
        <div class="feed-head">Canlı Aktivite Akışı</div>
        <div class="activity-feed" id="activityFeed">
          <div class="feed-item"><span class="feed-meta">Ağ dinleniyor…</span></div>
        </div>
      </aside>

      <main class="dashboard-main">
        <div class="welcome-bar">
          <div>
            <h2>Hoş geldiniz</h2>
            <p id="marketWelcome">Yatırım pazarı · canlı ajan operasyonları</p>
          </div>
          <div class="live-badge"><span class="live-dot"></span> CANLI</div>
        </div>

        <div class="stats-row">
          <div class="stat-card">
            <div class="stat-label">Aktif Ajan</div>
            <div class="stat-value emerald" id="statAgents">{agent_count}</div>
          </div>
          <div class="stat-card">
            <div class="stat-label">Toplam TVL</div>
            <div class="stat-value gold" id="statTvl">$0</div>
          </div>
          <div class="stat-card">
            <div class="stat-label">Ağ Getirisi</div>
            <div class="stat-value" id="statRevenue">$0</div>
          </div>
          <div class="stat-card">
            <div class="stat-label">Görev / dk</div>
            <div class="stat-value emerald" id="statTpm">—</div>
          </div>
        </div>

        <div class="agents-section-head">
          <h3>Canlı Ajanlar</h3>
          <div style="display:flex;gap:0.5rem;align-items:center">
            <span class="live-badge"><span class="live-dot"></span> <span id="liveDataLabel">{agent_count} düğüm</span></span>
            {'<button type="button" class="btn-trigger" onclick="triggerLiveRun()">▶ Görev Tetikle</button>' if not demo_mode else ''}
          </div>
        </div>
        <div class="grid" id="agentGrid">{card_html or '<p style="color:var(--muted)">Henüz ajan yok.</p>'}</div>
      </main>
    </div>
  </section>

  <!-- WALLET MODAL -->
  <div class="modal-overlay" id="walletModal" onclick="if(event.target===this)closeWalletModal()">
    <div class="modal" style="position:relative">
      <button class="modal-close" onclick="closeWalletModal()">×</button>
      <h2>Cüzdan Bağla</h2>
      <p>Devam etmek için Ethereum uyumlu cüzdan adresinizi girin. Üretimde MetaMask / WalletConnect entegrasyonu kullanılacaktır.</p>
      <input type="text" class="field" id="walletInput" placeholder="0x…" autocomplete="off" />
      <div class="modal-actions">
        <button class="btn-modal primary" onclick="connectWallet()">Bağlan ve Devam Et</button>
        <button class="btn-modal ghost" onclick="connectDemoWallet()">Demo Cüzdan Oluştur</button>
      </div>
    </div>
  </div>

  <div class="toast" id="toast"></div>

  <script>
    const WALLET_KEY = 'oam_hub_wallet';

    function getWallet() {{ return localStorage.getItem(WALLET_KEY) || ''; }}

    function shortAddr(a) {{
      return a.length > 12 ? a.slice(0,6) + '…' + a.slice(-4) : a;
    }}

    const DEMO_MODE = {'true' if demo_mode else 'false'};

    function updateWalletUI() {{
      const w = getWallet();
      const connected = document.getElementById('walletConnected');
      const btn = document.getElementById('btnConnect');
      const landing = document.getElementById('landing');
      const market = document.getElementById('market');
      if (w) {{
        connected.classList.add('show');
        document.getElementById('walletShort').textContent = shortAddr(w);
        btn.style.display = 'none';
        landing.classList.add('hidden');
        market.classList.add('visible');
        document.getElementById('marketWelcome').textContent =
          'Portföy · ' + shortAddr(w) + ' · canlı ajan operasyonları';
        if (sessionStorage.getItem('hub_just_connected')) {{
          sessionStorage.removeItem('hub_just_connected');
          showMarketSplash();
        }} else {{
          startLiveFeed();
          if (DEMO_MODE) startProcessAnimation();
        }}
        window.scrollTo({{ top: 0, behavior: 'smooth' }});
      }} else {{
        connected.classList.remove('show');
        btn.style.display = 'block';
        landing.classList.remove('hidden');
        market.classList.remove('visible');
        stopLiveFeed();
      }}
    }}

    let liveTimer = null;
    let processTimer = null;
    let liveSocket = null;
    let lastEventCount = 0;
    const agentNameMap = {{}};

    function showMarketSplash() {{
      const splash = document.getElementById('marketSplash');
      splash.classList.add('show');
      setTimeout(() => {{
        splash.classList.remove('show');
        startLiveFeed();
        if (DEMO_MODE) startProcessAnimation();
      }}, 1600);
    }}

    function stopLiveFeed() {{
      if (liveTimer) clearInterval(liveTimer);
      if (processTimer) clearInterval(processTimer);
      if (liveSocket) {{ liveSocket.close(); liveSocket = null; }}
      liveTimer = null; processTimer = null;
    }}

    function startLiveFeed() {{
      if (!DEMO_MODE && window.WebSocket) {{
        try {{
          const proto = location.protocol === 'https:' ? 'wss:' : 'ws:';
          liveSocket = new WebSocket(proto + '//' + location.host + '/hub/ws/live');
          liveSocket.onmessage = (ev) => {{
            const data = JSON.parse(ev.data);
            applyLiveSnapshot(data);
          }};
          liveSocket.onerror = () => {{ liveSocket = null; pollLiveFallback(); }};
          return;
        }} catch (_) {{}}
      }}
      pollLiveFallback();
    }}

    function pollLiveFallback() {{
      refreshLive();
      liveTimer = setInterval(refreshLive, 4000);
    }}

    function applyLiveSnapshot(data) {{
      updateNetworkStats(data.network);
      updateActivityFeed(data.activity_feed);
      updateAgentCards(data.agents);
      const label = document.getElementById('liveDataLabel');
      if (label && data.network) {{
        label.textContent = data.network.reachable_agents + ' çevrimiçi · ' +
          (data.network.real_event_count || 0) + ' gerçek işlem';
      }}
    }}

    async function triggerLiveRun() {{
      try {{
        const res = await fetch('/hub/trigger-run', {{ method: 'POST' }});
        const data = await res.json();
        if (res.ok) {{
          showToast('Görev tamamlandı · ' + data.tasks + ' task');
          refreshLive();
        }} else {{
          showToast(data.detail || 'Görev başarısız', true);
        }}
      }} catch {{ showToast('Bağlantı hatası', true); }}
    }}

    async function refreshLive() {{
      try {{
        const res = await fetch('/hub/live');
        if (!res.ok) return;
        const data = await res.json();
        applyLiveSnapshot(data);
      }} catch (_) {{}}
    }}

    function updateNetworkStats(net) {{
      document.getElementById('netStatus').textContent = net.status === 'online' ? '● Online' : net.status;
      document.getElementById('netActive').textContent = net.active_agents + ' / ' + net.total_agents;
      document.getElementById('netTvl').textContent = '$' + net.total_tvl_usd.toLocaleString('tr-TR');
      document.getElementById('netCalls').textContent = formatNum(net.total_calls);
      document.getElementById('statAgents').textContent = net.active_agents;
      document.getElementById('statTvl').textContent = '$' + net.total_tvl_usd.toLocaleString('tr-TR', {{maximumFractionDigits:0}});
      document.getElementById('statRevenue').textContent = '$' + net.total_revenue_usd.toLocaleString('tr-TR', {{minimumFractionDigits:2}});
      const tpm = Math.max(1, Math.round(net.total_calls / 1440));
      document.getElementById('statTpm').textContent = '~' + tpm;
    }}

    function formatNum(n) {{
      if (n >= 1e6) return (n/1e6).toFixed(1) + 'M';
      if (n >= 1e3) return (n/1e3).toFixed(1) + 'K';
      return String(n);
    }}

    function updateActivityFeed(feed) {{
      const el = document.getElementById('activityFeed');
      if (!feed || !feed.length) {{
        el.innerHTML = '<div class="feed-item"><span class="feed-meta">Ajanlar hazır — görev bekleniyor</span></div>';
        return;
      }}
      const isNew = feed.length > lastEventCount;
      lastEventCount = feed.length;
      el.innerHTML = feed.slice(0, 12).map((item, i) => {{
        const name = agentNameMap[item.agent_id] || item.agent_id.split('.')[0];
        const cls = i === 0 && isNew ? 'feed-item new' : 'feed-item';
        const sim = item.simulated ? ' · <span style="color:#fbbf24">DEMO</span>' : '';
        const status = item.success ? '✓ görev tamamlandı' : '✗ hata';
        return `<div class="${{cls}}">
          <span class="feed-agent">${{name}}</span> · ${{status}}${{sim}}
          <div class="feed-meta">+$${{item.staking_usd?.toFixed(4) || item.gross_usd?.toFixed(4)}} staking · ${{Math.round(item.latency_ms)}}ms · ${{item.tx_hash?.slice(0,10)}}…</div>
        </div>`;
      }}).join('');
    }}

    function updateAgentCards(agents) {{
      agents.forEach(a => {{
        agentNameMap[a.agent_id] = a.display_name;
        const card = document.querySelector('[data-agent="' + a.agent_id + '"]');
        if (!card) return;
        const dot = card.querySelector('.status-dot');
        const text = card.querySelector('.status-text');
        const lat = card.querySelector('.status-latency');
        dot.className = 'status-dot ' + a.status;
        const labels = {{
          active: a.reachable ? 'Çevrimiçi · endpoint yanıt veriyor' : 'Kayıtlı · endpoint kapalı',
          standby: 'Kayıtlı · henüz görev yok',
          degraded: 'Düşük performans',
          offline: 'Çevrimdışı · ajan yanıt vermiyor',
        }};
        text.textContent = labels[a.status] || a.status;
        lat.textContent = a.latency_ms > 0 ? Math.round(a.latency_ms) + 'ms' : '';
        card.classList.toggle('is-live', a.status === 'active');
      }});
    }}

    function startProcessAnimation() {{
      const cards = Array.from(document.querySelectorAll('.agent-card'));
      if (!cards.length) return;
      let idx = 0;
      const tasks = [
        'data_fetcher → query pipeline',
        'synthesizer → risk özeti üretiliyor',
        'transform → şema normalizasyonu',
        'DAG node execute · proof-of-work',
        'mesh/run → capability match',
        'staking yield dağıtımı',
      ];
      processTimer = setInterval(() => {{
        cards.forEach(c => c.classList.remove('processing'));
        const card = cards[idx % cards.length];
        card.classList.add('processing');
        const taskEl = card.querySelector('[data-live-task]');
        if (taskEl) taskEl.textContent = '▸ ' + tasks[idx % tasks.length];
        const dot = card.querySelector('.status-dot');
        if (dot) {{ dot.classList.add('processing'); setTimeout(() => dot.classList.remove('processing'), 1400); }}
        idx++;
      }}, 2800);
    }}

    function openWalletModal() {{ document.getElementById('walletModal').classList.add('open'); }}
    function closeWalletModal() {{ document.getElementById('walletModal').classList.remove('open'); }}

    function connectWallet() {{
      const addr = document.getElementById('walletInput').value.trim();
      if (!addr.startsWith('0x') || addr.length < 10) {{
        showToast('Geçerli bir cüzdan adresi girin (0x…)', true); return;
      }}
      localStorage.setItem(WALLET_KEY, addr);
      closeWalletModal();
      sessionStorage.setItem('hub_just_connected', '1');
      updateWalletUI();
      showToast('Cüzdan bağlandı · ' + shortAddr(addr));
    }}

    function connectDemoWallet() {{
      const demo = '0x' + Array.from({{length:40}}, () => Math.floor(Math.random()*16).toString(16)).join('');
      localStorage.setItem(WALLET_KEY, demo);
      closeWalletModal();
      updateWalletUI();
      showToast('Demo cüzdan oluşturuldu');
    }}

    function disconnectWallet() {{
      localStorage.removeItem(WALLET_KEY);
      updateWalletUI();
      showToast('Cüzdan bağlantısı kesildi');
    }}

    function switchTab(btn) {{
      const card = btn.closest('.agent-card');
      card.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
      card.querySelectorAll('.tab-panel').forEach(p => p.classList.remove('active'));
      btn.classList.add('active');
      card.querySelector('[data-panel="' + btn.dataset.tab + '"]').classList.add('active');
    }}

    function showToast(msg, err) {{
      const t = document.getElementById('toast');
      t.textContent = msg;
      t.classList.toggle('error', !!err);
      t.classList.add('show');
      setTimeout(() => t.classList.remove('show'), 4000);
    }}

    async function stake(agentId, btn) {{
      const w = getWallet();
      const amount = parseFloat(btn.closest('.agent-card').querySelector('.amount').value);
      if (!w) {{ openWalletModal(); return; }}
      if (!amount) {{ showToast('USDC miktarı girin', true); return; }}
      btn.classList.add('loading');
      try {{
        const res = await fetch('/hub/stake', {{
          method: 'POST',
          headers: {{'Content-Type':'application/json'}},
          body: JSON.stringify({{ investor_id: w, agent_id: agentId, amount_usdc: amount }})
        }});
        const data = await res.json();
        if (res.ok) {{
          showToast('Stake başarılı · ' + data.shares?.toFixed(2) + ' pay');
          setTimeout(() => location.reload(), 1800);
        }} else {{
          showToast(data.detail || 'Hata', true);
          btn.classList.remove('loading');
        }}
      }} catch {{ showToast('Sunucuya bağlanılamadı — gateway çalışıyor mu?', true); btn.classList.remove('loading'); }}
    }}

    async function claim(agentId, btn) {{
      const w = getWallet();
      if (!w) {{ openWalletModal(); return; }}
      try {{
        const res = await fetch('/hub/claim', {{
          method: 'POST',
          headers: {{'Content-Type':'application/json'}},
          body: JSON.stringify({{ investor_id: w, agent_id: agentId }})
        }});
        const data = await res.json();
        showToast(res.ok ? 'Ödül: $' + data.claimed_usdc?.toFixed(4) : (data.detail || 'Hata'), !res.ok);
      }} catch {{ showToast('Sunucuya bağlanılamadı', true); }}
    }}

    updateWalletUI();
    console.info('[The Hub] build:', '{_esc(build)}');
  </script>
</body>
</html>"""
