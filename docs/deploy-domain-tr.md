# .tr domain ile Hub kurulumu — axium.com.tr

`.tr` domain Let's Encrypt ve MetaMask ile uyumludur.

**Axium Hub, Zinesh’ten bağımsızdır.** Ayrı domain, ayrı marka, ayrı sunucu önerilir.

## Yeni sunucuya geçiş (önerilen)

Eski VPS RAM doluysa (OOM) **8GB RAM** li temiz Ubuntu VPS alın. **aaPanel kurmayın** — sadece Axium için nginx yeterli.

### 1. Yeni VPS — tek komut (root)

```bash
curl -fsSL https://raw.githubusercontent.com/cromles/fizobia/main/scripts/bootstrap_new_server.sh | bash
```

Gemini ile:

```bash
AXIUM_GEMINI_KEY="AIza..." CERTBOT_EMAIL="sen@email.com" \
  bash -c 'curl -fsSL https://raw.githubusercontent.com/cromles/fizobia/main/scripts/bootstrap_new_server.sh | bash'
```

### 2. DNS (Turhost)

| Kayıt | Tip | Değer |
|-------|-----|-------|
| `@` | A | **yeni sunucu IP** |
| `www` | CNAME | `axium.com.tr` |

Eski IP (`89.47.113.150`) kaydını silin veya güncelleyin.

### 3. Doğrulama

```bash
curl -s https://axium.com.tr/hub/version
curl -s https://axium.com.tr/hub/apis
```

Build `free-apis-v20` veya üzeri olmalı.

### 4. Eski sunucu — Axium'u kaldır

DNS yeni IP'ye geçtikten sonra eski VPS'ten Axium'u tamamen çıkarın (RAM boşalır, Zinesh/aaPanel kalır):

```bash
curl -fsSL https://raw.githubusercontent.com/cromles/fizobia/main/scripts/uninstall_axium.sh | bash
```

Kod klasörünü de silmek için:

```bash
REMOVE_DATA=1 bash -c 'curl -fsSL https://raw.githubusercontent.com/cromles/fizobia/main/scripts/uninstall_axium.sh | bash'
```

Eski VPS'i tamamen kapatabilir veya sadece durdurun.

---

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
