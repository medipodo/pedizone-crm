#!/usr/bin/env python3
"""Senkron pymongo ile admin oluştur"""
from pymongo import MongoClient
import uuid
from datetime import datetime, timezone

# MongoDB connection
MONGO_URL = "mongodb+srv://info_db_user:jF9GjoB9kullAaYi@pedizone.ewxga02.mongodb.net/?retryWrites=true&w=majority&appName=Pedizone&tlsInsecure=true"
DB_NAME = "pedizone_crm"

try:
    # Senkron client kullan
    client = MongoClient(
        MONGO_URL,
        serverSelectionTimeoutMS=5000,
        connectTimeoutMS=5000,
        socketTimeoutMS=5000
    )
    
    # Test connection
    client.admin.command('ping')
    print("✅ MongoDB'ye bağlandı!")
    
    db = client[DB_NAME]
    
    # Check if admin exists
    existing = db.users.find_one({"username": "admin"})
    if existing:
        print("✅ Admin kullanıcısı zaten var!")
        print(f"   Username: admin")
        print(f"   Email: {existing['email']}")
    else:
        # Create admin - bcrypt hash for "admin123"
        admin_user = {
            "id": str(uuid.uuid4()),
            "username": "admin",
            "email": "admin@pedizone.com",
            "full_name": "PediZone Admin",
            "role": "admin",
            "region_id": None,
            "password_hash": "$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5aeJEcPazpqLu",
            "active": True,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        
        db.users.insert_one(admin_user)
        print("✅ Admin kullanıcısı oluşturuldu!")
        print(f"   Username: admin")
        print(f"   Password: admin123")
        print(f"   Email: admin@pedizone.com")
    
    client.close()
    print("\n🎉 İşlem tamamlandı! Artık login yapabilirsiniz.")
    
except Exception as e:
    print(f"❌ Hata: {e}")
    print("\n⚠️ MongoDB Atlas'a bağlanılamadı!")
    print("Alternatif: MongoDB Atlas web interface'den manuel ekleyin")
