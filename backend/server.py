"""
PediZone CRM Backend - Güvenlik Odaklı Versiyon
Güvenlik iyileştirmeleri uygulandı.
"""

from fastapi import FastAPI, APIRouter, HTTPException, Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import sys
import logging
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict, EmailStr, field_validator
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, timezone, timedelta
from passlib.context import CryptContext
import jwt
import re
from collections import defaultdict
import time

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# ============ ENVIRONMENT VALIDATION ============
def validate_env_variables():
    """Zorunlu environment değişkenlerini kontrol et"""
    required_vars = ['MONGO_URL', 'DB_NAME', 'JWT_SECRET']
    missing = []
    
    for var in required_vars:
        value = os.environ.get(var)
        if not value or value.strip() == '':
            missing.append(var)
    
    if missing:
        error_msg = f"KRITIK HATA: Aşağıdaki zorunlu environment değişkenleri eksik veya boş: {', '.join(missing)}"
        print(f"\n{'='*60}")
        print(error_msg)
        print("Lütfen .env dosyasını kontrol edin ve gerekli değişkenleri ayarlayın.")
        print(f"{'='*60}\n")
        # Production'da crash etmeli, development'da uyarı ver
        if os.environ.get('ENVIRONMENT', 'development') == 'production':
            sys.exit(1)
        else:
            print("⚠️ Development modunda - varsayılan değerlerle devam ediliyor (GÜVENLİ DEĞİL!)")

validate_env_variables()

# ============ CONFIGURATION ============
MONGO_URL = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
DB_NAME = os.environ.get('DB_NAME', 'pedizone_crm')
JWT_SECRET = os.environ.get('JWT_SECRET')
ALGORITHM = "HS256"
TOKEN_EXPIRE_HOURS = 1
ENVIRONMENT = os.environ.get('ENVIRONMENT', 'development')

# JWT Secret için fallback sadece development'da
if not JWT_SECRET:
    if ENVIRONMENT == 'production':
        raise ValueError("JWT_SECRET production'da zorunludur!")
    JWT_SECRET = 'dev-only-insecure-secret-change-in-production'
    print("⚠️ UYARI: JWT_SECRET ayarlanmamış, güvensiz varsayılan kullanılıyor!")

# CORS Origins
CORS_ORIGINS = os.environ.get('CORS_ORIGINS', '')
if not CORS_ORIGINS or CORS_ORIGINS == '*':
    if ENVIRONMENT == 'production':
        print("⚠️ UYARI: CORS_ORIGINS production'da '*' olmamalı!")
    ALLOWED_ORIGINS = ["*"]
else:
    ALLOWED_ORIGINS = [origin.strip() for origin in CORS_ORIGINS.split(',') if origin.strip()]

# ============ LOGGING SETUP ============
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ============ DATABASE CONNECTION ============
try:
    client = AsyncIOMotorClient(
        MONGO_URL,
        serverSelectionTimeoutMS=30000,
        connectTimeoutMS=30000,
        socketTimeoutMS=30000
    )
    db = client[DB_NAME]
    logger.info(f"MongoDB bağlantısı başlatıldı: {DB_NAME}")
except Exception as e:
    logger.error(f"MongoDB bağlantı hatası: {e}")
    raise

# ============ SECURITY ============
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()

# Simple in-memory rate limiter for login attempts
class RateLimiter:
    def __init__(self, max_attempts: int = 5, window_seconds: int = 300):
        self.max_attempts = max_attempts
        self.window_seconds = window_seconds
        self.attempts = defaultdict(list)
    
    def is_rate_limited(self, key: str) -> bool:
        now = time.time()
        # Eski denemeleri temizle
        self.attempts[key] = [t for t in self.attempts[key] if now - t < self.window_seconds]
        return len(self.attempts[key]) >= self.max_attempts
    
    def record_attempt(self, key: str):
        self.attempts[key].append(time.time())
    
    def reset(self, key: str):
        self.attempts[key] = []

login_rate_limiter = RateLimiter(max_attempts=5, window_seconds=300)  # 5 dakikada 5 deneme

# ============ VALIDATION HELPERS ============
def validate_username(username: str) -> str:
    """Username validasyonu"""
    if not username or len(username) < 3:
        raise ValueError("Kullanıcı adı en az 3 karakter olmalı")
    if len(username) > 50:
        raise ValueError("Kullanıcı adı en fazla 50 karakter olabilir")
    if not re.match(r'^[a-zA-Z0-9_]+$', username):
        raise ValueError("Kullanıcı adı sadece harf, rakam ve alt çizgi içerebilir")
    return username.lower().strip()

