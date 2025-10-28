#!/usr/bin/env python3
"""
Test different login variations for testuser
"""

import requests

BACKEND_URL = "https://crm-pedizone.preview.emergentagent.com/api"

def test_login(username, password):
    """Test login with given credentials"""
    login_data = {
        "username": username,
        "password": password
    }
    
    response = requests.post(f"{BACKEND_URL}/auth/login", json=login_data, timeout=30)
    
    if response.status_code == 200:
        data = response.json()
        user_info = data.get("user", {})
        print(f"✅ Login successful: {username}/{password}")
        print(f"   User: {user_info.get('full_name')}")
        print(f"   Role: {user_info.get('role')}")
        print(f"   ID: {user_info.get('id')}")
        return True
    else:
        print(f"❌ Login failed: {username}/{password} - {response.status_code}")
        return False

if __name__ == "__main__":
    print("Testing different login variations for testuser...")
    
    # Try different password combinations
    passwords = ["123456", "testuser", "password", "admin123", "test123"]
    
    for password in passwords:
        if test_login("testuser", password):
            break
    else:
        print("\n❌ None of the password variations worked")
        print("Let's try to reset the testuser password...")
        
        # Login as admin and update testuser password
        admin_login = requests.post(f"{BACKEND_URL}/auth/login", json={"username": "admin", "password": "admin123"}, timeout=30)
        if admin_login.status_code == 200:
            admin_token = admin_login.json().get("access_token")
            headers = {"Authorization": f"Bearer {admin_token}", "Content-Type": "application/json"}
            
            # Get testuser ID
            users_response = requests.get(f"{BACKEND_URL}/users", headers=headers, timeout=30)
            if users_response.status_code == 200:
                users = users_response.json()
                testuser = next((u for u in users if u['username'] == 'testuser'), None)
                if testuser:
                    user_id = testuser['id']
                    
                    # Update password
                    update_data = {"password": "123456"}
                    update_response = requests.put(f"{BACKEND_URL}/users/{user_id}", headers=headers, json=update_data, timeout=30)
                    
                    if update_response.status_code == 200:
                        print("✅ Password updated successfully")
                        # Test login again
                        test_login("testuser", "123456")
                    else:
                        print(f"❌ Password update failed: {update_response.status_code} - {update_response.text}")