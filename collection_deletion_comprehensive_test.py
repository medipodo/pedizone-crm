#!/usr/bin/env python3
"""
PediZone CRM Collection Deletion Comprehensive Testing
Testing collection deletion functionality with test data creation
"""

import requests
import json
import sys
from datetime import datetime, timezone

# Backend URL as specified in review request
BACKEND_URL = "https://crm-pedizone.preview.emergentagent.com/api"

class ComprehensiveCollectionDeletionTester:
    def __init__(self):
        self.base_url = BACKEND_URL
        self.token = None
        self.headers = {"Content-Type": "application/json"}
        self.user_info = {}
        self.test_customer_id = None
        self.test_collection_id = None
        self.initial_collections = []
        
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
    
    def test_admin_login(self):
        """Test 1: Login as Admin"""
        self.log("=== Testing Admin Login ===")
        
        login_data = {
            "username": "admin",
            "password": "admin123"
        }
        
        response = self.make_request("POST", "/auth/login", login_data, auth_required=False)
        
        if not response or response.status_code != 200:
            self.log("❌ Admin login failed", "ERROR")
            return False
            
        data = response.json()
        self.token = data.get("access_token")
        self.user_info = data.get("user", {})
        
        if self.token and self.user_info.get("role") == "admin":
            self.log("✅ Admin login successful")
            return True
        else:
            self.log("❌ Login response invalid", "ERROR")
            return False
    
    def setup_test_data(self):
        """Setup: Create test customer and collection for deletion testing"""
        self.log("=== Setting Up Test Data ===")
        
        # Get existing customers first
        response = self.make_request("GET", "/customers")
        if response and response.status_code == 200:
            customers = response.json()
            if len(customers) > 0:
                self.test_customer_id = customers[0]["id"]
                self.log(f"✅ Using existing customer: {self.test_customer_id}")
            else:
                # Create a test customer if none exist
                customer_data = {
                    "name": "Test Customer for Collection Deletion",
                    "address": "Test Address 123",
                    "phone": "+90 555 123 4567",
                    "email": "test@example.com",
                    "region_id": "test-region-id",
                    "tax_number": "1234567890",
                    "notes": "Test customer for collection deletion testing"
                }
                
                response = self.make_request("POST", "/customers", customer_data)
                if response and response.status_code == 200:
                    customer = response.json()
                    self.test_customer_id = customer["id"]
                    self.log(f"✅ Created test customer: {self.test_customer_id}")
                else:
                    self.log("❌ Failed to create test customer", "ERROR")
                    return False
        else:
            self.log("❌ Failed to get customers list", "ERROR")
            return False
        
        # Create a test collection
        collection_data = {
            "customer_id": self.test_customer_id,
            "amount": 1500.0,
            "collection_date": datetime.now(timezone.utc).isoformat(),
            "payment_method": "nakit",
            "notes": "Test collection for deletion testing"
        }
        
        response = self.make_request("POST", "/collections", collection_data)
        if response and response.status_code == 200:
            collection = response.json()
            self.test_collection_id = collection["id"]
            self.log(f"✅ Created test collection: {self.test_collection_id}")
            self.log(f"   Amount: {collection['amount']}")
            return True
        else:
            self.log("❌ Failed to create test collection", "ERROR")
            return False
    
    def test_get_collections_list(self):
        """Test 2: Get Collections List"""
        self.log("=== Testing Get Collections List ===")
        
        response = self.make_request("GET", "/collections")
        
        if not response or response.status_code != 200:
            self.log("❌ Collections list request failed", "ERROR")
            return False
            
        data = response.json()
        if not isinstance(data, list):
            self.log("❌ Collections API should return a list", "ERROR")
            return False
        
        self.initial_collections = data
        self.log(f"✅ Collections list retrieved - found {len(data)} collections")
        
        # Verify our test collection is in the list
        test_collection_found = False
        for collection in data:
            if collection.get("id") == self.test_collection_id:
                test_collection_found = True
                self.log(f"   Test collection found: {self.test_collection_id}")
                break
        
        if not test_collection_found:
            self.log(f"❌ Test collection not found in list: {self.test_collection_id}", "ERROR")
            return False
        
        return True
    
    def test_delete_collection(self):
        """Test 3: Delete Collection"""
        self.log("=== Testing Collection Deletion ===")
        
        if not self.test_collection_id:
            self.log("❌ No test collection ID available", "ERROR")
            return False
        
        response = self.make_request("DELETE", f"/collections/{self.test_collection_id}")
        
        if not response:
            self.log("❌ Collection deletion request failed - no response", "ERROR")
            return False
            
        if response.status_code == 200:
            data = response.json()
            expected_message = "Tahsilat silindi"
            actual_message = data.get("message", "")
            
            if actual_message == expected_message:
                self.log("✅ Collection deletion successful")
                self.log(f"   Response: {actual_message}")
                return True
            else:
                self.log(f"❌ Unexpected response message: '{actual_message}'", "ERROR")
                return False
        else:
            self.log(f"❌ Collection deletion failed with status {response.status_code}", "ERROR")
            return False
    
    def test_verify_deletion(self):
        """Test 4: Verify Collection is Deleted"""
        self.log("=== Verifying Collection Deletion ===")
        
        response = self.make_request("GET", "/collections")
        
        if not response or response.status_code != 200:
            self.log("❌ Collections verification request failed", "ERROR")
            return False
            
        data = response.json()
        
        # Check if deleted collection is still in the list
        for collection in data:
            if collection.get("id") == self.test_collection_id:
                self.log(f"❌ Deleted collection still found in list", "ERROR")
                return False
        
        initial_count = len(self.initial_collections)
        current_count = len(data)
        expected_count = initial_count - 1
        
        if current_count == expected_count:
            self.log("✅ Collection successfully removed from database")
            self.log(f"   Initial count: {initial_count}, Current count: {current_count}")
            return True
        else:
            self.log(f"❌ Collection count mismatch - expected: {expected_count}, actual: {current_count}", "ERROR")
            return False
    
    def test_delete_nonexistent_collection(self):
        """Test 5: Try to delete non-existent collection (should return 404)"""
        self.log("=== Testing Delete Non-Existent Collection ===")
        
        fake_id = "non-existent-collection-id-12345"
        response = self.make_request("DELETE", f"/collections/{fake_id}")
        
        if response is None:
            self.log("❌ Delete non-existent collection request failed - no response", "ERROR")
            return False
            
        if response.status_code == 404:
            data = response.json()
            expected_message = "Tahsilat bulunamadı"
            actual_message = data.get("detail", "")
            
            if actual_message == expected_message:
                self.log("✅ Non-existent collection deletion correctly returned 404")
                self.log(f"   Error message: {actual_message}")
                return True
            else:
                self.log(f"❌ Unexpected 404 error message: '{actual_message}'", "ERROR")
                return False
        else:
            self.log(f"❌ Expected 404 for non-existent collection, got {response.status_code}", "ERROR")
            return False
    
    def run_all_tests(self):
        """Run all comprehensive collection deletion tests"""
        self.log(f"Starting Comprehensive PediZone CRM Collection Deletion Tests")
        self.log(f"Backend URL: {self.base_url}")
        self.log(f"Test Credentials: admin/admin123")
        
        results = {
            "admin_login": False,
            "setup_test_data": False,
            "get_collections_list": False,
            "delete_collection": False,
            "verify_deletion": False,
            "delete_nonexistent": False
        }
        
        # Test 1: Login as Admin
        results["admin_login"] = self.test_admin_login()
        if not results["admin_login"]:
            return results
        
        # Setup: Create test data
        results["setup_test_data"] = self.setup_test_data()
        if not results["setup_test_data"]:
            return results
        
        # Test 2: Get Collections List
        results["get_collections_list"] = self.test_get_collections_list()
        if not results["get_collections_list"]:
            return results
        
        # Test 3: Delete Collection
        results["delete_collection"] = self.test_delete_collection()
        
        # Test 4: Verify Deletion
        results["verify_deletion"] = self.test_verify_deletion()
        
        # Test 5: Delete Non-Existent Collection
        results["delete_nonexistent"] = self.test_delete_nonexistent_collection()
        
        # Summary
        self.log("=== COMPREHENSIVE TEST SUMMARY ===")
        passed = sum(1 for result in results.values() if result)
        total = len(results)
        
        for test_name, result in results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            self.log(f"{test_name.replace('_', ' ').title()}: {status}")
        
        self.log(f"Overall: {passed}/{total} tests passed")
        
        if all(results.values()):
            self.log("🎉 ALL COLLECTION DELETION TESTS PASSED")
            self.log("   ✅ Collection deletion API working correctly")
            self.log("   ✅ Proper success message returned")
            self.log("   ✅ Collection removed from database")
            self.log("   ✅ 404 error for non-existent collections")
        else:
            self.log("❌ SOME COLLECTION DELETION TESTS FAILED")
            failed_tests = [test for test, result in results.items() if not result]
            self.log(f"   Failed tests: {failed_tests}")
        
        return results

if __name__ == "__main__":
    tester = ComprehensiveCollectionDeletionTester()
    results = tester.run_all_tests()
    
    # Exit with error code if any test failed
    if not all(results.values()):
        sys.exit(1)
    else:
        print("\n🎉 All comprehensive collection deletion tests passed!")
        sys.exit(0)