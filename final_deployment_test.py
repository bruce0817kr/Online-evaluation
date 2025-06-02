#!/usr/bin/env python3
"""
온라인 평가 시스템 최종 배포 테스트 스크립트
Docker 환경에서의 완전한 시스템 통합 테스트
"""

import asyncio
import aiohttp
import json
import time
import sys
import subprocess
from datetime import datetime
import websockets
from pymongo import MongoClient
import redis
from typing import Dict, List, Any

class DeploymentTester:
    def __init__(self):
        self.base_url = "http://localhost:8080"
        self.frontend_url = "http://localhost:3000"
        self.ws_url = "ws://localhost:8080"
        self.mongodb_url = "mongodb://app_user:app_password123@localhost:27017/online_evaluation?authSource=online_evaluation"
        self.redis_host = "localhost"
        self.redis_port = 6379
        
        self.test_results = []
        self.session = None
        
    async def setup(self):
        """테스트 환경 설정"""
        self.session = aiohttp.ClientSession()
        print("🔧 테스트 환경 설정 완료")
        
    async def cleanup(self):
        """테스트 환경 정리"""
        if self.session:
            await self.session.close()
        print("🧹 테스트 환경 정리 완료")
        
    def log_test_result(self, test_name: str, success: bool, details: str = ""):
        """테스트 결과 기록"""
        result = {
            "test_name": test_name,
            "success": success,
            "details": details,
            "timestamp": datetime.now().isoformat()
        }
        self.test_results.append(result)
        
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
        if details:
            print(f"   📝 {details}")
            
    async def test_docker_containers(self):
        """Docker 컨테이너 상태 테스트"""
        print("\n🐳 Docker 컨테이너 상태 테스트")
        
        try:
            # docker-compose ps 실행
            result = subprocess.run(
                ['docker-compose', 'ps', '--format', 'json'],
                capture_output=True,
                text=True,
                cwd='.'
            )
            
            if result.returncode == 0:
                containers = []
                for line in result.stdout.strip().split('\n'):
                    if line.strip():
                        try:
                            containers.append(json.loads(line))
                        except json.JSONDecodeError:
                            pass
                
                required_services = ['mongodb', 'redis', 'backend', 'frontend', 'nginx']
                running_services = []
                
                for container in containers:
                    if container.get('State') == 'running':
                        service_name = container.get('Service', '')
                        running_services.append(service_name)
                
                for service in required_services:
                    if service in running_services:
                        self.log_test_result(f"Docker Container - {service}", True, "컨테이너 실행 중")
                    else:
                        self.log_test_result(f"Docker Container - {service}", False, "컨테이너 중지 상태")
                        
            else:
                self.log_test_result("Docker Containers Check", False, "docker-compose ps 실행 실패")
                
        except Exception as e:
            self.log_test_result("Docker Containers Check", False, f"오류: {str(e)}")
            
    async def test_database_connectivity(self):
        """데이터베이스 연결 테스트"""
        print("\n🗄️ 데이터베이스 연결 테스트")
        
        # MongoDB 테스트
        try:
            client = MongoClient(self.mongodb_url, serverSelectionTimeoutMS=5000)
            client.admin.command('ismaster')
            
            # 데이터베이스 및 컬렉션 확인
            db = client.online_evaluation
            collections = db.list_collection_names()
            
            expected_collections = ['exams', 'submissions', 'users', 'results']
            for collection in expected_collections:
                if collection in collections:
                    self.log_test_result(f"MongoDB Collection - {collection}", True, "컬렉션 존재")
                else:
                    self.log_test_result(f"MongoDB Collection - {collection}", False, "컬렉션 누락")
                    
            self.log_test_result("MongoDB Connection", True, f"연결 성공, 컬렉션 수: {len(collections)}")
            client.close()
            
        except Exception as e:
            self.log_test_result("MongoDB Connection", False, f"연결 실패: {str(e)}")
            
        # Redis 테스트
        try:
            r = redis.Redis(host=self.redis_host, port=self.redis_port, decode_responses=True)
            r.ping()
            
            # 캐시 테스트
            test_key = "deployment_test"
            test_value = "test_value_" + str(int(time.time()))
            r.set(test_key, test_value, ex=60)
            
            retrieved_value = r.get(test_key)
            if retrieved_value == test_value:
                self.log_test_result("Redis Cache Test", True, "캐시 읽기/쓰기 성공")
            else:
                self.log_test_result("Redis Cache Test", False, "캐시 값 불일치")
                
            r.delete(test_key)
            self.log_test_result("Redis Connection", True, "연결 및 기본 작업 성공")
            
        except Exception as e:
            self.log_test_result("Redis Connection", False, f"연결 실패: {str(e)}")
            
    async def test_backend_apis(self):
        """백엔드 API 테스트"""
        print("\n🔗 백엔드 API 테스트")
        
        # 헬스 체크 API
        try:
            async with self.session.get(f"{self.base_url}/health") as response:
                if response.status == 200:
                    data = await response.json()
                    self.log_test_result("Health Check API", True, f"응답: {data}")
                else:
                    self.log_test_result("Health Check API", False, f"상태 코드: {response.status}")
        except Exception as e:
            self.log_test_result("Health Check API", False, f"요청 실패: {str(e)}")
            
        # 메트릭스 API
        try:
            async with self.session.get(f"{self.base_url}/metrics") as response:
                if response.status == 200:
                    data = await response.json()
                    self.log_test_result("Metrics API", True, f"메트릭 항목 수: {len(data)}")
                else:
                    self.log_test_result("Metrics API", False, f"상태 코드: {response.status}")
        except Exception as e:
            self.log_test_result("Metrics API", False, f"요청 실패: {str(e)}")
            
        # CORS 테스트
        try:
            headers = {'Origin': 'http://localhost:3000'}
            async with self.session.options(f"{self.base_url}/health", headers=headers) as response:
                cors_headers = response.headers.get('Access-Control-Allow-Origin', '')
                if cors_headers:
                    self.log_test_result("CORS Configuration", True, f"CORS 헤더: {cors_headers}")
                else:
                    self.log_test_result("CORS Configuration", False, "CORS 헤더 누락")
        except Exception as e:
            self.log_test_result("CORS Configuration", False, f"테스트 실패: {str(e)}")
            
    async def test_websocket_connection(self):
        """WebSocket 연결 테스트"""
        print("\n🔌 WebSocket 연결 테스트")
        
        try:
            uri = f"{self.ws_url}/ws"
            async with websockets.connect(uri, timeout=10) as websocket:
                # 연결 성공
                self.log_test_result("WebSocket Connection", True, "연결 성공")
                
                # 메시지 전송 테스트
                test_message = {"type": "ping", "timestamp": time.time()}
                await websocket.send(json.dumps(test_message))
                
                # 응답 대기 (타임아웃 5초)
                try:
                    response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                    response_data = json.loads(response)
                    self.log_test_result("WebSocket Message Test", True, f"응답 받음: {response_data.get('type', 'unknown')}")
                except asyncio.TimeoutError:
                    self.log_test_result("WebSocket Message Test", False, "응답 타임아웃")
                    
        except Exception as e:
            self.log_test_result("WebSocket Connection", False, f"연결 실패: {str(e)}")
            
    async def test_frontend_access(self):
        """프론트엔드 접근 테스트"""
        print("\n🌐 프론트엔드 접근 테스트")
        
        try:
            async with self.session.get(self.frontend_url) as response:
                if response.status == 200:
                    content = await response.text()
                    
                    # React 앱 확인
                    if 'react' in content.lower() or 'root' in content:
                        self.log_test_result("Frontend Loading", True, "React 앱 로드 성공")
                    else:
                        self.log_test_result("Frontend Loading", False, "React 앱 식별 실패")
                        
                    # 필수 자원 확인
                    if 'script' in content and 'div' in content:
                        self.log_test_result("Frontend Resources", True, "필수 리소스 포함됨")
                    else:
                        self.log_test_result("Frontend Resources", False, "필수 리소스 누락")
                        
                else:
                    self.log_test_result("Frontend Access", False, f"상태 코드: {response.status}")
                    
        except Exception as e:
            self.log_test_result("Frontend Access", False, f"접근 실패: {str(e)}")
            
    async def test_integration_workflow(self):
        """통합 워크플로우 테스트"""
        print("\n🔄 통합 워크플로우 테스트")
        
        # 시험 데이터 생성 테스트
        try:
            exam_data = {
                "title": "배포 테스트 시험",
                "description": "Docker 배포 환경에서의 통합 테스트",
                "questions": [
                    {
                        "id": 1,
                        "question": "테스트 문제",
                        "type": "multiple_choice",
                        "options": ["A", "B", "C", "D"],
                        "correct_answer": "A"
                    }
                ],
                "time_limit": 30,
                "total_score": 100
            }
            
            async with self.session.post(f"{self.base_url}/exams", json=exam_data) as response:
                if response.status in [200, 201]:
                    result = await response.json()
                    exam_id = result.get('exam_id')
                    self.log_test_result("Exam Creation", True, f"시험 생성 성공: {exam_id}")
                    
                    # 생성된 시험 조회 테스트
                    if exam_id:
                        async with self.session.get(f"{self.base_url}/exams/{exam_id}") as get_response:
                            if get_response.status == 200:
                                self.log_test_result("Exam Retrieval", True, "시험 조회 성공")
                            else:
                                self.log_test_result("Exam Retrieval", False, f"조회 실패: {get_response.status}")
                                
                else:
                    self.log_test_result("Exam Creation", False, f"생성 실패: {response.status}")
                    
        except Exception as e:
            self.log_test_result("Integration Workflow", False, f"워크플로우 실패: {str(e)}")
            
    async def test_performance_metrics(self):
        """성능 메트릭 테스트"""
        print("\n📊 성능 메트릭 테스트")
        
        # API 응답 시간 테스트
        response_times = []
        
        for i in range(5):
            start_time = time.time()
            try:
                async with self.session.get(f"{self.base_url}/health") as response:
                    if response.status == 200:
                        response_time = (time.time() - start_time) * 1000  # ms
                        response_times.append(response_time)
            except Exception:
                pass
                
        if response_times:
            avg_response_time = sum(response_times) / len(response_times)
            max_response_time = max(response_times)
            
            if avg_response_time < 1000:  # 1초 미만
                self.log_test_result("API Response Time", True, f"평균: {avg_response_time:.2f}ms, 최대: {max_response_time:.2f}ms")
            else:
                self.log_test_result("API Response Time", False, f"응답 시간 초과: {avg_response_time:.2f}ms")
        else:
            self.log_test_result("API Response Time", False, "응답 시간 측정 실패")
            
    def generate_test_report(self):
        """테스트 보고서 생성"""
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result['success'])
        failed_tests = total_tests - passed_tests
        
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        print("\n" + "="*60)
        print("🎯 최종 배포 테스트 보고서")
        print("="*60)
        print(f"📈 전체 테스트: {total_tests}")
        print(f"✅ 성공: {passed_tests}")
        print(f"❌ 실패: {failed_tests}")
        print(f"📊 성공률: {success_rate:.1f}%")
        print("="*60)
        
        if failed_tests > 0:
            print("\n❌ 실패한 테스트:")
            for result in self.test_results:
                if not result['success']:
                    print(f"   • {result['test_name']}: {result['details']}")
                    
        print(f"\n📝 상세 보고서는 deployment_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json 에 저장됩니다.")
        
        # JSON 보고서 저장
        report_filename = f"deployment_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_filename, 'w', encoding='utf-8') as f:
            json.dump({
                'summary': {
                    'total_tests': total_tests,
                    'passed_tests': passed_tests,
                    'failed_tests': failed_tests,
                    'success_rate': success_rate,
                    'test_date': datetime.now().isoformat()
                },
                'detailed_results': self.test_results
            }, f, indent=2, ensure_ascii=False)
            
        return success_rate >= 80  # 80% 이상 성공시 배포 승인
        
    async def run_all_tests(self):
        """모든 테스트 실행"""
        print("🚀 온라인 평가 시스템 최종 배포 테스트 시작")
        print("="*60)
        
        await self.setup()
        
        try:
            await self.test_docker_containers()
            await self.test_database_connectivity()
            await self.test_backend_apis()
            await self.test_websocket_connection()
            await self.test_frontend_access()
            await self.test_integration_workflow()
            await self.test_performance_metrics()
            
        finally:
            await self.cleanup()
            
        deployment_ready = self.generate_test_report()
        
        if deployment_ready:
            print("\n🎉 배포 준비 완료! 시스템이 프로덕션 환경에서 실행할 준비가 되었습니다.")
            return 0
        else:
            print("\n⚠️ 배포 준비 미완료. 실패한 테스트를 확인하고 수정 후 다시 테스트하세요.")
            return 1

async def main():
    """메인 함수"""
    tester = DeploymentTester()
    exit_code = await tester.run_all_tests()
    sys.exit(exit_code)

if __name__ == "__main__":
    asyncio.run(main())
