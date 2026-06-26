def hub_styles(staking_pct: float, platform_pct: float, operator_pct: float) -> str:
    return f"""
:root {{
  --bg: #020204;
  --bg-2: #08080f;
  --surface: rgba(14,14,22,0.72);
  --surface-2: rgba(20,20,32,0.85);
  --border: rgba(255,255,255,0.06);
  --border-bright: rgba(0,255,163,0.22);
  --text: #f8fafc;
  --muted: #94a3b8;
  --dim: #64748b;
  --mint: #00ffa3;
  --mint-dim: rgba(0,255,163,0.12);
  --gold: #ffd166;
  --gold-dim: rgba(255,209,102,0.12);
  --cyan: #38bdf8;
  --danger: #fb7185;
  --ease: cubic-bezier(0.16, 1, 0.3, 1);
  --ease-bounce: cubic-bezier(0.34, 1.56, 0.64, 1);
  --radius: 20px;
  --nav-h: 64px;
  --split-stake: {staking_pct}%;
  --split-platform: {platform_pct}%;
  --split-operator: {operator_pct}%;
}}

*, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}
html {{ scroll-behavior: smooth; }}
body {{
  font-family: 'DM Sans', system-ui, sans-serif;
  background: var(--bg);
  color: var(--text);
  min-height: 100vh;
  overflow-x: hidden;
  -webkit-font-smoothing: antialiased;
}}

/* ── Canvas & ambient ── */
#mesh-canvas {{
  position: fixed; inset: 0; z-index: 0; pointer-events: none; opacity: 0.55;
}}
.ambient-gradient {{
  position: fixed; inset: 0; z-index: 0; pointer-events: none;
  background:
    radial-gradient(ellipse 80% 50% at 20% -10%, rgba(0,255,163,0.08), transparent 50%),
    radial-gradient(ellipse 60% 40% at 90% 100%, rgba(255,209,102,0.06), transparent 45%),
    radial-gradient(ellipse 50% 30% at 50% 50%, rgba(56,189,248,0.03), transparent 60%);
}}

/* ── Nav ── */
.nav {{
  position: fixed; top: 0; left: 0; right: 0; z-index: 200;
  height: var(--nav-h);
  display: flex; align-items: center; justify-content: space-between;
  padding: 0 1.5rem;
  background: rgba(2,2,4,0.75);
  backdrop-filter: blur(20px) saturate(1.4);
  border-bottom: 1px solid var(--border);
}}
.nav-brand {{
  display: flex; align-items: center; gap: 0.75rem;
}}
.nav-logo {{
  font-family: 'Syne', sans-serif;
  font-size: 1.25rem; font-weight: 800; letter-spacing: -0.02em;
  background: linear-gradient(135deg, var(--text), var(--mint));
  -webkit-background-clip: text; -webkit-text-fill-color: transparent;
}}
.nav-sub {{
  font-size: 0.7rem; color: var(--dim); letter-spacing: 0.12em; text-transform: uppercase;
}}
.nav-actions {{ display: flex; align-items: center; gap: 0.75rem; }}
.wallet-pill {{
  display: none; align-items: center; gap: 0.5rem;
  padding: 0.4rem 0.85rem; border-radius: 999px;
  background: var(--mint-dim); border: 1px solid var(--border-bright);
  font-size: 0.78rem; color: var(--mint); font-weight: 600;
}}
.wallet-pill.show {{ display: flex; animation: popIn 0.5s var(--ease-bounce); }}
.btn-nav {{
  padding: 0.55rem 1.25rem; border-radius: 999px; border: none; cursor: pointer;
  font-family: inherit; font-weight: 700; font-size: 0.8rem;
  background: linear-gradient(135deg, var(--mint), #00cc82);
  color: #001a0f;
  box-shadow: 0 0 30px rgba(0,255,163,0.25);
  transition: transform 0.3s var(--ease), box-shadow 0.3s;
}}
.btn-nav:hover {{ transform: translateY(-2px) scale(1.02); box-shadow: 0 0 50px rgba(0,255,163,0.4); }}
.btn-disconnect {{
  background: none; border: none; color: var(--dim); cursor: pointer; font-size: 0.7rem;
}}

.yield-ticker {{
  display: none;
  flex-direction: column;
  align-items: flex-end;
  padding: 0.25rem 0.75rem;
  border-radius: 10px;
  border: 1px solid rgba(255,209,102,0.25);
  background: rgba(255,209,102,0.06);
  line-height: 1.1;
}}
.yield-ticker.show {{ display: flex; }}
.yield-label {{
  font-size: 0.58rem;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: var(--gold);
  opacity: 0.85;
}}
.yield-value {{
  font-family: 'Syne', monospace;
  font-size: 0.95rem;
  font-weight: 700;
  color: var(--gold);
  font-variant-numeric: tabular-nums;
}}

/* ── Axium Terminal ── */
.terminal-shell {{ padding: 1.5rem 1.75rem 3rem; }}
.terminal-top {{
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 1rem;
  margin-bottom: 1.5rem;
  flex-wrap: wrap;
}}
.terminal-title {{
  font-family: 'Syne', sans-serif;
  font-size: 1.65rem;
  font-weight: 800;
  letter-spacing: -0.03em;
  background: linear-gradient(135deg, var(--text), var(--mint));
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}}
.terminal-sub {{ font-size: 0.82rem; color: var(--dim); margin-top: 0.25rem; }}
.terminal-tabs {{
  display: flex;
  gap: 0.35rem;
  padding: 0.25rem;
  border-radius: 999px;
  background: rgba(255,255,255,0.04);
  border: 1px solid var(--border);
}}
.terminal-tab {{
  border: none;
  background: transparent;
  color: var(--muted);
  font-family: inherit;
  font-size: 0.78rem;
  font-weight: 600;
  padding: 0.5rem 1.1rem;
  border-radius: 999px;
  cursor: pointer;
  transition: all 0.25s var(--ease);
}}
.terminal-tab.active {{
  background: linear-gradient(135deg, rgba(0,255,163,0.2), rgba(56,189,248,0.12));
  color: var(--mint);
  box-shadow: 0 0 20px rgba(0,255,163,0.15);
}}
.terminal-panel {{ display: none; animation: cardReveal 0.5s var(--ease) both; }}
.terminal-panel.active {{ display: block; }}

.zero-ui {{
  max-width: 920px;
  margin: 0 auto;
  padding: 2rem 0 1rem;
}}
.zero-ui-hint {{
  text-align: center;
  color: var(--dim);
  font-size: 0.88rem;
  margin-bottom: 1.25rem;
}}
.zero-ui-row {{
  display: flex;
  gap: 0.65rem;
  align-items: stretch;
}}
.zero-prompt {{
  flex: 1;
  border: 1px solid rgba(255,255,255,0.1);
  border-radius: 16px;
  background: rgba(0,0,0,0.45);
  color: var(--text);
  font: inherit;
  font-size: 1.05rem;
  padding: 1rem 1.25rem;
  box-shadow: inset 0 1px 0 rgba(255,255,255,0.04), 0 8px 40px rgba(0,0,0,0.35);
}}
.zero-prompt:focus {{
  outline: none;
  border-color: var(--border-bright);
  box-shadow: 0 0 0 3px rgba(0,255,163,0.12);
}}
.zero-submit {{ flex-shrink: 0; padding-left: 1.6rem; padding-right: 1.6rem; }}

.synapse-monitor {{
  margin-top: 1.5rem;
  border-radius: 14px;
  border: 1px solid rgba(0,255,163,0.15);
  background: rgba(0,8,6,0.85);
  overflow: hidden;
  min-height: 200px;
  max-height: 320px;
  display: flex;
  flex-direction: column;
}}
.synapse-monitor-label {{
  font-size: 0.62rem;
  letter-spacing: 0.16em;
  text-transform: uppercase;
  color: var(--mint);
  padding: 0.55rem 1rem;
  border-bottom: 1px solid rgba(0,255,163,0.1);
  background: rgba(0,255,163,0.04);
}}
.synapse-monitor-inner {{
  flex: 1;
  overflow-y: auto;
  padding: 0.85rem 1rem;
  font-family: ui-monospace, 'Cascadia Code', monospace;
  font-size: 0.78rem;
  line-height: 1.55;
  color: #6ee7b7;
  text-shadow: 0 0 8px rgba(0,255,163,0.35);
}}
.synapse-line {{
  opacity: 0;
  animation: synapseIn 0.35s ease forwards;
  margin-bottom: 0.35rem;
}}
.synapse-idle {{ color: var(--dim); font-style: italic; }}
@keyframes synapseIn {{
  from {{ opacity: 0; transform: translateX(-6px); }}
  to {{ opacity: 1; transform: none; }}
}}

.terminal-deliverable {{
  margin-top: 1.25rem;
  padding: 1.25rem 1.35rem;
  border-radius: 14px;
  border: 1px solid rgba(56,189,248,0.25);
  background: linear-gradient(145deg, rgba(56,189,248,0.08), rgba(0,0,0,0.5));
  font-size: 0.88rem;
  line-height: 1.6;
}}
.terminal-deliverable h4 {{
  font-family: 'Syne', sans-serif;
  color: var(--cyan);
  margin-bottom: 0.5rem;
}}
.compose-output {{
  white-space: pre-wrap;
  font-family: ui-monospace, monospace;
  font-size: 0.82rem;
  line-height: 1.55;
  color: var(--text);
  background: rgba(0,0,0,0.25);
  padding: 1rem;
  border-radius: 8px;
  border: 1px solid var(--border);
  max-height: 320px;
  overflow-y: auto;
}}

.leaderboard-section {{ margin: 1.25rem 0 1.75rem; }}
.leaderboard-head h3 {{
  font-family: 'Syne', sans-serif;
  font-size: 1.1rem;
  margin-bottom: 0.2rem;
}}
.leaderboard-sub {{ font-size: 0.75rem; color: var(--dim); }}
.dept-filter-bar {{
  display: flex; align-items: center; justify-content: space-between; gap: 0.75rem; flex-wrap: wrap;
  margin: 0.75rem 0 1rem;
}}
.dept-filter-label {{
  font-size: 0.7rem; font-weight: 700; text-transform: uppercase;
  letter-spacing: 0.06em; color: var(--dim);
}}
.lb-dept {{
  font-size: 0.72rem; color: var(--muted); padding: 0.15rem 0.45rem;
  border-radius: 4px; background: rgba(255,255,255,0.04);
}}
.leaderboard-table-wrap {{
  margin-top: 0.85rem;
  border-radius: 14px;
  border: 1px solid var(--border);
  overflow: auto;
  background: rgba(8,8,14,0.85);
}}
.leaderboard-table {{
  width: 100%;
  border-collapse: collapse;
  font-size: 0.8rem;
}}
.leaderboard-table th {{
  text-align: left;
  padding: 0.65rem 1rem;
  color: var(--dim);
  font-weight: 600;
  font-size: 0.68rem;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  border-bottom: 1px solid var(--border);
}}
.leaderboard-table td {{
  padding: 0.75rem 1rem;
  border-bottom: 1px solid rgba(255,255,255,0.04);
}}
.lb-rank {{ color: var(--dim); margin-right: 0.35rem; }}
.lb-token {{ font-size: 0.68rem; color: var(--dim); }}
.lb-mint {{ color: var(--mint); font-weight: 700; }}
.lb-up {{ color: var(--mint); font-size: 0.68rem; }}
.lb-down {{ color: var(--danger); font-size: 0.68rem; }}
.lb-stake {{
  border: 1px solid var(--border-bright);
  background: var(--mint-dim);
  color: var(--mint);
  border-radius: 8px;
  padding: 0.35rem 0.65rem;
  font-size: 0.72rem;
  font-weight: 700;
  cursor: pointer;
  font-family: inherit;
}}
.lb-empty {{ text-align: center; color: var(--dim); padding: 1.5rem !important; }}
.invest-section-title {{
  font-family: 'Syne', sans-serif;
  font-size: 1.05rem;
  margin-bottom: 0.5rem;
  color: var(--text);
}}
.invest-section-desc {{
  font-size: 0.82rem; color: var(--dim); line-height: 1.6; margin-bottom: 1rem; max-width: 72ch;
}}
.invest-section-spaced {{ margin-top: 2rem; }}

.invest-hero {{
  display: grid; grid-template-columns: 1.4fr 0.8fr; gap: 1.5rem; align-items: center;
  padding: 1.5rem; margin-bottom: 1.25rem; border-radius: calc(var(--radius) + 4px);
  background: linear-gradient(135deg, rgba(0,255,163,0.06), rgba(8,8,15,0.9));
  border: 1px solid var(--border-bright);
}}
.invest-kicker {{
  display: block; font-size: 0.68rem; letter-spacing: 0.14em; text-transform: uppercase;
  color: var(--mint); margin-bottom: 0.5rem;
}}
.invest-hero h3 {{
  font-family: 'Syne', sans-serif; font-size: clamp(1.25rem, 2.5vw, 1.65rem);
  font-weight: 800; line-height: 1.25; margin-bottom: 0.65rem;
}}
.invest-hero-copy p {{ color: var(--muted); line-height: 1.65; font-size: 0.88rem; }}
.invest-hero-copy strong {{ color: var(--mint); }}
.invest-split-bar {{ margin-bottom: 0.65rem; }}

.onchain-strip {{
  display: flex; align-items: center; gap: 0.75rem; flex-wrap: wrap;
  padding: 0.65rem 1rem; margin-bottom: 1rem; border-radius: 12px;
  background: rgba(0,0,0,0.35); border: 1px solid var(--border); font-size: 0.78rem;
}}
.onchain-strip.connected {{ border-color: var(--border-bright); background: rgba(0,255,163,0.06); }}
.onchain-dot {{
  width: 8px; height: 8px; border-radius: 50%; background: var(--dim); flex-shrink: 0;
}}
.onchain-strip.connected .onchain-dot {{
  background: var(--mint); box-shadow: 0 0 10px var(--mint); animation: livePulse 1.5s infinite;
}}
.onchain-chain {{ margin-left: auto; color: var(--dim); font-size: 0.72rem; }}

.portfolio-strip {{
  margin-bottom: 1.25rem; padding: 1rem 1.25rem; border-radius: 16px;
  background: var(--surface); border: 1px solid var(--border);
}}
.portfolio-empty {{ font-size: 0.82rem; color: var(--dim); text-align: center; padding: 0.5rem; }}
.portfolio-summary {{
  display: grid; grid-template-columns: repeat(3, 1fr); gap: 0.75rem; margin-bottom: 0.85rem;
}}
.portfolio-summary div {{
  padding: 0.65rem; border-radius: 10px; background: rgba(0,0,0,0.28); text-align: center;
}}
.portfolio-summary span {{ display: block; font-size: 0.62rem; color: var(--dim); text-transform: uppercase; }}
.portfolio-summary strong {{ font-family: 'Syne', sans-serif; font-size: 1.1rem; }}
.portfolio-summary strong.mint {{ color: var(--mint); }}
.portfolio-positions {{ display: flex; flex-direction: column; gap: 0.4rem; }}
.portfolio-pos {{
  display: grid; grid-template-columns: 1fr auto auto auto; gap: 0.75rem; align-items: center;
  padding: 0.5rem 0.65rem; border-radius: 8px; background: rgba(0,0,0,0.22); font-size: 0.78rem;
}}
.portfolio-pos-name {{ font-weight: 600; }}
.portfolio-pos-stake {{ color: var(--text); }}
.portfolio-pos-reward {{ color: var(--gold); font-weight: 600; }}
.portfolio-pos-btn {{
  border: 1px solid var(--border); background: transparent; color: var(--mint);
  border-radius: 6px; padding: 0.25rem 0.55rem; font-size: 0.68rem; cursor: pointer; font-family: inherit;
}}

.dept-insights {{ margin: 1.5rem 0; }}
.dept-insights-grid {{
  display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: 0.85rem;
}}
.dept-insight-card {{
  padding: 1.1rem; border-radius: 16px; background: var(--surface);
  border: 1px solid var(--border); transition: border-color 0.3s, transform 0.3s;
}}
.dept-insight-card:hover {{ border-color: var(--border-bright); transform: translateY(-2px); }}
.dept-insight-card.dept-hidden {{ display: none; }}
.dept-insight-kicker {{
  font-size: 0.62rem; letter-spacing: 0.1em; text-transform: uppercase; color: var(--cyan);
}}
.dept-insight-card h4 {{
  font-family: 'Syne', sans-serif; font-size: 0.95rem; margin: 0.35rem 0 0.5rem;
}}
.dept-insight-card p {{ font-size: 0.78rem; color: var(--muted); line-height: 1.55; margin-bottom: 0.65rem; }}
.dept-insight-hint {{ display: block; font-size: 0.72rem; color: var(--gold); margin-bottom: 0.35rem; }}
.dept-insight-count {{ font-size: 0.68rem; color: var(--dim); }}

.dept-agent-groups {{ display: flex; flex-direction: column; gap: 2rem; }}
.dept-agent-group {{ }}
.dept-group-head {{
  display: flex; justify-content: space-between; align-items: flex-start; gap: 1rem;
  margin-bottom: 1rem; padding-bottom: 0.75rem; border-bottom: 1px solid var(--border);
}}
.dept-group-head h4 {{
  font-family: 'Syne', sans-serif; font-size: 1.05rem; margin-bottom: 0.25rem;
}}
.dept-group-head p {{ font-size: 0.78rem; color: var(--dim); line-height: 1.5; max-width: 55ch; }}
.dept-invest-hint {{
  flex-shrink: 0; font-size: 0.72rem; color: var(--gold); padding: 0.4rem 0.75rem;
  border-radius: 999px; background: rgba(255,209,102,0.08); border: 1px solid rgba(255,209,102,0.2);
}}
.dept-grid {{ grid-template-columns: repeat(auto-fill, minmax(320px, 1fr)); }}

.lb-agent-link {{
  background: none; border: none; color: var(--text); font-weight: 700; font-family: inherit;
  font-size: inherit; cursor: pointer; padding: 0; text-align: left;
}}
.lb-agent-link:hover {{ color: var(--mint); }}
.lb-tier {{
  font-size: 0.68rem; padding: 0.15rem 0.45rem; border-radius: 6px; font-weight: 600;
}}
.tier-probation {{ background: rgba(100,116,139,0.2); color: var(--dim); }}
.tier-active {{ background: var(--mint-dim); color: var(--mint); }}
.tier-core {{ background: rgba(255,209,102,0.15); color: var(--gold); }}
.tier-culled {{ background: rgba(251,113,133,0.12); color: var(--danger); }}
.lb-apy {{ color: var(--mint); font-weight: 700; }}
.lb-row:hover {{ background: rgba(0,255,163,0.03); }}

.agent-detail-overlay .agent-detail-modal {{
  max-width: 560px; max-height: 90vh; overflow-y: auto;
}}
.agent-detail-loading, .agent-detail-error {{
  text-align: center; color: var(--dim); padding: 2rem 1rem;
}}
.agent-detail-header {{ margin-bottom: 1rem; }}
.agent-detail-class {{
  font-size: 0.65rem; letter-spacing: 0.12em; text-transform: uppercase; color: var(--cyan);
}}
.agent-detail-header h2 {{
  font-family: 'Syne', sans-serif; font-size: 1.5rem; margin: 0.35rem 0;
}}
.agent-detail-mission {{ color: var(--muted); font-size: 0.88rem; line-height: 1.55; }}
.agent-detail-tags {{ display: flex; gap: 0.4rem; margin-top: 0.65rem; flex-wrap: wrap; }}
.agent-detail-desc {{
  font-size: 0.85rem; color: var(--muted); line-height: 1.65; margin-bottom: 1rem;
}}
.agent-detail-metrics {{
  display: grid; grid-template-columns: repeat(3, 1fr); gap: 0.5rem; margin-bottom: 1rem;
}}
.agent-detail-metrics div {{
  padding: 0.6rem; border-radius: 10px; background: rgba(0,0,0,0.28); text-align: center;
}}
.agent-detail-metrics span {{ display: block; font-size: 0.6rem; color: var(--dim); text-transform: uppercase; }}
.agent-detail-metrics strong {{ font-family: 'Syne', sans-serif; font-size: 1rem; }}
.agent-detail-metrics strong.mint {{ color: var(--mint); }}
.agent-detail-thesis, .agent-detail-usecases, .agent-detail-covers {{
  margin-bottom: 0.85rem; font-size: 0.82rem; line-height: 1.6;
}}
.agent-detail-thesis strong, .agent-detail-usecases strong, .agent-detail-covers strong {{
  display: block; color: var(--gold); margin-bottom: 0.35rem; font-size: 0.72rem;
  text-transform: uppercase; letter-spacing: 0.06em;
}}
.agent-detail-usecases ul {{ list-style: none; display: flex; flex-wrap: wrap; gap: 0.35rem; }}
.agent-detail-usecases li {{
  font-size: 0.72rem; padding: 0.25rem 0.55rem; border-radius: 6px;
  background: rgba(255,255,255,0.04); border: 1px solid var(--border);
}}
.agent-detail-pool {{
  display: flex; gap: 1rem; flex-wrap: wrap; font-size: 0.75rem; color: var(--dim);
  margin-bottom: 1rem; padding: 0.65rem; border-radius: 8px; background: rgba(0,0,0,0.2);
}}

.stats-compact {{ margin-bottom: 0.5rem; }}
.terminal-advanced {{
  margin-top: 1.5rem;
  font-size: 0.82rem;
  color: var(--dim);
}}
.mesh-proof-compact {{
  margin-top: 0.75rem;
  padding: 1rem !important;
  grid-template-columns: 1fr auto !important;
}}
.worker-card.highlight-stake {{
  outline: 2px solid var(--mint);
  box-shadow: 0 0 30px rgba(0,255,163,0.2);
}}
body.arena-frozen .zero-ui-row {{ opacity: 0.55; pointer-events: none; }}

/* ── Banners ── */
.top-banner {{
  position: fixed; top: var(--nav-h); left: 0; right: 0; z-index: 190;
  padding: 0.5rem 1rem; text-align: center; font-size: 0.75rem; font-weight: 600;
  letter-spacing: 0.02em;
}}
.banner-live {{
  background: linear-gradient(90deg, rgba(0,255,163,0.12), rgba(0,204,130,0.08));
  color: var(--mint); border-bottom: 1px solid var(--border-bright);
}}
.banner-demo {{
  background: linear-gradient(90deg, rgba(251,146,60,0.2), rgba(234,88,12,0.15));
  color: #fed7aa; border-bottom: 1px solid rgba(251,146,60,0.3);
}}
.banner-warn {{
  background: linear-gradient(90deg, rgba(251,113,133,0.16), rgba(251,146,60,0.12));
  color: #fecdd3; border-bottom: 1px solid rgba(251,113,133,0.28);
}}
.hidden {{ display: none !important; }}
body.has-banner {{ --banner-offset: 36px; }}
body:not(.has-banner) {{ --banner-offset: 0px; }}

/* ── Landing ── */
#landing {{
  position: relative; z-index: 1;
  padding: calc(var(--nav-h) + var(--banner-offset) + 2rem) 1.5rem 4rem;
  max-width: 1100px; margin: 0 auto;
}}
.hero {{
  text-align: center; padding: 3rem 0 4rem;
  animation: fadeUp 1s var(--ease) both;
}}
.hero-badge {{
  display: inline-flex; align-items: center; gap: 0.5rem;
  padding: 0.35rem 1rem; border-radius: 999px;
  background: var(--mint-dim); border: 1px solid var(--border-bright);
  font-size: 0.72rem; font-weight: 600; color: var(--mint);
  letter-spacing: 0.08em; text-transform: uppercase;
  margin-bottom: 1.5rem;
  animation: fadeUp 0.8s var(--ease) 0.1s both;
}}
.hero-badge .pulse-dot {{
  width: 6px; height: 6px; border-radius: 50%; background: var(--mint);
  animation: livePulse 2s ease-in-out infinite;
}}
.hero h1 {{
  font-family: 'Syne', sans-serif;
  font-size: clamp(2.5rem, 7vw, 4.2rem);
  font-weight: 800; line-height: 1.05; letter-spacing: -0.03em;
  margin-bottom: 1.25rem;
  animation: fadeUp 0.9s var(--ease) 0.15s both;
}}
.hero h1 .gradient {{
  background: linear-gradient(135deg, var(--mint) 0%, var(--cyan) 50%, var(--gold) 100%);
  -webkit-background-clip: text; -webkit-text-fill-color: transparent;
  background-size: 200% auto;
  animation: shimmer 4s linear infinite;
}}
.hero-sub {{
  font-size: 1.05rem; line-height: 1.7; color: var(--muted);
  max-width: 520px; margin: 0 auto 2rem; font-weight: 400;
  animation: fadeUp 0.9s var(--ease) 0.25s both;
}}
.hero-proof-stats {{
  display: flex; gap: 1.25rem; justify-content: center; flex-wrap: wrap;
  margin-top: 1.5rem; font-size: 0.78rem; color: var(--dim);
}}
.hero-proof-stats span {{
  padding: 0.35rem 0.75rem; border-radius: 999px;
  border: 1px solid var(--border); background: rgba(0,0,0,0.25);
}}

.hero-cta {{
  display: flex; gap: 0.75rem; justify-content: center; flex-wrap: wrap;
  animation: fadeUp 0.9s var(--ease) 0.35s both;
}}
.btn-hero {{
  padding: 1rem 2rem; border-radius: 14px; border: none; cursor: pointer;
  font-family: inherit; font-weight: 700; font-size: 0.95rem;
  transition: all 0.35s var(--ease);
}}
.btn-hero.primary {{
  background: linear-gradient(135deg, var(--mint), #00cc82);
  color: #001a0f;
  box-shadow: 0 8px 40px rgba(0,255,163,0.3);
}}
.btn-hero.primary:hover {{ transform: translateY(-3px); box-shadow: 0 16px 60px rgba(0,255,163,0.45); }}
.btn-hero.ghost {{
  background: transparent; color: var(--text);
  border: 1px solid var(--border);
}}
.btn-hero.ghost:hover {{ border-color: var(--mint); color: var(--mint); }}

/* Steps */
.steps {{
  display: grid; grid-template-columns: repeat(3, 1fr); gap: 1rem;
  margin: 2rem 0 3rem;
}}
@media (max-width: 768px) {{ .steps {{ grid-template-columns: 1fr; }} }}
.step {{
  padding: 1.5rem; border-radius: var(--radius);
  background: var(--surface); border: 1px solid var(--border);
  backdrop-filter: blur(12px);
  transition: transform 0.4s var(--ease), border-color 0.4s;
  animation: fadeUp 0.8s var(--ease) calc(0.4s + var(--i, 0) * 0.1s) both;
}}
.step:hover {{ transform: translateY(-6px); border-color: var(--border-bright); }}
.step-num {{
  font-family: 'Syne', sans-serif; font-size: 2rem; font-weight: 800;
  color: var(--mint); opacity: 0.35; line-height: 1; margin-bottom: 0.5rem;
}}
.step h3 {{ font-size: 0.95rem; font-weight: 700; margin-bottom: 0.4rem; }}
.step p {{ font-size: 0.82rem; color: var(--muted); line-height: 1.6; }}

/* Split bar */
.split-section {{
  padding: 2rem; border-radius: var(--radius);
  background: var(--surface); border: 1px solid var(--border);
  animation: fadeUp 0.8s var(--ease) 0.7s both;
}}
.split-section h2 {{
  font-family: 'Syne', sans-serif; font-size: 1.1rem; margin-bottom: 1.25rem;
}}
.split-bar {{
  height: 12px; border-radius: 999px; overflow: hidden; display: flex;
  background: rgba(255,255,255,0.04); margin-bottom: 1rem;
}}
.split-seg {{ height: 100%; transition: width 1.2s var(--ease); }}
.seg-stake {{ width: var(--split-stake); background: linear-gradient(90deg, var(--mint), #00cc82); }}
.seg-platform {{ width: var(--split-platform); background: var(--gold); }}
.seg-operator {{ width: var(--split-operator); background: var(--cyan); }}
.split-legend {{
  display: flex; gap: 1.5rem; flex-wrap: wrap; font-size: 0.78rem; color: var(--muted);
}}
.split-legend strong {{ color: var(--text); }}

/* Compare strip */
.compare-strip {{
  display: grid; grid-template-columns: repeat(4, 1fr); gap: 0.75rem;
  margin-top: 2rem;
}}
@media (max-width: 900px) {{ .compare-strip {{ grid-template-columns: repeat(2, 1fr); }} }}
.compare-item {{
  padding: 1rem; border-radius: 14px;
  background: rgba(0,0,0,0.3); border: 1px solid var(--border);
  font-size: 0.75rem;
}}
.compare-item .vs {{ color: var(--dim); font-size: 0.65rem; text-transform: uppercase; letter-spacing: 0.08em; }}
.compare-item .us {{ color: var(--mint); font-weight: 600; margin-top: 0.35rem; display: block; }}

/* ── Dashboard ── */
#dashboard {{ display: none; position: relative; z-index: 1; }}
#dashboard.visible {{ display: block; animation: fadeIn 0.6s var(--ease); }}
#landing.hidden {{ display: none; }}

.dash-layout {{
  display: grid; grid-template-columns: 300px 1fr;
  min-height: calc(100vh - var(--nav-h) - var(--banner-offset));
  padding-top: calc(var(--nav-h) + var(--banner-offset));
}}
@media (max-width: 1024px) {{ .dash-layout {{ grid-template-columns: 1fr; }} }}

/* Sidebar */
.dash-sidebar {{
  border-right: 1px solid var(--border);
  padding: 1.25rem;
  background: rgba(4,4,8,0.6);
  backdrop-filter: blur(16px);
  position: sticky; top: calc(var(--nav-h) + var(--banner-offset));
  height: calc(100vh - var(--nav-h) - var(--banner-offset));
  display: flex; flex-direction: column; gap: 1rem;
  overflow: hidden;
}}
@media (max-width: 1024px) {{
  .dash-sidebar {{ position: relative; height: auto; max-height: 320px; border-right: none; border-bottom: 1px solid var(--border); }}
}}

.mesh-card {{
  padding: 1.25rem; border-radius: 16px;
  background: linear-gradient(145deg, var(--mint-dim), transparent);
  border: 1px solid var(--border-bright);
}}
.mesh-card h4 {{
  font-size: 0.65rem; text-transform: uppercase; letter-spacing: 0.14em;
  color: var(--mint); margin-bottom: 0.75rem;
  display: flex; align-items: center; gap: 0.4rem;
}}
.mesh-nodes {{
  display: flex; align-items: center; justify-content: center; gap: 0.25rem;
  margin-bottom: 1rem; height: 32px;
}}
.mesh-node {{
  width: 8px; height: 8px; border-radius: 50%; background: var(--mint);
  animation: meshPulse 2s ease-in-out infinite;
}}
.mesh-node:nth-child(2) {{ animation-delay: 0.35s; }}
.mesh-node:nth-child(4) {{ animation-delay: 0.7s; }}
.mesh-line {{ flex: 1; height: 1px; background: linear-gradient(90deg, transparent, var(--mint), transparent); opacity: 0.35; }}
.net-row {{
  display: flex; justify-content: space-between; font-size: 0.75rem;
  padding: 0.25rem 0; color: var(--muted);
}}
.net-row strong {{ color: var(--text); font-weight: 600; }}

.feed-title {{
  font-size: 0.65rem; text-transform: uppercase; letter-spacing: 0.12em; color: var(--dim);
}}
.feed-list {{
  flex: 0 1 auto;
  max-height: 180px;
  overflow-y: auto; display: flex; flex-direction: column; gap: 0.5rem;
  scrollbar-width: thin; scrollbar-color: var(--border) transparent;
}}
.feed-item {{
  padding: 0.7rem 0.85rem; border-radius: 12px;
  background: rgba(0,0,0,0.35); border: 1px solid var(--border);
  border-left: 2px solid var(--mint);
  font-size: 0.72rem; line-height: 1.45;
  animation: feedSlide 0.45s var(--ease);
}}
.feed-item.new {{ border-left-color: var(--gold); background: var(--gold-dim); }}
.feed-item.feed-setup {{ border-left-color: var(--danger); background: rgba(251,113,133,0.08); }}
.feed-item.feed-fail {{ border-left-color: var(--danger); opacity: 0.75; }}
.feed-agent {{ color: var(--text); font-weight: 600; display: block; }}
.feed-meta {{ color: var(--dim); font-size: 0.65rem; margin-top: 0.2rem; }}

/* Family mission */
.family-mission-banner {{
  margin-top: 0.75rem;
  padding: 0.75rem 0.85rem;
  border-radius: 12px;
  background: linear-gradient(135deg, rgba(52,211,153,0.12), rgba(251,191,36,0.08));
  border: 1px solid var(--border-bright);
}}
.family-mission-kicker {{
  display: block;
  font-size: 0.58rem;
  text-transform: uppercase;
  letter-spacing: 0.12em;
  color: var(--mint);
  font-weight: 700;
  margin-bottom: 0.35rem;
}}
.family-mission-text {{
  margin: 0;
  font-size: 0.72rem;
  line-height: 1.5;
  color: var(--muted);
}}
.hierarchy-chain {{
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 0.25rem 0.35rem;
  margin-bottom: 0.45rem;
  font-size: 0.62rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.06em;
}}
.h-tier {{
  padding: 0.2rem 0.45rem;
  border-radius: 6px;
  border: 1px solid var(--border);
}}
.h-tier.founder {{ color: var(--gold); border-color: rgba(251,191,36,0.35); background: rgba(251,191,36,0.08); }}
.h-tier.assistant {{ color: var(--cyan); border-color: rgba(56,189,248,0.35); background: rgba(56,189,248,0.08); }}
.h-tier.coord {{ color: var(--mint); border-color: var(--border-bright); background: var(--mint-dim); }}
.h-tier.workers {{ color: var(--muted); }}
.h-arrow {{ color: var(--dim); font-size: 0.55rem; }}
.autopilot-status {{
  margin-top: 0.4rem;
  font-size: 0.62rem;
  color: var(--mint);
  font-family: ui-monospace, monospace;
}}
.organism-phase {{
  margin-top: 0.25rem;
  font-size: 0.6rem;
  color: var(--gold);
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.08em;
}}

/* Agent dialogue */
.dialogue-panel {{
  flex: 1 1 auto;
  min-height: 0;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  border-top: 1px solid var(--border);
  padding-top: 0.75rem;
}}
.dialogue-header {{
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.5rem;
}}
.dialogue-live-badge {{
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
  font-size: 0.6rem;
  text-transform: uppercase;
  letter-spacing: 0.1em;
  color: var(--mint);
  font-weight: 700;
}}
.dialogue-thread {{
  flex: 1 1 auto;
  min-height: 120px;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 0.55rem;
  padding-right: 0.15rem;
  scrollbar-width: thin;
  scrollbar-color: var(--border) transparent;
}}
.dialogue-empty {{
  font-size: 0.72rem;
  color: var(--dim);
  line-height: 1.5;
  padding: 0.5rem 0;
}}
.dialogue-msg {{
  animation: dialogueIn 0.45s var(--ease) both;
  animation-delay: var(--delay, 0s);
}}
.dialogue-meta {{
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 0.25rem 0.35rem;
  font-size: 0.58rem;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: var(--dim);
  margin-bottom: 0.25rem;
}}
.dialogue-from {{ color: var(--cyan); font-weight: 700; }}
.dialogue-to {{ color: var(--gold); font-weight: 700; }}
.dialogue-arrow {{ opacity: 0.45; font-size: 0.55rem; }}
.dialogue-intent {{
  margin-left: auto;
  padding: 0.1rem 0.35rem;
  border-radius: 999px;
  background: rgba(255,255,255,0.04);
  border: 1px solid var(--border);
  font-size: 0.52rem;
}}
.dialogue-bubble {{
  padding: 0.55rem 0.7rem;
  border-radius: 12px 12px 12px 4px;
  background: rgba(0,0,0,0.45);
  border: 1px solid var(--border);
  font-size: 0.72rem;
  line-height: 1.45;
  color: var(--text);
}}
.dialogue-msg.coord .dialogue-bubble {{
  border-color: rgba(255,209,102,0.35);
  background: linear-gradient(135deg, rgba(255,209,102,0.08), rgba(0,0,0,0.4));
}}
.dialogue-msg.intent-hire_request .dialogue-bubble {{
  border-left: 2px solid var(--gold);
}}
.dialogue-msg.intent-handoff .dialogue-bubble {{
  border-left: 2px solid var(--cyan);
}}
.dialogue-msg.intent-task_done .dialogue-bubble,
.dialogue-msg.intent-pipeline_complete .dialogue-bubble {{
  border-left: 2px solid var(--mint);
}}
@keyframes dialogueIn {{
  from {{ opacity: 0; transform: translateY(8px); }}
  to {{ opacity: 1; transform: translateY(0); }}
}}

/* Main */
.dash-main {{ padding: 1.5rem 1.75rem 3rem; overflow: hidden; }}

.dash-header {{
  display: flex; justify-content: space-between; align-items: flex-start;
  flex-wrap: wrap; gap: 1rem; margin-bottom: 1.5rem;
  animation: fadeUp 0.6s var(--ease) both;
}}
.dash-header h2 {{
  font-family: 'Syne', sans-serif; font-size: 1.75rem; font-weight: 800; letter-spacing: -0.02em;
}}
.dash-header p {{ color: var(--muted); font-size: 0.85rem; margin-top: 0.25rem; }}

.stats-grid {{
  display: grid; grid-template-columns: repeat(4, 1fr); gap: 0.75rem;
  margin-bottom: 1.5rem;
}}
@media (max-width: 768px) {{ .stats-grid {{ grid-template-columns: repeat(2, 1fr); }} }}
.stat {{
  padding: 1.1rem 1.25rem; border-radius: 16px;
  background: var(--surface); border: 1px solid var(--border);
  transition: border-color 0.3s, transform 0.3s var(--ease);
  animation: fadeUp 0.6s var(--ease) calc(0.1s + var(--i,0)*0.05s) both;
}}
.stat:hover {{ border-color: var(--border-bright); transform: translateY(-2px); }}
.stat-label {{ font-size: 0.62rem; text-transform: uppercase; letter-spacing: 0.1em; color: var(--dim); }}
.stat-value {{
  font-family: 'Syne', sans-serif; font-size: 1.6rem; font-weight: 800;
  margin-top: 0.2rem; letter-spacing: -0.02em;
}}
.stat-value.mint {{ color: var(--mint); }}
.stat-value.gold {{ color: var(--gold); }}

.setup-alert {{
  display: flex; align-items: center; justify-content: space-between; gap: 1rem;
  flex-wrap: wrap; margin-bottom: 1.25rem; padding: 1rem 1.1rem; border-radius: 16px;
  background: rgba(251,113,133,0.08); border: 1px solid rgba(251,113,133,0.22);
  animation: fadeUp 0.5s var(--ease) both;
}}
.setup-alert strong {{ display: block; color: #fecdd3; font-size: 0.9rem; margin-bottom: 0.25rem; }}
.setup-alert p {{ color: var(--muted); font-size: 0.78rem; line-height: 1.5; margin: 0; }}
.setup-cmd {{
  padding: 0.55rem 0.85rem; border-radius: 10px; background: rgba(0,0,0,0.35);
  color: var(--mint); font-size: 0.72rem; border: 1px solid var(--border);
}}

.net-online {{ color: var(--mint) !important; }}
.net-degraded {{ color: var(--danger) !important; text-transform: capitalize; }}

.synapse-prompt {{
  margin: 0 0 1.25rem;
  padding: 1.25rem 1.35rem;
  border-radius: 16px;
  border: 1px solid rgba(120, 255, 200, 0.18);
  background: linear-gradient(145deg, rgba(8, 20, 18, 0.92), rgba(4, 8, 12, 0.95));
  position: relative;
}}
.synapse-prompt-kicker {{
  font-size: 0.65rem;
  letter-spacing: 0.14em;
  text-transform: uppercase;
  color: var(--mint);
}}
.synapse-prompt h3 {{ margin: 0.35rem 0 0.25rem; font-size: 1.15rem; }}
.synapse-prompt-head p {{ margin: 0 0 0.75rem; color: var(--dim); font-size: 0.82rem; }}
.synapse-prompt-input {{
  width: 100%;
  min-height: 88px;
  resize: vertical;
  border-radius: 12px;
  border: 1px solid rgba(255,255,255,0.08);
  background: rgba(0,0,0,0.35);
  color: var(--text);
  padding: 0.85rem 1rem;
  font: inherit;
  line-height: 1.45;
}}
.synapse-prompt-actions {{ margin-top: 0.75rem; display: flex; gap: 0.5rem; }}
.btn-prompt {{
  position: relative;
  border: none;
  border-radius: 999px;
  padding: 0.65rem 1.4rem;
  background: linear-gradient(90deg, #1ef2b0, #0ea5e9);
  color: #021208;
  font-weight: 700;
  cursor: pointer;
}}
.btn-prompt.loading .btn-text {{ opacity: 0; }}
.btn-prompt .btn-loader {{
  display: none;
  position: absolute;
  inset: 0;
  margin: auto;
  width: 18px; height: 18px;
  border: 2px solid rgba(0,0,0,0.2);
  border-top-color: #021208;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}}
.btn-prompt.loading .btn-loader {{ display: block; }}
.arena-overlay {{
  margin-top: 0.85rem;
  padding: 0.75rem 1rem;
  border-radius: 10px;
  background: rgba(30, 242, 176, 0.08);
  display: flex;
  align-items: center;
  gap: 0.75rem;
  color: var(--mint);
  font-size: 0.85rem;
}}
.arena-pulse {{
  width: 10px; height: 10px;
  border-radius: 50%;
  background: var(--mint);
  animation: pulse 1.2s ease-in-out infinite;
}}
.arena-result {{
  margin-top: 0.75rem;
  padding: 0.85rem 1rem;
  border-radius: 10px;
  background: rgba(255,255,255,0.04);
  font-size: 0.8rem;
  line-height: 1.5;
  color: var(--text);
}}
body.arena-frozen .synapse-prompt-input {{ opacity: 0.65; pointer-events: none; }}
body.arena-frozen .dash-main > *:not(.synapse-prompt) {{ opacity: 0.45; pointer-events: none; }}

.mesh-proof-hero {{
  display: grid;
  grid-template-columns: 1.4fr 0.8fr;
  gap: 1.25rem;
  margin-bottom: 1.25rem;
  padding: 1.35rem 1.5rem;
  border-radius: calc(var(--radius) + 6px);
  border: 1px solid rgba(255,209,102,0.35);
  background: linear-gradient(135deg, rgba(255,209,102,0.1), rgba(0,255,163,0.06) 55%, rgba(8,8,15,0.95));
  animation: cardReveal 0.7s var(--ease) both;
  position: relative;
  overflow: hidden;
}}
.mesh-proof-hero::after {{
  content: '';
  position: absolute;
  inset: 0;
  background: linear-gradient(105deg, transparent 40%, rgba(255,255,255,0.03) 50%, transparent 60%);
  animation: shine 8s ease-in-out infinite;
  pointer-events: none;
}}
.mesh-proof-kicker {{
  font-size: 0.68rem;
  letter-spacing: 0.14em;
  text-transform: uppercase;
  color: var(--gold);
  font-weight: 700;
}}
.mesh-proof-copy h3 {{
  font-family: 'Syne', sans-serif;
  font-size: clamp(1.4rem, 3vw, 1.9rem);
  font-weight: 800;
  margin: 0.35rem 0 0.5rem;
}}
.mesh-proof-copy p {{ color: var(--muted); line-height: 1.6; margin-bottom: 0.75rem; }}
.mesh-proof-steps {{
  margin: 0; padding-left: 1.1rem;
  color: var(--muted); font-size: 0.8rem; line-height: 1.7;
}}
.mesh-proof-action {{
  display: flex; flex-direction: column; justify-content: center; gap: 0.65rem;
  position: relative; z-index: 1;
}}
.mesh-proof-price {{
  font-family: 'Syne', sans-serif;
  font-size: 1.1rem;
  color: var(--gold);
  font-weight: 700;
}}
.btn-mesh-proof {{
  position: relative;
  padding: 1rem 1.25rem;
  border: none;
  border-radius: 14px;
  cursor: pointer;
  font-family: inherit;
  font-weight: 800;
  font-size: 0.95rem;
  color: #1a1200;
  background: linear-gradient(135deg, var(--gold), #ffb347);
  box-shadow: 0 12px 40px rgba(255,209,102,0.25);
  transition: transform 0.25s var(--ease);
}}
.btn-mesh-proof:hover {{ transform: translateY(-2px) scale(1.02); }}
.btn-mesh-proof.loading .btn-text {{ opacity: 0; }}
.btn-mesh-proof .btn-loader {{
  display: none;
  position: absolute; inset: 0; margin: auto;
  width: 20px; height: 20px;
  border: 2px solid rgba(26,18,0,0.25);
  border-top-color: #1a1200;
  border-radius: 50%;
  animation: spin 0.7s linear infinite;
}}
.btn-mesh-proof.loading .btn-loader {{ display: block; }}
.mesh-proof-result {{
  font-size: 0.72rem;
  color: var(--dim);
  line-height: 1.5;
  min-height: 2.8em;
}}
.mesh-proof-result.success {{ color: var(--mint); }}

.featured-slot {{ margin-bottom: 1.25rem; }}
.featured-grid {{
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
  gap: 1rem;
}}
.featured-worker {{
  position: relative; overflow: hidden; border-radius: calc(var(--radius) + 4px);
  border: 1px solid var(--border-bright);
  background: linear-gradient(145deg, rgba(0,255,163,0.08), rgba(8,8,15,0.92) 45%);
  padding: 1.5rem; animation: cardReveal 0.8s var(--ease) both;
}}
.featured-glow {{
  position: absolute; inset: -30% auto auto -10%; width: 55%; height: 120%;
  background: radial-gradient(circle, rgba(0,255,163,0.18), transparent 70%);
  pointer-events: none; animation: meshPulse 4s ease-in-out infinite;
}}
.featured-badge {{
  display: inline-flex; align-items: center; gap: 0.45rem;
  font-size: 0.68rem; font-weight: 700; letter-spacing: 0.08em; text-transform: uppercase;
  color: var(--mint); margin-bottom: 1rem;
}}
.featured-body {{
  display: grid; grid-template-columns: 1.2fr 0.9fr; gap: 1.25rem; align-items: stretch;
}}
.featured-kicker {{
  display: block; font-size: 0.68rem; letter-spacing: 0.12em; text-transform: uppercase;
  color: var(--cyan); margin-bottom: 0.35rem;
}}
.featured-copy h3 {{
  font-family: 'Syne', sans-serif; font-size: clamp(1.5rem, 3vw, 2rem);
  font-weight: 800; margin-bottom: 0.5rem;
}}
.featured-copy p {{ color: var(--muted); line-height: 1.6; margin-bottom: 0.85rem; }}
.featured-tags {{ display: flex; gap: 0.4rem; flex-wrap: wrap; margin-bottom: 1rem; }}
.featured-metrics {{
  display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 0.5rem;
}}
.featured-mission {{ color: var(--text); font-weight: 500; margin-bottom: 0.5rem; }}
.featured-desc {{
  font-size: 0.82rem; color: var(--muted); line-height: 1.65; margin-bottom: 0.85rem;
  display: -webkit-box; -webkit-line-clamp: 3; -webkit-box-orient: vertical; overflow: hidden;
}}
.featured-thesis {{
  font-size: 0.78rem; color: var(--gold); line-height: 1.55; margin-top: 0.75rem;
  padding: 0.65rem; border-radius: 10px; background: rgba(255,209,102,0.06);
  border-left: 2px solid var(--gold);
}}
.tag.dept {{ background: rgba(56,189,248,0.12); color: var(--cyan); }}
.tag.apy-tag {{ background: var(--mint-dim); color: var(--mint); border: 1px solid var(--border-bright); }}
.wc-use-cases {{
  list-style: none; display: flex; flex-wrap: wrap; gap: 0.35rem; margin: 0.65rem 0;
}}
.wc-use-cases li {{
  font-size: 0.68rem; padding: 0.2rem 0.55rem; border-radius: 6px;
  background: rgba(255,255,255,0.04); color: var(--muted); border: 1px solid var(--border);
}}
.wc-caps-compact {{ font-size: 0.68rem; margin-top: 0.5rem; }}
.btn-agent-detail {{
  width: 100%; padding: 0.65rem; border-radius: 10px; border: 1px solid var(--border);
  background: rgba(255,255,255,0.04); color: var(--muted); font-family: inherit;
  font-size: 0.78rem; font-weight: 600; cursor: pointer; transition: all 0.25s;
}}
.btn-agent-detail:hover {{ border-color: var(--cyan); color: var(--cyan); }}
.btn-agent-detail.inline {{ width: auto; margin: 0.75rem 0 0.5rem; }}
.wc-compact-apy {{ font-size: 0.68rem; color: var(--mint); font-weight: 700; }}
.wc-compact-detail {{
  width: 100%; margin-top: 0.5rem; padding: 0.4rem; border: none; background: none;
  color: var(--cyan); font-size: 0.72rem; cursor: pointer; font-family: inherit;
}}
.featured-metrics div {{
  padding: 0.65rem; border-radius: 12px; background: rgba(0,0,0,0.28);
  border: 1px solid var(--border);
}}
.featured-metrics span {{ display: block; font-size: 0.6rem; color: var(--dim); text-transform: uppercase; }}
.featured-metrics strong {{ font-family: 'Syne', sans-serif; font-size: 1rem; }}
.featured-actions {{
  display: flex; flex-direction: column; gap: 0.75rem; justify-content: center;
  padding: 1rem; border-radius: 16px; background: rgba(0,0,0,0.28); border: 1px solid var(--border);
}}
.featured-status {{ display: flex; align-items: center; gap: 0.45rem; font-size: 0.72rem; color: var(--dim); }}
.featured-task {{
  display: flex; align-items: center; gap: 0.45rem; padding: 0.55rem 0.7rem;
  border-radius: 10px; background: rgba(0,0,0,0.35); font-size: 0.72rem; color: var(--muted);
  font-family: ui-monospace, monospace;
}}
.featured-x402 {{
  margin-top: 0 !important; padding: 0.9rem !important; font-size: 0.9rem !important;
  border-style: solid !important; background: linear-gradient(135deg, rgba(0,255,163,0.18), rgba(0,255,163,0.08)) !important;
}}
.featured-hint {{ font-size: 0.68rem; color: var(--dim); line-height: 1.45; text-align: center; }}

.worker-pool {{
  border: 1px solid var(--border); border-radius: 16px; padding: 0.75rem 1rem 1rem;
  background: rgba(0,0,0,0.18);
}}
.worker-pool summary {{
  cursor: pointer; color: var(--muted); font-size: 0.82rem; font-weight: 600;
  list-style: none; display: flex; align-items: center; gap: 0.5rem;
}}
.worker-pool summary::-webkit-details-marker {{ display: none; }}
.worker-pool[open] summary {{ color: var(--mint); margin-bottom: 0.85rem; }}
.compact-grid {{ grid-template-columns: 1fr; gap: 0.65rem; }}

.toolbar {{
  display: flex; justify-content: space-between; align-items: center;
  flex-wrap: wrap; gap: 0.75rem; margin-bottom: 1.25rem;
}}
.filter-tabs {{
  display: flex; gap: 0.35rem; flex-wrap: wrap;
}}
.filter-tab {{
  padding: 0.4rem 0.85rem; border-radius: 999px; border: 1px solid var(--border);
  background: transparent; color: var(--muted); font-size: 0.75rem; font-weight: 600;
  cursor: pointer; transition: all 0.25s;
  font-family: inherit;
}}
.filter-tab:hover {{ border-color: var(--mint); color: var(--mint); }}
.filter-tab.active {{
  background: var(--mint-dim); border-color: var(--border-bright); color: var(--mint);
}}
.btn-trigger {{
  padding: 0.45rem 1rem; border-radius: 999px;
  border: 1px solid var(--border-bright); background: var(--mint-dim);
  color: var(--mint); font-size: 0.75rem; font-weight: 700; cursor: pointer;
  font-family: inherit; transition: all 0.25s;
}}
.btn-trigger:hover {{ background: rgba(0,255,163,0.2); transform: scale(1.03); }}

.workers-grid {{
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 1rem;
}}

/* ── Worker card ── */
.worker-card {{
  position: relative; border-radius: var(--radius);
  background: var(--surface); border: 1px solid var(--border);
  padding: 1.25rem; overflow: hidden;
  backdrop-filter: blur(16px);
  transition: transform 0.4s var(--ease), border-color 0.4s, box-shadow 0.4s;
  animation: cardReveal 0.7s var(--ease) var(--delay, 0s) both;
}}
.worker-card:hover {{
  border-color: var(--border-bright);
  transform: translateY(-4px);
  box-shadow: 0 20px 60px rgba(0,255,163,0.08);
}}
.worker-card.processing {{
  border-color: rgba(255,209,102,0.4);
  box-shadow: 0 0 40px rgba(255,209,102,0.1);
}}
.worker-card.is-live .wc-pulse {{ opacity: 1; animation: ringExpand 2s ease-out infinite; }}
.worker-card.compact {{
  padding: 0.85rem 1rem; animation: none;
}}
.worker-card.compact:hover {{ transform: none; box-shadow: none; }}
.wc-compact-main {{
  display: grid; grid-template-columns: auto 1fr auto; gap: 0.75rem; align-items: center;
}}
.wc-compact-copy h3 {{ font-family: 'Syne', sans-serif; font-size: 0.92rem; margin-bottom: 0.15rem; }}
.wc-compact-copy p {{
  font-size: 0.72rem; color: var(--dim); white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
}}
.wc-compact-meta {{ display: flex; flex-direction: column; align-items: flex-end; gap: 0.25rem; }}
.wc-compact-soon {{ font-size: 0.62rem; color: var(--dim); }}
.wc-shine {{
  position: absolute; top: 0; left: -100%; width: 60%; height: 100%;
  background: linear-gradient(90deg, transparent, rgba(255,255,255,0.03), transparent);
  animation: shine 6s ease-in-out infinite;
  animation-delay: calc(var(--i) * 0.8s);
  pointer-events: none;
}}
.wc-orbit {{
  position: absolute; top: -40px; right: -40px; width: 100px; height: 100px;
  border-radius: 50%; border: 1px solid rgba(0,255,163,0.06);
  pointer-events: none;
}}

.wc-head {{ display: flex; gap: 0.75rem; align-items: flex-start; margin-bottom: 0.75rem; }}
.wc-avatar {{
  width: 44px; height: 44px; border-radius: 14px; flex-shrink: 0;
  display: flex; align-items: center; justify-content: center;
  background: rgba(255,255,255,0.03); border: 1px solid var(--border);
  position: relative; font-size: 1.1rem;
}}
.wc-pulse {{
  position: absolute; inset: -3px; border-radius: 16px;
  border: 1px solid var(--mint); opacity: 0; pointer-events: none;
}}
.wc-title {{ flex: 1; min-width: 0; }}
.wc-title h3 {{
  font-family: 'Syne', sans-serif; font-size: 1rem; font-weight: 700;
  white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
}}
.wc-tags {{ display: flex; gap: 0.35rem; margin-top: 0.25rem; flex-wrap: wrap; }}
.tag {{
  font-size: 0.6rem; padding: 0.15rem 0.45rem; border-radius: 6px;
  font-weight: 600; letter-spacing: 0.04em;
}}
.tag.class {{ background: var(--mint-dim); color: var(--mint); }}
.tag.risk-düşük {{ color: var(--cyan); border: 1px solid rgba(56,189,248,0.2); }}
.tag.risk-orta {{ color: var(--gold); border: 1px solid rgba(255,209,102,0.2); }}
.tag.real-api {{ background: rgba(56,189,248,0.12); color: var(--cyan); border: 1px solid rgba(56,189,248,0.25); }}
.btn-x402 {{
  width: 100%; margin-top: 0.5rem; padding: 0.65rem; border-radius: 10px;
  border: 1px dashed var(--border-bright); background: rgba(0,255,163,0.06);
  color: var(--mint); font-family: inherit; font-size: 0.78rem; font-weight: 700;
  cursor: pointer; transition: all 0.25s;
}}
.btn-x402:hover {{ background: rgba(0,255,163,0.14); transform: translateY(-1px); }}
.btn-x402.loading {{ opacity: 0.6; pointer-events: none; }}
.wc-status {{
  display: flex; flex-direction: column; align-items: flex-end; gap: 0.2rem;
  font-size: 0.62rem; color: var(--dim);
}}
.status-dot {{
  width: 8px; height: 8px; border-radius: 50%; background: var(--dim);
}}
.status-dot.active {{ background: var(--mint); box-shadow: 0 0 10px var(--mint); animation: livePulse 1.5s infinite; }}
.status-dot.processing {{ background: var(--gold); animation: processBlink 0.5s infinite; }}
.status-dot.standby {{ background: #64748b; }}
.status-dot.offline {{ background: var(--danger); }}

.wc-mission {{
  font-size: 0.8rem; color: var(--muted); line-height: 1.55; margin-bottom: 1rem;
  display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden;
}}

.wc-metrics {{
  display: grid; grid-template-columns: repeat(4, 1fr); gap: 0.5rem; margin-bottom: 0.85rem;
}}
.wc-metric {{
  padding: 0.55rem 0.5rem; border-radius: 10px;
  background: rgba(0,0,0,0.25); text-align: center;
}}
.wc-metric.highlight {{ background: var(--mint-dim); border: 1px solid var(--border-bright); }}
.wc-m-label {{ display: block; font-size: 0.58rem; text-transform: uppercase; letter-spacing: 0.08em; color: var(--dim); }}
.wc-m-value {{ display: block; font-family: 'Syne', sans-serif; font-size: 0.95rem; font-weight: 700; margin-top: 0.15rem; }}
.wc-m-value.apy {{ color: var(--mint); font-size: 1.1rem; }}

.wc-task {{
  display: flex; align-items: center; gap: 0.5rem;
  padding: 0.5rem 0.65rem; border-radius: 8px; margin-bottom: 0.85rem;
  background: rgba(0,0,0,0.3); font-size: 0.68rem; color: var(--dim);
  font-family: ui-monospace, monospace;
  border-left: 2px solid transparent; transition: all 0.3s;
}}
.worker-card.processing .wc-task {{ border-left-color: var(--gold); color: var(--mint); }}
.task-pulse {{
  width: 5px; height: 5px; border-radius: 50%; background: var(--dim); flex-shrink: 0;
}}
.worker-card.processing .task-pulse {{ background: var(--gold); animation: livePulse 0.8s infinite; }}

.wc-stake {{ margin-bottom: 0.5rem; }}
.stake-input-wrap {{
  display: flex; align-items: center; gap: 0.5rem;
  padding: 0.65rem 0.85rem; border-radius: 12px;
  background: rgba(0,0,0,0.35); border: 1px solid var(--border);
  margin-bottom: 0.5rem; transition: border-color 0.3s;
}}
.stake-input-wrap:focus-within {{ border-color: var(--border-bright); }}
.currency {{ color: var(--dim); font-weight: 600; }}
.stake-input-wrap input {{
  flex: 1; background: none; border: none; outline: none;
  color: var(--text); font-family: inherit; font-size: 1rem; font-weight: 600;
  min-width: 0;
}}
.stake-input-wrap input::placeholder {{ color: var(--dim); font-weight: 400; }}
.token-tag {{ font-size: 0.65rem; color: var(--gold); font-weight: 700; }}
.stake-actions {{ display: grid; grid-template-columns: 1fr auto auto; gap: 0.5rem; }}
.btn-unstake {{
  padding: 0.75rem 0.85rem; border-radius: 12px;
  border: 1px solid rgba(251,113,133,0.35); background: rgba(251,113,133,0.08);
  color: var(--danger); font-family: inherit; font-weight: 600; font-size: 0.75rem;
  cursor: pointer; transition: all 0.25s; white-space: nowrap;
}}
.btn-unstake:hover {{ border-color: var(--danger); background: rgba(251,113,133,0.15); }}
.btn-stake {{
  position: relative; padding: 0.75rem; border-radius: 12px; border: none; cursor: pointer;
  font-family: inherit; font-weight: 700; font-size: 0.85rem;
  background: linear-gradient(135deg, var(--mint), #00cc82); color: #001a0f;
  overflow: hidden; transition: transform 0.3s var(--ease);
}}
.btn-stake:hover {{ transform: scale(1.02); }}
.btn-stake.loading .btn-text {{ opacity: 0; }}
.btn-stake.loading .btn-loader {{
  display: block; position: absolute; inset: 0; margin: auto;
  width: 18px; height: 18px; border: 2px solid rgba(0,26,15,0.3);
  border-top-color: #001a0f; border-radius: 50%; animation: spin 0.7s linear infinite;
}}
.btn-loader {{ display: none; }}
.btn-claim {{
  padding: 0.75rem 1rem; border-radius: 12px;
  border: 1px solid var(--border); background: transparent;
  color: var(--muted); font-family: inherit; font-weight: 600; font-size: 0.8rem;
  cursor: pointer; transition: all 0.25s; white-space: nowrap;
}}
.btn-claim:hover {{ border-color: var(--gold); color: var(--gold); }}

.wc-expand {{
  width: 100%; display: flex; align-items: center; justify-content: center; gap: 0.35rem;
  padding: 0.5rem; border: none; background: none; color: var(--dim);
  font-size: 0.72rem; cursor: pointer; font-family: inherit;
  transition: color 0.25s;
}}
.wc-expand:hover {{ color: var(--mint); }}
.wc-expand[aria-expanded="true"] svg {{ transform: rotate(180deg); }}
.wc-expand svg {{ transition: transform 0.3s var(--ease); }}

.wc-detail {{
  margin-top: 0.75rem; padding-top: 0.75rem; border-top: 1px solid var(--border);
  animation: fadeIn 0.35s var(--ease);
}}
.wc-detail[hidden] {{ display: none; }}
.wc-desc {{ font-size: 0.78rem; color: var(--muted); line-height: 1.65; margin-bottom: 0.75rem; }}
.wc-detail-grid {{
  display: grid; grid-template-columns: 1fr 1fr; gap: 0.5rem; margin-bottom: 0.75rem;
}}
.wc-detail-grid div {{
  padding: 0.5rem; border-radius: 8px; background: rgba(0,0,0,0.25); font-size: 0.72rem;
}}
.wc-detail-grid span {{ display: block; color: var(--dim); font-size: 0.62rem; text-transform: uppercase; }}
.wc-detail-grid strong {{ color: var(--text); }}
.wc-caps {{ list-style: none; font-size: 0.75rem; color: var(--muted); margin-bottom: 0.75rem; }}
.wc-caps .cap-name {{ color: var(--mint); font-weight: 600; }}
.wc-thesis {{ font-size: 0.78rem; color: var(--gold); line-height: 1.6; margin-bottom: 0.5rem; }}
.wc-covers {{ font-size: 0.72rem; color: var(--dim); line-height: 1.5; }}
.wc-contract {{ display: block; font-size: 0.65rem; color: var(--cyan); margin-top: 0.5rem; opacity: 0.7; }}

/* ── Modal ── */
.modal-overlay {{
  display: none; position: fixed; inset: 0; z-index: 500;
  background: rgba(0,0,0,0.8); backdrop-filter: blur(12px);
  align-items: center; justify-content: center; padding: 1rem;
}}
.modal-overlay.open {{ display: flex; animation: fadeIn 0.3s var(--ease); }}
.modal {{
  width: 100%; max-width: 400px; padding: 2rem; border-radius: 24px;
  background: var(--bg-2); border: 1px solid var(--border);
  box-shadow: 0 40px 100px rgba(0,0,0,0.6);
  position: relative; animation: modalIn 0.5s var(--ease-bounce);
}}
.modal h2 {{ font-family: 'Syne', sans-serif; font-size: 1.5rem; font-weight: 800; margin-bottom: 0.5rem; }}
.modal p {{ color: var(--muted); font-size: 0.85rem; line-height: 1.6; margin-bottom: 1.25rem; }}
.modal-close {{
  position: absolute; top: 1rem; right: 1rem; background: none; border: none;
  color: var(--dim); font-size: 1.4rem; cursor: pointer; line-height: 1;
}}
.btn-modal {{
  width: 100%; padding: 0.9rem; border-radius: 12px; border: none; cursor: pointer;
  font-family: inherit; font-weight: 700; font-size: 0.9rem; margin-bottom: 0.5rem;
  transition: transform 0.2s;
}}
.btn-modal.primary {{
  background: linear-gradient(135deg, var(--mint), #00cc82); color: #001a0f;
}}
.btn-modal.ghost {{
  background: rgba(255,255,255,0.04); color: var(--text); border: 1px solid var(--border);
}}
.btn-modal:hover {{ transform: translateY(-1px); }}
.modal input {{
  width: 100%; padding: 0.75rem; border-radius: 10px; border: 1px solid var(--border);
  background: rgba(0,0,0,0.4); color: var(--text); font-family: inherit; margin: 0.75rem 0 0.5rem;
  outline: none;
}}
.modal details {{ margin-top: 1rem; font-size: 0.82rem; color: var(--muted); }}
.modal summary {{ cursor: pointer; }}

/* Splash */
.splash {{
  position: fixed; inset: 0; z-index: 400;
  display: flex; align-items: center; justify-content: center;
  background: rgba(2,2,4,0.92); backdrop-filter: blur(20px);
  opacity: 0; pointer-events: none; transition: opacity 0.5s var(--ease);
}}
.splash.show {{ opacity: 1; pointer-events: auto; }}
.splash-inner {{ text-align: center; animation: modalIn 0.6s var(--ease-bounce); }}
.splash-ring {{
  width: 56px; height: 56px; margin: 0 auto 1.25rem; border-radius: 50%;
  border: 2px solid var(--border-bright); border-top-color: var(--mint);
  animation: spin 0.8s linear infinite;
}}
.splash h2 {{ font-family: 'Syne', sans-serif; font-size: 1.75rem; margin-bottom: 0.35rem; }}
.splash p {{ color: var(--muted); font-size: 0.9rem; }}

/* Toast */
.toast {{
  position: fixed; bottom: 1.5rem; left: 50%; transform: translateX(-50%) translateY(120px);
  z-index: 600; padding: 0.85rem 1.5rem; border-radius: 999px;
  background: var(--surface-2); border: 1px solid var(--border-bright);
  color: var(--mint); font-size: 0.85rem; font-weight: 600;
  box-shadow: 0 20px 60px rgba(0,0,0,0.5);
  opacity: 0; transition: all 0.45s var(--ease-bounce); pointer-events: none;
  max-width: 90vw; text-align: center;
}}
.toast.show {{ transform: translateX(-50%) translateY(0); opacity: 1; }}
.toast.error {{ border-color: rgba(251,113,133,0.4); color: var(--danger); }}

/* Embed */
body.embed-mode #landing {{ display: none !important; }}
body.embed-mode .dash-layout {{ padding-top: var(--nav-h); }}

/* ── Sade yatırım & renkli kartlar ── */
.invest-intro {{
  margin-bottom: 1.25rem; padding: 1rem 1.25rem; border-radius: 16px;
  background: rgba(0,255,163,0.05); border: 1px solid var(--border);
}}
.invest-intro h3 {{
  font-family: 'Syne', sans-serif; font-size: 1.15rem; margin-bottom: 0.35rem;
}}
.invest-intro p {{ font-size: 0.85rem; color: var(--muted); line-height: 1.55; }}
.invest-intro strong {{ color: var(--mint); }}
.stats-invest {{ grid-template-columns: repeat(3, 1fr); margin-bottom: 1rem; }}
.invest-empty {{ color: var(--dim); text-align: center; padding: 2rem; }}

.color-legend {{
  display: flex; gap: 0.65rem; flex-wrap: wrap; margin-left: auto;
}}
.legend-item {{
  font-size: 0.68rem; color: var(--dim); padding: 0.2rem 0.55rem;
  border-radius: 6px; border: 1px solid var(--border);
}}
.legend-media {{ border-color: rgba(168,85,247,0.35); color: #c4b5fd; background: rgba(168,85,247,0.08); }}
.legend-copy {{ border-color: rgba(56,189,248,0.35); color: #7dd3fc; background: rgba(56,189,248,0.08); }}
.legend-tech {{ border-color: rgba(255,209,102,0.35); color: #fde68a; background: rgba(255,209,102,0.08); }}

.agents-grid {{
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 0.85rem;
}}

.worker-card.tone-media_video {{ --card-r: 168; --card-g: 85; --card-b: 247; }}
.worker-card.tone-copywriting {{ --card-r: 56; --card-g: 189; --card-b: 248; }}
.worker-card.tone-technical {{ --card-r: 255; --card-g: 209; --card-b: 102; }}
.worker-card.tone-default {{ --card-r: 100; --card-g: 116; --card-b: 139; }}
.worker-card[class*="tone-"] {{
  background: linear-gradient(
    155deg,
    rgba(var(--card-r), var(--card-g), var(--card-b), 0.11),
    rgba(14, 14, 22, 0.88) 55%
  );
  border-color: rgba(var(--card-r), var(--card-g), var(--card-b), 0.22);
  border-left: 3px solid rgba(var(--card-r), var(--card-g), var(--card-b), 0.5);
}}
.worker-card.wc-variant-1 {{ filter: brightness(1.04); }}
.worker-card.wc-variant-2 {{ border-left-color: rgba(var(--card-r), var(--card-g), var(--card-b), 0.32); }}
.worker-card.wc-variant-3 {{ box-shadow: inset 0 1px 0 rgba(var(--card-r), var(--card-g), var(--card-b), 0.1); }}
.worker-card.is-live-worker {{
  box-shadow: 0 0 0 1px rgba(0,255,163,0.2), 0 8px 32px rgba(0,0,0,0.25);
}}

.wc-head-simple {{
  display: flex; gap: 0.65rem; align-items: flex-start; margin-bottom: 0.65rem;
}}
.wc-title-simple {{ flex: 1; min-width: 0; }}
.wc-title-simple h3 {{
  font-family: 'Syne', sans-serif; font-size: 0.98rem; font-weight: 700;
  margin-bottom: 0.25rem; line-height: 1.25;
}}
.wc-meta-row {{ display: flex; gap: 0.35rem; flex-wrap: wrap; align-items: center; }}
.wc-apy-badge {{
  flex-shrink: 0; font-family: 'Syne', sans-serif; font-size: 0.82rem; font-weight: 800;
  color: var(--mint); padding: 0.25rem 0.5rem; border-radius: 8px;
  background: var(--mint-dim); border: 1px solid var(--border-bright);
}}
.wc-live-pill {{
  display: inline-flex; align-items: center; gap: 0.3rem; font-size: 0.62rem;
  font-weight: 700; color: var(--mint); text-transform: uppercase; letter-spacing: 0.06em;
}}
.dept-tag.dept-media_video {{ color: #c4b5fd; background: rgba(168,85,247,0.15); }}
.dept-tag.dept-copywriting {{ color: #7dd3fc; background: rgba(56,189,248,0.15); }}
.dept-tag.dept-technical {{ color: #fde68a; background: rgba(255,209,102,0.15); }}

.wc-mission-simple {{
  font-size: 0.78rem; color: var(--muted); line-height: 1.5; margin-bottom: 0.65rem;
  display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden;
}}
.wc-stats-simple {{
  display: flex; gap: 0.75rem; flex-wrap: wrap; align-items: center;
  font-size: 0.72rem; color: var(--dim); margin-bottom: 0.75rem;
}}
.wc-stats-simple strong {{ color: var(--text); }}
.wc-status-inline {{ display: inline-flex; align-items: center; gap: 0.3rem; margin-left: auto; }}

.wc-stake-simple {{
  display: grid; grid-template-columns: 1fr auto; gap: 0.5rem; align-items: stretch;
  margin-bottom: 0.5rem;
}}
.wc-stake-simple .stake-input-wrap {{ margin-bottom: 0; }}
.wc-stake-simple .btn-stake {{ padding: 0.65rem 1rem; }}

.wc-actions-row {{
  display: flex; gap: 0.35rem; flex-wrap: wrap;
}}
.btn-claim-sm, .btn-unstake-sm, .btn-detail-sm {{
  padding: 0.35rem 0.6rem; border-radius: 8px; font-size: 0.68rem; font-weight: 600;
  font-family: inherit; cursor: pointer; border: 1px solid var(--border);
  background: rgba(255,255,255,0.03); color: var(--muted); transition: all 0.2s;
}}
.btn-claim-sm:hover {{ border-color: var(--gold); color: var(--gold); }}
.btn-unstake-sm:hover {{ border-color: var(--danger); color: var(--danger); }}
.btn-detail-sm:hover {{ border-color: var(--cyan); color: var(--cyan); }}
.btn-x402-sm {{
  padding: 0.35rem 0.6rem !important; width: auto !important; margin: 0 !important;
  font-size: 0.68rem !important; border-style: dashed !important;
}}

.invest-extra {{
  margin-top: 1.5rem; font-size: 0.82rem; color: var(--dim);
}}
.invest-extra summary {{ cursor: pointer; padding: 0.5rem 0; font-weight: 600; }}
.invest-extra[open] .leaderboard-section {{ margin-top: 0.75rem; }}

.worker-card .wc-shine, .worker-card .wc-orbit {{ display: none; }}
.worker-card {{ padding: 1rem; }}
.worker-card:hover {{
  transform: translateY(-2px);
  box-shadow: 0 12px 40px rgba(0,0,0,0.35);
  border-color: rgba(var(--card-r), var(--card-g), var(--card-b), 0.4);
}}

/* ── Gelir döngüsü (v24) ── */
.revenue-loop-panel {{
  margin-bottom: 1rem; padding: 1.1rem 1.25rem; border-radius: 16px;
  background: linear-gradient(135deg, rgba(0,255,163,0.07), rgba(56,189,248,0.05));
  border: 1px solid rgba(0,255,163,0.22);
}}
.revenue-loop-head {{
  display: flex; gap: 1rem; align-items: flex-start; justify-content: space-between;
  flex-wrap: wrap; margin-bottom: 0.85rem;
}}
.revenue-kicker {{
  display: block; font-size: 0.62rem; text-transform: uppercase; letter-spacing: 0.12em;
  color: var(--mint); margin-bottom: 0.25rem;
}}
.revenue-loop-head h3 {{
  font-family: 'Syne', sans-serif; font-size: 1.1rem; margin-bottom: 0.3rem;
}}
.revenue-loop-desc {{ font-size: 0.82rem; color: var(--muted); line-height: 1.5; max-width: 36rem; }}
.btn-mesh-proof-prominent {{
  padding: 0.7rem 1.1rem; font-weight: 700; white-space: nowrap;
}}
.revenue-loop-stats {{
  display: grid; grid-template-columns: repeat(4, 1fr); gap: 0.65rem;
}}
.rl-stat {{
  padding: 0.55rem 0.7rem; border-radius: 10px; background: rgba(0,0,0,0.25);
  border: 1px solid var(--border);
}}
.rl-stat span {{
  display: block; font-size: 0.58rem; text-transform: uppercase; letter-spacing: 0.08em;
  color: var(--dim); margin-bottom: 0.2rem;
}}
.rl-stat strong {{ font-family: 'Syne', sans-serif; font-size: 0.95rem; color: var(--mint); }}
.revenue-loop-result {{ margin-top: 0.65rem; font-size: 0.78rem; }}

.stake-mode-banner {{
  display: flex; align-items: center; gap: 0.5rem; margin-bottom: 1rem;
  padding: 0.65rem 0.9rem; border-radius: 12px;
  background: rgba(255,209,102,0.06); border: 1px solid rgba(255,209,102,0.28);
  font-size: 0.78rem; color: #fde68a; line-height: 1.45;
}}
.stake-mode-banner.onchain {{
  background: rgba(0,255,163,0.06); border-color: rgba(0,255,163,0.28); color: var(--mint);
}}
.stake-mode-dot {{
  width: 7px; height: 7px; border-radius: 50%; background: #fbbf24; flex-shrink: 0;
}}
.stake-mode-banner.onchain .stake-mode-dot {{ background: var(--mint); }}

.invest-workers-head {{
  margin-bottom: 0.75rem;
}}
.invest-workers-head h4 {{
  font-family: 'Syne', sans-serif; font-size: 0.95rem; margin-bottom: 0.2rem;
}}
.invest-workers-head p {{ font-size: 0.78rem; color: var(--dim); line-height: 1.5; }}

.tag.api-tag {{
  border-color: rgba(0,255,163,0.35); color: var(--mint); background: rgba(0,255,163,0.08);
  font-size: 0.62rem;
}}
.tag.proof-tag {{
  border-color: rgba(56,189,248,0.35); color: #7dd3fc; background: rgba(56,189,248,0.08);
  font-size: 0.62rem;
}}
.dept-filter-compact {{ margin-top: 0.75rem; margin-bottom: 0.5rem; }}

/* Keyframes */
@keyframes fadeUp {{ from {{ opacity: 0; transform: translateY(24px); }} to {{ opacity: 1; transform: none; }} }}
@keyframes fadeIn {{ from {{ opacity: 0; }} to {{ opacity: 1; }} }}
@keyframes cardReveal {{ from {{ opacity: 0; transform: translateY(20px) scale(0.97); }} to {{ opacity: 1; transform: none; }} }}
@keyframes feedSlide {{ from {{ opacity: 0; transform: translateX(-12px); }} to {{ opacity: 1; transform: none; }} }}
@keyframes livePulse {{ 0%,100% {{ opacity: 1; }} 50% {{ opacity: 0.4; box-shadow: 0 0 12px var(--mint); }} }}
@keyframes meshPulse {{ 0%,100% {{ opacity: 0.35; transform: scale(0.85); }} 50% {{ opacity: 1; transform: scale(1.15); }} }}
@keyframes processBlink {{ 50% {{ opacity: 0.3; transform: scale(1.2); }} }}
@keyframes ringExpand {{ 0% {{ transform: scale(1); opacity: 0.6; }} 100% {{ transform: scale(1.4); opacity: 0; }} }}
@keyframes shimmer {{ 0% {{ background-position: 0% center; }} 100% {{ background-position: 200% center; }} }}
@keyframes shine {{ 0%,100% {{ left: -100%; }} 50% {{ left: 120%; }} }}
@keyframes spin {{ to {{ transform: rotate(360deg); }} }}
@keyframes popIn {{ from {{ transform: scale(0.85); opacity: 0; }} to {{ transform: none; opacity: 1; }} }}
@keyframes modalIn {{ from {{ transform: scale(0.92) translateY(10px); opacity: 0; }} to {{ transform: none; opacity: 1; }} }}

@media (max-width: 900px) {{
  .stats-invest {{ grid-template-columns: 1fr; }}
  .revenue-loop-stats {{ grid-template-columns: repeat(2, 1fr); }}
  .revenue-loop-head {{ flex-direction: column; }}
  .dept-filter-bar {{ flex-direction: column; align-items: stretch; }}
  .color-legend {{ margin-left: 0; }}
  .agents-grid {{ grid-template-columns: 1fr; }}
  .invest-hero {{ grid-template-columns: 1fr; }}
  .portfolio-summary {{ grid-template-columns: 1fr; }}
  .featured-body {{ grid-template-columns: 1fr; }}
  .featured-metrics {{ grid-template-columns: repeat(2, 1fr); }}
  .mesh-proof-hero {{ grid-template-columns: 1fr; }}
  .wc-compact-main {{ grid-template-columns: auto 1fr; }}
  .wc-compact-meta {{ grid-column: 1 / -1; flex-direction: row; justify-content: space-between; align-items: center; }}
  .dept-group-head {{ flex-direction: column; }}
  .agent-detail-metrics {{ grid-template-columns: repeat(2, 1fr); }}
}}
"""
