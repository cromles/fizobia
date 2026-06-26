# Ajan Ekosistemi — Büyüme Protokolü

Sistem **donuk kod değil** — ajanlar üzerine inşa edilir.

## Kurucu dörtlü (bootstrap)

| Sıra | Ajan | Rol | Görev |
|------|------|-----|-------|
| 1 | Web-Crawler | Keşifçi | Dış veri girişi |
| 2 | Sentiment-Radar | Analist | Sinyal üretimi |
| 3 | Market-Pulse | Analist | Piyasa yorumu |
| 4 | Pipeline Orchestrator | Koordinatör | İşe alma, görev dağıtımı |

## Büyüme döngüsü

```
Kurucu 3 işçi sistemi kurar
    → Koordinatör mesh proof ile işe alır
    → Yeni operatör POST /hub/ecosystem/join ile katılır
    → Koordinatör goal pipeline ile dinamik işe alır
    → Gelir %65 staking havuzuna akar
```

## API

| Endpoint | Açıklama |
|----------|----------|
| `GET /hub/ecosystem` | Kurucular + büyüme ajanları + olaylar |
| `GET /hub/ecosystem/events` | Büyüme olay akışı |
| `POST /hub/ecosystem/join` | Yeni ajan kaydı |
| `POST /hub/ecosystem/hire` | Koordinatör işe alma (`mesh_proof` \| `goal`) |

## Çalıştır

```bash
bash scripts/start_founder_stack.sh
python3 scripts/demo_ecosystem_growth.py
```

Tam yığın (legacy mock + tüm ajanlar):

```bash
bash scripts/start_full_stack.sh
```

## Ortam

```bash
OAM_STACK_MODE=founder   # sadece kurucu dörtlü + gateway
OAM_STACK_MODE=full      # varsayılan — 10 ajan
```

## Yeni ajan katılımı (örnek)

```bash
curl -X POST http://127.0.0.1:8787/hub/ecosystem/join \
  -H 'Content-Type: application/json' \
  -d '{"manifest": {"agent_id": "operator.alerts.local", "endpoint": "http://127.0.0.1:8120", "capabilities": [...]}}'
```

Katılan ajan `growth` tier'ında listelenir; kurucular `founder` / `coordinator` olarak kalır.
