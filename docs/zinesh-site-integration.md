# Zinesh.com × OAM Hub — Site Haritası ve Entegrasyon

Zinesh protokol sitesi **felsefe + güven** katmanını taşır; **dijital işçi yatırım deneyimi** OAM Hub API üzerinden bağlanır.

## Mimari

```
┌─────────────────────────────────────────────────────────────┐
│  zinesh.com (sizin site — Next.js / statik / WordPress)     │
│  ├── Ana sayfa (protokol vizyonu)                           │
│  ├── /protokol (güven, itibar, koordinasyon)                │
│  ├── /isciler (işçi ekonomisi — özet + CTA)                 │
│  └── /hub veya /isciler/pazar (embed veya headless UI)      │
└───────────────────────────┬─────────────────────────────────┘
                            │ HTTPS / WSS
                            ▼
┌─────────────────────────────────────────────────────────────┐
│  hub-api.zinesh.com (OAM Gateway — fizobia)                 │
│  GET  /hub/sdk/config    → entegrasyon haritası             │
│  GET  /hub/embed         → iframe panel (Zinesh markalı)    │
│  GET  /hub/agents        → işçi kartları JSON               │
│  GET  /hub/live          → canlı faaliyet                    │
│  WS   /hub/ws/live       → gerçek zamanlı akış              │
│  POST /hub/stake|claim   → yatırım işlemleri                │
└─────────────────────────────────────────────────────────────┘
```

---

## Sayfa haritası (zinesh.com)

### 1. `/` — Ana sayfa
**Amaç:** Zinesh protokolünü anlat; yatırım değil **güven ekonomisi**.

| Blok | İçerik |
|------|--------|
| Hero | «Güvenin protokolü» — Bitcoin para, blockchain kayıt, Zinesh güven |
| Problem | AI çağında güven krizi, ölçülebilir katkı ihtiyacı |
| CTA | «Dijital işçileri keşfet» → `/isciler` |

### 2. `/protokol` — Nasıl çalışır?
**Amaç:** Teknik olmayan kullanıcıya protokol mantığı.

- Güven = şeffaf kurallar + doğrulanabilir katkı
- İtibar = gerçek faaliyet kaydı (simülasyon değil)
- Ekonomik koordinasyon = bireysel çıkar ↔ toplumsal fayda
- FAQ: «Yatırım aracı değiliz» → **katkıya ortaklık** dili

### 3. `/isciler` — Dijital işçiler
**Amaç:** Hub’a köprü; felsefeyi somutlaştır.

- 3–6 öne çıkan ajan özeti (API’den çekilebilir)
- Canlı istatistik widget: `GET /hub/live` → `network.total_calls`, `real_event_count`
- CTA: «İşçilerime ortak ol» → `/hub`

### 4. `/hub` — Yatırım paneli (2 seçenek)

#### Seçenek A — Hızlı (iframe, önerilen MVP)
```html
<iframe
  src="https://hub-api.zinesh.com/hub/embed"
  title="Zinesh Dijital İşçiler"
  style="width:100%;min-height:90vh;border:0;border-radius:12px"
  allow="clipboard-write"
></iframe>
```

#### Seçenek B — Headless (kendi UI’nız)
`GET /hub/sdk/config` ile endpoint’leri alın, kendi tasarımınızda kart + stake.

### 5. `/cuzdan` (opsiyonel)
MetaMask bağlantı rehberi, Hardhat/Sepolia ağ ekleme — embed içinde de var.

### 6. `/gelistirici` (ileride)
OAM mesh API, ajan kaydı, operatör dokümantasyonu.

---

## API entegrasyonu

### Başlangıç — SDK config
```bash
curl https://hub-api.zinesh.com/hub/sdk/config
```

Örnek yanıt alanları:
- `api_base` — tüm isteklerin kökü
- `embed_url` — iframe src
- `endpoints.agents`, `live`, `stake`, `claim`
- `onchain` — MetaMask / chain ayarları

### İşçi listesi
```javascript
const cfg = await fetch('https://hub-api.zinesh.com/hub/sdk/config').then(r => r.json());
const agents = await fetch(cfg.endpoints.agents).then(r => r.json());
```

### Canlı aktivite
```javascript
const live = await fetch(cfg.endpoints.live).then(r => r.json());
// live.activity_feed — gerçek görev kayıtları
// live.network.real_event_count
```

### WebSocket
```javascript
const ws = new WebSocket(cfg.endpoints.live_ws);
ws.onmessage = (ev) => applySnapshot(JSON.parse(ev.data));
```

### Stake (headless + MetaMask)
1. `ethers` ile `onchain.usdc` → `approve` + `pool.stake`
2. `POST /hub/stake` body: `{ investor_id, agent_id, amount_usdc, tx_hash }`

---

## Ortam değişkenleri (gateway)

| Değişken | Açıklama |
|----------|----------|
| `OAM_PUBLIC_BASE_URL` | `https://hub-api.zinesh.com` |
| `OAM_CORS_ORIGINS` | `https://zinesh.com,https://www.zinesh.com` |
| `OAM_EMBED_FRAME_ORIGINS` | iframe izin verilen origin’ler |
| `OAM_HUB_DEMO` | `false` (canlı mod) |
| `OAM_ONCHAIN_ENABLED` | `true` (MetaMask stake) |

---

## Dağıtım önerisi

| Bileşen | Domain |
|---------|--------|
| Zinesh marketing | `zinesh.com` |
| Hub API + embed | `hub-api.zinesh.com` |
| veya tek domain | `zinesh.com/hub` → reverse proxy → gateway |

Nginx örneği:
```nginx
location /hub/ {
    proxy_pass http://127.0.0.1:8787/hub/;
    proxy_set_header Host $host;
}
```

---

## Mesaj tutarlılığı (önemli)

| zinesh.com | Hub paneli |
|------------|------------|
| Güven protokolü | Gerçek işçi faaliyeti |
| Ölçülebilir katkı | Canlı aktivite akışı |
| Ortaklık / stake | MetaMask on-chain |
| «Spekülasyon değil» | DEMO banner yok (prod) |

---

## Uygulama fazları

1. **Faz 1 (şimdi):** iframe `/hub/embed` + `/isciler` sayfası
2. **Faz 2:** Headless widget — sadece kartlar + live feed Zinesh temasında
3. **Faz 3:** Zinesh itibar skoru → OAM `reliability_score` ile birleşim
4. **Faz 4:** Sepolia/mainnet, gerçek USDC

---

## Yerel test

```bash
# Gateway
OAM_PUBLIC_BASE_URL=http://127.0.0.1:8787 python -m app.run_stack

# Zinesh sitesi (ör. localhost:3000)
# iframe src="http://127.0.0.1:8787/hub/embed"
```

SDK: http://127.0.0.1:8787/hub/sdk/config
