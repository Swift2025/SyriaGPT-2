"""
Configuration file for API endpoint testing
"""

import os
from typing import Dict, Any

class TestConfig:
    """Configuration settings for API testing"""
    
    # Base configuration
    BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")
    TIMEOUT = int(os.getenv("API_TIMEOUT", "30"))
    MAX_RETRIES = int(os.getenv("API_MAX_RETRIES", "3"))
    
    # Test data configuration
    TEST_USER_EMAIL_DOMAIN = "test.example.com"
    TEST_USER_PASSWORD = "TestPassword123!"
    
    # Logging configuration
    LOG_LEVEL = os.getenv("TEST_LOG_LEVEL", "INFO")
    LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # Output configuration
    OUTPUT_DIR = os.getenv("TEST_OUTPUT_DIR", "test_results")
    SAVE_DETAILED_LOGS = os.getenv("SAVE_DETAILED_LOGS", "true").lower() == "true"
    
    # Test execution configuration
    SKIP_CLEANUP = os.getenv("SKIP_CLEANUP", "false").lower() == "true"
    PARALLEL_TESTS = os.getenv("PARALLEL_TESTS", "false").lower() == "true"
    
    # Endpoint groups to test
    ENABLED_TEST_GROUPS = {
        "health": True,
        "authentication": True,
        "user_management": True,
        "questions": True,
        "answers": True,
        "chat": True,
        "intelligent_qa": True,
        "session": True,
        "smtp": True
    }
    
    # Specific endpoints to skip (if any)
    SKIP_ENDPOINTS = [
        # Add specific endpoints to skip here
        # Example: "/auth/oauth/google/authorize"
    ]
    
    # Performance thresholds
    PERFORMANCE_THRESHOLDS = {
        "max_response_time_ms": 5000,  # 5 seconds
        "warning_response_time_ms": 2000,  # 2 seconds
        "critical_response_time_ms": 10000  # 10 seconds
    }
    
    @classmethod
    def get_test_data_config(cls) -> Dict[str, Any]:
        """Get test data configuration"""
        return {
            "user_registration": {
                "email_domain": cls.TEST_USER_EMAIL_DOMAIN,
                "password": cls.TEST_USER_PASSWORD,
                "required_fields": ["email", "password", "username", "first_name", "last_name"]
            },
            "question_data": {
                "categories": ["history", "culture", "economy", "government", "general"],
                "tags": ["syria", "test", "api"]
            },
            "chat_data": {
                "message_types": ["user", "assistant", "system"],
                "max_message_length": 1000
            }
        }
    
    @classmethod
    def get_environment_info(cls) -> Dict[str, str]:
        """Get environment information for test reports"""
        return {
            "base_url": cls.BASE_URL,
            "timeout": str(cls.TIMEOUT),
            "max_retries": str(cls.MAX_RETRIES),
            "log_level": cls.LOG_LEVEL,
            "output_dir": cls.OUTPUT_DIR,
            "python_version": os.sys.version,
            "platform": os.name
        }
