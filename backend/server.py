from fastapi import FastAPI, APIRouter, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, timezone, timedelta
from passlib.context import CryptContext
import jwt

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
# Motor configuration for local MongoDB
client = AsyncIOMotorClient(
    mongo_url,
    serverSelectionTimeoutMS=30000,
    connectTimeoutMS=30000,
    socketTimeoutMS=30000
)
db = client[os.environ['DB_NAME']]

# Security
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()
SECRET_KEY = os.environ.get('JWT_SECRET', 'pedizone-secret-key-2025')
ALGORITHM = "HS256"

app = FastAPI()
api_router = APIRouter(prefix="/api")

# ============ MODELS ============

class User(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    username: str
    email: str
    full_name: str
    role: str  # admin, regional_manager, salesperson
    region_id: Optional[str] = None
    password_hash: str
    active: bool = True
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

class UserCreate(BaseModel):
    username: str
    email: str
    full_name: str
    password: str
    role: str
    region_id: Optional[str] = None

class UserResponse(BaseModel):
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

class Customer(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    address: str
    phone: str
    email: Optional[str] = None
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

class Product(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    code: str
    name: str
    description: Optional[str] = None
    unit_price: float
    price_1_5: Optional[float] = None  # 1-5 adet fiyatı
    price_6_10: Optional[float] = None  # 6-10 adet fiyatı
    price_11_24: Optional[float] = None  # 11-24 adet fiyatı
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

class Visit(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    customer_id: str
    salesperson_id: str
    visit_date: str
    notes: Optional[str] = None
    location: Optional[Dict[str, float]] = None  # {latitude: float, longitude: float}
    photo_base64: Optional[str] = None
    status: str = "gorusuldu"  # gorusuldu, anlasildi, randevu_alindi
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

class VisitCreate(BaseModel):
    customer_id: str
    salesperson_id: str
    visit_date: str
    notes: Optional[str] = None
    location: Optional[Dict[str, float]] = None
    photo_base64: Optional[str] = None
    status: str = "gorusuldu"

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
    payment_method: str  # nakit, kredi_karti, banka_transferi
    notes: Optional[str] = None
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

class CollectionCreate(BaseModel):
    customer_id: str
    amount: float
    collection_date: str
    payment_method: str
    notes: Optional[str] = None

class Document(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    description: Optional[str] = None
    url: str
    type: str  # katalog, brosur, fiyat_listesi
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

class DocumentCreate(BaseModel):
    title: str
    description: Optional[str] = None
    url: str
    type: str

# ============ AUTH HELPERS ============

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(days=7)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        token = credentials.credentials
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        user = await db.users.find_one({"id": user_id}, {"_id": 0})
        if user is None:
            raise HTTPException(status_code=401, detail="User not found")
        return user
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

# ============ AUTH ROUTES ============

@api_router.post("/auth/login")
async def login(request: LoginRequest):
    user = await db.users.find_one({"username": request.username}, {"_id": 0})
    if not user or not verify_password(request.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Kullanıcı adı veya şifre hatalı")
    
    if not user.get("active", True):
        raise HTTPException(status_code=401, detail="Hesap devre dışı")
    
    access_token = create_access_token({"sub": user["id"], "role": user["role"]})
    user_response = UserResponse(**user)
    return {"access_token": access_token, "token_type": "bearer", "user": user_response}

@api_router.get("/auth/me", response_model=UserResponse)
async def get_me(current_user: dict = Depends(get_current_user)):
    return UserResponse(**current_user)

# ============ DASHBOARD ============

@api_router.get("/dashboard/stats")
async def get_dashboard_stats(current_user: dict = Depends(get_current_user)):
    role = current_user["role"]
    user_id = current_user["id"]
    
    # Tarih filtreleri
    now = datetime.now(timezone.utc)
    start_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0).isoformat()
    
    if role == "admin":
        # Tüm sistem istatistikleri
        total_sales_docs = await db.sales.find({}).to_list(10000)
        total_visits = await db.visits.count_documents({})
        total_collections_docs = await db.collections.find({}).to_list(10000)
        total_customers = await db.customers.count_documents({})
        
        total_sales_amount = sum([s["total_amount"] for s in total_sales_docs])
        total_collections_amount = sum([c["amount"] for c in total_collections_docs])
        
        # Bu ay
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
        # Bölge sorumlusu - kendi bölgesindeki ekibin istatistikleri
        region_id = current_user.get("region_id")
        if not region_id:
            return {"error": "Bölge ataması yok"}
        
        # Bölgedeki plasiyer ID'lerini al
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
        # Plasiyer - kendi istatistikleri
        my_sales = await db.sales.find({"salesperson_id": user_id}).to_list(10000)
        my_visits = await db.visits.count_documents({"salesperson_id": user_id})
        my_collections_docs = await db.collections.find({"salesperson_id": user_id}).to_list(10000)
        
        total_sales_amount = sum([s["total_amount"] for s in my_sales])
        total_collections_amount = sum([c["amount"] for c in my_collections_docs])
        
        monthly_sales = [s for s in my_sales if s["created_at"] >= start_of_month]
        monthly_amount = sum([s["total_amount"] for s in monthly_sales])
        
        # Prim emoji hesaplama
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
        raise HTTPException(status_code=403, detail="Yetkisiz erişim")
    
    query = {}
    if current_user["role"] == "regional_manager":
        query = {"region_id": current_user.get("region_id")}
    
    users = await db.users.find(query, {"_id": 0, "password_hash": 0}).to_list(1000)
    return [UserResponse(**u) for u in users]

@api_router.post("/users", response_model=UserResponse)
async def create_user(user_create: UserCreate, current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Sadece admin kullanıcı ekleyebilir")
    
    existing = await db.users.find_one({"username": user_create.username})
    if existing:
        raise HTTPException(status_code=400, detail="Kullanıcı adı zaten mevcut")
    
    user_dict = user_create.model_dump()
    password = user_dict.pop("password")
    user_obj = User(**user_dict, password_hash=get_password_hash(password))
    
    await db.users.insert_one(user_obj.model_dump())
    return UserResponse(**user_obj.model_dump())

@api_router.put("/users/{user_id}", response_model=UserResponse)
async def update_user(user_id: str, user_update: dict, current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Yetkisiz erişim")
    
    if "password" in user_update:
        user_update["password_hash"] = get_password_hash(user_update.pop("password"))
    
    await db.users.update_one({"id": user_id}, {"$set": user_update})
    updated = await db.users.find_one({"id": user_id}, {"_id": 0, "password_hash": 0})
    return UserResponse(**updated)

@api_router.delete("/users/{user_id}")
async def delete_user(user_id: str, current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Yetkisiz erişim")
    await db.users.delete_one({"id": user_id})
    return {"message": "Kullanıcı silindi"}

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
    return region_obj

@api_router.put("/regions/{region_id}", response_model=Region)
async def update_region(region_id: str, region_update: dict, current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Yetkisiz erişim")
    await db.regions.update_one({"id": region_id}, {"$set": region_update})
    updated = await db.regions.find_one({"id": region_id}, {"_id": 0})
    return Region(**updated)

@api_router.delete("/regions/{region_id}")
async def delete_region(region_id: str, current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Yetkisiz erişim")
    await db.regions.delete_one({"id": region_id})
    return {"message": "Bölge silindi"}

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
    return customer_obj

@api_router.put("/customers/{customer_id}", response_model=Customer)
async def update_customer(customer_id: str, customer_update: dict, current_user: dict = Depends(get_current_user)):
    await db.customers.update_one({"id": customer_id}, {"$set": customer_update})
    updated = await db.customers.find_one({"id": customer_id}, {"_id": 0})
    return Customer(**updated)

@api_router.delete("/customers/{customer_id}")
async def delete_customer(customer_id: str, current_user: dict = Depends(get_current_user)):
    await db.customers.delete_one({"id": customer_id})
    return {"message": "Müşteri silindi"}

# ============ PRODUCTS ============

@api_router.get("/products", response_model=List[Product])
async def get_products(current_user: dict = Depends(get_current_user)):
    products = await db.products.find({"active": True}, {"_id": 0}).to_list(10000)
    return products

@api_router.post("/products", response_model=Product)
async def create_product(product: ProductCreate, current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Sadece admin ürün ekleyebilir")
    product_obj = Product(**product.model_dump())
    await db.products.insert_one(product_obj.model_dump())
    return product_obj

@api_router.put("/products/{product_id}", response_model=Product)
async def update_product(product_id: str, product_update: dict, current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Yetkisiz erişim")
    await db.products.update_one({"id": product_id}, {"$set": product_update})
    updated = await db.products.find_one({"id": product_id}, {"_id": 0})
    return Product(**updated)

@api_router.delete("/products/{product_id}")
async def delete_product(product_id: str, current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Yetkisiz erişim")
    await db.products.update_one({"id": product_id}, {"$set": {"active": False}})
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
    visit_data["salesperson_id"] = current_user["id"]  # Override with current user
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

# ============ INIT ADMIN ============

@api_router.post("/init")
async def initialize_system():
    # Check if admin exists
    admin_exists = await db.users.find_one({"role": "admin"})
    if admin_exists:
        return {"message": "Sistem zaten başlatılmış"}
    
    # Create default admin
    admin = User(
        username="admin",
        email="admin@pedizone.com",
        full_name="PediZone Admin",
        role="admin",
        password_hash=get_password_hash("admin123")
    )
    await db.users.insert_one(admin.model_dump())
    
    # Create sample region
    region = Region(
        name="İstanbul Anadolu",
        description="İstanbul Anadolu bölgesi"
    )
    await db.regions.insert_one(region.model_dump())
    
    return {"message": "Sistem başlatıldı", "admin_username": "admin", "admin_password": "admin123"}

app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
