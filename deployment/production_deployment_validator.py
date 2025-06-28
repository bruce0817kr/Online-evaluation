#!/usr/bin/env python3
"""
🚀 AI 모델 관리 시스템 - 최종 프로덕션 배포 검증
스테이징 환경 완전성 검증 및 프로덕션 배포 준비도 평가

기능:
- 스테이징 환경 완전 검증
- 프로덕션 배포 준비도 평가
- 성능, 보안, 안정성 종합 검증
- 배포 체크리스트 완료도 확인
"""

import asyncio
import aiohttp
import json
import time
import logging
import os
import subprocess
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
import psutil
import hashlib

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class ValidationCheck:
    """검증 체크 항목"""
    category: str
    check_id: str
    name: str
    description: str
    status: str  # PASS, FAIL, WARNING, SKIP
    score: float
    details: str
    recommendation: Optional[str] = None

@dataclass
class DeploymentReadiness:
    """배포 준비도 평가"""
    category: str
    readiness_score: float
    required_score: float
    status: str  # READY, NOT_READY, WARNING
    critical_issues: List[str]
    improvements_needed: List[str]

class ProductionDeploymentValidator:
    """프로덕션 배포 검증기"""
    
    def __init__(self, staging_url: str, database_url: str):
        self.staging_url = staging_url.rstrip('/')
        self.database_url = database_url
        self.session = None
        self.validation_results: List[ValidationCheck] = []
        self.readiness_assessments: List[DeploymentReadiness] = []
        
    async def setup_session(self):
        """HTTP 세션 설정"""
        connector = aiohttp.TCPConnector(limit=50, limit_per_host=20)
        timeout = aiohttp.ClientTimeout(total=30)
        self.session = aiohttp.ClientSession(
            connector=connector,
            timeout=timeout,
            headers={"Content-Type": "application/json"}
        )
        logger.info("✅ HTTP 세션 설정 완료")
    
    async def cleanup_session(self):
        """HTTP 세션 정리"""
        if self.session:
            await self.session.close()
            logger.info("🔌 HTTP 세션 정리 완료")
    
    async def validate_infrastructure_readiness(self) -> Dict[str, Any]:
        """인프라 준비도 검증"""
        logger.info("🏗️ 인프라 준비도 검증 시작")
        
        checks = []
        
        # 1. 시스템 리소스 확인
        try:
            cpu_usage = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            # CPU 사용률 검증
            cpu_check = ValidationCheck(
                category="infrastructure",
                check_id="infra_001",
                name="CPU 사용률",
                description="시스템 CPU 사용률 확인",
                status="PASS" if cpu_usage < 70 else "WARNING" if cpu_usage < 85 else "FAIL",
                score=max(0, 100 - cpu_usage),
                details=f"현재 CPU 사용률: {cpu_usage:.1f}%",
                recommendation="CPU 사용률이 높을 경우 스케일링 고려" if cpu_usage > 70 else None
            )
            checks.append(cpu_check)
            
            # 메모리 사용률 검증
            memory_check = ValidationCheck(
                category="infrastructure",
                check_id="infra_002",
                name="메모리 사용률",
                description="시스템 메모리 사용률 확인",
                status="PASS" if memory.percent < 80 else "WARNING" if memory.percent < 90 else "FAIL",
                score=max(0, 100 - memory.percent),
                details=f"메모리 사용률: {memory.percent:.1f}%, 사용 가능: {memory.available / (1024**3):.1f}GB",
                recommendation="메모리 사용률이 높을 경우 인스턴스 업그레이드 고려" if memory.percent > 80 else None
            )
            checks.append(memory_check)
            
            # 디스크 사용률 검증
            disk_check = ValidationCheck(
                category="infrastructure",
                check_id="infra_003",
                name="디스크 사용률",
                description="시스템 디스크 사용률 확인",
                status="PASS" if disk.percent < 60 else "WARNING" if disk.percent < 80 else "FAIL",
                score=max(0, 100 - disk.percent),
                details=f"디스크 사용률: {disk.percent:.1f}%, 여유 공간: {disk.free / (1024**3):.1f}GB",
                recommendation="디스크 공간이 부족할 경우 볼륨 확장 필요" if disk.percent > 60 else None
            )
            checks.append(disk_check)
            
        except Exception as e:
            error_check = ValidationCheck(
                category="infrastructure",
                check_id="infra_error",
                name="시스템 리소스 확인 오류",
                description="시스템 리소스 정보 수집 실패",
                status="ERROR",
                score=0,
                details=f"오류: {str(e)}",
                recommendation="시스템 상태 수동 확인 필요"
            )
            checks.append(error_check)
        
        # 2. 네트워크 연결성 확인
        network_check = await self._validate_network_connectivity()
        checks.append(network_check)
        
        # 3. 서비스 가용성 확인
        service_checks = await self._validate_service_availability()
        checks.extend(service_checks)
        
        self.validation_results.extend(checks)
        
        # 인프라 준비도 평가
        infra_score = sum(check.score for check in checks) / len(checks) if checks else 0
        critical_issues = [check.details for check in checks if check.status == "FAIL"]
        warnings = [check.details for check in checks if check.status == "WARNING"]
        
        readiness = DeploymentReadiness(
            category="infrastructure",
            readiness_score=infra_score,
            required_score=85.0,
            status="READY" if infra_score >= 85 and not critical_issues else "WARNING" if infra_score >= 70 else "NOT_READY",
            critical_issues=critical_issues,
            improvements_needed=warnings
        )
        self.readiness_assessments.append(readiness)
        
        logger.info(f"✅ 인프라 준비도: {infra_score:.1f}점")
        return {
            "readiness_score": infra_score,
            "status": readiness.status,
            "checks": [asdict(check) for check in checks],
            "critical_issues": critical_issues
        }
    
    async def _validate_network_connectivity(self) -> ValidationCheck:
        """네트워크 연결성 검증"""
        try:
            start_time = time.time()
            async with self.session.get(f"{self.staging_url}/health") as response:
                response_time = (time.time() - start_time) * 1000
                
                if response.status == 200:
                    return ValidationCheck(
                        category="infrastructure",
                        check_id="network_001",
                        name="네트워크 연결성",
                        description="스테이징 환경 네트워크 연결 확인",
                        status="PASS",
                        score=100.0,
                        details=f"응답시간: {response_time:.1f}ms"
                    )
                else:
                    return ValidationCheck(
                        category="infrastructure",
                        check_id="network_001",
                        name="네트워크 연결성",
                        description="스테이징 환경 네트워크 연결 확인",
                        status="FAIL",
                        score=0.0,
                        details=f"HTTP {response.status} 응답",
                        recommendation="네트워크 설정 및 방화벽 확인 필요"
                    )
        except Exception as e:
            return ValidationCheck(
                category="infrastructure",
                check_id="network_001",
                name="네트워크 연결성",
                description="스테이징 환경 네트워크 연결 확인",
                status="FAIL",
                score=0.0,
                details=f"연결 실패: {str(e)}",
                recommendation="네트워크 연결 상태 점검 필요"
            )
    
    async def _validate_service_availability(self) -> List[ValidationCheck]:
        """서비스 가용성 검증"""
        checks = []
        
        # 주요 서비스 엔드포인트 확인
        endpoints = [
            ("/health", "시스템 헬스체크"),
            ("/api/health", "API 헬스체크"),
            ("/api/auth/login", "인증 서비스"),
            ("/api/users", "사용자 관리 서비스"),
            ("/api/templates", "템플릿 관리 서비스")
        ]
        
        for endpoint, service_name in endpoints:
            try:
                start_time = time.time()
                
                # POST 요청인 경우 (로그인)
                if endpoint == "/api/auth/login":
                    payload = {"login_id": "test", "password": "test"}
                    async with self.session.post(f"{self.staging_url}{endpoint}", json=payload) as response:
                        response_time = (time.time() - start_time) * 1000
                        # 401은 정상 (잘못된 인증 정보이므로)
                        expected_status = response.status in [200, 401, 422]
                else:
                    async with self.session.get(f"{self.staging_url}{endpoint}") as response:
                        response_time = (time.time() - start_time) * 1000
                        # 인증이 필요한 엔드포인트는 401도 정상
                        expected_status = response.status in [200, 401]
                
                if expected_status:
                    status = "PASS"
                    score = 100.0
                    details = f"서비스 정상 동작 (응답시간: {response_time:.1f}ms)"
                    recommendation = None
                else:
                    status = "FAIL"
                    score = 0.0
                    details = f"서비스 응답 오류: HTTP {response.status}"
                    recommendation = f"{service_name} 서비스 상태 점검 필요"
                
                check = ValidationCheck(
                    category="infrastructure",
                    check_id=f"service_{endpoint.replace('/', '_').replace('-', '_')}",
                    name=service_name,
                    description=f"{service_name} 가용성 확인",
                    status=status,
                    score=score,
                    details=details,
                    recommendation=recommendation
                )
                checks.append(check)
                
            except Exception as e:
                check = ValidationCheck(
                    category="infrastructure",
                    check_id=f"service_{endpoint.replace('/', '_').replace('-', '_')}",
                    name=service_name,
                    description=f"{service_name} 가용성 확인",
                    status="FAIL",
                    score=0.0,
                    details=f"서비스 접근 실패: {str(e)}",
                    recommendation=f"{service_name} 서비스 재시작 및 로그 확인 필요"
                )
                checks.append(check)
        
        return checks
    
    async def validate_application_readiness(self) -> Dict[str, Any]:
        """애플리케이션 준비도 검증"""
        logger.info("🔧 애플리케이션 준비도 검증 시작")
        
        checks = []
        
        # 1. API 엔드포인트 완전성 검증
        api_completeness = await self._validate_api_completeness()
        checks.extend(api_completeness)
        
        # 2. 데이터베이스 스키마 검증
        db_schema_check = await self._validate_database_schema()
        checks.append(db_schema_check)
        
        # 3. 인증 시스템 검증
        auth_check = await self._validate_authentication_system()
        checks.append(auth_check)
        
        # 4. 파일 업로드 기능 검증
        file_upload_check = await self._validate_file_upload()
        checks.append(file_upload_check)
        
        # 5. 에러 핸들링 검증
        error_handling_checks = await self._validate_error_handling()
        checks.extend(error_handling_checks)
        
        self.validation_results.extend(checks)
        
        # 애플리케이션 준비도 평가
        app_score = sum(check.score for check in checks) / len(checks) if checks else 0
        critical_issues = [check.details for check in checks if check.status == "FAIL"]
        warnings = [check.details for check in checks if check.status == "WARNING"]
        
        readiness = DeploymentReadiness(
            category="application",
            readiness_score=app_score,
            required_score=90.0,
            status="READY" if app_score >= 90 and not critical_issues else "WARNING" if app_score >= 75 else "NOT_READY",
            critical_issues=critical_issues,
            improvements_needed=warnings
        )
        self.readiness_assessments.append(readiness)
        
        logger.info(f"✅ 애플리케이션 준비도: {app_score:.1f}점")
        return {
            "readiness_score": app_score,
            "status": readiness.status,
            "checks": [asdict(check) for check in checks],
            "critical_issues": critical_issues
        }
    
    async def _validate_api_completeness(self) -> List[ValidationCheck]:
        """API 완전성 검증"""
        checks = []
        
        # 필수 API 엔드포인트 목록
        required_endpoints = [
            ("GET", "/health", "시스템 헬스체크"),
            ("GET", "/api/health", "API 헬스체크"),
            ("POST", "/api/auth/login", "로그인"),
            ("POST", "/api/auth/logout", "로그아웃"),
            ("GET", "/api/auth/me", "현재 사용자 정보"),
            ("GET", "/api/users", "사용자 목록"),
            ("POST", "/api/users", "사용자 생성"),
            ("GET", "/api/companies", "회사 목록"),
            ("GET", "/api/projects", "프로젝트 목록"),
            ("POST", "/api/projects", "프로젝트 생성"),
            ("GET", "/api/templates", "템플릿 목록"),
            ("GET", "/api/evaluations", "평가 목록"),
            ("GET", "/api/files", "파일 목록"),
            ("POST", "/api/files/upload", "파일 업로드")
        ]
        
        for method, endpoint, description in required_endpoints:
            try:
                if method == "GET":
                    async with self.session.get(f"{self.staging_url}{endpoint}") as response:
                        # 200 (성공) 또는 401 (인증 필요)은 엔드포인트가 존재함을 의미
                        exists = response.status != 404
                elif method == "POST":
                    # POST는 빈 데이터로 테스트 (400 또는 422는 정상)
                    async with self.session.post(f"{self.staging_url}{endpoint}", json={}) as response:
                        exists = response.status != 404
                else:
                    exists = False
                
                if exists:
                    check = ValidationCheck(
                        category="application",
                        check_id=f"api_{method.lower()}_{endpoint.replace('/', '_').replace('-', '_')}",
                        name=f"{method} {endpoint}",
                        description=f"{description} 엔드포인트 존재 확인",
                        status="PASS",
                        score=100.0,
                        details="엔드포인트 정상 동작"
                    )
                else:
                    check = ValidationCheck(
                        category="application",
                        check_id=f"api_{method.lower()}_{endpoint.replace('/', '_').replace('-', '_')}",
                        name=f"{method} {endpoint}",
                        description=f"{description} 엔드포인트 존재 확인",
                        status="FAIL",
                        score=0.0,
                        details="엔드포인트 없음 (404 응답)",
                        recommendation=f"{description} 엔드포인트 구현 필요"
                    )
                
                checks.append(check)
                
            except Exception as e:
                check = ValidationCheck(
                    category="application",
                    check_id=f"api_{method.lower()}_{endpoint.replace('/', '_').replace('-', '_')}",
                    name=f"{method} {endpoint}",
                    description=f"{description} 엔드포인트 존재 확인",
                    status="FAIL",
                    score=0.0,
                    details=f"엔드포인트 접근 실패: {str(e)}",
                    recommendation="네트워크 및 서비스 상태 확인 필요"
                )
                checks.append(check)
        
        return checks
    
    async def _validate_database_schema(self) -> ValidationCheck:
        """데이터베이스 스키마 검증"""
        try:
            # 데이터베이스 연결 테스트를 위한 시뮬레이션
            # 실제로는 MongoDB 연결 및 컬렉션 확인이 필요
            
            # API를 통한 간접 검증
            async with self.session.get(f"{self.staging_url}/api/health") as response:
                if response.status == 200:
                    data = await response.json()
                    db_status = data.get("database", {}).get("status", "unknown")
                    
                    if db_status == "connected":
                        return ValidationCheck(
                            category="application",
                            check_id="db_schema_001",
                            name="데이터베이스 스키마",
                            description="데이터베이스 연결 및 스키마 확인",
                            status="PASS",
                            score=100.0,
                            details="데이터베이스 정상 연결"
                        )
                    else:
                        return ValidationCheck(
                            category="application",
                            check_id="db_schema_001",
                            name="데이터베이스 스키마",
                            description="데이터베이스 연결 및 스키마 확인",
                            status="FAIL",
                            score=0.0,
                            details=f"데이터베이스 상태: {db_status}",
                            recommendation="데이터베이스 연결 설정 확인 필요"
                        )
                else:
                    return ValidationCheck(
                        category="application",
                        check_id="db_schema_001",
                        name="데이터베이스 스키마",
                        description="데이터베이스 연결 및 스키마 확인",
                        status="FAIL",
                        score=0.0,
                        details="API 헬스체크 실패",
                        recommendation="API 서버 상태 확인 필요"
                    )
                    
        except Exception as e:
            return ValidationCheck(
                category="application",
                check_id="db_schema_001",
                name="데이터베이스 스키마",
                description="데이터베이스 연결 및 스키마 확인",
                status="FAIL",
                score=0.0,
                details=f"데이터베이스 검증 실패: {str(e)}",
                recommendation="데이터베이스 연결 및 설정 점검 필요"
            )
    
    async def _validate_authentication_system(self) -> ValidationCheck:
        """인증 시스템 검증"""
        try:
            # 올바른 인증 정보로 로그인 테스트
            login_payload = {"login_id": "admin", "password": "admin123!"}
            
            async with self.session.post(f"{self.staging_url}/api/auth/login", json=login_payload) as response:
                if response.status == 200:
                    data = await response.json()
                    if "access_token" in data:
                        # 토큰으로 보호된 엔드포인트 접근 테스트
                        token = data["access_token"]
                        headers = {"Authorization": f"Bearer {token}"}
                        
                        async with self.session.get(f"{self.staging_url}/api/auth/me", headers=headers) as auth_response:
                            if auth_response.status == 200:
                                return ValidationCheck(
                                    category="application",
                                    check_id="auth_001",
                                    name="인증 시스템",
                                    description="JWT 인증 시스템 동작 확인",
                                    status="PASS",
                                    score=100.0,
                                    details="인증 및 토큰 기반 접근 정상"
                                )
                            else:
                                return ValidationCheck(
                                    category="application",
                                    check_id="auth_001",
                                    name="인증 시스템",
                                    description="JWT 인증 시스템 동작 확인",
                                    status="FAIL",
                                    score=50.0,
                                    details="토큰 기반 접근 실패",
                                    recommendation="JWT 토큰 검증 로직 확인 필요"
                                )
                    else:
                        return ValidationCheck(
                            category="application",
                            check_id="auth_001",
                            name="인증 시스템",
                            description="JWT 인증 시스템 동작 확인",
                            status="FAIL",
                            score=25.0,
                            details="로그인 응답에 토큰 없음",
                            recommendation="인증 응답 형식 확인 필요"
                        )
                else:
                    return ValidationCheck(
                        category="application",
                        check_id="auth_001",
                        name="인증 시스템",
                        description="JWT 인증 시스템 동작 확인",
                        status="FAIL",
                        score=0.0,
                        details=f"로그인 실패: HTTP {response.status}",
                        recommendation="인증 시스템 및 사용자 데이터 확인 필요"
                    )
                    
        except Exception as e:
            return ValidationCheck(
                category="application",
                check_id="auth_001",
                name="인증 시스템",
                description="JWT 인증 시스템 동작 확인",
                status="FAIL",
                score=0.0,
                details=f"인증 테스트 실패: {str(e)}",
                recommendation="인증 서비스 상태 점검 필요"
            )
    
    async def _validate_file_upload(self) -> ValidationCheck:
        """파일 업로드 기능 검증"""
        try:
            # 파일 업로드 엔드포인트 존재 확인
            async with self.session.post(f"{self.staging_url}/api/files/upload") as response:
                # 401 (인증 필요) 또는 400 (잘못된 요청)은 엔드포인트가 존재함을 의미
                if response.status in [400, 401, 422]:
                    return ValidationCheck(
                        category="application",
                        check_id="file_upload_001",
                        name="파일 업로드",
                        description="파일 업로드 기능 확인",
                        status="PASS",
                        score=100.0,
                        details="파일 업로드 엔드포인트 존재"
                    )
                elif response.status == 404:
                    return ValidationCheck(
                        category="application",
                        check_id="file_upload_001",
                        name="파일 업로드",
                        description="파일 업로드 기능 확인",
                        status="FAIL",
                        score=0.0,
                        details="파일 업로드 엔드포인트 없음",
                        recommendation="파일 업로드 API 구현 필요"
                    )
                else:
                    return ValidationCheck(
                        category="application",
                        check_id="file_upload_001",
                        name="파일 업로드",
                        description="파일 업로드 기능 확인",
                        status="WARNING",
                        score=75.0,
                        details=f"예상하지 못한 응답: HTTP {response.status}",
                        recommendation="파일 업로드 엔드포인트 동작 확인 필요"
                    )
                    
        except Exception as e:
            return ValidationCheck(
                category="application",
                check_id="file_upload_001",
                name="파일 업로드",
                description="파일 업로드 기능 확인",
                status="FAIL",
                score=0.0,
                details=f"파일 업로드 테스트 실패: {str(e)}",
                recommendation="파일 업로드 서비스 상태 확인 필요"
            )
    
    async def _validate_error_handling(self) -> List[ValidationCheck]:
        """에러 핸들링 검증"""
        checks = []
        
        # 1. 404 에러 처리
        try:
            async with self.session.get(f"{self.staging_url}/api/nonexistent") as response:
                if response.status == 404:
                    check = ValidationCheck(
                        category="application",
                        check_id="error_404",
                        name="404 에러 처리",
                        description="존재하지 않는 엔드포인트 처리",
                        status="PASS",
                        score=100.0,
                        details="404 에러 정상 반환"
                    )
                else:
                    check = ValidationCheck(
                        category="application",
                        check_id="error_404",
                        name="404 에러 처리",
                        description="존재하지 않는 엔드포인트 처리",
                        status="FAIL",
                        score=0.0,
                        details=f"예상하지 못한 응답: HTTP {response.status}",
                        recommendation="404 에러 핸들링 구현 필요"
                    )
        except Exception as e:
            check = ValidationCheck(
                category="application",
                check_id="error_404",
                name="404 에러 처리",
                description="존재하지 않는 엔드포인트 처리",
                status="FAIL",
                score=0.0,
                details=f"404 테스트 실패: {str(e)}",
                recommendation="에러 핸들링 미들웨어 확인 필요"
            )
        checks.append(check)
        
        # 2. 잘못된 JSON 처리
        try:
            async with self.session.post(
                f"{self.staging_url}/api/auth/login",
                data="invalid json",
                headers={"Content-Type": "application/json"}
            ) as response:
                if response.status == 400:
                    check = ValidationCheck(
                        category="application",
                        check_id="error_json",
                        name="JSON 파싱 에러 처리",
                        description="잘못된 JSON 형식 처리",
                        status="PASS",
                        score=100.0,
                        details="잘못된 JSON에 대해 400 에러 반환"
                    )
                else:
                    check = ValidationCheck(
                        category="application",
                        check_id="error_json",
                        name="JSON 파싱 에러 처리",
                        description="잘못된 JSON 형식 처리",
                        status="FAIL",
                        score=0.0,
                        details=f"예상하지 못한 응답: HTTP {response.status}",
                        recommendation="JSON 파싱 에러 핸들링 개선 필요"
                    )
        except Exception as e:
            check = ValidationCheck(
                category="application",
                check_id="error_json",
                name="JSON 파싱 에러 처리",
                description="잘못된 JSON 형식 처리",
                status="FAIL",
                score=0.0,
                details=f"JSON 에러 테스트 실패: {str(e)}",
                recommendation="JSON 파싱 에러 핸들링 구현 필요"
            )
        checks.append(check)
        
        return checks
    
    async def validate_performance_readiness(self) -> Dict[str, Any]:
        """성능 준비도 검증"""
        logger.info("⚡ 성능 준비도 검증 시작")
        
        checks = []
        
        # 1. 응답시간 테스트
        response_time_check = await self._validate_response_times()
        checks.append(response_time_check)
        
        # 2. 동시 접속 테스트
        concurrent_check = await self._validate_concurrent_access()
        checks.append(concurrent_check)
        
        # 3. 캐시 성능 테스트
        cache_check = await self._validate_cache_performance()
        checks.append(cache_check)
        
        self.validation_results.extend(checks)
        
        # 성능 준비도 평가
        perf_score = sum(check.score for check in checks) / len(checks) if checks else 0
        critical_issues = [check.details for check in checks if check.status == "FAIL"]
        warnings = [check.details for check in checks if check.status == "WARNING"]
        
        readiness = DeploymentReadiness(
            category="performance",
            readiness_score=perf_score,
            required_score=80.0,
            status="READY" if perf_score >= 80 and not critical_issues else "WARNING" if perf_score >= 65 else "NOT_READY",
            critical_issues=critical_issues,
            improvements_needed=warnings
        )
        self.readiness_assessments.append(readiness)
        
        logger.info(f"✅ 성능 준비도: {perf_score:.1f}점")
        return {
            "readiness_score": perf_score,
            "status": readiness.status,
            "checks": [asdict(check) for check in checks],
            "critical_issues": critical_issues
        }
    
    async def _validate_response_times(self) -> ValidationCheck:
        """응답시간 검증"""
        try:
            endpoints = ["/health", "/api/health", "/api/templates"]
            response_times = []
            
            for endpoint in endpoints:
                for _ in range(3):  # 각 엔드포인트 3회 테스트
                    start_time = time.time()
                    async with self.session.get(f"{self.staging_url}{endpoint}") as response:
                        response_time = (time.time() - start_time) * 1000
                        if response.status in [200, 401]:  # 정상 응답
                            response_times.append(response_time)
            
            if response_times:
                avg_response_time = sum(response_times) / len(response_times)
                max_response_time = max(response_times)
                
                if avg_response_time < 200:
                    status = "PASS"
                    score = 100.0
                elif avg_response_time < 500:
                    status = "WARNING"
                    score = 80.0
                else:
                    status = "FAIL"
                    score = 50.0
                
                return ValidationCheck(
                    category="performance",
                    check_id="perf_response_time",
                    name="응답시간 성능",
                    description="API 응답시간 측정",
                    status=status,
                    score=score,
                    details=f"평균: {avg_response_time:.1f}ms, 최대: {max_response_time:.1f}ms",
                    recommendation="응답시간 최적화 필요" if avg_response_time > 200 else None
                )
            else:
                return ValidationCheck(
                    category="performance",
                    check_id="perf_response_time",
                    name="응답시간 성능",
                    description="API 응답시간 측정",
                    status="FAIL",
                    score=0.0,
                    details="응답시간 측정 실패",
                    recommendation="API 서비스 상태 확인 필요"
                )
                
        except Exception as e:
            return ValidationCheck(
                category="performance",
                check_id="perf_response_time",
                name="응답시간 성능",
                description="API 응답시간 측정",
                status="FAIL",
                score=0.0,
                details=f"응답시간 테스트 실패: {str(e)}",
                recommendation="성능 테스트 환경 확인 필요"
            )
    
    async def _validate_concurrent_access(self) -> ValidationCheck:
        """동시 접속 테스트"""
        try:
            # 5개 동시 요청으로 간단한 부하 테스트
            concurrent_requests = 5
            tasks = []
            
            for _ in range(concurrent_requests):
                task = self.session.get(f"{self.staging_url}/health")
                tasks.append(task)
            
            start_time = time.time()
            responses = await asyncio.gather(*tasks, return_exceptions=True)
            total_time = time.time() - start_time
            
            successful_responses = 0
            for response in responses:
                if not isinstance(response, Exception) and hasattr(response, 'status'):
                    if response.status == 200:
                        successful_responses += 1
                    response.close()
            
            success_rate = (successful_responses / concurrent_requests) * 100
            
            if success_rate >= 100:
                status = "PASS"
                score = 100.0
            elif success_rate >= 80:
                status = "WARNING"
                score = 80.0
            else:
                status = "FAIL"
                score = 50.0
            
            return ValidationCheck(
                category="performance",
                check_id="perf_concurrent",
                name="동시 접속 처리",
                description="동시 요청 처리 능력 확인",
                status=status,
                score=score,
                details=f"성공률: {success_rate:.1f}% ({successful_responses}/{concurrent_requests}), 소요시간: {total_time:.2f}초",
                recommendation="동시 접속 처리 개선 필요" if success_rate < 100 else None
            )
            
        except Exception as e:
            return ValidationCheck(
                category="performance",
                check_id="perf_concurrent",
                name="동시 접속 처리",
                description="동시 요청 처리 능력 확인",
                status="FAIL",
                score=0.0,
                details=f"동시 접속 테스트 실패: {str(e)}",
                recommendation="서버 안정성 및 설정 확인 필요"
            )
    
    async def _validate_cache_performance(self) -> ValidationCheck:
        """캐시 성능 검증"""
        try:
            # 같은 엔드포인트를 연속으로 호출하여 캐시 효과 확인
            endpoint = "/api/templates"
            
            # 첫 번째 요청 (캐시 미스)
            start_time = time.time()
            async with self.session.get(f"{self.staging_url}{endpoint}") as response:
                first_response_time = (time.time() - start_time) * 1000
                first_status = response.status
            
            # 두 번째 요청 (캐시 히트 예상)
            start_time = time.time()
            async with self.session.get(f"{self.staging_url}{endpoint}") as response:
                second_response_time = (time.time() - start_time) * 1000
                second_status = response.status
            
            if first_status in [200, 401] and second_status in [200, 401]:
                # 캐시가 효과적이라면 두 번째 요청이 더 빨라야 함
                improvement = (first_response_time - second_response_time) / first_response_time * 100
                
                if improvement > 10:  # 10% 이상 개선
                    status = "PASS"
                    score = 100.0
                    details = f"캐시 효과 확인 (개선: {improvement:.1f}%)"
                elif improvement > 0:
                    status = "WARNING"
                    score = 70.0
                    details = f"캐시 효과 미미 (개선: {improvement:.1f}%)"
                else:
                    status = "WARNING"
                    score = 50.0
                    details = f"캐시 효과 없음 (첫째: {first_response_time:.1f}ms, 둘째: {second_response_time:.1f}ms)"
                
                return ValidationCheck(
                    category="performance",
                    check_id="perf_cache",
                    name="캐시 성능",
                    description="응답 캐싱 효과 확인",
                    status=status,
                    score=score,
                    details=details,
                    recommendation="캐시 전략 최적화 필요" if score < 100 else None
                )
            else:
                return ValidationCheck(
                    category="performance",
                    check_id="perf_cache",
                    name="캐시 성능",
                    description="응답 캐싱 효과 확인",
                    status="FAIL",
                    score=0.0,
                    details=f"엔드포인트 접근 실패 (상태: {first_status}, {second_status})",
                    recommendation="API 엔드포인트 상태 확인 필요"
                )
                
        except Exception as e:
            return ValidationCheck(
                category="performance",
                check_id="perf_cache",
                name="캐시 성능",
                description="응답 캐싱 효과 확인",
                status="FAIL",
                score=0.0,
                details=f"캐시 성능 테스트 실패: {str(e)}",
                recommendation="캐시 시스템 상태 확인 필요"
            )
    
    async def validate_security_readiness(self) -> Dict[str, Any]:
        """보안 준비도 검증"""
        logger.info("🔒 보안 준비도 검증 시작")
        
        checks = []
        
        # 1. HTTPS 설정 확인
        https_check = await self._validate_https_configuration()
        checks.append(https_check)
        
        # 2. 보안 헤더 확인
        security_headers_check = await self._validate_security_headers()
        checks.append(security_headers_check)
        
        # 3. 인증 보안 확인
        auth_security_check = await self._validate_authentication_security()
        checks.append(auth_security_check)
        
        # 4. 입력 검증 확인
        input_validation_check = await self._validate_input_validation()
        checks.append(input_validation_check)
        
        self.validation_results.extend(checks)
        
        # 보안 준비도 평가
        security_score = sum(check.score for check in checks) / len(checks) if checks else 0
        critical_issues = [check.details for check in checks if check.status == "FAIL"]
        warnings = [check.details for check in checks if check.status == "WARNING"]
        
        readiness = DeploymentReadiness(
            category="security",
            readiness_score=security_score,
            required_score=95.0,
            status="READY" if security_score >= 95 and not critical_issues else "WARNING" if security_score >= 80 else "NOT_READY",
            critical_issues=critical_issues,
            improvements_needed=warnings
        )
        self.readiness_assessments.append(readiness)
        
        logger.info(f"✅ 보안 준비도: {security_score:.1f}점")
        return {
            "readiness_score": security_score,
            "status": readiness.status,
            "checks": [asdict(check) for check in checks],
            "critical_issues": critical_issues
        }
    
    async def _validate_https_configuration(self) -> ValidationCheck:
        """HTTPS 설정 검증"""
        try:
            # HTTPS URL로 요청 시도
            https_url = self.staging_url.replace("http://", "https://")
            
            async with self.session.get(f"{https_url}/health") as response:
                if response.status == 200:
                    return ValidationCheck(
                        category="security",
                        check_id="sec_https",
                        name="HTTPS 설정",
                        description="HTTPS 암호화 연결 확인",
                        status="PASS",
                        score=100.0,
                        details="HTTPS 연결 정상 동작"
                    )
                else:
                    return ValidationCheck(
                        category="security",
                        check_id="sec_https",
                        name="HTTPS 설정",
                        description="HTTPS 암호화 연결 확인",
                        status="WARNING",
                        score=50.0,
                        details=f"HTTPS 응답 오류: HTTP {response.status}",
                        recommendation="HTTPS 설정 확인 및 SSL 인증서 점검 필요"
                    )
                    
        except Exception as e:
            # HTTP로 폴백 테스트
            if "http://" in self.staging_url:
                return ValidationCheck(
                    category="security",
                    check_id="sec_https",
                    name="HTTPS 설정",
                    description="HTTPS 암호화 연결 확인",
                    status="FAIL",
                    score=0.0,
                    details="HTTPS 미설정 (HTTP만 지원)",
                    recommendation="프로덕션 배포 전 HTTPS 설정 필수"
                )
            else:
                return ValidationCheck(
                    category="security",
                    check_id="sec_https",
                    name="HTTPS 설정",
                    description="HTTPS 암호화 연결 확인",
                    status="FAIL",
                    score=0.0,
                    details=f"HTTPS 연결 실패: {str(e)}",
                    recommendation="SSL/TLS 설정 및 인증서 확인 필요"
                )
    
    async def _validate_security_headers(self) -> ValidationCheck:
        """보안 헤더 검증"""
        try:
            async with self.session.get(f"{self.staging_url}/health") as response:
                headers = response.headers
                
                security_headers = {
                    "X-Content-Type-Options": headers.get("X-Content-Type-Options"),
                    "X-Frame-Options": headers.get("X-Frame-Options"),
                    "X-XSS-Protection": headers.get("X-XSS-Protection"),
                    "Strict-Transport-Security": headers.get("Strict-Transport-Security"),
                    "Content-Security-Policy": headers.get("Content-Security-Policy"),
                    "Referrer-Policy": headers.get("Referrer-Policy")
                }
                
                present_headers = [k for k, v in security_headers.items() if v is not None]
                missing_headers = [k for k, v in security_headers.items() if v is None]
                
                score = (len(present_headers) / len(security_headers)) * 100
                
                if score >= 100:
                    status = "PASS"
                elif score >= 80:
                    status = "WARNING"
                else:
                    status = "FAIL"
                
                return ValidationCheck(
                    category="security",
                    check_id="sec_headers",
                    name="보안 헤더",
                    description="HTTP 보안 헤더 설정 확인",
                    status=status,
                    score=score,
                    details=f"설정된 헤더: {len(present_headers)}/{len(security_headers)}, 누락: {missing_headers}",
                    recommendation="누락된 보안 헤더 설정 필요" if missing_headers else None
                )
                
        except Exception as e:
            return ValidationCheck(
                category="security",
                check_id="sec_headers",
                name="보안 헤더",
                description="HTTP 보안 헤더 설정 확인",
                status="FAIL",
                score=0.0,
                details=f"보안 헤더 확인 실패: {str(e)}",
                recommendation="서버 보안 설정 확인 필요"
            )
    
    async def _validate_authentication_security(self) -> ValidationCheck:
        """인증 보안 검증"""
        try:
            # 잘못된 토큰으로 접근 시도
            invalid_token = "invalid.jwt.token"
            headers = {"Authorization": f"Bearer {invalid_token}"}
            
            async with self.session.get(f"{self.staging_url}/api/auth/me", headers=headers) as response:
                if response.status == 401:
                    return ValidationCheck(
                        category="security",
                        check_id="sec_auth",
                        name="인증 보안",
                        description="잘못된 토큰 거부 확인",
                        status="PASS",
                        score=100.0,
                        details="잘못된 JWT 토큰 정상 거부"
                    )
                else:
                    return ValidationCheck(
                        category="security",
                        check_id="sec_auth",
                        name="인증 보안",
                        description="잘못된 토큰 거부 확인",
                        status="FAIL",
                        score=0.0,
                        details=f"잘못된 토큰이 승인됨: HTTP {response.status}",
                        recommendation="JWT 토큰 검증 로직 강화 필요"
                    )
                    
        except Exception as e:
            return ValidationCheck(
                category="security",
                check_id="sec_auth",
                name="인증 보안",
                description="잘못된 토큰 거부 확인",
                status="FAIL",
                score=0.0,
                details=f"인증 보안 테스트 실패: {str(e)}",
                recommendation="인증 시스템 상태 확인 필요"
            )
    
    async def _validate_input_validation(self) -> ValidationCheck:
        """입력 검증 확인"""
        try:
            # SQL 인젝션 시도
            malicious_payload = {
                "login_id": "'; DROP TABLE users; --",
                "password": "test"
            }
            
            async with self.session.post(f"{self.staging_url}/api/auth/login", json=malicious_payload) as response:
                # 400, 401, 422 중 하나여야 정상 (인젝션 방어)
                if response.status in [400, 401, 422]:
                    return ValidationCheck(
                        category="security",
                        check_id="sec_input",
                        name="입력 검증",
                        description="악성 입력 방어 확인",
                        status="PASS",
                        score=100.0,
                        details="악성 입력 정상 차단"
                    )
                elif response.status == 200:
                    return ValidationCheck(
                        category="security",
                        check_id="sec_input",
                        name="입력 검증",
                        description="악성 입력 방어 확인",
                        status="FAIL",
                        score=0.0,
                        details="악성 입력이 승인됨",
                        recommendation="입력 검증 및 SQL 인젝션 방어 강화 필요"
                    )
                else:
                    return ValidationCheck(
                        category="security",
                        check_id="sec_input",
                        name="입력 검증",
                        description="악성 입력 방어 확인",
                        status="WARNING",
                        score=70.0,
                        details=f"예상하지 못한 응답: HTTP {response.status}",
                        recommendation="입력 검증 로직 확인 필요"
                    )
                    
        except Exception as e:
            return ValidationCheck(
                category="security",
                check_id="sec_input",
                name="입력 검증",
                description="악성 입력 방어 확인",
                status="FAIL",
                score=0.0,
                details=f"입력 검증 테스트 실패: {str(e)}",
                recommendation="입력 검증 시스템 상태 확인 필요"
            )
    
    async def generate_deployment_readiness_report(self) -> Dict[str, Any]:
        """배포 준비도 리포트 생성"""
        logger.info("📋 최종 배포 준비도 리포트 생성")
        
        # 전체 점수 계산
        if self.readiness_assessments:
            overall_score = sum(assessment.readiness_score for assessment in self.readiness_assessments) / len(self.readiness_assessments)
        else:
            overall_score = 0.0
        
        # 전체 상태 결정
        critical_failures = [assessment for assessment in self.readiness_assessments if assessment.status == "NOT_READY"]
        has_warnings = any(assessment.status == "WARNING" for assessment in self.readiness_assessments)
        
        if critical_failures:
            overall_status = "NOT_READY"
            overall_recommendation = "중요한 문제들을 해결한 후 재검증 필요"
        elif has_warnings:
            overall_status = "WARNING" 
            overall_recommendation = "경고 사항들을 검토한 후 배포 고려"
        else:
            overall_status = "READY"
            overall_recommendation = "프로덕션 배포 준비 완료"
        
        # 카테고리별 체크리스트
        deployment_checklist = {
            "infrastructure": {
                "completed": len([c for c in self.validation_results if c.category == "infrastructure" and c.status == "PASS"]),
                "total": len([c for c in self.validation_results if c.category == "infrastructure"]),
                "critical_items": [c.details for c in self.validation_results if c.category == "infrastructure" and c.status == "FAIL"]
            },
            "application": {
                "completed": len([c for c in self.validation_results if c.category == "application" and c.status == "PASS"]),
                "total": len([c for c in self.validation_results if c.category == "application"]),
                "critical_items": [c.details for c in self.validation_results if c.category == "application" and c.status == "FAIL"]
            },
            "performance": {
                "completed": len([c for c in self.validation_results if c.category == "performance" and c.status == "PASS"]),
                "total": len([c for c in self.validation_results if c.category == "performance"]),
                "critical_items": [c.details for c in self.validation_results if c.category == "performance" and c.status == "FAIL"]
            },
            "security": {
                "completed": len([c for c in self.validation_results if c.category == "security" and c.status == "PASS"]),
                "total": len([c for c in self.validation_results if c.category == "security"]),
                "critical_items": [c.details for c in self.validation_results if c.category == "security" and c.status == "FAIL"]
            }
        }
        
        return {
            "validation_summary": {
                "timestamp": datetime.now().isoformat(),
                "overall_score": round(overall_score, 1),
                "overall_status": overall_status,
                "overall_recommendation": overall_recommendation,
                "total_checks": len(self.validation_results),
                "passed_checks": len([c for c in self.validation_results if c.status == "PASS"]),
                "failed_checks": len([c for c in self.validation_results if c.status == "FAIL"]),
                "warning_checks": len([c for c in self.validation_results if c.status == "WARNING"])
            },
            "readiness_by_category": {
                assessment.category: {
                    "score": assessment.readiness_score,
                    "status": assessment.status,
                    "required_score": assessment.required_score,
                    "critical_issues": assessment.critical_issues,
                    "improvements_needed": assessment.improvements_needed
                }
                for assessment in self.readiness_assessments
            },
            "deployment_checklist": deployment_checklist,
            "detailed_validation_results": [asdict(check) for check in self.validation_results],
            "production_deployment_recommendations": self._generate_production_recommendations(),
            "risk_assessment": self._assess_deployment_risks(),
            "rollback_plan": self._generate_rollback_plan()
        }
    
    def _generate_production_recommendations(self) -> List[str]:
        """프로덕션 배포 권장사항"""
        recommendations = [
            "배포 전 전체 시스템 백업 실행",
            "Blue-Green 배포 전략으로 무중단 배포",
            "배포 후 즉시 헬스체크 및 모니터링 확인",
            "트래픽을 점진적으로 증가시키며 시스템 안정성 확인",
            "배포 후 24시간 집중 모니터링",
            "주요 비즈니스 기능 수동 테스트 실행",
            "성능 메트릭 실시간 모니터링",
            "에러율 및 응답시간 임계값 설정 및 알림 활성화"
        ]
        
        # 검증 결과에 따른 추가 권장사항
        failed_checks = [c for c in self.validation_results if c.status == "FAIL"]
        if failed_checks:
            recommendations.append("실패한 검증 항목들 해결 후 재검증 필수")
        
        warning_checks = [c for c in self.validation_results if c.status == "WARNING"]
        if warning_checks:
            recommendations.append("경고 항목들에 대한 리스크 평가 및 대응 계획 수립")
        
        return recommendations
    
    def _assess_deployment_risks(self) -> Dict[str, Any]:
        """배포 리스크 평가"""
        high_risks = []
        medium_risks = []
        low_risks = []
        
        # 실패한 검증 항목들은 높은 리스크
        for check in self.validation_results:
            if check.status == "FAIL":
                if check.category in ["security", "infrastructure"]:
                    high_risks.append(f"{check.name}: {check.details}")
                else:
                    medium_risks.append(f"{check.name}: {check.details}")
            elif check.status == "WARNING":
                if check.category == "security":
                    medium_risks.append(f"{check.name}: {check.details}")
                else:
                    low_risks.append(f"{check.name}: {check.details}")
        
        # 전체 리스크 레벨 결정
        if high_risks:
            risk_level = "HIGH"
        elif medium_risks:
            risk_level = "MEDIUM"
        elif low_risks:
            risk_level = "LOW"
        else:
            risk_level = "MINIMAL"
        
        return {
            "overall_risk_level": risk_level,
            "high_risks": high_risks,
            "medium_risks": medium_risks,
            "low_risks": low_risks,
            "mitigation_required": len(high_risks) > 0,
            "deployment_recommendation": {
                "HIGH": "배포 연기 권장 - 중요 문제 해결 필요",
                "MEDIUM": "신중한 배포 - 추가 검토 및 대응 계획 필요",
                "LOW": "배포 가능 - 사소한 개선사항 있음",
                "MINIMAL": "배포 승인 - 모든 검증 통과"
            }[risk_level]
        }
    
    def _generate_rollback_plan(self) -> Dict[str, Any]:
        """롤백 계획 생성"""
        return {
            "rollback_triggers": [
                "API 응답시간 > 2초 지속",
                "에러율 > 5% 지속",
                "시스템 다운타임 발생",
                "데이터베이스 연결 장애",
                "보안 취약점 발견",
                "사용자 접근 불가 상황"
            ],
            "rollback_steps": [
                "1. 트래픽을 이전 버전으로 즉시 전환",
                "2. 현재 버전 서비스 중지",
                "3. 데이터베이스 롤백 (필요시)",
                "4. 시스템 상태 확인 및 모니터링",
                "5. 사용자 공지 및 상황 보고",
                "6. 근본 원인 분석 및 수정 계획 수립"
            ],
            "rollback_time_estimate": "5-15분",
            "responsible_team": "DevOps Team",
            "communication_plan": [
                "즉시: 개발팀 및 운영팀 알림",
                "10분 이내: 관리자 및 이해관계자 보고",
                "30분 이내: 전체 상황 보고서 작성"
            ]
        }
    
    async def comprehensive_deployment_validation(self) -> Dict[str, Any]:
        """종합 배포 검증 실행"""
        logger.info("🚀 최종 프로덕션 배포 검증 시작")
        
        validation_start_time = datetime.now()
        
        # HTTP 세션 설정
        await self.setup_session()
        
        try:
            # 1. 인프라 준비도 검증
            logger.info("1️⃣ 인프라 준비도 검증 중...")
            infra_results = await self.validate_infrastructure_readiness()
            
            # 2. 애플리케이션 준비도 검증
            logger.info("2️⃣ 애플리케이션 준비도 검증 중...")
            app_results = await self.validate_application_readiness()
            
            # 3. 성능 준비도 검증
            logger.info("3️⃣ 성능 준비도 검증 중...")
            perf_results = await self.validate_performance_readiness()
            
            # 4. 보안 준비도 검증
            logger.info("4️⃣ 보안 준비도 검증 중...")
            security_results = await self.validate_security_readiness()
            
            # 5. 최종 배포 준비도 리포트 생성
            logger.info("5️⃣ 최종 리포트 생성 중...")
            final_report = await self.generate_deployment_readiness_report()
            
            # 검증 시간 추가
            validation_end_time = datetime.now()
            validation_duration = (validation_end_time - validation_start_time).total_seconds()
            
            comprehensive_report = {
                "validation_session": {
                    "start_time": validation_start_time.isoformat(),
                    "end_time": validation_end_time.isoformat(),
                    "duration_seconds": validation_duration,
                    "staging_url": self.staging_url
                },
                "validation_results_by_category": {
                    "infrastructure": infra_results,
                    "application": app_results,
                    "performance": perf_results,
                    "security": security_results
                },
                "final_assessment": final_report,
                "deployment_decision": self._make_deployment_decision(final_report)
            }
            
            logger.info("✅ 최종 프로덕션 배포 검증 완료")
            return comprehensive_report
            
        finally:
            await self.cleanup_session()
    
    def _make_deployment_decision(self, report: Dict[str, Any]) -> Dict[str, Any]:
        """배포 결정 생성"""
        validation_summary = report["validation_summary"]
        overall_status = validation_summary["overall_status"]
        overall_score = validation_summary["overall_score"]
        
        # 배포 결정 로직
        if overall_status == "READY" and overall_score >= 90:
            decision = "APPROVED"
            confidence = "HIGH"
            message = "모든 검증을 통과했습니다. 프로덕션 배포를 승인합니다."
        elif overall_status == "WARNING" and overall_score >= 80:
            decision = "CONDITIONAL_APPROVAL"
            confidence = "MEDIUM"
            message = "일부 경고사항이 있으나 배포 가능합니다. 배포 후 집중 모니터링이 필요합니다."
        elif overall_status == "WARNING" and overall_score >= 70:
            decision = "REVIEW_REQUIRED"
            confidence = "LOW"
            message = "중요한 검토가 필요합니다. 리스크를 평가한 후 배포 여부를 결정해주세요."
        else:
            decision = "REJECTED"
            confidence = "NONE"
            message = "중요한 문제들이 발견되었습니다. 문제 해결 후 재검증이 필요합니다."
        
        return {
            "decision": decision,
            "confidence_level": confidence,
            "decision_message": message,
            "recommended_action": {
                "APPROVED": "즉시 프로덕션 배포 진행",
                "CONDITIONAL_APPROVAL": "신중한 배포 및 집중 모니터링",
                "REVIEW_REQUIRED": "추가 검토 및 리스크 평가 후 결정",
                "REJECTED": "문제 해결 후 재검증"
            }[decision],
            "next_steps": report["production_deployment_recommendations"][:3],
            "approval_criteria_met": overall_score >= 85 and validation_summary["failed_checks"] == 0
        }

