#!/usr/bin/env python3
"""MongoDB Atlas'a direkt admin kullanıcısı ekle"""
import requests
import json

# MongoDB Atlas Data API kullanarak admin ekle
# Ancak Data API key gerekiyor, bu yüzden başka yöntem kullanmalıyız

# Alternatif: Fly.io'ya yeni backend'i deploy etmeliyiz
print("⚠️ Backend'i Fly.io'ya deploy etmek gerekiyor!")
print()
print("ADIMLAR:")
print("1. GitHub'a push yapın")
print("2. Terminal'de: flyctl auth login")  
print("3. cd backend && flyctl deploy")
print("4. curl -X POST https://pedizone-api.fly.dev/api/init")
print()
print("Alternatif olarak MongoDB Compass ile manuel admin ekleyebilirsiniz:")
print("Connection: mongodb+srv://info_db_user:jF9GjoB9kullAaYi@pedizone.ewxga02.mongodb.net/")
print("Database: pedizone_crm")
print("Collection: users")
print()
print("Admin user JSON:")
admin_doc = {
    "id": "admin-001",
    "username": "admin",
    "email": "admin@pedizone.com",
    "full_name": "PediZone Admin",
    "role": "admin",
    "region_id": None,
    "password_hash": "$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5aeJEcPazpqLu",  # admin123
    "active": True,
    "created_at": "2025-10-23T10:00:00Z"
}
print(json.dumps(admin_doc, indent=2))
