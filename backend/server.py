from fastapi import FastAPI, APIRouter, HTTPException, Depends, status, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
import os
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from passlib.context import CryptContext
import jwt
from datetime import datetime, timedelta, timezone
import asyncpg
import json

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# PostgreSQL connection
DATABASE_URL = os.environ.get('DATABASE_URL')
pool = None

async def get_db_pool():
    global pool
    if pool is None:
        pool = await asyncpg.create_pool(DATABASE_URL, min_size=1, max_size=10)
    return pool

# Security
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()
SECRET_KEY = os.environ.get('SECRET_KEY', 'pedizone-secret-key-2025')

app = FastAPI(title="PediZone CRM API")
api_router = APIRouter(prefix="/api")

# CORS
origins = os.environ.get('CORS_ORIGINS', '*').split(',')
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============ MODELS ============

class LoginRequest(BaseModel):
    username: str
    password: str

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

class RegionCreate(BaseModel):
    name: str
    description: Optional[str] = None
    manager_id: Optional[str] = None

class CustomerCreate(BaseModel):
    name: str
    address: str
    phone: str
    email: Optional[str] = None
    region_id: str
    tax_number: Optional[str] = None
    notes: Optional[str] = None

class ProductCreate(BaseModel):
    name: str
    code: str
    unit_price: float
    price_1_5: Optional[float] = None
    price_6_10: Optional[float] = None
    price_11_24: Optional[float] = None
    unit: Optional[str] = "adet"
    category: Optional[str] = None
    description: Optional[str] = None
    photo_base64: Optional[str] = None

class VisitCreate(BaseModel):
    customer_id: str
    salesperson_id: str
    visit_date: str
    notes: Optional[str] = None
    location: Optional[Dict] = None

class SaleItem(BaseModel):
    product_id: str
    product_name: str
    quantity: float
    unit_price: float
    total: float

class SaleCreate(BaseModel):
    customer_id: str
    sale_date: str
    items: List[SaleItem]
    total_amount: float
    notes: Optional[str] = None

class CollectionCreate(BaseModel):
    sale_id: str
    amount: float
    collection_date: str
    payment_method: str
    notes: Optional[str] = None

class DocumentCreate(BaseModel):
    customer_id: str
    title: str
    file_name: str
    file_base64: str
    file_type: Optional[str] = None

# ============ DATABASE INIT ============

async def init_database():
    """Initialize all database tables"""
    pool = await get_db_pool()
    
    async with pool.acquire() as conn:
        # Users table
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id VARCHAR PRIMARY KEY,
                username VARCHAR UNIQUE NOT NULL,
                email VARCHAR UNIQUE NOT NULL,
                full_name VARCHAR,
                role VARCHAR,
                region_id VARCHAR,
                password_hash VARCHAR NOT NULL,
                active BOOLEAN DEFAULT true,
                created_at TIMESTAMP DEFAULT NOW()
            )
        ''')
        
        # Regions table
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS regions (
                id VARCHAR PRIMARY KEY,
                name VARCHAR NOT NULL,
                description TEXT,
                manager_id VARCHAR,
                created_at TIMESTAMP DEFAULT NOW()
            )
        ''')
        
        # Customers table
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS customers (
                id VARCHAR PRIMARY KEY,
                name VARCHAR NOT NULL,
                address TEXT,
                phone VARCHAR,
                email VARCHAR,
                region_id VARCHAR,
                tax_number VARCHAR,
                notes TEXT,
                created_at TIMESTAMP DEFAULT NOW()
            )
        ''')
        
        # Products table
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS products (
                id VARCHAR PRIMARY KEY,
                name VARCHAR NOT NULL,
                code VARCHAR UNIQUE NOT NULL,
                unit_price DECIMAL(10,2),
                price_1_5 DECIMAL(10,2),
                price_6_10 DECIMAL(10,2),
                price_11_24 DECIMAL(10,2),
                unit VARCHAR DEFAULT 'adet',
                category VARCHAR,
                description TEXT,
                photo_base64 TEXT,
                created_at TIMESTAMP DEFAULT NOW()
            )
        ''')
        
        # Visits table
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS visits (
                id VARCHAR PRIMARY KEY,
                customer_id VARCHAR,
                salesperson_id VARCHAR,
                visit_date TIMESTAMP,
                notes TEXT,
                location JSONB,
                photo_base64 TEXT,
                status VARCHAR DEFAULT 'gorusuldu',
                created_at TIMESTAMP DEFAULT NOW()
            )
        ''')
        
        # Sales table
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS sales (
                id VARCHAR PRIMARY KEY,
                customer_id VARCHAR,
                salesperson_id VARCHAR,
                sale_date TIMESTAMP,
                items JSONB,
                total_amount DECIMAL(10,2),
                notes TEXT,
                created_at TIMESTAMP DEFAULT NOW()
            )
        ''')
        
        # Collections table
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS collections (
                id VARCHAR PRIMARY KEY,
                sale_id VARCHAR,
                amount DECIMAL(10,2),
                collection_date TIMESTAMP,
                payment_method VARCHAR,
                notes TEXT,
                created_at TIMESTAMP DEFAULT NOW()
            )
        ''')
        
        # Documents table
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS documents (
                id VARCHAR PRIMARY KEY,
                customer_id VARCHAR,
                title VARCHAR NOT NULL,
                file_name VARCHAR NOT NULL,
                file_base64 TEXT NOT NULL,
                file_type VARCHAR,
                uploaded_by VARCHAR,
                created_at TIMESTAMP DEFAULT NOW()
            )
        ''')

