# 🔧 Netlify "Not Found" Sorunu - Çözüm

## Sorun
https://pedizone-crm.netlify.app/login → "Not Found" hatası

## Neden?
React Router ile SPA (Single Page Application) kullanıyoruz. Netlify tüm route'ları `/index.html`'e yönlendirmeli.

## Çözüm

### Adım 1: Netlify Environment Variable Kontrolü
https://app.netlify.com/sites/pedizone-crm/settings/env

**Olması gereken:**
```
REACT_APP_BACKEND_URL = https://pedizone-api.fly.dev
```

Yoksa ekleyin!

### Adım 2: Redeploy
https://app.netlify.com/sites/pedizone-crm/deploys

- "Trigger deploy" → "Clear cache and deploy site"

### Adım 3: netlify.toml Kontrolü
`netlify.toml` dosyasında redirects var, doğru:

```toml
[[redirects]]
  from = "/*"
  to = "/index.html"
  status = 200
```

Bu kodu zaten ekledik, sorun olmamalı.

## Test
Deploy sonrası:
- https://pedizone-crm.netlify.app → Ana sayfa ✅
- https://pedizone-crm.netlify.app/login → Login sayfası ✅
- https://pedizone-crm.netlify.app/dashboard → Dashboard ✅

## Emergent vs Production Farkı

**preview.emergentagent.com:**
- Geliştirme ortamı
- Her değişiklikte otomatik güncellenir
- Sadece development için

**pedizone-crm.netlify.app:**
- Production ortamı
- GitHub push → Netlify build → Canlı
- 7/24 çalışır, uykuya geçmez
- CDN ile hızlı
- Ücretsiz 100GB bandwidth

## Emergent Hakkında
Emergent bir **geliştirme platformu**. Kodunuzu yazıp test ediyorsunuz.

Production için:
- Frontend: Netlify (7/24 aktif)
- Backend: Fly.io (7/24 aktif)
- Database: MongoDB Atlas (7/24 aktif)

Hiçbiri uykuya geçmez, hepsi sürekli aktif! 🚀
