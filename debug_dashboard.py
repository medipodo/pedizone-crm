#!/usr/bin/env python3
"""
Debug dashboard responses for different roles
"""

import requests
import json

BACKEND_URL = "https://crm-pedizone.preview.emergentagent.com/api"

def login_and_get_dashboard(username, password):
    """Login and get dashboard data"""
    # Login
    login_data = {"username": username, "password": password}
    login_response = requests.post(f"{BACKEND_URL}/auth/login", json=login_data, timeout=30)
    
    if login_response.status_code != 200:
        print(f"❌ Login failed for {username}")
        return None
    
    token = login_response.json().get("access_token")
    user_info = login_response.json().get("user")
    
    # Get dashboard
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    dashboard_response = requests.get(f"{BACKEND_URL}/dashboard/stats", headers=headers, timeout=30)
    
    if dashboard_response.status_code != 200:
        print(f"❌ Dashboard failed for {username}")
        return None
    
    dashboard_data = dashboard_response.json()
    
    return {
        "user": user_info,
        "dashboard": dashboard_data
    }

if __name__ == "__main__":
    print("Debugging Dashboard Responses")
    print("============================")
    
    # Test admin dashboard
    print("\n1. Admin Dashboard:")
    admin_result = login_and_get_dashboard("admin", "admin123")
    if admin_result:
        print(f"   User: {admin_result['user']['full_name']} ({admin_result['user']['role']})")
        print(f"   Dashboard fields: {list(admin_result['dashboard'].keys())}")
        print(f"   Dashboard data: {json.dumps(admin_result['dashboard'], indent=2)}")
    
    # Test testuser dashboard
    print("\n2. Testuser Dashboard:")
    testuser_result = login_and_get_dashboard("testuser", "test123")
    if testuser_result:
        print(f"   User: {testuser_result['user']['full_name']} ({testuser_result['user']['role']})")
        print(f"   Dashboard fields: {list(testuser_result['dashboard'].keys())}")
        print(f"   Dashboard data: {json.dumps(testuser_result['dashboard'], indent=2)}")
    
    # Compare fields
    if admin_result and testuser_result:
        admin_fields = set(admin_result['dashboard'].keys())
        testuser_fields = set(testuser_result['dashboard'].keys())
        
        print(f"\n3. Field Comparison:")
        print(f"   Admin only fields: {admin_fields - testuser_fields}")
        print(f"   Testuser only fields: {testuser_fields - admin_fields}")
        print(f"   Common fields: {admin_fields & testuser_fields}")