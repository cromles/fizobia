from __future__ import annotations

import html
from typing import Any, List

from app.investment.schemas import AgentIdentityCard, RevenueSplitConfig


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


def _esc(text: str) -> str:
    return html.escape(text)


def _render_agent_card(card: AgentIdentityCard, index: int) -> str:
    p = card.profile
    h = card.health
    f = card.finance
    pool = card.pool
    success_pct = h.success_rate * 100
    delay = 0.12 + index * 0.1
    contract = _esc(pool.contract_address or "—")
    agent_id = _esc(p.agent_id)

    return f"""
    <article class="agent-card reveal" style="--delay:{delay}s" data-agent="{agent_id}">
      <div class="card-glow"></div>
      <div class="card-shine"></div>
      <header class="card-header">
        <div class="agent-identity">
          <div class="avatar-ring class-{p.agent_class.value}">
            <span class="avatar-letter">{_esc(p.display_name[0])}</span>
          </div>
          <div>
            <h2 class="agent-name">{_esc(p.display_name)}</h2>
            <span class="badge class-{p.agent_class.value}">{_class_label(p.agent_class.value)}</span>
          </div>
        </div>
        <div class="token-pill">
          <span class="token-dot"></span>
          {_esc(p.token_symbol)}
        </div>
      </header>

      <p class="mission">{_esc(p.mission)}</p>

      <div class="metrics-grid">
        <div class="metric glass">
          <span class="label">Başarı Oranı</span>
          <span class="value green counter" data-target="{success_pct:.1f}" data-prefix="%" data-decimals="1">0</span>
          <div class="metric-bar"><div class="metric-fill green-fill" style="width:{success_pct}%"></div></div>
        </div>
        <div class="metric glass">
          <span class="label">Ort. Yanıt</span>
          <span class="value counter" data-target="{h.avg_latency_ms:.0f}" data-suffix="ms" data-decimals="0">0</span>
        </div>
        <div class="metric glass">
          <span class="label">Toplam Çağrı</span>
          <span class="value">{_format_number(h.total_calls)}</span>
        </div>
        <div class="metric glass">
          <span class="label">Token Fiyatı</span>
          <span class="value gold counter" data-target="{f.token_price_usdc:.4f}" data-prefix="$" data-decimals="4">0</span>
        </div>
      </div>

      <div class="finance-panel glass">
        <div class="finance-head">
          <h3><span class="live-dot"></span> Canlı Finansal Rapor</h3>
          <span class="on-chain">On-Chain</span>
        </div>
        <div class="finance-row">
          <span>Toplam Ağ Getirisi</span>
          <strong class="counter" data-target="{f.total_revenue_usd:.2f}" data-prefix="$" data-decimals="2">0</strong>
        </div>
        <div class="finance-row">
          <span>Son 24s Hacim</span>
          <strong class="counter" data-target="{f.volume_24h_usd:.2f}" data-prefix="$" data-decimals="2">0</strong>
        </div>
        <div class="finance-row highlight">
          <span>Tahmini APY</span>
          <strong class="apy counter pulse" data-target="{f.estimated_apy:.1f}" data-prefix="%" data-decimals="1">0</strong>
        </div>
        <div class="finance-row">
          <span>Havuz TVL</span>
          <strong class="counter" data-target="{f.staking_pool_tvl_usd:.2f}" data-prefix="$" data-decimals="2">0</strong>
        </div>
        <div class="contract">
          <span>Sözleşme</span>
          <code title="{contract}">{contract[:10]}…{contract[-6:] if len(contract) > 16 else contract}</code>
        </div>
      </div>

      <div class="stake-panel">
        <label class="field-label">Cüzdan</label>
        <input type="text" class="wallet field" placeholder="0x…" autocomplete="off" />
        <label class="field-label">Miktar (USDC)</label>
        <div class="stake-actions">
          <input type="number" class="amount field" placeholder="100" min="1" step="1" />
          <button class="btn-primary" onclick="stake('{agent_id}', this)">
            <span class="btn-text">Stake</span>
            <span class="btn-loader"></span>
          </button>
          <button class="btn-ghost" onclick="claim('{agent_id}', this)">Ödül Al</button>
        </div>
        <p class="stake-hint">Bonding curve · {_esc(p.token_symbol)} dinamik fiyatlandırma</p>
      </div>
    </article>"""


