#!/usr/bin/env python3
"""
Comprehensive role-based filtering test
Verify plasiyer only sees their own data and not admin/other user data
"""

import requests
import json
from datetime import datetime, timezone

BACKEND_URL = "https://crm-pedizone.preview.emergentagent.com/api"

def login_user(username, password):
    """Login and return token and user info"""
    login_data = {"username": username, "password": password}
    response = requests.post(f"{BACKEND_URL}/auth/login", json=login_data, timeout=30)
    
    if response.status_code == 200:
        data = response.json()
        return data.get("access_token"), data.get("user")
    return None, None

def get_data_counts(token, user_role):
    """Get data counts for comparison"""
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    
    # Get dashboard stats
    dashboard_response = requests.get(f"{BACKEND_URL}/dashboard/stats", headers=headers, timeout=30)
    dashboard_data = dashboard_response.json() if dashboard_response.status_code == 200 else {}
    
    # Get actual data
    visits_response = requests.get(f"{BACKEND_URL}/visits", headers=headers, timeout=30)
    visits = visits_response.json() if visits_response.status_code == 200 else []
    
    sales_response = requests.get(f"{BACKEND_URL}/sales", headers=headers, timeout=30)
    sales = sales_response.json() if sales_response.status_code == 200 else []
    
    collections_response = requests.get(f"{BACKEND_URL}/collections", headers=headers, timeout=30)
    collections = collections_response.json() if collections_response.status_code == 200 else []
    
    return {
        "role": user_role,
        "dashboard": dashboard_data,
        "visits_count": len(visits),
        "sales_count": len(sales),
        "collections_count": len(collections),
        "visits": visits,
        "sales": sales,
        "collections": collections
    }

def verify_data_isolation(testuser_data, admin_data):
    """Verify that testuser data is isolated from admin data"""
    print("\n=== VERIFYING DATA ISOLATION ===")
    
    # Check that testuser has less data than admin (admin sees all)
    if admin_data["visits_count"] >= testuser_data["visits_count"]:
        print(f"✅ Admin sees more/equal visits ({admin_data['visits_count']}) than testuser ({testuser_data['visits_count']})")
    else:
        print(f"❌ Data isolation issue: Admin sees fewer visits than testuser")
        return False
    
    if admin_data["sales_count"] >= testuser_data["sales_count"]:
        print(f"✅ Admin sees more/equal sales ({admin_data['sales_count']}) than testuser ({testuser_data['sales_count']})")
    else:
        print(f"❌ Data isolation issue: Admin sees fewer sales than testuser")
        return False
    
    # Check that testuser data belongs only to testuser
    testuser_id = "a6ace860-5c8e-46cd-a9cc-1e0126267e26"  # Known testuser ID
    
    for visit in testuser_data["visits"]:
        if visit.get("salesperson_id") != testuser_id:
            print(f"❌ Testuser sees visit from other salesperson: {visit.get('salesperson_id')}")
            return False
    
    for sale in testuser_data["sales"]:
        if sale.get("salesperson_id") != testuser_id:
            print(f"❌ Testuser sees sale from other salesperson: {sale.get('salesperson_id')}")
            return False
    
    for collection in testuser_data["collections"]:
        if collection.get("salesperson_id") != testuser_id:
            print(f"❌ Testuser sees collection from other salesperson: {collection.get('salesperson_id')}")
            return False
    
    print("✅ All testuser data belongs to testuser only")
    
    # Check dashboard field differences
    testuser_dashboard = testuser_data["dashboard"]
    admin_dashboard = admin_data["dashboard"]
    
    # Admin should have fields that testuser doesn't
    admin_only_fields = ["total_customers", "team_size"]
    testuser_only_fields = ["commission_emoji"]
    
    for field in admin_only_fields:
        if field in testuser_dashboard:
            print(f"❌ Testuser dashboard contains admin-only field: {field}")
            return False
        if field not in admin_dashboard:
            print(f"❌ Admin dashboard missing expected field: {field}")
            return False
    
    for field in testuser_only_fields:
        if field not in testuser_dashboard:
            print(f"❌ Testuser dashboard missing expected field: {field}")
            return False
        if field in admin_dashboard:
            print(f"❌ Admin dashboard contains testuser-only field: {field}")
            return False
    
    print("✅ Dashboard fields are properly role-specific")
    
    return True

if __name__ == "__main__":
    print("Comprehensive Role-Based Filtering Test")
    print("======================================")
    
    # Login as admin
    print("\n1. Getting admin data...")
    admin_token, admin_user = login_user("admin", "admin123")
    if not admin_token:
        print("❌ Cannot login as admin")
        exit(1)
    
    admin_data = get_data_counts(admin_token, admin_user["role"])
    print(f"Admin data: {admin_data['visits_count']} visits, {admin_data['sales_count']} sales, {admin_data['collections_count']} collections")
    
    # Login as testuser
    print("\n2. Getting testuser data...")
    testuser_token, testuser_user = login_user("testuser", "test123")
    if not testuser_token:
        print("❌ Cannot login as testuser")
        exit(1)
    
    testuser_data = get_data_counts(testuser_token, testuser_user["role"])
    print(f"Testuser data: {testuser_data['visits_count']} visits, {testuser_data['sales_count']} sales, {testuser_data['collections_count']} collections")
    
    # Verify isolation
    print("\n3. Verifying data isolation...")
    isolation_ok = verify_data_isolation(testuser_data, admin_data)
    
    # Summary
    print("\n=== COMPREHENSIVE TEST SUMMARY ===")
    if isolation_ok:
        print("🎉 ROLE-BASED FILTERING COMPREHENSIVE TEST PASSED")
        print("✅ Testuser can only see their own data")
        print("✅ Admin can see all data")
        print("✅ Dashboard fields are role-specific")
        print("✅ Data isolation is working correctly")
    else:
        print("❌ ROLE-BASED FILTERING HAS ISSUES")
        print("   Data isolation is not working properly")
        exit(1)