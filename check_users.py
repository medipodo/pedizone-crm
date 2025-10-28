#!/usr/bin/env python3
"""
Check existing users and create testuser if needed
"""

import requests
import json

BACKEND_URL = "https://crm-pedizone.preview.emergentagent.com/api"

def login_admin():
    """Login as admin to check users"""
    login_data = {
        "username": "admin",
        "password": "admin123"
    }
    
    response = requests.post(f"{BACKEND_URL}/auth/login", json=login_data, timeout=30)
    
    if response.status_code == 200:
        data = response.json()
        return data.get("access_token")
    else:
        print(f"Admin login failed: {response.status_code} - {response.text}")
        return None

def get_users(token):
    """Get list of users"""
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    response = requests.get(f"{BACKEND_URL}/users", headers=headers, timeout=30)
    
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Get users failed: {response.status_code} - {response.text}")
        return []

def create_testuser(token):
    """Create testuser salesperson"""
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # First get regions to find a region_id
    regions_response = requests.get(f"{BACKEND_URL}/regions", headers=headers, timeout=30)
    regions = regions_response.json() if regions_response.status_code == 200 else []
    
    region_id = regions[0]["id"] if regions else None
    
    user_data = {
        "username": "testuser",
        "email": "testuser@pedizone.com",
        "full_name": "Test Plasiyer",
        "password": "123456",
        "role": "salesperson",
        "region_id": region_id
    }
    
    response = requests.post(f"{BACKEND_URL}/users", headers=headers, json=user_data, timeout=30)
    
    if response.status_code == 200:
        print("✅ testuser created successfully")
        return response.json()
    else:
        print(f"Create testuser failed: {response.status_code} - {response.text}")
        return None

if __name__ == "__main__":
    print("Checking users and creating testuser if needed...")
    
    # Login as admin
    token = login_admin()
    if not token:
        print("❌ Cannot login as admin")
        exit(1)
    
    # Get existing users
    users = get_users(token)
    print(f"Found {len(users)} users:")
    for user in users:
        print(f"  - {user['username']} ({user['role']}) - {user['full_name']}")
    
    # Check if testuser exists
    testuser_exists = any(user['username'] == 'testuser' for user in users)
    
    if not testuser_exists:
        print("\ntestuser not found, creating...")
        create_testuser(token)
    else:
        print("\n✅ testuser already exists")