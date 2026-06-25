# Cursor'da Zinesh bağlantısı

## 1. Workspace aç

Cursor'da **File → Open Workspace from File** → `fizobia-zinesh.code-workspace`

İki klasör görünür:
- **OAM Gateway** — Python backend
- **Zinesh Web Site** — statik site

## 2. İki servisi başlat

**Windows:**
```bat
scripts\dev_zinesh_cursor.bat
```

**Linux/Mac:**
```bash
chmod +x scripts/dev_zinesh_cursor.sh
./scripts/dev_zinesh_cursor.sh
```

## 3. Tarayıcıda test

| URL | Ne |
|-----|-----|
| http://127.0.0.1:3000 | Zinesh ana sayfa |
| http://127.0.0.1:3000/isciler.html | API'den canlı işçiler |
| http://127.0.0.1:3000/hub.html | Hub iframe embed |
| http://127.0.0.1:8787/hub/sdk/config | Bağlantı haritası |

Ana sayfada yeşil **「Hub bağlı」** görürsen bağlantı tamam.

## 4. Cursor AI bağlamı

`.cursor/rules/zinesh-oam.mdc` — Agent otomatik olarak Zinesh + Hub ilişkisini bilir.

## 5. Hub API adresini değiştirme

Tarayıcı konsolunda:
```javascript
localStorage.setItem('zinesh_hub_api', 'https://hub-api.zinesh.com');
location.reload();
```

## Mimari (tek satır)

**zinesh-web (3000)** → fetch/iframe → **OAM Hub (8787)** → mesh işçiler
