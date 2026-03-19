#!/usr/bin/env python3
"""
PediZone CRM - Güvenli Admin Oluşturma Script'i
Bu script, güvenli bir şekilde admin kullanıcısı oluşturmak için kullanılır.
"""

import asyncio
import os
import sys
import secrets
import string
from pathlib import Path
from motor.motor_asyncio import AsyncIOMotorClient
from passlib.context import CryptContext
import uuid
from datetime import datetime, timezone
from dotenv import load_dotenv

# .env dosyasını yükle
ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# Konfigürasyon
MONGO_URL = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
DB_NAME = os.environ.get('DB_NAME', 'pedizone_crm')

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def generate_secure_password(length: int = 16) -> str:
    """Güvenli rastgele şifre üret"""
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
    return ''.join(secrets.choice(alphabet) for _ in range(length))

async def create_admin_user(username: str = None, email: str = None, password: str = None):
    """Admin kullanıcısı oluştur"""
    client = AsyncIOMotorClient(MONGO_URL)
    db = client[DB_NAME]
    
    try:
        # Parametreleri al veya varsayılan kullan
        admin_username = username or input("Admin kullanıcı adı (varsayılan: admin): ").strip() or "admin"
        admin_email = email or input("Admin email (varsayılan: admin@pedizone.com): ").strip() or "admin@pedizone.com"
        
        # Mevcut admin kontrolü
        existing_username = await db.users.find_one({"username": admin_username})
        if existing_username:
            print(f"❌ '{admin_username}' kullanıcı adı zaten mevcut!")
            return False
        
        existing_email = await db.users.find_one({"email": admin_email})
        if existing_email:
            print(f"❌ '{admin_email}' email adresi zaten kullanılıyor!")
            return False
        
        # Şifre belirleme
        if password:
            admin_password = password
        else:
            use_generated = input("Güvenli rastgele şifre oluşturulsun mu? (E/h): ").strip().lower()
            if use_generated != 'h':
                admin_password = generate_secure_password()
                print(f"\n🔐 Oluşturulan şifre: {admin_password}")
                print("⚠️  Bu şifreyi güvenli bir yerde saklayın!\n")
            else:
                admin_password = input("Şifre (min 6 karakter): ").strip()
                if len(admin_password) < 6:
                    print("❌ Şifre en az 6 karakter olmalı!")
                    return False
        
        # Admin kullanıcısını oluştur
        admin_user = {
            "id": str(uuid.uuid4()),
            "username": admin_username,
            "email": admin_email,
            "full_name": "PediZone Admin",
            "role": "admin",
            "region_id": None,
            "password_hash": pwd_context.hash(admin_password),
            "active": True,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        
        await db.users.insert_one(admin_user)
        
        print("\n" + "="*50)
        print("✅ Admin kullanıcısı başarıyla oluşturuldu!")
        print("="*50)
        print(f"   Kullanıcı adı: {admin_username}")
        print(f"   Email: {admin_email}")
        print(f"   Rol: admin")
        if password or use_generated != 'h':
            print(f"   Şifre: {admin_password}")
        print("="*50)
        
        return True
        
    except Exception as e:
        print(f"❌ Hata: {e}")
        return False
    finally:
        client.close()

async def list_users():
    """Mevcut kullanıcıları listele"""
    client = AsyncIOMotorClient(MONGO_URL)
    db = client[DB_NAME]
    
    try:
        users = await db.users.find({}, {"_id": 0, "password_hash": 0}).to_list(100)
        
        if not users:
            print("📭 Henüz kullanıcı yok.")
            return
        
        print("\n" + "="*60)
        print("MEVCUT KULLANICILAR")
        print("="*60)
        
        for user in users:
            status = "✅ Aktif" if user.get("active", True) else "❌ Pasif"
            print(f"\n👤 {user['username']} ({user['email']})")
            print(f"   Ad: {user['full_name']}")
            print(f"   Rol: {user['role']}")
            print(f"   Durum: {status}")
        
        print("\n" + "="*60)
        
    finally:
        client.close()

async def main():
    """Ana menü"""
    print("\n" + "="*50)
    print("🏥 PediZone CRM - Kullanıcı Yönetimi")
    print("="*50)
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        if command == "create":
            # Komut satırı argümanları ile oluştur
            username = sys.argv[2] if len(sys.argv) > 2 else None
            email = sys.argv[3] if len(sys.argv) > 3 else None
            password = sys.argv[4] if len(sys.argv) > 4 else None
            await create_admin_user(username, email, password)
        elif command == "list":
            await list_users()
        else:
            print(f"Bilinmeyen komut: {command}")
            print("Kullanım: python create_admin.py [create|list]")
    else:
        print("\n1. Admin kullanıcı oluştur")
        print("2. Mevcut kullanıcıları listele")
        print("3. Çıkış")
        
        choice = input("\nSeçiminiz (1-3): ").strip()
        
        if choice == "1":
            await create_admin_user()
        elif choice == "2":
            await list_users()
        elif choice == "3":
            print("Görüşürüz! 👋")
        else:
            print("Geçersiz seçim.")

if __name__ == "__main__":
    asyncio.run(main())
