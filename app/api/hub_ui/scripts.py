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
    'function claimRewards()',
    'function pendingReward(address user) view returns (uint256)',
  ];

  let liveTimer = null, processTimer = null, liveSocket = null, lastEventCount = 0;
  const agentNameMap = {{}};

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
    const landing = $('landing');
    const dash = $('dashboard');
    if (w) {{
      pill.classList.add('show');
      $('walletShort').textContent = shortAddr(w);
      btn.style.display = 'none';
      landing.classList.add('hidden');
      dash.classList.add('visible');
      $('dashWelcome').textContent = shortAddr(w) + ' · işçileriniz çalışıyor';
      if (sessionStorage.getItem('hub_just_connected')) {{
        sessionStorage.removeItem('hub_just_connected');
        showSplash();
      }} else {{
        startLiveFeed();
        if (DEMO_MODE) startProcessAnimation();
      }}
      window.scrollTo({{ top: 0, behavior: 'smooth' }});
    }} else {{
      pill.classList.remove('show');
      btn.style.display = 'block';
      landing.classList.remove('hidden');
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
      if (DEMO_MODE) startProcessAnimation();
    }}, 1400);
  }}

  function stopLiveFeed() {{
    if (liveTimer) clearInterval(liveTimer);
    if (processTimer) clearInterval(processTimer);
    if (liveSocket) {{ liveSocket.close(); liveSocket = null; }}
    liveTimer = processTimer = null;
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
    liveTimer = setInterval(refreshLive, 4000);
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
        <div class="feed-meta">Gateway çalışıyor ama 10 ajan başlamadı. <code>${{net.setup_command || 'python3 -m app.run_stack'}}</code> ile tam mesh'i açın. x402 ödemesi gateway üzerinden çalışmaya devam eder.</div>
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
    try {{
      await window.ethereum.request({{ method: 'wallet_switchEthereumChain', params: [{{ chainId: hexId }}] }});
    }} catch (err) {{
      if (err.code === 4902) {{
        await window.ethereum.request({{
          method: 'wallet_addEthereumChain',
          params: [{{ chainId: hexId, chainName: 'OAM Local', rpcUrls: ['http://127.0.0.1:8545'],
            nativeCurrency: {{ name: 'ETH', symbol: 'ETH', decimals: 18 }} }}],
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

  function resolvePoolAddress(agentId, card) {{
    const fromCard = card?.dataset?.pool;
    if (fromCard && fromCard.startsWith('0x') && fromCard.length > 10) return fromCard;
    return ONCHAIN_CONFIG.pools?.[agentId]?.address || null;
  }}

  window.stake = async function(agentId, btn) {{
    const w = getWallet();
    const card = btn.closest('.worker-card');
    const amount = parseFloat(card.querySelector('.amount').value);
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

  window.triggerLiveRun = triggerLiveRun;

  window.runMeshProof = async function(btn) {{
    btn.classList.add('loading');
    const resultEl = $('meshProofResult');
    if (resultEl) {{
      resultEl.className = 'mesh-proof-result';
      resultEl.textContent = '3 işçi çalışıyor…';
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
      if (resultEl) {{
        resultEl.className = 'mesh-proof-result success';
        resultEl.textContent = '✓ ' + verdict;
      }}
      showToast('Mesh kanıtı OK · 3 gerçek işçi');
      refreshLive();
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
      const card = btn.closest('.featured-worker') || btn.closest('.worker-card');
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

  initMeshCanvas();
  ensureLatestBuild();
  updateWalletUI();
  if (EMBED_MODE && !getWallet()) setTimeout(openWalletModal, 500);
  console.info('[Hub] build:', '{build}');
}})();
</script>
"""
