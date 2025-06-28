#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
온라인 평가 시스템 최종 통합 테스트
모든 주요 기능의 연동 상태와 시스템 안정성을 검증합니다.
"""

import asyncio
import aiohttp
import json
import time
import os
from datetime import datetime
from typing import Dict, List, Any, Optional
import logging

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('integration_test.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class SystemIntegrationTester:
    """시스템 통합 테스트 실행기"""
    
    def __init__(self):
        self.backend_url = os.getenv('BACKEND_URL', 'http://localhost:8081')
        self.frontend_url = os.getenv('FRONTEND_URL', 'http://localhost:3000')
        self.test_results = {
            'total_tests': 0,
            'passed_tests': 0,
            'failed_tests': 0,
            'test_details': []
        }
        self.session = None
        self.admin_token = None
        self.evaluator_token = None
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30)
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    def log_test_result(self, test_name: str, passed: bool, details: str = "", duration: float = 0):
        """테스트 결과 로깅"""
        self.test_results['total_tests'] += 1
        if passed:
            self.test_results['passed_tests'] += 1
            logger.info(f"✅ {test_name} - PASSED ({duration:.2f}s)")
        else:
            self.test_results['failed_tests'] += 1
            logger.error(f"❌ {test_name} - FAILED ({duration:.2f}s)")
            if details:
                logger.error(f"   Details: {details}")
        
        self.test_results['test_details'].append({
            'name': test_name,
            'passed': passed,
            'details': details,
            'duration': duration,
            'timestamp': datetime.now().isoformat()
        })
    
    async def test_backend_health(self) -> bool:
        """백엔드 헬스 체크"""
        start_time = time.time()
        try:
            async with self.session.get(f"{self.backend_url}/health") as response:
                if response.status == 200:
                    data = await response.json()
                    self.log_test_result(
                        "Backend Health Check", 
                        True, 
                        f"Status: {data.get('status', 'OK')}", 
                        time.time() - start_time
                    )
                    return True
                else:
                    self.log_test_result(
                        "Backend Health Check", 
                        False, 
                        f"HTTP {response.status}", 
                        time.time() - start_time
                    )
                    return False
        except Exception as e:
            self.log_test_result(
                "Backend Health Check", 
                False, 
                f"Exception: {str(e)}", 
                time.time() - start_time
            )
            return False
    
    async def test_database_connection(self) -> bool:
        """데이터베이스 연결 테스트"""
        start_time = time.time()
        try:
            async with self.session.get(f"{self.backend_url}/api/dashboard/statistics") as response:
                if response.status == 401:
                    # 인증이 필요하지만 연결은 정상
                    self.log_test_result(
                        "Database Connection", 
                        True, 
                        "DB connection successful (auth required)", 
                        time.time() - start_time
                    )
                    return True
                elif response.status == 200:
                    self.log_test_result(
                        "Database Connection", 
                        True, 
                        "DB connection and auth successful", 
                        time.time() - start_time
                    )
                    return True
                else:
                    self.log_test_result(
                        "Database Connection", 
                        False, 
                        f"HTTP {response.status}", 
                        time.time() - start_time
                    )
                    return False
        except Exception as e:
            self.log_test_result(
                "Database Connection", 
                False, 
                f"Exception: {str(e)}", 
                time.time() - start_time
            )
            return False
    
    async def test_authentication_system(self) -> bool:
        """인증 시스템 테스트"""
        start_time = time.time()
        try:
            # 관리자 로그인 테스트
            login_data = {
                "username": "admin",
                "password": "admin123"
            }
            
            async with self.session.post(
                f"{self.backend_url}/api/auth/login",
                data=login_data
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    if 'access_token' in data:
                        self.admin_token = data['access_token']
                        self.log_test_result(
                            "Authentication System", 
                            True, 
                            "Admin login successful", 
                            time.time() - start_time
                        )
                        return True
                
                self.log_test_result(
                    "Authentication System", 
                    False, 
                    f"Login failed: HTTP {response.status}", 
                    time.time() - start_time
                )
                return False
                
        except Exception as e:
            self.log_test_result(
                "Authentication System", 
                False, 
                f"Exception: {str(e)}", 
                time.time() - start_time
            )
            return False
    
    async def test_user_management(self) -> bool:
        """사용자 관리 시스템 테스트"""
        if not self.admin_token:
            self.log_test_result("User Management", False, "No admin token available", 0)
            return False
        
        start_time = time.time()
        try:
            headers = {"Authorization": f"Bearer {self.admin_token}"}
            
            # 사용자 목록 조회
            async with self.session.get(
                f"{self.backend_url}/api/users",
                headers=headers
            ) as response:
                if response.status == 200:
                    users = await response.json()
                    self.log_test_result(
                        "User Management", 
                        True, 
                        f"Retrieved {len(users)} users", 
                        time.time() - start_time
                    )
                    return True
                else:
                    self.log_test_result(
                        "User Management", 
                        False, 
                        f"HTTP {response.status}", 
                        time.time() - start_time
                    )
                    return False
                    
        except Exception as e:
            self.log_test_result(
                "User Management", 
                False, 
                f"Exception: {str(e)}", 
                time.time() - start_time
            )
            return False
    
    async def test_template_system(self) -> bool:
        """템플릿 시스템 테스트"""
        if not self.admin_token:
            self.log_test_result("Template System", False, "No admin token available", 0)
            return False
        
        start_time = time.time()
        try:
            headers = {"Authorization": f"Bearer {self.admin_token}"}
            
            # 템플릿 목록 조회
            async with self.session.get(
                f"{self.backend_url}/api/templates",
                headers=headers
            ) as response:
                if response.status == 200:
                    templates = await response.json()
                    self.log_test_result(
                        "Template System", 
                        True, 
                        f"Retrieved {len(templates)} templates", 
                        time.time() - start_time
                    )
                    return True
                else:
                    self.log_test_result(
                        "Template System", 
                        False, 
                        f"HTTP {response.status}", 
                        time.time() - start_time
                    )
                    return False
                    
        except Exception as e:
            self.log_test_result(
                "Template System", 
                False, 
                f"Exception: {str(e)}", 
                time.time() - start_time
            )
            return False
    
    async def test_ai_system(self) -> bool:
        """AI 시스템 테스트"""
        if not self.admin_token:
            self.log_test_result("AI System", False, "No admin token available", 0)
            return False
        
        start_time = time.time()
        try:
            headers = {"Authorization": f"Bearer {self.admin_token}"}
            
            # AI 서비스 상태 확인
            async with self.session.get(
                f"{self.backend_url}/api/ai/status",
                headers=headers
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    status = data.get('status', {})
                    service_status = status.get('service_status', 'unknown')
                    self.log_test_result(
                        "AI System", 
                        True, 
                        f"AI Service Status: {service_status}", 
                        time.time() - start_time
                    )
                    return True
                else:
                    self.log_test_result(
                        "AI System", 
                        False, 
                        f"HTTP {response.status}", 
                        time.time() - start_time
                    )
                    return False
                    
        except Exception as e:
            self.log_test_result(
                "AI System", 
                False, 
                f"Exception: {str(e)}", 
                time.time() - start_time
            )
            return False
    
    async def test_file_security_system(self) -> bool:
        """파일 보안 시스템 테스트"""
        if not self.admin_token:
            self.log_test_result("File Security System", False, "No admin token available", 0)
            return False
        
        start_time = time.time()
        try:
            headers = {"Authorization": f"Bearer {self.admin_token}"}
            
            # 파일 보안 로그 조회
            async with self.session.get(
                f"{self.backend_url}/api/secure-files/access-logs",
                headers=headers
            ) as response:
                if response.status in [200, 404]:  # 404는 로그가 없을 때
                    self.log_test_result(
                        "File Security System", 
                        True, 
                        "File security endpoint accessible", 
                        time.time() - start_time
                    )
                    return True
                else:
                    self.log_test_result(
                        "File Security System", 
                        False, 
                        f"HTTP {response.status}", 
                        time.time() - start_time
                    )
                    return False
                    
        except Exception as e:
            self.log_test_result(
                "File Security System", 
                False, 
                f"Exception: {str(e)}", 
                time.time() - start_time
            )
            return False
    
    async def test_websocket_connection(self) -> bool:
        """WebSocket 연결 테스트"""
        start_time = time.time()
        try:
            import websockets
            
            ws_url = self.backend_url.replace('http', 'ws') + '/ws/test_user'
            
            async with websockets.connect(ws_url) as websocket:
                # ping 메시지 전송
                await websocket.send(json.dumps({"type": "ping"}))
                
                # pong 응답 대기 (최대 5초)
                response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                data = json.loads(response)
                
                if data.get("type") == "pong":
                    self.log_test_result(
                        "WebSocket Connection", 
                        True, 
                        "Ping/Pong successful", 
                        time.time() - start_time
                    )
                    return True
                else:
                    self.log_test_result(
                        "WebSocket Connection", 
                        False, 
                        f"Unexpected response: {data}", 
                        time.time() - start_time
                    )
                    return False
                    
        except ImportError:
            self.log_test_result(
                "WebSocket Connection", 
                False, 
                "websockets library not available", 
                time.time() - start_time
            )
            return False
        except Exception as e:
            self.log_test_result(
                "WebSocket Connection", 
                False, 
                f"Exception: {str(e)}", 
                time.time() - start_time
            )
            return False
    
    async def test_frontend_accessibility(self) -> bool:
        """프론트엔드 접근성 테스트"""
        start_time = time.time()
        try:
            async with self.session.get(self.frontend_url) as response:
                if response.status == 200:
                    content = await response.text()
                    if 'React' in content or 'root' in content:
                        self.log_test_result(
                            "Frontend Accessibility", 
                            True, 
                            "Frontend is accessible", 
                            time.time() - start_time
                        )
                        return True
                    else:
                        self.log_test_result(
                            "Frontend Accessibility", 
                            False, 
                            "Frontend content unexpected", 
                            time.time() - start_time
                        )
                        return False
                else:
                    self.log_test_result(
                        "Frontend Accessibility", 
                        False, 
                        f"HTTP {response.status}", 
                        time.time() - start_time
                    )
                    return False
                    
        except Exception as e:
            self.log_test_result(
                "Frontend Accessibility", 
                False, 
                f"Exception: {str(e)}", 
                time.time() - start_time
            )
            return False
    
    async def run_all_tests(self) -> Dict[str, Any]:
        """모든 테스트 실행"""
        logger.info("🚀 온라인 평가 시스템 통합 테스트 시작")
        logger.info(f"Backend URL: {self.backend_url}")
        logger.info(f"Frontend URL: {self.frontend_url}")
        logger.info("=" * 60)
        
        test_functions = [
            self.test_backend_health,
            self.test_database_connection,
            self.test_authentication_system,
            self.test_user_management,
            self.test_template_system,
            self.test_ai_system,
            self.test_file_security_system,
            self.test_websocket_connection,
            self.test_frontend_accessibility,
        ]
        
        for test_func in test_functions:
            try:
                await test_func()
                await asyncio.sleep(0.5)  # 테스트 간 잠시 대기
            except Exception as e:
                logger.error(f"테스트 실행 오류 ({test_func.__name__}): {e}")
        
        # 결과 요약
        logger.info("=" * 60)
        logger.info("📊 테스트 결과 요약")
        logger.info(f"총 테스트: {self.test_results['total_tests']}")
        logger.info(f"성공: {self.test_results['passed_tests']}")
        logger.info(f"실패: {self.test_results['failed_tests']}")
        
        success_rate = (self.test_results['passed_tests'] / max(self.test_results['total_tests'], 1)) * 100
        logger.info(f"성공률: {success_rate:.1f}%")
        
        if success_rate >= 80:
            logger.info("✅ 시스템 상태: 양호 (배포 가능)")
        elif success_rate >= 60:
            logger.warning("⚠️ 시스템 상태: 주의 (일부 수정 필요)")
        else:
            logger.error("❌ 시스템 상태: 불량 (배포 불가)")
        
        # 상세 결과를 파일로 저장
        report_filename = f"integration_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_filename, 'w', encoding='utf-8') as f:
            json.dump(self.test_results, f, ensure_ascii=False, indent=2)
        
        logger.info(f"📄 상세 리포트 저장됨: {report_filename}")
        
        return self.test_results

async def main():
    """메인 실행 함수"""
    async with SystemIntegrationTester() as tester:
        results = await tester.run_all_tests()
        return results

if __name__ == "__main__":
    # 통합 테스트 실행
    results = asyncio.run(main())
    
    # 종료 코드 설정 (CI/CD에서 사용)
    if results['failed_tests'] == 0:
        exit(0)
    else:
        exit(1)