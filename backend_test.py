import requests
import sys
import json
from datetime import datetime
import uuid

class AutoCheckAPITester:
    def __init__(self, base_url="https://turkce-chat-app-2.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0
        self.buyer_user = None
        self.inspector_user = None
        self.inspection_id = None
        self.security_code = None

    def run_test(self, name, method, endpoint, expected_status, data=None, params=None):
        """Run a single API test"""
        url = f"{self.api_url}/{endpoint}"
        headers = {'Content-Type': 'application/json'}
        
        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        print(f"   URL: {url}")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, params=params)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers, params=params)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=headers, params=params)

            success = response.status_code == expected_status
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                try:
                    return True, response.json()
                except:
                    return True, {}
            else:
                print(f"❌ Failed - Expected {expected_status}, got {response.status_code}")
                try:
                    print(f"   Response: {response.text}")
                except:
                    pass
                return False, {}

        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            return False, {}

    def test_health_check(self):
        """Test API health endpoints"""
        print("\n=== HEALTH CHECK TESTS ===")
        self.run_test("API Root", "GET", "", 200)
        self.run_test("Health Check", "GET", "health", 200)

    def test_packages(self):
        """Test packages endpoint"""
        print("\n=== PACKAGES TESTS ===")
        success, packages = self.run_test("Get Packages", "GET", "packages", 200)
        if success and packages:
            expected_packages = ['basic', 'premium', 'professional']
            for pkg in expected_packages:
                if pkg in packages:
                    print(f"✅ Package {pkg} found: ${packages[pkg]['price']}")
                else:
                    print(f"❌ Package {pkg} missing")

    def test_user_registration(self):
        """Test user registration for both buyer and inspector"""
        print("\n=== USER REGISTRATION TESTS ===")
        
        # Test buyer registration
        timestamp = datetime.now().strftime('%H%M%S')
        buyer_data = {
            "email": f"buyer_{timestamp}@test.com",
            "password": "TestPass123!",
            "full_name": f"Test Buyer {timestamp}",
            "phone": "+1234567890",
            "user_type": "buyer"
        }
        
        success, buyer_response = self.run_test("Register Buyer", "POST", "auth/register", 200, buyer_data)
        if success:
            self.buyer_user = buyer_response
            print(f"✅ Buyer registered: {buyer_response.get('id')}")
        
        # Test inspector registration
        inspector_data = {
            "email": f"inspector_{timestamp}@test.com",
            "password": "TestPass123!",
            "full_name": f"Test Inspector {timestamp}",
            "phone": "+1234567891",
            "user_type": "inspector"
        }
        
        success, inspector_response = self.run_test("Register Inspector", "POST", "auth/register", 200, inspector_data)
        if success:
            self.inspector_user = inspector_response
            print(f"✅ Inspector registered: {inspector_response.get('id')}")

        # Test duplicate email
        self.run_test("Duplicate Email", "POST", "auth/register", 400, buyer_data)

    def test_user_login(self):
        """Test user login"""
        print("\n=== USER LOGIN TESTS ===")
        
        if self.buyer_user:
            login_data = {
                "email": self.buyer_user['email'],
                "password": "TestPass123!"
            }
            success, response = self.run_test("Buyer Login", "POST", "auth/login", 200, login_data)
            if success:
                print(f"✅ Buyer login successful: {response.get('user_type')}")

        if self.inspector_user:
            login_data = {
                "email": self.inspector_user['email'],
                "password": "TestPass123!"
            }
            success, response = self.run_test("Inspector Login", "POST", "auth/login", 200, login_data)
            if success:
                print(f"✅ Inspector login successful: {response.get('user_type')}")

        # Test invalid credentials
        invalid_data = {"email": "invalid@test.com", "password": "wrong"}
        self.run_test("Invalid Login", "POST", "auth/login", 401, invalid_data)

    def test_inspector_verification(self):
        """Test inspector ID verification (mocked)"""
        print("\n=== INSPECTOR VERIFICATION TESTS ===")
        
        if self.inspector_user:
            # Get inspector profile
            success, profile = self.run_test(
                "Get Inspector Profile", 
                "GET", 
                f"inspector/profile/{self.inspector_user['id']}", 
                200
            )
            if success:
                print(f"✅ Inspector profile found, verified: {profile.get('id_verified')}")
            
            # Verify inspector ID (mocked)
            success, response = self.run_test(
                "Verify Inspector ID", 
                "POST", 
                f"inspector/verify-id/{self.inspector_user['id']}", 
                200
            )
            if success:
                print("✅ Inspector ID verification successful (mocked)")

    def test_inspection_workflow(self):
        """Test complete inspection workflow"""
        print("\n=== INSPECTION WORKFLOW TESTS ===")
        
        if not self.buyer_user:
            print("❌ No buyer user available for inspection tests")
            return

        # Create inspection request
        inspection_data = {
            "vehicle": {
                "make": "Toyota",
                "model": "Camry",
                "year": 2020,
                "vin": "1HGBH41JXMN109186",
                "color": "Silver",
                "mileage": 50000
            },
            "seller": {
                "name": "John Seller",
                "phone": "+1234567892",
                "address": "123 Main St",
                "city": "Chicago",
                "state": "IL",
                "zip_code": "60601",
                "lat": 41.8781,
                "lng": -87.6298
            },
            "package_type": "premium",
            "tip_amount": 20.0,
            "preferred_date": "2024-01-15",
            "notes": "Please check the engine carefully"
        }

        success, inspection_response = self.run_test(
            "Create Inspection Request", 
            "POST", 
            f"inspections?buyer_id={self.buyer_user['id']}", 
            200, 
            inspection_data
        )
        
        if success:
            self.inspection_id = inspection_response.get('id')
            self.security_code = inspection_response.get('security_code')
            print(f"✅ Inspection created: {self.inspection_id}")
            print(f"✅ Security code: {self.security_code}")

        # Get buyer inspections
        if self.buyer_user:
            success, inspections = self.run_test(
                "Get Buyer Inspections", 
                "GET", 
                f"inspections/buyer/{self.buyer_user['id']}", 
                200
            )
            if success:
                print(f"✅ Found {len(inspections)} inspections for buyer")

        # Get available jobs for inspector
        success, available_jobs = self.run_test(
            "Get Available Jobs", 
            "GET", 
            "inspections/available", 
            200,
            params={"inspector_lat": 41.8781, "inspector_lng": -87.6298, "radius": 50}
        )
        if success:
            print(f"✅ Found {len(available_jobs)} available jobs")

        # Accept job as inspector
        if self.inspection_id and self.inspector_user:
            success, response = self.run_test(
                "Accept Inspection Job", 
                "POST", 
                f"inspections/{self.inspection_id}/accept?inspector_id={self.inspector_user['id']}", 
                200
            )
            if success:
                print("✅ Inspection job accepted by inspector")

        # Verify security code
        if self.inspection_id and self.security_code:
            success, response = self.run_test(
                "Verify Security Code", 
                "POST", 
                f"inspections/{self.inspection_id}/verify-code?code={self.security_code}", 
                200
            )
            if success:
                print("✅ Security code verified, inspection started")

        # Get inspection progress
        if self.inspection_id:
            success, progress = self.run_test(
                "Get Inspection Progress", 
                "GET", 
                f"inspections/{self.inspection_id}/progress", 
                200
            )
            if success:
                print(f"✅ Inspection progress retrieved, steps: {len(progress.get('steps', []))}")

        # Complete a step
        if self.inspection_id:
            success, response = self.run_test(
                "Complete Inspection Step", 
                "POST", 
                f"inspections/{self.inspection_id}/complete-step?step_name=exterior_front&notes=Front looks good", 
                200
            )
            if success:
                print("✅ Inspection step completed")

        # Submit report
        if self.inspection_id:
            report_data = {
                "inspection_id": self.inspection_id,
                "steps": [
                    {
                        "step_name": "exterior_front",
                        "description": "Front view inspection",
                        "completed": True,
                        "photos": [],
                        "notes": "Front looks good"
                    }
                ],
                "overall_notes": "Vehicle is in good condition overall",
                "recommendation": "buy"
            }
            
            success, response = self.run_test(
                "Submit Inspection Report", 
                "POST", 
                f"inspections/{self.inspection_id}/submit-report", 
                200,
                report_data
            )
            if success:
                report_id = response.get('report_id')
                print(f"✅ Inspection report submitted: {report_id}")
                
                # Get the report
                if report_id:
                    success, report = self.run_test(
                        "Get Report", 
                        "GET", 
                        f"reports/{report_id}", 
                        200
                    )
                    if success:
                        print(f"✅ Report retrieved: {report.get('recommendation')}")

    def test_notifications(self):
        """Test notifications system"""
        print("\n=== NOTIFICATIONS TESTS ===")
        
        if self.buyer_user:
            success, notifications = self.run_test(
                "Get Buyer Notifications", 
                "GET", 
                f"notifications/{self.buyer_user['id']}", 
                200
            )
            if success:
                print(f"✅ Found {len(notifications)} notifications for buyer")
                
                # Mark first notification as read if exists
                if notifications:
                    notif_id = notifications[0]['id']
                    success, response = self.run_test(
                        "Mark Notification Read", 
                        "POST", 
                        f"notifications/{notif_id}/read", 
                        200
                    )
                    if success:
                        print("✅ Notification marked as read")

        if self.inspector_user:
            success, notifications = self.run_test(
                "Get Inspector Notifications", 
                "GET", 
                f"notifications/{self.inspector_user['id']}", 
                200
            )
            if success:
                print(f"✅ Found {len(notifications)} notifications for inspector")

    def test_inspector_jobs(self):
        """Test inspector job management"""
        print("\n=== INSPECTOR JOBS TESTS ===")
        
        if self.inspector_user:
            success, jobs = self.run_test(
                "Get Inspector Jobs", 
                "GET", 
                f"inspector/jobs/{self.inspector_user['id']}", 
                200
            )
            if success:
                print(f"✅ Found {len(jobs)} jobs for inspector")

    def run_all_tests(self):
        """Run all API tests"""
        print("🚀 Starting AutoCheck API Tests...")
        print(f"Base URL: {self.base_url}")
        
        try:
            self.test_health_check()
            self.test_packages()
            self.test_user_registration()
            self.test_user_login()
            self.test_inspector_verification()
            self.test_inspection_workflow()
            self.test_notifications()
            self.test_inspector_jobs()
            
        except Exception as e:
            print(f"\n❌ Test suite failed with error: {str(e)}")
            return False

        # Print final results
        print(f"\n📊 Final Results:")
        print(f"Tests run: {self.tests_run}")
        print(f"Tests passed: {self.tests_passed}")
        print(f"Success rate: {(self.tests_passed/self.tests_run*100):.1f}%")
        
        return self.tests_passed == self.tests_run

def main():
    tester = AutoCheckAPITester()
    success = tester.run_all_tests()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())