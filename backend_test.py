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
            "password": "test123"
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
    
    def test_plasiyer_commission_data(self):
        """Test 6: Commission Data - GET /api/sales/commission"""
        self.log("=== Testing Plasiyer Commission Data ===")
        
        response = self.make_request("GET", "/sales/commission")
        
        if not response:
            self.log("❌ Commission API request failed - no response", "ERROR")
            return False
            
        if response.status_code == 200:
            data = response.json()
            
            # Check for expected commission fields
            expected_fields = ["monthly_total", "emoji", "level", "sales_count"]
            missing_fields = [field for field in expected_fields if field not in data]
            
            if missing_fields:
                self.log(f"❌ Commission data missing fields: {missing_fields}", "ERROR")
                return False
            
            self.log("✅ Commission data endpoint working")
            self.log(f"   Monthly Total: {data.get('monthly_total', 0)}")
            self.log(f"   Commission Emoji: {data.get('emoji', 'N/A')}")
            self.log(f"   Commission Level: {data.get('level', 'N/A')}")
            self.log(f"   Sales Count: {data.get('sales_count', 0)}")
            
            # Validate emoji is one of expected values
            expected_emojis = ["🌱", "💪", "🔥", "🏆"]
            emoji = data.get("emoji")
            if emoji not in expected_emojis:
                self.log(f"❌ Unexpected commission emoji: {emoji}", "ERROR")
                return False
            
            self.test_data["commission"] = data
            return True
        else:
            self.log(f"❌ Commission API failed with status {response.status_code}: {response.text}", "ERROR")
            return False
    
    def validate_data_consistency(self):
        """Test 7: Validate Data Consistency Across Endpoints"""
        self.log("=== Validating Data Consistency ===")
        
        dashboard_data = self.test_data.get("dashboard_stats", {})
        sales_data = self.test_data.get("sales", [])
        visits_data = self.test_data.get("visits", [])
        collections_data = self.test_data.get("collections", [])
        commission_data = self.test_data.get("commission", {})
        
        # Validate sales count consistency
        dashboard_sales_count = dashboard_data.get("total_sales", 0)
        actual_sales_count = len(sales_data)
        
        if dashboard_sales_count != actual_sales_count:
            self.log(f"❌ Sales count mismatch: dashboard={dashboard_sales_count}, actual={actual_sales_count}", "ERROR")
            return False
        
        # Validate visits count consistency
        dashboard_visits_count = dashboard_data.get("total_visits", 0)
        actual_visits_count = len(visits_data)
        
        if dashboard_visits_count != actual_visits_count:
            self.log(f"❌ Visits count mismatch: dashboard={dashboard_visits_count}, actual={actual_visits_count}", "ERROR")
            return False
        
        # Validate sales amount consistency
        dashboard_sales_amount = dashboard_data.get("total_sales_amount", 0)
        calculated_sales_amount = sum([sale.get("total_amount", 0) for sale in sales_data])
        
        if abs(dashboard_sales_amount - calculated_sales_amount) > 0.01:  # Allow for floating point precision
            self.log(f"❌ Sales amount mismatch: dashboard={dashboard_sales_amount}, calculated={calculated_sales_amount}", "ERROR")
            return False
        
        # Validate collections amount consistency
        dashboard_collections_amount = dashboard_data.get("total_collections", 0)
        calculated_collections_amount = sum([collection.get("amount", 0) for collection in collections_data])
        
        if abs(dashboard_collections_amount - calculated_collections_amount) > 0.01:
            self.log(f"❌ Collections amount mismatch: dashboard={dashboard_collections_amount}, calculated={calculated_collections_amount}", "ERROR")
            return False
        
        self.log("✅ Data consistency validated across all endpoints")
        self.log(f"   Sales count: {actual_sales_count}")
        self.log(f"   Visits count: {actual_visits_count}")
        self.log(f"   Sales amount: {calculated_sales_amount}")
        self.log(f"   Collections amount: {calculated_collections_amount}")
        
        return True
    
    def run_all_tests(self):
        """Run all role-based filtering tests for plasiyer (salesperson)"""
        self.log(f"Starting PediZone CRM Role-Based Filtering Tests")
        self.log(f"Backend URL: {self.base_url}")
        self.log(f"Test Credentials: testuser/123456 (Plasiyer/Salesperson)")
        self.log(f"Focus: Verify plasiyer only sees their own data")
        
        results = {
            "plasiyer_login": False,
            "dashboard_stats": False,
            "visits_list": False,
            "sales_list": False,
            "collections_list": False,
            "commission_data": False,
            "data_consistency": False
        }
        
        # Test 1: Login as Plasiyer
        results["plasiyer_login"] = self.test_plasiyer_login()
        if not results["plasiyer_login"]:
            self.log("❌ Cannot continue without plasiyer authentication", "ERROR")
            return results
        
        # Test 2: Dashboard Stats (Personal)
        results["dashboard_stats"] = self.test_plasiyer_dashboard_stats()
        
        # Test 3: Visits List (Personal Only)
        results["visits_list"] = self.test_plasiyer_visits_list()
        
        # Test 4: Sales List (Personal Only)
        results["sales_list"] = self.test_plasiyer_sales_list()
        
        # Test 5: Collections List (Personal Only)
        results["collections_list"] = self.test_plasiyer_collections_list()
        
        # Test 6: Commission Data
        results["commission_data"] = self.test_plasiyer_commission_data()
        
        # Test 7: Data Consistency Validation
        results["data_consistency"] = self.validate_data_consistency()
        
        # Summary
        self.log("=== TEST SUMMARY ===")
        passed = sum(1 for result in results.values() if result)
        total = len(results)
        
        for test_name, result in results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            self.log(f"{test_name.replace('_', ' ').title()}: {status}")
        
        self.log(f"Overall: {passed}/{total} tests passed")
        
        # Role-based filtering verification
        self.log("=== ROLE-BASED FILTERING VERIFICATION ===")
        self.log(f"✅ Plasiyer Login: {'WORKING' if results['plasiyer_login'] else 'FAILED'}")
        self.log(f"✅ Personal Dashboard Stats: {'WORKING' if results['dashboard_stats'] else 'FAILED'}")
        self.log(f"✅ Personal Visits Only: {'WORKING' if results['visits_list'] else 'FAILED'}")
        self.log(f"✅ Personal Sales Only: {'WORKING' if results['sales_list'] else 'FAILED'}")
        self.log(f"✅ Personal Collections Only: {'WORKING' if results['collections_list'] else 'FAILED'}")
        self.log(f"✅ Commission Data: {'WORKING' if results['commission_data'] else 'FAILED'}")
        
        if all(results.values()):
            self.log("🎉 ROLE-BASED FILTERING WORKING CORRECTLY")
            self.log("   Plasiyer can only see their own data")
            self.log("   No access to other salespeople's data")
            self.log("   Dashboard shows personal statistics with commission emoji")
        else:
            self.log("❌ ROLE-BASED FILTERING HAS ISSUES")
            failed_tests = [test for test, result in results.items() if not result]
            self.log(f"   Failed tests: {failed_tests}")
        
        return results

if __name__ == "__main__":
    tester = PediZoneRoleBasedTester()
    results = tester.run_all_tests()
    
    # Exit with error code if any test failed
    if not all(results.values()):
        sys.exit(1)
    else:
        print("\n🎉 All role-based filtering tests passed!")
        sys.exit(0)