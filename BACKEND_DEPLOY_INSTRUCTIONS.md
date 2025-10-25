# 🚀 Backend Deploy Talimatları

## Sorun
- Frontend (pedizone.xyz) güncel ✅
- Backend (pedizone-api.fly.dev) ESKİ ❌
- Bu yüzden ekleme işlemleri başarısız oluyor

## Çözüm: Backend'i Fly.io'ya Deploy Et

### Adım 1: Terminal Aç
Kendi bilgisayarınızda terminal açın

### Adım 2: GitHub'dan Güncel Kodu Çek
```bash
git clone https://github.com/medipodo/pedizone-crm.git
cd pedizone-crm/backend
```

### Adım 3: Fly.io'ya Login
```bash
fly auth login
```
(Tarayıcıda Fly.io'ya giriş yapın)

### Adım 4: Deploy
```bash
fly deploy
```

### Adım 5: Bekle
2-3 dakika bekleyin, deploy tamamlanacak

### Adım 6: Test Et
https://pedizone.xyz'de ürün eklemeyi deneyin, çalışacak!

---

## Alternatif: GitHub Actions (Otomatik)

Eğer her push'ta otomatik deploy istiyorsanız:

1. GitHub repo → Settings → Secrets and variables → Actions
2. "New repository secret" tıklayın
3. Name: `FLY_API_TOKEN`
4. Value: Fly.io token'ınız (https://fly.io/user/personal_access_tokens)
5. Save

Artık her push'ta otomatik deploy olacak!

---

## Hızlı Test

Deploy sonrası çalışıyor mu test et:
```bash
curl https://pedizone-api.fly.dev/api/status
```

Eğer güncel response gelirse, başarılı! ✅
