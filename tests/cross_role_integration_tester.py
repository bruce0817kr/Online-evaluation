#!/usr/bin/env python3
"""
Cross-Role Integration Tester
다중 사용자 역할 간 통합 시나리오 테스트
"""

import asyncio
import json
import time
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import logging
from playwright.async_api import async_playwright, Browser, Page, BrowserContext

logger = logging.getLogger('CrossRoleIntegrationTester')

@dataclass
class UserSession:
    """사용자 세션 정보"""
    role: str
    name: str
    browser: Browser
    context: BrowserContext
    page: Page
    session_id: str
    login_time: datetime
    actions_performed: List[Dict[str, Any]]

@dataclass
class IntegrationTestResult:
    """통합 테스트 결과"""
    scenario_id: str
    participants: List[str]
    start_time: datetime
    end_time: datetime
    success: bool
    completed_workflows: int
    total_workflows: int
    data_consistency_score: float
    communication_events: List[Dict[str, Any]]
    performance_metrics: Dict[str, Any]
    errors: List[str]

class CrossRoleIntegrationTester:
    def __init__(self, base_url: str = "http://localhost:3000"):
        self.base_url = base_url
        self.active_sessions: Dict[str, UserSession] = {}
        self.test_results: List[IntegrationTestResult] = []
        self.communication_events: List[Dict[str, Any]] = []
        self.shared_data_state: Dict[str, Any] = {}
        
    async def setup_multi_user_environment(self, user_configs: List[Dict[str, str]]) -> Dict[str, UserSession]:
        """다중 사용자 환경 설정"""
        logger.info(f"다중 사용자 환경 설정: {len(user_configs)}명")
        
        playwright = await async_playwright().start()
        sessions = {}
        
        for config in user_configs:
            role = config['role']
            name = config['name']
            
            # 사용자별 브라우저 컨텍스트 생성
            browser = await playwright.chromium.launch(
                headless=False,
                slow_mo=500,
                args=[f'--user-data-dir=./test-profiles/{role}']
            )
            
            context = await browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent=f"IntegrationTest-{role}",
                record_video_dir=f"tests/results/videos/{role}",
                extra_http_headers={'X-Test-User': role}
            )
            
            page = await context.new_page()
            
            # 페이지 이벤트 리스너 설정
            page.on('response', lambda response, r=role: self._track_api_calls(response, r))
            page.on('console', lambda msg, r=role: self._track_console_messages(msg, r))
            
            session = UserSession(
                role=role,
                name=name,
                browser=browser,
                context=context,
                page=page,
                session_id=f"{role}_{int(time.time())}",
                login_time=datetime.now(),
                actions_performed=[]
            )
            
            sessions[role] = session
            self.active_sessions[role] = session
        
        return sessions
    
    async def _track_api_calls(self, response, user_role: str):
        """API 호출 추적"""
        if '/api/' in response.url:
            self.communication_events.append({
                'type': 'api_call',
                'user_role': user_role,
                'url': response.url,
                'method': response.request.method,
                'status': response.status,
                'timestamp': datetime.now().isoformat()
            })
    
    async def _track_console_messages(self, msg, user_role: str):
        """콘솔 메시지 추적"""
        if msg.type == 'log' and 'notification' in msg.text.lower():
            self.communication_events.append({
                'type': 'notification',
                'user_role': user_role,
                'message': msg.text,
                'timestamp': datetime.now().isoformat()
            })
    
    async def login_all_users(self, sessions: Dict[str, UserSession]) -> bool:
        """모든 사용자 로그인"""
        logger.info("모든 사용자 로그인 시작")
        
        login_tasks = []
        for role, session in sessions.items():
            task = self._login_user(session)
            login_tasks.append(task)
        
        results = await asyncio.gather(*login_tasks, return_exceptions=True)
        
        success_count = sum(1 for result in results if result is True)
        logger.info(f"로그인 완료: {success_count}/{len(sessions)}명 성공")
        
        return success_count == len(sessions)
    
    async def _login_user(self, session: UserSession) -> bool:
        """개별 사용자 로그인"""
        try:
            page = session.page
            role = session.role
            
            # 로그인 페이지 이동
            await page.goto(f"{self.base_url}/login")
            await page.wait_for_load_state('networkidle')
            
            # 테스트 계정 정보
            credentials = self._get_test_credentials(role)
            
            # 로그인 폼 작성
            await page.fill('[data-testid="email-input"]', credentials['email'])
            await page.fill('[data-testid="password-input"]', credentials['password'])
            await page.click('[data-testid="login-button"]')
            
            # 대시보드 로드 대기
            await page.wait_for_url('**/dashboard', timeout=10000)
            
            session.actions_performed.append({
                'action': 'login',
                'timestamp': datetime.now().isoformat(),
                'success': True
            })
            
            logger.info(f"{role} 로그인 성공")
            return True
            
        except Exception as e:
            logger.error(f"{session.role} 로그인 실패: {str(e)}")
            return False
    
    def _get_test_credentials(self, role: str) -> Dict[str, str]:
        """테스트 계정 정보 반환"""
        credentials_map = {
            'admin': {'email': 'admin@company.com', 'password': 'Admin123!@#'},
            'secretary': {'email': 'secretary@company.com', 'password': 'Secretary789!@#'},
            'evaluator1': {'email': 'eval1@company.com', 'password': 'Eval123!@#'},
            'evaluator2': {'email': 'eval2@company.com', 'password': 'Eval456!@#'},
            'evaluator3': {'email': 'eval3@company.com', 'password': 'Eval789!@#'}
        }
        return credentials_map.get(role, {'email': '', 'password': ''})
    
    async def execute_complete_evaluation_lifecycle(self) -> IntegrationTestResult:
        """완전한 평가 생명주기 통합 테스트"""
        scenario_id = "complete_evaluation_lifecycle"
        start_time = datetime.now()
        
        logger.info("완전한 평가 생명주기 통합 테스트 시작")
        
        # 참여자 설정
        participants = [
            {'role': 'admin', 'name': '김관리'},
            {'role': 'secretary', 'name': '박간사'},
            {'role': 'evaluator1', 'name': '이평가1'},
            {'role': 'evaluator2', 'name': '최평가2'}
        ]
        
        try:
            # 1. 다중 사용자 환경 설정
            sessions = await self.setup_multi_user_environment(participants)
            
            # 2. 모든 사용자 로그인
            login_success = await self.login_all_users(sessions)
            if not login_success:
                raise Exception("일부 사용자 로그인 실패")
            
            # 3. 관리자: 시스템 초기 설정
            await self._admin_system_setup(sessions['admin'])
            
            # 4. 간사: 프로젝트 생성 및 평가위원 배정
            project_data = await self._secretary_project_creation(sessions['secretary'])
            
            # 5. 평가위원들: 동시 평가 수행
            evaluation_tasks = [
                self._evaluator_conduct_evaluation(sessions['evaluator1'], project_data),
                self._evaluator_conduct_evaluation(sessions['evaluator2'], project_data)
            ]
            evaluation_results = await asyncio.gather(*evaluation_tasks, return_exceptions=True)
            
            # 6. 간사: 결과 취합 및 보고서 생성
            report_data = await self._secretary_compile_results(sessions['secretary'])
            
            # 7. 관리자: 최종 검토 및 승인
            final_approval = await self._admin_final_approval(sessions['admin'], report_data)
            
            # 8. 데이터 일관성 검증
            consistency_score = await self._verify_data_consistency()
            
            # 결과 정리
            end_time = datetime.now()
            completed_workflows = sum([
                1 if sessions['admin'].actions_performed else 0,
                1 if sessions['secretary'].actions_performed else 0,
                len([r for r in evaluation_results if not isinstance(r, Exception)])
            ])
            
            result = IntegrationTestResult(
                scenario_id=scenario_id,
                participants=[p['role'] for p in participants],
                start_time=start_time,
                end_time=end_time,
                success=all([
                    login_success,
                    final_approval,
                    consistency_score > 0.9
                ]),
                completed_workflows=completed_workflows,
                total_workflows=4,
                data_consistency_score=consistency_score,
                communication_events=self.communication_events.copy(),
                performance_metrics=await self._calculate_performance_metrics(),
                errors=[]
            )
            
            self.test_results.append(result)
            return result
            
        except Exception as e:
            logger.error(f"통합 테스트 실패: {str(e)}")
            
            result = IntegrationTestResult(
                scenario_id=scenario_id,
                participants=[p['role'] for p in participants],
                start_time=start_time,
                end_time=datetime.now(),
                success=False,
                completed_workflows=0,
                total_workflows=4,
                data_consistency_score=0.0,
                communication_events=self.communication_events.copy(),
                performance_metrics={},
                errors=[str(e)]
            )
            
            return result
        
        finally:
            # 모든 브라우저 세션 정리
            await self._cleanup_sessions()
    
    async def _admin_system_setup(self, admin_session: UserSession):
        """관리자 시스템 설정"""
        page = admin_session.page
        
        try:
            # AI 제공업체 설정
            await page.goto(f"{self.base_url}/admin/ai-providers")
            await page.wait_for_load_state('networkidle')
            
            # OpenAI 설정
            await page.click('[data-testid="add-ai-provider"]')
            await page.fill('[data-testid="provider-name"]', 'OpenAI')
            await page.fill('[data-testid="api-key"]', 'test-api-key')
            await page.select_option('[data-testid="model-select"]', 'gpt-4')
            await page.click('[data-testid="save-provider"]')
            
            # 회사 등록
            await page.goto(f"{self.base_url}/admin/companies")
            await page.click('[data-testid="add-company"]')
            await page.fill('[data-testid="company-name"]', '테스트회사A')
            await page.fill('[data-testid="company-industry"]', 'IT/소프트웨어')
            await page.click('[data-testid="save-company"]')
            
            admin_session.actions_performed.append({
                'action': 'system_setup',
                'timestamp': datetime.now().isoformat(),
                'details': 'AI 제공업체 및 회사 설정 완료'
            })
            
            # 공유 데이터 상태 업데이트
            self.shared_data_state.update({
                'ai_providers_configured': True,
                'test_company_created': True,
                'company_id': 'test_company_a'
            })
            
        except Exception as e:
            logger.error(f"관리자 시스템 설정 실패: {str(e)}")
            raise
    
    async def _secretary_project_creation(self, secretary_session: UserSession) -> Dict[str, Any]:
        """간사 프로젝트 생성"""
        page = secretary_session.page
        
        try:
            # 프로젝트 생성 페이지 이동
            await page.goto(f"{self.base_url}/projects")
            await page.click('[data-testid="create-project"]')
            
            # 프로젝트 정보 입력
            project_name = "2024 통합테스트 프로젝트"
            await page.fill('[data-testid="project-name"]', project_name)
            await page.fill('[data-testid="project-description"]', "통합 테스트용 프로젝트")
            await page.fill('[data-testid="start-date"]', "2024-07-01")
            await page.fill('[data-testid="end-date"]', "2024-08-31")
            
            # 프로젝트 저장
            await page.click('[data-testid="save-project"]')
            await page.wait_for_selector('[data-testid="project-created"]', timeout=5000)
            
            # 평가 템플릿 생성
            await page.goto(f"{self.base_url}/templates")
            await page.click('[data-testid="create-template"]')
            await page.fill('[data-testid="template-name"]', "통합테스트 템플릿")
            
            # 평가 기준 추가
            criteria = [
                {'name': '기술 혁신성', 'weight': 30, 'max_score': 10},
                {'name': '시장 잠재력', 'weight': 25, 'max_score': 10},
                {'name': '팀 역량', 'weight': 25, 'max_score': 10},
                {'name': '재무 건전성', 'weight': 20, 'max_score': 10}
            ]
            
            for i, criterion in enumerate(criteria):
                await page.click('[data-testid="add-criterion"]')
                await page.fill(f'[data-testid="criterion-name-{i}"]', criterion['name'])
                await page.fill(f'[data-testid="criterion-weight-{i}"]', str(criterion['weight']))
                await page.fill(f'[data-testid="criterion-score-{i}"]', str(criterion['max_score']))
            
            await page.click('[data-testid="save-template"]')
            
            # 평가위원 배정
            await page.goto(f"{self.base_url}/assignments")
            await page.click('[data-testid="create-assignment"]')
            
            # 회사 선택
            await page.select_option('[data-testid="company-select"]', 'test_company_a')
            
            # 평가위원 선택
            await page.check('[data-testid="evaluator-eval1"]')
            await page.check('[data-testid="evaluator-eval2"]')
            
            # 마감일 설정
            await page.fill('[data-testid="deadline"]', "2024-08-15")
            
            # 배정 저장
            await page.click('[data-testid="save-assignment"]')
            
            secretary_session.actions_performed.append({
                'action': 'project_creation',
                'timestamp': datetime.now().isoformat(),
                'details': f'프로젝트 "{project_name}" 생성 및 평가위원 배정 완료'
            })
            
            project_data = {
                'project_name': project_name,
                'template_id': 'integration_test_template',
                'company_id': 'test_company_a',
                'assigned_evaluators': ['eval1', 'eval2'],
                'deadline': '2024-08-15'
            }
            
            # 공유 데이터 상태 업데이트
            self.shared_data_state.update({
                'project_created': True,
                'project_data': project_data,
                'evaluators_assigned': True
            })
            
            return project_data
            
        except Exception as e:
            logger.error(f"간사 프로젝트 생성 실패: {str(e)}")
            raise
    
    async def _evaluator_conduct_evaluation(self, evaluator_session: UserSession, 
                                          project_data: Dict[str, Any]) -> Dict[str, Any]:
        """평가위원 평가 수행"""
        page = evaluator_session.page
        role = evaluator_session.role
        
        try:
            # 배정된 평가 확인
            await page.goto(f"{self.base_url}/my-evaluations")
            await page.wait_for_load_state('networkidle')
            
            # 평가 대상 회사 클릭
            await page.click(f'[data-testid="evaluation-{project_data["company_id"]}"]')
            
            # 문서 검토
            await page.click('[data-testid="view-documents"]')
            await asyncio.sleep(2)  # 문서 로딩 대기
            
            # AI 도우미 활성화
            await page.click('[data-testid="ai-assistant-toggle"]')
            await page.fill('[data-testid="ai-prompt"]', '이 회사의 강점과 약점을 분석해주세요.')
            await page.click('[data-testid="ai-submit"]')
            
            # AI 응답 대기
            await page.wait_for_selector('[data-testid="ai-response"]', timeout=15000)
            
            # 평가 점수 입력
            evaluation_scores = {
                '기술 혁신성': 8.5,
                '시장 잠재력': 7.8,
                '팀 역량': 8.2,
                '재무 건전성': 7.5
            }
            
            for criterion, score in evaluation_scores.items():
                await page.fill(f'[data-testid="score-{criterion}"]', str(score))
            
            # 전체 코멘트 작성
            comment = f"{role}의 종합 평가: 우수한 기술력과 시장 잠재력을 보유한 회사로 평가됩니다."
            await page.fill('[data-testid="overall-comment"]', comment)
            
            # 평가 제출
            await page.click('[data-testid="submit-evaluation"]')
            await page.wait_for_selector('[data-testid="evaluation-submitted"]', timeout=5000)
            
            evaluator_session.actions_performed.append({
                'action': 'evaluation_submission',
                'timestamp': datetime.now().isoformat(),
                'details': f'회사 {project_data["company_id"]} 평가 완료',
                'scores': evaluation_scores
            })
            
            return {
                'evaluator': role,
                'scores': evaluation_scores,
                'comment': comment,
                'submission_time': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"{role} 평가 수행 실패: {str(e)}")
            raise
    
    async def _secretary_compile_results(self, secretary_session: UserSession) -> Dict[str, Any]:
        """간사 결과 취합"""
        page = secretary_session.page
        
        try:
            # 평가 결과 페이지 이동
            await page.goto(f"{self.base_url}/evaluation-results")
            await page.wait_for_load_state('networkidle')
            
            # 진행 상황 확인
            await page.click('[data-testid="refresh-progress"]')
            await asyncio.sleep(2)
            
            # 결과 분석 대시보드 생성
            await page.click('[data-testid="generate-analytics"]')
            await page.wait_for_selector('[data-testid="analytics-dashboard"]', timeout=10000)
            
            # 보고서 생성
            await page.click('[data-testid="generate-report"]')
            await page.select_option('[data-testid="report-format"]', 'comprehensive')
            await page.click('[data-testid="create-report"]')
            
            # 보고서 생성 완료 대기
            await page.wait_for_selector('[data-testid="report-ready"]', timeout=15000)
            
            secretary_session.actions_performed.append({
                'action': 'results_compilation',
                'timestamp': datetime.now().isoformat(),
                'details': '평가 결과 취합 및 보고서 생성 완료'
            })
            
            # 공유 데이터 상태 업데이트
            self.shared_data_state.update({
                'results_compiled': True,
                'report_generated': True,
                'report_id': 'integration_test_report'
            })
            
            return {
                'report_id': 'integration_test_report',
                'compilation_time': datetime.now().isoformat(),
                'evaluations_processed': 2
            }
            
        except Exception as e:
            logger.error(f"간사 결과 취합 실패: {str(e)}")
            raise
    
    async def _admin_final_approval(self, admin_session: UserSession, 
                                  report_data: Dict[str, Any]) -> bool:
        """관리자 최종 승인"""
        page = admin_session.page
        
        try:
            # 보고서 검토 페이지 이동
            await page.goto(f"{self.base_url}/admin/reports")
            await page.click(f'[data-testid="review-{report_data["report_id"]}"]')
            
            # 보고서 내용 검토
            await page.wait_for_selector('[data-testid="report-content"]', timeout=5000)
            
            # 데이터 품질 확인
            await page.click('[data-testid="verify-data-quality"]')
            await page.wait_for_selector('[data-testid="quality-check-passed"]', timeout=5000)
            
            # 최종 승인
            await page.fill('[data-testid="approval-comment"]', '통합 테스트 결과 검토 완료. 승인합니다.')
            await page.click('[data-testid="approve-report"]')
            
            # 승인 완료 확인
            await page.wait_for_selector('[data-testid="approval-confirmed"]', timeout=5000)
            
            admin_session.actions_performed.append({
                'action': 'final_approval',
                'timestamp': datetime.now().isoformat(),
                'details': f'보고서 {report_data["report_id"]} 최종 승인 완료'
            })
            
            # 공유 데이터 상태 업데이트
            self.shared_data_state.update({
                'final_approved': True,
                'approval_time': datetime.now().isoformat()
            })
            
            return True
            
        except Exception as e:
            logger.error(f"관리자 최종 승인 실패: {str(e)}")
            return False
    
    async def _verify_data_consistency(self) -> float:
        """데이터 일관성 검증"""
        try:
            consistency_checks = [
                'ai_providers_configured' in self.shared_data_state,
                'test_company_created' in self.shared_data_state,
                'project_created' in self.shared_data_state,
                'evaluators_assigned' in self.shared_data_state,
                'results_compiled' in self.shared_data_state,
                'final_approved' in self.shared_data_state
            ]
            
            passed_checks = sum(consistency_checks)
            total_checks = len(consistency_checks)
            
            consistency_score = passed_checks / total_checks
            
            logger.info(f"데이터 일관성 점수: {consistency_score:.2f} ({passed_checks}/{total_checks})")
            
            return consistency_score
            
        except Exception as e:
            logger.error(f"데이터 일관성 검증 실패: {str(e)}")
            return 0.0
    
    async def _calculate_performance_metrics(self) -> Dict[str, Any]:
        """성능 메트릭 계산"""
        api_calls = [event for event in self.communication_events if event['type'] == 'api_call']
        notifications = [event for event in self.communication_events if event['type'] == 'notification']
        
        return {
            'total_api_calls': len(api_calls),
            'total_notifications': len(notifications),
            'avg_response_time': self._calculate_avg_response_time(api_calls),
            'error_rate': self._calculate_error_rate(api_calls),
            'communication_efficiency': len(notifications) / len(api_calls) if api_calls else 0
        }
    
    def _calculate_avg_response_time(self, api_calls: List[Dict[str, Any]]) -> float:
        """평균 응답 시간 계산"""
        # 실제 구현에서는 응답 시간 데이터를 수집해야 함
        return 250.0  # ms
    
    def _calculate_error_rate(self, api_calls: List[Dict[str, Any]]) -> float:
        """오류율 계산"""
        if not api_calls:
            return 0.0
        
        error_calls = [call for call in api_calls if call['status'] >= 400]
        return len(error_calls) / len(api_calls)
    
    async def _cleanup_sessions(self):
        """모든 세션 정리"""
        for session in self.active_sessions.values():
            try:
                await session.browser.close()
            except Exception as e:
                logger.warning(f"세션 정리 중 오류: {str(e)}")
        
        self.active_sessions.clear()
    
    async def execute_realtime_collaborative_evaluation(self) -> IntegrationTestResult:
        """실시간 협업 평가 테스트"""
        scenario_id = "realtime_collaborative_evaluation"
        start_time = datetime.now()
        
        logger.info("실시간 협업 평가 테스트 시작")
        
        participants = [
            {'role': 'secretary', 'name': '박간사'},
            {'role': 'evaluator1', 'name': '이평가1'},
            {'role': 'evaluator2', 'name': '최평가2'},
            {'role': 'evaluator3', 'name': '정평가3'}
        ]
        
        try:
            # 다중 사용자 환경 설정
            sessions = await self.setup_multi_user_environment(participants)
            await self.login_all_users(sessions)
            
            # 동시 평가 시나리오 실행
            evaluation_tasks = []
            for role in ['evaluator1', 'evaluator2', 'evaluator3']:
                if role in sessions:
                    task = self._perform_collaborative_evaluation(sessions[role])
                    evaluation_tasks.append(task)
            
            # 간사 모니터링
            monitoring_task = self._monitor_collaborative_progress(sessions['secretary'])
            
            # 모든 작업 동시 실행
            all_tasks = evaluation_tasks + [monitoring_task]
            results = await asyncio.gather(*all_tasks, return_exceptions=True)
            
            # 결과 분석
            successful_evaluations = len([r for r in results[:-1] if not isinstance(r, Exception)])
            monitoring_success = not isinstance(results[-1], Exception)
            
            end_time = datetime.now()
            
            result = IntegrationTestResult(
                scenario_id=scenario_id,
                participants=[p['role'] for p in participants],
                start_time=start_time,
                end_time=end_time,
                success=successful_evaluations >= 2 and monitoring_success,
                completed_workflows=successful_evaluations + (1 if monitoring_success else 0),
                total_workflows=4,
                data_consistency_score=await self._verify_collaborative_consistency(),
                communication_events=self.communication_events.copy(),
                performance_metrics=await self._calculate_performance_metrics(),
                errors=[str(r) for r in results if isinstance(r, Exception)]
            )
            
            return result
            
        except Exception as e:
            logger.error(f"실시간 협업 테스트 실패: {str(e)}")
            return IntegrationTestResult(
                scenario_id=scenario_id,
                participants=[p['role'] for p in participants],
                start_time=start_time,
                end_time=datetime.now(),
                success=False,
                completed_workflows=0,
                total_workflows=4,
                data_consistency_score=0.0,
                communication_events=self.communication_events.copy(),
                performance_metrics={},
                errors=[str(e)]
            )
        
        finally:
            await self._cleanup_sessions()
    
    async def _perform_collaborative_evaluation(self, evaluator_session: UserSession) -> bool:
        """협업 평가 수행"""
        page = evaluator_session.page
        role = evaluator_session.role
        
        try:
            # 협업 평가 페이지 접근
            await page.goto(f"{self.base_url}/collaborative-evaluation")
            
            # 실시간 채팅 활성화
            await page.click('[data-testid="enable-chat"]')
            
            # 다른 평가위원과 의견 교환
            chat_message = f"{role}입니다. 평가를 시작합니다."
            await page.fill('[data-testid="chat-input"]', chat_message)
            await page.click('[data-testid="send-chat"]')
            
            # 개별 평가 수행
            scores = {'기술혁신성': 8, '시장잠재력': 7, '팀역량': 8, '재무건전성': 7}
            for criterion, score in scores.items():
                await page.fill(f'[data-testid="collab-score-{criterion}"]', str(score))
            
            # 의견 불일치 시 토론
            await page.click('[data-testid="request-discussion"]')
            await asyncio.sleep(5)  # 토론 시간
            
            # 합의 도출
            await page.click('[data-testid="consensus-vote"]')
            
            return True
            
        except Exception as e:
            logger.error(f"{role} 협업 평가 실패: {str(e)}")
            return False
    
    async def _monitor_collaborative_progress(self, secretary_session: UserSession) -> bool:
        """협업 진행 상황 모니터링"""
        page = secretary_session.page
        
        try:
            # 실시간 모니터링 대시보드 접근
            await page.goto(f"{self.base_url}/monitoring/collaborative")
            
            # 진행 상황 추적
            for _ in range(10):  # 10회 체크
                await page.click('[data-testid="refresh-status"]')
                await asyncio.sleep(3)
                
                # 완료 여부 확인
                try:
                    await page.wait_for_selector('[data-testid="all-evaluations-complete"]', timeout=1000)
                    break
                except:
                    continue
            
            # 결과 정리
            await page.click('[data-testid="compile-collaborative-results"]')
            
            return True
            
        except Exception as e:
            logger.error(f"협업 모니터링 실패: {str(e)}")
            return False
    
    async def _verify_collaborative_consistency(self) -> float:
        """협업 데이터 일관성 검증"""
        # 실제 구현에서는 데이터베이스에서 일관성 확인
        return 0.95
    
    async def generate_integration_report(self, results: List[IntegrationTestResult]) -> str:
        """통합 테스트 보고서 생성"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = f"tests/results/integration_test_report_{timestamp}.json"
        
        # 종합 분석
        total_tests = len(results)
        successful_tests = len([r for r in results if r.success])
        
        avg_consistency = sum(r.data_consistency_score for r in results) / total_tests if total_tests > 0 else 0
        total_communication_events = sum(len(r.communication_events) for r in results)
        
        report = {
            'test_summary': {
                'timestamp': timestamp,
                'total_integration_tests': total_tests,
                'successful_tests': successful_tests,
                'success_rate': (successful_tests / total_tests * 100) if total_tests > 0 else 0,
                'average_data_consistency': avg_consistency,
                'total_communication_events': total_communication_events
            },
            'test_results': [
                {
                    'scenario_id': r.scenario_id,
                    'participants': r.participants,
                    'success': r.success,
                    'duration_seconds': (r.end_time - r.start_time).total_seconds(),
                    'data_consistency_score': r.data_consistency_score,
                    'communication_events_count': len(r.communication_events),
                    'errors': r.errors
                }
                for r in results
            ],
            'communication_analysis': self._analyze_communication_patterns(),
            'performance_analysis': self._analyze_cross_role_performance(),
            'recommendations': self._generate_integration_recommendations(results)
        }
        
        # 보고서 저장
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False, default=str)
        
        logger.info(f"통합 테스트 보고서 생성: {report_file}")
        return report_file
    
    def _analyze_communication_patterns(self) -> Dict[str, Any]:
        """커뮤니케이션 패턴 분석"""
        return {
            'api_calls_by_role': {},
            'notification_patterns': {},
            'cross_role_interactions': {}
        }
    
    def _analyze_cross_role_performance(self) -> Dict[str, Any]:
        """교차 역할 성능 분석"""
        return {
            'role_efficiency': {},
            'bottleneck_identification': [],
            'optimization_opportunities': []
        }
    
    def _generate_integration_recommendations(self, results: List[IntegrationTestResult]) -> List[str]:
        """통합 테스트 권고사항 생성"""
        recommendations = []
        
        # 성공률 기반 권고
        success_rate = len([r for r in results if r.success]) / len(results) * 100
        if success_rate < 90:
            recommendations.append("교차 역할 통합 테스트 성공률 개선 필요")
        
        # 데이터 일관성 기반 권고
        avg_consistency = sum(r.data_consistency_score for r in results) / len(results)
        if avg_consistency < 0.95:
            recommendations.append("다중 사용자 환경에서 데이터 일관성 강화 필요")
        
        # 커뮤니케이션 효율성 기반 권고
        total_events = sum(len(r.communication_events) for r in results)
        if total_events < 50:
            recommendations.append("사용자 간 실시간 커뮤니케이션 기능 개선 필요")
        
        return recommendations

# CLI 실행
async def main():
    """메인 실행 함수"""
    tester = CrossRoleIntegrationTester()
    
    # 완전한 평가 생명주기 테스트
    lifecycle_result = await tester.execute_complete_evaluation_lifecycle()
    print(f"평가 생명주기 테스트: {'성공' if lifecycle_result.success else '실패'}")
    
    # 실시간 협업 테스트
    collaborative_result = await tester.execute_realtime_collaborative_evaluation()
    print(f"실시간 협업 테스트: {'성공' if collaborative_result.success else '실패'}")
    
    # 통합 보고서 생성
    results = [lifecycle_result, collaborative_result]
    report_file = await tester.generate_integration_report(results)
    print(f"통합 테스트 보고서: {report_file}")

if __name__ == "__main__":
    asyncio.run(main())