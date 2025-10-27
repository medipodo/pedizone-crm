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
    
    def test_dashboard_stats(self):
        """Test 3: Dashboard Stats Endpoint - GET /api/dashboard/stats"""
        self.log("=== Testing Dashboard Stats Endpoint ===")
        
        response = self.make_request("GET", "/dashboard/stats")
        
        if not response:
            self.log("Dashboard stats request failed - no response", "ERROR")
            return False
            
        if response.status_code == 200:
            data = response.json()
            
            # Check for expected dashboard fields
            expected_fields = ["total_sales", "total_visits"]
            missing_fields = [field for field in expected_fields if field not in data]
            
            if missing_fields:
                self.log(f"❌ Dashboard stats missing fields: {missing_fields}", "ERROR")
                return False
            
            self.log("✅ Dashboard stats endpoint working")
            self.log(f"   Total Sales: {data.get('total_sales', 0)}")
            self.log(f"   Total Visits: {data.get('total_visits', 0)}")
            
            # Compare with alias endpoint data
            if "dashboard_alias" in self.test_data:
                alias_data = self.test_data["dashboard_alias"]
                if data == alias_data:
                    self.log("✅ Dashboard alias and stats return identical data")
                else:
                    self.log("❌ Dashboard alias and stats return different data", "ERROR")
                    self.log(f"   Alias: {alias_data}")
                    self.log(f"   Stats: {data}")
                    return False
            
            return True
        else:
            self.log(f"❌ Dashboard stats failed with status {response.status_code}: {response.text}", "ERROR")
            return False
    
    def test_visits_api(self):
        """Test 4: Visits API - GET /api/visits"""
        self.log("=== Testing Visits API ===")
        
        response = self.make_request("GET", "/visits")
        
        if not response:
            self.log("Visits API request failed - no response", "ERROR")
            return False
            
        if response.status_code == 200:
            data = response.json()
            
            if not isinstance(data, list):
                self.log("❌ Visits API should return a list", "ERROR")
                return False
            
            self.log(f"✅ Visits API working - returned {len(data)} visits")
            
            # Check visit data structure if visits exist
            if len(data) > 0:
                visit = data[0]
                
                # Check for location object
                if "location" not in visit:
                    self.log("❌ Visit missing location field", "ERROR")
                    return False
                
                location = visit.get("location")
                if location and isinstance(location, dict):
                    if "latitude" in location and "longitude" in location:
                        self.log("✅ Visit has location with latitude/longitude")
                        self.log(f"   Sample location: {location}")
                    else:
                        self.log("❌ Location object missing latitude/longitude", "ERROR")
                        return False
                
                # Check visit_date format
                if "visit_date" not in visit:
                    self.log("❌ Visit missing visit_date field", "ERROR")
                    return False
                
                visit_date = visit.get("visit_date")
                if visit_date:
                    self.log(f"✅ Visit has visit_date: {visit_date}")
                    # Check if it's in ISO format (basic validation)
                    if "T" in visit_date or "-" in visit_date:
                        self.log("✅ Visit date appears to be in ISO format")
                    else:
                        self.log("❌ Visit date not in expected ISO format", "ERROR")
                        return False
                
                # Check status field
                if "status" not in visit:
                    self.log("❌ Visit missing status field", "ERROR")
                    return False
                
                status = visit.get("status")
                expected_statuses = ["gorusuldu", "anlasildi", "randevu_alindi"]
                if status in expected_statuses:
                    self.log(f"✅ Visit has valid status: {status}")
                else:
                    self.log(f"❌ Visit has unexpected status: {status}", "ERROR")
                    return False
                
            else:
                self.log("ℹ️ No visits found in database - structure validation skipped")
            
            return True
        else:
            self.log(f"❌ Visits API failed with status {response.status_code}: {response.text}", "ERROR")
            return False
    
    def validate_dashboard_data_consistency(self):
        """Test 5: Validate Dashboard Data Consistency"""
        self.log("=== Validating Dashboard Data Consistency ===")
        
        if "dashboard_alias" not in self.test_data:
            self.log("❌ Cannot validate consistency - dashboard alias data not available", "ERROR")
            return False
        
        dashboard_data = self.test_data["dashboard_alias"]
        
        # Check that all expected fields are present and have reasonable values
        required_fields = ["total_sales", "total_visits"]
        
        for field in required_fields:
            if field not in dashboard_data:
                self.log(f"❌ Dashboard missing required field: {field}", "ERROR")
                return False
            
            value = dashboard_data[field]
            if not isinstance(value, (int, float)) or value < 0:
                self.log(f"❌ Dashboard field {field} has invalid value: {value}", "ERROR")
                return False
        
        self.log("✅ Dashboard data consistency validated")
        self.log(f"   All required fields present with valid values")
        
        # Check for additional fields that might be role-specific
        additional_fields = [k for k in dashboard_data.keys() if k not in required_fields]
        if additional_fields:
            self.log(f"   Additional fields found: {additional_fields}")
        
        return True
    
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