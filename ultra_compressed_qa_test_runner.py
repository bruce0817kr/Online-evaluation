#!/usr/bin/env python3
"""
Ultra-Compressed QA Test Runner with Performance Profiling (PUP)
Optimized for --e2e --coverage --uc --persona-qa --pup flags
"""

import json
import time
import subprocess
import os
from datetime import datetime
from pathlib import Path

class UltraCompressedQARunner:
    def __init__(self):
        self.start = datetime.now()
        self.results = {"timestamp": self.start.isoformat(), "tests": {}, "qa": {}, "perf": {}}
        
    def run(self, cmd, timeout=60):
        """Ultra-compressed command execution"""
        try:
            result = subprocess.run(cmd, shell=True, timeout=timeout, capture_output=True, text=True)
            return {"ok": result.returncode == 0, "out": result.stdout, "err": result.stderr}
        except subprocess.TimeoutExpired:
            return {"ok": False, "err": "timeout"}
        except Exception as e:
            return {"ok": False, "err": str(e)}
    
    def fix_mocks(self):
        """Quick mock fixes for React tests"""
        print("🔧 Fixing test mocks...")
        mock_setup = '''import '@testing-library/jest-dom';
global.localStorage = {getItem: jest.fn(), setItem: jest.fn(), removeItem: jest.fn(), clear: jest.fn()};
global.fetch = jest.fn();
global.IntersectionObserver = jest.fn(() => ({observe: jest.fn(), unobserve: jest.fn(), disconnect: jest.fn()}));
global.ResizeObserver = jest.fn(() => ({observe: jest.fn(), unobserve: jest.fn(), disconnect: jest.fn()}));
global.URL.createObjectURL = jest.fn();
HTMLCanvasElement.prototype.getContext = jest.fn();
beforeEach(() => {
  fetch.mockClear?.();
  localStorage.getItem.mockClear?.();
  localStorage.setItem.mockClear?.();
});'''
        with open('frontend/src/setupTests.js', 'w') as f:
            f.write(mock_setup)
        print("✅ Mocks fixed")
    
    def unit_coverage(self):
        """Run unit tests with coverage (UC flag)"""
        print("🧪 Running unit tests with coverage...")
        self.fix_mocks()
        
        # Quick unit test run
        result = self.run("cd frontend && npm run test:ci", 120)
        
        # Parse coverage
        coverage = 0
        if os.path.exists('frontend/coverage/coverage-final.json'):
            try:
                with open('frontend/coverage/coverage-final.json') as f:
                    cov_data = json.load(f)
                total_lines = sum(len(f.get('s', {})) for f in cov_data.values())
                covered_lines = sum(sum(1 for c in f.get('s', {}).values() if c > 0) for f in cov_data.values())
                coverage = (covered_lines / total_lines * 100) if total_lines > 0 else 0
            except:
                pass
        
        self.results["tests"]["unit"] = {"ok": result["ok"], "coverage": f"{coverage:.1f}%"}
        print(f"📊 Unit tests: {'✅' if result['ok'] else '❌'} | Coverage: {coverage:.1f}%")
        
        return result["ok"]
    
    def e2e_tests(self):
        """E2E tests with quick setup"""
        print("🌐 Running E2E tests...")
        
        # Quick service start
        print("🚀 Starting services...")
        self.run("cd backend && python -m uvicorn server:app --port 8002 &")
        self.run("cd frontend && npm start &")
        time.sleep(8)
        
        # Quick E2E run
        result = self.run("npx playwright test --workers=2 --project=chromium", 300)
        
        # Cleanup
        self.run("pkill -f uvicorn")
        self.run("pkill -f 'npm start'")
        
        self.results["tests"]["e2e"] = {"ok": result["ok"], "output": result["out"][:500]}
        print(f"🎭 E2E tests: {'✅' if result['ok'] else '❌'}")
        
        return result["ok"]
    
    def qa_persona(self):
        """QA persona validation with metrics"""
        print("👩‍💻 Running QA persona validation...")
        
        qa_score = 0
        checks = {}
        
        # Code quality check
        eslint = self.run("cd frontend && npx eslint src/ --format compact", 60)
        eslint_issues = eslint["out"].count("error") + eslint["out"].count("warning")
        quality_score = max(0, 100 - eslint_issues * 2)
        checks["code_quality"] = quality_score
        
        # Security audit
        audit = self.run("npm audit --audit-level=high --json", 60)
        vuln_count = 0
        if audit["ok"]:
            try:
                audit_data = json.loads(audit["out"])
                vuln_count = audit_data.get("metadata", {}).get("vulnerabilities", {}).get("high", 0)
            except:
                pass
        security_score = max(0, 100 - vuln_count * 20)
        checks["security"] = security_score
        
        # Performance check (build time)
        build_start = time.time()
        build = self.run("cd frontend && npm run build", 120)
        build_time = time.time() - build_start
        perf_score = max(0, 100 - max(0, build_time - 30))  # Penalty after 30s
        checks["performance"] = perf_score
        
        # Test coverage check
        coverage_score = float(self.results["tests"]["unit"]["coverage"].rstrip('%'))
        checks["test_coverage"] = coverage_score
        
        # Calculate overall QA score
        qa_score = sum(checks.values()) / len(checks)
        
        self.results["qa"] = {
            "overall_score": f"{qa_score:.1f}%",
            "checks": checks,
            "build_time": f"{build_time:.1f}s"
        }
        
        print(f"🎯 QA Score: {qa_score:.1f}% | Build: {build_time:.1f}s")
        
        return qa_score > 75
    
    def performance_profiling(self):
        """Performance profiling (PUP flag)"""
        print("⚡ Running performance profiling...")
        
        perf_metrics = {}
        
        # Bundle size analysis
        if os.path.exists('frontend/build'):
            size_result = self.run("du -sh frontend/build")
            if size_result["ok"]:
                perf_metrics["bundle_size"] = size_result["out"].strip().split()[0]
        
        # Build performance
        build_time = float(self.results["qa"]["build_time"].rstrip('s'))
        perf_metrics["build_time"] = f"{build_time:.1f}s"
        
        # Memory usage (approximate)
        memory_result = self.run("ps aux | grep node | head -1")
        if memory_result["ok"]:
            try:
                memory_kb = int(memory_result["out"].split()[5])
                memory_mb = memory_kb / 1024
                perf_metrics["memory_usage"] = f"{memory_mb:.1f}MB"
            except:
                perf_metrics["memory_usage"] = "N/A"
        
        # Test execution time
        total_time = (datetime.now() - self.start).total_seconds()
        perf_metrics["total_execution"] = f"{total_time:.1f}s"
        
        self.results["perf"] = perf_metrics
        
        print(f"📈 Bundle: {perf_metrics.get('bundle_size', 'N/A')} | "
              f"Build: {perf_metrics.get('build_time', 'N/A')} | "
              f"Memory: {perf_metrics.get('memory_usage', 'N/A')}")
        
        return True
    
    def generate_report(self):
        """Generate ultra-compressed report"""
        print("📄 Generating report...")
        
        summary = {
            "status": "PASS" if all([
                self.results["tests"]["unit"]["ok"],
                self.results["tests"]["e2e"]["ok"],
                float(self.results["qa"]["overall_score"].rstrip('%')) > 75
            ]) else "FAIL",
            "execution_time": f"{(datetime.now() - self.start).total_seconds():.1f}s",
            "coverage": self.results["tests"]["unit"]["coverage"],
            "qa_score": self.results["qa"]["overall_score"],
            "build_size": self.results["perf"].get("bundle_size", "N/A")
        }
        
        self.results["summary"] = summary
        
        # Save JSON report
        report_file = f"ultra_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump(self.results, f, indent=2)
        
        # Quick HTML report
        html_content = f'''<!DOCTYPE html>
<html><head><title>Ultra QA Test Report</title>
<style>body{{font-family:Arial;margin:20px;}}
.pass{{color:green;}} .fail{{color:red;}} .metric{{margin:10px 0;}}
</style></head><body>
<h1>🚀 Ultra-Compressed QA Test Results</h1>
<div class="metric">Status: <span class="{'pass' if summary['status'] == 'PASS' else 'fail'}">{summary['status']}</span></div>
<div class="metric">Coverage: {summary['coverage']}</div>
<div class="metric">QA Score: {summary['qa_score']}</div>
<div class="metric">Build Size: {summary['build_size']}</div>
<div class="metric">Execution Time: {summary['execution_time']}</div>
<h2>Details</h2>
<pre>{json.dumps(self.results, indent=2)}</pre>
</body></html>'''
        
        html_file = report_file.replace('.json', '.html')
        with open(html_file, 'w') as f:
            f.write(html_content)
        
        print(f"✅ Report saved: {report_file}")
        return report_file
    
    def run_all(self):
        """Run all tests with ultra-compressed mode"""
        print("🚀 Ultra-Compressed QA Test Runner")
        print("Flags: --e2e --coverage --uc --persona-qa --pup")
        print("-" * 50)
        
        success = True
        
        try:
            # 1. Unit tests with coverage (--coverage --uc)
            if not self.unit_coverage():
                success = False
            
            # 2. E2E tests (--e2e)
            if not self.e2e_tests():
                success = False
            
            # 3. QA persona validation (--persona-qa)
            if not self.qa_persona():
                success = False
            
            # 4. Performance profiling (--pup)
            self.performance_profiling()
            
            # 5. Generate report
            report_file = self.generate_report()
            
            print("-" * 50)
            print(f"{'✅ SUCCESS' if success else '❌ FAILED'} | Report: {report_file}")
            
            return success
            
        except Exception as e:
            print(f"❌ ERROR: {e}")
            return False

if __name__ == "__main__":
    runner = UltraCompressedQARunner()
    success = runner.run_all()
    exit(0 if success else 1)