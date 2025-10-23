from fastapi import FastAPI, APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
import os
from pathlib import Path
from pydantic import BaseModel
from passlib.context import CryptContext
import jwt
from datetime import datetime, timedelta
import asyncpg
import asyncio

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# PostgreSQL connection
DATABASE_URL = os.environ.get('DATABASE_URL')
pool = None

async def get_db_pool():
    global pool
    if pool is None:
        pool = await asyncpg.create_pool(DATABASE_URL)
    return pool

# Security
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()
SECRET_KEY = os.environ.get('SECRET_KEY', 'your-secret-key-change-in-production')

app = FastAPI()
api_router = APIRouter(prefix="/api")

# CORS
origins = os.environ.get('CORS_ORIGINS', '*').split(',')
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Models
class LoginRequest(BaseModel):
    username: str
    password: str

class LoginResponse(BaseModel):
    access_token: str
    token_type: str
    user: dict

# Routes
@api_router.get("/")
async def root():
    return {"message": "PediZone CRM API - PostgreSQL"}

@api_router.post("/init")
async def initialize_system():
    """Create admin user"""
    pool = await get_db_pool()
    
    # Create users table if not exists
    async with pool.acquire() as conn:
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id VARCHAR PRIMARY KEY,
                username VARCHAR UNIQUE NOT NULL,
                email VARCHAR UNIQUE NOT NULL,
                full_name VARCHAR,
                role VARCHAR,
                password_hash VARCHAR NOT NULL,
                active BOOLEAN DEFAULT true,
                created_at TIMESTAMP DEFAULT NOW()
            )
        ''')
        
        # Check if admin exists
        admin = await conn.fetchrow('SELECT * FROM users WHERE username = $1', 'admin')
        
        if admin:
            return {"message": "Admin zaten var"}
        
        # Create admin
        admin_id = str(datetime.now().timestamp())
        password_hash = pwd_context.hash('admin123')
        
        await conn.execute('''
            INSERT INTO users (id, username, email, full_name, role, password_hash, active)
            VALUES ($1, $2, $3, $4, $5, $6, $7)
        ''', admin_id, 'admin', 'admin@pedizone.com', 'PediZone Admin', 'admin', password_hash, True)
        
        return {
            "message": "Sistem başlatıldı",
            "admin_username": "admin",
            "admin_password": "admin123"
        }

@api_router.post("/auth/login", response_model=LoginResponse)
async def login(request: LoginRequest):
    """Login endpoint"""
    pool = await get_db_pool()
    
    async with pool.acquire() as conn:
        user = await conn.fetchrow('SELECT * FROM users WHERE username = $1', request.username)
        
        if not user or not pwd_context.verify(request.password, user['password_hash']):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Kullanıcı adı veya şifre hatalı"
            )
        
        if not user['active']:
            raise HTTPException(status_code=403, detail="Kullanıcı aktif değil")
        
        # Create token
        token_data = {
            "sub": user['username'],
            "user_id": user['id'],
            "exp": datetime.utcnow() + timedelta(days=7)
        }
        token = jwt.encode(token_data, SECRET_KEY, algorithm="HS256")
        
        return {
            "access_token": token,
            "token_type": "bearer",
            "user": {
                "id": user['id'],
                "username": user['username'],
                "email": user['email'],
                "full_name": user['full_name'],
                "role": user['role']
            }
        }

@api_router.get("/auth/me")
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Get current user"""
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=["HS256"])
        username = payload.get("sub")
        
        pool = await get_db_pool()
        async with pool.acquire() as conn:
            user = await conn.fetchrow('SELECT * FROM users WHERE username = $1', username)
            
            if not user:
                raise HTTPException(status_code=404, detail="Kullanıcı bulunamadı")
            
            return {
                "id": user['id'],
                "username": user['username'],
                "email": user['email'],
                "full_name": user['full_name'],
                "role": user['role']
            }
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token süresi doldu")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Geçersiz token")

# Placeholder for other endpoints
@api_router.get("/status")
async def status():
    return {"status": "ok", "database": "postgresql"}

app.include_router(api_router)

@app.on_event("startup")
async def startup():
    await get_db_pool()

@app.on_event("shutdown")
async def shutdown():
    global pool
    if pool:
        await pool.close()
