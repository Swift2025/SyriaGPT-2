#!/usr/bin/env python3
"""
Comprehensive API Endpoint Testing Framework for SyriaGPT
Tests all endpoints and logs results in structured format
"""

import asyncio
import json
import logging
import time
from datetime import datetime
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict
import httpx
import uuid

# Configure structured logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class TestResult:
    """Structured test result data"""
    endpoint: str
    method: str
    status_code: int
    response_time_ms: float
    success: bool
    error_message: Optional[str] = None
    response_data: Optional[Dict[str, Any]] = None
    request_data: Optional[Dict[str, Any]] = None
    headers: Optional[Dict[str, str]] = None
    timestamp: str = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now().isoformat()

@dataclass
class TestSummary:
    """Test execution summary"""
    total_tests: int
    passed_tests: int
    failed_tests: int
    total_time_seconds: float
    start_time: str
    end_time: str
    success_rate: float
    results: List[TestResult]

class APITester:
    """Comprehensive API endpoint tester"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url.rstrip('/')
        self.client = httpx.AsyncClient(timeout=30.0)
        self.test_results: List[TestResult] = []
        self.auth_token: Optional[str] = None
        self.test_user_id: Optional[str] = None
        self.test_chat_id: Optional[str] = None
        self.test_question_id: Optional[str] = None
        self.test_answer_id: Optional[str] = None
        self.test_session_id: Optional[str] = None
        
        # Test data generators
        self.test_email = f"test_{uuid.uuid4().hex[:8]}@example.com"
        self.test_password = "TestPassword123!"
        self.test_username = f"testuser_{uuid.uuid4().hex[:6]}"
        
    async def __aenter__(self):
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()
    
    def generate_test_data(self, data_type: str) -> Dict[str, Any]:
        """Generate test data for different endpoint types"""
        generators = {
            "user_registration": {
                "email": self.test_email,
                "password": self.test_password,
                "username": self.test_username,
                "first_name": "Test",
                "last_name": "User",
                "phone": "+1234567890"
            },
            "user_login": {
                "email": self.test_email,
                "password": self.test_password
            },
            "question_create": {
                "title": f"Test Question {uuid.uuid4().hex[:6]}",
                "content": "This is a test question about Syria's history and culture.",
                "category": "history",
                "tags": ["syria", "history", "test"]
            },
            "answer_create": {
                "content": "This is a test answer providing information about Syria.",
                "is_verified": False
            },
            "chat_create": {
                "title": f"Test Chat {uuid.uuid4().hex[:6]}",
                "description": "Test chat session for API testing"
            },
            "chat_message": {
                "content": "Hello, this is a test message for the chat system.",
                "message_type": "user"
            },
            "session_create": {
                "name": f"Test Session {uuid.uuid4().hex[:6]}",
                "description": "Test session for API testing"
            },
            "smtp_test": {
                "provider": "gmail",
                "email": "test@example.com",
                "subject": "Test Email",
                "message": "This is a test email from SyriaGPT API testing."
            }
        }
        return generators.get(data_type, {})
    
    async def make_request(
        self, 
        method: str, 
        endpoint: str, 
        data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        params: Optional[Dict[str, Any]] = None
    ) -> TestResult:
        """Make HTTP request and return structured test result"""
        url = f"{self.base_url}{endpoint}"
        start_time = time.time()
        
        # Add auth token if available
        request_headers = headers or {}
        if self.auth_token and "Authorization" not in request_headers:
            request_headers["Authorization"] = f"Bearer {self.auth_token}"
        
        try:
            if method.upper() == "GET":
                response = await self.client.get(url, headers=request_headers, params=params)
            elif method.upper() == "POST":
                response = await self.client.post(url, json=data, headers=request_headers, params=params)
            elif method.upper() == "PUT":
                response = await self.client.put(url, json=data, headers=request_headers, params=params)
            elif method.upper() == "DELETE":
                response = await self.client.delete(url, headers=request_headers, params=params)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            response_time = (time.time() - start_time) * 1000
            
            # Parse response data
            try:
                response_data = response.json()
            except (ValueError, TypeError):
                response_data = {"raw_response": response.text}
            
            success = 200 <= response.status_code < 300
            
            result = TestResult(
                endpoint=endpoint,
                method=method.upper(),
                status_code=response.status_code,
                response_time_ms=response_time,
                success=success,
                response_data=response_data,
                request_data=data,
                headers=request_headers
            )
            
            if not success:
                result.error_message = response_data.get("detail", f"HTTP {response.status_code}")
            
            return result
            
        except (httpx.RequestError, httpx.TimeoutException, ValueError) as e:
            response_time = (time.time() - start_time) * 1000
            return TestResult(
                endpoint=endpoint,
                method=method.upper(),
                status_code=0,
                response_time_ms=response_time,
                success=False,
                error_message=str(e),
                request_data=data,
                headers=request_headers
            )
    
    async def test_health_endpoints(self):
        """Test health and system endpoints"""
        logger.info("Testing health and system endpoints...")
        
        health_endpoints = [
            ("GET", "/test/health"),
            ("GET", "/health"),
            ("GET", "/version"),
            ("GET", "/system/info")
        ]
        
        for method, endpoint in health_endpoints:
            result = await self.make_request(method, endpoint)
            self.test_results.append(result)
            logger.info("%s %s - Status: %s, Time: %.2fms", method, endpoint, result.status_code, result.response_time_ms)
    
    async def test_authentication_endpoints(self):
        """Test authentication endpoints"""
        logger.info("Testing authentication endpoints...")
        
        # Test registration
        reg_data = self.generate_test_data("user_registration")
        reg_result = await self.make_request("POST", "/auth/register", reg_data)
        self.test_results.append(reg_result)
        logger.info("POST /auth/register - Status: %s", reg_result.status_code)
        
        # Test login
        login_data = self.generate_test_data("user_login")
        login_result = await self.make_request("POST", "/auth/login", login_data)
        self.test_results.append(login_result)
        logger.info("POST /auth/login - Status: %s", login_result.status_code)
        
        if login_result.success and login_result.response_data:
            self.auth_token = login_result.response_data.get("access_token")
            self.test_user_id = login_result.response_data.get("user", {}).get("id")
            logger.info("Authentication token obtained for protected endpoint testing")
        
        # Test OAuth providers
        oauth_result = await self.make_request("GET", "/auth/oauth/providers")
        self.test_results.append(oauth_result)
        logger.info("GET /auth/oauth/providers - Status: %s", oauth_result.status_code)
        
        # Test forgot password
        forgot_data = {"email": self.test_email}
        forgot_result = await self.make_request("POST", "/auth/forgot-password", forgot_data)
        self.test_results.append(forgot_result)
        logger.info("POST /auth/forgot-password - Status: %s", forgot_result.status_code)
        
        # Test protected endpoint (get current user)
        if self.auth_token:
            me_result = await self.make_request("GET", "/auth/me")
            self.test_results.append(me_result)
            logger.info("GET /auth/me - Status: %s", me_result.status_code)
    
    async def test_user_management_endpoints(self):
        """Test user management endpoints"""
        if not self.auth_token:
            logger.warning("Skipping user management tests - no auth token")
            return
            
        logger.info("Testing user management endpoints...")
        
        # Test user profile endpoints
        profile_endpoints = [
            ("GET", "/users/me/profile"),
            ("GET", "/users/me/settings"),
            ("GET", "/users/stats")
        ]
        
        for method, endpoint in profile_endpoints:
            result = await self.make_request(method, endpoint)
            self.test_results.append(result)
            logger.info("%s %s - Status: %s", method, endpoint, result.status_code)
        
        # Test user search (admin endpoint)
        search_result = await self.make_request("GET", "/users/", params={"page": 1, "limit": 10})
        self.test_results.append(search_result)
        logger.info("GET /users/ - Status: %s", search_result.status_code)
        
        # Test profile update
        update_data = {
            "first_name": "Updated",
            "last_name": "User",
            "bio": "Updated bio for testing"
        }
        update_result = await self.make_request("PUT", "/users/me/profile", update_data)
        self.test_results.append(update_result)
        logger.info("PUT /users/me/profile - Status: %s", update_result.status_code)
        
        # Test password change
        password_data = {
            "current_password": self.test_password,
            "new_password": "NewTestPassword123!"
        }
        password_result = await self.make_request("POST", "/users/me/change-password", password_data)
        self.test_results.append(password_result)
        logger.info("POST /users/me/change-password - Status: %s", password_result.status_code)
    
    async def test_questions_endpoints(self):
        """Test questions endpoints"""
        logger.info("Testing questions endpoints...")
        
        # Test get all questions
        questions_result = await self.make_request("GET", "/questions/")
        self.test_results.append(questions_result)
        logger.info("GET /questions/ - Status: %s", questions_result.status_code)
        
        # Test create question
        if self.auth_token:
            question_data = self.generate_test_data("question_create")
            create_result = await self.make_request("POST", "/questions/", question_data)
            self.test_results.append(create_result)
            logger.info("POST /questions/ - Status: %s", create_result.status_code)
            
            if create_result.success and create_result.response_data:
                self.test_question_id = create_result.response_data.get("id")
                
                # Test get specific question
                if self.test_question_id:
                    get_result = await self.make_request("GET", f"/questions/{self.test_question_id}")
                    self.test_results.append(get_result)
                    logger.info("GET /questions/%s - Status: %s", self.test_question_id, get_result.status_code)
                    
                    # Test update question
                    update_data = {"title": "Updated Test Question", "content": "Updated content"}
                    update_result = await self.make_request("PUT", f"/questions/{self.test_question_id}", update_data)
                    self.test_results.append(update_result)
                    logger.info("PUT /questions/%s - Status: %s", self.test_question_id, update_result.status_code)
    
    async def test_answers_endpoints(self):
        """Test answers endpoints"""
        logger.info("Testing answers endpoints...")
        
        # Test get all answers
        answers_result = await self.make_request("GET", "/answers/")
        self.test_results.append(answers_result)
        logger.info("GET /answers/ - Status: %s", answers_result.status_code)
        
        # Test create answer
        if self.auth_token and self.test_question_id:
            answer_data = self.generate_test_data("answer_create")
            answer_data["question_id"] = self.test_question_id
            
            create_result = await self.make_request("POST", "/answers/", answer_data)
            self.test_results.append(create_result)
            logger.info("POST /answers/ - Status: %s", create_result.status_code)
            
            if create_result.success and create_result.response_data:
                self.test_answer_id = create_result.response_data.get("id")
                
                # Test get answers by question
                get_result = await self.make_request("GET", f"/questions/{self.test_question_id}/answers")
                self.test_results.append(get_result)
                logger.info("GET /questions/%s/answers - Status: %s", self.test_question_id, get_result.status_code)
                
                # Test update answer
                if self.test_answer_id:
                    update_data = {"content": "Updated test answer content"}
                    update_result = await self.make_request("PUT", f"/answers/{self.test_answer_id}", update_data)
                    self.test_results.append(update_result)
                    logger.info("PUT /answers/%s - Status: %s", self.test_answer_id, update_result.status_code)
    
    async def test_chat_endpoints(self):
        """Test chat management endpoints"""
        if not self.auth_token:
            logger.warning("Skipping chat tests - no auth token")
            return
            
        logger.info("Testing chat management endpoints...")
        
        # Test get all chats
        chats_result = await self.make_request("GET", "/chat/")
        self.test_results.append(chats_result)
        logger.info("GET /chat/ - Status: %s", chats_result.status_code)
        
        # Test create chat
        chat_data = self.generate_test_data("chat_create")
        create_result = await self.make_request("POST", "/chat/", chat_data)
        self.test_results.append(create_result)
        logger.info("POST /chat/ - Status: %s", create_result.status_code)
        
        if create_result.success and create_result.response_data:
            self.test_chat_id = create_result.response_data.get("id")
            
            # Test get specific chat
            if self.test_chat_id:
                get_result = await self.make_request("GET", f"/chat/{self.test_chat_id}")
                self.test_results.append(get_result)
                logger.info("GET /chat/%s - Status: %s", self.test_chat_id, get_result.status_code)
                
                # Test send message
                message_data = self.generate_test_data("chat_message")
                message_result = await self.make_request("POST", f"/chat/{self.test_chat_id}/messages", message_data)
                self.test_results.append(message_result)
                logger.info("POST /chat/%s/messages - Status: %s", self.test_chat_id, message_result.status_code)
                
                # Test get chat messages
                messages_result = await self.make_request("GET", f"/chat/{self.test_chat_id}/messages")
                self.test_results.append(messages_result)
                logger.info("GET /chat/%s/messages - Status: %s", self.test_chat_id, messages_result.status_code)
                
                # Test update chat
                update_data = {"title": "Updated Test Chat", "description": "Updated description"}
                update_result = await self.make_request("PUT", f"/chat/{self.test_chat_id}", update_data)
                self.test_results.append(update_result)
                logger.info("PUT /chat/%s - Status: %s", self.test_chat_id, update_result.status_code)
    
    async def test_intelligent_qa_endpoints(self):
        """Test intelligent Q&A endpoints"""
        if not self.auth_token:
            logger.warning("Skipping intelligent Q&A tests - no auth token")
            return
            
        logger.info("Testing intelligent Q&A endpoints...")
        
        # Test ask question
        ask_result = await self.make_request(
            "POST", 
            "/intelligent-qa/ask", 
            params={"question": "What is the capital of Syria?", "language": "en"}
        )
        self.test_results.append(ask_result)
        logger.info("POST /intelligent-qa/ask - Status: %s", ask_result.status_code)
        
        # Test question variants
        variants_result = await self.make_request(
            "POST",
            "/intelligent-qa/augment-variants",
            params={"question": "Tell me about Syria's history"}
        )
        self.test_results.append(variants_result)
        logger.info("POST /intelligent-qa/augment-variants - Status: %s", variants_result.status_code)
    
    async def test_session_endpoints(self):
        """Test session management endpoints"""
        if not self.auth_token:
            logger.warning("Skipping session tests - no auth token")
            return
            
        logger.info("Testing session management endpoints...")
        
        # Test get user sessions
        sessions_result = await self.make_request("GET", "/sessions/")
        self.test_results.append(sessions_result)
        logger.info("GET /sessions/ - Status: %s", sessions_result.status_code)
        
        # Test create session
        session_data = self.generate_test_data("session_create")
        create_result = await self.make_request("POST", "/sessions/", session_data)
        self.test_results.append(create_result)
        logger.info("POST /sessions/ - Status: %s", create_result.status_code)
        
        if create_result.success and create_result.response_data:
            self.test_session_id = create_result.response_data.get("id")
            
            # Test get specific session
            if self.test_session_id:
                get_result = await self.make_request("GET", f"/sessions/{self.test_session_id}")
                self.test_results.append(get_result)
                logger.info("GET /sessions/%s - Status: %s", self.test_session_id, get_result.status_code)
                
                # Test update session
                update_data = {"name": "Updated Test Session", "description": "Updated description"}
                update_result = await self.make_request("PUT", f"/sessions/{self.test_session_id}", update_data)
                self.test_results.append(update_result)
                logger.info("PUT /sessions/%s - Status: %s", self.test_session_id, update_result.status_code)
        
        # Test logout session
        logout_data = {"session_id": self.test_session_id or "test_session"}
        logout_result = await self.make_request("POST", "/sessions/logout", logout_data)
        self.test_results.append(logout_result)
        logger.info("POST /sessions/logout - Status: %s", logout_result.status_code)
    
    async def test_smtp_endpoints(self):
        """Test SMTP configuration endpoints"""
        logger.info("Testing SMTP endpoints...")
        
        # Test get SMTP providers
        providers_result = await self.make_request("GET", "/smtp/providers")
        self.test_results.append(providers_result)
        logger.info("GET /smtp/providers - Status: %s", providers_result.status_code)
        
        # Test get specific provider
        provider_result = await self.make_request("GET", "/smtp/providers/gmail")
        self.test_results.append(provider_result)
        logger.info("GET /smtp/providers/gmail - Status: %s", provider_result.status_code)
        
        # Test SMTP health
        health_result = await self.make_request("GET", "/smtp/health")
        self.test_results.append(health_result)
        logger.info("GET /smtp/health - Status: %s", health_result.status_code)
        
        # Test SMTP test (if authenticated)
        if self.auth_token:
            smtp_data = self.generate_test_data("smtp_test")
            test_result = await self.make_request("POST", "/smtp/test", smtp_data)
            self.test_results.append(test_result)
            logger.info("POST /smtp/test - Status: %s", test_result.status_code)
    
    async def cleanup_test_data(self):
        """Clean up test data created during testing"""
        logger.info("Cleaning up test data...")
        
        # Delete test chat
        if self.test_chat_id:
            delete_result = await self.make_request("DELETE", f"/chat/{self.test_chat_id}")
            self.test_results.append(delete_result)
            logger.info("DELETE /chat/%s - Status: %s", self.test_chat_id, delete_result.status_code)
        
        # Delete test session
        if self.test_session_id:
            delete_result = await self.make_request("DELETE", f"/sessions/{self.test_session_id}")
            self.test_results.append(delete_result)
            logger.info("DELETE /sessions/%s - Status: %s", self.test_session_id, delete_result.status_code)
        
        # Delete test answer
        if self.test_answer_id:
            delete_result = await self.make_request("DELETE", f"/answers/{self.test_answer_id}")
            self.test_results.append(delete_result)
            logger.info("DELETE /answers/%s - Status: %s", self.test_answer_id, delete_result.status_code)
        
        # Delete test question
        if self.test_question_id:
            delete_result = await self.make_request("DELETE", f"/questions/{self.test_question_id}")
            self.test_results.append(delete_result)
            logger.info("DELETE /questions/%s - Status: %s", self.test_question_id, delete_result.status_code)
    
    async def run_all_tests(self) -> TestSummary:
        """Run all endpoint tests"""
        start_time = datetime.now()
        logger.info("Starting comprehensive API endpoint testing...")
        
        try:
            # Run all test suites
            await self.test_health_endpoints()
            await self.test_authentication_endpoints()
            await self.test_user_management_endpoints()
            await self.test_questions_endpoints()
            await self.test_answers_endpoints()
            await self.test_chat_endpoints()
            await self.test_intelligent_qa_endpoints()
            await self.test_session_endpoints()
            await self.test_smtp_endpoints()
            
            # Cleanup test data
            await self.cleanup_test_data()
            
        except (httpx.RequestError, httpx.TimeoutException, ValueError, KeyError) as e:
            logger.error("Error during testing: %s", e)
        
        end_time = datetime.now()
        total_time = (end_time - start_time).total_seconds()
        
        # Calculate summary
        passed_tests = sum(1 for result in self.test_results if result.success)
        failed_tests = len(self.test_results) - passed_tests
        success_rate = (passed_tests / len(self.test_results) * 100) if self.test_results else 0
        
        summary = TestSummary(
            total_tests=len(self.test_results),
            passed_tests=passed_tests,
            failed_tests=failed_tests,
            total_time_seconds=total_time,
            start_time=start_time.isoformat(),
            end_time=end_time.isoformat(),
            success_rate=success_rate,
            results=self.test_results
        )
        
        return summary
    
    def save_results_to_file(self, summary: TestSummary, filename: str = None):
        """Save test results to structured JSON file"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"api_test_results_{timestamp}.json"
        
        # Convert to serializable format
        results_data = {
            "test_summary": asdict(summary),
            "test_metadata": {
                "base_url": self.base_url,
                "test_user_email": self.test_email,
                "test_username": self.test_username,
                "framework_version": "1.0.0"
            }
        }
        
        # Save to file
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(results_data, f, indent=2, ensure_ascii=False)
        
        logger.info("Test results saved to: %s", filename)
        return filename

async def main():
    """Main test execution function"""
    base_url = "http://localhost:8000"  # Adjust as needed
    
    async with APITester(base_url) as tester:
        summary = await tester.run_all_tests()
        
        # Print summary
        print("\n" + "="*80)
        print("API ENDPOINT TESTING SUMMARY")
        print("="*80)
        print(f"Total Tests: {summary.total_tests}")
        print(f"Passed: {summary.passed_tests}")
        print(f"Failed: {summary.failed_tests}")
        print(f"Success Rate: {summary.success_rate:.2f}%")
        print(f"Total Time: {summary.total_time_seconds:.2f} seconds")
        print(f"Start Time: {summary.start_time}")
        print(f"End Time: {summary.end_time}")
        print("="*80)
        
        # Show failed tests
        failed_tests = [r for r in summary.results if not r.success]
        if failed_tests:
            print("\nFAILED TESTS:")
            print("-" * 40)
            for test in failed_tests:
                print(f"{test.method} {test.endpoint} - {test.status_code} - {test.error_message}")
        
        # Save results
        filename = tester.save_results_to_file(summary)
        print(f"\nDetailed results saved to: {filename}")

if __name__ == "__main__":
    asyncio.run(main())
