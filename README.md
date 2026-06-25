# fizobia — Open Agent Mesh (OAM)

## The Hub'u 30 saniyede aç (Windows)

### Yöntem 1 — Çift tık (en kolay)

1. `git pull` ve branch: `cursor/investment-hub-0b7c`
2. Dosya gezgininde **`scripts/start_hub.bat`** dosyasına çift tıkla
3. Siyah terminal penceresi açık kalsın
4. Tarayıcıda: **http://127.0.0.1:8787/hub**

### Yöntem 2 — Cursor terminali

```powershell
cd fizobia
git checkout cursor/investment-hub-0b7c
git pull
pip install -r requirements.txt
python -m app.main
```

Terminalde şunu görmelisin:

```
Uvicorn running on http://0.0.0.0:8787
```

Sonra Cursor sağ önizlemede veya Chrome'da `/hub` aç.

### "Connection refused" hatası

Sunucu **çalışmıyor** demektir. `python -m app.main` komutunu çalıştır ve terminali kapatma.

| Kontrol | Beklenen |
|---------|----------|
| http://127.0.0.1:8787/health | `{"protocol":"OAM",...}` |
| http://127.0.0.1:8000/health | Başka servis — OAM değil |

### Tam stack (3 mock ajan + gateway)

```bash
python -m app.run_stack
```

Sadece Hub için `python -m app.main` yeterli.
