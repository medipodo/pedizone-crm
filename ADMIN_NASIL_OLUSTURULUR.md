# 🔐 Admin Kullanıcısı Nasıl Oluşturulur?

## YÖN TEM 1: MongoDB Atlas Web Interface (EN KOLAY) ⭐

### Adım 1: MongoDB Atlas'a Giriş
https://cloud.mongodb.com/

### Adım 2: Cluster'ınıza Gidin
- Organizations → pedizone
- Clusters → Browse Collections

### Adım 3: Database Seçin
- Database: `pedizone_crm`
- Collection: `users` (yoksa oluşturun)

### Adım 4: Admin Kullanıcısı Ekleyin
"Insert Document" butonuna tıklayın ve bu JSON'u yapıştırın:

```json
{
  "id": "admin-001",
  "username": "admin",
  "email": "admin@pedizone.com",
  "full_name": "PediZone Admin",
  "role": "admin",
  "region_id": null,
  "password_hash": "$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5aeJEcPazpqLu",
  "active": true,
  "created_at": "2025-10-23T12:00:00.000Z"
}
```

**ÖNEMLİ:** `_id` alanını MongoDB otomatik oluşturacak, siz eklemeyin!

### Adım 5: Kaydet
"Insert" butonuna basın.

### Adım 6: Login Test
https://pedizone-crm.netlify.app/login

```
Username: admin
Password: admin123
```

---

## YÖNTEM 2: MongoDB Compass (Desktop App)

### Adım 1: MongoDB Compass'ı İndirin
https://www.mongodb.com/try/download/compass

### Adım 2: Bağlantı String'i
```
mongodb+srv://info_db_user:jF9GjoB9kullAaYi@pedizone.ewxga02.mongodb.net/
```

### Adım 3: Database ve Collection
- Database: `pedizone_crm`
- Collection: `users`

### Adım 4: Insert Document
Yukarıdaki JSON'u ekleyin.

---

## YÖNTEM 3: Fly.io Deploy (Backend Güncel Olacak)

Eğer MongoDB'ye erişemiyorsanız:

### Terminal'de:
```bash
flyctl auth login
cd ~/pedizone-crm/backend
flyctl deploy
```

Deploy bittikten sonra:
```bash
curl -X POST https://pedizone-api.fly.dev/api/init
```

Bu otomatik admin oluşturacak!

---

## ✅ BAŞARILI OLDUĞUNU NASIL ANLARIM?

MongoDB'de `users` collection'ında admin kullanıcısını göreceksiniz.

Login test:
- URL: https://pedizone-crm.netlify.app/login
- Username: admin
- Password: admin123

"Giriş başarılı!" mesajı görürseniz → ✅ TAMAM!

---

## 🆘 SORUN ÇÖZME

### "Not Found" Hatası Alıyorsanız:
Backend hala eski versiyon. Fly.io'ya deploy yapın (Yöntem 3)

### "Kullanıcı adı veya şifre hatalı" Alıyorsanız:
Admin eklendi ama şifre yanlış. MongoDB'de `password_hash` alanını kontrol edin.

### "Network Error" Alıyorsanız:
Backend çalışmıyor. Fly.io'da backend'i restart edin:
```bash
flyctl apps restart pedizone-api
```

---

**EN HIZLI ÇÖZÜM: YÖNTEM 1 (MongoDB Atlas Web) - 2 dakika! ⚡**
