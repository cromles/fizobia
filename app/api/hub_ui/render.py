from __future__ import annotations

import json
from typing import Dict, List, Optional

from app.config import settings
from app.api.hub_ui.cards import render_featured_worker_card, render_worker_card
from app.api.hub_ui.helpers import esc
from app.api.hub_ui.scripts import hub_scripts
from app.api.hub_ui.styles import hub_styles
from app.investment.schemas import AgentIdentityCard, RevenueSplitConfig
from app.protocol.schemas import AgentManifest
from app.workers.registry import LIVE_WORKER_IDS, LIVE_WORKERS

HUB_UI_BUILD = "2026.06.25-ecosystem-assembly-v14"


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

    featured_html = "".join(
        render_featured_worker_card(
            card,
            manifests.get(card.profile.agent_id),
            LIVE_WORKERS[card.profile.agent_id],
        )
        for card in featured_cards
        if card.profile.agent_id in LIVE_WORKERS
    )

    pool_html = "".join(
        render_worker_card(c, i, manifests.get(c.profile.agent_id), compact=True)
        for i, c in enumerate(other_cards)
    )
    pool_count = len(other_cards)

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
  <title>{esc(brand_title)} — Pasif Dijital İşçi Ortaklığı</title>
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

      <div class="dash-main">
        <header class="dash-header">
          <div>
            <h2>İşçilerin</h2>
            <p id="dashWelcome">Pasif ortaklık paneli</p>
          </div>
          <span style="font-size:0.7rem;color:var(--dim)" id="liveDataLabel">{agent_count} işçi</span>
        </header>

        <div class="stats-grid">
          <div class="stat" style="--i:0"><span class="stat-label">Aktif</span><span class="stat-value mint" id="statAgents">0 / {agent_count}</span></div>
          <div class="stat" style="--i:1"><span class="stat-label">TVL</span><span class="stat-value gold" id="statTvl">$0</span></div>
          <div class="stat" style="--i:2"><span class="stat-label">Gelir</span><span class="stat-value" id="statRevenue">$0</span></div>
          <div class="stat" style="--i:3"><span class="stat-label">Görev/dk</span><span class="stat-value mint" id="statTpm">—</span></div>
        </div>

        <div class="setup-alert hidden" id="setupAlert">
          <div class="setup-alert-copy">
            <strong>Mesh henüz çalışmıyor</strong>
            <p>Gateway açık ama işçi süreçleri kapalı — bu yüzden ağ <em>degraded</em> görünür ve görevler başarısız olur.</p>
          </div>
          <code class="setup-cmd">python3 -m app.run_stack</code>
        </div>

        <div class="toolbar">
          <div class="filter-tabs">
            <button class="filter-tab active" onclick="filterWorkers('all', this)">Canlı işçiler ({len(featured_cards)})</button>
            <button class="filter-tab" onclick="filterWorkers('pool', this)">Havuz ({pool_count})</button>
          </div>
          {trigger_btn}
        </div>

        <div class="mesh-proof-hero" id="meshProofHero">
          <div class="mesh-proof-copy">
            <span class="mesh-proof-kicker">Skeptiklere cevap</span>
            <h3>Mesh Kanıtı</h3>
            <p>4 gerçek dijital işçi <strong>konuşarak</strong> ardışık çalışır — mock yok.</p>
            <ol class="mesh-proof-steps">
              <li>Web-Crawler → canlı haber çeker</li>
              <li>Sentiment-Radar → Fear &amp; Greed + NLP</li>
              <li>Market-Pulse → CoinGecko fiyat</li>
              <li>On-Chain-Watcher → zincir doğrulama</li>
            </ol>
          </div>
          <div class="mesh-proof-action">
            <div class="mesh-proof-price">x402 · ${settings.x402_mesh_proof_price_usd:.2f}</div>
            <button type="button" class="btn-mesh-proof" id="btnMeshProof" onclick="runMeshProof(this)">
              <span class="btn-text">Mesh Kanıtını Çalıştır</span>
              <span class="btn-loader"></span>
            </button>
            <p class="mesh-proof-result" id="meshProofResult">Tek tıkla kanıt üret — gelirin %65'i havuza</p>
          </div>
        </div>

        <div class="featured-slot featured-grid" id="featuredSlot">
          {featured_html}
        </div>

        <details class="worker-pool" id="workerPool">
          <summary>Diğer işçiler · tam mesh ile aktif olur ({pool_count})</summary>
          <div class="workers-grid compact-grid" id="workersGrid">
            {pool_html or '<p style="color:var(--dim)">Havuz boş.</p>'}
          </div>
        </details>
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

  <div class="toast" id="toast"></div>
  {hub_scripts(build, demo_mode, embed_mode, onchain_json)}
</body>
</html>"""
