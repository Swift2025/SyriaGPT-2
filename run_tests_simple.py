#!/usr/bin/env python3
"""
Simple API Test Runner - Easy to use version
"""

import asyncio
import sys
from pathlib import Path

# Add current directory to path to import our modules
sys.path.append(str(Path(__file__).parent))

from test_endpoints import APITester
from test_config import TestConfig

async def run_simple_tests():
    """Run all tests with simple output"""
    print("🚀 Starting SyriaGPT API Endpoint Testing...")
    print(f"📡 Testing API at: {TestConfig.BASE_URL}")
    print("-" * 60)
    
    async with APITester(TestConfig.BASE_URL) as tester:
        summary = await tester.run_all_tests()
        
        # Print simple summary
        print("\n" + "="*60)
        print("📊 TEST RESULTS SUMMARY")
        print("="*60)
        print(f"Total Tests: {summary.total_tests}")
        print(f"✅ Passed: {summary.passed_tests}")
        print(f"❌ Failed: {summary.failed_tests}")
        print(f"📈 Success Rate: {summary.success_rate:.2f}%")
        print(f"⏱️  Total Time: {summary.total_time_seconds:.2f} seconds")
        
        # Show failed tests
        failed_tests = [r for r in summary.results if not r.success]
        if failed_tests:
            print(f"\n❌ FAILED TESTS ({len(failed_tests)}):")
            print("-" * 40)
            for test in failed_tests:
                print(f"  {test.method} {test.endpoint} - {test.status_code}")
                if test.error_message:
                    print(f"    Error: {test.error_message}")
        
        # Save results
        filename = tester.save_results_to_file(summary)
        print(f"\n📁 Detailed results saved to: {filename}")
        
        # Performance summary
        response_times = [r.response_time_ms for r in summary.results]
        if response_times:
            avg_time = sum(response_times) / len(response_times)
            max_time = max(response_times)
            min_time = min(response_times)
            print("\n⚡ PERFORMANCE:")
            print(f"  Average Response Time: {avg_time:.2f}ms")
            print(f"  Fastest Response: {min_time:.2f}ms")
            print(f"  Slowest Response: {max_time:.2f}ms")
        
        print("="*60)
        
        # Return exit code
        return 0 if summary.failed_tests == 0 else 1

if __name__ == "__main__":
    try:
        exit_code = asyncio.run(run_simple_tests())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n⚠️  Testing interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Testing failed with error: {e}")
        sys.exit(1)
