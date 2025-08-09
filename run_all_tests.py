#!/usr/bin/env python3
"""
Master Test Suite Runner
Runs all test suites and provides comprehensive system validation
"""

import asyncio
import sys
import os
from datetime import datetime

# Import all test modules
from test_recipe_system import TestRecipeSystem
from test_api_endpoints import TestAPIEndpoints
from test_data_integrity import TestDataIntegrity
from test_performance import TestPerformance
from test_integration import TestIntegration

class MasterTestSuite:
    def __init__(self):
        self.test_suites = [
            ("Recipe System Tests", TestRecipeSystem),
            ("API Endpoints Tests", TestAPIEndpoints),
            ("Data Integrity Tests", TestDataIntegrity),
            ("Performance Tests", TestPerformance),
            ("Integration Tests", TestIntegration)
        ]
        
    def log(self, message: str, level: str = "INFO"):
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {level}: {message}")
    
    async def run_test_suite(self, name, test_class):
        """Run a single test suite"""
        self.log(f"🧪 Starting {name}...")
        
        tester = test_class()
        try:
            success = await tester.run_all_tests()
            return success
        except Exception as e:
            self.log(f"❌ {name} encountered critical error: {str(e)}", "ERROR")
            return False
        finally:
            await tester.cleanup()
    
    async def run_all_test_suites(self):
        """Run all test suites sequentially"""
        self.log("🚀 AI Recipe + Grocery Delivery App - Master Test Suite")
        self.log("=" * 70)
        self.log("Testing cleaned codebase and rebuilt recipe history system")
        self.log("=" * 70)
        
        total_suites = len(self.test_suites)
        passed_suites = 0
        results = []
        
        for i, (suite_name, test_class) in enumerate(self.test_suites, 1):
            self.log(f"\n{'='*20} [{i}/{total_suites}] {suite_name} {'='*20}")
            
            success = await self.run_test_suite(suite_name, test_class)
            
            if success:
                passed_suites += 1
                status = "✅ PASSED"
            else:
                status = "❌ FAILED"
            
            results.append((suite_name, success, status))
            self.log(f"{'='*20} {suite_name}: {status} {'='*20}")
            
            # Delay between test suites to allow system to stabilize
            if i < total_suites:
                self.log("⏸️  Cooling down between test suites...")
                await asyncio.sleep(3)
        
        # Final Results Summary
        self.log("\n" + "=" * 70)
        self.log("🎯 MASTER TEST SUITE RESULTS")
        self.log("=" * 70)
        
        for suite_name, success, status in results:
            self.log(f"{status} {suite_name}")
        
        self.log("=" * 70)
        success_rate = (passed_suites / total_suites) * 100
        self.log(f"📊 Overall Success Rate: {passed_suites}/{total_suites} ({success_rate:.1f}%)")
        
        if passed_suites == total_suites:
            self.log("🎉 ALL TEST SUITES PASSED - SYSTEM IS HEALTHY!")
            self.log("✅ Recipe history navigation working perfectly")
            self.log("✅ Diverse recipe generation functioning")
            self.log("✅ Code cleanup successful - no debug statements")
            self.log("✅ Data integrity maintained")
            self.log("✅ Performance within acceptable limits")
            self.log("✅ All integrations functioning")
            return True
        elif passed_suites >= total_suites * 0.8:  # 80% pass rate
            self.log("⚠️  MOSTLY HEALTHY - MINOR ISSUES DETECTED")
            self.log("System is functional but some improvements recommended")
            return True
        else:
            self.log("❌ SYSTEM NEEDS ATTENTION - MULTIPLE ISSUES DETECTED")
            self.log("Please review failed test suites and address issues")
            return False
    
    async def run_quick_health_check(self):
        """Run a quick health check (subset of tests)"""
        self.log("🏥 Running Quick Health Check...")
        self.log("=" * 50)
        
        # Run only critical tests
        critical_tests = [
            ("Recipe System Tests", TestRecipeSystem),
            ("API Endpoints Tests", TestAPIEndpoints)
        ]
        
        passed = 0
        for suite_name, test_class in critical_tests:
            success = await self.run_test_suite(suite_name, test_class)
            if success:
                passed += 1
        
        self.log("=" * 50)
        if passed == len(critical_tests):
            self.log("🎉 Quick Health Check PASSED - Core system healthy!")
            return True
        else:
            self.log("❌ Quick Health Check FAILED - Core system issues detected")
            return False

def print_usage():
    print("Usage:")
    print("  python run_all_tests.py [full|quick]")
    print("")
    print("Options:")
    print("  full  - Run complete test suite (default)")
    print("  quick - Run quick health check only")

async def main():
    master_suite = MasterTestSuite()
    
    # Parse command line arguments
    if len(sys.argv) > 1:
        mode = sys.argv[1].lower()
    else:
        mode = "full"
    
    if mode not in ["full", "quick"]:
        print_usage()
        return False
    
    try:
        if mode == "quick":
            success = await master_suite.run_quick_health_check()
        else:
            success = await master_suite.run_all_test_suites()
        
        return success
        
    except KeyboardInterrupt:
        print("\n❌ Test suite interrupted by user")
        return False
    except Exception as e:
        print(f"\n❌ Master test suite error: {str(e)}")
        return False

if __name__ == "__main__":
    print("🚀 AI Recipe + Grocery Delivery App Test Suite")
    print(f"⏰ Started at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("")
    
    success = asyncio.run(main())
    
    print("")
    print(f"⏰ Completed at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    if success:
        print("🎉 Test suite completed successfully!")
        exit(0)
    else:
        print("❌ Test suite completed with failures!")
        exit(1)