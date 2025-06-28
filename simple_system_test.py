#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
온라인 평가 시스템 간단 테스트
기본 라이브러리만 사용하여 시스템 상태를 확인합니다.
"""

import urllib.request
import urllib.error
import json
import time
import os
import sys
from datetime import datetime

class SimpleSystemTester:
    """간단한 시스템 테스트 클래스"""
    
    def __init__(self):
        self.backend_url = os.getenv('BACKEND_URL', 'http://localhost:8081')
        self.frontend_url = os.getenv('FRONTEND_URL', 'http://localhost:3000')
        self.results = []
        
    def log_result(self, test_name, passed, details=""):
        """테스트 결과 로깅"""
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{status} - {test_name}")
        if details:
            print(f"    {details}")
        
        self.results.append({
            'test': test_name,
            'passed': passed,
            'details': details,
            'timestamp': datetime.now().isoformat()
        })
    
    def test_backend_health(self):
        """백엔드 헬스 체크"""
        try:
            with urllib.request.urlopen(f"{self.backend_url}/health", timeout=10) as response:
                if response.status == 200:
                    data = json.loads(response.read().decode())
                    self.log_result("Backend Health", True, f"Status: {data.get('status', 'OK')}")
                    return True
                else:
                    self.log_result("Backend Health", False, f"HTTP {response.status}")
                    return False
        except Exception as e:
            self.log_result("Backend Health", False, f"Error: {str(e)}")
            return False
    
    def test_backend_api(self):
        """백엔드 API 기본 엔드포인트 테스트"""
        try:
            # 인증이 필요한 엔드포인트 - 401 응답이 정상
            with urllib.request.urlopen(f"{self.backend_url}/api/dashboard/statistics", timeout=10) as response:
                pass
        except urllib.error.HTTPError as e:
            if e.code == 401:
                self.log_result("Backend API", True, "API endpoints responding (auth required)")
                return True
            else:
                self.log_result("Backend API", False, f"HTTP {e.code}")
                return False
        except Exception as e:
            self.log_result("Backend API", False, f"Error: {str(e)}")
            return False
    
    def test_frontend_access(self):
        """프론트엔드 접근성 테스트"""
        try:
            with urllib.request.urlopen(f"{self.frontend_url}", timeout=10) as response:
                if response.status == 200:
                    content = response.read().decode()
                    if 'root' in content or 'React' in content:
                        self.log_result("Frontend Access", True, "Frontend is accessible")
                        return True
                    else:
                        self.log_result("Frontend Access", False, "Unexpected content")
                        return False
                else:
                    self.log_result("Frontend Access", False, f"HTTP {response.status}")
                    return False
        except Exception as e:
            self.log_result("Frontend Access", False, f"Error: {str(e)}")
            return False
    
    def check_required_files(self):
        """필수 파일 존재 확인"""
        required_files = [
            'backend/server.py',
            'frontend/package.json',
            'frontend/src/App.js',
            'docker-compose.yml',
            'requirements.txt'
        ]
        
        missing_files = []
        for file_path in required_files:
            if not os.path.exists(file_path):
                missing_files.append(file_path)
        
        if not missing_files:
            self.log_result("Required Files", True, "All required files present")
            return True
        else:
            self.log_result("Required Files", False, f"Missing: {', '.join(missing_files)}")
            return False
    
    def check_environment_files(self):
        """환경 설정 파일 확인"""
        env_files = [
            'backend/.env',
            'frontend/.env'
        ]
        
        missing_env = []
        for env_file in env_files:
            if not os.path.exists(env_file):
                missing_env.append(env_file)
        
        if not missing_env:
            self.log_result("Environment Files", True, "Environment files present")
            return True
        else:
            self.log_result("Environment Files", False, f"Missing: {', '.join(missing_env)}")
            return False
    
    def run_all_tests(self):
        """모든 테스트 실행"""
        print("🚀 온라인 평가 시스템 기본 테스트 시작")
        print(f"Backend URL: {self.backend_url}")
        print(f"Frontend URL: {self.frontend_url}")
        print("=" * 50)
        
        # 파일 시스템 테스트
        self.check_required_files()
        self.check_environment_files()
        
        # 서비스 테스트
        self.test_backend_health()
        self.test_backend_api()
        self.test_frontend_access()
        
        # 결과 요약
        total_tests = len(self.results)
        passed_tests = sum(1 for result in self.results if result['passed'])
        failed_tests = total_tests - passed_tests
        
        print("=" * 50)
        print("📊 테스트 결과 요약")
        print(f"총 테스트: {total_tests}")
        print(f"성공: {passed_tests}")
        print(f"실패: {failed_tests}")
        
        success_rate = (passed_tests / max(total_tests, 1)) * 100
        print(f"성공률: {success_rate:.1f}%")
        
        if success_rate >= 80:
            print("✅ 시스템 상태: 양호")
            status = "GOOD"
        elif success_rate >= 60:
            print("⚠️ 시스템 상태: 주의")
            status = "WARNING"
        else:
            print("❌ 시스템 상태: 불량")
            status = "ERROR"
        
        # 결과를 파일로 저장
        report = {
            'timestamp': datetime.now().isoformat(),
            'total_tests': total_tests,
            'passed_tests': passed_tests,
            'failed_tests': failed_tests,
            'success_rate': success_rate,
            'status': status,
            'details': self.results
        }
        
        report_file = f"simple_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        try:
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(report, f, ensure_ascii=False, indent=2)
            print(f"📄 리포트 저장됨: {report_file}")
        except Exception as e:
            print(f"리포트 저장 실패: {e}")
        
        return report

def main():
    """메인 실행 함수"""
    tester = SimpleSystemTester()
    results = tester.run_all_tests()
    
    # 종료 코드 설정
    if results['failed_tests'] == 0:
        sys.exit(0)
    else:
        sys.exit(1)

if __name__ == "__main__":
    main()