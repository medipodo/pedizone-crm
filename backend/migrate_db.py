import asyncio
import asyncpg
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.environ.get('DATABASE_URL')

async def migrate():
    """Migrate database to new schema"""
    conn = await asyncpg.connect(DATABASE_URL)
    
    try:
        print("🔄 Dropping old tables...")
        
        # Drop tables in correct order (respecting foreign keys)
        await conn.execute('DROP TABLE IF EXISTS collections CASCADE')
        await conn.execute('DROP TABLE IF EXISTS sales CASCADE')
        await conn.execute('DROP TABLE IF EXISTS visits CASCADE')
        await conn.execute('DROP TABLE IF EXISTS products CASCADE')
        await conn.execute('DROP TABLE IF EXISTS documents CASCADE')
        await conn.execute('DROP TABLE IF EXISTS customers CASCADE')
        await conn.execute('DROP TABLE IF EXISTS regions CASCADE')
        await conn.execute('DROP TABLE IF EXISTS users CASCADE')
        
        print("✅ Old tables dropped")
        print("🔄 Creating new tables...")
        
        # Users table
        await conn.execute('''
            CREATE TABLE users (
                id VARCHAR PRIMARY KEY,
                username VARCHAR UNIQUE NOT NULL,
                email VARCHAR UNIQUE NOT NULL,
                full_name VARCHAR NOT NULL,
                role VARCHAR NOT NULL,
                region_id VARCHAR,
                password_hash VARCHAR NOT NULL,
                active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT NOW()
            )
        ''')
        
        # Regions table
        await conn.execute('''
            CREATE TABLE regions (
                id VARCHAR PRIMARY KEY,
                name VARCHAR NOT NULL,
                code VARCHAR UNIQUE NOT NULL,
                manager_id VARCHAR,
                created_at TIMESTAMP DEFAULT NOW()
            )
        ''')
        
        # Customers table
        await conn.execute('''
            CREATE TABLE customers (
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
        
        # Products table WITH NEW COLUMNS
        await conn.execute('''
            CREATE TABLE products (
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
        
        # Visits table WITH location
        await conn.execute('''
            CREATE TABLE visits (
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
        
        # Sales table WITH items JSONB
        await conn.execute('''
            CREATE TABLE sales (
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
            CREATE TABLE collections (
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
            CREATE TABLE documents (
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
        
        print("✅ New tables created")
        
        # Create admin user
        print("🔄 Creating admin user...")
        await conn.execute('''
            INSERT INTO users (id, username, email, full_name, role, password_hash, active)
            VALUES ($1, $2, $3, $4, $5, $6, $7)
            ON CONFLICT (username) DO NOTHING
        ''', 'admin', 'admin', 'admin@pedizone.com', 'PediZone Admin', 'admin', 
        '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5NU.oQdZ.qK1a', True)  # password: admin123
        
        print("✅ Admin user created (username: admin, password: admin123)")
        print("🎉 Migration completed successfully!")
        
    except Exception as e:
        print(f"❌ Error during migration: {e}")
        raise
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(migrate())
