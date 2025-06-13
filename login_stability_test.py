#!/usr/bin/env python3
"""
로그인 기능 안정성 테스트 스크립트
간헐적 로그인 실패 문제를 진단하고 해결하기 위한 종합 테스트
"""

import requests
import time
import json
import threading
from datetime import datetime
import statistics

# 설정
BACKEND_URL = "http://localhost:8000"
FRONTEND_URL = "http://localhost:3000"
API_BASE = f"{BACKEND_URL}/api"

# 테스트 계정
TEST_ACCOUNTS = [
    {"username": "admin", "password": "admin123", "role": "admin"},
    {"username": "secretary01", "password": "secretary123", "role": "secretary"},
    {"username": "evaluator01", "password": "evaluator123", "role": "evaluator"}
]

class LoginStabilityTester:
    def __init__(self):
        self.results = []
        self.session = requests.Session()
        
    def test_backend_health(self):
        """백엔드 서버 상태 확인"""
        print("🏥 백엔드 서버 상태 확인...")
        try:
            response = self.session.get(f"{BACKEND_URL}/health", timeout=5)
            if response.status_code == 200:
                health_data = response.json()
                print(f"✅ 백엔드 서버 정상 - 상태: {health_data.get('status', 'unknown')}")
                services = health_data.get('services', {})
                for service, status in services.items():
                    print(f"   - {service}: {status}")
                return True
            else:
                print(f"❌ 백엔드 서버 응답 오류: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ 백엔드 서버 연결 실패: {e}")
            return False
    
    def test_frontend_access(self):
        """프론트엔드 접근 확인"""
        print("🌐 프론트엔드 접근 확인...")
        try:
            response = self.session.get(FRONTEND_URL, timeout=5)
            if response.status_code == 200:
                print("✅ 프론트엔드 접근 정상")
                return True
            else:
                print(f"❌ 프론트엔드 접근 오류: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ 프론트엔드 연결 실패: {e}")
            return False
    
    def single_login_test(self, account, test_id=1):
        """단일 로그인 테스트"""
        start_time = time.time()
        
        try:
            # FormData 형식으로 로그인 요청
            login_data = {
                'username': account['username'],
                'password': account['password']
            }
            
            response = self.session.post(
                f"{API_BASE}/auth/login", 
                data=login_data,  # FormData로 전송
                timeout=10
            )
            
            end_time = time.time()
            response_time = end_time - start_time
            
            result = {
                'test_id': test_id,
                'account': account['username'],
                'success': False,
                'response_time': response_time,
                'status_code': response.status_code,
                'error': None,
                'timestamp': datetime.now().isoformat()
            }
            
            if response.status_code == 200:
                data = response.json()
                if 'access_token' in data and 'user' in data:
                    result['success'] = True
                    result['token_received'] = True
                    result['user_role'] = data['user'].get('role')
                    print(f"✅ 테스트 {test_id}: {account['username']} 로그인 성공 ({response_time:.3f}s)")
                else:
                    result['error'] = "토큰 또는 사용자 정보 누락"
                    print(f"❌ 테스트 {test_id}: {account['username']} - 응답 데이터 불완전")
            else:
                result['error'] = response.text
                print(f"❌ 테스트 {test_id}: {account['username']} 로그인 실패 - {response.status_code}")
                
        except requests.exceptions.Timeout:
            result = {
                'test_id': test_id,
                'account': account['username'],
                'success': False,
                'response_time': time.time() - start_time,
                'status_code': None,
                'error': 'Timeout',
                'timestamp': datetime.now().isoformat()
            }
            print(f"⏰ 테스트 {test_id}: {account['username']} - 타임아웃")
            
        except Exception as e:
            result = {
                'test_id': test_id,
                'account': account['username'],
                'success': False,
                'response_time': time.time() - start_time,
                'status_code': None,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
            print(f"💥 테스트 {test_id}: {account['username']} - 예외 발생: {e}")
        
        self.results.append(result)
        return result
    
    def bulk_login_test(self, iterations=10):
        """대량 로그인 테스트 (간헐적 실패 확인)"""
        print(f"\n🔄 대량 로그인 테스트 시작 ({iterations}회 반복)...")
        
        test_count = 0
        for i in range(iterations):
            for account in TEST_ACCOUNTS:
                test_count += 1
                self.single_login_test(account, test_count)
                time.sleep(0.1)  # 서버 부하 방지
        
        self.analyze_results()
    
    def concurrent_login_test(self, concurrent_users=5):
        """동시 로그인 테스트"""
        print(f"\n⚡ 동시 로그인 테스트 시작 ({concurrent_users}명 동시)...")
        
        def worker(account, worker_id):
            for i in range(3):  # 각 워커당 3회 테스트
                test_id = f"{worker_id}-{i+1}"
                self.single_login_test(account, test_id)
                time.sleep(0.5)
        
        threads = []
        for i in range(concurrent_users):
            account = TEST_ACCOUNTS[i % len(TEST_ACCOUNTS)]
            thread = threading.Thread(target=worker, args=(account, i+1))
            threads.append(thread)
            thread.start()
        
        for thread in threads:
            thread.join()
        
        print(f"✅ 동시 로그인 테스트 완료")
    
    def analyze_results(self):
        """테스트 결과 분석"""
        if not self.results:
            print("❌ 분석할 결과가 없습니다.")
            return
        
        print("\n📊 테스트 결과 분석")
        print("=" * 50)
        
        # 성공률 계산
        total_tests = len(self.results)
        successful_tests = len([r for r in self.results if r['success']])
        success_rate = (successful_tests / total_tests) * 100
        
        print(f"총 테스트 수: {total_tests}")
        print(f"성공한 테스트: {successful_tests}")
        print(f"실패한 테스트: {total_tests - successful_tests}")
        print(f"성공률: {success_rate:.1f}%")
        
        # 응답시간 분석
        response_times = [r['response_time'] for r in self.results if r['response_time']]
        if response_times:
            print(f"\n응답시간 분석:")
            print(f"평균: {statistics.mean(response_times):.3f}초")
            print(f"최소: {min(response_times):.3f}초")
            print(f"최대: {max(response_times):.3f}초")
            if len(response_times) > 1:
                print(f"표준편차: {statistics.stdev(response_times):.3f}초")
        
        # 실패 원인 분석
        failed_tests = [r for r in self.results if not r['success']]
        if failed_tests:
            print(f"\n실패 원인 분석:")
            error_counts = {}
            for test in failed_tests:
                error = test.get('error', 'Unknown')
                status = test.get('status_code', 'None')
                key = f"{error} (HTTP {status})" if status else error
                error_counts[key] = error_counts.get(key, 0) + 1
            
            for error, count in error_counts.items():
                print(f"- {error}: {count}회")
        
        # 계정별 성공률
        print(f"\n계정별 성공률:")
        for account in TEST_ACCOUNTS:
            account_tests = [r for r in self.results if r['account'] == account['username']]
            if account_tests:
                account_success = len([r for r in account_tests if r['success']])
                account_rate = (account_success / len(account_tests)) * 100
                print(f"- {account['username']}: {account_rate:.1f}% ({account_success}/{len(account_tests)})")
    
    def save_results(self, filename=None):
        """결과를 JSON 파일로 저장"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"login_test_results_{timestamp}.json"
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False)
        
        print(f"📁 결과가 {filename}에 저장되었습니다.")

def main():
    print("🚀 로그인 기능 안정성 테스트 시작")
    print("=" * 50)
    
    tester = LoginStabilityTester()
    
    # 1. 서버 상태 확인
    if not tester.test_backend_health():
        print("❌ 백엔드 서버가 정상적으로 작동하지 않습니다. 테스트를 중단합니다.")
        return
    
    if not tester.test_frontend_access():
        print("❌ 프론트엔드 서버가 정상적으로 작동하지 않습니다. 테스트를 중단합니다.")
        return
    
    # 2. 기본 로그인 테스트
    print("\n🔑 기본 로그인 테스트...")
    for i, account in enumerate(TEST_ACCOUNTS, 1):
        tester.single_login_test(account, i)
    
    # 3. 대량 로그인 테스트 (간헐적 실패 확인)
    tester.bulk_login_test(15)  # 15회 반복
    
    # 4. 동시 로그인 테스트
    tester.concurrent_login_test(3)  # 3명 동시
    
    # 5. 결과 분석 및 저장
    tester.analyze_results()
    tester.save_results()
    
    print("\n🏁 테스트 완료!")

if __name__ == "__main__":
    main()
