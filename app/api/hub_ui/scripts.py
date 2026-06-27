from app.config import settings


def hub_scripts(build: str, demo_mode: bool, embed_mode: bool, onchain_json: str) -> str:
    demo = "true" if demo_mode else "false"
    embed = "true" if embed_mode else "false"
    return f"""
<script>
(function() {{
  const WALLET_KEY = 'oam_hub_wallet';
  const ONCHAIN_CONFIG = {onchain_json};
  const DEMO_MODE = {demo};
  const EMBED_MODE = {embed};
  const ERC20_ABI = [
    'function approve(address spender, uint256 amount) returns (bool)',
    'function balanceOf(address account) view returns (uint256)',
  ];
  const POOL_ABI = [
    'function stake(uint256 amount)',
    'function unstake(uint256 shareAmount)',
    'function claimRewards()',
    'function pendingReward(address user) view returns (uint256)',
  ];

  let liveTimer = null, processTimer = null, liveSocket = null, dialogueTimer = null;
  let lastEventCount = 0, lastDialogueCount = 0, dialogueThreadId = null;
  const agentNameMap = {{}};
  const AGENT_LABELS = {{
    'oam.founder.operator': 'Yasin Karademir',
    'oam.assistant.chief.local': 'Baş Yardımcı',
    'oam.orchestrator.pipeline.local': 'Koordinatör',
    'oam.mesh.workers': 'İşçiler',
    'oam.fetcher.web.local': 'Web-Crawler',
    'oam.analyst.sentiment.local': 'Sentiment',
    'oam.analyst.market.local': 'Market',
    'oam.watcher.onchain.local': 'On-Chain',
    'oam.media.story.local': 'Story-Weaver',
    'oam.media.brand.local': 'Brand-Voice',
    'oam.media.outreach.local': 'Outreach',
    'oam.media.proof.local': 'Proof-Broadcast',
    'oam.capital.fundraise.local': 'Fund-Radar',
    '*': 'Mesh',
  }};

  function $(id) {{ return document.getElementById(id); }}
  function getWallet() {{ return localStorage.getItem(WALLET_KEY) || ''; }}
  function shortAddr(a) {{ return a.length > 12 ? a.slice(0,6) + '…' + a.slice(-4) : a; }}

  /* ── Mesh canvas background ── */
  function initMeshCanvas() {{
    const canvas = $('mesh-canvas');
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    let w, h, nodes = [], animId;

    function resize() {{
      w = canvas.width = window.innerWidth;
      h = canvas.height = window.innerHeight;
      const count = Math.min(48, Math.floor(w * h / 28000));
      nodes = Array.from({{length: count}}, () => ({{
        x: Math.random() * w, y: Math.random() * h,
        vx: (Math.random() - 0.5) * 0.35, vy: (Math.random() - 0.5) * 0.35,
        r: Math.random() * 1.5 + 0.5,
      }}));
    }}

    function draw() {{
      ctx.clearRect(0, 0, w, h);
      const maxDist = 140;
      for (let i = 0; i < nodes.length; i++) {{
        const a = nodes[i];
        a.x += a.vx; a.y += a.vy;
        if (a.x < 0 || a.x > w) a.vx *= -1;
        if (a.y < 0 || a.y > h) a.vy *= -1;
        for (let j = i + 1; j < nodes.length; j++) {{
          const b = nodes[j];
          const dx = a.x - b.x, dy = a.y - b.y;
          const dist = Math.sqrt(dx*dx + dy*dy);
          if (dist < maxDist) {{
            const alpha = (1 - dist / maxDist) * 0.12;
            ctx.strokeStyle = `rgba(0,255,163,${{alpha}})`;
            ctx.lineWidth = 0.5;
            ctx.beginPath(); ctx.moveTo(a.x, a.y); ctx.lineTo(b.x, b.y); ctx.stroke();
          }}
        }}
        ctx.fillStyle = 'rgba(0,255,163,0.35)';
        ctx.beginPath(); ctx.arc(a.x, a.y, a.r, 0, Math.PI * 2); ctx.fill();
      }}
      animId = requestAnimationFrame(draw);
    }}

    resize();
    draw();
    window.addEventListener('resize', resize);
    document.addEventListener('visibilitychange', () => {{
      if (document.hidden) cancelAnimationFrame(animId);
      else draw();
    }});
  }}

  /* ── UI state ── */
  function updateWalletUI() {{
    const w = getWallet();
    const pill = $('walletPill');
    const btn = $('btnConnect');
    const dash = $('dashboard');
    document.body.classList.toggle('has-wallet', !!w);
    if (w) {{
      pill.classList.add('show');
      $('walletShort').textContent = shortAddr(w);
      btn.style.display = 'none';
      dash.classList.add('visible');
      $('dashWelcome').textContent = shortAddr(w) + ' · ortaklık paneli';
      if (sessionStorage.getItem('hub_just_connected')) {{
        sessionStorage.removeItem('hub_just_connected');
      }}
      startLiveFeed();
      startDialoguePoll();
      refreshPortfolio();
      switchHubTab('invest', document.querySelector('.terminal-tab[data-tab="invest"]'));
    }} else {{
      pill.classList.remove('show');
      btn.style.display = 'block';
      dash.classList.remove('visible');
      stopLiveFeed();
    }}
  }}

  function showSplash() {{
    const s = $('splash');
    s.classList.add('show');
    setTimeout(() => {{
      s.classList.remove('show');
      startLiveFeed();
      startDialoguePoll();
      if (DEMO_MODE) startProcessAnimation();
    }}, 1400);
  }}

  function stopLiveFeed() {{
    if (liveTimer) clearInterval(liveTimer);
    if (processTimer) clearInterval(processTimer);
    if (dialogueTimer) clearInterval(dialogueTimer);
    if (liveSocket) {{ liveSocket.close(); liveSocket = null; }}
    liveTimer = processTimer = dialogueTimer = null;
  }}

  function labelAgent(id) {{
    if (!id) return '—';
    if (id === '*') return AGENT_LABELS['*'];
    return AGENT_LABELS[id] || agentNameMap[id] || id.split('.').slice(-2, -1)[0] || id;
  }}

  function escapeHtml(s) {{
    return String(s || '')
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;');
  }}

  async function refreshMission() {{
    try {{
      const res = await fetch('/hub/ecosystem/mission?_=' + Date.now(), {{ cache: 'no-store' }});
      if (!res.ok) return;
      const data = await res.json();
      const el = $('familyMissionText');
      if (el && data.motto) {{
        el.textContent = data.motto + ' ' + (data.hierarchy || '');
      }}
    }} catch (_) {{}}
  }}

  async function refreshHierarchy() {{
    try {{
      const [hRes, aRes, mRes] = await Promise.all([
        fetch('/hub/hierarchy?_=' + Date.now(), {{ cache: 'no-store' }}),
        fetch('/hub/autopilot?_=' + Date.now(), {{ cache: 'no-store' }}),
        fetch('/hub/manifest?_=' + Date.now(), {{ cache: 'no-store' }}),
      ]);
      if (hRes.ok) {{
        const h = await hRes.json();
        const el = $('familyMissionText');
        if (el && h.motto) el.textContent = h.motto + ' — bahane yok, kısa yol var.';
      }}
      if (mRes.ok) {{
        const m = await mRes.json();
        const phase = $('organismPhase');
        if (phase && m.founder) {{
          phase.textContent = 'Faz: ' + (m.founder.current_phase_name || 'Sıfır Noktası');
        }}
        const el = $('familyMissionText');
        if (el && m.synapse_vision) {{
          el.textContent = String(m.synapse_vision).slice(0, 140) + '…';
        }} else if (el && m.organism) {{
          el.textContent = String(m.organism).slice(0, 120) + '…';
        }}
      }}
      if (aRes.ok) {{
        const a = await aRes.json();
        const ap = $('autopilotStatus');
        if (ap) {{
          const cycles = a.cycles_completed || 0;
          const running = a.running ? 'aktif' : 'beklemede';
          ap.textContent = 'Otopilot: ' + running + ' · ' + cycles + ' döngü · sermaye modu';
        }}
      }}
    }} catch (_) {{}}
  }}

  function renderDialogueMessages(messages) {{
    const thread = $('dialogueThread');
    if (!thread) return;
    if (!messages || !messages.length) {{
      thread.innerHTML = '<div class="dialogue-empty">Henüz mesaj yok — Mesh Kanıtı çalıştırın</div>';
      return;
    }}
    const ordered = [...messages].reverse();
    thread.innerHTML = ordered.map((m, i) => {{
      const isCoord = m.from === 'oam.orchestrator.pipeline.local';
      const intent = (m.intent || 'inform').replace(/[^a-z_]/g, '');
      return (
        '<div class="dialogue-msg ' + (isCoord ? 'coord ' : '') + 'intent-' + intent + '" style="--delay:' + (i * 0.04) + 's">' +
          '<div class="dialogue-meta">' +
            '<span class="dialogue-from">' + escapeHtml(labelAgent(m.from)) + '</span>' +
            '<span class="dialogue-arrow">→</span>' +
            '<span class="dialogue-to">' + escapeHtml(labelAgent(m.to)) + '</span>' +
            '<span class="dialogue-intent">' + escapeHtml(intent) + '</span>' +
          '</div>' +
          '<div class="dialogue-bubble">' + escapeHtml(m.text) + '</div>' +
        '</div>'
      );
    }}).join('');
    thread.scrollTop = thread.scrollHeight;
  }}

  async function refreshDialogue(forceThread) {{
    try {{
      let url = '/hub/ecosystem/dialogue?limit=40';
      const tid = forceThread || dialogueThreadId;
      if (tid) url += '&thread_id=' + encodeURIComponent(tid);
      const res = await fetch(url + '&_=' + Date.now(), {{ cache: 'no-store' }});
      if (!res.ok) return;
      const data = await res.json();
      if (!forceThread && data.count === lastDialogueCount) return;
      lastDialogueCount = data.count;
      renderDialogueMessages(data.messages);
    }} catch (_) {{}}
  }}

  function startDialoguePoll() {{
    refreshMission();
    refreshHierarchy();
    refreshDialogue();
    if (dialogueTimer) clearInterval(dialogueTimer);
    dialogueTimer = setInterval(() => {{ refreshDialogue(); refreshHierarchy(); }}, 3500);
  }}

  function startLiveFeed() {{
    if (!DEMO_MODE && window.WebSocket) {{
      try {{
        const proto = location.protocol === 'https:' ? 'wss:' : 'ws:';
        liveSocket = new WebSocket(proto + '//' + location.host + '/hub/ws/live');
        liveSocket.onmessage = (ev) => applyLiveSnapshot(JSON.parse(ev.data));
        liveSocket.onerror = () => {{ liveSocket = null; pollLiveFallback(); }};
        return;
      }} catch (_) {{}}
    }}
    pollLiveFallback();
  }}

  function pollLiveFallback() {{
    refreshLive();
    refreshDialogue();
    liveTimer = setInterval(refreshLive, 4000);
    if (!dialogueTimer) dialogueTimer = setInterval(refreshDialogue, 3500);
  }}

  async function refreshLive() {{
    try {{
      const res = await fetch('/hub/live');
      if (res.ok) applyLiveSnapshot(await res.json());
    }} catch (_) {{}}
  }}

  function applyLiveSnapshot(data) {{
    updateNetworkStats(data.network);
    updateActivityFeed(data.activity_feed, data.network);
    updateWorkerCards(data.agents);
    const label = $('liveDataLabel');
    if (label && data.network) {{
      label.textContent = data.network.reachable_agents + ' / ' + data.network.total_agents +
        ' çevrimiçi · ' + (data.network.real_event_count || 0) + ' faaliyet';
    }}
  }}

  function updateNetworkStats(net) {{
    if (!net) return;
    const online = net.status === 'online';
    const statusEl = $('netStatus');
    statusEl.textContent = online ? '● Online' : 'degraded';
    statusEl.className = online ? 'net-online' : 'net-degraded';
    $('netActive').textContent = net.active_agents + ' / ' + net.total_agents;
    $('netTvl').textContent = '$' + net.total_tvl_usd.toLocaleString('tr-TR');
    $('netCalls').textContent = formatNum(net.total_calls);
    animateStat('statAgents', net.active_agents + ' / ' + net.total_agents);
    animateStat('statTvl', '$' + Math.round(net.total_tvl_usd).toLocaleString('tr-TR'));
    animateStat('statRevenue', '$' + net.total_revenue_usd.toFixed(2));
    const tpm = Number(net.tasks_per_min || 0);
    $('statTpm').textContent = tpm > 0 ? '~' + tpm.toFixed(1) : '—';

    const alert = $('setupAlert');
    const banner = $('topBanner');
    if (alert) alert.classList.toggle('hidden', !net.mesh_offline);
    if (banner && !DEMO_MODE) {{
      banner.className = online
        ? 'top-banner banner-live'
        : 'top-banner banner-warn';
      banner.textContent = online
        ? '● Mesh çalışıyor — gelirin %65\\'i staking havuzuna'
        : '⚠ Mesh kapalı — x402 hâlâ çalışır · tam ağ için python3 -m app.run_stack';
    }}
  }}

  function animateStat(id, val) {{
    const el = $(id);
    if (!el || el.textContent === String(val)) return;
    el.style.transform = 'scale(1.08)';
    el.style.color = 'var(--mint)';
    el.textContent = val;
    setTimeout(() => {{ el.style.transform = ''; el.style.color = ''; }}, 300);
  }}

  function formatNum(n) {{
    if (n >= 1e6) return (n/1e6).toFixed(1) + 'M';
    if (n >= 1e3) return (n/1e3).toFixed(1) + 'K';
    return String(n);
  }}

  function updateActivityFeed(feed, net) {{
    const el = $('activityFeed');
    if (net && net.mesh_offline) {{
      el.innerHTML = `<div class="feed-item feed-setup">
        <span class="feed-agent">İşçi süreçleri kapalı</span>
        <div class="feed-meta">Gateway çalışıyor ama tam ekosistem başlamadı. <code>${{net.setup_command || 'python3 -m app.run_stack'}}</code> ile 15 mikro ajanı açın. x402 ödemesi gateway üzerinden çalışmaya devam eder.</div>
      </div>`;
      return;
    }}
    if (!feed || !feed.length) {{
      el.innerHTML = '<div class="feed-item"><span class="feed-meta">İşçiler hazır — görev bekliyor</span></div>';
      return;
    }}
    const isNew = feed.length > lastEventCount;
    lastEventCount = feed.length;
    const items = feed.filter(item => item.success !== false).slice(0, 14);
    const display = items.length ? items : feed.slice(0, 6);
    el.innerHTML = display.map((item, i) => {{
      const cls = i === 0 && isNew ? 'feed-item new' : 'feed-item';
      const sim = item.simulated
        ? ' <span style="color:#fbbf24">DEMO</span>'
        : ' <span style="color:var(--mint)">CANLI</span>';
      const headline = item.message || (item.worker_name || 'İşçi') + ' görev tamamladı';
      const failed = item.success === false;
      return `<div class="${{cls}}${{failed ? ' feed-fail' : ''}}">
        <span class="feed-agent">${{headline}}</span>${{sim}}
        <div class="feed-meta">+${{(item.staking_usd || item.gross_usd || 0).toFixed(4)}} havuza · ${{Math.round(item.latency_ms || 0)}}ms</div>
      </div>`;
    }}).join('');
  }}

  function updateWorkerCards(agents) {{
    if (!agents) return;
    agents.forEach(a => {{
      agentNameMap[a.agent_id] = a.display_name;
      const card = document.querySelector('[data-agent="' + a.agent_id + '"]');
      if (!card) return;
      const dot = card.querySelector('.status-dot');
      const label = card.querySelector('.status-label');
      const labels = {{
        active: a.reachable ? 'Çalışıyor' : 'Kayıtlı',
        standby: 'Hazır',
        offline: 'Kapalı',
        degraded: 'Düşük',
      }};
      if (dot) dot.className = 'status-dot ' + a.status;
      if (label) label.textContent = labels[a.status] || a.status;
      card.classList.toggle('is-live', a.status === 'active');
      const apyEl = card.querySelector('.apy');
      if (apyEl && a.apy != null) apyEl.textContent = '%' + a.apy.toFixed(1);
    }});
  }}

  window.filterWorkers = function(cls, btn) {{
    document.querySelectorAll('.filter-tab').forEach(t => t.classList.remove('active'));
    btn.classList.add('active');
    const featured = $('featuredSlot');
    const pool = $('workerPool');
    if (cls === 'all') {{
      if (featured) featured.style.display = '';
      if (pool) pool.open = false;
    }} else {{
      if (featured) featured.style.display = 'none';
      if (pool) pool.open = true;
    }}
  }};

  let activeDepartment = 'all';

  function applyDepartmentFilter(code) {{
    const cards = document.querySelectorAll('.worker-card[data-department]');
    cards.forEach(card => {{
      const dept = card.getAttribute('data-department') || '';
      const show = code === 'all' || dept === code;
      card.style.display = show ? '' : 'none';
    }});
  }}

  window.filterByDepartment = function(code, btn) {{
    activeDepartment = code || 'all';
    document.querySelectorAll('#deptFilterTabs .filter-tab').forEach(t => t.classList.remove('active'));
    if (btn) btn.classList.add('active');
    applyDepartmentFilter(activeDepartment);
    refreshLeaderboard();
  }};

  function startProcessAnimation() {{
    const cards = Array.from(document.querySelectorAll('.worker-card'));
    if (!cards.length) return;
    let idx = 0;
    const tasks = ['veri çekiliyor…', 'analiz yapılıyor…', 'sentez üretiliyor…', 'doğrulama…', 'gelir dağıtılıyor…'];
    processTimer = setInterval(() => {{
      cards.forEach(c => c.classList.remove('processing'));
      const card = cards[idx % cards.length];
      card.classList.add('processing');
      const taskEl = card.querySelector('.task-text');
      if (taskEl) taskEl.textContent = tasks[idx % tasks.length];
      idx++;
    }}, 2600);
  }}

  function isQuickComposePrompt(text) {{
    const t = (text || '').toLowerCase();
    if (/reels|instagram|tiktok|shorts|\bvideo\b|30\s*saniye|dikey|reel\b/.test(t)) return false;
    return true;
  }}

  function startSynapseProgress(monitor, prompt) {{
    if (!monitor) return null;
    const quick = isQuickComposePrompt(prompt);
    const steps = quick
      ? [
          '[x402] Ödeme doğrulandı',
          '[Lyric-Weaver] Uzman taslak üretiyor…',
          '[Brand-Voice] Üslup düzenlemesi…',
          '[Immune-Critic] Kalite denetimi…',
          '[Orkestratör] Tamamlanıyor…',
        ]
      : [
          '[x402] Ödeme doğrulandı',
          '[Arena] Gladyatörler paralel yazıyor…',
          '[Immune-Critic] Kör denetim…',
          '[Render] Reels spec…',
        ];
    let i = 0;
    monitor.innerHTML = '<div class="synapse-line">' + steps[0] + '</div>';
    return setInterval(() => {{
      i = (i + 1) % steps.length;
      const div = document.createElement('div');
      div.className = 'synapse-line';
      div.textContent = steps[i];
      monitor.appendChild(div);
      monitor.scrollTop = monitor.scrollHeight;
    }}, 900);
  }}

  async function submitUserPrompt() {{
    const input = $('userPrompt');
    const btn = $('btnPrompt');
    const overlay = $('arenaOverlay');
    const resultEl = $('arenaResult');
    const monitor = $('synapseMonitorInner');
    const prompt = (input?.value || '').trim();
    if (!prompt || prompt.length < 8) {{
      showToast('En az 8 karakterlik bir istem yazın', true);
      return;
    }}
    btn?.classList.add('loading');
    overlay?.classList.remove('hidden');
    resultEl?.classList.add('hidden');
    document.body.classList.add('arena-frozen');
    const progressTimer = startSynapseProgress(monitor, prompt);
    try {{
      const proof = JSON.stringify({{
        amount_usdc: 0.10,
        payer: getWallet() || '0x' + 'a'.repeat(40),
        payment_id: 'arena_' + Date.now(),
      }});
      const res = await fetch('/hub/prompt', {{
        method: 'POST',
        headers: {{
          'Content-Type': 'application/json',
          'X-Payment-Proof': proof,
        }},
        body: JSON.stringify({{ prompt, background_music: true, duration_sec: 30 }}),
      }});
      const data = await res.json();
      if (res.status === 402) {{
        showToast('x402 ödeme gerekli', true);
        return;
      }}
      if (!res.ok) {{
        showToast(data.detail || 'Arena hatası', true);
        return;
      }}
      streamSynapseLog(data.result?.synapse_log || ['[Orkestratör] Tamamlandı.']);
      const w = data.result?.winner;
      const render = data.result?.render;
      const isCompose = data.mode === 'quick_compose' || data.result?.mode === 'quick_compose';
      if (resultEl) {{
        resultEl.classList.remove('hidden');
        if (isCompose) {{
          resultEl.innerHTML = (
            '<h4>Metin hazır</h4>' +
            '<p><strong>Ajan:</strong> ' + (w?.display_name || 'Story-Weaver') +
            ' · ~' + Math.round((data.result?.total_latency_ms || 0) / 1000) + ' sn</p>' +
            '<pre class="compose-output">' + (render?.text || w?.script || '').replace(/</g, '&lt;') + '</pre>'
          );
        }} else {{
          resultEl.innerHTML = (
            '<h4>Nihai ürün</h4>' +
            '<p><strong>Kazanan:</strong> ' + (w?.display_name || '—') +
            ' · denetçi skoru ' + ((w?.critic_score || 0) * 100).toFixed(0) + '%</p>' +
            '<p><strong>Script:</strong> ' + (w?.script || '').slice(0, 280) + '</p>' +
            '<p><strong>Format:</strong> ' + (render?.format || '') + ' · ' + (render?.duration_sec || 30) + 's · ' +
            (render?.audio?.background_music ? 'fon müziği açık' : 'sessiz') + '</p>'
          );
        }}
      }}
      showToast(data.message || 'Ürün hazır');
      refreshDialogue();
      refreshLeaderboard();
    }} catch (err) {{
      showToast(err.message || 'Bağlantı hatası', true);
    }} finally {{
      if (progressTimer) clearInterval(progressTimer);
      btn?.classList.remove('loading');
      overlay?.classList.add('hidden');
      document.body.classList.remove('arena-frozen');
    }}
  }}
  window.submitUserPrompt = submitUserPrompt;

  function streamSynapseLog(lines) {{
    const inner = $('synapseMonitorInner');
    if (!inner || !lines?.length) return;
    inner.innerHTML = '';
    let i = 0;
    const tick = () => {{
      if (i >= lines.length) return;
      const div = document.createElement('div');
      div.className = 'synapse-line';
      div.textContent = lines[i];
      inner.appendChild(div);
      inner.scrollTop = inner.scrollHeight;
      i += 1;
      setTimeout(tick, 260);
    }};
    tick();
  }}

  function switchHubTab(tab, btn) {{
    document.querySelectorAll('.terminal-tab').forEach(t => t.classList.remove('active'));
    if (btn) btn.classList.add('active');
    const produce = $('tabProduce');
    const invest = $('tabInvest');
    if (produce) {{
      produce.classList.toggle('active', tab === 'produce');
      produce.hidden = tab !== 'produce';
    }}
    if (invest) {{
      invest.classList.toggle('active', tab === 'invest');
      invest.hidden = tab !== 'invest';
    }}
    if (tab === 'invest') {{
      refreshLeaderboard();
      refreshPortfolio();
      refreshRevenueLoop();
    }}
  }}
  window.switchHubTab = switchHubTab;

  async function refreshRevenueLoop() {{
    try {{
      const res = await fetch('/hub/revenue/summary?_=' + Date.now(), {{ cache: 'no-store' }});
      if (!res.ok) return;
      const data = await res.json();
      const totals = data.totals || {{}};
      const rlX402 = $('rlX402');
      const rlStaking = $('rlStaking');
      const rlProofs = $('rlProofs');
      const rlTvl = $('rlTvl');
      if (rlX402) rlX402.textContent = '$' + Number(totals.x402_revenue_usd || 0).toFixed(2);
      if (rlStaking) rlStaking.textContent = '$' + Number(totals.staking_pool_usd || 0).toFixed(2);
      if (rlProofs) rlProofs.textContent = String(totals.mesh_proofs || 0);
      if (rlTvl) rlTvl.textContent = '$' + Number(totals.tvl_usd || 0).toFixed(0);
      const stakeBanner = $('stakeModeBanner');
      const stakeLabel = $('stakeModeLabel');
      if (stakeBanner && stakeLabel) {{
        const mode = data.stake_mode || 'ledger_demo';
        stakeBanner.classList.toggle('onchain', mode === 'onchain');
        let text = data.stake_mode_label || 'Demo defter — gelir gerçek';
        const oc = data.onchain || {{}};
        if (mode !== 'onchain' && oc.deployer && !oc.deploy_ready) {{
          if (oc.funding && oc.funding.bridge_needed) {{
            text += ' · Ethereum Sepolia\\'da ETH var → Base köprüsü: testnets.superbridge.app/base-sepolia';
          }} else {{
            text += ' · Factory deploy: ' + shortAddr(oc.deployer) + ' cüzdana Base Sepolia ETH';
          }}
        }}
        stakeLabel.textContent = text;
      }}
      (data.agents || []).forEach(a => {{
        agentNameMap[a.agent_id] = a.display_name;
      }});
    }} catch (_) {{}}
  }}
  window.refreshRevenueLoop = refreshRevenueLoop;

  function lbEsc(s) {{
    return String(s || '').replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/"/g, '&quot;');
  }}

  const TIER_LABELS = {{
    probation: 'Deneme',
    active: 'Aktif',
    core: 'Çekirdek',
    culled: 'Elenmiş',
  }};

  async function refreshLeaderboard() {{
    const tbody = $('leaderboardBody');
    if (!tbody) return;
    try {{
      const qs = activeDepartment && activeDepartment !== 'all'
        ? '?department_code=' + encodeURIComponent(activeDepartment) + '&_=' + Date.now()
        : '?_=' + Date.now();
      const res = await fetch('/hub/leaderboard' + qs, {{ cache: 'no-store' }});
      if (!res.ok) return;
      const data = await res.json();
      const rows = data.agents || [];
      const sub = $('leaderboardSub');
      if (sub && activeDepartment !== 'all') {{
        const deptLabel = document.querySelector('#deptFilterTabs .filter-tab.active')?.textContent || activeDepartment;
        sub.textContent = deptLabel + ' departmanı · ' + rows.length + ' ajan · TVL $' + Number(data.total_tvl_usd || 0).toFixed(0);
      }} else if (sub) {{
        sub.textContent = rows.length + ' otonom ajan · toplam TVL $' + Number(data.total_tvl_usd || 0).toFixed(0);
      }}
      if (!rows.length) {{
        tbody.innerHTML = '<tr><td colspan="5" class="lb-empty">Veri yok</td></tr>';
        return;
      }}
      tbody.innerHTML = rows.map((a, i) => (
        '<tr class="lb-row">' +
        '<td><strong>' + lbEsc(a.display_name) + '</strong><br/><span class="lb-token">' + lbEsc(a.token_symbol) + '</span></td>' +
        '<td><span class="lb-dept">' + lbEsc(a.department_label || '—') + '</span></td>' +
        '<td class="lb-apy">' + Number(a.apy_pct || 0).toFixed(1) + '%</td>' +
        '<td>$' + Number(a.tvl_usd || 0).toFixed(0) + '</td>' +
        '<td><button type="button" class="lb-stake" onclick="focusStakeAgent(\\'' + a.agent_id + '\\')">Seç</button></td>' +
        '</tr>'
      )).join('');
    }} catch (_) {{}}
  }}
  window.refreshLeaderboard = refreshLeaderboard;

  window.focusStakeAgent = function(agentId) {{
    switchHubTab('invest', document.querySelector('.terminal-tab[data-tab="invest"]'));
    const card = document.querySelector('[data-agent="' + agentId + '"]');
    if (card) {{
      card.scrollIntoView({{ behavior: 'smooth', block: 'center' }});
      card.classList.add('highlight-stake');
      setTimeout(() => card.classList.remove('highlight-stake'), 2400);
      const input = card.querySelector('.amount');
      if (input) input.focus();
    }} else {{
      openAgentDetail(agentId);
    }}
  }};

  function renderAgentDetailHtml(card) {{
    const p = card.profile || {{}};
    const h = card.health || {{}};
    const f = card.finance || {{}};
    const pool = card.pool || {{}};
    const useCases = (p.use_cases || []).map(u => '<li>' + lbEsc(u) + '</li>').join('');
    const risk = {{ düşük: 'Düşük', orta: 'Orta', yüksek: 'Yüksek' }}[p.risk_level] || p.risk_level;
    return (
      '<div class="agent-detail-header">' +
      '<span class="agent-detail-class">' + lbEsc(p.agent_class || '') + '</span>' +
      '<h2>' + lbEsc(p.display_name || p.agent_id) + '</h2>' +
      '<p class="agent-detail-mission">' + lbEsc(p.mission || '') + '</p>' +
      '<div class="agent-detail-tags">' +
      '<span class="tag class">' + lbEsc(p.token_symbol || '') + '</span>' +
      '<span class="tag risk">' + lbEsc(risk) + ' risk</span>' +
      '</div></div>' +
      '<p class="agent-detail-desc">' + lbEsc(p.long_description || p.mission || '') + '</p>' +
      '<div class="agent-detail-metrics">' +
      '<div><span>APY</span><strong class="mint">%' + Number(f.estimated_apy || 0).toFixed(1) + '</strong></div>' +
      '<div><span>TVL</span><strong>$' + Number(f.staking_pool_tvl_usd || 0).toFixed(0) + '</strong></div>' +
      '<div><span>24s Hacim</span><strong>$' + Number(f.volume_24h_usd || 0).toFixed(0) + '</strong></div>' +
      '<div><span>Başarı</span><strong>' + Math.round((h.success_rate || 0) * 100) + '%</strong></div>' +
      '<div><span>Toplam gelir</span><strong>$' + Number(f.total_revenue_usd || 0).toFixed(2) + '</strong></div>' +
      '<div><span>Token fiyat</span><strong>$' + Number(f.token_price_usdc || 0).toFixed(4) + '</strong></div>' +
      '</div>' +
      (p.investment_thesis ? '<div class="agent-detail-thesis"><strong>Yatırım tezi</strong><p>' + lbEsc(p.investment_thesis) + '</p></div>' : '') +
      (useCases ? '<div class="agent-detail-usecases"><strong>Kullanım senaryoları</strong><ul>' + useCases + '</ul></div>' : '') +
      (p.staking_covers ? '<div class="agent-detail-covers"><strong>Staking karşılar</strong><p>' + lbEsc(p.staking_covers) + '</p></div>' : '') +
      '<div class="agent-detail-pool">' +
      '<span>Havuz stake: $' + Number(pool.total_staked_usdc || 0).toFixed(2) + '</span>' +
      '<span>Biriken ödül: $' + Number(pool.rewards_accrued_usdc || 0).toFixed(2) + '</span>' +
      '</div>' +
      '<button type="button" class="btn-modal primary" onclick="closeAgentDetail(); focusStakeAgent(\\'' + (p.agent_id || '') + '\\')">Bu ajana ortak ol</button>'
    );
  }}

  window.openAgentDetail = async function(agentId) {{
    const modal = $('agentDetailModal');
    const body = $('agentDetailBody');
    if (!modal || !body) return;
    modal.classList.add('open');
    body.innerHTML = '<div class="agent-detail-loading">Ajan dosyası yükleniyor…</div>';
    try {{
      const res = await fetch('/hub/agents/' + encodeURIComponent(agentId) + '?_=' + Date.now());
      if (!res.ok) throw new Error('Ajan bulunamadı');
      const card = await res.json();
      body.innerHTML = renderAgentDetailHtml(card);
    }} catch (err) {{
      body.innerHTML = '<p class="agent-detail-error">' + lbEsc(err.message || 'Hata') + '</p>';
    }}
  }};

  window.closeAgentDetail = function() {{
    $('agentDetailModal')?.classList.remove('open');
  }};

  async function refreshPortfolio() {{
    const strip = $('portfolioStrip');
    if (!strip) return;
    const w = getWallet();
    if (!w) {{
      strip.innerHTML = '<div class="portfolio-empty">Cüzdan bağlayın — pozisyonlarınız ve bekleyen ödüller burada görünür</div>';
      return;
    }}
    try {{
      const res = await fetch('/hub/positions/' + encodeURIComponent(w) + '?_=' + Date.now());
      if (!res.ok) throw new Error();
      const positions = await res.json();
      if (!positions.length) {{
        strip.innerHTML = '<div class="portfolio-empty">Henüz pozisyon yok — aşağıdan bir işçiye <strong>ortak ol</strong></div>';
        return;
      }}
      const totalStaked = positions.reduce((s, p) => s + (p.staked_usdc || 0), 0);
      const totalPending = positions.reduce((s, p) => s + (p.rewards_pending_usdc || 0), 0);
      const posHtml = positions.map(p => {{
        const name = agentNameMap[p.agent_id] || p.agent_id.split('.').pop();
        return (
          '<div class="portfolio-pos">' +
          '<span class="portfolio-pos-name">' + lbEsc(name) + '</span>' +
          '<span class="portfolio-pos-stake">$' + Number(p.staked_usdc || 0).toFixed(2) + '</span>' +
          '<span class="portfolio-pos-reward">+$' + Number(p.rewards_pending_usdc || 0).toFixed(4) + '</span>' +
          '<button type="button" class="portfolio-pos-btn" onclick="focusStakeAgent(\\'' + p.agent_id + '\\')">Yönet</button>' +
          '</div>'
        );
      }}).join('');
      strip.innerHTML =
        '<div class="portfolio-summary">' +
        '<div><span>Toplam stake</span><strong>$' + totalStaked.toFixed(2) + '</strong></div>' +
        '<div><span>Bekleyen ödül</span><strong class="mint">$' + totalPending.toFixed(4) + '</strong></div>' +
        '<div><span>Aktif pozisyon</span><strong>' + positions.length + ' ajan</strong></div>' +
        '</div>' +
        '<div class="portfolio-positions">' + posHtml + '</div>';
    }} catch (_) {{
      strip.innerHTML = '<div class="portfolio-empty">Pozisyonlar yüklenemedi</div>';
    }}
  }}
  window.refreshPortfolio = refreshPortfolio;

  let yieldBalance = 0;
  async function tickYield() {{
    const ticker = $('yieldTicker');
    const valEl = $('yieldValue');
    const w = getWallet();
    if (!w) {{
      ticker?.classList.remove('show');
      return;
    }}
    ticker?.classList.add('show');
    try {{
      const res = await fetch('/hub/positions/' + encodeURIComponent(w) + '?_=' + Date.now());
      if (res.ok) {{
        const positions = await res.json();
        const pending = positions.reduce((s, p) => s + (p.rewards_pending_usdc || 0), 0);
        yieldBalance = Math.max(yieldBalance, pending);
      }}
    }} catch (_) {{}}
    yieldBalance += 0.000002 + Math.random() * 0.000006;
    if (valEl) valEl.textContent = '$' + yieldBalance.toFixed(6);
  }}

  async function triggerLiveRun() {{
    try {{
      const res = await fetch('/hub/trigger-run', {{ method: 'POST' }});
      const data = await res.json();
      if (res.ok) {{ showToast('Görev tamamlandı · ' + data.tasks + ' adım'); refreshLive(); }}
      else showToast(data.detail || 'Hata', true);
    }} catch {{ showToast('Bağlantı hatası', true); }}
  }}

  /* ── Filter ── */
  window.toggleWorkerDetail = function(btn) {{
    const card = btn.closest('.worker-card');
    const detail = card.querySelector('.wc-detail');
    const open = btn.getAttribute('aria-expanded') === 'true';
    btn.setAttribute('aria-expanded', open ? 'false' : 'true');
    detail.hidden = open;
  }};

  /* ── Wallet ── */
  window.openWalletModal = function() {{ $('walletModal').classList.add('open'); }};
  window.closeWalletModal = function() {{ $('walletModal').classList.remove('open'); }};

  async function ensureTargetChain(provider) {{
    if (!ONCHAIN_CONFIG.chain_id) return;
    const network = await provider.getNetwork();
    const target = BigInt(ONCHAIN_CONFIG.chain_id);
    if (network.chainId === target) return;
    const hexId = '0x' + target.toString(16);
    const rpcUrls = ONCHAIN_CONFIG.rpc_urls?.length
      ? ONCHAIN_CONFIG.rpc_urls
      : ['http://127.0.0.1:8545'];
    const chainParams = {{
      chainId: hexId,
      chainName: ONCHAIN_CONFIG.chain_name || 'OAM Chain',
      rpcUrls,
      nativeCurrency: {{ name: 'ETH', symbol: 'ETH', decimals: 18 }},
    }};
    if (ONCHAIN_CONFIG.block_explorer_urls?.length) {{
      chainParams.blockExplorerUrls = ONCHAIN_CONFIG.block_explorer_urls;
    }}
    try {{
      await window.ethereum.request({{ method: 'wallet_switchEthereumChain', params: [{{ chainId: hexId }}] }});
    }} catch (err) {{
      if (err.code === 4902) {{
        await window.ethereum.request({{
          method: 'wallet_addEthereumChain',
          params: [chainParams],
        }});
      }} else throw err;
    }}
  }}

  window.connectMetaMask = async function() {{
    if (!window.ethereum) {{ showToast('MetaMask gerekli', true); return; }}
    try {{
      const provider = new ethers.BrowserProvider(window.ethereum);
      await ensureTargetChain(provider);
      const accounts = await provider.send('eth_requestAccounts', []);
      localStorage.setItem(WALLET_KEY, accounts[0]);
      closeWalletModal();
      sessionStorage.setItem('hub_just_connected', '1');
      updateWalletUI();
      showToast('Bağlandı · ' + shortAddr(accounts[0]));
    }} catch (err) {{ showToast(err.message || 'Hata', true); }}
  }};

  window.connectWallet = function() {{
    const addr = $('walletInput').value.trim();
    if (!addr.startsWith('0x') || addr.length < 10) {{ showToast('Geçerli adres girin', true); return; }}
    localStorage.setItem(WALLET_KEY, addr);
    closeWalletModal();
    sessionStorage.setItem('hub_just_connected', '1');
    updateWalletUI();
    showToast('Bağlandı');
  }};

  window.connectDemoWallet = function() {{
    const demo = '0x' + Array.from({{length:40}}, () => Math.floor(Math.random()*16).toString(16)).join('');
    localStorage.setItem(WALLET_KEY, demo);
    closeWalletModal();
    updateWalletUI();
    showToast('Demo cüzdan hazır');
  }};

  window.disconnectWallet = function() {{
    localStorage.removeItem(WALLET_KEY);
    updateWalletUI();
    showToast('Çıkış yapıldı');
  }};

  function showToast(msg, err) {{
    const t = $('toast');
    t.textContent = msg;
    t.classList.toggle('error', !!err);
    t.classList.add('show');
    setTimeout(() => t.classList.remove('show'), 3800);
  }}
  window.showToast = showToast;

  async function onchainStake(agentId, amount, poolAddress) {{
    const provider = new ethers.BrowserProvider(window.ethereum);
    await ensureTargetChain(provider);
    const signer = await provider.getSigner();
    const wei = ethers.parseUnits(String(amount), ONCHAIN_CONFIG.usdc_decimals || 6);
    const usdc = new ethers.Contract(ONCHAIN_CONFIG.usdc, ERC20_ABI, signer);
    const pool = new ethers.Contract(poolAddress, POOL_ABI, signer);
    await (await usdc.approve(poolAddress, wei)).wait();
    const receipt = await (await pool.stake(wei)).wait();
    return receipt.hash;
  }}

  async function onchainClaim(poolAddress) {{
    const provider = new ethers.BrowserProvider(window.ethereum);
    await ensureTargetChain(provider);
    const signer = await provider.getSigner();
    const pool = new ethers.Contract(poolAddress, POOL_ABI, signer);
    const receipt = await (await pool.claimRewards()).wait();
    return receipt.hash;
  }}

  async function onchainUnstake(poolAddress, shares) {{
    const provider = new ethers.BrowserProvider(window.ethereum);
    await ensureTargetChain(provider);
    const signer = await provider.getSigner();
    const pool = new ethers.Contract(poolAddress, POOL_ABI, signer);
    const wei = ethers.parseUnits(String(shares), ONCHAIN_CONFIG.usdc_decimals || 6);
    const receipt = await (await pool.unstake(wei)).wait();
    return receipt.hash;
  }}

  function resolvePoolAddress(agentId, card) {{
    const fromCard = card?.dataset?.pool;
    if (fromCard && fromCard.startsWith('0x') && fromCard.length > 10) return fromCard;
    return ONCHAIN_CONFIG.pools?.[agentId]?.address || null;
  }}

  window.stake = async function(agentId, btn) {{
    const w = getWallet();
    const card = btn.closest('.worker-card');
    const amount = parseFloat(card?.querySelector('.amount')?.value || '0');
    if (!w) {{ openWalletModal(); return; }}
    if (!amount) {{ showToast('Miktar girin', true); return; }}
    btn.classList.add('loading');
    try {{
      let txHash = null;
      if (ONCHAIN_CONFIG.ready && ONCHAIN_CONFIG.require_tx && window.ethereum) {{
        const pool = resolvePoolAddress(agentId, card);
        if (!pool) throw new Error('Havuz bulunamadı');
        showToast('MetaMask onayı…');
        txHash = await onchainStake(agentId, amount, pool);
      }}
      const res = await fetch('/hub/partnership/stake', {{
        method: 'POST',
        headers: {{'Content-Type':'application/json'}},
        body: JSON.stringify({{ investor_id: w, agent_id: agentId, amount_usdc: amount, tx_hash: txHash, partnership_mode: 'passive' }}),
      }});
      const data = await res.json();
      if (res.ok) {{
        showToast(data.message || 'Ortaklık aktif!');
        setTimeout(() => location.reload(), 1600);
      }} else {{
        showToast(data.detail || 'Hata', true);
        btn.classList.remove('loading');
      }}
    }} catch (err) {{
      showToast(err.message || 'Başarısız', true);
      btn.classList.remove('loading');
    }}
  }};

  window.claim = async function(agentId, btn) {{
    const w = getWallet();
    const card = btn?.closest?.('.worker-card');
    if (!w) {{ openWalletModal(); return; }}
    try {{
      let txHash = null;
      if (ONCHAIN_CONFIG.ready && ONCHAIN_CONFIG.require_tx && window.ethereum) {{
        const pool = resolvePoolAddress(agentId, card);
        if (!pool) throw new Error('Havuz bulunamadı');
        txHash = await onchainClaim(pool);
      }}
      const res = await fetch('/hub/claim', {{
        method: 'POST',
        headers: {{'Content-Type':'application/json'}},
        body: JSON.stringify({{ investor_id: w, agent_id: agentId, tx_hash: txHash }}),
      }});
      const data = await res.json();
      if (res.ok) showToast('Ödül: $' + (data.claimed_usdc?.toFixed(4) || '0'));
      else showToast(data.detail || 'Hata', true);
    }} catch (err) {{ showToast(err.message || 'Hata', true); }}
  }};

  window.unstake = async function(agentId, btn) {{
    const w = getWallet();
    const card = btn.closest('.worker-card');
    const shares = parseFloat(card?.querySelector('.amount')?.value || '0');
    if (!w) {{ openWalletModal(); return; }}
    if (!shares) {{ showToast('Çekilecek miktar girin', true); return; }}
    btn.classList.add('loading');
    try {{
      let txHash = null;
      if (ONCHAIN_CONFIG.ready && ONCHAIN_CONFIG.require_tx && window.ethereum) {{
        const pool = resolvePoolAddress(agentId, card);
        if (!pool) throw new Error('Havuz bulunamadı');
        showToast('MetaMask unstake onayı…');
        txHash = await onchainUnstake(pool, shares);
      }}
      const res = await fetch('/hub/unstake', {{
        method: 'POST',
        headers: {{'Content-Type':'application/json'}},
        body: JSON.stringify({{ investor_id: w, agent_id: agentId, shares, tx_hash: txHash }}),
      }});
      const data = await res.json();
      if (res.ok) {{
        showToast('Çekildi: $' + (data.usdc_returned?.toFixed(2) || '0'));
        setTimeout(() => location.reload(), 1600);
      }} else {{
        showToast(data.detail || 'Hata', true);
        btn.classList.remove('loading');
      }}
    }} catch (err) {{
      showToast(err.message || 'Başarısız', true);
      btn.classList.remove('loading');
    }}
  }};

  window.triggerLiveRun = triggerLiveRun;

  window.runMeshProof = async function(btn) {{
    btn.classList.add('loading');
    const resultEl = $('meshProofResult') || $('meshProofResultTop');
    const mirrorEl = $('meshProofResultTop') !== resultEl ? $('meshProofResultTop') : $('meshProofResult');
    if (resultEl) {{
      resultEl.className = 'mesh-proof-result';
      resultEl.textContent = '4 işçi konuşarak çalışıyor…';
    }}
    if (mirrorEl && mirrorEl !== resultEl) {{
      mirrorEl.className = 'mesh-proof-result revenue-loop-result';
      mirrorEl.textContent = '4 işçi konuşarak çalışıyor…';
    }}
    const proof = JSON.stringify({{
      amount_usdc: {settings.x402_mesh_proof_price_usd},
      payer: getWallet() || '0x' + 'a'.repeat(40),
      payment_id: 'mesh_' + Date.now(),
      network: 'x402-demo',
      asset: 'USDC',
    }});
    try {{
      const res = await fetch('/hub/proof/mesh/run', {{
        method: 'POST',
        headers: {{
          'Content-Type': 'application/json',
          'X-Payment-Proof': proof,
        }},
        body: JSON.stringify({{ symbol: 'bitcoin' }}),
      }});
      const data = await res.json();
      if (res.status === 402) {{
        if (resultEl) resultEl.textContent = 'Ödeme gerekli — tekrar deneyin';
        showToast('x402 ödeme gerekli', true);
        btn.classList.remove('loading');
        return;
      }}
      if (!res.ok) {{
        if (resultEl) resultEl.textContent = data.detail || 'Hata';
        showToast(data.detail || 'Mesh kanıt hatası', true);
        btn.classList.remove('loading');
        return;
      }}
      const verdict = data.proof?.verdict || data.message || 'Kanıt tamamlandı';
      const share = data.share || {{}};
      const successHtml = share.card
        ? '✓ ' + verdict + '<br/><a href="' + share.card + '" target="_blank" rel="noopener" style="color:var(--mint);font-size:0.72rem">Paylaşılabilir kanıt kartı →</a>'
        : '✓ ' + verdict;
      if (resultEl) {{
        resultEl.className = 'mesh-proof-result success';
        resultEl.innerHTML = successHtml;
      }}
      if (mirrorEl && mirrorEl !== resultEl) {{
        mirrorEl.className = 'mesh-proof-result revenue-loop-result success';
        mirrorEl.innerHTML = successHtml;
      }}
      showToast('Mesh kanıtı OK · paylaşım linki hazır');
      if (data.proof?.dialogue_thread) {{
        dialogueThreadId = data.proof.dialogue_thread;
        lastDialogueCount = 0;
        await refreshDialogue(dialogueThreadId);
      }} else {{
        lastDialogueCount = 0;
        await refreshDialogue();
      }}
      refreshLive();
      refreshHeroStats();
      refreshRevenueLoop();
    }} catch (err) {{
      if (resultEl) resultEl.textContent = err.message || 'Bağlantı hatası';
      showToast(err.message || 'Bağlantı hatası', true);
    }}
    btn.classList.remove('loading');
  }};

  window.tryX402MarketPulse = async function(agentId, btn) {{
    return tryX402Service('market-pulse', agentId, btn, {{ symbol: 'bitcoin' }});
  }};

  window.tryX402SentimentRadar = async function(agentId, btn) {{
    return tryX402Service(
      'sentiment-radar',
      agentId,
      btn,
      {{ text: 'Bitcoin ETF inflows rise while macro risk stays elevated' }},
    );
  }};

  async function tryX402Service(serviceId, agentId, btn, body) {{
    const prices = {{
      'market-pulse': {settings.x402_market_pulse_price_usd},
      'sentiment-radar': {settings.x402_sentiment_radar_price_usd},
    }};
    btn.classList.add('loading');
    const proof = JSON.stringify({{
      amount_usdc: prices[serviceId] || 0.05,
      payer: getWallet() || '0x' + 'a'.repeat(40),
      payment_id: 'ui_' + serviceId + '_' + Date.now(),
      network: 'x402-demo',
      asset: 'USDC',
    }});
    try {{
      const res = await fetch('/hub/x402/' + serviceId + '/analyze', {{
        method: 'POST',
        headers: {{
          'Content-Type': 'application/json',
          'X-Payment-Proof': proof,
        }},
        body: JSON.stringify(body),
      }});
      const data = await res.json();
      if (res.status === 402) {{
        showToast('Ödeme gerekli — demo proof ile tekrar deneyin', true);
        btn.classList.remove('loading');
        return;
      }}
      if (!res.ok) {{
        showToast(data.detail || 'x402 hatası', true);
        btn.classList.remove('loading');
        return;
      }}
      const a = data.analysis || {{}};
      showToast('x402 OK · ' + (a.analysis || a.sentiment || a.symbol || 'tamamlandı'));
      const card = btn.closest('.worker-card');
      const taskEl = card?.querySelector('.task-text');
      if (taskEl) taskEl.textContent = 'x402 · ' + (a.analysis || a.sentiment || 'tamamlandı');
      refreshLive();
    }} catch (err) {{
      showToast(err.message || 'Bağlantı hatası', true);
    }}
    btn.classList.remove('loading');
  }};

  async function ensureLatestBuild() {{
    try {{
      const res = await fetch('/hub/version?_=' + Date.now(), {{ cache: 'no-store' }});
      if (!res.ok) return;
      const data = await res.json();
      const serverBuild = data.hub_build;
      const metaBuild = document.querySelector('meta[name="hub-build"]')?.content;
      const hasNewUi = !!document.getElementById('setupAlert');
      const qs = new URLSearchParams(location.search);
      if (serverBuild && metaBuild && serverBuild !== metaBuild) {{
        qs.set('v', serverBuild);
        location.replace(location.pathname + '?' + qs.toString());
        return;
      }}
      if (serverBuild && !hasNewUi && serverBuild.indexOf('hub-pulse-v') !== -1) {{
        qs.set('v', serverBuild);
        location.replace(location.pathname + '?' + qs.toString());
      }}
    }} catch (_) {{}}
  }}

  let workerCatalog = null;
  let selectedWorkerId = null;
  let workerRefreshTimer = null;

  function renderNewsFeed(data) {{
    const items = data.items || [];
    if (!items.length) return '<p class="worker-live-loading">Haber bulunamadı</p>';
    return '<ul class="worker-news-list">' + items.map(it => (
      '<li class="worker-news-item">' +
      '<a href="' + lbEsc(it.link || '#') + '" target="_blank" rel="noopener">' + lbEsc(it.title) + '</a>' +
      (it.snippet ? '<p>' + lbEsc(it.snippet) + '</p>' : '') +
      '</li>'
    )).join('') + '</ul>';
  }}

  function renderKvGrid(pairs) {{
    return '<div class="worker-kv-grid">' + pairs.map(([k, v]) => (
      '<div class="worker-kv"><span>' + lbEsc(k) + '</span><strong>' + lbEsc(String(v)) + '</strong></div>'
    )).join('') + '</div>';
  }}

  function renderThreatList(data) {{
    const items = data.items || [];
    if (!items.length) return '<p class="worker-live-loading">Zafiyet bulunamadı</p>';
    return '<ul class="worker-threat-list">' + items.map(it => (
      '<li class="worker-threat-item">' +
      '<strong>' + lbEsc(it.cve || '—') + '</strong>' +
      '<span>' + lbEsc(it.vendor || '') + ' · ' + lbEsc(it.product || '') + '</span>' +
      '<span class="worker-threat-meta">Eklendi: ' + lbEsc(it.date_added || '—') +
      (it.ransomware === 'Known' ? ' · <em>ransomware</em>' : '') + '</span>' +
      '</li>'
    )).join('') + '</ul>' +
    '<p style="margin-top:0.75rem;font-size:0.78rem;color:var(--muted)">' + lbEsc(data.analysis || '') + '</p>';
  }}

  function renderYieldPools(data) {{
    const items = data.items || [];
    if (!items.length) return '<p class="worker-live-loading">Yield havuzu bulunamadı</p>';
    return '<ul class="worker-yield-list">' + items.map(it => (
      '<li class="worker-yield-item">' +
      '<strong>' + lbEsc(it.project || '—') + '</strong> · ' + lbEsc(it.symbol || '') +
      '<span>' + lbEsc(it.chain || '') + ' · %' + Number(it.apy_pct || 0).toFixed(2) + ' APY · TVL $' + Number(it.tvl_usd || 0).toLocaleString() + '</span>' +
      '</li>'
    )).join('') + '</ul>' +
    '<p style="margin-top:0.75rem;font-size:0.78rem;color:var(--muted)">' + lbEsc(data.analysis || '') + '</p>';
  }}

  function renderWorkerOutput(data, outputType) {{
    if (outputType === 'regulatory' || outputType === 'news_feed') {{
      if (data.items) return renderNewsFeed(data);
    }}
    if (outputType === 'threat') return renderThreatList(data);
    if (outputType === 'yield') return renderYieldPools(data);
    if (outputType === 'macro' || data.btc_dominance_pct != null) {{
      const fx = data.fx_basket || {{}};
      const fxPairs = Object.keys(fx).slice(0, 4).map(k => ['USD/' + k, fx[k]]);
      return renderKvGrid([
        ['Piyasa cap', '$' + Number(data.total_market_cap_usd || 0).toLocaleString()],
        ['24s değişim', (data.market_change_24h_pct != null ? data.market_change_24h_pct + '%' : '—')],
        ['BTC dom', (data.btc_dominance_pct != null ? data.btc_dominance_pct + '%' : '—')],
        ['Risk tonu', data.risk_tone || '—'],
      ]) + (fxPairs.length ? '<div style="margin-top:0.65rem">' + renderKvGrid(fxPairs) + '</div>' : '') +
      '<p style="margin-top:0.75rem;font-size:0.78rem;color:var(--muted)">' + lbEsc(data.analysis || '') + '</p>';
    }}
    if (outputType === 'market' || data.price_usd != null) {{
      return renderKvGrid([
        ['Fiyat USD', '$' + Number(data.price_usd || 0).toLocaleString()],
        ['24s', (data.change_24h_pct != null ? data.change_24h_pct + '%' : '—')],
        ['Hacim 24s', data.volume_24h_usd ? '$' + Number(data.volume_24h_usd).toLocaleString() : '—'],
        ['Kaynak', data.source || 'CoinGecko'],
      ]) + '<p style="margin-top:0.75rem;font-size:0.78rem;color:var(--muted)">' + lbEsc(data.analysis || '') + '</p>';
    }}
    if (outputType === 'sentiment' || data.fear_greed_index != null) {{
      return renderKvGrid([
        ['Fear & Greed', data.fear_greed_index + ' · ' + (data.fear_greed_class || '')],
        ['Metin', data.text_sentiment || data.sentiment || '—'],
        ['Skor', data.text_score != null ? data.text_score : (data.score != null ? data.score : '—')],
      ]) + '<p style="margin-top:0.75rem;font-size:0.78rem;color:var(--muted)">' + lbEsc(data.analysis || '') + '</p>';
    }}
    if (outputType === 'fx' || data.usd_try != null) {{
      const rates = data.rates || {{}};
      const pairs = Object.keys(rates).slice(0, 6).map(k => [k, rates[k]]);
      if (data.usd_try) pairs.unshift(['USD/TRY', data.usd_try]);
      return renderKvGrid(pairs) + '<p style="margin-top:0.75rem;font-size:0.78rem;color:var(--muted)">' + lbEsc(data.analysis || '') + '</p>';
    }}
    if (outputType === 'defi' || data.leader_chain) {{
      const chains = (data.top_chains || []).slice(0, 5).map(c => [c.name || c.chain, '$' + Number(c.tvl_usd || c.tvl || 0).toLocaleString()]);
      return renderKvGrid([
        ['Lider', data.leader_chain],
        ['TVL', '$' + Number(data.leader_tvl_usd || 0).toLocaleString()],
      ]) + (chains.length ? '<div style="margin-top:0.65rem">' + renderKvGrid(chains) + '</div>' : '');
    }}
    if (outputType === 'btc_network' || data.btc_usd != null) {{
      const fees = data.fees_sat_vb || {{}};
      return renderKvGrid([
        ['BTC USD', '$' + Number(data.btc_usd || 0).toLocaleString()],
        ['Blok', data.block_height || '—'],
        ['Mempool', data.mempool_congestion || '—'],
        ['Ücret hızlı', fees.fastestFee || fees.halfHourFee || '—'],
      ]);
    }}
    if (outputType === 'chain' || data.block_number != null) {{
      return renderKvGrid([
        ['Ağ', data.network || '—'],
        ['Chain ID', data.chain_id || '—'],
        ['Blok', data.block_number || '—'],
        ['x402', data.x402_enabled ? 'açık' : 'kapalı'],
      ]) + '<p style="margin-top:0.75rem;font-size:0.78rem;color:var(--muted)">' + lbEsc(data.analysis || '') + '</p>';
    }}
    return '<pre style="font-size:0.72rem;color:var(--muted);white-space:pre-wrap">' + lbEsc(JSON.stringify(data, null, 2)) + '</pre>';
  }}

  async function loadWorkerCatalog() {{
    const res = await fetch('/hub/workers?_=' + Date.now(), {{ cache: 'no-store' }});
    if (!res.ok) throw new Error('İşçi kataloğu yüklenemedi');
    workerCatalog = await res.json();
    return workerCatalog;
  }}

  async function refreshWorkerLive() {{
    const out = $('workerLiveOutput');
    if (!out || !selectedWorkerId) return;
    const worker = (workerCatalog?.workers || []).find(w => w.agent_id === selectedWorkerId);
    if (!worker) return;
    out.innerHTML = '<div class="worker-live-loading">Yükleniyor…</div>';
    try {{
      const res = await fetch(worker.live_route + '?_=' + Date.now(), {{ cache: 'no-store' }});
      if (!res.ok) throw new Error('Veri alınamadı');
      const data = await res.json();
      out.innerHTML = renderWorkerOutput(data, worker.output_type);
      const proof = $('workerLiveProof');
      if (proof) proof.textContent = (data.real_data ? '● Gerçek veri' : '—') + ' · ' + worker.api_tag;
    }} catch (err) {{
      out.innerHTML = '<p class="worker-live-loading">' + lbEsc(err.message || 'Hata') + '</p>';
    }}
  }}

  window.selectWorker = function(agentId, btn) {{
    selectedWorkerId = agentId;
    document.querySelectorAll('.worker-pick-item').forEach(el => el.classList.remove('active'));
    if (btn) btn.classList.add('active');
    const worker = (workerCatalog?.workers || []).find(w => w.agent_id === agentId);
    const title = $('workerLiveTitle');
    const meta = $('workerLiveMeta');
    if (worker && title) title.textContent = worker.display_name;
    if (worker && meta) {{
      meta.textContent = worker.api_tag + ' · ' + worker.token_symbol + ' · sabit arz ' + Number(worker.fixed_supply).toLocaleString();
    }}
    refreshWorkerLive();
    if (workerRefreshTimer) clearInterval(workerRefreshTimer);
    workerRefreshTimer = setInterval(refreshWorkerLive, 45000);
  }};
  window.refreshWorkerLive = refreshWorkerLive;

  window.focusWorkerStake = function() {{
    const w = getWallet();
    if (!w) {{ openWalletModal(); return; }}
    if (selectedWorkerId) focusStakeAgent(selectedWorkerId);
    else {{
      document.getElementById('dashboard')?.scrollIntoView({{ behavior: 'smooth' }});
      switchHubTab('invest', document.querySelector('.terminal-tab[data-tab="invest"]'));
    }}
  }};

  async function initWorkerConsole() {{
    if (!$('workerConsole')) return;
    try {{
      const cat = await loadWorkerCatalog();
      const first = cat.default_agent_id || (cat.workers && cat.workers[0]?.agent_id);
      const btn = document.querySelector('.worker-pick-item[data-agent="' + first + '"]');
      if (first) selectWorker(first, btn);
    }} catch (_) {{
      const out = $('workerLiveOutput');
      if (out) out.innerHTML = '<p class="worker-live-loading">İşçiler yüklenemedi</p>';
    }}
  }}

  async function refreshHeroStats() {{
    try {{
      const res = await fetch('/hub/stats?_=' + Date.now(), {{ cache: 'no-store' }});
      if (!res.ok) return;
      const s = await res.json();
      const badge = $('heroLiveBadge');
      if (badge) badge.textContent = (s.live_workers || 7) + ' gerçek işçi · canlı API';
    }} catch (_) {{}}
  }}

  initMeshCanvas();
  ensureLatestBuild();
  initWorkerConsole();
  refreshRevenueLoop();
  refreshLeaderboard();
  refreshPortfolio();
  updateWalletUI();
  setInterval(tickYield, 900);
  const promptInput = $('userPrompt');
  if (promptInput) {{
    promptInput.addEventListener('keydown', (e) => {{
      if (e.key === 'Enter') {{ e.preventDefault(); submitUserPrompt(); }}
    }});
  }}
  if (EMBED_MODE && !getWallet()) {{ /* işçi konsolu önce — otomatik cüzdan açma */ }}
  console.info('[Hub] build:', '{build}');
}})();
</script>
"""
