#!/usr/bin/env python3
"""
AI 모델 관리 시스템 - 보안 테스트 실행기
종합적인 보안 테스트 실행 및 취약점 분석
"""

import asyncio
import aiohttp
import json
import time
import re
import hashlib
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from datetime import datetime
import logging
import argparse
import os
import subprocess
import base64
import jwt
from urllib.parse import urljoin, urlparse
import ssl
import socket

# 보안 테스트 관련 임포트
try:
    import bandit
    from safety import safety
    SECURITY_TOOLS_AVAILABLE = True
except ImportError:
    SECURITY_TOOLS_AVAILABLE = False
    print("경고: 일부 보안 도구가 설치되지 않았습니다. pip install bandit safety 실행을 권장합니다.")

@dataclass
class SecurityTestResult:
    """보안 테스트 결과"""
    test_category: str
    test_name: str
    severity: str  # critical, high, medium, low, info
    status: str    # passed, failed, warning
    description: str
    details: Dict[str, Any]
    remediation: str
    timestamp: datetime

@dataclass
class VulnerabilityFinding:
    """취약점 발견사항"""
    vuln_id: str
    title: str
    severity: str
    cwe_id: Optional[str]
    description: str
    location: str
    evidence: Dict[str, Any]
    remediation: str
    references: List[str]