# ============ AUTH ============

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Get current user from token"""
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=["HS256"])
        username = payload.get("sub")
        
        pool = await get_db_pool()
        async with pool.acquire() as conn:
            user = await conn.fetchrow('SELECT * FROM users WHERE username = $1', username)
            
            if not user:
                raise HTTPException(status_code=404, detail="Kullanıcı bulunamadı")
            
            return dict(user)
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token süresi doldu")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Geçersiz token")

# ============ ROUTES ============

@api_router.get("/")
async def root():
    return {"message": "PediZone CRM API - PostgreSQL", "version": "2.0"}

@api_router.get("/status")
async def status():
    return {"status": "ok", "database": "postgresql"}

@api_router.post("/init")
async def initialize_system():
    """Initialize system with tables and admin user"""
    await init_database()
    
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        admin = await conn.fetchrow('SELECT * FROM users WHERE username = $1', 'admin')
        
        if admin:
            return {"message": "Sistem zaten başlatılmış"}
        
        admin_id = f"admin-{datetime.now().timestamp()}"
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

@api_router.post("/migrate")
async def migrate_database():
    """Drop and recreate all tables - USE WITH CAUTION!"""
    pool = await get_db_pool()
    
    async with pool.acquire() as conn:
        # Drop all tables
        await conn.execute('DROP TABLE IF EXISTS collections CASCADE')
        await conn.execute('DROP TABLE IF EXISTS sales CASCADE')
        await conn.execute('DROP TABLE IF EXISTS visits CASCADE')
        await conn.execute('DROP TABLE IF EXISTS products CASCADE')
        await conn.execute('DROP TABLE IF EXISTS documents CASCADE')
        await conn.execute('DROP TABLE IF EXISTS customers CASCADE')
        await conn.execute('DROP TABLE IF EXISTS regions CASCADE')
        await conn.execute('DROP TABLE IF EXISTS users CASCADE')
        
        # Recreate with init_database
        await init_database()
        
        # Create admin
        admin_id = f"admin-{datetime.now().timestamp()}"
        password_hash = pwd_context.hash('admin123')
        
        await conn.execute('''
            INSERT INTO users (id, username, email, full_name, role, password_hash, active)
            VALUES ($1, $2, $3, $4, $5, $6, $7)
        ''', admin_id, 'admin', 'admin@pedizone.com', 'PediZone Admin', 'admin', password_hash, True)
        
        return {"message": "Database migrated successfully", "admin_created": True}

@api_router.post("/auth/login")
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
        
        token_data = {
            "sub": user['username'],
            "user_id": user['id'],
            "role": user['role'],
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
                "role": user['role'],
                "region_id": user.get('region_id')
            }
        }

@api_router.get("/auth/me", response_model=UserResponse)
async def get_me(current_user: dict = Depends(get_current_user)):
    """Get current user info"""
    return {
        "id": current_user['id'],
        "username": current_user['username'],
        "email": current_user['email'],
        "full_name": current_user['full_name'],
        "role": current_user['role'],
        "region_id": current_user.get('region_id'),
        "active": current_user['active'],
        "created_at": str(current_user['created_at'])
    }

# ============ DASHBOARD ============

@api_router.get("/dashboard/stats")
async def get_dashboard_stats(current_user: dict = Depends(get_current_user)):
    """Get dashboard statistics"""
    pool = await get_db_pool()
    
    async with pool.acquire() as conn:
        total_customers = await conn.fetchval('SELECT COUNT(*) FROM customers')
        total_sales = await conn.fetchval('SELECT COUNT(*) FROM sales')
        total_revenue = await conn.fetchval('SELECT COALESCE(SUM(total_amount), 0) FROM sales')
        
        return {
            "total_customers": total_customers or 0,
            "total_sales": total_sales or 0,
            "total_revenue": float(total_revenue or 0),
            "active_users": 1
        }

# ============ USERS ============

@api_router.get("/users", response_model=List[UserResponse])
async def get_users():
    """Get all users"""
    pool = await get_db_pool()
    
    async with pool.acquire() as conn:
        users = await conn.fetch('SELECT * FROM users ORDER BY created_at DESC')
        return [dict(u) | {"created_at": str(u['created_at'])} for u in users]

@api_router.post("/users", response_model=UserResponse)
async def create_user(user: UserCreate, current_user: dict = Depends(get_current_user)):
    """Create new user"""
    pool = await get_db_pool()
    user_id = f"user-{datetime.now().timestamp()}"
    password_hash = pwd_context.hash(user.password)
    
    async with pool.acquire() as conn:
        await conn.execute('''
            INSERT INTO users (id, username, email, full_name, role, region_id, password_hash, active)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
        ''', user_id, user.username, user.email, user.full_name, user.role, user.region_id, password_hash, True)
        
        new_user = await conn.fetchrow('SELECT * FROM users WHERE id = $1', user_id)
        return dict(new_user) | {"created_at": str(new_user['created_at'])}

# ============ REGIONS ============

@api_router.get("/regions")
async def get_regions():
    """Get all regions"""
    pool = await get_db_pool()
    
    async with pool.acquire() as conn:
        regions = await conn.fetch('SELECT * FROM regions ORDER BY name')
        return [dict(r) | {"created_at": str(r['created_at'])} for r in regions]

@api_router.post("/regions")
async def create_region(region: RegionCreate, current_user: dict = Depends(get_current_user)):
    """Create new region"""
    pool = await get_db_pool()
    region_id = f"region-{datetime.now().timestamp()}"
    
    async with pool.acquire() as conn:
        await conn.execute('''
            INSERT INTO regions (id, name, description, manager_id)
            VALUES ($1, $2, $3, $4)
        ''', region_id, region.name, region.description, region.manager_id)
        
        new_region = await conn.fetchrow('SELECT * FROM regions WHERE id = $1', region_id)
        return dict(new_region) | {"created_at": str(new_region['created_at'])}

# ============ CUSTOMERS ============

@api_router.get("/customers")
async def get_customers(
    region_id: Optional[str] = Query(None)
):
    """Get all customers"""
    pool = await get_db_pool()
    
    async with pool.acquire() as conn:
        if region_id:
            customers = await conn.fetch('SELECT * FROM customers WHERE region_id = $1 ORDER BY name', region_id)
        else:
            customers = await conn.fetch('SELECT * FROM customers ORDER BY name')
        
        return [dict(c) | {"created_at": str(c['created_at'])} for c in customers]

@api_router.post("/customers")
async def create_customer(customer: CustomerCreate, current_user: dict = Depends(get_current_user)):
    """Create new customer"""
    pool = await get_db_pool()
    customer_id = f"customer-{datetime.now().timestamp()}"
    
    async with pool.acquire() as conn:
        await conn.execute('''
            INSERT INTO customers (id, name, address, phone, email, region_id, tax_number, notes)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
        ''', customer_id, customer.name, customer.address, customer.phone, customer.email, 
        customer.region_id, customer.tax_number, customer.notes)
        
        new_customer = await conn.fetchrow('SELECT * FROM customers WHERE id = $1', customer_id)
        return dict(new_customer) | {"created_at": str(new_customer['created_at'])}

# ============ PRODUCTS ============

@api_router.get("/products")
async def get_products():
    """Get all products"""
    pool = await get_db_pool()
    
    async with pool.acquire() as conn:
        products = await conn.fetch('SELECT * FROM products ORDER BY name')
        return [dict(p) | {
            "created_at": str(p['created_at']), 
            "unit_price": float(p['unit_price']) if p['unit_price'] else 0,
            "price_1_5": float(p['price_1_5']) if p['price_1_5'] else None,
            "price_6_10": float(p['price_6_10']) if p['price_6_10'] else None,
            "price_11_24": float(p['price_11_24']) if p['price_11_24'] else None
        } for p in products]

@api_router.post("/products")
async def create_product(product: ProductCreate, current_user: dict = Depends(get_current_user)):
    """Create new product"""
    pool = await get_db_pool()
    product_id = f"product-{datetime.now().timestamp()}"
    
    async with pool.acquire() as conn:
        await conn.execute('''
            INSERT INTO products (id, name, code, unit_price, price_1_5, price_6_10, price_11_24, unit, category, description, photo_base64)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
        ''', product_id, product.name, product.code, product.unit_price, product.price_1_5, 
        product.price_6_10, product.price_11_24, product.unit, product.category, product.description, product.photo_base64)
        
        new_product = await conn.fetchrow('SELECT * FROM products WHERE id = $1', product_id)
        return dict(new_product) | {
            "created_at": str(new_product['created_at']), 
            "unit_price": float(new_product['unit_price']) if new_product['unit_price'] else 0,
            "price_1_5": float(new_product['price_1_5']) if new_product['price_1_5'] else None,
            "price_6_10": float(new_product['price_6_10']) if new_product['price_6_10'] else None,
            "price_11_24": float(new_product['price_11_24']) if new_product['price_11_24'] else None
        }

# ============ VISITS ============

@api_router.get("/visits")
async def get_visits(
    salesperson_id: Optional[str] = Query(None),
    customer_id: Optional[str] = Query(None)
):
    """Get all visits"""
    pool = await get_db_pool()
    
    async with pool.acquire() as conn:
        if salesperson_id:
            visits = await conn.fetch('SELECT * FROM visits WHERE salesperson_id = $1 ORDER BY visit_date DESC', salesperson_id)
        elif customer_id:
            visits = await conn.fetch('SELECT * FROM visits WHERE customer_id = $1 ORDER BY visit_date DESC', customer_id)
        else:
            visits = await conn.fetch('SELECT * FROM visits ORDER BY visit_date DESC LIMIT 100')
        
        return [dict(v) | {
            "created_at": str(v['created_at']),
            "visit_date": str(v['visit_date'])
        } for v in visits]

@api_router.post("/visits")
async def create_visit(visit: VisitCreate, current_user: dict = Depends(get_current_user)):
    """Create new visit"""
    pool = await get_db_pool()
    visit_id = f"visit-{datetime.now().timestamp()}"
    
    # Parse visit_date to datetime if it's a string
    if isinstance(visit.visit_date, str):
        from dateutil import parser
        visit_date_parsed = parser.parse(visit.visit_date)
    else:
        visit_date_parsed = visit.visit_date
    
    async with pool.acquire() as conn:
        await conn.execute('''
            INSERT INTO visits (id, customer_id, salesperson_id, visit_date, notes, location)
            VALUES ($1, $2, $3, $4, $5, $6)
        ''', visit_id, visit.customer_id, visit.salesperson_id, visit_date_parsed, 
        visit.notes, json.dumps(visit.location) if visit.location else None)
        
        new_visit = await conn.fetchrow('SELECT * FROM visits WHERE id = $1', visit_id)
        return dict(new_visit) | {
            "created_at": str(new_visit['created_at']),
            "visit_date": str(new_visit['visit_date'])
        }

# ============ SALES ============

@api_router.get("/sales")
async def get_sales(
    salesperson_id: Optional[str] = Query(None),
    customer_id: Optional[str] = Query(None)
):
    """Get all sales"""
    pool = await get_db_pool()
    
    async with pool.acquire() as conn:
        if salesperson_id:
            sales = await conn.fetch('SELECT * FROM sales WHERE salesperson_id = $1 ORDER BY sale_date DESC', salesperson_id)
        elif customer_id:
            sales = await conn.fetch('SELECT * FROM sales WHERE customer_id = $1 ORDER BY sale_date DESC', customer_id)
        else:
            sales = await conn.fetch('SELECT * FROM sales ORDER BY sale_date DESC LIMIT 100')
        
        return [dict(s) | {
            "created_at": str(s['created_at']),
            "sale_date": str(s['sale_date']),
            "total_amount": float(s['total_amount'])
        } for s in sales]

@api_router.post("/sales")
async def create_sale(sale: SaleCreate, current_user: dict = Depends(get_current_user)):
    """Create new sale"""
    pool = await get_db_pool()
    sale_id = f"sale-{datetime.now().timestamp()}"
    
    async with pool.acquire() as conn:
        await conn.execute('''
            INSERT INTO sales (id, customer_id, salesperson_id, sale_date, items, total_amount, notes)
            VALUES ($1, $2, $3, $4, $5, $6, $7)
        ''', sale_id, sale.customer_id, current_user['id'], sale.sale_date, 
        json.dumps([item.dict() for item in sale.items]), sale.total_amount, sale.notes)
        
        new_sale = await conn.fetchrow('SELECT * FROM sales WHERE id = $1', sale_id)
        return dict(new_sale) | {
            "created_at": str(new_sale['created_at']),
            "sale_date": str(new_sale['sale_date']),
            "total_amount": float(new_sale['total_amount'])
        }

# ============ COLLECTIONS ============

@api_router.get("/collections")
async def get_collections(
    sale_id: Optional[str] = Query(None),
    current_user: dict = Depends(get_current_user)
):
    """Get all collections"""
    pool = await get_db_pool()
    
    async with pool.acquire() as conn:
        if sale_id:
            collections = await conn.fetch('SELECT * FROM collections WHERE sale_id = $1 ORDER BY collection_date DESC', sale_id)
        else:
            collections = await conn.fetch('SELECT * FROM collections ORDER BY collection_date DESC LIMIT 100')
        
        return [dict(c) | {
            "created_at": str(c['created_at']),
            "collection_date": str(c['collection_date']),
            "amount": float(c['amount'])
        } for c in collections]

@api_router.post("/collections")
async def create_collection(collection: CollectionCreate, current_user: dict = Depends(get_current_user)):
    """Create new collection"""
    pool = await get_db_pool()
    collection_id = f"collection-{datetime.now().timestamp()}"
    
    async with pool.acquire() as conn:
        await conn.execute('''
            INSERT INTO collections (id, sale_id, amount, collection_date, payment_method, notes)
            VALUES ($1, $2, $3, $4, $5, $6)
        ''', collection_id, collection.sale_id, collection.amount, collection.collection_date, 
        collection.payment_method, collection.notes)
        
        new_collection = await conn.fetchrow('SELECT * FROM collections WHERE id = $1', collection_id)
        return dict(new_collection) | {
            "created_at": str(new_collection['created_at']),
            "collection_date": str(new_collection['collection_date']),
            "amount": float(new_collection['amount'])
        }

# ============ DOCUMENTS ============

@api_router.get("/documents")
async def get_documents(customer_id: Optional[str] = Query(None)):
    """Get all documents"""
    pool = await get_db_pool()
    
    async with pool.acquire() as conn:
        if customer_id:
            documents = await conn.fetch('SELECT * FROM documents WHERE customer_id = $1 ORDER BY created_at DESC', customer_id)
        else:
            documents = await conn.fetch('SELECT * FROM documents ORDER BY created_at DESC LIMIT 100')
        
        return [dict(d) | {"created_at": str(d['created_at'])} for d in documents]

@api_router.post("/documents")
async def create_document(document: DocumentCreate, current_user: dict = Depends(get_current_user)):
    """Create new document"""
    pool = await get_db_pool()
    document_id = f"document-{datetime.now().timestamp()}"
    
    async with pool.acquire() as conn:
        await conn.execute('''
            INSERT INTO documents (id, customer_id, title, file_name, file_base64, file_type, uploaded_by)
            VALUES ($1, $2, $3, $4, $5, $6, $7)
        ''', document_id, document.customer_id, document.title, document.file_name, 
        document.file_base64, document.file_type, current_user['id'])
        
        new_document = await conn.fetchrow('SELECT * FROM documents WHERE id = $1', document_id)
        return dict(new_document) | {"created_at": str(new_document['created_at'])}

# ============ REPORTS ============

@api_router.get("/reports/sales")
async def get_sales_report(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    current_user: dict = Depends(get_current_user)
):
    """Get sales report"""
    pool = await get_db_pool()
    
    async with pool.acquire() as conn:
        if start_date and end_date:
            total = await conn.fetchval(
                'SELECT COALESCE(SUM(total_amount), 0) FROM sales WHERE sale_date BETWEEN $1 AND $2',
                start_date, end_date
            )
        else:
            total = await conn.fetchval('SELECT COALESCE(SUM(total_amount), 0) FROM sales')
        
        return {
            "total_revenue": float(total or 0),
            "period": f"{start_date} - {end_date}" if start_date and end_date else "All time"
        }

app.include_router(api_router)

@app.on_event("startup")
async def startup():
    await get_db_pool()
    await init_database()

@app.on_event("shutdown")
async def shutdown():
    global pool
    if pool:
        await pool.close()
