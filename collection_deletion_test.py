#!/usr/bin/env python3
"""
PediZone CRM Collection Deletion Testing
Testing collection deletion functionality as specified in review request
"""

import requests
import json
import sys
from datetime import datetime, timezone

# Backend URL as specified in review request
BACKEND_URL = "https://crm-pedizone.preview.emergentagent.com/api"

class CollectionDeletionTester:
    def __init__(self):
        self.base_url = BACKEND_URL
        self.token = None
        self.headers = {"Content-Type": "application/json"}
        self.user_info = {}
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
        """Test 1: Login as Admin - POST /api/auth/login"""
        self.log("=== Testing Admin Login ===")
        
        login_data = {
            "username": "admin",
            "password": "admin123"
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
                if role == "admin":
                    self.log("✅ Admin login successful - JWT token obtained")
                    self.log(f"   User: {self.user_info.get('full_name', 'Unknown')}")
                    self.log(f"   Role: {role}")
                    self.log(f"   User ID: {self.user_info.get('id')}")
                    return True
                else:
                    self.log(f"❌ Expected role 'admin', got '{role}'", "ERROR")
                    return False
            else:
                self.log("❌ Login response missing token or user info", "ERROR")
                return False
        else:
            self.log(f"❌ Admin login failed with status {response.status_code}: {response.text}", "ERROR")
            return False
    
    def test_get_collections_list(self):
        """Test 2: Get Collections List - GET /api/collections"""
        self.log("=== Testing Get Collections List ===")
        
        response = self.make_request("GET", "/collections")
        
        if not response:
            self.log("❌ Collections list request failed - no response", "ERROR")
            return False
            
        if response.status_code == 200:
            data = response.json()
            
            if not isinstance(data, list):
                self.log("❌ Collections API should return a list", "ERROR")
                return False
            
            self.initial_collections = data
            self.log(f"✅ Collections list retrieved - found {len(data)} collections")
            
            if len(data) > 0:
                # Save first collection ID for deletion test
                self.test_collection_id = data[0].get("id")
                self.log(f"   Selected collection for deletion: {self.test_collection_id}")
                self.log(f"   Collection amount: {data[0].get('amount', 'N/A')}")
                self.log(f"   Collection date: {data[0].get('collection_date', 'N/A')}")
                return True
            else:
                self.log("❌ No collections found - cannot test deletion", "ERROR")
                return False
        else:
            self.log(f"❌ Collections list failed with status {response.status_code}: {response.text}", "ERROR")
            return False
    
    def test_delete_collection(self):
        """Test 3: Delete Collection - DELETE /api/collections/{collection_id}"""
        self.log("=== Testing Collection Deletion ===")
        
        if not self.test_collection_id:
            self.log("❌ No collection ID available for deletion test", "ERROR")
            return False
        
        response = self.make_request("DELETE", f"/collections/{self.test_collection_id}")
        
        if not response:
            self.log("❌ Collection deletion request failed - no response", "ERROR")
            return False
            
        if response.status_code == 200:
            data = response.json()
            
            # Verify response message
            expected_message = "Tahsilat silindi"
            actual_message = data.get("message", "")
            
            if actual_message == expected_message:
                self.log("✅ Collection deletion successful")
                self.log(f"   Response: {actual_message}")
                self.log(f"   Deleted collection ID: {self.test_collection_id}")
                return True
            else:
                self.log(f"❌ Unexpected response message: '{actual_message}' (expected: '{expected_message}')", "ERROR")
                return False
        elif response.status_code == 404:
            self.log(f"❌ Collection not found (404) - ID: {self.test_collection_id}", "ERROR")
            return False
        else:
            self.log(f"❌ Collection deletion failed with status {response.status_code}: {response.text}", "ERROR")
            return False
    
    def test_verify_deletion(self):
        """Test 4: Verify Collection is Deleted - GET /api/collections"""
        self.log("=== Verifying Collection Deletion ===")
        
        if not self.test_collection_id:
            self.log("❌ No collection ID to verify deletion", "ERROR")
            return False
        
        response = self.make_request("GET", "/collections")
        
        if not response:
            self.log("❌ Collections verification request failed - no response", "ERROR")
            return False
            
        if response.status_code == 200:
            data = response.json()
            
            if not isinstance(data, list):
                self.log("❌ Collections API should return a list", "ERROR")
                return False
            
            # Check if deleted collection is still in the list
            deleted_collection_found = False
            for collection in data:
                if collection.get("id") == self.test_collection_id:
                    deleted_collection_found = True
                    break
            
            if deleted_collection_found:
                self.log(f"❌ Deleted collection still found in list - ID: {self.test_collection_id}", "ERROR")
                return False
            else:
                initial_count = len(self.initial_collections)
                current_count = len(data)
                expected_count = initial_count - 1
                
                if current_count == expected_count:
                    self.log("✅ Collection successfully removed from database")
                    self.log(f"   Initial collections count: {initial_count}")
                    self.log(f"   Current collections count: {current_count}")
                    self.log(f"   Deleted collection ID: {self.test_collection_id}")
                    return True
                else:
                    self.log(f"❌ Collection count mismatch - expected: {expected_count}, actual: {current_count}", "ERROR")
                    return False
        else:
            self.log(f"❌ Collections verification failed with status {response.status_code}: {response.text}", "ERROR")
            return False
    
    def run_all_tests(self):
        """Run all collection deletion tests"""
        self.log(f"Starting PediZone CRM Collection Deletion Tests")
        self.log(f"Backend URL: {self.base_url}")
        self.log(f"Test Credentials: admin/admin123")
        self.log(f"Focus: Verify collection deletion functionality")
        
        results = {
            "admin_login": False,
            "get_collections_list": False,
            "delete_collection": False,
            "verify_deletion": False
        }
        
        # Test 1: Login as Admin
        results["admin_login"] = self.test_admin_login()
        if not results["admin_login"]:
            self.log("❌ Cannot continue without admin authentication", "ERROR")
            return results
        
        # Test 2: Get Collections List
        results["get_collections_list"] = self.test_get_collections_list()
        if not results["get_collections_list"]:
            self.log("❌ Cannot continue without collections list", "ERROR")
            return results
        
        # Test 3: Delete Collection
        results["delete_collection"] = self.test_delete_collection()
        
        # Test 4: Verify Deletion
        results["verify_deletion"] = self.test_verify_deletion()
        
        # Summary
        self.log("=== TEST SUMMARY ===")
        passed = sum(1 for result in results.values() if result)
        total = len(results)
        
        for test_name, result in results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            self.log(f"{test_name.replace('_', ' ').title()}: {status}")
        
        self.log(f"Overall: {passed}/{total} tests passed")
        
        # Collection deletion verification
        self.log("=== COLLECTION DELETION VERIFICATION ===")
        self.log(f"✅ Admin Login: {'WORKING' if results['admin_login'] else 'FAILED'}")
        self.log(f"✅ Collections List API: {'WORKING' if results['get_collections_list'] else 'FAILED'}")
        self.log(f"✅ Collection Deletion API: {'WORKING' if results['delete_collection'] else 'FAILED'}")
        self.log(f"✅ Deletion Verification: {'WORKING' if results['verify_deletion'] else 'FAILED'}")
        
        if all(results.values()):
            self.log("🎉 COLLECTION DELETION FUNCTIONALITY WORKING CORRECTLY")
            self.log("   DELETE /api/collections/{id} endpoint working")
            self.log("   Returns proper success message: 'Tahsilat silindi'")
            self.log("   Collection removed from database")
        else:
            self.log("❌ COLLECTION DELETION FUNCTIONALITY HAS ISSUES")
            failed_tests = [test for test, result in results.items() if not result]
            self.log(f"   Failed tests: {failed_tests}")
        
        return results

if __name__ == "__main__":
    tester = CollectionDeletionTester()
    results = tester.run_all_tests()
    
    # Exit with error code if any test failed
    if not all(results.values()):
        sys.exit(1)
    else:
        print("\n🎉 All collection deletion tests passed!")
        sys.exit(0)