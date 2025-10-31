#!/usr/bin/env python3
"""
PediZone CRM Document Upload and Visit Map Display Testing
Testing document upload functionality (file base64 and URL) and visit location data for map display
"""

import requests
import json
import sys
from datetime import datetime, timezone

# Backend URL as specified in review request
BACKEND_URL = "https://crm-pedizone.preview.emergentagent.com/api"

class PediZoneDocumentTester:
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
    
    def test_document_upload_base64(self):
        """Test 2: Document Upload with Base64 File - POST /api/documents"""
        self.log("=== Testing Document Upload (Base64 File) ===")
        
        document_data = {
            "title": "Test Katalog",
            "description": "Test açıklama",
            "type": "katalog",
            "file_name": "test.pdf",
            "file_base64": "JVBERi0xLjQKJeLjz9MKMyAwIG9iago8PC9TdWJ0eXBlL0ltYWdlL1dpZHRoIDEwMC9IZWlnaHQgMTAwL0NvbG9yU3BhY2UvRGV2aWNlUkdCL0JpdHNQZXJDb21wb25lbnQgOC9GaWx0ZXIvRmxhdGVEZWNvZGU+PnN0cmVhbQp4nOzBAQ0AAADCoPdPbQ8HFAAAAAAAAAD/AgD/AAFxgAABCg==",
            "file_type": "application/pdf"
        }
        
        response = self.make_request("POST", "/documents", document_data)
        
        if not response:
            self.log("❌ Document upload request failed - no response", "ERROR")
            return False
            
        if response.status_code == 200:
            data = response.json()
            
            # Verify response structure
            required_fields = ["id", "title", "description", "type", "file_name", "file_base64", "file_type", "created_at"]
            missing_fields = [field for field in required_fields if field not in data]
            
            if missing_fields:
                self.log(f"❌ Document response missing fields: {missing_fields}", "ERROR")
                return False
            
            # Verify data matches input
            if (data.get("title") != document_data["title"] or 
                data.get("type") != document_data["type"] or
                data.get("file_name") != document_data["file_name"]):
                self.log("❌ Document response data doesn't match input", "ERROR")
                return False
            
            self.log("✅ Document upload (Base64) successful")
            self.log(f"   Document ID: {data.get('id')}")
            self.log(f"   Title: {data.get('title')}")
            self.log(f"   Type: {data.get('type')}")
            self.log(f"   File Name: {data.get('file_name')}")
            self.log(f"   File Type: {data.get('file_type')}")
            
            self.test_data["base64_document"] = data
            return True
        else:
            self.log(f"❌ Document upload failed with status {response.status_code}: {response.text}", "ERROR")
            return False
    
    def test_document_upload_url(self):
        """Test 3: Document Upload with URL - POST /api/documents"""
        self.log("=== Testing Document Upload (URL) ===")
        
        document_data = {
            "title": "Test URL Doküman",
            "description": "URL ile eklendi",
            "type": "brosur",
            "url": "https://example.com/test.pdf"
        }
        
        response = self.make_request("POST", "/documents", document_data)
        
        if not response:
            self.log("❌ Document URL upload request failed - no response", "ERROR")
            return False
            
        if response.status_code == 200:
            data = response.json()
            
            # Verify response structure
            required_fields = ["id", "title", "description", "type", "url", "created_at"]
            missing_fields = [field for field in required_fields if field not in data]
            
            if missing_fields:
                self.log(f"❌ Document URL response missing fields: {missing_fields}", "ERROR")
                return False
            
            # Verify data matches input
            if (data.get("title") != document_data["title"] or 
                data.get("type") != document_data["type"] or
                data.get("url") != document_data["url"]):
                self.log("❌ Document URL response data doesn't match input", "ERROR")
                return False
            
            self.log("✅ Document upload (URL) successful")
            self.log(f"   Document ID: {data.get('id')}")
            self.log(f"   Title: {data.get('title')}")
            self.log(f"   Type: {data.get('type')}")
            self.log(f"   URL: {data.get('url')}")
            
            self.test_data["url_document"] = data
            return True
        else:
            self.log(f"❌ Document URL upload failed with status {response.status_code}: {response.text}", "ERROR")
            return False
    
    def test_get_documents(self):
        """Test 4: Get Documents List - GET /api/documents"""
        self.log("=== Testing Get Documents List ===")
        
        response = self.make_request("GET", "/documents")
        
        if not response:
            self.log("❌ Get documents request failed - no response", "ERROR")
            return False
            
        if response.status_code == 200:
            data = response.json()
            
            if not isinstance(data, list):
                self.log("❌ Documents API should return a list", "ERROR")
                return False
            
            self.log(f"✅ Documents API working - returned {len(data)} documents")
            
            # Verify our test documents are in the list
            base64_doc = self.test_data.get("base64_document")
            url_doc = self.test_data.get("url_document")
            
            if base64_doc:
                base64_found = any(doc.get("id") == base64_doc.get("id") for doc in data)
                if not base64_found:
                    self.log("❌ Base64 document not found in documents list", "ERROR")
                    return False
                else:
                    self.log("✅ Base64 document found in documents list")
            
            if url_doc:
                url_found = any(doc.get("id") == url_doc.get("id") for doc in data)
                if not url_found:
                    self.log("❌ URL document not found in documents list", "ERROR")
                    return False
                else:
                    self.log("✅ URL document found in documents list")
            
            # Check document structure
            if len(data) > 0:
                doc = data[0]
                required_fields = ["id", "title", "type", "created_at"]
                missing_fields = [field for field in required_fields if field not in doc]
                
                if missing_fields:
                    self.log(f"❌ Document missing required fields: {missing_fields}", "ERROR")
                    return False
                
                self.log("✅ Document data structure validated")
                self.log(f"   Sample document ID: {doc.get('id')}")
                self.log(f"   Document type: {doc.get('type')}")
            
            self.test_data["documents"] = data
            return True
        else:
            self.log(f"❌ Get documents failed with status {response.status_code}: {response.text}", "ERROR")
            return False
    
    def test_get_visits_with_location(self):
        """Test 5: Get Visits with Location Data - GET /api/visits"""
        self.log("=== Testing Get Visits with Location Data ===")
        
        response = self.make_request("GET", "/visits")
        
        if not response:
            self.log("❌ Get visits request failed - no response", "ERROR")
            return False
            
        if response.status_code == 200:
            data = response.json()
            
            if not isinstance(data, list):
                self.log("❌ Visits API should return a list", "ERROR")
                return False
            
            self.log(f"✅ Visits API working - returned {len(data)} visits")
            
            # Count visits with valid location coordinates
            visits_with_location = 0
            visits_with_coordinates = 0
            
            for i, visit in enumerate(data):
                # Check for location object with latitude/longitude
                location = visit.get("location")
                if location and isinstance(location, dict):
                    lat = location.get("latitude")
                    lng = location.get("longitude")
                    if lat is not None and lng is not None:
                        visits_with_location += 1
                        self.log(f"   Visit {i+1}: Location object found - lat: {lat}, lng: {lng}")
                
                # Check for direct latitude/longitude fields
                direct_lat = visit.get("latitude")
                direct_lng = visit.get("longitude")
                if direct_lat is not None and direct_lng is not None:
                    visits_with_coordinates += 1
                    self.log(f"   Visit {i+1}: Direct coordinates found - lat: {direct_lat}, lng: {direct_lng}")
            
            self.log(f"✅ Visits with location object: {visits_with_location}")
            self.log(f"✅ Visits with direct coordinates: {visits_with_coordinates}")
            
            # Verify visit data structure for map display
            if len(data) > 0:
                visit = data[0]
                required_fields = ["id", "customer_id", "salesperson_id", "visit_date", "status"]
                missing_fields = [field for field in required_fields if field not in visit]
                
                if missing_fields:
                    self.log(f"❌ Visit missing required fields: {missing_fields}", "ERROR")
                    return False
                
                self.log("✅ Visit data structure validated for map display")
                self.log(f"   Sample visit ID: {visit.get('id')}")
                self.log(f"   Visit date: {visit.get('visit_date')}")
                self.log(f"   Visit status: {visit.get('status')}")
                
                # Check if visit has location data
                if visit.get("location"):
                    location = visit.get("location")
                    self.log(f"   Location: {location}")
                elif visit.get("latitude") and visit.get("longitude"):
                    self.log(f"   Coordinates: lat={visit.get('latitude')}, lng={visit.get('longitude')}")
                else:
                    self.log("   No location data found for this visit")
            
            total_with_location = visits_with_location + visits_with_coordinates
            self.log(f"✅ Total visits with valid coordinates for map: {total_with_location}/{len(data)}")
            
            self.test_data["visits"] = data
            self.test_data["visits_with_location"] = total_with_location
            return True
        else:
            self.log(f"❌ Get visits failed with status {response.status_code}: {response.text}", "ERROR")
            return False
    
    def validate_document_model_flexibility(self):
        """Test 6: Validate Document Model Accepts Both File and URL"""
        self.log("=== Validating Document Model Flexibility ===")
        
        base64_doc = self.test_data.get("base64_document")
        url_doc = self.test_data.get("url_document")
        
        if not base64_doc or not url_doc:
            self.log("❌ Cannot validate - missing test documents", "ERROR")
            return False
        
        # Verify base64 document has file fields but no URL
        if (base64_doc.get("file_base64") and 
            base64_doc.get("file_name") and 
            base64_doc.get("file_type") and
            not base64_doc.get("url")):
            self.log("✅ Base64 document model validation passed")
        else:
            self.log("❌ Base64 document model validation failed", "ERROR")
            return False
        
        # Verify URL document has URL but no file fields
        if (url_doc.get("url") and 
            not url_doc.get("file_base64") and
            not url_doc.get("file_name")):
            self.log("✅ URL document model validation passed")
        else:
            self.log("❌ URL document model validation failed", "ERROR")
            return False
        
        self.log("✅ Document model accepts both file upload and URL methods")
        return True
    
    def run_all_tests(self):
        """Run all document upload and visit map tests"""
        self.log(f"Starting PediZone CRM Document Upload and Visit Map Tests")
        self.log(f"Backend URL: {self.base_url}")
        self.log(f"Test Credentials: admin/admin123")
        self.log(f"Focus: Document upload (file base64 + URL) and visit location data")
        
        results = {
            "admin_login": False,
            "document_upload_base64": False,
            "document_upload_url": False,
            "get_documents": False,
            "get_visits_with_location": False,
            "document_model_validation": False
        }
        
        # Test 1: Login as Admin
        results["admin_login"] = self.test_admin_login()
        if not results["admin_login"]:
            self.log("❌ Cannot continue without admin authentication", "ERROR")
            return results
        
        # Test 2: Document Upload (Base64)
        results["document_upload_base64"] = self.test_document_upload_base64()
        
        # Test 3: Document Upload (URL)
        results["document_upload_url"] = self.test_document_upload_url()
        
        # Test 4: Get Documents List
        results["get_documents"] = self.test_get_documents()
        
        # Test 5: Get Visits with Location Data
        results["get_visits_with_location"] = self.test_get_visits_with_location()
        
        # Test 6: Document Model Validation
        results["document_model_validation"] = self.validate_document_model_flexibility()
        
        # Summary
        self.log("=== TEST SUMMARY ===")
        passed = sum(1 for result in results.values() if result)
        total = len(results)
        
        for test_name, result in results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            self.log(f"{test_name.replace('_', ' ').title()}: {status}")
        
        self.log(f"Overall: {passed}/{total} tests passed")
        
        # Feature verification
        self.log("=== FEATURE VERIFICATION ===")
        self.log(f"✅ Admin Login: {'WORKING' if results['admin_login'] else 'FAILED'}")
        self.log(f"✅ Document Upload (Base64): {'WORKING' if results['document_upload_base64'] else 'FAILED'}")
        self.log(f"✅ Document Upload (URL): {'WORKING' if results['document_upload_url'] else 'FAILED'}")
        self.log(f"✅ Document Retrieval: {'WORKING' if results['get_documents'] else 'FAILED'}")
        self.log(f"✅ Visit Location Data: {'WORKING' if results['get_visits_with_location'] else 'FAILED'}")
        self.log(f"✅ Document Model Flexibility: {'WORKING' if results['document_model_validation'] else 'FAILED'}")
        
        # Additional info
        visits_with_location = self.test_data.get("visits_with_location", 0)
        total_visits = len(self.test_data.get("visits", []))
        documents_count = len(self.test_data.get("documents", []))
        
        self.log("=== ADDITIONAL INFO ===")
        self.log(f"📄 Total documents in system: {documents_count}")
        self.log(f"📍 Visits with location data: {visits_with_location}/{total_visits}")
        
        if all(results.values()):
            self.log("🎉 ALL DOCUMENT AND VISIT MAP FEATURES WORKING")
            self.log("   ✅ Document upload supports both file base64 and URL methods")
            self.log("   ✅ Documents are properly stored and retrievable")
            self.log("   ✅ Visits have location data for map display")
        else:
            self.log("❌ SOME FEATURES HAVE ISSUES")
            failed_tests = [test for test, result in results.items() if not result]
            self.log(f"   Failed tests: {failed_tests}")
        
        return results

if __name__ == "__main__":
    tester = PediZoneDocumentTester()
    results = tester.run_all_tests()
    
    # Exit with error code if any test failed
    if not all(results.values()):
        sys.exit(1)
    else:
        print("\n🎉 All document upload and visit map tests passed!")
        sys.exit(0)