def validate_password(password: str) -> str:
    """Şifre validasyonu"""
    if not password or len(password) < 6:
        raise ValueError("Şifre en az 6 karakter olmalı")
    if len(password) > 128:
        raise ValueError("Şifre en fazla 128 karakter olabilir")
    return password

app = FastAPI(title="PediZone CRM API", version="2.0.0")
api_router = APIRouter(prefix="/api")

# ============ MODELS ============

class User(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    username: str
    email: EmailStr
    full_name: str
    role: str  # admin, regional_manager, salesperson
    region_id: Optional[str] = None
    password_hash: str
    active: bool = True
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

class UserCreate(BaseModel):
    username: str
    email: EmailStr
    full_name: str
    password: str
    role: str
    region_id: Optional[str] = None
    
    @field_validator('username')
    @classmethod
    def validate_username_field(cls, v):
        return validate_username(v)
    
    @field_validator('password')
    @classmethod
    def validate_password_field(cls, v):
        return validate_password(v)
    
    @field_validator('role')
    @classmethod
    def validate_role(cls, v):
        allowed_roles = ['admin', 'regional_manager', 'salesperson']
        if v not in allowed_roles:
            raise ValueError(f"Geçersiz rol. İzin verilen roller: {', '.join(allowed_roles)}")
        return v
    
    @field_validator('full_name')
    @classmethod
    def validate_full_name(cls, v):
        if not v or len(v.strip()) < 2:
            raise ValueError("Ad soyad en az 2 karakter olmalı")
        return v.strip()

class UserUpdate(BaseModel):
    """Kullanıcı güncelleme modeli - güvenli alanlar"""
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    role: Optional[str] = None
    region_id: Optional[str] = None
    active: Optional[bool] = None
    password: Optional[str] = None
    
    @field_validator('password')
    @classmethod
    def validate_password_field(cls, v):
        if v is not None:
            return validate_password(v)
        return v
    
    @field_validator('role')
    @classmethod
    def validate_role(cls, v):
        if v is not None:
            allowed_roles = ['admin', 'regional_manager', 'salesperson']
            if v not in allowed_roles:
                raise ValueError(f"Geçersiz rol")
        return v

class UserResponse(BaseModel):
    """API response için güvenli kullanıcı modeli - password_hash YOK"""
    id: str
    username: str
    email: str
    full_name: str
    role: str
    region_id: Optional[str] = None
    active: bool
    created_at: str

class LoginRequest(BaseModel):
    username: str
    password: str
    
    @field_validator('username')
    @classmethod
    def clean_username(cls, v):
        return v.strip().lower() if v else v

class Region(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: Optional[str] = None
    manager_id: Optional[str] = None
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

class RegionCreate(BaseModel):
    name: str
    description: Optional[str] = None
    manager_id: Optional[str] = None
    
    @field_validator('name')
    @classmethod
    def validate_name(cls, v):
        if not v or len(v.strip()) < 2:
            raise ValueError("Bölge adı en az 2 karakter olmalı")
        return v.strip()

class Customer(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    address: str
    phone: str
    email: Optional[EmailStr] = None
    region_id: str
    tax_number: Optional[str] = None
    notes: Optional[str] = None
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

class CustomerCreate(BaseModel):
    name: str
    address: str
    phone: str
    email: Optional[str] = None
    region_id: str
    tax_number: Optional[str] = None
    notes: Optional[str] = None
    
    @field_validator('name')
    @classmethod
    def validate_name(cls, v):
        if not v or len(v.strip()) < 2:
            raise ValueError("Müşteri adı en az 2 karakter olmalı")
        return v.strip()
    
    @field_validator('phone')
    @classmethod
    def validate_phone(cls, v):
        if not v or len(v.strip()) < 5:
            raise ValueError("Geçerli bir telefon numarası girin")
        return v.strip()
    
    @field_validator('email')
    @classmethod
    def validate_email(cls, v):
        if v is None or v == '' or v.strip() == '':
            return None
        return v.strip()

class Product(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    code: str
    name: str
    description: Optional[str] = None
    unit_price: float
    price_1_5: Optional[float] = None
    price_6_10: Optional[float] = None
    price_11_24: Optional[float] = None
    unit: str = "adet"
    photo_base64: Optional[str] = None
    active: bool = True
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

class ProductCreate(BaseModel):
    code: str
    name: str
    description: Optional[str] = None
    unit_price: float
    price_1_5: Optional[float] = None
    price_6_10: Optional[float] = None
    price_11_24: Optional[float] = None
    unit: str = "adet"
    photo_base64: Optional[str] = None
    active: bool = True
    
    @field_validator('code', 'name')
    @classmethod
    def validate_required_string(cls, v):
        if not v or len(v.strip()) < 1:
            raise ValueError("Bu alan zorunludur")
        return v.strip()
    
    @field_validator('unit_price')
    @classmethod
    def validate_price(cls, v):
        if v < 0:
            raise ValueError("Fiyat negatif olamaz")
        return v

class Visit(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    customer_id: str
    salesperson_id: str
    visit_date: str
    notes: Optional[str] = None
    location: Optional[Dict[str, float]] = None
    photo_base64: Optional[str] = None
    status: str = "gorusuldu"
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

class VisitCreate(BaseModel):
    customer_id: str
    salesperson_id: str
    visit_date: str
    notes: Optional[str] = None
    location: Optional[Dict[str, float]] = None
    photo_base64: Optional[str] = None
    status: str = "gorusuldu"
    
    @field_validator('status')
    @classmethod
    def validate_status(cls, v):
        allowed = ['gorusuldu', 'anlasildi', 'randevu_alindi']
        if v not in allowed:
            raise ValueError(f"Geçersiz durum")
        return v

class SaleItem(BaseModel):
    product_id: str
    product_name: str
    quantity: float
    unit_price: float
    total: float

class Sale(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    customer_id: str
    salesperson_id: str
    sale_date: str
    items: List[SaleItem]
    total_amount: float
    notes: Optional[str] = None
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

class SaleCreate(BaseModel):
    customer_id: str
    sale_date: str
    items: List[SaleItem]
    total_amount: float
    notes: Optional[str] = None

class Collection(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    customer_id: str
    salesperson_id: str
    amount: float
    collection_date: str
    payment_method: str
    notes: Optional[str] = None
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

class CollectionCreate(BaseModel):
    customer_id: str
    amount: float
    collection_date: str
    payment_method: str
    notes: Optional[str] = None
    
    @field_validator('payment_method')
    @classmethod
    def validate_payment_method(cls, v):
        allowed = ['nakit', 'kredi_karti', 'banka_transferi']
        if v not in allowed:
            raise ValueError(f"Geçersiz ödeme yöntemi")
        return v
    
    @field_validator('amount')
    @classmethod
    def validate_amount(cls, v):
        if v <= 0:
            raise ValueError("Tutar pozitif olmalı")
        return v

class Document(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    description: Optional[str] = None
    url: Optional[str] = None
    type: str
    file_name: Optional[str] = None
    file_base64: Optional[str] = None
    file_type: Optional[str] = None
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

class DocumentCreate(BaseModel):
    title: str
    description: Optional[str] = None
    url: Optional[str] = None
    type: str
    file_name: Optional[str] = None
    file_base64: Optional[str] = None
    file_type: Optional[str] = None
    
    @field_validator('type')
    @classmethod
    def validate_type(cls, v):
        allowed = ['katalog', 'brosur', 'fiyat_listesi']
        if v not in allowed:
            raise ValueError(f"Geçersiz doküman tipi")
        return v

# ============ AUTH HELPERS ============

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Şifre doğrulama"""
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except Exception:
        return False

def get_password_hash(password: str) -> str:
    """Şifre hashleme"""
    return pwd_context.hash(password)

def create_access_token(data: dict) -> str:
    """JWT token oluşturma - exp ve iat dahil"""
    to_encode = data.copy()
    now = datetime.now(timezone.utc)
    expire = now + timedelta(hours=TOKEN_EXPIRE_HOURS)
    to_encode.update({
        "exp": expire,
        "iat": now  # Token oluşturulma zamanı
    })
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    """Mevcut kullanıcıyı JWT'den al - password_hash HARİÇ"""
    try:
        token = credentials.credentials
        payload = jwt.decode(token, JWT_SECRET, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        if user_id is None:
            logger.warning("Token'da user ID bulunamadı")
            raise HTTPException(status_code=401, detail="Geçersiz kimlik bilgisi")
        
        # password_hash'i projection'dan hariç tut
        user = await db.users.find_one(
            {"id": user_id}, 
            {"_id": 0, "password_hash": 0}
        )
        if user is None:
            logger.warning(f"Token'daki kullanıcı bulunamadı: {user_id}")
            raise HTTPException(status_code=401, detail="Kullanıcı bulunamadı")
        
        if not user.get("active", True):
            raise HTTPException(status_code=401, detail="Hesap devre dışı")
        
        return user
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Oturum süresi doldu, lütfen tekrar giriş yapın")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Geçersiz kimlik bilgisi")

# ============ DATABASE INITIALIZATION ============

async def ensure_indexes():
    """Veritabanı indexlerini oluştur"""
    try:
        # Users için unique indexler
        await db.users.create_index("username", unique=True)
        await db.users.create_index("email", unique=True)
        await db.users.create_index("id", unique=True)
        
        # Diğer koleksiyonlar için indexler
        await db.regions.create_index("id", unique=True)
        await db.customers.create_index("id", unique=True)
        await db.products.create_index("id", unique=True)
        await db.products.create_index("code", unique=True)
        await db.visits.create_index("id", unique=True)
        await db.sales.create_index("id", unique=True)
        await db.collections.create_index("id", unique=True)
        await db.documents.create_index("id", unique=True)
        
        logger.info("Veritabanı indexleri oluşturuldu")
    except Exception as e:
        logger.error(f"Index oluşturma hatası: {e}")

@app.on_event("startup")
async def startup_event():
    """Uygulama başlangıcında çalışacak işlemler"""
    logger.info("Uygulama başlatılıyor...")
    
    # Veritabanı bağlantısını test et
    try:
        await client.admin.command('ping')
        logger.info("MongoDB bağlantısı başarılı")
    except Exception as e:
        logger.error(f"MongoDB bağlantı hatası: {e}")
        raise
    
    # Indexleri oluştur
    await ensure_indexes()
    logger.info("Uygulama başlatıldı")

@app.on_event("shutdown")
async def shutdown_event():
    """Uygulama kapanışında çalışacak işlemler"""
    logger.info("Uygulama kapatılıyor...")
    client.close()
    logger.info("MongoDB bağlantısı kapatıldı")

# ============ AUTH ROUTES ============

@api_router.post("/auth/login")
async def login(request: LoginRequest, req: Request):
    """Kullanıcı girişi - Rate limiting ile korumalı"""
    client_ip = req.client.host if req.client else "unknown"
    rate_limit_key = f"{client_ip}:{request.username}"
    
    # Rate limit kontrolü
    if login_rate_limiter.is_rate_limited(rate_limit_key):
        logger.warning(f"Rate limit aşıldı: {rate_limit_key}")
        raise HTTPException(
            status_code=429, 
            detail="Çok fazla başarısız giriş denemesi. Lütfen 5 dakika bekleyin."
        )
    
    # Kullanıcıyı bul
    user = await db.users.find_one({"username": request.username}, {"_id": 0})
    
    # Güvenlik: Kullanıcı yoksa veya şifre yanlışsa aynı mesajı ver
    if not user or not verify_password(request.password, user.get("password_hash", "")):
        login_rate_limiter.record_attempt(rate_limit_key)
        logger.warning(f"Başarısız giriş denemesi: {request.username}")
        raise HTTPException(status_code=401, detail="Kullanıcı adı veya şifre hatalı")
    
    if not user.get("active", True):
        raise HTTPException(status_code=401, detail="Hesap devre dışı bırakılmış")
    
    # Başarılı giriş - rate limiter'ı sıfırla
    login_rate_limiter.reset(rate_limit_key)
    
    access_token = create_access_token({"sub": user["id"], "role": user["role"]})
    
    # Response için password_hash'i çıkar
    user_response = UserResponse(**{k: v for k, v in user.items() if k != "password_hash"})
    
    logger.info(f"Başarılı giriş: {request.username}")
    return {"access_token": access_token, "token_type": "bearer", "user": user_response}

@api_router.get("/auth/me", response_model=UserResponse)
async def get_me(current_user: dict = Depends(get_current_user)):
    """Mevcut kullanıcı bilgilerini getir"""
    return UserResponse(**current_user)

# ============ DASHBOARD ============

@api_router.get("/dashboard")
async def get_dashboard(current_user: dict = Depends(get_current_user)):
    """Dashboard istatistikleri"""
    return await get_dashboard_stats(current_user)

@api_router.get("/dashboard/stats")
async def get_dashboard_stats(current_user: dict = Depends(get_current_user)):
    role = current_user["role"]
    user_id = current_user["id"]
    
    now = datetime.now(timezone.utc)
    start_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0).isoformat()
    
    if role == "admin":
        total_sales_docs = await db.sales.find({}).to_list(10000)
        total_visits = await db.visits.count_documents({})
        total_collections_docs = await db.collections.find({}).to_list(10000)
        total_customers = await db.customers.count_documents({})
        
        total_sales_amount = sum([s["total_amount"] for s in total_sales_docs])
        total_collections_amount = sum([c["amount"] for c in total_collections_docs])
        
        monthly_sales = [s for s in total_sales_docs if s["created_at"] >= start_of_month]
        monthly_amount = sum([s["total_amount"] for s in monthly_sales])
        
        return {
            "total_sales": len(total_sales_docs),
            "total_sales_amount": total_sales_amount,
            "total_visits": total_visits,
            "total_collections": total_collections_amount,
            "total_customers": total_customers,
            "monthly_sales_amount": monthly_amount
        }
    
    elif role == "regional_manager":
        region_id = current_user.get("region_id")
        if not region_id:
            return {"error": "Bölge ataması yok"}
        
        team_users = await db.users.find({"region_id": region_id, "role": "salesperson"}, {"_id": 0}).to_list(100)
        team_ids = [u["id"] for u in team_users]
        
        team_sales = await db.sales.find({"salesperson_id": {"$in": team_ids}}).to_list(10000)
        team_visits = await db.visits.count_documents({"salesperson_id": {"$in": team_ids}})
        team_collections_docs = await db.collections.find({"salesperson_id": {"$in": team_ids}}).to_list(10000)
        
        total_sales_amount = sum([s["total_amount"] for s in team_sales])
        total_collections_amount = sum([c["amount"] for c in team_collections_docs])
        
        monthly_sales = [s for s in team_sales if s["created_at"] >= start_of_month]
        monthly_amount = sum([s["total_amount"] for s in monthly_sales])
        
        return {
            "total_sales": len(team_sales),
            "total_sales_amount": total_sales_amount,
            "total_visits": team_visits,
            "total_collections": total_collections_amount,
            "team_size": len(team_users),
            "monthly_sales_amount": monthly_amount
        }
    
    else:  # salesperson
        my_sales = await db.sales.find({"salesperson_id": user_id}).to_list(10000)
        my_visits = await db.visits.count_documents({"salesperson_id": user_id})
        my_collections_docs = await db.collections.find({"salesperson_id": user_id}).to_list(10000)
        
        total_sales_amount = sum([s["total_amount"] for s in my_sales])
        total_collections_amount = sum([c["amount"] for c in my_collections_docs])
        
        monthly_sales = [s for s in my_sales if s["created_at"] >= start_of_month]
        monthly_amount = sum([s["total_amount"] for s in monthly_sales])
        
        emoji = "🌱"
        if monthly_amount > 50000:
            emoji = "🏆"
        elif monthly_amount > 30000:
            emoji = "🔥"
        elif monthly_amount > 10000:
            emoji = "💪"
        
        return {
            "total_sales": len(my_sales),
            "total_sales_amount": total_sales_amount,
            "total_visits": my_visits,
            "total_collections": total_collections_amount,
            "monthly_sales_amount": monthly_amount,
            "commission_emoji": emoji
        }

# ============ USERS ============

@api_router.get("/users", response_model=List[UserResponse])
async def get_users(current_user: dict = Depends(get_current_user)):
    if current_user["role"] not in ["admin", "regional_manager"]:
        raise HTTPException(status_code=403, detail="Bu işlem için yetkiniz yok")
    
    query = {}
    if current_user["role"] == "regional_manager":
        query = {"region_id": current_user.get("region_id")}
    
    # password_hash'i kesinlikle hariç tut
    users = await db.users.find(query, {"_id": 0, "password_hash": 0}).to_list(1000)
    return [UserResponse(**u) for u in users]

@api_router.post("/users", response_model=UserResponse)
async def create_user(user_create: UserCreate, current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Sadece admin kullanıcı ekleyebilir")
    
    # Username kontrolü
    existing_username = await db.users.find_one({"username": user_create.username})
    if existing_username:
        raise HTTPException(status_code=400, detail="Bu kullanıcı adı zaten kullanılıyor")
    
    # Email kontrolü
    existing_email = await db.users.find_one({"email": user_create.email})
    if existing_email:
        raise HTTPException(status_code=400, detail="Bu email adresi zaten kullanılıyor")
    
    user_dict = user_create.model_dump()
    password = user_dict.pop("password")
    user_obj = User(**user_dict, password_hash=get_password_hash(password))
    
    try:
        await db.users.insert_one(user_obj.model_dump())
        logger.info(f"Yeni kullanıcı oluşturuldu: {user_create.username}")
    except Exception as e:
        if "duplicate key" in str(e).lower():
            raise HTTPException(status_code=400, detail="Kullanıcı adı veya email zaten mevcut")
        raise HTTPException(status_code=500, detail="Kullanıcı oluşturulurken bir hata oluştu")
    
    return UserResponse(**user_obj.model_dump())

@api_router.put("/users/{user_id}", response_model=UserResponse)
async def update_user(user_id: str, user_update: UserUpdate, current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Bu işlem için yetkiniz yok")
    
    # Güncellenecek alanları hazırla
    update_data = user_update.model_dump(exclude_unset=True)
    
    # Şifre güncellemesi varsa hashle
    if "password" in update_data and update_data["password"]:
        update_data["password_hash"] = get_password_hash(update_data.pop("password"))
    elif "password" in update_data:
        del update_data["password"]
    
    if not update_data:
        raise HTTPException(status_code=400, detail="Güncellenecek alan bulunamadı")
    
    await db.users.update_one({"id": user_id}, {"$set": update_data})
    updated = await db.users.find_one({"id": user_id}, {"_id": 0, "password_hash": 0})
    
    if not updated:
        raise HTTPException(status_code=404, detail="Kullanıcı bulunamadı")
    
    logger.info(f"Kullanıcı güncellendi: {user_id}")
    return UserResponse(**updated)

@api_router.delete("/users/{user_id}")
async def delete_user(user_id: str, current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Bu işlem için yetkiniz yok")
    
    # Kendini silmeye çalışmasın
    if current_user["id"] == user_id:
        raise HTTPException(status_code=400, detail="Kendi hesabınızı silemezsiniz")
    
    result = await db.users.delete_one({"id": user_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Kullanıcı bulunamadı")
    
    logger.info(f"Kullanıcı silindi: {user_id}")
    return {"message": "Kullanıcı başarıyla silindi"}

# ============ REGIONS ============

@api_router.get("/regions", response_model=List[Region])
async def get_regions(current_user: dict = Depends(get_current_user)):
    regions = await db.regions.find({}, {"_id": 0}).to_list(1000)
    return regions

@api_router.post("/regions", response_model=Region)
async def create_region(region: RegionCreate, current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Sadece admin bölge ekleyebilir")
    region_obj = Region(**region.model_dump())
    await db.regions.insert_one(region_obj.model_dump())
    logger.info(f"Yeni bölge oluşturuldu: {region.name}")
    return region_obj

@api_router.put("/regions/{region_id}", response_model=Region)
async def update_region(region_id: str, region_update: dict, current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Bu işlem için yetkiniz yok")
    await db.regions.update_one({"id": region_id}, {"$set": region_update})
    updated = await db.regions.find_one({"id": region_id}, {"_id": 0})
    if not updated:
        raise HTTPException(status_code=404, detail="Bölge bulunamadı")
    return Region(**updated)

@api_router.delete("/regions/{region_id}")
async def delete_region(region_id: str, current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Bu işlem için yetkiniz yok")
    result = await db.regions.delete_one({"id": region_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Bölge bulunamadı")
    return {"message": "Bölge başarıyla silindi"}

# ============ CUSTOMERS ============

@api_router.get("/customers", response_model=List[Customer])
async def get_customers(current_user: dict = Depends(get_current_user)):
    query = {}
    if current_user["role"] == "regional_manager":
        query = {"region_id": current_user.get("region_id")}
    customers = await db.customers.find(query, {"_id": 0}).to_list(10000)
    return customers

@api_router.post("/customers", response_model=Customer)
async def create_customer(customer: CustomerCreate, current_user: dict = Depends(get_current_user)):
    customer_obj = Customer(**customer.model_dump())
    await db.customers.insert_one(customer_obj.model_dump())
    logger.info(f"Yeni müşteri oluşturuldu: {customer.name}")
    return customer_obj

@api_router.put("/customers/{customer_id}", response_model=Customer)
async def update_customer(customer_id: str, customer_update: dict, current_user: dict = Depends(get_current_user)):
    await db.customers.update_one({"id": customer_id}, {"$set": customer_update})
    updated = await db.customers.find_one({"id": customer_id}, {"_id": 0})
    if not updated:
        raise HTTPException(status_code=404, detail="Müşteri bulunamadı")
    return Customer(**updated)

@api_router.delete("/customers/{customer_id}")
async def delete_customer(customer_id: str, current_user: dict = Depends(get_current_user)):
    result = await db.customers.delete_one({"id": customer_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Müşteri bulunamadı")
    return {"message": "Müşteri başarıyla silindi"}

# ============ PRODUCTS ============

@api_router.get("/products", response_model=List[Product])
async def get_products(current_user: dict = Depends(get_current_user)):
    products = await db.products.find({"active": True}, {"_id": 0}).to_list(10000)
    return products

@api_router.post("/products", response_model=Product)
async def create_product(product: ProductCreate, current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Sadece admin ürün ekleyebilir")
    
    # Ürün kodu kontrolü
    existing = await db.products.find_one({"code": product.code})
    if existing:
        raise HTTPException(status_code=400, detail="Bu ürün kodu zaten kullanılıyor")
    
    product_obj = Product(**product.model_dump())
    await db.products.insert_one(product_obj.model_dump())
    logger.info(f"Yeni ürün oluşturuldu: {product.name}")
    return product_obj

@api_router.put("/products/{product_id}", response_model=Product)
async def update_product(product_id: str, product_update: dict, current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Bu işlem için yetkiniz yok")
    await db.products.update_one({"id": product_id}, {"$set": product_update})
    updated = await db.products.find_one({"id": product_id}, {"_id": 0})
    if not updated:
        raise HTTPException(status_code=404, detail="Ürün bulunamadı")
    return Product(**updated)

@api_router.delete("/products/{product_id}")
async def delete_product(product_id: str, current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Bu işlem için yetkiniz yok")
    # Soft delete
    result = await db.products.update_one({"id": product_id}, {"$set": {"active": False}})
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Ürün bulunamadı")
    return {"message": "Ürün devre dışı bırakıldı"}

# ============ VISITS ============

@api_router.get("/visits", response_model=List[Visit])
async def get_visits(current_user: dict = Depends(get_current_user)):
    query = {}
    if current_user["role"] == "salesperson":
        query = {"salesperson_id": current_user["id"]}
    elif current_user["role"] == "regional_manager":
        team_users = await db.users.find({"region_id": current_user.get("region_id"), "role": "salesperson"}, {"_id": 0}).to_list(100)
        team_ids = [u["id"] for u in team_users]
        query = {"salesperson_id": {"$in": team_ids}}
    
    visits = await db.visits.find(query, {"_id": 0}).to_list(10000)
    return visits

@api_router.post("/visits", response_model=Visit)
async def create_visit(visit: VisitCreate, current_user: dict = Depends(get_current_user)):
    visit_data = visit.model_dump()
    visit_data["salesperson_id"] = current_user["id"]
    visit_obj = Visit(**visit_data)
    await db.visits.insert_one(visit_obj.model_dump())
    return visit_obj

@api_router.get("/visits/{visit_id}", response_model=Visit)
async def get_visit(visit_id: str, current_user: dict = Depends(get_current_user)):
    visit = await db.visits.find_one({"id": visit_id}, {"_id": 0})
    if not visit:
        raise HTTPException(status_code=404, detail="Ziyaret bulunamadı")
    return Visit(**visit)

# ============ SALES ============

@api_router.get("/sales", response_model=List[Sale])
async def get_sales(current_user: dict = Depends(get_current_user)):
    query = {}
    if current_user["role"] == "salesperson":
        query = {"salesperson_id": current_user["id"]}
    elif current_user["role"] == "regional_manager":
        team_users = await db.users.find({"region_id": current_user.get("region_id"), "role": "salesperson"}, {"_id": 0}).to_list(100)
        team_ids = [u["id"] for u in team_users]
        query = {"salesperson_id": {"$in": team_ids}}
    
    sales = await db.sales.find(query, {"_id": 0}).to_list(10000)
    return sales

@api_router.post("/sales", response_model=Sale)
async def create_sale(sale: SaleCreate, current_user: dict = Depends(get_current_user)):
    sale_obj = Sale(**sale.model_dump(), salesperson_id=current_user["id"])
    await db.sales.insert_one(sale_obj.model_dump())
    return sale_obj

@api_router.get("/sales/commission")
async def get_commission_data(current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "salesperson":
        raise HTTPException(status_code=403, detail="Sadece plasiyerler prim bilgisini görebilir")
    
    now = datetime.now(timezone.utc)
    start_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0).isoformat()
    
    my_sales = await db.sales.find({
        "salesperson_id": current_user["id"],
        "created_at": {"$gte": start_of_month}
    }).to_list(10000)
    
    monthly_total = sum([s["total_amount"] for s in my_sales])
    
    emoji = "🌱"
    level = "Başlangıç"
    if monthly_total > 50000:
        emoji = "🏆"
        level = "Şampiyon"
    elif monthly_total > 30000:
        emoji = "🔥"
        level = "Ateşli"
    elif monthly_total > 10000:
        emoji = "💪"
        level = "Güçlü"
    
    return {
        "monthly_total": monthly_total,
        "emoji": emoji,
        "level": level,
        "sales_count": len(my_sales)
    }

# ============ COLLECTIONS ============

@api_router.get("/collections", response_model=List[Collection])
async def get_collections(current_user: dict = Depends(get_current_user)):
    query = {}
    if current_user["role"] == "salesperson":
        query = {"salesperson_id": current_user["id"]}
    elif current_user["role"] == "regional_manager":
        team_users = await db.users.find({"region_id": current_user.get("region_id"), "role": "salesperson"}, {"_id": 0}).to_list(100)
        team_ids = [u["id"] for u in team_users]
        query = {"salesperson_id": {"$in": team_ids}}
    
    collections = await db.collections.find(query, {"_id": 0}).to_list(10000)
    return collections

@api_router.post("/collections", response_model=Collection)
async def create_collection(collection: CollectionCreate, current_user: dict = Depends(get_current_user)):
    collection_obj = Collection(**collection.model_dump(), salesperson_id=current_user["id"])
    await db.collections.insert_one(collection_obj.model_dump())
    return collection_obj

@api_router.delete("/collections/{collection_id}")
async def delete_collection(collection_id: str, current_user: dict = Depends(get_current_user)):
    # Yetki kontrolü: admin her şeyi silebilir, diğerleri sadece kendi tahsilatlarını
    query = {"id": collection_id}
    if current_user["role"] != "admin":
        query["salesperson_id"] = current_user["id"]
    
    result = await db.collections.delete_one(query)
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Tahsilat bulunamadı veya silme yetkiniz yok")
    return {"message": "Tahsilat başarıyla silindi"}

# ============ DOCUMENTS ============

@api_router.get("/documents", response_model=List[Document])
async def get_documents(current_user: dict = Depends(get_current_user)):
    documents = await db.documents.find({}, {"_id": 0}).to_list(1000)
    return documents

@api_router.post("/documents", response_model=Document)
async def create_document(document: DocumentCreate, current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Sadece admin doküman ekleyebilir")
    document_obj = Document(**document.model_dump())
    await db.documents.insert_one(document_obj.model_dump())
    return document_obj

# ============ REPORTS ============

@api_router.get("/reports/sales")
async def get_sales_report(start_date: str = None, end_date: str = None, current_user: dict = Depends(get_current_user)):
    query = {}
    if current_user["role"] == "salesperson":
        query["salesperson_id"] = current_user["id"]
    elif current_user["role"] == "regional_manager":
        team_users = await db.users.find({"region_id": current_user.get("region_id"), "role": "salesperson"}, {"_id": 0}).to_list(100)
        team_ids = [u["id"] for u in team_users]
        query["salesperson_id"] = {"$in": team_ids}
    
    if start_date:
        query["sale_date"] = {"$gte": start_date}
    if end_date:
        if "sale_date" in query:
            query["sale_date"]["$lte"] = end_date
        else:
            query["sale_date"] = {"$lte": end_date}
    
    sales = await db.sales.find(query, {"_id": 0}).to_list(10000)
    total_amount = sum([s["total_amount"] for s in sales])
    
    return {
        "sales": sales,
        "total_count": len(sales),
        "total_amount": total_amount
    }

@api_router.get("/reports/visits")
async def get_visits_report(start_date: str = None, end_date: str = None, current_user: dict = Depends(get_current_user)):
    query = {}
    if current_user["role"] == "salesperson":
        query["salesperson_id"] = current_user["id"]
    elif current_user["role"] == "regional_manager":
        team_users = await db.users.find({"region_id": current_user.get("region_id"), "role": "salesperson"}, {"_id": 0}).to_list(100)
        team_ids = [u["id"] for u in team_users]
        query["salesperson_id"] = {"$in": team_ids}
    
    if start_date:
        query["visit_date"] = {"$gte": start_date}
    if end_date:
        if "visit_date" in query:
            query["visit_date"]["$lte"] = end_date
        else:
            query["visit_date"] = {"$lte": end_date}
    
    visits = await db.visits.find(query, {"_id": 0, "photo_base64": 0}).to_list(10000)
    
    return {
        "visits": visits,
        "total_count": len(visits)
    }

# ============ HEALTH CHECK ============

@api_router.get("/health")
async def health_check():
    """Sistem sağlık kontrolü"""
    try:
        await client.admin.command('ping')
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {"status": "unhealthy", "database": "disconnected"}

# NOT: /api/init endpoint'i KALDIRILDI - Güvenlik riski!
# Admin kullanıcı oluşturmak için güvenli bir yöntem kullanın (örn: CLI script veya environment variable ile)

app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=ALLOWED_ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"],
)
