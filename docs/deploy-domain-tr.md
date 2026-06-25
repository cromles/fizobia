# .tr domain ile Hub kurulumu

`.tr` domain **sorun değil** — Let's Encrypt ve MetaMask ile uyumludur.

## 1. DNS (domain panelinde)

| Kayıt | Tip | Değer |
|-------|-----|-------|
| `hub` (veya `@`) | **A** | `89.47.113.150` |

Örnek: `hub.sizindomain.tr` → sunucu IP

Doğrula:
```bash
dig +short hub.sizindomain.tr
```

## 2. Sunucuda Hub

```bash
git clone https://github.com/cromles/fizobia.git
cd fizobia
git checkout main
bash scripts/deploy_server.sh

cp .env.domain.example .env.server
nano .env.server   # hub.sizindomain.tr yazın
bash scripts/start_production.sh
```

## 3. HTTPS (önerilen — Caddy en kolay)

```bash
sudo apt install -y caddy
sudo cp deploy/Caddyfile.example /etc/caddy/Caddyfile
sudo nano /etc/caddy/Caddyfile   # domain düzenle
sudo systemctl reload caddy
```

Artık: **https://hub.sizindomain.tr/hub**

`.env.server` içinde:
```
OAM_PUBLIC_BASE_URL=https://hub.sizindomain.tr
```

## 4. Firewall

```bash
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw allow 8787/tcp   # sadece localhost'tan erişim için kapalı da tutulabilir
```

## IP vs .tr domain

| | Sadece IP | .tr + HTTPS |
|--|-----------|-------------|
| Hub UI | ✅ | ✅ |
| Paylaşılabilir kanıt linki | ✅ | ✅ daha profesyonel |
| MetaMask | ⚠️ uyarı | ✅ |
| x402 gerçek USDC | ⚠️ | ✅ |
| Zinesh embed | ❌ | ✅ |

## Zinesh ayrı domain ise

`OAM_EMBED_FRAME_ORIGINS` içine `https://zinesh.com` ekleyin.