async def main():
    """메인 실행 함수"""
    # 환경 변수에서 설정 가져오기
    staging_url = os.getenv("STAGING_URL", "http://localhost:8000")
    database_url = os.getenv("MONGO_URL", "mongodb://admin:password123@localhost:27017/online_evaluation")
    
    validator = ProductionDeploymentValidator(staging_url, database_url)
    
    try:
        print("🚀 AI 모델 관리 시스템 - 최종 프로덕션 배포 검증")
        print(f"🎯 검증 대상: {staging_url}")
        print("=" * 60)
        
        # 종합 배포 검증 실행
        report = await validator.comprehensive_deployment_validation()
        
        # 리포트 저장
        report_file = f"/tmp/production_deployment_validation_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        print(f"\n📋 검증 리포트 저장: {report_file}")
        
        # 결과 요약 출력
        print("\n" + "="*60)
        print("🎯 최종 배포 검증 결과")
        print("="*60)
        
        session = report["validation_session"]
        print(f"🕐 검증 소요시간: {session['duration_seconds']:.1f}초")
        
        final_assessment = report["final_assessment"]
        validation_summary = final_assessment["validation_summary"]
        
        print(f"📊 총 검증 항목: {validation_summary['total_checks']}개")
        print(f"✅ 통과: {validation_summary['passed_checks']}개")
        print(f"❌ 실패: {validation_summary['failed_checks']}개")
        print(f"⚠️ 경고: {validation_summary['warning_checks']}개")
        print(f"🏆 전체 점수: {validation_summary['overall_score']}점")
        print(f"📈 전체 상태: {validation_summary['overall_status']}")
        
        # 카테고리별 결과
        print(f"\n📋 카테고리별 준비도:")
        for category, results in report["validation_results_by_category"].items():
            print(f"  {category.capitalize()}: {results['readiness_score']:.1f}점 ({results['status']})")
        
        # 배포 결정
        decision = report["deployment_decision"]
        print(f"\n🎯 배포 결정: {decision['decision']}")
        print(f"📝 결정 사유: {decision['decision_message']}")
        print(f"🔍 권장 조치: {decision['recommended_action']}")
        
        # 중요 이슈
        if validation_summary['failed_checks'] > 0:
            print(f"\n🚨 해결 필요한 중요 이슈:")
            failed_checks = [c for c in final_assessment['detailed_validation_results'] if c['status'] == 'FAIL']
            for i, check in enumerate(failed_checks[:5], 1):  # 상위 5개만 표시
                print(f"  {i}. {check['name']}: {check['details']}")
        
        # 리스크 평가
        risk_assessment = final_assessment["risk_assessment"]
        print(f"\n⚠️ 배포 리스크 레벨: {risk_assessment['overall_risk_level']}")
        print(f"💡 배포 권장사항: {risk_assessment['deployment_recommendation']}")
        
        print("\n🚀 최종 프로덕션 배포 검증 완료!")
        
        # 배포 승인 여부 반환
        return decision['approval_criteria_met']
        
    except Exception as e:
        print(f"\n❌ 검증 실행 실패: {e}")
        raise

if __name__ == "__main__":
    approval_result = asyncio.run(main())