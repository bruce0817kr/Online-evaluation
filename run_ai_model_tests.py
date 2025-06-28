#!/usr/bin/env python3
"""
Comprehensive Test Runner for AI Model Management System
Runs all unit, integration, and E2E tests with coverage reporting
"""

import subprocess
import sys
import os
import json
import time
from datetime import datetime
from pathlib import Path

class AIModelTestRunner:
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.backend_dir = self.project_root / "backend"
        self.frontend_dir = self.project_root / "frontend"
        self.e2e_dir = self.project_root / "tests" / "e2e"
        
        self.test_results = {
            "timestamp": datetime.now().isoformat(),
            "total_tests": 0,
            "passed": 0,
            "failed": 0,
            "skipped": 0,
            "coverage": {},
            "test_suites": {}
        }
    
    def print_header(self, text):
        """Print formatted header"""
        print(f"\n{'='*60}")
        print(f"{text:^60}")
        print(f"{'='*60}")
    
    def print_step(self, text):
        """Print formatted step"""
        print(f"\n🔧 {text}")
        print("-" * 50)
    
    def run_command(self, cmd, cwd=None, capture_output=True):
        """Run shell command and return result"""
        try:
            result = subprocess.run(
                cmd, 
                shell=True, 
                cwd=cwd or self.project_root,
                capture_output=capture_output,
                text=True,
                timeout=300  # 5 minute timeout
            )
            return result.returncode == 0, result.stdout, result.stderr
        except subprocess.TimeoutExpired:
            return False, "", "Command timed out"
        except Exception as e:
            return False, "", str(e)
    
    def check_dependencies(self):
        """Check if all required dependencies are installed"""
        self.print_step("Checking Dependencies")
        
        # Backend dependencies
        backend_deps = [
            "pytest",
            "pytest-asyncio", 
            "pytest-cov",
            "httpx",
            "fastapi[all]"
        ]
        
        # Frontend dependencies
        frontend_deps = [
            "@testing-library/react",
            "@testing-library/jest-dom",
            "@testing-library/user-event",
            "jest"
        ]
        
        # Check Python dependencies
        print("Checking Python dependencies...")
        for dep in backend_deps:
            success, _, _ = self.run_command(f"python -c \"import {dep.split('[')[0].replace('-', '_')}\"")
            if not success:
                print(f"❌ Missing Python dependency: {dep}")
                print(f"   Install with: pip install {dep}")
                return False
            print(f"✅ {dep}")
        
        # Check Node dependencies
        print("\nChecking Node.js dependencies...")
        if not (self.frontend_dir / "node_modules").exists():
            print("❌ Node modules not installed")
            print("   Run: cd frontend && npm install")
            return False
        
        package_lock = self.frontend_dir / "package-lock.json"
        if package_lock.exists():
            print("✅ Node.js dependencies installed")
        
        return True
    
    def run_backend_unit_tests(self):
        """Run backend unit tests with coverage"""
        self.print_step("Running Backend Unit Tests")
        
        # Install test dependencies if needed
        self.run_command("pip install pytest pytest-asyncio pytest-cov httpx", cwd=self.backend_dir)
        
        # Run tests with coverage
        cmd = (
            "python -m pytest test_ai_model_management.py test_ai_model_endpoints.py "
            "--cov=ai_model_management --cov=ai_model_settings_endpoints "
            "--cov-report=term-missing --cov-report=json:coverage.json "
            "--json-report --json-report-file=test_results.json -v"
        )
        
        success, stdout, stderr = self.run_command(cmd, cwd=self.backend_dir)
        
        # Parse results
        try:
            results_file = self.backend_dir / "test_results.json"
            if results_file.exists():
                with open(results_file, 'r') as f:
                    results = json.load(f)
                    self.test_results["test_suites"]["backend_unit"] = {
                        "total": results.get("summary", {}).get("total", 0),
                        "passed": results.get("summary", {}).get("passed", 0),
                        "failed": results.get("summary", {}).get("failed", 0),
                        "skipped": results.get("summary", {}).get("skipped", 0),
                        "duration": results.get("duration", 0)
                    }
            
            # Parse coverage
            coverage_file = self.backend_dir / "coverage.json"
            if coverage_file.exists():
                with open(coverage_file, 'r') as f:
                    coverage = json.load(f)
                    self.test_results["coverage"]["backend"] = {
                        "percent_covered": coverage.get("totals", {}).get("percent_covered", 0),
                        "num_statements": coverage.get("totals", {}).get("num_statements", 0),
                        "missing_lines": coverage.get("totals", {}).get("missing_lines", 0)
                    }
        except Exception as e:
            print(f"⚠️  Could not parse test results: {e}")
        
        if success:
            print("✅ Backend unit tests completed successfully")
        else:
            print("❌ Backend unit tests failed")
            print(f"STDOUT: {stdout}")
            print(f"STDERR: {stderr}")
        
        return success
    
    def run_frontend_unit_tests(self):
        """Run frontend unit tests"""
        self.print_step("Running Frontend Unit Tests")
        
        # Set test environment variables
        env = os.environ.copy()
        env.update({
            "CI": "true",
            "NODE_ENV": "test",
            "REACT_APP_BACKEND_URL": "http://localhost:8002"
        })
        
        # Run Jest tests
        cmd = "npm test -- --coverage --watchAll=false --testResultsProcessor=jest-json-reporter"
        
        success, stdout, stderr = self.run_command(cmd, cwd=self.frontend_dir)
        
        # Parse results
        try:
            results_file = self.frontend_dir / "test-results.json"
            if results_file.exists():
                with open(results_file, 'r') as f:
                    results = json.load(f)
                    self.test_results["test_suites"]["frontend_unit"] = {
                        "total": results.get("numTotalTests", 0),
                        "passed": results.get("numPassedTests", 0),
                        "failed": results.get("numFailedTests", 0),
                        "skipped": results.get("numPendingTests", 0),
                        "duration": results.get("testResults", [{}])[0].get("perfStats", {}).get("end", 0)
                    }
            
            # Parse coverage
            coverage_file = self.frontend_dir / "coverage" / "coverage-summary.json"
            if coverage_file.exists():
                with open(coverage_file, 'r') as f:
                    coverage = json.load(f)
                    total_coverage = coverage.get("total", {})
                    self.test_results["coverage"]["frontend"] = {
                        "lines": total_coverage.get("lines", {}).get("pct", 0),
                        "functions": total_coverage.get("functions", {}).get("pct", 0),
                        "branches": total_coverage.get("branches", {}).get("pct", 0),
                        "statements": total_coverage.get("statements", {}).get("pct", 0)
                    }
        except Exception as e:
            print(f"⚠️  Could not parse frontend test results: {e}")
        
        if success:
            print("✅ Frontend unit tests completed successfully")
        else:
            print("❌ Frontend unit tests failed")
            print(f"STDOUT: {stdout}")
            print(f"STDERR: {stderr}")
        
        return success
    
    def start_test_services(self):
        """Start required services for E2E tests"""
        self.print_step("Starting Test Services")
        
        # Check if services are already running
        backend_running, _, _ = self.run_command("curl -s http://localhost:8002/health || echo 'not running'")
        frontend_running, _, _ = self.run_command("curl -s http://localhost:3000 || echo 'not running'")
        
        services_started = []
        
        if not backend_running:
            print("Starting backend service...")
            # Start backend in background
            subprocess.Popen([
                "python", "-m", "uvicorn", "server:app", 
                "--host", "0.0.0.0", "--port", "8002", "--reload"
            ], cwd=self.backend_dir)
            services_started.append("backend")
            time.sleep(5)  # Wait for backend to start
        
        if not frontend_running:
            print("Starting frontend service...")
            # Start frontend in background
            subprocess.Popen([
                "npm", "start"
            ], cwd=self.frontend_dir, env={**os.environ, "PORT": "3000"})
            services_started.append("frontend")
            time.sleep(10)  # Wait for frontend to build and start
        
        # Wait for services to be ready
        print("Waiting for services to be ready...")
        for _ in range(30):  # 30 second timeout
            backend_ready, _, _ = self.run_command("curl -s http://localhost:8002/health")
            frontend_ready, _, _ = self.run_command("curl -s http://localhost:3000")
            
            if backend_ready and frontend_ready:
                print("✅ All services are ready")
                return True, services_started
            
            time.sleep(1)
        
        print("❌ Services failed to start within timeout")
        return False, services_started
    
    def run_e2e_tests(self):
        """Run E2E tests with Playwright"""
        self.print_step("Running End-to-End Tests")
        
        # Start services
        services_ready, started_services = self.start_test_services()
        if not services_ready:
            return False
        
        try:
            # Install Playwright if needed
            self.run_command("npx playwright install", cwd=self.project_root)
            
            # Run Playwright tests
            cmd = (
                "npx playwright test tests/e2e/ai_model_management.spec.js "
                "--reporter=json --output=e2e-results.json "
                "--video=retain-on-failure --screenshot=only-on-failure"
            )
            
            success, stdout, stderr = self.run_command(cmd, cwd=self.project_root)
            
            # Parse results
            try:
                results_file = self.project_root / "e2e-results.json"
                if results_file.exists():
                    with open(results_file, 'r') as f:
                        results = json.load(f)
                        
                        total_tests = len(results.get("tests", []))
                        passed_tests = sum(1 for test in results.get("tests", []) 
                                         if test.get("outcome") == "expected")
                        failed_tests = total_tests - passed_tests
                        
                        self.test_results["test_suites"]["e2e"] = {
                            "total": total_tests,
                            "passed": passed_tests,
                            "failed": failed_tests,
                            "skipped": 0,
                            "duration": results.get("stats", {}).get("duration", 0)
                        }
            except Exception as e:
                print(f"⚠️  Could not parse E2E test results: {e}")
            
            if success:
                print("✅ E2E tests completed successfully")
            else:
                print("❌ E2E tests failed")
                print(f"STDOUT: {stdout}")
                print(f"STDERR: {stderr}")
            
            return success
            
        finally:
            # Cleanup: stop started services if needed
            if "backend" in started_services:
                self.run_command("pkill -f 'uvicorn server:app'")
            if "frontend" in started_services:
                self.run_command("pkill -f 'npm start'")
    
    def run_performance_tests(self):
        """Run performance and load tests"""
        self.print_step("Running Performance Tests")
        
        # Basic performance test with multiple concurrent requests
        performance_script = '''
import asyncio
import aiohttp
import time
import statistics

async def test_model_list_performance():
    """Test API response time under load"""
    url = "http://localhost:8002/api/ai-models/available"
    headers = {"Authorization": "Bearer admin-token"}
    
    async with aiohttp.ClientSession() as session:
        start_time = time.time()
        tasks = []
        
        # Create 50 concurrent requests
        for _ in range(50):
            task = session.get(url, headers=headers)
            tasks.append(task)
        
        responses = await asyncio.gather(*tasks, return_exceptions=True)
        end_time = time.time()
        
        # Calculate metrics
        successful_requests = sum(1 for r in responses if hasattr(r, 'status') and r.status == 200)
        total_time = end_time - start_time
        avg_response_time = total_time / len(responses)
        
        print(f"Performance Test Results:")
        print(f"Total requests: {len(responses)}")
        print(f"Successful requests: {successful_requests}")
        print(f"Success rate: {successful_requests/len(responses)*100:.1f}%")
        print(f"Total time: {total_time:.2f}s")
        print(f"Average response time: {avg_response_time:.3f}s")
        print(f"Requests per second: {len(responses)/total_time:.1f}")
        
        return successful_requests >= 45  # 90% success rate

if __name__ == "__main__":
    result = asyncio.run(test_model_list_performance())
    exit(0 if result else 1)
'''
        
        # Write and run performance test
        perf_file = self.project_root / "temp_performance_test.py"
        try:
            with open(perf_file, 'w') as f:
                f.write(performance_script)
            
            success, stdout, stderr = self.run_command(f"python {perf_file}")
            
            if success:
                print("✅ Performance tests passed")
            else:
                print("❌ Performance tests failed")
                print(stdout)
            
            return success
            
        finally:
            # Cleanup
            if perf_file.exists():
                perf_file.unlink()
    
    def generate_report(self):
        """Generate comprehensive test report"""
        self.print_step("Generating Test Report")
        
        # Calculate totals
        total_tests = 0
        total_passed = 0
        total_failed = 0
        total_skipped = 0
        
        for suite_name, suite_data in self.test_results["test_suites"].items():
            total_tests += suite_data.get("total", 0)
            total_passed += suite_data.get("passed", 0)
            total_failed += suite_data.get("failed", 0)
            total_skipped += suite_data.get("skipped", 0)
        
        self.test_results.update({
            "total_tests": total_tests,
            "passed": total_passed,
            "failed": total_failed,
            "skipped": total_skipped
        })
        
        # Generate report
        report = f"""
# AI Model Management System - Test Report

**Generated:** {self.test_results['timestamp']}

## 📊 Test Summary

| Metric | Count | Percentage |
|--------|--------|------------|
| Total Tests | {total_tests} | 100% |
| Passed | {total_passed} | {(total_passed/total_tests*100):.1f}% |
| Failed | {total_failed} | {(total_failed/total_tests*100):.1f}% |
| Skipped | {total_skipped} | {(total_skipped/total_tests*100):.1f}% |

## 🧪 Test Suite Results

"""
        
        for suite_name, suite_data in self.test_results["test_suites"].items():
            report += f"""
### {suite_name.replace('_', ' ').title()}
- **Total:** {suite_data.get('total', 0)}
- **Passed:** {suite_data.get('passed', 0)}
- **Failed:** {suite_data.get('failed', 0)}
- **Duration:** {suite_data.get('duration', 0):.2f}s
"""
        
        # Coverage section
        if self.test_results["coverage"]:
            report += "\n## 📈 Code Coverage\n\n"
            
            for component, coverage_data in self.test_results["coverage"].items():
                report += f"### {component.title()}\n"
                if component == "backend":
                    report += f"- **Overall Coverage:** {coverage_data.get('percent_covered', 0):.1f}%\n"
                    report += f"- **Statements:** {coverage_data.get('num_statements', 0)}\n"
                elif component == "frontend":
                    report += f"- **Lines:** {coverage_data.get('lines', 0):.1f}%\n"
                    report += f"- **Functions:** {coverage_data.get('functions', 0):.1f}%\n"
                    report += f"- **Branches:** {coverage_data.get('branches', 0):.1f}%\n"
                report += "\n"
        
        # Status
        overall_status = "✅ PASSED" if total_failed == 0 else "❌ FAILED"
        report += f"\n## 🎯 Overall Status: {overall_status}\n"
        
        if total_failed > 0:
            report += f"\n⚠️  **{total_failed} test(s) failed. Please review the logs above.**\n"
        
        # Save report
        report_file = self.project_root / "AI_MODEL_TEST_REPORT.md"
        with open(report_file, 'w') as f:
            f.write(report)
        
        # Save JSON results
        results_file = self.project_root / "test_results.json"
        with open(results_file, 'w') as f:
            json.dump(self.test_results, f, indent=2)
        
        print(f"📄 Test report saved to: {report_file}")
        print(f"📊 Test results saved to: {results_file}")
        
        return total_failed == 0
    
    def run_all_tests(self):
        """Run complete test suite"""
        self.print_header("AI Model Management System - Test Suite")
        
        start_time = time.time()
        all_passed = True
        
        # Check dependencies
        if not self.check_dependencies():
            print("❌ Dependency check failed. Please install missing dependencies.")
            return False
        
        # Run test suites
        test_suites = [
            ("Backend Unit Tests", self.run_backend_unit_tests),
            ("Frontend Unit Tests", self.run_frontend_unit_tests),
            ("End-to-End Tests", self.run_e2e_tests),
            ("Performance Tests", self.run_performance_tests)
        ]
        
        for suite_name, test_function in test_suites:
            try:
                success = test_function()
                if not success:
                    all_passed = False
                    print(f"❌ {suite_name} failed")
                else:
                    print(f"✅ {suite_name} passed")
            except Exception as e:
                print(f"❌ {suite_name} failed with exception: {e}")
                all_passed = False
        
        # Generate report
        report_success = self.generate_report()
        
        end_time = time.time()
        duration = end_time - start_time
        
        self.print_header("Test Suite Complete")
        print(f"⏱️  Total duration: {duration:.2f} seconds")
        print(f"📊 Status: {'✅ ALL TESTS PASSED' if all_passed else '❌ SOME TESTS FAILED'}")
        
        return all_passed and report_success


def main():
    """Main entry point"""
    runner = AIModelTestRunner()
    
    # Handle command line arguments
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "backend":
            success = runner.run_backend_unit_tests()
        elif command == "frontend":
            success = runner.run_frontend_unit_tests()
        elif command == "e2e":
            success = runner.run_e2e_tests()
        elif command == "performance":
            success = runner.run_performance_tests()
        elif command == "deps":
            success = runner.check_dependencies()
        else:
            print(f"Unknown command: {command}")
            print("Available commands: backend, frontend, e2e, performance, deps")
            return 1
    else:
        success = runner.run_all_tests()
    
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())