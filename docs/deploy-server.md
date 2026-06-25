# Sunucuya kurulum (domain olmadan)

Domain **zorunlu değil**. Sunucu IP adresi ile Hub çalışır.

## Ne çalışır (sadece IP)

| Özellik | IP ile |
|---------|--------|
| Hub arayüzü (`/hub`) | Evet |
| Canlı API / WebSocket | Evet |
| Market-Pulse + x402 demo | Evet |
| Pasif ortaklık API | Evet |
| Tam mesh (10 işçi) | Evet (8101–8110 portları açık olmalı) |

## Sınırlamalar (domain/HTTPS yokken)

| Özellik | Durum |
|---------|--------|
| MetaMask stake (gerçek TX) | HTTP + IP'de tarayıcı uyarı verebilir; demo cüzdan veya localhost daha sorunsuz |
| Zinesh.com iframe embed | `OAM_EMBED_FRAME_ORIGINS` içine site adresi gerekir |
| Agentic.Market keşif | HTTPS domain tercih edilir |
| Üretim x402 (gerçek USDC) | HTTPS + domain önerilir |

**Özet:** Demo, vitrin ve ilk yatırımcı testi için **IP yeterli**. Ciddi on-chain ve dış entegrasyon için sonra domain + HTTPS eklenir.

## Hızlı kurulum

```bash
# Sunucuda
git clone https://github.com/cromles/fizobia.git
cd fizobia
git checkout main

bash scripts/deploy_server.sh
nano .env.server   # OAM_PUBLIC_BASE_URL=http://SUNUCU_IP:8787

# Firewall
sudo ufw allow 8787/tcp
sudo ufw allow 8101:8110/tcp   # tam mesh

# Sadece gateway
bash scripts/start_production.sh

# veya tam stack (arka planda)
nohup env OAM_ENV_FILE=.env.server bash scripts/start_full_stack.sh > hub.log 2>&1 &
```

Tarayıcı: `http://SUNUCU_IP:8787/hub`

## systemd (kalıcı)

```bash
sudo cp -r . /opt/fizobia
sudo cp deploy/oam-hub.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now oam-hub
```

## Ortam değişkenleri

| Değişken | Örnek (IP) |
|----------|------------|
| `OAM_PUBLIC_BASE_URL` | `http://185.12.34.56:8787` |
| `OAM_GATEWAY_HOST` | `0.0.0.0` |
| `OAM_CORS_ORIGINS` | `http://185.12.34.56:8787` |

Şablon: `.env.server.example`
