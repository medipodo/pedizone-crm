# 🚀 Fly.io Deployment Rehberi - PediZone CRM

Bu rehber, PediZone CRM uygulamasını Fly.io'ya deploy etmek için adım adım talimatlar içerir.

## 📋 Ön Gereksinimler

1. **Fly.io Hesabı**: https://fly.io/app/sign-up
2. **Fly CLI Kurulumu**:
   ```bash
   # macOS
   brew install flyctl
   
   # Linux
   curl -L https://fly.io/install.sh | sh
   
   # Windows
   powershell -Command "iwr https://fly.io/install.ps1 -useb | iex"
   ```

3. **Fly.io'ya Giriş**:
   ```bash
   flyctl auth login
   ```

## 🗄️ Adım 1: MongoDB Atlas Kurulumu

PediZone CRM MongoDB kullanıyor. MongoDB Atlas ücretsiz tier ile başlayabilirsiniz:

1. https://www.mongodb.com/cloud/atlas/register adresine gidin
2. Ücretsiz cluster oluşturun (M0 Free tier)
3. Database User oluşturun (username + password)
4. Network Access'te IP whitelist'e `0.0.0.0/0` ekleyin (tüm IP'lere izin)
5. Connection string'i kopyalayın. Örnek:
   ```
   mongodb+srv://<username>:<password>@cluster0.xxxxx.mongodb.net/?retryWrites=true&w=majority
   ```

## 🔧 Adım 2: Backend Deploy

### 2.1 Backend Dizinine Geçin
```bash
cd backend
```

### 2.2 Fly App Oluşturun
```bash
flyctl launch --no-deploy
```

Sorular:
- App name: `pedizone-api` (veya istediğiniz isim)
- Region: `Amsterdam (ams)` önerilir
- PostgreSQL/Redis: **Hayır** (MongoDB kullanıyoruz)

### 2.3 Environment Variables Ayarlayın
```bash
# MongoDB Atlas connection string'inizi girin
flyctl secrets set MONGO_URL="mongodb+srv://<username>:<password>@cluster0.xxxxx.mongodb.net/?retryWrites=true&w=majority"

# Database adı
flyctl secrets set DB_NAME="pedizone_crm"

# CORS settings
flyctl secrets set CORS_ORIGINS="*"
```

### 2.4 Deploy Edin
```bash
flyctl deploy
```

### 2.5 Backend URL'i Not Edin
Deploy başarılı olduktan sonra URL'i göreceksiniz:
```
https://pedizone-api.fly.dev
```

### 2.6 Test Edin
```bash
curl https://pedizone-api.fly.dev/api/
```

Çıktı: `{"message":"Hello World"}`

## 🎨 Adım 3: Frontend Deploy

### 3.1 fly.toml'da Backend URL'i Güncelleyin
```bash
cd ../frontend
```

`fly.toml` dosyasını açın ve backend URL'inizi güncelleyin:
```toml
[build.args]
  REACT_APP_BACKEND_URL = "https://pedizone-api.fly.dev"  # Kendi backend URL'iniz
```

### 3.2 Fly App Oluşturun
```bash
flyctl launch --no-deploy
```

Sorular:
- App name: `pedizone-web` (veya istediğiniz isim)
- Region: `Amsterdam (ams)` (backend ile aynı)
- PostgreSQL/Redis: **Hayır**

### 3.3 Deploy Edin
```bash
flyctl deploy
```

### 3.4 Uygulamanızı Açın
```bash
flyctl open
```

Veya tarayıcıda: `https://pedizone-web.fly.dev`

## ✅ Deployment Kontrol

### Backend Kontrolü
```bash
# Backend loglarını izleyin
cd backend
flyctl logs

# Health check
curl https://pedizone-api.fly.dev/api/

# Status endpoint test
curl https://pedizone-api.fly.dev/api/status
```

### Frontend Kontrolü
```bash
# Frontend loglarını izleyin
cd frontend
flyctl logs

# Tarayıcıda açın
flyctl open
```

## 🔄 Güncelleme (Update)

Kod değişikliği yaptığınızda:

### Backend Güncelleme
```bash
cd backend
flyctl deploy
```

### Frontend Güncelleme
```bash
cd frontend
flyctl deploy
```

## 🐛 Troubleshooting

### Backend Hatası: "Can't connect to MongoDB"
```bash
# Secrets kontrolü
flyctl secrets list

# MONGO_URL'i yeniden ayarlayın
flyctl secrets set MONGO_URL="your-connection-string"
```

### Frontend Hatası: "Network Error"
```bash
# Backend URL kontrolü
cat fly.toml | grep REACT_APP_BACKEND_URL

# CORS ayarlarını kontrol edin (backend'de)
flyctl ssh console -a pedizone-api
```

### App Çalışmıyor
```bash
# Logları kontrol edin
flyctl logs

# App durumunu kontrol edin
flyctl status

# Restart edin
flyctl apps restart
```

### Build Hatası
```bash
# Local build test
docker build -t test-build .

# Fly.io builder'ı sıfırlayın
flyctl deploy --no-cache
```

## 💰 Maliyet Optimizasyonu

Fly.io free tier:
- 3 shared-cpu-1x VMs (256MB RAM)
- 160GB bandwidth/ay

**Öneriler:**
1. `auto_stop_machines = true` kullanın (zaten aktif)
2. `min_machines_running = 0` kullanın (kullanılmadığında dursun)
3. Gerekirse machine size'ı küçültün

## 📊 Monitoring

### Metrics Görüntüleme
```bash
# Backend metrics
flyctl dashboard -a pedizone-api

# Frontend metrics
flyctl dashboard -a pedizone-web
```

### Real-time Logs
```bash
# Backend logs
flyctl logs -a pedizone-api

# Frontend logs
flyctl logs -a pedizone-web
```

## 🔒 Güvenlik

### Production Secrets
```bash
# Güçlü secret key ekleyin (opsiyonel, gelecek için)
flyctl secrets set SECRET_KEY="your-secret-key-here"
```

### CORS Güncelleme
Production'da tüm origin'lere izin vermek yerine sadece frontend URL'inize izin verin:
```bash
flyctl secrets set CORS_ORIGINS="https://pedizone-web.fly.dev"
```

## 📚 Faydalı Komutlar

```bash
# App listesi
flyctl apps list

# SSH ile bağlanma
flyctl ssh console

# Scale up/down
flyctl scale count 2  # 2 instance
flyctl scale vm shared-cpu-2x  # Daha güçlü VM

# App silme
flyctl apps destroy app-name
```

## 🎯 Sonraki Adımlar

1. ✅ Custom domain ekleyin: `flyctl certs add yourdomain.com`
2. ✅ CI/CD pipeline kurun (GitHub Actions)
3. ✅ Monitoring ve alerting ekleyin
4. ✅ Backup stratejisi oluşturun (MongoDB Atlas auto-backup)

## 🆘 Yardım

- Fly.io Docs: https://fly.io/docs/
- Community: https://community.fly.io/
- Status: https://status.fly.io/

---

**Hazırlayan**: E1 AI Agent
**Tarih**: 2025
**Proje**: PediZone CRM
