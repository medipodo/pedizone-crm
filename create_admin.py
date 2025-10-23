#!/usr/bin/env python3
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from passlib.context import CryptContext
import uuid
from datetime import datetime, timezone

# MongoDB connection
MONGO_URL = "mongodb+srv://info_db_user:jF9GjoB9kullAaYi@pedizone.ewxga02.mongodb.net/?retryWrites=true&w=majority&appName=Pedizone"
DB_NAME = "pedizone_crm"

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

async def create_admin_user():
    client = AsyncIOMotorClient(MONGO_URL)
    db = client[DB_NAME]
    
    # Check if admin exists
    existing = await db.users.find_one({"username": "admin"})
    if existing:
        print("✅ Admin kullanıcısı zaten mevcut")
        print(f"   Username: admin")
        print(f"   Email: {existing['email']}")
        return
    
    # Create admin user
    admin_user = {
        "id": str(uuid.uuid4()),
        "username": "admin",
        "email": "admin@pedizone.com",
        "full_name": "Admin User",
        "role": "admin",
        "region_id": None,
        "password_hash": pwd_context.hash("admin123"),
        "active": True,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.users.insert_one(admin_user)
    print("✅ Admin kullanıcısı oluşturuldu!")
    print(f"   Username: admin")
    print(f"   Password: admin123")
    print(f"   Email: admin@pedizone.com")
    print(f"   Role: admin")
    
    client.close()

if __name__ == "__main__":
    asyncio.run(create_admin_user())
