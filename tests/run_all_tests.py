#!/usr/bin/env python3
"""
Comprehensive Test Runner for Online Evaluation System
Runs all types of tests: unit, integration, E2E, performance, and accessibility
"""

import os
import sys
import subprocess
import json
import time
from datetime import datetime
from typing import Dict, List, Any
import argparse


class TestRunner:
    def __init__(self):
        self.project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.results = {
            'test_run_id': f"comprehensive_test_{int(time.time())}",
            'start_time': datetime.now().isoformat(),
            'test_suites': {},
            'summary': {
                'total_suites': 0,
                'passed_suites': 0,
                'failed_suites': 0,
                'total_tests': 0,
                'passed_tests': 0,
                'failed_tests': 0,
                'skipped_tests': 0
            }
        }
    
    def run_command(self, command: List[str], cwd: str = None, timeout: int = 300) -> Dict[str, Any]:
        """Run a command and return results"""
        try:
            print(f"🏃 Running: {' '.join(command)}")
            if cwd:
                print(f"📁 Working directory: {cwd}")
            
            start_time = time.time()
            
            result = subprocess.run(
                command,
                cwd=cwd or self.project_root,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            
            end_time = time.time()
            duration = end_time - start_time
            
            return {
                'success': result.returncode == 0,
                'returncode': result.returncode,
                'stdout': result.stdout,
                'stderr': result.stderr,
                'duration': duration
            }
            
        except subprocess.TimeoutExpired:
            return {
                'success': False,
                'returncode': -1,
                'stdout': '',
                'stderr': f'Command timed out after {timeout} seconds',
                'duration': timeout
            }
        except Exception as e:
            return {
                'success': False,
                'returncode': -1,
                'stdout': '',
                'stderr': str(e),
                'duration': 0
            }
    
    def check_dependencies(self) -> bool:
        """Check if all required dependencies are available"""
        print("🔍 Checking dependencies...")
        
        dependencies = [
            {
                'name': 'Node.js',
                'command': ['node', '--version'],
                'required': True
            },
            {
                'name': 'npm',
                'command': ['npm', '--version'],
                'required': True
            },
            {
                'name': 'Python',
                'command': ['python', '--version'],
                'required': True
            },
            {
                'name': 'Playwright',
                'command': ['npx', 'playwright', '--version'],
                'required': False
            },
            {
                'name': 'pytest',
                'command': ['python', '-m', 'pytest', '--version'],
                'required': False
            }
        ]
        
        all_required_available = True
        
        for dep in dependencies:
            result = self.run_command(dep['command'], timeout=10)
            status = "✅" if result['success'] else "❌"
            
            print(f"{status} {dep['name']}: {'Available' if result['success'] else 'Not available'}")
            
            if dep['required'] and not result['success']:
                all_required_available = False
        
        return all_required_available
    
    def run_backend_tests(self) -> Dict[str, Any]:
        """Run backend Python tests"""
        print("\n🐍 Running Backend Tests...")
        
        backend_dir = os.path.join(self.project_root, 'backend')
        
        # Check if pytest is available
        pytest_check = self.run_command(['python', '-m', 'pytest', '--version'])
        if not pytest_check['success']:
            return {
                'status': 'skipped',
                'reason': 'pytest not available',
                'tests': 0,
                'passed': 0,
                'failed': 0
            }
        
        # Run pytest with coverage if available
        pytest_command = [
            'python', '-m', 'pytest',
            '--tb=short',
            '--durations=10',
            '-v'
        ]
        
        # Add coverage if available
        coverage_check = self.run_command(['python', '-m', 'coverage', '--version'])
        if coverage_check['success']:
            pytest_command.extend(['--cov=.', '--cov-report=term-missing'])
        
        result = self.run_command(pytest_command, cwd=backend_dir, timeout=600)
        
        # Parse pytest output for test counts
        test_counts = self.parse_pytest_output(result['stdout'])
        
        return {
            'status': 'passed' if result['success'] else 'failed',
            'returncode': result['returncode'],
            'duration': result['duration'],
            'output': result['stdout'],
            'error': result['stderr'],
            **test_counts
        }
    
    def run_frontend_tests(self) -> Dict[str, Any]:
        """Run frontend JavaScript/React tests with coverage analysis"""
        print("\n⚛️ Running Frontend Tests...")
        
        frontend_dir = os.path.join(self.project_root, 'frontend')
        
        # Check if we can run npm test
        package_json_path = os.path.join(frontend_dir, 'package.json')
        if not os.path.exists(package_json_path):
            return {
                'status': 'skipped',
                'reason': 'No package.json found in frontend directory',
                'tests': 0,
                'passed': 0,
                'failed': 0,
                'coverage': {}
            }
        
        # Install dependencies first
        print("📦 Installing frontend dependencies...")
        install_result = self.run_command(['npm', 'install'], cwd=frontend_dir, timeout=300)
        
        if not install_result['success']:
            return {
                'status': 'failed',
                'reason': 'npm install failed',
                'error': install_result['stderr'],
                'tests': 0,
                'passed': 0,
                'failed': 0,
                'coverage': {}
            }
        
        # Run tests with coverage
        print("🧪 Running Jest tests with coverage analysis...")
        test_result = self.run_command(
            ['npm', 'test', '--', '--watchAll=false', '--coverage', '--coverageReporters=json', '--coverageReporters=text'],
            cwd=frontend_dir,
            timeout=300
        )
        
        # Parse Jest output for test counts
        test_counts = self.parse_jest_output(test_result['stdout'])
        
        # Parse coverage data
        coverage_data = self.parse_jest_coverage(frontend_dir)
        
        # Analyze component coverage
        component_analysis = self.analyze_component_coverage(frontend_dir)
        
        return {
            'status': 'passed' if test_result['success'] else 'failed',
            'returncode': test_result['returncode'],
            'duration': test_result['duration'],
            'output': test_result['stdout'],
            'error': test_result['stderr'],
            'coverage': coverage_data,
            'component_analysis': component_analysis,
            **test_counts
        }
    
    def parse_jest_coverage(self, frontend_dir: str) -> Dict[str, Any]:
        """Parse Jest coverage report"""
        coverage_file = os.path.join(frontend_dir, 'coverage', 'coverage-final.json')
        
        if not os.path.exists(coverage_file):
            return {
                'error': 'Coverage file not found',
                'overall': {'lines': 0, 'functions': 0, 'branches': 0, 'statements': 0}
            }
        
        try:
            with open(coverage_file, 'r') as f:
                coverage_data = json.load(f)
            
            # Calculate overall coverage
            total_coverage = {
                'lines': {'covered': 0, 'total': 0, 'percentage': 0},
                'functions': {'covered': 0, 'total': 0, 'percentage': 0},
                'branches': {'covered': 0, 'total': 0, 'percentage': 0},
                'statements': {'covered': 0, 'total': 0, 'percentage': 0}
            }
            
            file_coverage = {}
            
            for file_path, file_data in coverage_data.items():
                # Skip node_modules and test files
                if 'node_modules' in file_path or '.test.' in file_path:
                    continue
                
                relative_path = file_path.replace(self.project_root, '').lstrip('/')
                
                # Extract coverage metrics
                lines_data = file_data.get('l', {})
                functions_data = file_data.get('f', {})
                branches_data = file_data.get('b', {})
                statements_data = file_data.get('s', {})
                
                file_metrics = {
                    'lines': {
                        'total': len(lines_data),
                        'covered': sum(1 for v in lines_data.values() if v > 0),
                        'percentage': 0
                    },
                    'functions': {
                        'total': len(functions_data),
                        'covered': sum(1 for v in functions_data.values() if v > 0),
                        'percentage': 0
                    },
                    'branches': {
                        'total': len(branches_data),
                        'covered': sum(1 for branch_set in branches_data.values() 
                                     for v in branch_set if v > 0),
                        'percentage': 0
                    },
                    'statements': {
                        'total': len(statements_data),
                        'covered': sum(1 for v in statements_data.values() if v > 0),
                        'percentage': 0
                    }
                }
                
                # Calculate percentages
                for metric in ['lines', 'functions', 'branches', 'statements']:
                    if file_metrics[metric]['total'] > 0:
                        file_metrics[metric]['percentage'] = (
                            file_metrics[metric]['covered'] / file_metrics[metric]['total'] * 100
                        )
                    
                    # Add to totals
                    total_coverage[metric]['total'] += file_metrics[metric]['total']
                    total_coverage[metric]['covered'] += file_metrics[metric]['covered']
                
                file_coverage[relative_path] = file_metrics
            
            # Calculate overall percentages
            for metric in ['lines', 'functions', 'branches', 'statements']:
                if total_coverage[metric]['total'] > 0:
                    total_coverage[metric]['percentage'] = (
                        total_coverage[metric]['covered'] / total_coverage[metric]['total'] * 100
                    )
            
            return {
                'overall': total_coverage,
                'files': file_coverage,
                'thresholds': {
                    'lines': 80,
                    'functions': 80,
                    'branches': 75,
                    'statements': 80
                }
            }
            
        except Exception as e:
            return {
                'error': f'Failed to parse coverage: {str(e)}',
                'overall': {'lines': 0, 'functions': 0, 'branches': 0, 'statements': 0}
            }
    
    def analyze_component_coverage(self, frontend_dir: str) -> Dict[str, Any]:
        """Analyze React component test coverage"""
        components_dir = os.path.join(frontend_dir, 'src', 'components')
        tests_dir = os.path.join(frontend_dir, 'src', 'components', '__tests__')
        
        analysis = {
            'total_components': 0,
            'tested_components': 0,
            'untested_components': [],
            'test_coverage_percentage': 0,
            'recommendations': []
        }
        
        if not os.path.exists(components_dir):
            analysis['recommendations'].append("⚠️ Components directory not found")
            return analysis
        
        # Find all React components
        component_files = []
        for root, dirs, files in os.walk(components_dir):
            for file in files:
                if file.endswith('.js') and not file.startswith('.') and '__tests__' not in root:
                    component_files.append(file)
        
        analysis['total_components'] = len(component_files)
        
        # Find corresponding test files
        tested_components = []
        if os.path.exists(tests_dir):
            for root, dirs, files in os.walk(tests_dir):
                for file in files:
                    if file.endswith('.test.js'):
                        component_name = file.replace('.test.js', '.js')
                        if component_name in component_files:
                            tested_components.append(component_name)
        
        analysis['tested_components'] = len(tested_components)
        analysis['untested_components'] = [c for c in component_files if c not in tested_components]
        
        if analysis['total_components'] > 0:
            analysis['test_coverage_percentage'] = (
                analysis['tested_components'] / analysis['total_components'] * 100
            )
        
        # Generate recommendations
        if analysis['test_coverage_percentage'] < 50:
            analysis['recommendations'].append(
                f"❌ Only {analysis['test_coverage_percentage']:.1f}% of components have tests - should be >50%"
            )
        elif analysis['test_coverage_percentage'] < 80:
            analysis['recommendations'].append(
                f"⚠️ {analysis['test_coverage_percentage']:.1f}% component test coverage - should be >80%"
            )
        
        if analysis['untested_components']:
            top_untested = analysis['untested_components'][:5]
            analysis['recommendations'].append(
                f"📝 Add tests for: {', '.join(top_untested)}" + 
                (f" and {len(analysis['untested_components']) - 5} more" if len(analysis['untested_components']) > 5 else "")
            )
        
        return analysis
    
    def run_integration_tests(self) -> Dict[str, Any]:
        """Run API integration tests"""
        print("\n🔗 Running Integration Tests...")
        
        integration_test_path = os.path.join(
            self.project_root, 'tests', 'integration', 'test_api_integration.py'
        )
        
        if not os.path.exists(integration_test_path):
            return {
                'status': 'skipped',
                'reason': 'Integration test file not found',
                'tests': 0,
                'passed': 0,
                'failed': 0
            }
        
        # Run the integration test
        result = self.run_command(
            ['python', integration_test_path],
            timeout=600
        )
        
        # Try to parse JSON results if available
        results_files = [f for f in os.listdir(self.project_root) 
                        if f.startswith('integration_test_results_') and f.endswith('.json')]
        
        test_counts = {'tests': 0, 'passed': 0, 'failed': 0}
        
        if results_files:
            try:
                latest_results = sorted(results_files)[-1]
                with open(os.path.join(self.project_root, latest_results), 'r') as f:
                    integration_data = json.load(f)
                
                summary = integration_data.get('summary', {})
                test_counts = {
                    'tests': summary.get('total_tests', 0),
                    'passed': summary.get('passed', 0),
                    'failed': summary.get('failed', 0)
                }
            except Exception as e:
                print(f"Warning: Could not parse integration test results: {e}")
        
        return {
            'status': 'passed' if result['success'] else 'failed',
            'returncode': result['returncode'],
            'duration': result['duration'],
            'output': result['stdout'],
            'error': result['stderr'],
            **test_counts
        }
    
    def run_e2e_tests(self) -> Dict[str, Any]:
        """Run end-to-end Playwright tests"""
        print("\n🎭 Running E2E Tests...")
        
        # Check if Playwright is installed
        playwright_check = self.run_command(['npx', 'playwright', '--version'])
        if not playwright_check['success']:
            return {
                'status': 'skipped',
                'reason': 'Playwright not available',
                'tests': 0,
                'passed': 0,
                'failed': 0,
                'browser_results': {}
            }
        
        # Install Playwright browsers if needed
        print("🌐 Installing Playwright browsers...")
        install_result = self.run_command(
            ['npx', 'playwright', 'install'],
            timeout=300
        )
        
        # Run comprehensive E2E test suites
        e2e_suites = {
            'navigation': 'tests/e2e/navigation-enhancement.spec.js',
            'critical_functions': 'tests/e2e/critical-functions.spec.js',
            'auth': 'tests/e2e/auth.spec.js',
            'system': 'tests/e2e/system.spec.js',
            'workflow': 'tests/e2e/workflow.spec.js'
        }
        
        suite_results = {}
        total_tests = total_passed = total_failed = 0
        overall_duration = 0
        
        for suite_name, suite_file in e2e_suites.items():
            print(f"🧪 Running {suite_name} E2E tests...")
            
            # Set test environment headers
            test_env = os.environ.copy()
            test_env.update({
                'X_TEST_ENVIRONMENT': 'true',
                'X_E2E_TEST': f'{suite_name}-suite'
            })
            
            test_command = [
                'npx', 'playwright', 'test',
                suite_file,
                '--reporter=json',
                '--project=chromium'  # Default to chromium for speed
            ]
            
            # Check if suite file exists
            suite_path = os.path.join(self.project_root, suite_file)
            if not os.path.exists(suite_path):
                suite_results[suite_name] = {
                    'status': 'skipped',
                    'reason': f'Test file not found: {suite_file}',
                    'tests': 0,
                    'passed': 0,
                    'failed': 0
                }
                continue
            
            result = self.run_command(test_command, timeout=600)  # 10 minutes per suite
            
            # Parse Playwright JSON output
            test_counts = self.parse_playwright_output(result['stdout'])
            
            suite_results[suite_name] = {
                'status': 'passed' if result['success'] else 'failed',
                'returncode': result['returncode'],
                'duration': result['duration'],
                'output': result['stdout'],
                'error': result['stderr'],
                **test_counts
            }
            
            total_tests += test_counts['tests']
            total_passed += test_counts['passed']
            total_failed += test_counts['failed']
            overall_duration += result['duration']
        
        # Run additional cross-browser tests if time permits
        browser_results = {}
        if total_failed == 0:  # Only run cross-browser if basic tests pass
            print("🌐 Running cross-browser compatibility tests...")
            for browser in ['firefox', 'webkit']:
                browser_command = [
                    'npx', 'playwright', 'test',
                    'tests/e2e/auth.spec.js',  # Quick auth test for each browser
                    f'--project={browser}',
                    '--reporter=json'
                ]
                
                browser_result = self.run_command(browser_command, timeout=300)
                browser_counts = self.parse_playwright_output(browser_result['stdout'])
                browser_results[browser] = {
                    'status': 'passed' if browser_result['success'] else 'failed',
                    **browser_counts
                }
        
        return {
            'status': 'passed' if total_failed == 0 else 'failed',
            'tests': total_tests,
            'passed': total_passed,
            'failed': total_failed,
            'duration': overall_duration,
            'suite_results': suite_results,
            'browser_results': browser_results
        }
    
    def run_performance_tests(self) -> Dict[str, Any]:
        """Run performance tests including Lighthouse audits"""
        print("\n⚡ Running Performance Tests...")
        
        performance_results = {
            'lighthouse_audits': {},
            'playwright_performance': {},
            'python_performance': {}
        }
        
        total_tests = total_passed = total_failed = 0
        overall_duration = 0
        
        # 1. Run Lighthouse audits via Playwright
        lighthouse_file = os.path.join(self.project_root, 'tests/performance/lighthouse-audit.spec.js')
        if os.path.exists(lighthouse_file):
            print("🚀 Running Lighthouse performance audits...")
            
            lighthouse_command = [
                'npx', 'playwright', 'test',
                lighthouse_file,
                '--reporter=json'
            ]
            
            lighthouse_result = self.run_command(lighthouse_command, timeout=600)
            lighthouse_counts = self.parse_playwright_output(lighthouse_result['stdout'])
            
            performance_results['lighthouse_audits'] = {
                'status': 'passed' if lighthouse_result['success'] else 'failed',
                'duration': lighthouse_result['duration'],
                **lighthouse_counts
            }
            
            total_tests += lighthouse_counts['tests']
            total_passed += lighthouse_counts['passed']
            total_failed += lighthouse_counts['failed']
            overall_duration += lighthouse_result['duration']
        
        # 2. Look for other performance test files
        perf_test_files = []
        tests_dir = os.path.join(self.project_root, 'tests')
        
        for root, dirs, files in os.walk(tests_dir):
            for file in files:
                if ('performance' in file.lower() and 
                    file.endswith(('.py', '.js', '.spec.js')) and 
                    'lighthouse-audit.spec.js' not in file):
                    perf_test_files.append(os.path.join(root, file))
        
        # 3. Run Python performance tests
        python_perf_files = [f for f in perf_test_files if f.endswith('.py')]
        if python_perf_files:
            print("🐍 Running Python performance tests...")
            python_results = []
            
            for test_file in python_perf_files:
                result = self.run_command(['python', test_file], timeout=300)
                python_results.append({
                    'file': os.path.basename(test_file),
                    'success': result['success'],
                    'duration': result['duration'],
                    'output': result['stdout'][:500] if result['stdout'] else '',
                    'error': result['stderr'][:500] if result['stderr'] else ''
                })
                
                total_tests += 1
                if result['success']:
                    total_passed += 1
                else:
                    total_failed += 1
                overall_duration += result['duration']
            
            performance_results['python_performance'] = {
                'status': 'passed' if all(r['success'] for r in python_results) else 'failed',
                'tests_run': len(python_results),
                'results': python_results
            }
        
        # 4. Run Playwright performance tests (non-Lighthouse)
        playwright_perf_files = [f for f in perf_test_files if f.endswith('.spec.js')]
        if playwright_perf_files:
            print("🎭 Running Playwright performance tests...")
            playwright_results = []
            
            for test_file in playwright_perf_files:
                result = self.run_command(
                    ['npx', 'playwright', 'test', test_file],
                    timeout=300
                )
                test_counts = self.parse_playwright_output(result['stdout'])
                
                playwright_results.append({
                    'file': os.path.basename(test_file),
                    'success': result['success'],
                    'duration': result['duration'],
                    **test_counts
                })
                
                total_tests += test_counts['tests']
                total_passed += test_counts['passed']
                total_failed += test_counts['failed']
                overall_duration += result['duration']
            
            performance_results['playwright_performance'] = {
                'status': 'passed' if all(r['success'] for r in playwright_results) else 'failed',
                'results': playwright_results
            }
        
        # 5. Generate performance recommendations
        recommendations = []
        if performance_results['lighthouse_audits'].get('status') == 'failed':
            recommendations.append("⚠️ Lighthouse audits failed - check page performance metrics")
        
        if total_failed > 0:
            recommendations.append(f"❌ {total_failed} performance tests failed - review performance bottlenecks")
        
        if not performance_results['lighthouse_audits']:
            recommendations.append("💡 Consider adding Lighthouse audits for automated performance monitoring")
        
        overall_status = 'passed' if total_failed == 0 else 'failed'
        if total_tests == 0:
            overall_status = 'skipped'
            recommendations.append("⚠️ No performance tests found - add performance test coverage")
        
        return {
            'status': overall_status,
            'tests': total_tests,
            'passed': total_passed,
            'failed': total_failed,
            'duration': overall_duration,
            'detailed_results': performance_results,
            'recommendations': recommendations
        }
    
    def run_security_tests(self) -> Dict[str, Any]:
        """Run security tests"""
        print("\n🔒 Running Security Tests...")
        
        security_checks = []
        
        # Check for common security tools
        tools = [
            {
                'name': 'bandit',
                'command': ['python', '-m', 'bandit', '-r', 'backend/', '-f', 'json'],
                'type': 'python_security'
            },
            {
                'name': 'npm audit',
                'command': ['npm', 'audit', '--json'],
                'type': 'npm_security',
                'cwd': 'frontend'
            },
            {
                'name': 'safety',
                'command': ['python', '-m', 'safety', 'check', '--json'],
                'type': 'python_dependencies'
            }
        ]
        
        results = []
        issues_found = 0
        
        for tool in tools:
            print(f"🔍 Running {tool['name']}...")
            
            cwd = os.path.join(self.project_root, tool.get('cwd', '')) if tool.get('cwd') else self.project_root
            result = self.run_command(tool['command'], cwd=cwd, timeout=120)
            
            # Security tools often return non-zero for issues found
            tool_result = {
                'tool': tool['name'],
                'type': tool['type'],
                'success': result['returncode'] == 0,
                'output': result['stdout'],
                'error': result['stderr'],
                'duration': result['duration']
            }
            
            # Try to parse JSON output for issue counts
            if result['stdout']:
                try:
                    if tool['name'] == 'npm audit':
                        audit_data = json.loads(result['stdout'])
                        vulnerabilities = audit_data.get('metadata', {}).get('vulnerabilities', {})
                        tool_result['issues'] = sum(vulnerabilities.values())
                    elif tool['name'] == 'bandit':
                        bandit_data = json.loads(result['stdout'])
                        tool_result['issues'] = len(bandit_data.get('results', []))
                    else:
                        tool_result['issues'] = 0
                except json.JSONDecodeError:
                    tool_result['issues'] = 0
            else:
                tool_result['issues'] = 0
            
            issues_found += tool_result.get('issues', 0)
            results.append(tool_result)
        
        return {
            'status': 'passed' if issues_found == 0 else 'warning',
            'total_issues': issues_found,
            'tools_run': len(results),
            'results': results
        }
    
    def parse_pytest_output(self, output: str) -> Dict[str, int]:
        """Parse pytest output for test counts"""
        import re
        
        # Look for pytest summary line
        patterns = [
            r'=+ (\d+) passed.*in [\d\.]+s =+',
            r'=+ (\d+) failed, (\d+) passed.*in [\d\.]+s =+',
            r'=+ (\d+) passed, (\d+) skipped.*in [\d\.]+s =+',
            r'=+ (\d+) failed.*in [\d\.]+s =+'
        ]
        
        tests = passed = failed = skipped = 0
        
        for pattern in patterns:
            match = re.search(pattern, output)
            if match:
                numbers = [int(x) for x in match.groups()]
                if 'passed' in pattern and 'failed' in pattern:
                    failed, passed = numbers
                elif 'passed' in pattern and 'skipped' in pattern:
                    passed, skipped = numbers
                elif 'failed' in pattern:
                    failed = numbers[0]
                elif 'passed' in pattern:
                    passed = numbers[0]
                break
        
        tests = passed + failed + skipped
        
        return {
            'tests': tests,
            'passed': passed,
            'failed': failed,
            'skipped': skipped
        }
    
    def parse_jest_output(self, output: str) -> Dict[str, int]:
        """Parse Jest output for test counts"""
        import re
        
        # Look for Jest summary
        test_pattern = r'Tests:\s+(\d+) passed,\s+(\d+) total'
        match = re.search(test_pattern, output)
        
        if match:
            passed, total = map(int, match.groups())
            failed = total - passed
            return {
                'tests': total,
                'passed': passed,
                'failed': failed,
                'skipped': 0
            }
        
        return {'tests': 0, 'passed': 0, 'failed': 0, 'skipped': 0}
    
    def parse_playwright_output(self, output: str) -> Dict[str, int]:
        """Parse Playwright JSON output for test counts"""
        try:
            if output.strip():
                data = json.loads(output)
                stats = data.get('stats', {})
                
                return {
                    'tests': stats.get('total', 0),
                    'passed': stats.get('passed', 0),
                    'failed': stats.get('failed', 0),
                    'skipped': stats.get('skipped', 0)
                }
        except json.JSONDecodeError:
            pass
        
        return {'tests': 0, 'passed': 0, 'failed': 0, 'skipped': 0}
    
    def run_all_tests(self, suites: List[str] = None) -> Dict[str, Any]:
        """Run all test suites"""
        print("🚀 Starting Comprehensive Test Run...")
        print(f"📅 Started at: {self.results['start_time']}")
        
        # Check dependencies first
        if not self.check_dependencies():
            print("❌ Required dependencies missing. Aborting test run.")
            return self.results
        
        # Define available test suites
        available_suites = {
            'backend': self.run_backend_tests,
            'frontend': self.run_frontend_tests,
            'integration': self.run_integration_tests,
            'e2e': self.run_e2e_tests,
            'performance': self.run_performance_tests,
            'security': self.run_security_tests
        }
        
        # Determine which suites to run
        if suites is None:
            suites_to_run = list(available_suites.keys())
        else:
            suites_to_run = [s for s in suites if s in available_suites]
        
        print(f"🎯 Running test suites: {', '.join(suites_to_run)}")
        
        # Run each suite
        for suite_name in suites_to_run:
            print(f"\\n{'='*60}")
            print(f"🧪 RUNNING {suite_name.upper()} TESTS")
            print(f"{'='*60}")
            
            suite_func = available_suites[suite_name]
            suite_result = suite_func()
            
            self.results['test_suites'][suite_name] = suite_result
            self.results['summary']['total_suites'] += 1
            
            # Update summary
            if suite_result['status'] == 'passed':
                self.results['summary']['passed_suites'] += 1
            elif suite_result['status'] == 'failed':
                self.results['summary']['failed_suites'] += 1
            
            # Add test counts
            if 'tests' in suite_result:
                self.results['summary']['total_tests'] += suite_result['tests']
            if 'passed' in suite_result:
                self.results['summary']['passed_tests'] += suite_result['passed']
            if 'failed' in suite_result:
                self.results['summary']['failed_tests'] += suite_result['failed']
            if 'skipped' in suite_result:
                self.results['summary']['skipped_tests'] += suite_result['skipped']
            
            # Print suite result
            status_emoji = {
                'passed': '✅',
                'failed': '❌',
                'skipped': '⏭️',
                'warning': '⚠️'
            }.get(suite_result['status'], '❓')
            
            print(f"\\n{status_emoji} {suite_name.upper()} TESTS: {suite_result['status'].upper()}")
            
            if 'tests' in suite_result:
                print(f"   Tests: {suite_result['tests']} | "
                      f"Passed: {suite_result['passed']} | "
                      f"Failed: {suite_result['failed']}")
        
        # Finalize results
        self.results['end_time'] = datetime.now().isoformat()
        self.results['duration'] = (
            datetime.fromisoformat(self.results['end_time']) - 
            datetime.fromisoformat(self.results['start_time'])
        ).total_seconds()
        
        return self.results
    
    def print_summary(self):
        """Print comprehensive test summary"""
        results = self.results
        summary = results['summary']
        
        print("\\n" + "="*80)
        print("📊 COMPREHENSIVE TEST RESULTS SUMMARY")
        print("="*80)
        print(f"🆔 Test Run ID: {results['test_run_id']}")
        print(f"⏱️  Duration: {results.get('duration', 0):.2f} seconds")
        print(f"📅 Started: {results['start_time']}")
        print(f"🏁 Finished: {results.get('end_time', 'Unknown')}")
        
        print(f"\\n📋 Test Suite Summary:")
        print(f"   Total Suites: {summary['total_suites']}")
        print(f"   ✅ Passed: {summary['passed_suites']}")
        print(f"   ❌ Failed: {summary['failed_suites']}")
        
        print(f"\\n🧪 Individual Test Summary:")
        print(f"   Total Tests: {summary['total_tests']}")
        print(f"   ✅ Passed: {summary['passed_tests']}")
        print(f"   ❌ Failed: {summary['failed_tests']}")
        print(f"   ⏭️  Skipped: {summary['skipped_tests']}")
        
        if summary['total_tests'] > 0:
            pass_rate = (summary['passed_tests'] / summary['total_tests']) * 100
            print(f"   📈 Pass Rate: {pass_rate:.1f}%")
        
        print(f"\\n📄 Detailed Results by Suite:")
        for suite_name, suite_result in results['test_suites'].items():
            status_emoji = {
                'passed': '✅',
                'failed': '❌',
                'skipped': '⏭️',
                'warning': '⚠️'
            }.get(suite_result['status'], '❓')
            
            print(f"   {status_emoji} {suite_name.ljust(12)}: {suite_result['status']}")
            
            if 'tests' in suite_result and suite_result['tests'] > 0:
                print(f"      Tests: {suite_result['tests']} | "
                      f"Passed: {suite_result['passed']} | "
                      f"Failed: {suite_result['failed']}")
            
            if suite_result['status'] == 'failed' and 'error' in suite_result:
                print(f"      Error: {suite_result['error'][:100]}...")
        
        # Overall status
        overall_status = "PASSED" if summary['failed_suites'] == 0 else "FAILED"
        status_emoji = "✅" if overall_status == "PASSED" else "❌"
        
        print(f"\\n{status_emoji} OVERALL STATUS: {overall_status}")
        print("="*80)
    
    def save_results(self, filename: str = None):
        """Save test results to JSON file"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"comprehensive_test_results_{timestamp}.json"
        
        filepath = os.path.join(self.project_root, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False, default=str)
        
        print(f"💾 Test results saved to: {filepath}")
        return filepath


def main():
    """Main function"""
    parser = argparse.ArgumentParser(
        description="Run comprehensive tests for Online Evaluation System"
    )
    parser.add_argument(
        '--suites',
        nargs='+',
        choices=['backend', 'frontend', 'integration', 'e2e', 'performance', 'security'],
        help='Test suites to run (default: all)'
    )
    parser.add_argument(
        '--output',
        '-o',
        help='Output file for test results'
    )
    parser.add_argument(
        '--quiet',
        '-q',
        action='store_true',
        help='Reduce output verbosity'
    )
    
    args = parser.parse_args()
    
    # Create test runner
    runner = TestRunner()
    
    # Run tests
    results = runner.run_all_tests(suites=args.suites)
    
    # Print summary unless quiet
    if not args.quiet:
        runner.print_summary()
    
    # Save results
    runner.save_results(args.output)
    
    # Exit with appropriate code
    exit_code = 0 if results['summary']['failed_suites'] == 0 else 1
    print(f"\\n🏁 Test run completed with exit code: {exit_code}")
    
    return exit_code


if __name__ == "__main__":
    exit(main())