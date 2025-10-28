#!/usr/bin/env python3
"""
PediZone CRM Backend API Testing - Role-Based Filtering for Salesperson
Testing plasiyer (salesperson) role-based filtering to verify data isolation
"""

import requests
import json
import sys
from datetime import datetime, timezone

# Backend URL as specified in review request
BACKEND_URL = "https://crm-pedizone.preview.emergentagent.com/api"

class PediZoneRoleBasedTester:
    def __init__(self):
        self.base_url = BACKEND_URL
        self.token = None
        self.headers = {"Content-Type": "application/json"}
        self.user_info = {}
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
    
    def test_plasiyer_login(self):
        """Test 1: Login as Plasiyer (Salesperson) - POST /api/auth/login"""
        self.log("=== Testing Plasiyer Login ===")
        
        login_data = {
            "username": "testuser",
            "password": "123456"
        }
        
        response = self.make_request("POST", "/auth/login", login_data, auth_required=False)
        
        if not response:
            self.log("❌ Login request failed - no response", "ERROR")
            return False
            
        if response.status_code == 200:
            data = response.json()
            self.token = data.get("access_token")
            self.user_info = data.get("user", {})
            
            if self.token and self.user_info:
                role = self.user_info.get("role")
                if role == "salesperson":
                    self.log("✅ Plasiyer login successful - JWT token obtained")
                    self.log(f"   User: {self.user_info.get('full_name', 'Unknown')}")
                    self.log(f"   Role: {role}")
                    self.log(f"   User ID: {self.user_info.get('id')}")
                    return True
                else:
                    self.log(f"❌ Expected role 'salesperson', got '{role}'", "ERROR")
                    return False
            else:
                self.log("❌ Login response missing token or user info", "ERROR")
                return False
        else:
            self.log(f"❌ Plasiyer login failed with status {response.status_code}: {response.text}", "ERROR")
            return False
    
    def test_plasiyer_dashboard_stats(self):
        """Test 2: Dashboard Stats (Personal) - GET /api/dashboard/stats"""
        self.log("=== Testing Plasiyer Dashboard Stats (Personal Only) ===")
        
        response = self.make_request("GET", "/dashboard/stats")
        
        if not response:
            self.log("❌ Dashboard stats request failed - no response", "ERROR")
            return False
            
        if response.status_code == 200:
            data = response.json()
            
            # Check for expected plasiyer dashboard fields
            expected_fields = ["total_sales", "total_sales_amount", "total_visits", "total_collections", "monthly_sales_amount", "commission_emoji"]
            missing_fields = [field for field in expected_fields if field not in data]
            
            if missing_fields:
                self.log(f"❌ Dashboard stats missing expected plasiyer fields: {missing_fields}", "ERROR")
                return False
            
            # Check that admin-only fields are NOT present
            admin_only_fields = ["team_size", "total_customers"]
            present_admin_fields = [field for field in admin_only_fields if field in data]
            
            if present_admin_fields:
                self.log(f"❌ Dashboard contains admin-only fields for plasiyer: {present_admin_fields}", "ERROR")
                return False
            
            self.log("✅ Plasiyer dashboard stats working correctly")
            self.log(f"   Personal Total Sales: {data.get('total_sales', 0)}")
            self.log(f"   Personal Total Sales Amount: {data.get('total_sales_amount', 0)}")
            self.log(f"   Personal Total Visits: {data.get('total_visits', 0)}")
            self.log(f"   Personal Total Collections: {data.get('total_collections', 0)}")
            self.log(f"   Monthly Sales Amount: {data.get('monthly_sales_amount', 0)}")
            self.log(f"   Commission Emoji: {data.get('commission_emoji', 'N/A')}")
            
            # Store data for validation
            self.test_data["dashboard_stats"] = data
            return True
        else:
            self.log(f"❌ Dashboard stats failed with status {response.status_code}: {response.text}", "ERROR")
            return False
    
    def test_plasiyer_visits_list(self):
        """Test 3: Visits List (Personal Only) - GET /api/visits"""
        self.log("=== Testing Plasiyer Visits List (Personal Only) ===")
        
        response = self.make_request("GET", "/visits")
        
        if not response:
            self.log("❌ Visits API request failed - no response", "ERROR")
            return False
            
        if response.status_code == 200:
            data = response.json()
            
            if not isinstance(data, list):
                self.log("❌ Visits API should return a list", "ERROR")
                return False
            
            self.log(f"✅ Visits API working - returned {len(data)} visits")
            
            # Verify all visits belong to current plasiyer
            user_id = self.user_info.get("id")
            if not user_id:
                self.log("❌ Cannot verify visit ownership - user ID not available", "ERROR")
                return False
            
            for i, visit in enumerate(data):
                visit_salesperson_id = visit.get("salesperson_id")
                if visit_salesperson_id != user_id:
                    self.log(f"❌ Visit {i+1} belongs to different salesperson: {visit_salesperson_id} (expected: {user_id})", "ERROR")
                    return False
            
            if len(data) > 0:
                self.log(f"✅ All {len(data)} visits belong to current plasiyer (ID: {user_id})")
                
                # Check visit data structure
                visit = data[0]
                required_fields = ["id", "customer_id", "salesperson_id", "visit_date", "status"]
                missing_fields = [field for field in required_fields if field not in visit]
                
                if missing_fields:
                    self.log(f"❌ Visit missing required fields: {missing_fields}", "ERROR")
                    return False
                
                self.log("✅ Visit data structure validated")
                self.log(f"   Sample visit ID: {visit.get('id')}")
                self.log(f"   Visit status: {visit.get('status')}")
            else:
                self.log("ℹ️ No visits found for this plasiyer")
            
            self.test_data["visits"] = data
            return True
        else:
            self.log(f"❌ Visits API failed with status {response.status_code}: {response.text}", "ERROR")
            return False
    
    def test_plasiyer_sales_list(self):
        """Test 4: Sales List (Personal Only) - GET /api/sales"""
        self.log("=== Testing Plasiyer Sales List (Personal Only) ===")
        
        response = self.make_request("GET", "/sales")
        
        if not response:
            self.log("❌ Sales API request failed - no response", "ERROR")
            return False
            
        if response.status_code == 200:
            data = response.json()
            
            if not isinstance(data, list):
                self.log("❌ Sales API should return a list", "ERROR")
                return False
            
            self.log(f"✅ Sales API working - returned {len(data)} sales")
            
            # Verify all sales belong to current plasiyer
            user_id = self.user_info.get("id")
            if not user_id:
                self.log("❌ Cannot verify sale ownership - user ID not available", "ERROR")
                return False
            
            for i, sale in enumerate(data):
                sale_salesperson_id = sale.get("salesperson_id")
                if sale_salesperson_id != user_id:
                    self.log(f"❌ Sale {i+1} belongs to different salesperson: {sale_salesperson_id} (expected: {user_id})", "ERROR")
                    return False
            
            if len(data) > 0:
                self.log(f"✅ All {len(data)} sales belong to current plasiyer (ID: {user_id})")
                
                # Check sale data structure
                sale = data[0]
                required_fields = ["id", "customer_id", "salesperson_id", "sale_date", "total_amount", "items"]
                missing_fields = [field for field in required_fields if field not in sale]
                
                if missing_fields:
                    self.log(f"❌ Sale missing required fields: {missing_fields}", "ERROR")
                    return False
                
                self.log("✅ Sale data structure validated")
                self.log(f"   Sample sale ID: {sale.get('id')}")
                self.log(f"   Sale total amount: {sale.get('total_amount')}")
            else:
                self.log("ℹ️ No sales found for this plasiyer")
            
            self.test_data["sales"] = data
            return True
        else:
            self.log(f"❌ Sales API failed with status {response.status_code}: {response.text}", "ERROR")
            return False
    
    def test_plasiyer_collections_list(self):
        """Test 5: Collections List (Personal Only) - GET /api/collections"""
        self.log("=== Testing Plasiyer Collections List (Personal Only) ===")
        
        response = self.make_request("GET", "/collections")
        
        if not response:
            self.log("❌ Collections API request failed - no response", "ERROR")
            return False
            
        if response.status_code == 200:
            data = response.json()
            
            if not isinstance(data, list):
                self.log("❌ Collections API should return a list", "ERROR")
                return False
            
            self.log(f"✅ Collections API working - returned {len(data)} collections")
            
            # Verify all collections belong to current plasiyer
            user_id = self.user_info.get("id")
            if not user_id:
                self.log("❌ Cannot verify collection ownership - user ID not available", "ERROR")
                return False
            
            for i, collection in enumerate(data):
                collection_salesperson_id = collection.get("salesperson_id")
                if collection_salesperson_id != user_id:
                    self.log(f"❌ Collection {i+1} belongs to different salesperson: {collection_salesperson_id} (expected: {user_id})", "ERROR")
                    return False
            
            if len(data) > 0:
                self.log(f"✅ All {len(data)} collections belong to current plasiyer (ID: {user_id})")
                
                # Check collection data structure
                collection = data[0]
                required_fields = ["id", "customer_id", "salesperson_id", "amount", "collection_date", "payment_method"]
                missing_fields = [field for field in required_fields if field not in collection]
                
                if missing_fields:
                    self.log(f"❌ Collection missing required fields: {missing_fields}", "ERROR")
                    return False
                
                self.log("✅ Collection data structure validated")
                self.log(f"   Sample collection ID: {collection.get('id')}")
                self.log(f"   Collection amount: {collection.get('amount')}")
            else:
                self.log("ℹ️ No collections found for this plasiyer")
            
            self.test_data["collections"] = data
            return True
        else:
            self.log(f"❌ Collections API failed with status {response.status_code}: {response.text}", "ERROR")
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
        """Run all tests in sequence - Focus on Dashboard and Visits API"""
        self.log(f"Starting PediZone CRM API Tests - Review Request Focus")
        self.log(f"Backend URL: {self.base_url}")
        self.log(f"Test Credentials: admin/admin123")
        
        results = {
            "login_auth": False,
            "dashboard_alias": False,
            "dashboard_stats": False,
            "visits_api": False,
            "data_consistency": False
        }
        
        # Test 1: Login & Auth
        results["login_auth"] = self.test_login()
        if not results["login_auth"]:
            self.log("❌ Cannot continue without authentication", "ERROR")
            return results
        
        # Test 2: Dashboard Alias Endpoint (NEW)
        results["dashboard_alias"] = self.test_dashboard_alias()
        
        # Test 3: Dashboard Stats Endpoint (existing)
        results["dashboard_stats"] = self.test_dashboard_stats()
        
        # Test 4: Visits API with location data
        results["visits_api"] = self.test_visits_api()
        
        # Test 5: Data Consistency Validation
        results["data_consistency"] = self.validate_dashboard_data_consistency()
        
        # Summary
        self.log("=== TEST SUMMARY ===")
        passed = sum(1 for result in results.values() if result)
        total = len(results)
        
        for test_name, result in results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            self.log(f"{test_name.replace('_', ' ').title()}: {status}")
        
        self.log(f"Overall: {passed}/{total} tests passed")
        
        # Specific focus areas from review request
        self.log("=== REVIEW REQUEST FOCUS AREAS ===")
        self.log(f"✅ Login & Auth: {'WORKING' if results['login_auth'] else 'FAILED'}")
        self.log(f"✅ Dashboard Alias (/api/dashboard): {'WORKING' if results['dashboard_alias'] else 'FAILED'}")
        self.log(f"✅ Dashboard Stats (/api/dashboard/stats): {'WORKING' if results['dashboard_stats'] else 'FAILED'}")
        self.log(f"✅ Visits API with location data: {'WORKING' if results['visits_api'] else 'FAILED'}")
        
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