# 🚀 PediZone CRM - Hızlı Deployment Rehberi

## ✅ Hazırlık Tamamlandı!

MongoDB Atlas bağlantınız yapılandırıldı ve deployment dosyaları hazır.

## 📦 İhtiyacınız Olanlar

1. **Fly.io CLI** (flyctl) kurulu olmalı
2. **Fly.io hesabı** (https://fly.io/app/sign-up)

## 🎯 3 Adımda Deployment

### Adım 1: Fly CLI Kurulumu

**macOS:**
```bash
brew install flyctl
```

**Linux:**
```bash
curl -L https://fly.io/install.sh | sh
```

**Windows:**
```powershell
powershell -Command "iwr https://fly.io/install.ps1 -useb | iex"
```

### Adım 2: Fly.io'ya Giriş

```bash
flyctl auth login
```

Tarayıcıda açılacak sayfadan giriş yapın.

### Adım 3: Deploy!

Proje dizininizde (pedizone-crm):

**Backend Deploy:**
```bash
./deploy-backend.sh
```

**Frontend Deploy:**
```bash
./deploy-frontend.sh
```

## 🎉 Tamamlandı!

Script'ler çalıştıktan sonra:
- Backend: `https://pedizone-api.fly.dev`
- Frontend: `https://pedizone-web.fly.dev`

## 📝 Manuel Deployment (Opsiyonel)

Script kullanmak istemezseniz:

### Backend:
```bash
cd backend

# App oluştur
flyctl launch --no-deploy

# Secrets ayarla
flyctl secrets set MONGO_URL="mongodb+srv://info_db_user:jF9GjoB9kullAaYi@pedizone.ewxga02.mongodb.net/?retryWrites=true&w=majority&appName=Pedizone"
flyctl secrets set DB_NAME="pedizone_crm"
flyctl secrets set CORS_ORIGINS="*"

# Deploy
flyctl deploy
```

### Frontend:
```bash
cd frontend

# App oluştur
flyctl launch --no-deploy

# Deploy
flyctl deploy
```

## 🔍 Kontrol Komutları

```bash
# Logları görüntüle
flyctl logs -a pedizone-api
flyctl logs -a pedizone-web

# Status kontrol
flyctl status -a pedizone-api
flyctl status -a pedizone-web

# Tarayıcıda aç
flyctl open -a pedizone-web
```

## 🐛 Sorun mu Var?

1. **MongoDB bağlantı hatası:** MongoDB Atlas'ta Network Access'te `0.0.0.0/0` eklediğinizden emin olun
2. **CORS hatası:** Backend secrets'ta `CORS_ORIGINS="*"` olduğunu kontrol edin
3. **Build hatası:** `flyctl deploy --no-cache` ile tekrar deneyin

## 🔄 Güncelleme

Kod değişikliği yaptığınızda:

```bash
# Backend için
cd backend
flyctl deploy

# Frontend için
cd frontend
flyctl deploy
```

## 📚 Daha Fazla Bilgi

Detaylı rehber için: `DEPLOY_FLYIO.md`

---

**Database Info:**
- MongoDB Atlas Cluster: pedizone.ewxga02.mongodb.net
- Database: pedizone_crm
- User: info_db_user ✅

**Happy Coding! 🎉**
