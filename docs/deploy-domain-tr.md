# .tr domain ile Hub kurulumu — axium.com.tr

`.tr` domain Let's Encrypt ve MetaMask ile uyumludur.

**Axium Hub, Zinesh’ten bağımsızdır.** Ayrı domain, ayrı marka, ayrı sunucu önerilir.

## 1. DNS (Turhost — axium.com.tr)

| Kayıt | Tip | Değer |
|-------|-----|-------|
| `@` | **A** | Hub sunucu IP (Zinesh sunucusu değil) |
| `www` | CNAME | `axium.com.tr` |

```bash
dig +short axium.com.tr
```

## 2. Hub sunucusunda kurulum

```bash
git clone https://github.com/cromles/fizobia.git /opt/fizobia
cd fizobia
git checkout main
bash scripts/deploy_server.sh

cp .env.domain.example .env.server
bash scripts/start_production.sh
```

Tek komut (systemd):
```bash
HUB_IP=HUB_SUNUCU_IP bash scripts/install_hub_server.sh
```

## 3. HTTPS

### aaPanel (sunucuda bu panel varsa — önerilen)

1. **Site** → **Add site** → `axium.com.tr` + `www.axium.com.tr`
2. **SSL** → Let's Encrypt (ücretsiz)
3. **Reverse proxy** → hedef: `http://127.0.0.1:8787`
4. Kaydet

Tek komut Hub kurulumu:
```bash
curl -fsSL https://raw.githubusercontent.com/cromles/fizobia/main/scripts/deploy_axium_production.sh | bash
```

### Caddy (alternatif)

```bash
sudo apt install -y caddy
sudo tee /etc/caddy/Caddyfile <<'EOF'
axium.com.tr, www.axium.com.tr {
    reverse_proxy 127.0.0.1:8787
}
EOF
sudo systemctl enable --now caddy
```

Hub: **https://axium.com.tr/hub**

## 4. Firewall

```bash
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
```

## Önemli

- `axium.com.tr` → **sadece Axium Hub**
- Zinesh domain’i, CORS’u veya embed’i **eklemeyin**
- Mümkünse Hub için **ayrı VPS** kullanın (Zinesh IP’sine DNS bağlamayın)
