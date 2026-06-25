# .tr domain ile Hub kurulumu (axium.com.tr)

`.tr` domain **sorun değil** — Let's Encrypt ve MetaMask ile uyumludur.

## Zinesh vs Hub — karışmaz

| Bileşen | Domain | Sunucu |
|---------|--------|--------|
| **Zinesh** (vitrin, protokol) | `zinesh.com` | Zinesh’in kendi sunucusu |
| **OAM Hub** (fizobia) | `axium.com.tr` | **Hub için ayrı sunucu / VPS** |

Zinesh sunucusuna Hub kurmayın. `axium.com.tr` DNS A kaydı **Hub sunucusunun IP’sine** gider. Zinesh sitesi Hub’ı iframe/API ile çağırır (`OAM_EMBED_FRAME_ORIGINS` içinde `zinesh.com`).

## 1. DNS (Turhost — axium.com.tr)

| Kayıt | Tip | Değer |
|-------|-----|-------|
| `@` | **A** | `HUB_SUNUCU_IP` (Hub VPS — Zinesh IP’si değil) |
| `www` | CNAME | `axium.com.tr` (zaten varsa dokunma) |

Doğrula:
```bash
dig +short axium.com.tr
```

## 2. Hub sunucusunda kurulum

```bash
git clone https://github.com/cromles/fizobia.git
cd fizobia
git checkout main
bash scripts/deploy_server.sh

cp .env.domain.example .env.server
nano .env.server
bash scripts/start_production.sh
```

Tek komut (systemd):
```bash
HUB_IP=HUB_SUNUCU_IP bash scripts/install_hub_server.sh
```

## 3. HTTPS (Caddy)

```bash
sudo apt install -y caddy
sudo tee /etc/caddy/Caddyfile <<'EOF'
axium.com.tr, www.axium.com.tr {
    reverse_proxy 127.0.0.1:8787
}
EOF
sudo systemctl enable --now caddy
```

`.env.server`:
```
OAM_PUBLIC_BASE_URL=https://axium.com.tr
```

Hub: **https://axium.com.tr/hub**

## 4. Zinesh embed

`zinesh.com` sitesinde:
```html
<iframe src="https://axium.com.tr/hub/embed" ...></iframe>
```

## Firewall

```bash
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
```

## Hub sunucusu yoksa

- Turhost / başka sağlayıcıdan **küçük bir VPS** al (1 GB RAM yeterli başlangıç için)
- `axium.com.tr` A kaydını o VPS IP’sine yönlendir
- Zinesh sunucusuna dokunma
