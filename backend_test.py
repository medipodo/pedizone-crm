#!/usr/bin/env python3
"""
PediZone CRM Backend API Testing
Focus on Dashboard endpoints and Visits API as per review request
"""

import requests
import json
import sys
from datetime import datetime, timezone

# Backend URL as specified in review request
BACKEND_URL = "https://crm-pedizone.preview.emergentagent.com/api"

class PediZoneAPITester:
    def __init__(self):
        self.base_url = BACKEND_URL
        self.token = None
        self.headers = {"Content-Type": "application/json"}
        self.test_data = {}
        
    def log(self, message, level="INFO"):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] {level}: {message}")
        
    def make_request(self, method, endpoint, data=None, auth_required=True):
        """Make HTTP request with proper headers"""
        url = f"{self.base_url}{endpoint}"
        headers = self.headers.copy()
        
        if auth_required and self.token:
            headers["Authorization"] = f"Bearer {self.token}"
            
        try:
            if method == "GET":
                response = requests.get(url, headers=headers, timeout=30)
            elif method == "POST":
                response = requests.post(url, headers=headers, json=data, timeout=30)
            elif method == "PUT":
                response = requests.put(url, headers=headers, json=data, timeout=30)
            elif method == "DELETE":
                response = requests.delete(url, headers=headers, timeout=30)
            else:
                raise ValueError(f"Unsupported method: {method}")
                
            self.log(f"{method} {endpoint} -> {response.status_code}")
            
            if response.status_code >= 400:
                self.log(f"Error response: {response.text}", "ERROR")
                
            return response
            
        except requests.exceptions.RequestException as e:
            self.log(f"Request failed: {str(e)}", "ERROR")
            return None
    
    def test_login(self):
        """Test 1: Login & Auth - POST /api/auth/login"""
        self.log("=== Testing Login & Auth ===")
        
        login_data = {
            "username": "admin",
            "password": "admin123"
        }
        
        response = self.make_request("POST", "/auth/login", login_data, auth_required=False)
        
        if not response:
            self.log("Login request failed - no response", "ERROR")
            return False
            
        if response.status_code == 200:
            data = response.json()
            self.token = data.get("access_token")
            user_info = data.get("user")
            
            if self.token and user_info:
                self.log("✅ Login successful - JWT token obtained")
                self.log(f"   User: {user_info.get('full_name', 'Unknown')}")
                self.log(f"   Role: {user_info.get('role', 'Unknown')}")
                return True
            else:
                self.log("❌ Login response missing token or user info", "ERROR")
                return False
        else:
            self.log(f"❌ Login failed with status {response.status_code}: {response.text}", "ERROR")
            return False
    
    def test_dashboard_alias(self):
        """Test 2: Dashboard Alias Endpoint - GET /api/dashboard"""
        self.log("=== Testing Dashboard Alias Endpoint ===")
        
        response = self.make_request("GET", "/dashboard")
        
        if not response:
            self.log("Dashboard alias request failed - no response", "ERROR")
            return False
            
        if response.status_code == 200:
            data = response.json()
            
            # Check for expected dashboard fields
            expected_fields = ["total_sales", "total_visits"]
            missing_fields = [field for field in expected_fields if field not in data]
            
            if missing_fields:
                self.log(f"❌ Dashboard alias missing fields: {missing_fields}", "ERROR")
                return False
            
            self.log("✅ Dashboard alias endpoint working")
            self.log(f"   Total Sales: {data.get('total_sales', 0)}")
            self.log(f"   Total Visits: {data.get('total_visits', 0)}")
            
            # Store data for comparison with stats endpoint
            self.test_data["dashboard_alias"] = data
            return True
        else:
            self.log(f"❌ Dashboard alias failed with status {response.status_code}: {response.text}", "ERROR")
            return False
    
    def test_customer_creation(self):
        """Test 3: Customer Creation API"""
        self.log("=== Testing Customer Creation ===")
        
        customer_data = {
            "name": "Test Customer",
            "address": "Test Address",
            "phone": "1234567890",
            "email": "test@test.com",
            "region_id": "test-region-id",
            "tax_number": "1234567890",
            "notes": "Test notes"
        }
        
        response = self.make_request("POST", "/customers", customer_data)
        
        if not response:
            self.log("Customer creation request failed - no response", "ERROR")
            return False
            
        if response.status_code == 200:
            data = response.json()
            customer_id = data.get("id")
            if customer_id:
                self.test_data["customer_id"] = customer_id
                self.log(f"✅ Customer created successfully - ID: {customer_id}")
                return True
            else:
                self.log("❌ Customer creation response missing ID", "ERROR")
                return False
        else:
            self.log(f"❌ Customer creation failed with status {response.status_code}: {response.text}", "ERROR")
            return False
    
    def test_visit_creation(self):
        """Test 4: Visit Creation API"""
        self.log("=== Testing Visit Creation ===")
        
        if "customer_id" not in self.test_data:
            self.log("❌ Cannot test visit creation - no customer_id available", "ERROR")
            return False
        
        visit_data = {
            "customer_id": self.test_data["customer_id"],
            "salesperson_id": "auto-set-from-token",  # This should be overridden by backend
            "visit_date": "2025-10-23T10:00:00Z",
            "notes": "Test visit",
            "location": {"latitude": 41.0082, "longitude": 28.9784},
            "status": "gorusuldu"
        }
        
        response = self.make_request("POST", "/visits", visit_data)
        
        if not response:
            self.log("Visit creation request failed - no response", "ERROR")
            return False
            
        if response.status_code == 200:
            data = response.json()
            visit_id = data.get("id")
            if visit_id:
                self.test_data["visit_id"] = visit_id
                self.log(f"✅ Visit created successfully - ID: {visit_id}")
                return True
            else:
                self.log("❌ Visit creation response missing ID", "ERROR")
                return False
        else:
            self.log(f"❌ Visit creation failed with status {response.status_code}: {response.text}", "ERROR")
            return False
    
    def test_sales_creation(self):
        """Test 5: Sales Creation API"""
        self.log("=== Testing Sales Creation ===")
        
        if "customer_id" not in self.test_data or "product_id" not in self.test_data:
            self.log("❌ Cannot test sales creation - missing customer_id or product_id", "ERROR")
            return False
        
        sales_data = {
            "customer_id": self.test_data["customer_id"],
            "sale_date": "2025-10-23",
            "items": [
                {
                    "product_id": self.test_data["product_id"],
                    "product_name": self.test_data.get("product_name", "Test Product"),
                    "quantity": 5,
                    "unit_price": 2500,
                    "total": 12500
                }
            ],
            "total_amount": 12500,
            "notes": "Test sale"
        }
        
        response = self.make_request("POST", "/sales", sales_data)
        
        if not response:
            self.log("Sales creation request failed - no response", "ERROR")
            return False
            
        if response.status_code == 200:
            data = response.json()
            sale_id = data.get("id")
            if sale_id:
                self.test_data["sale_id"] = sale_id
                self.log(f"✅ Sale created successfully - ID: {sale_id}")
                return True
            else:
                self.log("❌ Sales creation response missing ID", "ERROR")
                return False
        else:
            self.log(f"❌ Sales creation failed with status {response.status_code}: {response.text}", "ERROR")
            return False
    
    def run_all_tests(self):
        """Run all tests in sequence"""
        self.log(f"Starting PediZone CRM API Tests")
        self.log(f"Backend URL: {self.base_url}")
        
        results = {
            "login": False,
            "product_creation": False,
            "customer_creation": False,
            "visit_creation": False,
            "sales_creation": False
        }
        
        # Test 1: Login
        results["login"] = self.test_login()
        if not results["login"]:
            self.log("❌ Cannot continue without authentication", "ERROR")
            return results
        
        # Test 2: Product Creation
        results["product_creation"] = self.test_product_creation()
        
        # Test 3: Customer Creation
        results["customer_creation"] = self.test_customer_creation()
        
        # Test 4: Visit Creation (depends on customer)
        results["visit_creation"] = self.test_visit_creation()
        
        # Test 5: Sales Creation (depends on product and customer)
        results["sales_creation"] = self.test_sales_creation()
        
        # Summary
        self.log("=== TEST SUMMARY ===")
        passed = sum(1 for result in results.values() if result)
        total = len(results)
        
        for test_name, result in results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            self.log(f"{test_name.replace('_', ' ').title()}: {status}")
        
        self.log(f"Overall: {passed}/{total} tests passed")
        
        return results

if __name__ == "__main__":
    tester = PediZoneAPITester()
    results = tester.run_all_tests()
    
    # Exit with error code if any test failed
    if not all(results.values()):
        sys.exit(1)
    else:
        print("\n🎉 All tests passed!")
        sys.exit(0)