class SecurityTestRunner:
    """보안 테스트 실행기"""
    
    def __init__(self, target_url: str, api_url: str, test_mode: str = 'safe'):
        self.target_url = target_url.rstrip('/')
        self.api_url = api_url.rstrip('/')
        self.test_mode = test_mode  # safe, aggressive
        self.session = None
        self.results: List[SecurityTestResult] = []
        self.vulnerabilities: List[VulnerabilityFinding] = []
        
        # 테스트 사용자 정보
        self.test_users = {
            'admin': {'email': 'admin@test.com', 'password': 'testpass123'},
            'secretary': {'email': 'secretary@test.com', 'password': 'testpass123'},
            'evaluator': {'email': 'evaluator@test.com', 'password': 'testpass123'}
        }
        
        # 로깅 설정
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
        
    async def setup_session(self):
        """HTTP 세션 설정"""
        connector = aiohttp.TCPConnector(
            ssl=ssl.create_default_context(),
            limit=50
        )
        
        timeout = aiohttp.ClientTimeout(total=30)
        self.session = aiohttp.ClientSession(
            connector=connector,
            timeout=timeout
        )
        
    async def cleanup_session(self):
        """세션 정리"""
        if self.session:
            await self.session.close()
            
    async def run_all_tests(self) -> Dict[str, Any]:
        """모든 보안 테스트 실행"""
        self.logger.info("🔒 보안 테스트 시작")
        start_time = time.time()
        
        await self.setup_session()
        
        try:
            # 1. 인증 및 권한 테스트
            self.logger.info("🔐 인증 및 권한 테스트 실행")
            await self.test_authentication_security()
            
            # 2. 입력 검증 테스트
            self.logger.info("📝 입력 검증 테스트 실행")
            await self.test_input_validation()
            
            # 3. API 보안 테스트
            self.logger.info("🔌 API 보안 테스트 실행")
            await self.test_api_security()
            
            # 4. 세션 보안 테스트
            self.logger.info("🕒 세션 보안 테스트 실행")
            await self.test_session_security()
            
            # 5. 데이터 보안 테스트
            self.logger.info("💾 데이터 보안 테스트 실행")
            await self.test_data_security()
            
            # 6. 정적 코드 분석 (가능한 경우)
            if SECURITY_TOOLS_AVAILABLE:
                self.logger.info("🔍 정적 코드 분석 실행")
                await self.run_static_analysis()
                
            # 7. SSL/TLS 보안 테스트
            self.logger.info("🔒 SSL/TLS 보안 테스트 실행")
            await self.test_ssl_security()
            
        finally:
            await self.cleanup_session()
            
        end_time = time.time()
        self.logger.info(f"보안 테스트 완료: {end_time - start_time:.2f}초")
        
        return await self.generate_security_report()
        
    async def test_authentication_security(self):
        """인증 시스템 보안 테스트"""
        
        # 1. 약한 비밀번호 테스트
        await self._test_weak_passwords()
        
        # 2. 브루트 포스 방어 테스트
        await self._test_brute_force_protection()
        
        # 3. JWT 토큰 보안 테스트
        await self._test_jwt_security()
        
        # 4. 권한 상승 테스트
        await self._test_privilege_escalation()
        
        # 5. 세션 고정 공격 테스트
        await self._test_session_fixation()
        
    async def _test_weak_passwords(self):
        """약한 비밀번호 정책 테스트"""
        weak_passwords = [
            '123456', 'password', '123456789', 'qwerty', 'abc123',
            'password123', 'admin', 'test', '1234567890', 'Password1'
        ]
        
        for password in weak_passwords:
            try:
                login_data = {
                    'email': 'admin@test.com',
                    'password': password
                }
                
                async with self.session.post(
                    f"{self.api_url}/api/auth/login",
                    json=login_data
                ) as response:
                    if response.status == 200:
                        # 약한 비밀번호로 로그인 성공 (보안 위험)
                        self.results.append(SecurityTestResult(
                            test_category="authentication",
                            test_name="weak_password_policy",
                            severity="high",
                            status="failed",
                            description=f"약한 비밀번호 '{password}'로 로그인 성공",
                            details={"password": password, "response_status": response.status},
                            remediation="강력한 비밀번호 정책 구현 (최소 8자, 대소문자, 숫자, 특수문자 포함)",
                            timestamp=datetime.now()
                        ))
                        
            except Exception as e:
                self.logger.debug(f"약한 비밀번호 테스트 오류: {e}")
                
        # 약한 비밀번호로 로그인이 모두 실패한 경우 (양호)
        if not any(r.test_name == "weak_password_policy" and r.status == "failed" for r in self.results):
            self.results.append(SecurityTestResult(
                test_category="authentication",
                test_name="weak_password_policy",
                severity="info",
                status="passed",
                description="약한 비밀번호로 로그인 시도 모두 차단됨",
                details={"tested_passwords": len(weak_passwords)},
                remediation="현재 비밀번호 정책 유지",
                timestamp=datetime.now()
            ))
            
    async def _test_brute_force_protection(self):
        """브루트 포스 공격 방어 테스트"""
        failed_attempts = 0
        locked_out = False
        
        # 연속 실패 로그인 시도
        for i in range(10):
            try:
                login_data = {
                    'email': 'admin@test.com',
                    'password': f'wrong_password_{i}'
                }
                
                start_time = time.time()
                async with self.session.post(
                    f"{self.api_url}/api/auth/login",
                    json=login_data
                ) as response:
                    end_time = time.time()
                    response_time = end_time - start_time
                    
                    if response.status == 429:  # Too Many Requests
                        locked_out = True
                        break
                    elif response.status == 401:
                        failed_attempts += 1
                        
                    # 응답 시간 증가 확인 (속도 제한)
                    if response_time > 2.0:  # 2초 이상 지연
                        self.results.append(SecurityTestResult(
                            test_category="authentication",
                            test_name="brute_force_rate_limiting",
                            severity="info",
                            status="passed",
                            description="브루트 포스 공격 시 응답 시간 지연 감지",
                            details={"attempt": i+1, "response_time": response_time},
                            remediation="현재 속도 제한 정책 유지",
                            timestamp=datetime.now()
                        ))
                        
                # 각 시도 간 짧은 지연
                await asyncio.sleep(0.1)
                
            except Exception as e:
                self.logger.debug(f"브루트 포스 테스트 오류: {e}")
                
        # 결과 평가
        if locked_out:
            self.results.append(SecurityTestResult(
                test_category="authentication",
                test_name="brute_force_protection",
                severity="info",
                status="passed",
                description="브루트 포스 공격 방어 메커니즘 작동",
                details={"failed_attempts_before_lockout": failed_attempts},
                remediation="현재 보안 정책 유지",
                timestamp=datetime.now()
            ))
        else:
            self.results.append(SecurityTestResult(
                test_category="authentication",
                test_name="brute_force_protection",
                severity="medium",
                status="warning",
                description="브루트 포스 공격 방어 메커니즘 미흡",
                details={"total_attempts": 10, "lockout_triggered": False},
                remediation="계정 잠금 정책 및 속도 제한 구현",
                timestamp=datetime.now()
            ))
            
    async def _test_jwt_security(self):
        """JWT 토큰 보안 테스트"""
        # 정상 로그인으로 토큰 획득
        login_data = self.test_users['admin']
        
        try:
            async with self.session.post(
                f"{self.api_url}/api/auth/login",
                json=login_data
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    token = data.get('access_token')
                    
                    if token:
                        await self._analyze_jwt_token(token)
                        await self._test_jwt_manipulation(token)
                        await self._test_jwt_algorithms(token)
                        
        except Exception as e:
            self.logger.error(f"JWT 테스트 준비 실패: {e}")
            
    async def _analyze_jwt_token(self, token: str):
        """JWT 토큰 구조 분석"""
        try:
            # JWT 토큰 디코딩 (서명 검증 없이)
            unverified_payload = jwt.decode(token, options={"verify_signature": False})
            header = jwt.get_unverified_header(token)
            
            # 토큰 만료 시간 확인
            if 'exp' in unverified_payload:
                exp_time = datetime.fromtimestamp(unverified_payload['exp'])
                current_time = datetime.now()
                time_to_expire = (exp_time - current_time).total_seconds()
                
                if time_to_expire > 86400:  # 24시간 초과
                    self.results.append(SecurityTestResult(
                        test_category="authentication",
                        test_name="jwt_expiration_time",
                        severity="medium",
                        status="warning",
                        description="JWT 토큰 만료 시간이 너무 길음",
                        details={"expiration_hours": time_to_expire / 3600},
                        remediation="JWT 토큰 만료 시간을 더 짧게 설정 (권장: 1-8시간)",
                        timestamp=datetime.now()
                    ))
                    
            # 알고리즘 확인
            algorithm = header.get('alg', 'unknown')
            if algorithm in ['none', 'HS256'] and algorithm != 'RS256':
                severity = "high" if algorithm == 'none' else "medium"
                self.results.append(SecurityTestResult(
                    test_category="authentication",
                    test_name="jwt_algorithm_security",
                    severity=severity,
                    status="warning",
                    description=f"JWT에서 {algorithm} 알고리즘 사용",
                    details={"algorithm": algorithm, "header": header},
                    remediation="RS256 또는 ES256 같은 비대칭 알고리즘 사용 권장",
                    timestamp=datetime.now()
                ))
                
        except Exception as e:
            self.logger.error(f"JWT 분석 실패: {e}")
            
    async def _test_jwt_manipulation(self, original_token: str):
        """JWT 토큰 조작 테스트"""
        try:
            # 토큰 부분별 분리
            parts = original_token.split('.')
            if len(parts) != 3:
                return
                
            header_b64, payload_b64, signature = parts
            
            # 페이로드 디코딩
            payload_json = base64.urlsafe_b64decode(payload_b64 + '==').decode('utf-8')
            payload = json.loads(payload_json)
            
            # 권한 상승 시도 - 역할 변경
            if 'role' in payload:
                malicious_payload = payload.copy()
                malicious_payload['role'] = 'admin'
                
                # 새 페이로드 인코딩
                new_payload_json = json.dumps(malicious_payload, separators=(',', ':'))
                new_payload_b64 = base64.urlsafe_b64encode(new_payload_json.encode()).decode().rstrip('=')
                
                # 조작된 토큰 생성
                manipulated_token = f"{header_b64}.{new_payload_b64}.{signature}"
                
                # 조작된 토큰으로 접근 시도
                await self._test_manipulated_token(manipulated_token, "role_elevation")
                
            # 만료 시간 연장 시도
            if 'exp' in payload:
                malicious_payload = payload.copy()
                malicious_payload['exp'] = int(time.time()) + 86400 * 365  # 1년 연장
                
                new_payload_json = json.dumps(malicious_payload, separators=(',', ':'))
                new_payload_b64 = base64.urlsafe_b64encode(new_payload_json.encode()).decode().rstrip('=')
                
                manipulated_token = f"{header_b64}.{new_payload_b64}.{signature}"
                await self._test_manipulated_token(manipulated_token, "expiration_extension")
                
        except Exception as e:
            self.logger.debug(f"JWT 조작 테스트 오류: {e}")
            
    async def _test_manipulated_token(self, token: str, attack_type: str):
        """조작된 토큰으로 접근 시도"""
        try:
            headers = {'Authorization': f'Bearer {token}'}
            
            async with self.session.get(
                f"{self.api_url}/api/auth/me",
                headers=headers
            ) as response:
                if response.status == 200:
                    self.results.append(SecurityTestResult(
                        test_category="authentication",
                        test_name="jwt_token_manipulation",
                        severity="critical",
                        status="failed",
                        description=f"조작된 JWT 토큰 접근 성공 ({attack_type})",
                        details={"attack_type": attack_type, "response_status": response.status},
                        remediation="JWT 서명 검증 강화 및 토큰 무결성 검사 구현",
                        timestamp=datetime.now()
                    ))
                elif response.status in [401, 403]:
                    self.results.append(SecurityTestResult(
                        test_category="authentication",
                        test_name="jwt_token_manipulation",
                        severity="info",
                        status="passed",
                        description=f"조작된 JWT 토큰 접근 차단됨 ({attack_type})",
                        details={"attack_type": attack_type, "response_status": response.status},
                        remediation="현재 JWT 검증 로직 유지",
                        timestamp=datetime.now()
                    ))
                    
        except Exception as e:
            self.logger.debug(f"조작된 토큰 테스트 오류: {e}")
            
    async def _test_jwt_algorithms(self, token: str):
        """JWT 알고리즘 혼동 공격 테스트"""
        try:
            parts = token.split('.')
            if len(parts) != 3:
                return
                
            # 헤더 디코딩
            header_b64 = parts[0]
            header_json = base64.urlsafe_b64decode(header_b64 + '==').decode('utf-8')
            header = json.loads(header_json)
            
            # none 알고리즘으로 변경 시도
            malicious_header = header.copy()
            malicious_header['alg'] = 'none'
            
            new_header_json = json.dumps(malicious_header, separators=(',', ':'))
            new_header_b64 = base64.urlsafe_b64encode(new_header_json.encode()).decode().rstrip('=')
            
            # none 알고리즘 토큰 생성 (서명 없음)
            none_token = f"{new_header_b64}.{parts[1]}."
            
            await self._test_manipulated_token(none_token, "none_algorithm")
            
        except Exception as e:
            self.logger.debug(f"JWT 알고리즘 테스트 오류: {e}")
            
    async def test_input_validation(self):
        """입력 검증 테스트"""
        
        # 1. NoSQL 인젝션 테스트
        await self._test_nosql_injection()
        
        # 2. XSS 테스트
        await self._test_xss_vulnerabilities()
        
        # 3. 명령어 인젝션 테스트
        await self._test_command_injection()
        
        # 4. 경로 탐색 테스트
        await self._test_path_traversal()
        
        # 5. 파일 업로드 보안 테스트
        await self._test_file_upload_security()
        
    async def _test_nosql_injection(self):
        """NoSQL 인젝션 테스트"""
        nosql_payloads = [
            {"$ne": None},
            {"$gt": ""},
            {"$where": "this.username == this.password"},
            {"$regex": ".*"},
            {"$exists": True},
            {"$or": [{"username": "admin"}, {"role": "admin"}]},
            {"username": {"$ne": "admin"}, "password": {"$ne": "password"}}
        ]
        
        # 로그인 엔드포인트 테스트
        for payload in nosql_payloads:
            try:
                # 이메일 필드에 NoSQL 인젝션 시도
                login_data = {
                    "email": payload,
                    "password": "any_password"
                }
                
                async with self.session.post(
                    f"{self.api_url}/api/auth/login",
                    json=login_data
                ) as response:
                    if response.status == 200:
                        self.results.append(SecurityTestResult(
                            test_category="input_validation",
                            test_name="nosql_injection",
                            severity="critical",
                            status="failed",
                            description="NoSQL 인젝션 공격 성공",
                            details={"payload": str(payload), "endpoint": "/api/auth/login"},
                            remediation="입력 데이터 타입 검증 및 쿼리 매개변수화",
                            timestamp=datetime.now()
                        ))
                        break
                        
            except Exception as e:
                self.logger.debug(f"NoSQL 인젝션 테스트 오류: {e}")
                
        # 모델 조회 엔드포인트 테스트
        try:
            # 정상 토큰 획득
            admin_token = await self._get_valid_token('admin')
            if admin_token:
                headers = {'Authorization': f'Bearer {admin_token}'}
                
                for payload in nosql_payloads:
                    try:
                        # 쿼리 매개변수에 NoSQL 인젝션 시도
                        async with self.session.get(
                            f"{self.api_url}/api/ai-models/available",
                            headers=headers,
                            params={"filter": json.dumps(payload)}
                        ) as response:
                            if response.status == 200:
                                data = await response.json()
                                # 예상보다 많은 데이터 반환 시 인젝션 성공 의심
                                if isinstance(data, list) and len(data) > 20:
                                    self.results.append(SecurityTestResult(
                                        test_category="input_validation",
                                        test_name="nosql_injection_query",
                                        severity="high",
                                        status="failed",
                                        description="쿼리 매개변수에서 NoSQL 인젝션 가능성",
                                        details={"payload": str(payload), "result_count": len(data)},
                                        remediation="쿼리 매개변수 검증 강화",
                                        timestamp=datetime.now()
                                    ))
                                    
                    except Exception as e:
                        self.logger.debug(f"NoSQL 쿼리 인젝션 테스트 오류: {e}")
                        
        except Exception as e:
            self.logger.error(f"NoSQL 인젝션 테스트 준비 실패: {e}")
            
    async def _test_xss_vulnerabilities(self):
        """XSS 취약점 테스트"""
        xss_payloads = [
            "<script>alert('XSS')</script>",
            "<img src=x onerror=alert('XSS')>",
            "<svg onload=alert('XSS')>",
            "javascript:alert('XSS')",
            "<iframe src=\"javascript:alert('XSS')\"></iframe>",
            "'\"><script>alert('XSS')</script>",
            "<script>fetch('/api/auth/me').then(r=>r.json()).then(d=>alert(JSON.stringify(d)))</script>"
        ]
        
        # 모델 생성 시 XSS 테스트
        admin_token = await self._get_valid_token('admin')
        if not admin_token:
            return
            
        headers = {'Authorization': f'Bearer {admin_token}'}
        
        for i, payload in enumerate(xss_payloads):
            try:
                model_data = {
                    "model_id": f"xss-test-{i}",
                    "provider": "test",
                    "model_name": "test-model",
                    "display_name": payload,  # XSS 페이로드 삽입
                    "quality_score": 0.8,
                    "speed_score": 0.9,
                    "cost_efficiency": 0.85,
                    "reliability_score": 0.9
                }
                
                async with self.session.post(
                    f"{self.api_url}/api/ai-models/create",
                    headers=headers,
                    json=model_data
                ) as response:
                    if response.status == 201:
                        # 생성된 모델 조회하여 XSS 페이로드가 그대로 반환되는지 확인
                        async with self.session.get(
                            f"{self.api_url}/api/ai-models/{model_data['model_id']}",
                            headers=headers
                        ) as get_response:
                            if get_response.status == 200:
                                data = await get_response.json()
                                if payload in str(data):
                                    self.results.append(SecurityTestResult(
                                        test_category="input_validation",
                                        test_name="stored_xss",
                                        severity="high",
                                        status="failed",
                                        description="저장형 XSS 취약점 발견",
                                        details={
                                            "payload": payload,
                                            "field": "display_name",
                                            "endpoint": "/api/ai-models/create"
                                        },
                                        remediation="입력 데이터 HTML 인코딩 및 출력 시 이스케이프 처리",
                                        timestamp=datetime.now()
                                    ))
                                    
                        # 테스트 모델 정리
                        await self.session.delete(
                            f"{self.api_url}/api/ai-models/{model_data['model_id']}",
                            headers=headers
                        )
                        
            except Exception as e:
                self.logger.debug(f"XSS 테스트 오류: {e}")
                
    async def _get_valid_token(self, user_type: str) -> Optional[str]:
        """유효한 토큰 획득"""
        try:
            login_data = self.test_users[user_type]
            async with self.session.post(
                f"{self.api_url}/api/auth/login",
                json=login_data
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get('access_token')
        except Exception as e:
            self.logger.error(f"토큰 획득 실패: {e}")
        return None
        
    async def test_api_security(self):
        """API 보안 테스트"""
        
        # 1. IDOR (Insecure Direct Object Reference) 테스트
        await self._test_idor_vulnerabilities()
        
        # 2. HTTP 메소드 조작 테스트
        await self._test_http_method_override()
        
        # 3. 속도 제한 테스트
        await self._test_rate_limiting()
        
        # 4. CORS 설정 테스트
        await self._test_cors_configuration()
        
        # 5. 보안 헤더 테스트
        await self._test_security_headers()
        
    async def _test_idor_vulnerabilities(self):
        """IDOR 취약점 테스트"""
        # 두 개의 다른 사용자 토큰 획득
        admin_token = await self._get_valid_token('admin')
        secretary_token = await self._get_valid_token('secretary')
        
        if not admin_token or not secretary_token:
            return
            
        # 관리자로 모델 생성
        admin_headers = {'Authorization': f'Bearer {admin_token}'}
        
        test_model = {
            "model_id": "idor-test-model",
            "provider": "test",
            "model_name": "idor-test",
            "display_name": "IDOR Test Model",
            "quality_score": 0.8,
            "speed_score": 0.9,
            "cost_efficiency": 0.85,
            "reliability_score": 0.9
        }
        
        try:
            # 관리자로 모델 생성
            async with self.session.post(
                f"{self.api_url}/api/ai-models/create",
                headers=admin_headers,
                json=test_model
            ) as response:
                if response.status == 201:
                    # 간사 권한으로 모델 수정 시도 (IDOR 테스트)
                    secretary_headers = {'Authorization': f'Bearer {secretary_token}'}
                    
                    update_data = {
                        "display_name": "Modified by Secretary",
                        "quality_score": 0.1
                    }
                    
                    async with self.session.put(
                        f"{self.api_url}/api/ai-models/{test_model['model_id']}",
                        headers=secretary_headers,
                        json=update_data
                    ) as update_response:
                        if update_response.status == 200:
                            self.results.append(SecurityTestResult(
                                test_category="api_security",
                                test_name="idor_vulnerability",
                                severity="high",
                                status="failed",
                                description="IDOR 취약점: 간사가 관리자 리소스 수정 가능",
                                details={
                                    "resource": test_model['model_id'],
                                    "unauthorized_action": "PUT /api/ai-models/{id}"
                                },
                                remediation="리소스 접근 시 소유권 및 권한 검증 강화",
                                timestamp=datetime.now()
                            ))
                        else:
                            self.results.append(SecurityTestResult(
                                test_category="api_security",
                                test_name="idor_protection",
                                severity="info",
                                status="passed",
                                description="IDOR 공격 차단됨",
                                details={
                                    "resource": test_model['model_id'],
                                    "blocked_action": "PUT /api/ai-models/{id}",
                                    "response_status": update_response.status
                                },
                                remediation="현재 접근 제어 정책 유지",
                                timestamp=datetime.now()
                            ))
                            
                    # 테스트 모델 정리
                    await self.session.delete(
                        f"{self.api_url}/api/ai-models/{test_model['model_id']}",
                        headers=admin_headers
                    )
                    
        except Exception as e:
            self.logger.error(f"IDOR 테스트 실패: {e}")
            
    async def _test_security_headers(self):
        """보안 헤더 테스트"""
        security_headers = {
            'X-Content-Type-Options': 'nosniff',
            'X-Frame-Options': 'DENY',
            'X-XSS-Protection': '1; mode=block',
            'Strict-Transport-Security': 'max-age=31536000; includeSubDomains',
            'Content-Security-Policy': 'default-src',
            'Referrer-Policy': 'strict-origin-when-cross-origin'
        }
        
        try:
            async with self.session.get(f"{self.target_url}") as response:
                missing_headers = []
                weak_headers = []
                
                for header, expected_value in security_headers.items():
                    actual_value = response.headers.get(header)
                    
                    if not actual_value:
                        missing_headers.append(header)
                    elif header == 'Content-Security-Policy' and 'unsafe-inline' in actual_value:
                        weak_headers.append(f"{header}: unsafe-inline 사용")
                    elif header == 'X-Frame-Options' and actual_value.lower() not in ['deny', 'sameorigin']:
                        weak_headers.append(f"{header}: {actual_value}")
                        
                if missing_headers:
                    self.results.append(SecurityTestResult(
                        test_category="api_security",
                        test_name="missing_security_headers",
                        severity="medium",
                        status="failed",
                        description="필수 보안 헤더 누락",
                        details={"missing_headers": missing_headers},
                        remediation="누락된 보안 헤더 추가 설정",
                        timestamp=datetime.now()
                    ))
                    
                if weak_headers:
                    self.results.append(SecurityTestResult(
                        test_category="api_security",
                        test_name="weak_security_headers",
                        severity="low",
                        status="warning",
                        description="약한 보안 헤더 설정",
                        details={"weak_headers": weak_headers},
                        remediation="보안 헤더 설정 강화",
                        timestamp=datetime.now()
                    ))
                    
                if not missing_headers and not weak_headers:
                    self.results.append(SecurityTestResult(
                        test_category="api_security",
                        test_name="security_headers",
                        severity="info",
                        status="passed",
                        description="보안 헤더 적절히 설정됨",
                        details={"checked_headers": list(security_headers.keys())},
                        remediation="현재 보안 헤더 설정 유지",
                        timestamp=datetime.now()
                    ))
                    
        except Exception as e:
            self.logger.error(f"보안 헤더 테스트 실패: {e}")
            
    async def test_session_security(self):
        """세션 보안 테스트"""
        
        # 1. 세션 고정 공격 테스트
        await self._test_session_fixation()
        
        # 2. CSRF 취약점 테스트  
        await self._test_csrf_protection()
        
        # 3. 세션 타임아웃 테스트
        await self._test_session_timeout()
        
    async def test_data_security(self):
        """데이터 보안 테스트"""
        
        # 1. 민감 정보 노출 테스트
        await self._test_sensitive_data_exposure()
        
        # 2. 로그 파일 보안 테스트
        await self._test_log_security()
        
    async def _test_sensitive_data_exposure(self):
        """민감 정보 노출 테스트"""
        try:
            # API 엔드포인트에서 민감 정보 노출 확인
            admin_token = await self._get_valid_token('admin')
            if admin_token:
                headers = {'Authorization': f'Bearer {admin_token}'}
                
                async with self.session.get(
                    f"{self.api_url}/api/ai-models/available",
                    headers=headers
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        response_text = json.dumps(data)
                        
                        # 민감 정보 패턴 검색
                        sensitive_patterns = {
                            'api_keys': r'(sk-[a-zA-Z0-9]{48}|sk-ant-[a-zA-Z0-9]{95})',
                            'passwords': r'password["\']?\s*[:=]\s*["\']([^"\']+)["\']',
                            'tokens': r'token["\']?\s*[:=]\s*["\']([^"\']+)["\']',
                            'secrets': r'secret["\']?\s*[:=]\s*["\']([^"\']+)["\']'
                        }
                        
                        for pattern_name, pattern in sensitive_patterns.items():
                            matches = re.findall(pattern, response_text, re.IGNORECASE)
                            if matches:
                                self.results.append(SecurityTestResult(
                                    test_category="data_security",
                                    test_name="sensitive_data_exposure",
                                    severity="critical",
                                    status="failed",
                                    description=f"API 응답에서 민감 정보 노출: {pattern_name}",
                                    details={
                                        "pattern_type": pattern_name,
                                        "matches_count": len(matches),
                                        "endpoint": "/api/ai-models/available"
                                    },
                                    remediation="API 응답에서 민감 정보 필터링 및 마스킹",
                                    timestamp=datetime.now()
                                ))
                                
        except Exception as e:
            self.logger.error(f"민감 정보 노출 테스트 실패: {e}")
            
    async def test_ssl_security(self):
        """SSL/TLS 보안 테스트"""
        parsed_url = urlparse(self.target_url)
        hostname = parsed_url.hostname
        port = parsed_url.port or (443 if parsed_url.scheme == 'https' else 80)
        
        if parsed_url.scheme != 'https':
            self.results.append(SecurityTestResult(
                test_category="transport_security",
                test_name="https_enforcement",
                severity="high",
                status="failed",
                description="HTTPS 사용되지 않음",
                details={"current_scheme": parsed_url.scheme},
                remediation="HTTPS 강제 사용 및 HTTP to HTTPS 리다이렉트 구현",
                timestamp=datetime.now()
            ))
            return
            
        try:
            # SSL 인증서 정보 확인
            context = ssl.create_default_context()
            
            with socket.create_connection((hostname, port), timeout=10) as sock:
                with context.wrap_socket(sock, server_hostname=hostname) as ssock:
                    cert = ssock.getpeercert()
                    
                    # 인증서 만료일 확인
                    not_after = datetime.strptime(cert['notAfter'], '%b %d %H:%M:%S %Y %Z')
                    days_until_expiry = (not_after - datetime.now()).days
                    
                    if days_until_expiry < 30:
                        severity = "high" if days_until_expiry < 7 else "medium"
                        self.results.append(SecurityTestResult(
                            test_category="transport_security",
                            test_name="ssl_certificate_expiry",
                            severity=severity,
                            status="warning",
                            description=f"SSL 인증서가 {days_until_expiry}일 후 만료",
                            details={
                                "expiry_date": cert['notAfter'],
                                "days_remaining": days_until_expiry
                            },
                            remediation="SSL 인증서 갱신",
                            timestamp=datetime.now()
                        ))
                        
                    # SSL 프로토콜 버전 확인
                    protocol_version = ssock.version()
                    if protocol_version in ['TLSv1', 'TLSv1.1']:
                        self.results.append(SecurityTestResult(
                            test_category="transport_security",
                            test_name="ssl_protocol_version",
                            severity="medium",
                            status="warning",
                            description=f"구버전 SSL/TLS 프로토콜 사용: {protocol_version}",
                            details={"protocol_version": protocol_version},
                            remediation="TLS 1.2 이상 사용 강제",
                            timestamp=datetime.now()
                        ))
                        
        except Exception as e:
            self.logger.error(f"SSL 보안 테스트 실패: {e}")
            
    async def generate_security_report(self) -> Dict[str, Any]:
        """보안 테스트 리포트 생성"""
        # 심각도별 집계
        severity_counts = {'critical': 0, 'high': 0, 'medium': 0, 'low': 0, 'info': 0}
        status_counts = {'passed': 0, 'failed': 0, 'warning': 0}
        category_results = {}
        
        for result in self.results:
            severity_counts[result.severity] += 1
            status_counts[result.status] += 1
            
            if result.test_category not in category_results:
                category_results[result.test_category] = []
            category_results[result.test_category].append(asdict(result))
            
        # 전체 보안 점수 계산 (0-100)
        total_tests = len(self.results)
        if total_tests > 0:
            # 가중치: critical(-10), high(-5), medium(-2), low(-1), passed(+1)
            score = 100
            score -= severity_counts['critical'] * 10
            score -= severity_counts['high'] * 5
            score -= severity_counts['medium'] * 2
            score -= severity_counts['low'] * 1
            score = max(0, min(100, score))
        else:
            score = 0
            
        # 위험 등급 결정
        if score >= 90:
            risk_level = "낮음"
        elif score >= 70:
            risk_level = "보통"
        elif score >= 50:
            risk_level = "높음"
        else:
            risk_level = "매우 높음"
            
        report = {
            'summary': {
                'total_tests': total_tests,
                'security_score': score,
                'risk_level': risk_level,
                'test_timestamp': datetime.now().isoformat(),
                'severity_distribution': severity_counts,
                'status_distribution': status_counts
            },
            'categories': category_results,
            'vulnerabilities': [asdict(vuln) for vuln in self.vulnerabilities],
            'recommendations': self._generate_recommendations()
        }
        
        return report
        
    def _generate_recommendations(self) -> List[str]:
        """보안 개선 권장사항 생성"""
        recommendations = []
        
        # 심각도별 권장사항
        critical_issues = [r for r in self.results if r.severity == 'critical']
        if critical_issues:
            recommendations.append("🚨 긴급: Critical 등급 취약점 즉시 해결 필요")
            
        high_issues = [r for r in self.results if r.severity == 'high']
        if high_issues:
            recommendations.append("⚠️ 높음: High 등급 취약점 7일 내 해결 권장")
            
        # 카테고리별 권장사항
        auth_issues = [r for r in self.results if r.test_category == 'authentication' and r.status == 'failed']
        if auth_issues:
            recommendations.append("🔐 인증 시스템 보안 강화 필요")
            
        input_issues = [r for r in self.results if r.test_category == 'input_validation' and r.status == 'failed']
        if input_issues:
            recommendations.append("📝 입력 검증 로직 개선 필요")
            
        # 일반적인 보안 강화 권장사항
        recommendations.extend([
            "🛡️ 정기적인 보안 테스트 및 코드 리뷰 실시",
            "📚 개발팀 보안 교육 프로그램 운영",
            "🔍 자동화된 보안 스캔 도구 도입",
            "📋 보안 정책 및 가이드라인 수립"
        ])
        
        return recommendations

def main():
    """메인 함수"""
    parser = argparse.ArgumentParser(description='AI Model Management Security Test')
    parser.add_argument('--target', default='http://localhost:3000', help='Target frontend URL')
    parser.add_argument('--api', default='http://localhost:8000', help='Target API URL')
    parser.add_argument('--mode', choices=['safe', 'aggressive'], default='safe', 
                       help='Test mode (safe=non-destructive, aggressive=may cause service impact)')
    
    args = parser.parse_args()
    
    async def run_security_tests():
        runner = SecurityTestRunner(args.target, args.api, args.mode)
        report = await runner.run_all_tests()
        
        # 리포트 출력
        print("\n" + "="*60)
        print("🔒 AI 모델 관리 시스템 - 보안 테스트 리포트")
        print("="*60)
        print(f"📊 전체 보안 점수: {report['summary']['security_score']}/100")
        print(f"🎯 위험 등급: {report['summary']['risk_level']}")
        print(f"🧪 총 테스트 수: {report['summary']['total_tests']}")
        print(f"⏰ 테스트 시간: {report['summary']['test_timestamp']}")
        print()
        
        # 심각도별 결과
        print("📊 심각도별 결과:")
        for severity, count in report['summary']['severity_distribution'].items():
            if count > 0:
                print(f"  {severity.upper()}: {count}개")
        print()
        
        # 주요 취약점
        critical_results = [r for category in report['categories'].values() 
                          for r in category if r['severity'] == 'critical']
        
        if critical_results:
            print("🚨 긴급 해결 필요 (Critical):")
            for result in critical_results[:5]:  # 상위 5개만 표시
                print(f"  - {result['description']}")
            print()
            
        # 권장사항
        print("💡 보안 개선 권장사항:")
        for rec in report['recommendations'][:5]:  # 상위 5개만 표시
            print(f"  {rec}")
        print()
        
        # 결과 저장
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # JSON 리포트
        json_file = f"security_report_{timestamp}.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False, default=str)
            
        print(f"📄 상세 리포트 저장: {json_file}")
        
        # 심각한 취약점이 발견된 경우 종료 코드 1 반환
        if report['summary']['security_score'] < 70:
            return 1
        return 0
        
    # 비동기 실행
    exit_code = asyncio.run(run_security_tests())
    exit(exit_code)

if __name__ == "__main__":
    main()