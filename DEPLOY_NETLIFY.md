# 🚀 Netlify Deployment Rehberi - PediZone CRM

Bu rehber, PediZone CRM frontend'ini Netlify'da deploy etmek için adım adım talimatlar içerir.

## ⚠️ Önemli Not

**Backend Fly.io'da kalmalı!** Netlify sadece frontend (static files) host eder.

- Frontend: Netlify'da
- Backend: https://pedizone-api.fly.dev (Fly.io'da)

## 📋 Ön Gereksinimler

1. **Netlify Hesabı**: https://app.netlify.com/signup
2. **GitHub'a push edilmiş kod**: https://github.com/medipodo/pedizone-crm

## 🎯 Netlify Deployment Yöntemleri

### Yöntem 1: GitHub ile Otomatik Deploy (Önerilen)

#### Adım 1: Netlify'a Giriş Yapın
https://app.netlify.com

#### Adım 2: New Site from Git
1. "Add new site" → "Import an existing project" 
2. "GitHub" seçin
3. Repository'yi seçin: `medipodo/pedizone-crm`

#### Adım 3: Build Settings
Netlify otomatik olarak `netlify.toml` dosyasını algılayacak. Manuel ayarlar:

```
Base directory: frontend
Build command: yarn install && yarn build
Publish directory: frontend/build
```

#### Adım 4: Environment Variables
**Önemli!** Netlify'da bu environment variable'ı ekleyin:

```
REACT_APP_BACKEND_URL = https://pedizone-api.fly.dev
```

Eklemek için:
1. Site settings → Environment variables
2. "Add a variable"
3. Key: `REACT_APP_BACKEND_URL`
4. Value: `https://pedizone-api.fly.dev`
5. Save

#### Adım 5: Deploy
"Deploy site" butonuna basın!

### Yöntem 2: Netlify CLI (Manuel)

```bash
# Netlify CLI kurulumu
npm install -g netlify-cli

# Giriş
netlify login

# Frontend dizinine git
cd frontend

# Build
yarn install
yarn build

# Deploy
netlify deploy --prod --dir=build
```

## 🔍 Netlify Yapılandırması

Proje root'unda `netlify.toml` dosyası mevcut:

```toml
[build]
  base = "frontend"
  command = "yarn install && yarn build"
  publish = "build"

[build.environment]
  REACT_APP_BACKEND_URL = "https://pedizone-api.fly.dev"
  NODE_VERSION = "20"

[[redirects]]
  from = "/*"
  to = "/index.html"
  status = 200
```

## 🐛 Sorun Giderme

### Hata: "Deploy directory does not exist"

**Çözüm 1:** netlify.toml kontrolü
```toml
[build]
  base = "frontend"           # ✅ Doğru
  publish = "build"            # ✅ Doğru (frontend içinde build)
```

**Çözüm 2:** Build komutu test
```bash
cd frontend
yarn install
yarn build
ls -la build/  # build klasörü var mı kontrol et
```

### Hata: "Command failed with exit code 1"

**Node version hatası:**
```toml
[build.environment]
  NODE_VERSION = "20"  # React Router 7 için gerekli
```

### Hata: "Failed to fetch backend"

Backend URL kontrolü:
```bash
# Environment variable doğru mu?
echo $REACT_APP_BACKEND_URL

# Backend çalışıyor mu?
curl https://pedizone-api.fly.dev/api/
```

## ✅ Deployment Kontrolü

### 1. Build Loglarını İzleyin
Netlify dashboard → Deploys → Son deployment

### 2. Backend Bağlantısını Test Edin
Browser console'da:
```javascript
console.log(process.env.REACT_APP_BACKEND_URL)
// Çıktı: https://pedizone-api.fly.dev
```

### 3. API Çağrılarını Kontrol Edin
Network tab'inde API istekleri:
- ✅ https://pedizone-api.fly.dev/api/...
- ❌ https://localhost:8001/api/... (yanlış!)

## 🔄 Güncelleme Süreci

### Otomatik (GitHub)
1. Kodunuzu GitHub'a push edin
2. Netlify otomatik build başlatır
3. 2-3 dakika içinde yeni versiyon yayında

### Manuel (CLI)
```bash
cd frontend
yarn build
netlify deploy --prod --dir=build
```

## 🌐 Custom Domain

### Adım 1: Domain Ekle
Netlify dashboard → Domain settings → Add custom domain

### Adım 2: DNS Ayarları
Domain sağlayıcınızda (GoDaddy, Namecheap, vb.):

**A Record:**
```
Type: A
Name: @
Value: 75.2.60.5 (Netlify load balancer)
```

**CNAME Record:**
```
Type: CNAME
Name: www
Value: your-site-name.netlify.app
```

### Adım 3: SSL
Netlify otomatik olarak Let's Encrypt SSL sertifikası ekler.

## 📊 Netlify Özellikleri

### Ücretsiz Plan Limitleri
- ✅ 100GB bandwidth/ay
- ✅ 300 build minutes/ay
- ✅ Otomatik SSL
- ✅ Global CDN
- ✅ Form handling
- ✅ Split testing

### Deploy Önizleme
Her PR için otomatik önizleme URL'i oluşturulur.

## 🔐 Güvenlik

### Environment Variables
Hassas bilgileri **asla** kodda hardcode etmeyin:

❌ **Yanlış:**
```javascript
const API_URL = "https://pedizone-api.fly.dev"
```

✅ **Doğru:**
```javascript
const API_URL = process.env.REACT_APP_BACKEND_URL
```

### CORS
Backend'de (Fly.io) CORS ayarlarını kontrol edin:
```python
# backend/server.py
CORS_ORIGINS = "https://your-site.netlify.app"
```

## 🎯 Production Checklist

Deployment öncesi kontrol listesi:

- [ ] `netlify.toml` dosyası mevcut
- [ ] `REACT_APP_BACKEND_URL` environment variable ayarlandı
- [ ] Backend Fly.io'da çalışıyor
- [ ] CORS backend'de yapılandırıldı
- [ ] Build test edildi: `yarn build`
- [ ] `.env` dosyası `.gitignore`'da (güvenlik)
- [ ] GitHub'a push edildi

## 🆘 Yardım

### Netlify Destek
- Docs: https://docs.netlify.com
- Community: https://answers.netlify.com
- Status: https://www.netlifystatus.com

### Backend (Fly.io) Sorunları
Backend çalışmıyorsa:
```bash
# Fly.io logs
flyctl logs -a pedizone-api

# Restart
flyctl apps restart pedizone-api
```

## 📝 Deployment Sonrası

1. ✅ Site URL'inizi not edin: `https://your-site.netlify.app`
2. ✅ Backend CORS'u güncelle
3. ✅ Custom domain ekle (opsiyonel)
4. ✅ Analytics aktif et (Netlify Analytics)

---

**Hazırlayan**: E1 AI Agent  
**Tarih**: 2025  
**Proje**: PediZone CRM
