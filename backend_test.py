#!/usr/bin/env python3
"""
PediZone CRM Backend API Security Testing
Comprehensive test suite for authentication, CRUD operations, security features, and data protection.
"""

import requests
import json
import time
from typing import Dict, Optional, Any
import uuid

# Base configuration
BASE_URL = "https://clinic-manager-227.preview.emergentagent.com/api"
ADMIN_CREDENTIALS = {"username": "admin", "password": "Admin123!"}

class SecurityTester:
    def __init__(self):
        self.base_url = BASE_URL
        self.session = requests.Session()
        self.admin_token = None
        self.test_results = []
        print(f"🔧 Initialized Security Tester with BASE_URL: {self.base_url}")
    
    def log_test(self, test_name: str, success: bool, details: str = "", status_code: int = None):
        """Log test result with details"""
        status = "✅ PASS" if success else "❌ FAIL"
        result = {
            "test": test_name,
            "success": success,
            "details": details,
            "status_code": status_code
        }
        self.test_results.append(result)
        
        status_info = f" (Status: {status_code})" if status_code else ""
        print(f"{status} {test_name}{status_info}")
        if details:
            print(f"    {details}")
        print()
    
    def setup_admin_user(self):
        """Setup admin user for testing"""
        print("🔧 Setting up admin user...")
        try:
            # Run the create_admin script
            import subprocess
            result = subprocess.run([
                "python3", "/app/backend/create_admin.py", "create", 
                ADMIN_CREDENTIALS["username"], "admin@pedizone.com", ADMIN_CREDENTIALS["password"]
            ], capture_output=True, text=True, cwd="/app/backend")
            
            if "başarıyla oluşturuldu" in result.stdout or "zaten mevcut" in result.stdout:
                print("✅ Admin user setup completed")
                return True
            else:
                print(f"⚠️ Admin setup output: {result.stdout}")
                return True  # Continue even if admin already exists
        except Exception as e:
            print(f"⚠️ Admin setup error: {e}")
            return True  # Continue with testing
    
    def test_health_check(self):
        """Test health check endpoint"""
        try:
            response = self.session.get(f"{self.base_url}/health")
            
            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "healthy":
                    self.log_test("Health Check", True, "System is healthy", response.status_code)
                else:
                    self.log_test("Health Check", False, f"Unhealthy status: {data}", response.status_code)
            else:
                self.log_test("Health Check", False, f"Unexpected status code", response.status_code)
                
        except Exception as e:
            self.log_test("Health Check", False, f"Request failed: {e}")
    
    def test_auth_login_valid(self):
        """Test login with valid credentials"""
        try:
            response = self.session.post(
                f"{self.base_url}/auth/login",
                json=ADMIN_CREDENTIALS
            )
            
            if response.status_code == 200:
                data = response.json()
                if "access_token" in data and "user" in data:
                    self.admin_token = data["access_token"]
                    # Verify password_hash is NOT in response
                    user_data = data["user"]
                    if "password_hash" in user_data:
                        self.log_test("Login Valid - Data Protection", False, 
                                    "SECURITY ISSUE: password_hash exposed in response", response.status_code)
                    else:
                        self.log_test("Login Valid", True, 
                                    f"Token received, user role: {user_data.get('role')}", response.status_code)
                else:
                    self.log_test("Login Valid", False, "Missing token or user data in response", response.status_code)
            else:
                self.log_test("Login Valid", False, f"Login failed: {response.text}", response.status_code)
                
        except Exception as e:
            self.log_test("Login Valid", False, f"Request failed: {e}")
    
    def test_auth_login_invalid_password(self):
        """Test login with invalid password"""
        try:
            response = self.session.post(
                f"{self.base_url}/auth/login",
                json={"username": "admin", "password": "wrongpassword"}
            )
            
            if response.status_code == 401:
                self.log_test("Login Invalid Password", True, "Correctly rejected invalid password", response.status_code)
            else:
                self.log_test("Login Invalid Password", False, 
                            f"Should return 401, got {response.status_code}", response.status_code)
                
        except Exception as e:
            self.log_test("Login Invalid Password", False, f"Request failed: {e}")
    
    def test_auth_login_nonexistent_user(self):
        """Test login with non-existent user"""
        try:
            response = self.session.post(
                f"{self.base_url}/auth/login",
                json={"username": "nonexistent", "password": "somepassword"}
            )
            
            if response.status_code == 401:
                self.log_test("Login Non-existent User", True, "Correctly rejected non-existent user", response.status_code)
            else:
                self.log_test("Login Non-existent User", False, 
                            f"Should return 401, got {response.status_code}", response.status_code)
                
        except Exception as e:
            self.log_test("Login Non-existent User", False, f"Request failed: {e}")
    
    def test_rate_limiting(self):
        """Test rate limiting on login endpoint"""
        print("🔄 Testing rate limiting (may take a moment)...")
        
        # Make multiple failed login attempts to trigger rate limiting
        rate_limited = False
        for i in range(10):  # Try up to 10 attempts
            try:
                # Use fresh session for each attempt to simulate different connections
                session = requests.Session()
                response = session.post(
                    f"{self.base_url}/auth/login",
                    json={"username": "ratelimituser", "password": "wrongpass"}
                )
                print(f"    Attempt {i+1}: Status {response.status_code}")
                
                if response.status_code == 429:
                    self.log_test("Rate Limiting", True, f"Correctly blocked after {i+1} attempts (5 allowed + 1 blocked)", response.status_code)
                    rate_limited = True
                    break
                    
            except Exception as e:
                self.log_test("Rate Limiting Setup", False, f"Failed attempt {i+1}: {e}")
                return
        
        if not rate_limited:
            self.log_test("Rate Limiting", False, "Rate limiting not triggered after 10 attempts")
    
    def test_auth_me_with_token(self):
        """Test /auth/me with valid token"""
        if not self.admin_token:
            self.log_test("Auth Me With Token", False, "No admin token available")
            return
        
        try:
            headers = {"Authorization": f"Bearer {self.admin_token}"}
            response = self.session.get(f"{self.base_url}/auth/me", headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                if "password_hash" in data:
                    self.log_test("Auth Me With Token - Data Protection", False, 
                                "SECURITY ISSUE: password_hash exposed in user info", response.status_code)
                else:
                    self.log_test("Auth Me With Token", True, 
                                f"User info retrieved, role: {data.get('role')}", response.status_code)
            else:
                self.log_test("Auth Me With Token", False, f"Failed: {response.text}", response.status_code)
                
        except Exception as e:
            self.log_test("Auth Me With Token", False, f"Request failed: {e}")
    
    def test_auth_me_without_token(self):
        """Test /auth/me without token"""
        try:
            response = self.session.get(f"{self.base_url}/auth/me")
            
            if response.status_code == 401 or response.status_code == 403:
                self.log_test("Auth Me Without Token", True, "Correctly rejected request without token", response.status_code)
            else:
                self.log_test("Auth Me Without Token", False, 
                            f"Should return 401/403, got {response.status_code}", response.status_code)
                
        except Exception as e:
            self.log_test("Auth Me Without Token", False, f"Request failed: {e}")
    
    def test_auth_me_invalid_token(self):
        """Test /auth/me with invalid token"""
        try:
            headers = {"Authorization": "Bearer invalid_token_12345"}
            response = self.session.get(f"{self.base_url}/auth/me", headers=headers)
            
            if response.status_code == 401:
                self.log_test("Auth Me Invalid Token", True, "Correctly rejected invalid token", response.status_code)
            else:
                self.log_test("Auth Me Invalid Token", False, 
                            f"Should return 401, got {response.status_code}", response.status_code)
                
        except Exception as e:
            self.log_test("Auth Me Invalid Token", False, f"Request failed: {e}")
    
    def test_users_list(self):
        """Test GET /users with admin token"""
        if not self.admin_token:
            self.log_test("Users List", False, "No admin token available")
            return
        
        try:
            headers = {"Authorization": f"Bearer {self.admin_token}"}
            response = self.session.get(f"{self.base_url}/users", headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                # Check for password_hash exposure
                password_hash_found = False
                for user in data:
                    if "password_hash" in user:
                        password_hash_found = True
                        break
                
                if password_hash_found:
                    self.log_test("Users List - Data Protection", False, 
                                "SECURITY ISSUE: password_hash exposed in user list", response.status_code)
                else:
                    self.log_test("Users List", True, f"Retrieved {len(data)} users safely", response.status_code)
            else:
                self.log_test("Users List", False, f"Failed: {response.text}", response.status_code)
                
        except Exception as e:
            self.log_test("Users List", False, f"Request failed: {e}")
    
    def test_user_create_valid(self):
        """Test POST /users with valid data"""
        if not self.admin_token:
            self.log_test("User Create Valid", False, "No admin token available")
            return
        
        try:
            headers = {"Authorization": f"Bearer {self.admin_token}"}
            test_user = {
                "username": f"testuser_{uuid.uuid4().hex[:8]}",
                "email": f"test_{uuid.uuid4().hex[:8]}@example.com",
                "full_name": "Test User",
                "password": "TestPass123!",
                "role": "salesperson",
                "region_id": None
            }
            
            response = self.session.post(f"{self.base_url}/users", headers=headers, json=test_user)
            
            if response.status_code == 200:
                data = response.json()
                if "password_hash" in data:
                    self.log_test("User Create Valid - Data Protection", False, 
                                "SECURITY ISSUE: password_hash exposed in creation response", response.status_code)
                else:
                    self.log_test("User Create Valid", True, 
                                f"User created successfully: {test_user['username']}", response.status_code)
            else:
                self.log_test("User Create Valid", False, f"Failed: {response.text}", response.status_code)
                
        except Exception as e:
            self.log_test("User Create Valid", False, f"Request failed: {e}")
    
    def test_user_create_invalid_email(self):
        """Test POST /users with invalid email"""
        if not self.admin_token:
            self.log_test("User Create Invalid Email", False, "No admin token available")
            return
        
        try:
            headers = {"Authorization": f"Bearer {self.admin_token}"}
            test_user = {
                "username": f"testuser_{uuid.uuid4().hex[:8]}",
                "email": "invalid-email",
                "full_name": "Test User",
                "password": "TestPass123!",
                "role": "salesperson"
            }
            
            response = self.session.post(f"{self.base_url}/users", headers=headers, json=test_user)
            
            if response.status_code == 422:  # Validation error
                self.log_test("User Create Invalid Email", True, "Correctly rejected invalid email", response.status_code)
            else:
                self.log_test("User Create Invalid Email", False, 
                            f"Should return 422, got {response.status_code}", response.status_code)
                
        except Exception as e:
            self.log_test("User Create Invalid Email", False, f"Request failed: {e}")
    
    def test_user_create_short_password(self):
        """Test POST /users with too short password"""
        if not self.admin_token:
            self.log_test("User Create Short Password", False, "No admin token available")
            return
        
        try:
            headers = {"Authorization": f"Bearer {self.admin_token}"}
            test_user = {
                "username": f"testuser_{uuid.uuid4().hex[:8]}",
                "email": f"test_{uuid.uuid4().hex[:8]}@example.com",
                "full_name": "Test User",
                "password": "123",  # Too short
                "role": "salesperson"
            }
            
            response = self.session.post(f"{self.base_url}/users", headers=headers, json=test_user)
            
            if response.status_code == 422:  # Validation error
                self.log_test("User Create Short Password", True, "Correctly rejected short password", response.status_code)
            else:
                self.log_test("User Create Short Password", False, 
                            f"Should return 422, got {response.status_code}", response.status_code)
                
        except Exception as e:
            self.log_test("User Create Short Password", False, f"Request failed: {e}")
    
    def test_user_create_duplicate_username(self):
        """Test POST /users with existing username"""
        if not self.admin_token:
            self.log_test("User Create Duplicate Username", False, "No admin token available")
            return
        
        try:
            headers = {"Authorization": f"Bearer {self.admin_token}"}
            test_user = {
                "username": "admin",  # Should already exist
                "email": f"duplicate_{uuid.uuid4().hex[:8]}@example.com",
                "full_name": "Duplicate Test",
                "password": "TestPass123!",
                "role": "salesperson"
            }
            
            response = self.session.post(f"{self.base_url}/users", headers=headers, json=test_user)
            
            if response.status_code == 400:
                self.log_test("User Create Duplicate Username", True, "Correctly rejected duplicate username", response.status_code)
            else:
                self.log_test("User Create Duplicate Username", False, 
                            f"Should return 400, got {response.status_code}", response.status_code)
                
        except Exception as e:
            self.log_test("User Create Duplicate Username", False, f"Request failed: {e}")
    
    def test_regions_crud(self):
        """Test Region CRUD operations"""
        if not self.admin_token:
            self.log_test("Regions CRUD", False, "No admin token available")
            return
        
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        region_id = None
        
        # Test GET /regions
        try:
            response = self.session.get(f"{self.base_url}/regions", headers=headers)
            if response.status_code == 200:
                self.log_test("Regions GET", True, f"Retrieved regions list", response.status_code)
            else:
                self.log_test("Regions GET", False, f"Failed: {response.text}", response.status_code)
        except Exception as e:
            self.log_test("Regions GET", False, f"Request failed: {e}")
        
        # Test POST /regions
        try:
            test_region = {
                "name": f"Test Region {uuid.uuid4().hex[:8]}",
                "description": "Test region for security testing"
            }
            
            response = self.session.post(f"{self.base_url}/regions", headers=headers, json=test_region)
            if response.status_code == 200:
                data = response.json()
                region_id = data.get("id")
                self.log_test("Regions POST", True, f"Created region: {test_region['name']}", response.status_code)
            else:
                self.log_test("Regions POST", False, f"Failed: {response.text}", response.status_code)
        except Exception as e:
            self.log_test("Regions POST", False, f"Request failed: {e}")
        
        # Test PUT /regions/{id} if we have a region_id
        if region_id:
            try:
                update_data = {"description": "Updated description for testing"}
                response = self.session.put(f"{self.base_url}/regions/{region_id}", headers=headers, json=update_data)
                if response.status_code == 200:
                    self.log_test("Regions PUT", True, f"Updated region {region_id}", response.status_code)
                else:
                    self.log_test("Regions PUT", False, f"Failed: {response.text}", response.status_code)
            except Exception as e:
                self.log_test("Regions PUT", False, f"Request failed: {e}")
            
            # Test DELETE /regions/{id}
            try:
                response = self.session.delete(f"{self.base_url}/regions/{region_id}", headers=headers)
                if response.status_code == 200:
                    self.log_test("Regions DELETE", True, f"Deleted region {region_id}", response.status_code)
                else:
                    self.log_test("Regions DELETE", False, f"Failed: {response.text}", response.status_code)
            except Exception as e:
                self.log_test("Regions DELETE", False, f"Request failed: {e}")
    
    def test_expired_token(self):
        """Test with expired token (simulated by using invalid token format)"""
        try:
            # Create a token that looks expired
            expired_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyLCJleHAiOjE1MTYyMzkwMjJ9.invalid"
            headers = {"Authorization": f"Bearer {expired_token}"}
            response = self.session.get(f"{self.base_url}/auth/me", headers=headers)
            
            if response.status_code == 401:
                self.log_test("Expired Token", True, "Correctly rejected expired/invalid token", response.status_code)
            else:
                self.log_test("Expired Token", False, 
                            f"Should return 401, got {response.status_code}", response.status_code)
                
        except Exception as e:
            self.log_test("Expired Token", False, f"Request failed: {e}")
    
    def run_all_tests(self):
        """Run all security tests"""
        print("🚀 Starting PediZone CRM Backend Security Testing...")
        print("=" * 60)
        
        # Setup
        self.setup_admin_user()
        time.sleep(1)
        
        # Health check first
        self.test_health_check()
        
        # Authentication tests
        self.test_auth_login_valid()
        self.test_auth_login_invalid_password()
        self.test_auth_login_nonexistent_user()
        
        # Token validation tests
        self.test_auth_me_with_token()
        self.test_auth_me_without_token()
        self.test_auth_me_invalid_token()
        self.test_expired_token()
        
        # User CRUD tests
        self.test_users_list()
        self.test_user_create_valid()
        self.test_user_create_invalid_email()
        self.test_user_create_short_password()
        self.test_user_create_duplicate_username()
        
        # Region CRUD tests
        self.test_regions_crud()
        
        # Rate limiting test (last as it affects subsequent requests)
        self.test_rate_limiting()
        
        # Generate summary
        self.generate_summary()
    
    def generate_summary(self):
        """Generate test summary"""
        print("\n" + "=" * 60)
        print("🔍 SECURITY TEST SUMMARY")
        print("=" * 60)
        
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if r["success"]])
        failed_tests = total_tests - passed_tests
        
        print(f"📊 Total Tests: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {failed_tests}")
        print(f"📈 Success Rate: {(passed_tests/total_tests*100):.1f}%")
        
        if failed_tests > 0:
            print("\n🔴 FAILED TESTS:")
            print("-" * 40)
            for result in self.test_results:
                if not result["success"]:
                    print(f"❌ {result['test']}")
                    if result["details"]:
                        print(f"   {result['details']}")
                    print()
        
        # Security-specific summary
        security_issues = []
        for result in self.test_results:
            if "SECURITY ISSUE" in result["details"]:
                security_issues.append(result)
        
        if security_issues:
            print("\n🚨 CRITICAL SECURITY ISSUES:")
            print("-" * 40)
            for issue in security_issues:
                print(f"🚨 {issue['test']}: {issue['details']}")
        else:
            print("\n🛡️ NO CRITICAL SECURITY ISSUES DETECTED")
        
        print("\n" + "=" * 60)


if __name__ == "__main__":
    tester = SecurityTester()
    tester.run_all_tests()