def render_hub_dashboard(cards: List[AgentIdentityCard], split: RevenueSplitConfig) -> str:
    card_html = "".join(_render_agent_card(c, i) for i, c in enumerate(cards))
    agent_count = len(cards)
    staking_pct = split.staking_share * 100
    platform_pct = split.platform_share * 100
    operator_pct = split.operator_share * 100

    empty_state = """
    <div class="empty-state reveal">
      <div class="empty-icon">◇</div>
      <p>Henüz yatırıma açık ajan yok.</p>
    </div>"""

    return f"""<!DOCTYPE html>
<html lang="tr">
<head>
  <meta charset="utf-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1"/>
  <title>The Hub — Veridag</title>
  <link rel="preconnect" href="https://fonts.googleapis.com"/>
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin/>
  <link href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,400;0,600;1,400&family=Manrope:wght@300;400;500;600;700&display=swap" rel="stylesheet"/>
  <style>
    :root {{
      --bg-deep: #050508;
      --bg-surface: #0c0c12;
      --glass: rgba(18, 18, 28, 0.55);
      --glass-border: rgba(255, 255, 255, 0.06);
      --glass-hover: rgba(255, 255, 255, 0.09);
      --text: #f0ece4;
      --text-muted: rgba(240, 236, 228, 0.45);
      --gold: #c9a962;
      --gold-light: #e8d5a3;
      --gold-dim: rgba(201, 169, 98, 0.25);
      --emerald: #5ee4a8;
      --emerald-dim: rgba(94, 228, 168, 0.15);
      --violet: #9b8cff;
      --cyan: #6ecfff;
      --ease-out: cubic-bezier(0.16, 1, 0.3, 1);
      --ease-spring: cubic-bezier(0.34, 1.56, 0.64, 1);
    }}

    *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}

    html {{ scroll-behavior: smooth; }}

    body {{
      font-family: 'Manrope', system-ui, sans-serif;
      background: var(--bg-deep);
      color: var(--text);
      min-height: 100vh;
      overflow-x: hidden;
      -webkit-font-smoothing: antialiased;
    }}

    /* Ambient background */
    .ambient {{
      position: fixed; inset: 0; z-index: 0; pointer-events: none; overflow: hidden;
    }}
    .orb {{
      position: absolute; border-radius: 50%; filter: blur(100px); opacity: 0.35;
      animation: drift 20s ease-in-out infinite alternate;
    }}
    .orb-1 {{ width: 600px; height: 600px; background: #1a1530; top: -15%; left: -10%; }}
    .orb-2 {{ width: 500px; height: 500px; background: #0d2818; bottom: -20%; right: -5%; animation-delay: -7s; }}
    .orb-3 {{ width: 350px; height: 350px; background: #2a1f0a; top: 40%; left: 50%; opacity: 0.2; animation-delay: -12s; }}
    .grid-noise {{
      position: absolute; inset: 0;
      background-image:
        linear-gradient(rgba(255,255,255,0.02) 1px, transparent 1px),
        linear-gradient(90deg, rgba(255,255,255,0.02) 1px, transparent 1px);
      background-size: 64px 64px;
      mask-image: radial-gradient(ellipse 80% 60% at 50% 30%, black, transparent);
    }}
    @keyframes drift {{
      from {{ transform: translate(0, 0) scale(1); }}
      to {{ transform: translate(40px, 30px) scale(1.08); }}
    }}

    /* Hero */
    .hero {{
      position: relative; z-index: 1;
      padding: 3rem 2.5rem 2rem;
      max-width: 1440px; margin: 0 auto;
    }}
    .hero-top {{
      display: flex; justify-content: space-between; align-items: flex-start;
      flex-wrap: wrap; gap: 1.5rem;
      animation: fadeDown 1s var(--ease-out) both;
    }}
    .brand {{ display: flex; flex-direction: column; gap: 0.5rem; }}
    .brand-tag {{
      font-size: 0.7rem; letter-spacing: 0.35em; text-transform: uppercase;
      color: var(--gold); font-weight: 600;
    }}
    .hero h1 {{
      font-family: 'Cormorant Garamond', Georgia, serif;
      font-size: clamp(2.4rem, 5vw, 3.6rem);
      font-weight: 400; line-height: 1.1;
      background: linear-gradient(135deg, var(--text) 0%, var(--gold-light) 50%, var(--text-muted) 100%);
      -webkit-background-clip: text; -webkit-text-fill-color: transparent;
      background-clip: text;
    }}
    .hero-sub {{
      color: var(--text-muted); font-size: 0.95rem; font-weight: 300;
      max-width: 480px; line-height: 1.6; margin-top: 0.25rem;
    }}
    .hero-stats {{
      display: flex; gap: 2rem; align-items: center;
    }}
    .hero-stat {{ text-align: right; }}
    .hero-stat .num {{
      font-family: 'Cormorant Garamond', serif;
      font-size: 2rem; color: var(--gold-light); line-height: 1;
    }}
    .hero-stat .lbl {{ font-size: 0.7rem; color: var(--text-muted); letter-spacing: 0.1em; text-transform: uppercase; }}

    .split-bar {{
      display: flex; gap: 0.75rem; margin-top: 2rem; flex-wrap: wrap;
      animation: fadeDown 1s var(--ease-out) 0.15s both;
    }}
    .split-chip {{
      display: flex; align-items: center; gap: 0.5rem;
      padding: 0.55rem 1.1rem;
      background: var(--glass);
      border: 1px solid var(--glass-border);
      border-radius: 100px;
      font-size: 0.8rem; color: var(--text-muted);
      backdrop-filter: blur(12px);
      transition: border-color 0.4s, transform 0.4s var(--ease-out);
    }}
    .split-chip:hover {{ border-color: var(--gold-dim); transform: translateY(-2px); }}
    .split-chip strong {{ color: var(--gold-light); font-weight: 600; }}
    .split-chip .dot {{ width: 6px; height: 6px; border-radius: 50%; background: var(--gold); opacity: 0.8; }}

    nav {{
      margin-top: 1.5rem;
      display: flex; gap: 1.5rem;
      animation: fadeDown 1s var(--ease-out) 0.25s both;
    }}
    nav a {{
      color: var(--text-muted); text-decoration: none; font-size: 0.8rem;
      letter-spacing: 0.05em; transition: color 0.3s;
      position: relative;
    }}
    nav a::after {{
      content: ''; position: absolute; bottom: -4px; left: 0; width: 0; height: 1px;
      background: var(--gold); transition: width 0.4s var(--ease-out);
    }}
    nav a:hover {{ color: var(--gold-light); }}
    nav a:hover::after {{ width: 100%; }}

    /* Grid */
    .container {{
      position: relative; z-index: 1;
      max-width: 1440px; margin: 0 auto;
      padding: 1rem 2.5rem 4rem;
    }}
    .grid {{
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(380px, 1fr));
      gap: 1.75rem;
    }}

    /* Cards */
    .agent-card {{
      position: relative;
      background: var(--glass);
      border: 1px solid var(--glass-border);
      border-radius: 20px;
      padding: 1.5rem;
      backdrop-filter: blur(20px);
      overflow: hidden;
      transition: transform 0.5s var(--ease-out), border-color 0.5s, box-shadow 0.5s;
    }}
    .agent-card:hover {{
      transform: translateY(-6px);
      border-color: rgba(201, 169, 98, 0.2);
      box-shadow: 0 24px 80px rgba(0,0,0,0.5), 0 0 0 1px rgba(201,169,98,0.08);
    }}
    .card-glow {{
      position: absolute; top: -50%; left: -50%; width: 200%; height: 200%;
      background: radial-gradient(circle at 30% 20%, rgba(201,169,98,0.06), transparent 50%);
      opacity: 0; transition: opacity 0.6s; pointer-events: none;
    }}
    .agent-card:hover .card-glow {{ opacity: 1; }}
    .card-shine {{
      position: absolute; top: 0; left: -100%; width: 60%; height: 100%;
      background: linear-gradient(90deg, transparent, rgba(255,255,255,0.03), transparent);
      transform: skewX(-20deg);
      transition: left 0.8s var(--ease-out);
      pointer-events: none;
    }}
    .agent-card:hover .card-shine {{ left: 150%; }}

    .reveal {{
      opacity: 0; transform: translateY(32px);
      animation: revealUp 0.9s var(--ease-out) var(--delay, 0s) forwards;
    }}
    @keyframes revealUp {{
      to {{ opacity: 1; transform: translateY(0); }}
    }}
    @keyframes fadeDown {{
      from {{ opacity: 0; transform: translateY(-16px); }}
      to {{ opacity: 1; transform: translateY(0); }}
    }}

    .card-header {{
      display: flex; justify-content: space-between; align-items: flex-start;
      margin-bottom: 1rem; position: relative; z-index: 1;
    }}
    .agent-identity {{ display: flex; gap: 0.85rem; align-items: center; }}
    .avatar-ring {{
      width: 44px; height: 44px; border-radius: 14px;
      display: flex; align-items: center; justify-content: center;
      border: 1px solid var(--glass-border);
      background: rgba(255,255,255,0.03);
      transition: transform 0.4s var(--ease-spring);
    }}
    .agent-card:hover .avatar-ring {{ transform: scale(1.05) rotate(-3deg); }}
    .avatar-letter {{
      font-family: 'Cormorant Garamond', serif;
      font-size: 1.3rem; color: var(--gold-light);
    }}
    .class-fetcher .avatar-letter {{ color: var(--emerald); }}
    .class-synthesizer .avatar-letter {{ color: #f0c674; }}
    .class-transformer .avatar-letter {{ color: var(--cyan); }}

    .agent-name {{
      font-family: 'Cormorant Garamond', serif;
      font-size: 1.35rem; font-weight: 600; letter-spacing: 0.02em;
    }}
    .badge {{
      display: inline-block; margin-top: 0.25rem;
      padding: 0.2rem 0.55rem; border-radius: 6px;
      font-size: 0.65rem; font-weight: 600; letter-spacing: 0.08em; text-transform: uppercase;
    }}
    .class-fetcher {{ background: var(--emerald-dim); color: var(--emerald); }}
    .class-synthesizer {{ background: rgba(240,198,116,0.12); color: #f0c674; }}
    .class-transformer {{ background: rgba(110,207,255,0.12); color: var(--cyan); }}
    .class-analyst {{ background: rgba(155,140,255,0.12); color: var(--violet); }}
    .class-validator {{ background: rgba(201,169,98,0.12); color: var(--gold); }}

    .token-pill {{
      display: flex; align-items: center; gap: 0.4rem;
      padding: 0.35rem 0.75rem; border-radius: 100px;
      background: rgba(201,169,98,0.08); border: 1px solid var(--gold-dim);
      font-family: 'Manrope', monospace; font-size: 0.75rem; font-weight: 600;
      color: var(--gold-light); letter-spacing: 0.05em;
    }}
    .token-dot {{
      width: 5px; height: 5px; border-radius: 50%; background: var(--gold);
      animation: pulse 2s ease-in-out infinite;
    }}
    @keyframes pulse {{
      0%, 100% {{ opacity: 1; transform: scale(1); }}
      50% {{ opacity: 0.5; transform: scale(0.85); }}
    }}

    .mission {{
      color: var(--text-muted); font-size: 0.85rem; line-height: 1.65;
      font-weight: 300; min-height: 2.8rem; margin-bottom: 1.1rem;
      position: relative; z-index: 1;
    }}

    .glass {{
      background: rgba(0,0,0,0.25);
      border: 1px solid rgba(255,255,255,0.04);
      border-radius: 12px;
    }}

    .metrics-grid {{
      display: grid; grid-template-columns: 1fr 1fr; gap: 0.65rem;
      margin-bottom: 1rem; position: relative; z-index: 1;
    }}
    .metric {{
      padding: 0.75rem; transition: background 0.3s, border-color 0.3s;
    }}
    .metric:hover {{ background: rgba(255,255,255,0.04); border-color: rgba(255,255,255,0.08); }}
    .metric .label {{
      display: block; font-size: 0.65rem; color: var(--text-muted);
      letter-spacing: 0.12em; text-transform: uppercase; margin-bottom: 0.35rem;
    }}
    .metric .value {{
      font-size: 1.15rem; font-weight: 600; font-variant-numeric: tabular-nums;
    }}
    .metric .value.green {{ color: var(--emerald); }}
    .metric .value.gold {{ color: var(--gold-light); }}
    .metric-bar {{
      height: 2px; background: rgba(255,255,255,0.06); border-radius: 2px;
      margin-top: 0.5rem; overflow: hidden;
    }}
    .metric-fill {{
      height: 100%; border-radius: 2px;
      transform: scaleX(0); transform-origin: left;
      animation: barGrow 1.2s var(--ease-out) 0.6s forwards;
    }}
    .green-fill {{ background: linear-gradient(90deg, var(--emerald), #3dd68c); }}
    @keyframes barGrow {{ to {{ transform: scaleX(1); }} }}

    .finance-panel {{
      padding: 1rem; margin-bottom: 1rem; position: relative; z-index: 1;
    }}
    .finance-head {{
      display: flex; justify-content: space-between; align-items: center;
      margin-bottom: 0.75rem;
    }}
    .finance-head h3 {{
      font-size: 0.65rem; letter-spacing: 0.15em; text-transform: uppercase;
      color: var(--text-muted); font-weight: 600;
      display: flex; align-items: center; gap: 0.5rem;
    }}
    .live-dot {{
      width: 6px; height: 6px; border-radius: 50%; background: var(--emerald);
      box-shadow: 0 0 8px var(--emerald);
      animation: livePulse 1.5s ease-in-out infinite;
    }}
    @keyframes livePulse {{
      0%, 100% {{ box-shadow: 0 0 4px var(--emerald); }}
      50% {{ box-shadow: 0 0 12px var(--emerald), 0 0 20px rgba(94,228,168,0.3); }}
    }}
    .on-chain {{
      font-size: 0.6rem; letter-spacing: 0.1em; text-transform: uppercase;
      color: var(--gold); opacity: 0.7; padding: 0.2rem 0.5rem;
      border: 1px solid var(--gold-dim); border-radius: 4px;
    }}
    .finance-row {{
      display: flex; justify-content: space-between; align-items: center;
      padding: 0.45rem 0; font-size: 0.85rem; color: var(--text-muted);
      border-bottom: 1px solid rgba(255,255,255,0.03);
      transition: color 0.3s;
    }}
    .finance-row:hover {{ color: var(--text); }}
    .finance-row strong {{
      color: var(--text); font-weight: 600; font-variant-numeric: tabular-nums;
    }}
    .finance-row.highlight {{
      border-bottom: none; padding-top: 0.65rem; margin-top: 0.25rem;
      border-top: 1px solid rgba(201,169,98,0.15);
    }}
    .apy {{
      font-family: 'Cormorant Garamond', serif;
      font-size: 1.5rem !important; color: var(--emerald) !important;
    }}
    .apy.pulse {{ animation: apyGlow 3s ease-in-out infinite; }}
    @keyframes apyGlow {{
      0%, 100% {{ text-shadow: 0 0 20px rgba(94,228,168,0.2); }}
      50% {{ text-shadow: 0 0 30px rgba(94,228,168,0.45); }}
    }}
    .contract {{
      margin-top: 0.75rem; display: flex; justify-content: space-between;
      font-size: 0.7rem; color: var(--text-muted);
    }}
    .contract code {{
      color: var(--cyan); font-size: 0.68rem; cursor: default;
      transition: color 0.3s;
    }}
    .contract code:hover {{ color: var(--gold-light); }}

    /* Stake */
    .stake-panel {{ position: relative; z-index: 1; }}
    .field-label {{
      display: block; font-size: 0.65rem; letter-spacing: 0.12em;
      text-transform: uppercase; color: var(--text-muted); margin-bottom: 0.35rem;
    }}
    .field {{
      width: 100%; padding: 0.7rem 0.9rem; margin-bottom: 0.75rem;
      border-radius: 10px; border: 1px solid rgba(255,255,255,0.06);
      background: rgba(0,0,0,0.35); color: var(--text);
      font-family: inherit; font-size: 0.85rem;
      transition: border-color 0.3s, box-shadow 0.3s, background 0.3s;
      outline: none;
    }}
    .field:focus {{
      border-color: var(--gold-dim);
      box-shadow: 0 0 0 3px rgba(201,169,98,0.1);
      background: rgba(0,0,0,0.5);
    }}
    .field::placeholder {{ color: rgba(240,236,228,0.2); }}
    .stake-actions {{ display: flex; gap: 0.5rem; }}
    .btn-primary, .btn-ghost {{
      flex: 1; padding: 0.7rem 1rem; border-radius: 10px;
      font-family: inherit; font-size: 0.8rem; font-weight: 600;
      letter-spacing: 0.05em; cursor: pointer;
      transition: transform 0.3s var(--ease-spring), box-shadow 0.3s, opacity 0.3s;
      position: relative; overflow: hidden;
    }}
    .btn-primary {{
      background: linear-gradient(135deg, var(--gold) 0%, #a88b4a 100%);
      color: #0a0806; border: none;
      box-shadow: 0 4px 20px rgba(201,169,98,0.25);
    }}
    .btn-primary:hover {{
      transform: translateY(-2px);
      box-shadow: 0 8px 30px rgba(201,169,98,0.35);
    }}
    .btn-primary:active {{ transform: translateY(0); }}
    .btn-primary.loading {{ pointer-events: none; opacity: 0.7; }}
    .btn-primary.loading .btn-text {{ opacity: 0; }}
    .btn-primary.loading .btn-loader {{
      display: block; position: absolute; inset: 0;
      margin: auto; width: 18px; height: 18px;
      border: 2px solid rgba(10,8,6,0.3); border-top-color: #0a0806;
      border-radius: 50%; animation: spin 0.7s linear infinite;
    }}
    .btn-loader {{ display: none; }}
    @keyframes spin {{ to {{ transform: rotate(360deg); }} }}
    .btn-ghost {{
      background: transparent; color: var(--text-muted);
      border: 1px solid rgba(255,255,255,0.08);
    }}
    .btn-ghost:hover {{
      border-color: var(--gold-dim); color: var(--gold-light);
      background: rgba(201,169,98,0.05);
    }}
    .stake-hint {{
      font-size: 0.7rem; color: var(--text-muted); margin-top: 0.65rem;
      font-weight: 300; opacity: 0.7;
    }}

    .empty-state {{
      grid-column: 1 / -1; text-align: center; padding: 4rem;
      color: var(--text-muted);
    }}
    .empty-icon {{ font-size: 2rem; color: var(--gold-dim); margin-bottom: 1rem; }}

    /* Toast */
    .toast {{
      position: fixed; bottom: 2rem; right: 2rem; z-index: 100;
      padding: 1rem 1.5rem; border-radius: 12px;
      background: rgba(18, 28, 22, 0.95);
      border: 1px solid rgba(94, 228, 168, 0.25);
      color: var(--emerald); font-size: 0.85rem;
      backdrop-filter: blur(16px);
      transform: translateY(120%); opacity: 0;
      transition: transform 0.5s var(--ease-spring), opacity 0.4s;
      box-shadow: 0 20px 60px rgba(0,0,0,0.5);
    }}
    .toast.show {{ transform: translateY(0); opacity: 1; }}
    .toast.error {{ border-color: rgba(255,100,100,0.3); color: #ff8a8a; }}

    @media (max-width: 768px) {{
      .hero {{ padding: 2rem 1.25rem 1.5rem; }}
      .container {{ padding: 1rem 1.25rem 3rem; }}
      .grid {{ grid-template-columns: 1fr; }}
      .hero-stats {{ display: none; }}
    }}
  </style>
</head>
<body>
  <div class="ambient">
    <div class="orb orb-1"></div>
    <div class="orb orb-2"></div>
    <div class="orb orb-3"></div>
    <div class="grid-noise"></div>
  </div>

  <header class="hero">
    <div class="hero-top">
      <div class="brand">
        <span class="brand-tag">Veridag · Open Agent Mesh</span>
        <h1>The Hub</h1>
        <p class="hero-sub">Token tabanlı staking · Bonding curve · Gerçek zamanlı kâr payı dağıtımı</p>
      </div>
      <div class="hero-stats">
        <div class="hero-stat">
          <div class="num">{agent_count}</div>
          <div class="lbl">Aktif Ajan</div>
        </div>
        <div class="hero-stat">
          <div class="num">OAM</div>
          <div class="lbl">Protokol</div>
        </div>
      </div>
    </div>
    <div class="split-bar">
      <span class="split-chip"><span class="dot"></span> Staking & Altyapı <strong>%{staking_pct:.0f}</strong></span>
      <span class="split-chip"><span class="dot"></span> Veridag Platform <strong>%{platform_pct:.0f}</strong></span>
      <span class="split-chip"><span class="dot"></span> Ajan Operatörü <strong>%{operator_pct:.0f}</strong></span>
    </div>
    <nav>
      <a href="/">← OAM Dashboard</a>
      <a href="/hub/agents">JSON API</a>
      <a href="/docs">API Docs</a>
    </nav>
  </header>

  <main class="container">
    <div class="grid">{card_html or empty_state}</div>
  </main>

  <div class="toast" id="toast"></div>

  <script>
    // Animated counters
    function animateCounter(el) {{
      const target = parseFloat(el.dataset.target);
      const prefix = el.dataset.prefix || '';
      const suffix = el.dataset.suffix || '';
      const decimals = parseInt(el.dataset.decimals || '0', 10);
      const duration = 1400;
      const start = performance.now();
      function tick(now) {{
        const t = Math.min((now - start) / duration, 1);
        const eased = 1 - Math.pow(1 - t, 4);
        const val = target * eased;
        el.textContent = prefix + val.toLocaleString('tr-TR', {{
          minimumFractionDigits: decimals,
          maximumFractionDigits: decimals
        }}) + suffix;
        if (t < 1) requestAnimationFrame(tick);
      }}
      requestAnimationFrame(tick);
    }}

    const observer = new IntersectionObserver((entries) => {{
      entries.forEach(e => {{
        if (e.isIntersecting) {{
          e.target.querySelectorAll('.counter').forEach(animateCounter);
          observer.unobserve(e.target);
        }}
      }});
    }}, {{ threshold: 0.2 }});

    document.querySelectorAll('.agent-card').forEach(card => observer.observe(card));

    // Toast
    function showToast(msg, isError) {{
      const t = document.getElementById('toast');
      t.textContent = msg;
      t.classList.toggle('error', !!isError);
      t.classList.add('show');
      setTimeout(() => t.classList.remove('show'), 4200);
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
      if (!investor_id || !amount) {{ showToast('Cüzdan ve miktar gerekli', true); return; }}
      btn.classList.add('loading');
      try {{
        const res = await fetch('/hub/stake', {{
          method: 'POST',
          headers: {{'Content-Type': 'application/json'}},
          body: JSON.stringify({{investor_id, agent_id: agentId, amount_usdc: amount}})
        }});
        const data = await res.json();
        if (res.ok) {{
          showToast(`Stake başarılı · ${{data.shares?.toFixed(2)}} pay`);
          setTimeout(() => location.reload(), 1800);
        }} else {{
          showToast(data.detail || 'İşlem başarısız', true);
          btn.classList.remove('loading');
        }}
      }} catch {{
        showToast('Ağ hatası', true);
        btn.classList.remove('loading');
      }}
    }}

    async function claim(agentId, btn) {{
      const investor_id = getWallet(btn);
      if (!investor_id) {{ showToast('Cüzdan adresi gerekli', true); return; }}
      btn.disabled = true;
      try {{
        const res = await fetch('/hub/claim', {{
          method: 'POST',
          headers: {{'Content-Type': 'application/json'}},
          body: JSON.stringify({{investor_id, agent_id: agentId}})
        }});
        const data = await res.json();
        showToast(res.ok ? `Ödül alındı · $${{data.claimed_usdc?.toFixed(4)}}` : (data.detail || 'Hata'), !res.ok);
      }} catch {{
        showToast('Ağ hatası', true);
      }}
      btn.disabled = false;
    }}

    // Subtle parallax on cards
    document.querySelectorAll('.agent-card').forEach(card => {{
      card.addEventListener('mousemove', (e) => {{
        const rect = card.getBoundingClientRect();
        const x = (e.clientX - rect.left) / rect.width - 0.5;
        const y = (e.clientY - rect.top) / rect.height - 0.5;
        card.style.transform = `translateY(-6px) perspective(800px) rotateX(${{-y * 4}}deg) rotateY(${{x * 4}}deg)`;
      }});
      card.addEventListener('mouseleave', () => {{
        card.style.transform = '';
      }});
    }});
  </script>
</body>
</html>"""
