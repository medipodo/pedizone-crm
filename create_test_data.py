#!/usr/bin/env python3
"""
Create test data for testuser to properly test role-based filtering
"""

import requests
import json
from datetime import datetime, timezone

BACKEND_URL = "https://crm-pedizone.preview.emergentagent.com/api"

def login_user(username, password):
    """Login and return token"""
    login_data = {"username": username, "password": password}
    response = requests.post(f"{BACKEND_URL}/auth/login", json=login_data, timeout=30)
    
    if response.status_code == 200:
        data = response.json()
        return data.get("access_token"), data.get("user")
    return None, None

def create_customer(token, name_suffix=""):
    """Create a test customer"""
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    
    # Get regions first
    regions_response = requests.get(f"{BACKEND_URL}/regions", headers=headers, timeout=30)
    regions = regions_response.json() if regions_response.status_code == 200 else []
    region_id = regions[0]["id"] if regions else "default-region"
    
    customer_data = {
        "name": f"Test Customer {name_suffix}",
        "address": f"Test Address {name_suffix}",
        "phone": f"555-000{name_suffix}",
        "email": f"customer{name_suffix}@test.com",
        "region_id": region_id,
        "tax_number": f"12345{name_suffix}",
        "notes": f"Test customer for {name_suffix}"
    }
    
    response = requests.post(f"{BACKEND_URL}/customers", headers=headers, json=customer_data, timeout=30)
    
    if response.status_code == 200:
        customer = response.json()
        print(f"✅ Created customer: {customer['name']} (ID: {customer['id']})")
        return customer
    else:
        print(f"❌ Failed to create customer: {response.status_code} - {response.text}")
        return None

def create_visit(token, customer_id, user_id):
    """Create a test visit"""
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    
    visit_data = {
        "customer_id": customer_id,
        "salesperson_id": user_id,
        "visit_date": datetime.now(timezone.utc).isoformat(),
        "notes": "Test visit for role-based filtering",
        "location": {"latitude": 41.0082, "longitude": 28.9784},
        "status": "gorusuldu"
    }
    
    response = requests.post(f"{BACKEND_URL}/visits", headers=headers, json=visit_data, timeout=30)
    
    if response.status_code == 200:
        visit = response.json()
        print(f"✅ Created visit: {visit['id']} for customer {customer_id}")
        return visit
    else:
        print(f"❌ Failed to create visit: {response.status_code} - {response.text}")
        return None

def create_product(token):
    """Create a test product (admin only)"""
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    
    product_data = {
        "code": "TEST-PROD-001",
        "name": "Test Product for Role Testing",
        "description": "Test product for role-based filtering",
        "unit_price": 100.0,
        "price_1_5": 95.0,
        "price_6_10": 90.0,
        "price_11_24": 85.0,
        "unit": "adet",
        "active": True
    }
    
    response = requests.post(f"{BACKEND_URL}/products", headers=headers, json=product_data, timeout=30)
    
    if response.status_code == 200:
        product = response.json()
        print(f"✅ Created product: {product['name']} (ID: {product['id']})")
        return product
    else:
        print(f"❌ Failed to create product: {response.status_code} - {response.text}")
        return None

def create_sale(token, customer_id, product_id):
    """Create a test sale"""
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    
    sale_data = {
        "customer_id": customer_id,
        "sale_date": datetime.now(timezone.utc).isoformat(),
        "items": [{
            "product_id": product_id,
            "product_name": "Test Product for Role Testing",
            "quantity": 5,
            "unit_price": 95.0,
            "total": 475.0
        }],
        "total_amount": 475.0,
        "notes": "Test sale for role-based filtering"
    }
    
    response = requests.post(f"{BACKEND_URL}/sales", headers=headers, json=sale_data, timeout=30)
    
    if response.status_code == 200:
        sale = response.json()
        print(f"✅ Created sale: {sale['id']} for customer {customer_id}")
        return sale
    else:
        print(f"❌ Failed to create sale: {response.status_code} - {response.text}")
        return None

def create_collection(token, customer_id):
    """Create a test collection"""
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    
    collection_data = {
        "customer_id": customer_id,
        "amount": 200.0,
        "collection_date": datetime.now(timezone.utc).isoformat(),
        "payment_method": "nakit",
        "notes": "Test collection for role-based filtering"
    }
    
    response = requests.post(f"{BACKEND_URL}/collections", headers=headers, json=collection_data, timeout=30)
    
    if response.status_code == 200:
        collection = response.json()
        print(f"✅ Created collection: {collection['id']} for customer {customer_id}")
        return collection
    else:
        print(f"❌ Failed to create collection: {response.status_code} - {response.text}")
        return None

if __name__ == "__main__":
    print("Creating test data for role-based filtering tests...")
    
    # Login as admin to create product
    admin_token, admin_user = login_user("admin", "admin123")
    if not admin_token:
        print("❌ Cannot login as admin")
        exit(1)
    
    # Create a test product (admin only)
    product = create_product(admin_token)
    if not product:
        print("❌ Cannot create product")
        exit(1)
    
    # Login as testuser
    testuser_token, testuser_user = login_user("testuser", "test123")
    if not testuser_token:
        print("❌ Cannot login as testuser")
        exit(1)
    
    print(f"\nCreating data for testuser (ID: {testuser_user['id']})...")
    
    # Create customer for testuser
    customer = create_customer(testuser_token, "TESTUSER")
    if not customer:
        print("❌ Cannot create customer")
        exit(1)
    
    # Create visit for testuser
    visit = create_visit(testuser_token, customer["id"], testuser_user["id"])
    
    # Create sale for testuser
    sale = create_sale(testuser_token, customer["id"], product["id"])
    
    # Create collection for testuser
    collection = create_collection(testuser_token, customer["id"])
    
    print("\n✅ Test data creation completed!")
    print("Now testuser should have:")
    print("- 1 customer")
    print("- 1 visit")
    print("- 1 sale (475.0)")
    print("- 1 collection (200.0)")