from __future__ import annotations

import json
from typing import Dict, List, Optional

from app.config import settings
from app.api.hub_ui.cards import render_featured_worker_card, render_worker_card
from app.api.hub_ui.helpers import esc
from app.mesh.departments import DEPARTMENTS
from app.api.hub_ui.scripts import hub_scripts
from app.api.hub_ui.styles import hub_styles
from app.investment.schemas import AgentIdentityCard, RevenueSplitConfig
from app.protocol.schemas import AgentManifest
from app.workers.registry import LIVE_WORKER_IDS, LIVE_WORKERS

HUB_UI_BUILD = "2026.06.26-simple-cards-v22"


def render_hub_dashboard(
    cards: List[AgentIdentityCard],
    split: RevenueSplitConfig,
    manifests: Optional[Dict[str, AgentManifest]] = None,
    build: str = HUB_UI_BUILD,
    demo_mode: bool = True,
    onchain: Optional[Dict[str, object]] = None,
    embed_mode: bool = False,
    brand_title: str = "The Hub",
    brand_sub: str = "Dijital İşçiler",
) -> str:
    manifests = manifests or {}
    agent_count = len(cards)

    featured_cards = [c for c in cards if c.profile.agent_id in LIVE_WORKER_IDS]
    other_cards = [c for c in cards if c.profile.agent_id not in LIVE_WORKER_IDS]
    pool_count = len(cards)

    agents_html_parts: list[str] = []
    idx = 0
    for card in featured_cards:
        if card.profile.agent_id in LIVE_WORKERS:
            agents_html_parts.append(
                render_featured_worker_card(
                    card,
                    manifests.get(card.profile.agent_id),
                    LIVE_WORKERS[card.profile.agent_id],
                )
            )
            idx += 1
    for i, card in enumerate(other_cards):
        agents_html_parts.append(
            render_worker_card(card, idx + i, manifests.get(card.profile.agent_id))
        )
    agents_html = "".join(agents_html_parts)

    onchain = onchain or {}
    chain_name = esc(str(onchain.get("chain_name", "Base Sepolia")))
    chain_connected = onchain.get("connected", False)
    chain_ready = onchain.get("ready", False)
    onchain_status = (
        f"● {chain_name} bağlı · stake {'aktif' if chain_ready else 'RPC modu'}"
        if onchain.get("enabled") and chain_connected
        else "○ Zincir yapılandırılıyor"
    )

    dept_tabs = "".join(
        f'<button type="button" class="filter-tab" data-dept="{esc(spec.code)}" '
        f'onclick="filterByDepartment(\'{esc(spec.code)}\', this)">{esc(spec.label_short)}</button>'
        for spec in DEPARTMENTS.values()
    )

    staking_pct = split.staking_share * 100
    platform_pct = split.platform_share * 100
    operator_pct = split.operator_share * 100

    banner = (
        '<div class="top-banner banner-demo">⚠ Demo modu — gerçek veri için <code>python3 -m app.run_stack</code></div>'
        if demo_mode
        else '<div class="top-banner banner-live" id="topBanner">● Pasif ortaklık — x402 ile gerçek ödeme açık</div>'
    )
    body_class = "has-banner" + (" embed-mode" if embed_mode else "")
    onchain_json = json.dumps(onchain or {"enabled": False, "ready": False})
    trigger_btn = (
        '<button type="button" class="btn-trigger" onclick="triggerLiveRun()">▶ Görev Ver</button>'
        if not demo_mode
        else ""
    )
    landing_hidden = " hidden" if embed_mode else ""

    return f"""<!DOCTYPE html>
<html lang="tr">
<head>
  <meta charset="utf-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover"/>
  <meta name="theme-color" content="#020204"/>
  <meta name="hub-build" content="{esc(build)}"/>
  <meta http-equiv="Cache-Control" content="no-cache, no-store, must-revalidate"/>
  <meta http-equiv="Pragma" content="no-cache"/>
  <meta http-equiv="Expires" content="0"/>
  <title>{esc(brand_title)} — Financial Terminal</title>
  <link rel="preconnect" href="https://fonts.googleapis.com"/>
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin/>
  <link href="https://fonts.googleapis.com/css2?family=DM+Sans:ital,opsz,wght@0,9..40,300;0,9..40,500;0,9..40,600;0,9..40,700;1,9..40,400&family=Syne:wght@600;700;800&display=swap" rel="stylesheet"/>
  <script src="https://cdn.jsdelivr.net/npm/ethers@6.13.4/dist/ethers.umd.min.js"></script>
  <style>{hub_styles(staking_pct, platform_pct, operator_pct)}</style>
</head>
<body class="{body_class}">
  <canvas id="mesh-canvas" aria-hidden="true"></canvas>
  <div class="ambient-gradient" aria-hidden="true"></div>
  {banner}

  <nav class="nav">
    <div class="nav-brand">
      <span class="nav-logo">{esc(brand_title)}</span>
      <span class="nav-sub">{esc(brand_sub)} · {esc(build)}</span>
    </div>
    <div class="nav-actions">
      <div class="yield-ticker" id="yieldTicker" title="Canlı temettü tahmini">
        <span class="yield-label">Temettü</span>
        <span class="yield-value" id="yieldValue">$0.000000</span>
      </div>
      <div class="wallet-pill" id="walletPill">
        <span id="walletShort">0x…</span>
        <button class="btn-disconnect" onclick="disconnectWallet()">×</button>
      </div>
      <button class="btn-nav" id="btnConnect" onclick="openWalletModal()">Başla</button>
    </div>
  </nav>

  <!-- ═══ LANDING ═══ -->
  <main id="landing"{landing_hidden}>
    <section class="hero">
      <div class="hero-badge"><span class="pulse-dot"></span> <span id="heroLiveBadge">{len(featured_cards)} canlı API · mesh kanıtı</span></div>
      <h1>Uyurken<br/><span class="gradient">kazan</span></h1>
      <p class="hero-sub">
        AI işçilerine ortak ol. Sen çalıştırma — mesh 7/24 çalışsın.
        Her görev gelirinin <strong style="color:var(--mint)">%65'i</strong> sana aksın.
      </p>
      <div class="hero-cta">
        <button class="btn-hero primary" onclick="openWalletModal()">Hemen Başla</button>
        <button class="btn-hero ghost" onclick="document.getElementById('meshProofHero')?.scrollIntoView({{behavior:'smooth'}})">Mesh kanıtını gör</button>
      </div>
      <div class="hero-proof-stats" id="heroProofStats">
        <span>— kanıt</span><span>— gelir</span><span>4 gerçek API · ajan diyaloğu</span>
      </div>
    </section>

    <section class="steps" id="steps">
      <div class="step" style="--i:0">
        <div class="step-num">01</div>
        <h3>Cüzdan bağla</h3>
        <p>MetaMask ile 30 saniyede. KYC yok, karmaşık kayıt yok.</p>
      </div>
      <div class="step" style="--i:1">
        <div class="step-num">02</div>
        <h3>İşçi seç, ortak ol</h3>
        <p>USDC stake et. Elektrik ve API maliyetini karşıla, pay al.</p>
      </div>
      <div class="step" style="--i:2">
        <div class="step-num">03</div>
        <h3>Gelir topla</h3>
        <p>İşçin çalıştıkça havuz büyür. İstediğin zaman ödülünü çek.</p>
      </div>
    </section>

    <section class="split-section">
      <h2>Gelir nereye gidiyor?</h2>
      <div class="split-bar">
        <div class="split-seg seg-stake"></div>
        <div class="split-seg seg-platform"></div>
        <div class="split-seg seg-operator"></div>
      </div>
      <div class="split-legend">
        <span><strong>%{staking_pct:.0f}</strong> Sana (staking)</span>
        <span><strong>%{platform_pct:.0f}</strong> Platform</span>
        <span><strong>%{operator_pct:.0f}</strong> Operatör</span>
      </div>
    </section>

    <section class="compare-strip">
      <div class="compare-item">
        <span class="vs">Virtuals</span>
        <span class="us">Biz: iş geliri, onlar: token spekülasyonu</span>
      </div>
      <div class="compare-item">
        <span class="vs">Olas Pearl</span>
        <span class="us">Biz: pasif ortaklık, onlar: sen çalıştır</span>
      </div>
      <div class="compare-item">
        <span class="vs">AgentBazaar</span>
        <span class="us">Biz: yatırımcı katmanı + gelir havuzu</span>
      </div>
      <div class="compare-item">
        <span class="vs">Bittensor</span>
        <span class="us">Biz: görev geliri, onlar: subnet bahsi</span>
      </div>
    </section>

    <div style="text-align:center;padding:3rem 0 2rem">
      <button class="btn-hero primary" onclick="openWalletModal()">İşçilerimi Gör</button>
    </div>
  </main>

  <!-- ═══ DASHBOARD ═══ -->
  <section id="dashboard">
    <div class="dash-layout">
      <aside class="dash-sidebar">
        <div class="mesh-card">
          <h4><span class="pulse-dot" style="width:5px;height:5px;border-radius:50%;background:var(--mint);display:inline-block"></span> Canlı Ağ</h4>
          <div class="mesh-nodes">
            <span class="mesh-node"></span><span class="mesh-line"></span>
            <span class="mesh-node"></span><span class="mesh-line"></span>
            <span class="mesh-node"></span>
          </div>
          <div class="net-row"><span>Durum</span><strong id="netStatus">—</strong></div>
          <div class="net-row"><span>Aktif</span><strong id="netActive">—</strong></div>
          <div class="net-row"><span>TVL</span><strong id="netTvl">—</strong></div>
          <div class="net-row"><span>Çağrı</span><strong id="netCalls">—</strong></div>
        </div>
        <div class="feed-title">Canlı aktivite</div>
        <div class="feed-list" id="activityFeed">
          <div class="feed-item"><span class="feed-meta">Bağlanıyor…</span></div>
        </div>

        <div class="family-mission-banner" id="familyMissionBanner">
          <span class="family-mission-kicker">Synapse Net · Yasin Karademir · Axium</span>
          <div class="hierarchy-chain" id="hierarchyChain">
            <span class="h-tier founder">Yasin</span>
            <span class="h-arrow">→</span>
            <span class="h-tier assistant">Baş Yardımcı</span>
            <span class="h-arrow">→</span>
            <span class="h-tier coord">Koordinatör</span>
            <span class="h-arrow">→</span>
            <span class="h-tier workers">İşçiler</span>
          </div>
          <p class="family-mission-text" id="familyMissionText">Süper organizma — sıfır noktasından çıkıyoruz. Sermayeye kısa yol.</p>
          <div class="autopilot-status" id="autopilotStatus">Otopilot: —</div>
          <div class="organism-phase" id="organismPhase">Faz: Sıfır Noktasından Çıkış</div>
        </div>

        <div class="dialogue-panel" id="agentDialoguePanel">
          <div class="dialogue-header">
            <span class="feed-title" style="margin:0">Ajan diyaloğu</span>
            <span class="dialogue-live-badge"><span class="pulse-dot"></span> Canlı</span>
          </div>
          <div class="dialogue-thread" id="dialogueThread">
            <div class="dialogue-empty">Mesh çalışınca ajanlar birbirleriyle konuşur…</div>
          </div>
        </div>
      </aside>

      <div class="dash-main terminal-shell">
        <header class="terminal-top">
          <div>
            <h2 class="terminal-title">Axium Terminal</h2>
            <p class="terminal-sub" id="dashWelcome">Üretim ve yatırım — tek ekran</p>
          </div>
          <div class="terminal-tabs" role="tablist">
            <button type="button" class="terminal-tab active" data-tab="produce" onclick="switchHubTab('produce', this)">Üretim</button>
            <button type="button" class="terminal-tab" data-tab="invest" onclick="switchHubTab('invest', this)">Yatırım</button>
          </div>
        </header>

        <div id="tabProduce" class="terminal-panel active" role="tabpanel">
          <section class="zero-ui" id="zeroUi">
            <p class="zero-ui-hint">Ne üretelim? Tek cümle yazın — arka plandaki organizma gerisini halleder.</p>
            <div class="zero-ui-row">
              <input type="text" id="userPrompt" class="zero-prompt" autocomplete="off"
                placeholder="30 saniyelik dikey Instagram Reels — son teknoloji haberleri, fon müziği…" />
              <button type="button" class="btn-prompt zero-submit" id="btnPrompt" onclick="submitUserPrompt()">
                <span class="btn-text">Üret</span>
                <span class="btn-loader"></span>
              </button>
            </div>
            <div class="synapse-monitor" id="synapseMonitor">
              <div class="synapse-monitor-label">Synapse Monitor</div>
              <div class="synapse-monitor-inner" id="synapseMonitorInner">
                <div class="synapse-idle">İstem gönderildiğinde ajan diyaloğu burada akar…</div>
              </div>
            </div>
            <div class="arena-overlay hidden" id="arenaOverlay" aria-live="polite">
              <div class="arena-pulse"></div>
              <p>Sinir sistemi aktif — x402 ödeme · paralel arena · kör denetim</p>
            </div>
            <div class="terminal-deliverable hidden" id="arenaResult"></div>
          </section>
        </div>

        <div id="tabInvest" class="terminal-panel" role="tabpanel" hidden>
          <section class="invest-intro">
            <h3>İşçi seç, USDC ile ortak ol</h3>
            <p>Gelirin <strong>%{staking_pct:.0f}'i</strong> stake edenlere gider. Sen çalıştırmazsın — mesh 7/24 çalışır.</p>
          </section>

          <section class="portfolio-strip" id="portfolioStrip">
            <div class="portfolio-empty">Cüzdan bağlayınca pozisyonların burada görünür</div>
          </section>

          <div class="stats-grid stats-compact stats-invest">
            <div class="stat" style="--i:0"><span class="stat-label">TVL</span><span class="stat-value gold" id="statTvl">$0</span></div>
            <div class="stat" style="--i:1"><span class="stat-label">Gelir</span><span class="stat-value" id="statRevenue">$0</span></div>
            <div class="stat" style="--i:2"><span class="stat-label">Ajan</span><span class="stat-value mint" id="statAgents">{agent_count}</span></div>
          </div>

          <div class="dept-filter-bar">
            <div class="filter-tabs" id="deptFilterTabs">
              <button type="button" class="filter-tab active" data-dept="all" onclick="filterByDepartment('all', this)">Tümü</button>
              {dept_tabs}
            </div>
            <div class="color-legend" aria-hidden="true">
              <span class="legend-item legend-media">Video</span>
              <span class="legend-item legend-copy">Makale</span>
              <span class="legend-item legend-tech">Teknik</span>
            </div>
          </div>

          <div class="invest-workers">
            <div class="workers-grid agents-grid" id="workersGrid">
              {agents_html or '<p class="invest-empty">Henüz ajan yok.</p>'}
            </div>
          </div>

          <details class="invest-extra">
            <summary>Sıralama tablosu</summary>
            <section class="leaderboard-section">
              <div class="leaderboard-table-wrap">
                <table class="leaderboard-table" id="leaderboardTable">
                  <thead>
                    <tr>
                      <th>Ajan</th>
                      <th>Departman</th>
                      <th>APY</th>
                      <th>TVL</th>
                      <th></th>
                    </tr>
                  </thead>
                  <tbody id="leaderboardBody">
                    <tr><td colspan="5" class="lb-empty">Yükleniyor…</td></tr>
                  </tbody>
                </table>
              </div>
            </section>
          </details>

          <div class="setup-alert hidden" id="setupAlert">
            <div class="setup-alert-copy">
              <strong>Mesh henüz çalışmıyor</strong>
              <p>Gateway açık ama işçi süreçleri kapalı.</p>
            </div>
            <code class="setup-cmd">python3 -m app.run_stack</code>
          </div>

          <details class="terminal-advanced">
            <summary>Gelişmiş — Mesh Kanıtı · {onchain_status}</summary>
            <div class="mesh-proof-hero mesh-proof-compact" id="meshProofHero">
              <div class="mesh-proof-copy">
                <p>4 gerçek işçi konuşarak çalışır — x402 ${settings.x402_mesh_proof_price_usd:.2f}</p>
              </div>
              <button type="button" class="btn-mesh-proof" id="btnMeshProof" onclick="runMeshProof(this)">
                <span class="btn-text">Mesh Kanıtı</span>
                <span class="btn-loader"></span>
              </button>
              <p class="mesh-proof-result" id="meshProofResult"></p>
            </div>
          </details>
        </div>
      </div>
    </div>
  </section>

  <!-- Splash -->
  <div class="splash" id="splash">
    <div class="splash-inner">
      <div class="splash-ring"></div>
      <h2>Ağa bağlanılıyor</h2>
      <p>İşçileriniz hazırlanıyor…</p>
    </div>
  </div>

  <!-- Wallet modal -->
  <div class="modal-overlay" id="walletModal" onclick="if(event.target===this)closeWalletModal()">
    <div class="modal">
      <button class="modal-close" onclick="closeWalletModal()">×</button>
      <h2>Başlayalım</h2>
      <p>Dijital işçilerine ortak olmak için cüzdanını bağla. 30 saniye sürer.</p>
      <button class="btn-modal primary" onclick="connectMetaMask()">MetaMask ile Bağlan</button>
      <details>
        <summary>Diğer seçenekler</summary>
        <input type="text" id="walletInput" placeholder="0x…" autocomplete="off"/>
        <button class="btn-modal ghost" onclick="connectWallet()">Adres ile devam</button>
        <button class="btn-modal ghost" onclick="connectDemoWallet()">Demo cüzdan</button>
      </details>
    </div>
  </div>

  <!-- Agent detail modal -->
  <div class="modal-overlay agent-detail-overlay" id="agentDetailModal" onclick="if(event.target===this)closeAgentDetail()">
    <div class="modal agent-detail-modal">
      <button class="modal-close" onclick="closeAgentDetail()">×</button>
      <div id="agentDetailBody">
        <div class="agent-detail-loading">Ajan dosyası yükleniyor…</div>
      </div>
    </div>
  </div>

  <div class="toast" id="toast"></div>
  {hub_scripts(build, demo_mode, embed_mode, onchain_json)}
</body>
</html>"""
