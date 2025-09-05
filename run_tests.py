#!/usr/bin/env python3
"""
Enhanced API Test Runner with Advanced Logging and Reporting
"""

import asyncio
import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Any
import argparse

from test_endpoints import APITester, TestSummary
from test_config import TestConfig

# Setup logging
logging.basicConfig(
    level=getattr(logging, TestConfig.LOG_LEVEL),
    format=TestConfig.LOG_FORMAT,
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(f"api_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
    ]
)
logger = logging.getLogger(__name__)

class EnhancedAPITester(APITester):
    """Enhanced API tester with advanced logging and reporting"""
    
    def __init__(self, base_url: str = None, config: TestConfig = None):
        super().__init__(base_url or TestConfig.BASE_URL)
        self.config = config or TestConfig
        self.performance_metrics = []
        self.error_categories = {}
        self.endpoint_coverage = {}
        
    async def log_test_result(self, result):
        """Enhanced logging for test results"""
        status_emoji = "✅" if result.success else "❌"
        performance_indicator = ""
        
        if result.response_time_ms > self.config.PERFORMANCE_THRESHOLDS["critical_response_time_ms"]:
            performance_indicator = "🐌 CRITICAL"
        elif result.response_time_ms > self.config.PERFORMANCE_THRESHOLDS["warning_response_time_ms"]:
            performance_indicator = "⚠️ SLOW"
        elif result.response_time_ms < 100:
            performance_indicator = "⚡ FAST"
        
        logger.info(
            "%s %s %s - Status: %s - Time: %.2fms %s",
            status_emoji, result.method, result.endpoint, result.status_code, 
            result.response_time_ms, performance_indicator
        )
        
        if not result.success:
            error_key = f"{result.status_code}_{result.error_message}"
            self.error_categories[error_key] = self.error_categories.get(error_key, 0) + 1
            logger.error("   Error: %s", result.error_message)
        
        # Track performance metrics
        self.performance_metrics.append({
            "endpoint": result.endpoint,
            "method": result.method,
            "response_time": result.response_time_ms,
            "status_code": result.status_code,
            "success": result.success
        })
        
        # Track endpoint coverage
        endpoint_key = f"{result.method} {result.endpoint}"
        self.endpoint_coverage[endpoint_key] = {
            "tested": True,
            "success": result.success,
            "last_test_time": result.timestamp
        }
    
    async def make_request(self, method: str, endpoint: str, data: Dict[str, Any] = None, 
                          headers: Dict[str, str] = None, params: Dict[str, Any] = None):
        """Override to add enhanced logging"""
        result = await super().make_request(method, endpoint, data, headers, params)
        await self.log_test_result(result)
        return result
    
    def generate_performance_report(self) -> Dict[str, Any]:
        """Generate performance analysis report"""
        if not self.performance_metrics:
            return {}
        
        response_times = [m["response_time"] for m in self.performance_metrics]
        
        return {
            "average_response_time_ms": sum(response_times) / len(response_times),
            "min_response_time_ms": min(response_times),
            "max_response_time_ms": max(response_times),
            "slowest_endpoints": sorted(
                self.performance_metrics, 
                key=lambda x: x["response_time"], 
                reverse=True
            )[:5],
            "fastest_endpoints": sorted(
                self.performance_metrics, 
                key=lambda x: x["response_time"]
            )[:5],
            "performance_distribution": {
                "under_100ms": len([t for t in response_times if t < 100]),
                "100ms_to_500ms": len([t for t in response_times if 100 <= t < 500]),
                "500ms_to_1000ms": len([t for t in response_times if 500 <= t < 1000]),
                "over_1000ms": len([t for t in response_times if t >= 1000])
            }
        }
    
    def generate_error_analysis(self) -> Dict[str, Any]:
        """Generate error analysis report"""
        return {
            "total_errors": sum(self.error_categories.values()),
            "error_categories": self.error_categories,
            "most_common_errors": sorted(
                self.error_categories.items(), 
                key=lambda x: x[1], 
                reverse=True
            )[:5],
            "error_rate_by_endpoint": {
                endpoint: {
                    "total_tests": len([r for r in self.test_results if r.endpoint == endpoint.split()[1]]),
                    "errors": len([r for r in self.test_results if not r.success and r.endpoint == endpoint.split()[1]]),
                    "error_rate": len([r for r in self.test_results if not r.success and r.endpoint == endpoint.split()[1]]) / 
                                len([r for r in self.test_results if r.endpoint == endpoint.split()[1]]) * 100
                }
                for endpoint in self.endpoint_coverage.keys()
            }
        }
    
    def generate_coverage_report(self) -> Dict[str, Any]:
        """Generate endpoint coverage report"""
        total_endpoints = len(self.endpoint_coverage)
        successful_endpoints = len([e for e in self.endpoint_coverage.values() if e["success"]])
        
        return {
            "total_endpoints_tested": total_endpoints,
            "successful_endpoints": successful_endpoints,
            "coverage_percentage": (successful_endpoints / total_endpoints * 100) if total_endpoints > 0 else 0,
            "endpoint_details": self.endpoint_coverage,
            "untested_endpoints": [
                endpoint for endpoint, details in self.endpoint_coverage.items() 
                if not details["tested"]
            ]
        }
    
    async def run_all_tests(self) -> TestSummary:
        """Run all tests with enhanced reporting"""
        logger.info("🚀 Starting Enhanced API Endpoint Testing...")
        logger.info("📊 Configuration: %s", self.config.get_environment_info())
        
        start_time = datetime.now()
        
        try:
            # Run test suites based on configuration
            if self.config.ENABLED_TEST_GROUPS.get("health", True):
                await self.test_health_endpoints()
            
            if self.config.ENABLED_TEST_GROUPS.get("authentication", True):
                await self.test_authentication_endpoints()
            
            if self.config.ENABLED_TEST_GROUPS.get("user_management", True):
                await self.test_user_management_endpoints()
            
            if self.config.ENABLED_TEST_GROUPS.get("questions", True):
                await self.test_questions_endpoints()
            
            if self.config.ENABLED_TEST_GROUPS.get("answers", True):
                await self.test_answers_endpoints()
            
            if self.config.ENABLED_TEST_GROUPS.get("chat", True):
                await self.test_chat_endpoints()
            
            if self.config.ENABLED_TEST_GROUPS.get("intelligent_qa", True):
                await self.test_intelligent_qa_endpoints()
            
            if self.config.ENABLED_TEST_GROUPS.get("session", True):
                await self.test_session_endpoints()
            
            if self.config.ENABLED_TEST_GROUPS.get("smtp", True):
                await self.test_smtp_endpoints()
            
            # Cleanup if not skipped
            if not self.config.SKIP_CLEANUP:
                await self.cleanup_test_data()
            
        except Exception as e:
            logger.error("💥 Critical error during testing: %s", e)
            raise
        
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
    
    def save_enhanced_results(self, summary: TestSummary, filename: str = None):
        """Save enhanced test results with additional analysis"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"enhanced_api_test_results_{timestamp}.json"
        
        # Create output directory if it doesn't exist
        output_dir = Path(self.config.OUTPUT_DIR)
        output_dir.mkdir(exist_ok=True)
        filepath = output_dir / filename
        
        # Generate additional reports
        performance_report = self.generate_performance_report()
        error_analysis = self.generate_error_analysis()
        coverage_report = self.generate_coverage_report()
        
        # Compile comprehensive results
        results_data = {
            "test_summary": {
                "total_tests": summary.total_tests,
                "passed_tests": summary.passed_tests,
                "failed_tests": summary.failed_tests,
                "success_rate": summary.success_rate,
                "total_time_seconds": summary.total_time_seconds,
                "start_time": summary.start_time,
                "end_time": summary.end_time
            },
            "performance_analysis": performance_report,
            "error_analysis": error_analysis,
            "coverage_analysis": coverage_report,
            "detailed_results": [
                {
                    "endpoint": r.endpoint,
                    "method": r.method,
                    "status_code": r.status_code,
                    "response_time_ms": r.response_time_ms,
                    "success": r.success,
                    "error_message": r.error_message,
                    "timestamp": r.timestamp,
                    "request_data": r.request_data,
                    "response_data": r.response_data
                }
                for r in summary.results
            ],
            "test_metadata": {
                "base_url": self.base_url,
                "test_user_email": self.test_email,
                "test_username": self.test_username,
                "framework_version": "2.0.0",
                "configuration": self.config.get_environment_info()
            }
        }
        
        # Save to file
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(results_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"📁 Enhanced test results saved to: {filepath}")
        return str(filepath)

def print_enhanced_summary(summary: TestSummary, tester: EnhancedAPITester):
    """Print enhanced test summary with additional metrics"""
    print("\n" + "="*100)
    print("🚀 ENHANCED API ENDPOINT TESTING SUMMARY")
    print("="*100)
    
    # Basic summary
    print(f"📊 Total Tests: {summary.total_tests}")
    print(f"✅ Passed: {summary.passed_tests}")
    print(f"❌ Failed: {summary.failed_tests}")
    print(f"📈 Success Rate: {summary.success_rate:.2f}%")
    print(f"⏱️  Total Time: {summary.total_time_seconds:.2f} seconds")
    print(f"🕐 Start Time: {summary.start_time}")
    print(f"🕐 End Time: {summary.end_time}")
    
    # Performance analysis
    perf_report = tester.generate_performance_report()
    if perf_report:
        print("\n⚡ PERFORMANCE ANALYSIS")
        print("-" * 50)
        print(f"Average Response Time: {perf_report.get('average_response_time_ms', 0):.2f}ms")
        print(f"Fastest Response: {perf_report.get('min_response_time_ms', 0):.2f}ms")
        print(f"Slowest Response: {perf_report.get('max_response_time_ms', 0):.2f}ms")
        
        if perf_report.get('slowest_endpoints'):
            print("\n🐌 Slowest Endpoints:")
            for endpoint in perf_report['slowest_endpoints'][:3]:
                print(f"  {endpoint['method']} {endpoint['endpoint']}: {endpoint['response_time']:.2f}ms")
    
    # Error analysis
    error_analysis = tester.generate_error_analysis()
    if error_analysis.get('error_categories'):
        print("\n❌ ERROR ANALYSIS")
        print("-" * 50)
        print(f"Total Errors: {error_analysis['total_errors']}")
        if error_analysis.get('most_common_errors'):
            print("Most Common Errors:")
            for error, count in error_analysis['most_common_errors'][:3]:
                print(f"  {error}: {count} occurrences")
    
    # Coverage analysis
    coverage_report = tester.generate_coverage_report()
    if coverage_report:
        print("\n📋 COVERAGE ANALYSIS")
        print("-" * 50)
        print(f"Endpoints Tested: {coverage_report['total_endpoints_tested']}")
        print(f"Successful Endpoints: {coverage_report['successful_endpoints']}")
        print(f"Coverage Rate: {coverage_report['coverage_percentage']:.2f}%")
    
    print("="*100)

async def main():
    """Main test execution with command line arguments"""
    parser = argparse.ArgumentParser(description="Enhanced API Endpoint Testing Framework")
    parser.add_argument("--base-url", default=TestConfig.BASE_URL, help="Base URL for API testing")
    parser.add_argument("--output-dir", default=TestConfig.OUTPUT_DIR, help="Output directory for results")
    parser.add_argument("--skip-cleanup", action="store_true", help="Skip cleanup of test data")
    parser.add_argument("--groups", nargs="+", help="Specific test groups to run")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose logging")
    
    args = parser.parse_args()
    
    # Update configuration based on arguments
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    if args.groups:
        # Reset all groups to False, then enable specified ones
        TestConfig.ENABLED_TEST_GROUPS = {k: False for k in TestConfig.ENABLED_TEST_GROUPS}
        for group in args.groups:
            if group in TestConfig.ENABLED_TEST_GROUPS:
                TestConfig.ENABLED_TEST_GROUPS[group] = True
    
    TestConfig.SKIP_CLEANUP = args.skip_cleanup
    TestConfig.OUTPUT_DIR = args.output_dir
    
    # Run tests
    async with EnhancedAPITester(args.base_url, TestConfig) as tester:
        try:
            summary = await tester.run_all_tests()
            print_enhanced_summary(summary, tester)
            
            # Save results
            filename = tester.save_enhanced_results(summary)
            print(f"\n📁 Detailed results saved to: {filename}")
            
            # Exit with appropriate code
            sys.exit(0 if summary.failed_tests == 0 else 1)
            
        except Exception as e:
            logger.error(f"💥 Test execution failed: {e}")
            sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
