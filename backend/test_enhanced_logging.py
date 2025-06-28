#!/usr/bin/env python3
"""
Enhanced Logging Integration Test Script
Tests the comprehensive logging system with ELK stack integration
"""

import sys
import os
import asyncio
import json
import time
from pathlib import Path

# Add the backend directory to the Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

try:
    # Import the enhanced logging system
    from enhanced_logging import (
        setup_logging, get_logger, RequestContext, log_async_performance,
        log_database_operation, log_security_event, log_startup_info, log_shutdown_info,
        request_id_context, user_id_context, session_id_context
    )
    print("✅ Enhanced logging system imported successfully")
except ImportError as e:
    print(f"❌ Failed to import enhanced logging system: {e}")
    sys.exit(1)

class LoggingIntegrationTester:
    """Test class for enhanced logging integration"""
    
    def __init__(self):
        self.logger = None
        self.test_results = []
        
    def setup_test_environment(self):
        """Setup test environment with enhanced logging"""
        try:
            # Initialize enhanced logging
            setup_logging(
                service_name="logging-integration-test",
                log_level="DEBUG",
                log_file="/tmp/test_app.log" if os.name != 'nt' else "test_app.log"
            )
            
            self.logger = get_logger(__name__)
            self.logger.info("Test environment setup completed", extra={
                'custom_test_phase': 'setup',
                'custom_test_status': 'success'
            })
            
            self.add_test_result("Enhanced logging setup", True, "Logging system initialized successfully")
            return True
            
        except Exception as e:
            self.add_test_result("Enhanced logging setup", False, f"Setup failed: {e}")
            return False
    
    def add_test_result(self, test_name: str, success: bool, message: str):
        """Add test result to results list"""
        self.test_results.append({
            "test_name": test_name,
            "success": success,
            "message": message,
            "timestamp": time.time()
        })
        
        status = "✅" if success else "❌"
        print(f"{status} {test_name}: {message}")
    
    def test_basic_logging(self):
        """Test basic logging functionality"""
        try:
            self.logger.debug("Debug message test")
            self.logger.info("Info message test")
            self.logger.warning("Warning message test")
            
            self.add_test_result("Basic logging levels", True, "All log levels working")
            return True
            
        except Exception as e:
            self.add_test_result("Basic logging levels", False, f"Logging failed: {e}")
            return False
    
    def test_structured_logging(self):
        """Test structured logging with custom fields"""
        try:
            self.logger.info("Structured logging test", extra={
                'custom_user_id': 'test-user-123',
                'custom_operation': 'test_operation',
                'custom_data': {'key': 'value', 'count': 42}
            })
            
            self.add_test_result("Structured logging", True, "Custom fields added successfully")
            return True
            
        except Exception as e:
            self.add_test_result("Structured logging", False, f"Structured logging failed: {e}")
            return False
    
    def test_request_context(self):
        """Test request context management"""
        try:
            with RequestContext(request_id="test-req-123", user_id="test-user-456", session_id="test-sess-789"):
                self.logger.info("Request context test message")
                
                # Test context variable access
                request_id = request_id_context.get()
                user_id = user_id_context.get()
                session_id = session_id_context.get()
                
                if request_id == "test-req-123" and user_id == "test-user-456" and session_id == "test-sess-789":
                    self.add_test_result("Request context", True, "Context variables set and retrieved correctly")
                    return True
                else:
                    self.add_test_result("Request context", False, "Context variables not set correctly")
                    return False
                    
        except Exception as e:
            self.add_test_result("Request context", False, f"Request context failed: {e}")
            return False
    
    @log_async_performance("test_performance_decorator")
    async def test_performance_logging(self):
        """Test performance logging decorator"""
        try:
            # Simulate some work
            await asyncio.sleep(0.1)
            
            self.add_test_result("Performance decorator", True, "Performance logging decorator working")
            return True
            
        except Exception as e:
            self.add_test_result("Performance decorator", False, f"Performance decorator failed: {e}")
            return False
    
    @log_database_operation("test_collection")
    async def test_database_logging(self):
        """Test database operation logging decorator"""
        try:
            # Simulate database operation
            await asyncio.sleep(0.05)
            
            # Return mock result that simulates database response
            class MockResult:
                def __init__(self):
                    self.inserted_id = "test-id-123"
            
            self.add_test_result("Database decorator", True, "Database logging decorator working")
            return MockResult()
            
        except Exception as e:
            self.add_test_result("Database decorator", False, f"Database decorator failed: {e}")
            return False
    
    @log_security_event("test_security_event", "medium")
    async def test_security_logging(self):
        """Test security event logging decorator"""
        try:
            # Simulate security operation
            await asyncio.sleep(0.02)
            
            self.add_test_result("Security decorator", True, "Security logging decorator working")
            return True
            
        except Exception as e:
            self.add_test_result("Security decorator", False, f"Security decorator failed: {e}")
            return False
    
    def test_error_logging(self):
        """Test error logging with context"""
        try:
            try:
                # Intentionally cause an error for testing
                1 / 0
            except ZeroDivisionError as e:
                self.logger.error("Test error handling", extra={
                    'custom_error_test': True,
                    'custom_error_type': type(e).__name__
                })
            
            self.add_test_result("Error logging", True, "Error logging with context working")
            return True
            
        except Exception as e:
            self.add_test_result("Error logging", False, f"Error logging failed: {e}")
            return False
    
    def test_json_formatting(self):
        """Test JSON log formatting"""
        try:
            from enhanced_logging import JSONFormatter
            
            formatter = JSONFormatter("test-service")
            
            # Create a mock log record
            import logging
            record = logging.LogRecord(
                name="test",
                level=logging.INFO,
                pathname="test.py",
                lineno=1,
                msg="Test JSON formatting",
                args=(),
                exc_info=None
            )
            
            # Test JSON formatting
            json_output = formatter.format(record)
            parsed_json = json.loads(json_output)
            
            # Verify required fields
            required_fields = ["@timestamp", "service", "host", "log", "message"]
            missing_fields = [field for field in required_fields if field not in parsed_json]
            
            if not missing_fields:
                self.add_test_result("JSON formatting", True, "JSON formatting working correctly")
                return True
            else:
                self.add_test_result("JSON formatting", False, f"Missing fields: {missing_fields}")
                return False
                
        except Exception as e:
            self.add_test_result("JSON formatting", False, f"JSON formatting failed: {e}")
            return False
    
    def test_log_file_creation(self):
        """Test log file creation and writing"""
        try:
            log_file = "test_app.log" if os.name == 'nt' else "/tmp/test_app.log"
            
            if os.path.exists(log_file):
                # Read the log file and check for our test messages
                with open(log_file, 'r', encoding='utf-8') as f:
                    log_content = f.read()
                
                if "Test environment setup completed" in log_content:
                    self.add_test_result("Log file creation", True, f"Log file created and written to: {log_file}")
                    return True
                else:
                    self.add_test_result("Log file creation", False, "Log file exists but doesn't contain expected content")
                    return False
            else:
                self.add_test_result("Log file creation", False, f"Log file not created: {log_file}")
                return False
                
        except Exception as e:
            self.add_test_result("Log file creation", False, f"Log file test failed: {e}")
            return False
    
    async def run_all_tests(self):
        """Run all logging integration tests"""
        print("🧪 Starting Enhanced Logging Integration Tests")
        print("=" * 60)
        
        # Setup
        if not self.setup_test_environment():
            print("❌ Test environment setup failed. Aborting tests.")
            return False
        
        # Run individual tests
        tests = [
            ("Basic Logging", self.test_basic_logging),
            ("Structured Logging", self.test_structured_logging),
            ("Request Context", self.test_request_context),
            ("Performance Decorator", self.test_performance_logging),
            ("Database Decorator", self.test_database_logging),
            ("Security Decorator", self.test_security_logging),
            ("Error Logging", self.test_error_logging),
            ("JSON Formatting", self.test_json_formatting),
            ("Log File Creation", self.test_log_file_creation),
        ]
        
        for test_name, test_func in tests:
            try:
                if asyncio.iscoroutinefunction(test_func):
                    await test_func()
                else:
                    test_func()
            except Exception as e:
                self.add_test_result(test_name, False, f"Test execution failed: {e}")
        
        # Test startup/shutdown logging
        try:
            log_startup_info()
            log_shutdown_info()
            self.add_test_result("Startup/Shutdown Logging", True, "Startup and shutdown logging working")
        except Exception as e:
            self.add_test_result("Startup/Shutdown Logging", False, f"Startup/shutdown logging failed: {e}")
        
        return self.generate_test_report()
    
    def generate_test_report(self):
        """Generate comprehensive test report"""
        print("\n" + "=" * 60)
        print("📊 Enhanced Logging Integration Test Report")
        print("=" * 60)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result["success"])
        failed_tests = total_tests - passed_tests
        
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {failed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        if failed_tests > 0:
            print("\n❌ Failed Tests:")
            for result in self.test_results:
                if not result["success"]:
                    print(f"   • {result['test_name']}: {result['message']}")
        
        print("\n📋 Test Details:")
        for result in self.test_results:
            status = "✅ PASS" if result["success"] else "❌ FAIL"
            print(f"   {status} {result['test_name']}")
        
        # Save detailed test results
        report_file = "enhanced_logging_test_report.json"
        report_data = {
            "test_summary": {
                "total_tests": total_tests,
                "passed_tests": passed_tests,
                "failed_tests": failed_tests,
                "success_rate": (passed_tests/total_tests)*100
            },
            "test_results": self.test_results,
            "timestamp": time.time()
        }
        
        try:
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(report_data, f, indent=2, ensure_ascii=False)
            print(f"\n📄 Detailed report saved to: {report_file}")
        except Exception as e:
            print(f"\n⚠️ Failed to save detailed report: {e}")
        
        return failed_tests == 0

async def main():
    """Main test execution function"""
    tester = LoggingIntegrationTester()
    success = await tester.run_all_tests()
    
    if success:
        print("\n🎉 All Enhanced Logging Integration Tests Passed!")
        print("\n🎯 Next Steps:")
        print("   1. ✅ Enhanced logging system is ready for production")
        print("   2. ✅ ELK stack integration can be tested")
        print("   3. ✅ FastAPI server can be started with enhanced logging")
        print("   4. ✅ Monitor log output in development environment")
        return 0
    else:
        print("\n❌ Some Enhanced Logging Integration Tests Failed!")
        print("\n🔧 Recommended Actions:")
        print("   1. Review failed test details above")
        print("   2. Check enhanced_logging.py configuration")
        print("   3. Verify file permissions for log file creation")
        print("   4. Test individual components manually")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
