#!/usr/bin/env python3
"""
MCP-Powered Scenario Test Runner
사용자별 시나리오 기반 테스트 실행 및 추적 시스템
"""

import json
import yaml
import time
import asyncio
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from playwright.async_api import async_playwright, Page, Browser
import aiofiles

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('scenario_test_runner.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('ScenarioRunner')

@dataclass
class ScenarioStep:
    """시나리오 단계 정의"""
    action: str
    description: str
    data: Dict[str, Any]
    expected: str
    timeout: int = 30
    retry_count: int = 3
    
@dataclass
class ScenarioResult:
    """시나리오 실행 결과"""
    scenario_id: str
    user_role: str
    status: str  # success, failed, partial
    execution_time: float
    steps_completed: int
    total_steps: int
    errors: List[str]
    screenshots: List[str]
    performance_metrics: Dict[str, Any]
    
@dataclass
class UserJourney:
    """사용자 여정 추적"""
    user_role: str
    session_id: str
    start_time: datetime
    end_time: Optional[datetime]
    actions: List[Dict[str, Any]]
    page_views: List[str]
    interactions: List[Dict[str, Any]]
    errors_encountered: List[str]

class MCPScenarioRunner:
    def __init__(self, config_path: str = "tests/scenarios"):
        self.config_path = Path(config_path)
        self.test_data_path = Path("tests/scenario-data")
        self.results_path = Path("tests/results")
        self.results_path.mkdir(exist_ok=True)
        
        self.scenarios = {}
        self.test_data = {}
        self.user_journeys = {}
        self.active_sessions = {}
        
        # 성능 메트릭 수집
        self.performance_metrics = {
            'page_load_times': [],
            'api_response_times': [],
            'user_action_times': [],
            'error_rates': []
        }
        
        self.load_configurations()
    
    def load_configurations(self):
        """시나리오 및 테스트 데이터 로드"""
        logger.info("시나리오 설정 파일 로드 중...")
        
        # 시나리오 파일 로드
        scenario_files = [
            'admin-scenarios.yml',
            'secretary-scenarios.yml', 
            'evaluator-scenarios.yml',
            'cross-role-scenarios.yml'
        ]
        
        for file_name in scenario_files:
            file_path = self.config_path / file_name
            if file_path.exists():
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = yaml.safe_load(f)
                    role = file_name.split('-')[0]
                    self.scenarios[role] = data
        
        # 테스트 데이터 로드
        test_data_files = [
            'test-accounts.json',
            'sample-companies.json',
            'evaluation-templates.json'
        ]
        
        for file_name in test_data_files:
            file_path = self.test_data_path / file_name
            if file_path.exists():
                with open(file_path, 'r', encoding='utf-8') as f:
                    data_key = file_name.split('.')[0].replace('-', '_')
                    self.test_data[data_key] = json.load(f)
        
        logger.info(f"로드된 시나리오: {list(self.scenarios.keys())}")
        logger.info(f"로드된 테스트 데이터: {list(self.test_data.keys())}")
    
    async def create_browser_context(self, user_role: str) -> tuple[Browser, Page]:
        """사용자 역할별 브라우저 컨텍스트 생성"""
        playwright = await async_playwright().start()
        
        # 브라우저 설정
        browser = await playwright.chromium.launch(
            headless=False,  # 시나리오 실행 시각화
            slow_mo=1000,   # 액션 간 지연
            args=['--start-maximized']
        )
        
        # 사용자별 컨텍스트 설정
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent=f"ScenarioRunner-{user_role}",
            record_video_dir=f"tests/results/videos/{user_role}",
            record_video_size={'width': 1920, 'height': 1080}
        )
        
        # 페이지 생성 및 이벤트 리스너 설정
        page = await context.new_page()
        
        # 성능 메트릭 수집을 위한 리스너
        page.on('response', self._track_api_response)
        page.on('console', self._track_console_logs)
        page.on('pageerror', self._track_page_errors)
        
        return browser, page
    
    async def _track_api_response(self, response):
        """API 응답 시간 추적"""
        if '/api/' in response.url:
            request_time = response.request.timing
            if request_time:
                response_time = request_time['responseEnd'] - request_time['requestStart']
                self.performance_metrics['api_response_times'].append({
                    'url': response.url,
                    'time': response_time,
                    'status': response.status,
                    'timestamp': datetime.now().isoformat()
                })
    
    async def _track_console_logs(self, msg):
        """콘솔 로그 추적"""
        if msg.type == 'error':
            logger.warning(f"브라우저 콘솔 오류: {msg.text}")
    
    async def _track_page_errors(self, error):
        """페이지 오류 추적"""
        logger.error(f"페이지 오류: {error}")
        self.performance_metrics['error_rates'].append({
            'error': str(error),
            'timestamp': datetime.now().isoformat()
        })
    
    async def execute_scenario(self, scenario_id: str, user_role: str) -> ScenarioResult:
        """시나리오 실행"""
        logger.info(f"시나리오 실행 시작: {scenario_id} ({user_role})")
        
        start_time = time.time()
        browser, page = await self.create_browser_context(user_role)
        
        try:
            scenario = self._get_scenario(scenario_id, user_role)
            if not scenario:
                raise ValueError(f"시나리오를 찾을 수 없음: {scenario_id}")
            
            # 사용자 여정 추적 시작
            session_id = f"{user_role}_{scenario_id}_{int(time.time())}"
            journey = self._start_user_journey(user_role, session_id)
            
            # 시나리오 단계별 실행
            steps_completed = 0
            total_steps = len(scenario.get('steps', []))
            errors = []
            screenshots = []
            
            for step_index, step_data in enumerate(scenario.get('steps', [])):
                try:
                    step_result = await self._execute_step(
                        page, step_data, user_role, journey
                    )
                    
                    if step_result['success']:
                        steps_completed += 1
                        logger.info(f"단계 {step_index + 1} 완료: {step_data['action']}")
                    else:
                        errors.append(f"단계 {step_index + 1} 실패: {step_result['error']}")
                        logger.error(f"단계 {step_index + 1} 실패: {step_result['error']}")
                    
                    # 스크린샷 캡처
                    screenshot_path = await self._capture_screenshot(
                        page, f"{scenario_id}_step_{step_index + 1}"
                    )
                    screenshots.append(screenshot_path)
                    
                except Exception as e:
                    errors.append(f"단계 {step_index + 1} 오류: {str(e)}")
                    logger.error(f"단계 실행 오류: {str(e)}")
                    break
            
            # 실행 결과 정리
            execution_time = time.time() - start_time
            status = self._determine_scenario_status(steps_completed, total_steps, errors)
            
            result = ScenarioResult(
                scenario_id=scenario_id,
                user_role=user_role,
                status=status,
                execution_time=execution_time,
                steps_completed=steps_completed,
                total_steps=total_steps,
                errors=errors,
                screenshots=screenshots,
                performance_metrics=self._get_current_performance_metrics()
            )
            
            # 사용자 여정 완료
            self._complete_user_journey(session_id)
            
            logger.info(f"시나리오 실행 완료: {scenario_id} - {status}")
            return result
            
        finally:
            await browser.close()
    
    def _get_scenario(self, scenario_id: str, user_role: str) -> Dict[str, Any]:
        """시나리오 데이터 조회"""
        if user_role in self.scenarios:
            for scenario in self.scenarios[user_role].get('scenarios', []):
                if scenario.get('id') == scenario_id:
                    return scenario
        
        # 교차 역할 시나리오 확인
        if 'cross' in self.scenarios:
            for scenario in self.scenarios['cross'].get('integration_scenarios', []):
                if scenario.get('id') == scenario_id:
                    return scenario
        
        return None
    
    def _start_user_journey(self, user_role: str, session_id: str) -> UserJourney:
        """사용자 여정 추적 시작"""
        journey = UserJourney(
            user_role=user_role,
            session_id=session_id,
            start_time=datetime.now(),
            end_time=None,
            actions=[],
            page_views=[],
            interactions=[],
            errors_encountered=[]
        )
        
        self.user_journeys[session_id] = journey
        return journey
    
    async def _execute_step(self, page: Page, step_data: Dict[str, Any], 
                          user_role: str, journey: UserJourney) -> Dict[str, Any]:
        """시나리오 단계 실행"""
        action = step_data['action']
        description = step_data['description']
        data = step_data.get('data', {})
        expected = step_data['expected']
        
        # 액션 추적
        journey.actions.append({
            'action': action,
            'description': description,
            'timestamp': datetime.now().isoformat(),
            'data': data
        })
        
        try:
            if action == 'login':
                return await self._handle_login(page, data, user_role)
            elif action == 'navigate_to':
                return await self._handle_navigation(page, data)
            elif action == 'create_project':
                return await self._handle_create_project(page, data)
            elif action == 'assign_evaluators':
                return await self._handle_assign_evaluators(page, data)
            elif action == 'conduct_evaluation':
                return await self._handle_conduct_evaluation(page, data)
            elif action == 'ai_assistant_interaction':
                return await self._handle_ai_interaction(page, data)
            elif action == 'generate_report':
                return await self._handle_generate_report(page, data)
            else:
                return await self._handle_generic_action(page, action, data)
                
        except Exception as e:
            journey.errors_encountered.append(str(e))
            return {'success': False, 'error': str(e)}
    
    async def _handle_login(self, page: Page, data: Dict[str, Any], 
                          user_role: str) -> Dict[str, Any]:
        """로그인 처리"""
        try:
            # 테스트 계정 정보 가져오기
            account_info = self._get_test_account(user_role)
            if not account_info:
                return {'success': False, 'error': '테스트 계정 정보를 찾을 수 없음'}
            
            # 로그인 페이지 이동
            await page.goto('http://localhost:3000/login')
            await page.wait_for_load_state('networkidle')
            
            # 로그인 폼 작성
            await page.fill('[data-testid="email-input"]', account_info['email'])
            await page.fill('[data-testid="password-input"]', account_info['password'])
            
            # 로그인 버튼 클릭
            await page.click('[data-testid="login-button"]')
            
            # 대시보드 로드 대기
            await page.wait_for_url('**/dashboard', timeout=10000)
            
            return {'success': True, 'message': '로그인 성공'}
            
        except Exception as e:
            return {'success': False, 'error': f'로그인 실패: {str(e)}'}
    
    async def _handle_navigation(self, page: Page, data: Dict[str, Any]) -> Dict[str, Any]:
        """페이지 네비게이션 처리"""
        try:
            url = data.get('url')
            menu_item = data.get('menu_item')
            
            if url:
                await page.goto(url)
            elif menu_item:
                await page.click(f'[data-testid="menu-{menu_item}"]')
            
            await page.wait_for_load_state('networkidle')
            return {'success': True, 'message': '네비게이션 성공'}
            
        except Exception as e:
            return {'success': False, 'error': f'네비게이션 실패: {str(e)}'}
    
    async def _handle_create_project(self, page: Page, data: Dict[str, Any]) -> Dict[str, Any]:
        """프로젝트 생성 처리"""
        try:
            # 프로젝트 생성 페이지 이동
            await page.click('[data-testid="create-project-button"]')
            
            # 프로젝트 정보 입력
            await page.fill('[data-testid="project-name"]', data['name'])
            await page.fill('[data-testid="project-description"]', data['description'])
            
            # 시작일/종료일 설정
            if 'start_date' in data:
                await page.fill('[data-testid="start-date"]', data['start_date'])
            if 'end_date' in data:
                await page.fill('[data-testid="end-date"]', data['end_date'])
            
            # 저장 버튼 클릭
            await page.click('[data-testid="save-project-button"]')
            
            # 성공 메시지 확인
            await page.wait_for_selector('[data-testid="success-message"]', timeout=5000)
            
            return {'success': True, 'message': '프로젝트 생성 성공'}
            
        except Exception as e:
            return {'success': False, 'error': f'프로젝트 생성 실패: {str(e)}'}
    
    async def _handle_conduct_evaluation(self, page: Page, data: Dict[str, Any]) -> Dict[str, Any]:
        """평가 수행 처리"""
        try:
            company_name = data['company_name']
            evaluation_data = data['evaluation_data']
            
            # 평가 대상 회사 선택
            await page.click(f'[data-testid="company-{company_name}"]')
            
            # 평가 항목별 점수 입력
            for section, criteria_list in evaluation_data.items():
                for criteria, score in criteria_list.items():
                    await page.fill(f'[data-testid="score-{criteria}"]', str(score))
            
            # 전체 코멘트 입력
            if 'overall_comment' in data:
                await page.fill('[data-testid="overall-comment"]', data['overall_comment'])
            
            # 평가 제출
            await page.click('[data-testid="submit-evaluation"]')
            
            # 제출 확인 대기
            await page.wait_for_selector('[data-testid="evaluation-submitted"]', timeout=10000)
            
            return {'success': True, 'message': '평가 제출 성공'}
            
        except Exception as e:
            return {'success': False, 'error': f'평가 수행 실패: {str(e)}'}
    
    async def _handle_ai_interaction(self, page: Page, data: Dict[str, Any]) -> Dict[str, Any]:
        """AI 도우미 상호작용 처리"""
        try:
            # AI 도우미 활성화
            await page.click('[data-testid="ai-assistant-toggle"]')
            
            # AI 프롬프트 입력
            prompt = data.get('prompt', '이 회사를 어떻게 평가해야 할까요?')
            await page.fill('[data-testid="ai-prompt-input"]', prompt)
            
            # AI 응답 요청
            await page.click('[data-testid="ai-submit-button"]')
            
            # AI 응답 대기
            await page.wait_for_selector('[data-testid="ai-response"]', timeout=15000)
            
            # 응답 내용 확인
            response = await page.text_content('[data-testid="ai-response"]')
            
            return {
                'success': True, 
                'message': 'AI 상호작용 성공',
                'ai_response': response
            }
            
        except Exception as e:
            return {'success': False, 'error': f'AI 상호작용 실패: {str(e)}'}
    
    async def _handle_generic_action(self, page: Page, action: str, 
                                   data: Dict[str, Any]) -> Dict[str, Any]:
        """일반적인 액션 처리"""
        try:
            # 기본적인 액션 패턴 처리
            if 'click' in action:
                selector = data.get('selector', f'[data-testid="{action}"]')
                await page.click(selector)
            elif 'fill' in action:
                selector = data.get('selector')
                value = data.get('value')
                await page.fill(selector, value)
            elif 'wait' in action:
                selector = data.get('selector')
                timeout = data.get('timeout', 5000)
                await page.wait_for_selector(selector, timeout=timeout)
            
            return {'success': True, 'message': f'{action} 실행 성공'}
            
        except Exception as e:
            return {'success': False, 'error': f'{action} 실행 실패: {str(e)}'}
    
    def _get_test_account(self, user_role: str) -> Dict[str, Any]:
        """테스트 계정 정보 조회"""
        accounts = self.test_data.get('test_accounts', {}).get('test_accounts', {})
        
        if user_role == 'admin':
            return accounts.get('admin', {}).get('primary')
        elif user_role == 'secretary':
            return accounts.get('secretary', {}).get('primary')
        elif user_role in ['evaluator', 'evaluator1', 'evaluator2']:
            evaluators = accounts.get('evaluators', [])
            if evaluators:
                return evaluators[0]  # 첫 번째 평가위원 계정 사용
        
        return None
    
    async def _capture_screenshot(self, page: Page, filename: str) -> str:
        """스크린샷 캡처"""
        screenshot_dir = self.results_path / 'screenshots'
        screenshot_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        screenshot_path = screenshot_dir / f"{filename}_{timestamp}.png"
        
        await page.screenshot(path=str(screenshot_path), full_page=True)
        return str(screenshot_path)
    
    def _determine_scenario_status(self, completed: int, total: int, errors: List[str]) -> str:
        """시나리오 실행 상태 결정"""
        if len(errors) == 0 and completed == total:
            return 'success'
        elif completed >= total * 0.7:  # 70% 이상 완료
            return 'partial'
        else:
            return 'failed'
    
    def _get_current_performance_metrics(self) -> Dict[str, Any]:
        """현재 성능 메트릭 반환"""
        return {
            'avg_page_load_time': self._calculate_average(self.performance_metrics['page_load_times']),
            'avg_api_response_time': self._calculate_average(self.performance_metrics['api_response_times']),
            'error_count': len(self.performance_metrics['error_rates']),
            'total_actions': len(self.performance_metrics['user_action_times'])
        }
    
    def _calculate_average(self, metrics_list: List[Dict[str, Any]]) -> float:
        """메트릭 평균 계산"""
        if not metrics_list:
            return 0.0
        
        total = sum(item.get('time', 0) for item in metrics_list)
        return total / len(metrics_list)
    
    def _complete_user_journey(self, session_id: str):
        """사용자 여정 완료"""
        if session_id in self.user_journeys:
            self.user_journeys[session_id].end_time = datetime.now()
    
    async def run_scenario_suite(self, scenarios: List[Dict[str, str]]) -> List[ScenarioResult]:
        """시나리오 스위트 실행"""
        results = []
        
        for scenario_config in scenarios:
            scenario_id = scenario_config['scenario_id']
            user_role = scenario_config['user_role']
            
            try:
                result = await self.execute_scenario(scenario_id, user_role)
                results.append(result)
                
                # 시나리오 간 간격
                await asyncio.sleep(2)
                
            except Exception as e:
                logger.error(f"시나리오 실행 오류: {scenario_id} - {str(e)}")
                
                error_result = ScenarioResult(
                    scenario_id=scenario_id,
                    user_role=user_role,
                    status='failed',
                    execution_time=0,
                    steps_completed=0,
                    total_steps=0,
                    errors=[str(e)],
                    screenshots=[],
                    performance_metrics={}
                )
                results.append(error_result)
        
        return results
    
    async def generate_comprehensive_report(self, results: List[ScenarioResult]) -> str:
        """종합 보고서 생성"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = self.results_path / f"scenario_test_report_{timestamp}.json"
        
        # 결과 통계 계산
        total_scenarios = len(results)
        successful_scenarios = len([r for r in results if r.status == 'success'])
        failed_scenarios = len([r for r in results if r.status == 'failed'])
        partial_scenarios = len([r for r in results if r.status == 'partial'])
        
        avg_execution_time = sum(r.execution_time for r in results) / total_scenarios if total_scenarios > 0 else 0
        
        # 사용자 여정 분석
        journey_analysis = self._analyze_user_journeys()
        
        comprehensive_report = {
            'test_summary': {
                'timestamp': timestamp,
                'total_scenarios': total_scenarios,
                'successful_scenarios': successful_scenarios,
                'failed_scenarios': failed_scenarios,
                'partial_scenarios': partial_scenarios,
                'success_rate': (successful_scenarios / total_scenarios * 100) if total_scenarios > 0 else 0,
                'average_execution_time': avg_execution_time
            },
            'scenario_results': [asdict(result) for result in results],
            'user_journey_analysis': journey_analysis,
            'performance_metrics': self.performance_metrics,
            'recommendations': self._generate_recommendations(results)
        }
        
        # JSON 보고서 저장
        async with aiofiles.open(report_file, 'w', encoding='utf-8') as f:
            await f.write(json.dumps(comprehensive_report, indent=2, ensure_ascii=False))
        
        # HTML 보고서 생성
        html_report = await self._generate_html_report(comprehensive_report)
        html_file = self.results_path / f"scenario_test_report_{timestamp}.html"
        
        async with aiofiles.open(html_file, 'w', encoding='utf-8') as f:
            await f.write(html_report)
        
        logger.info(f"종합 보고서 생성 완료: {report_file}")
        return str(report_file)
    
    def _analyze_user_journeys(self) -> Dict[str, Any]:
        """사용자 여정 분석"""
        analysis = {
            'total_journeys': len(self.user_journeys),
            'role_distribution': {},
            'common_error_patterns': [],
            'average_session_duration': 0
        }
        
        for journey in self.user_journeys.values():
            role = journey.user_role
            analysis['role_distribution'][role] = analysis['role_distribution'].get(role, 0) + 1
            
            # 세션 지속 시간 계산
            if journey.end_time:
                duration = (journey.end_time - journey.start_time).total_seconds()
                analysis['average_session_duration'] += duration
        
        if self.user_journeys:
            analysis['average_session_duration'] /= len(self.user_journeys)
        
        return analysis
    
    def _generate_recommendations(self, results: List[ScenarioResult]) -> List[str]:
        """개선 권고사항 생성"""
        recommendations = []
        
        # 성공률 기반 권고
        success_rate = len([r for r in results if r.status == 'success']) / len(results) * 100
        if success_rate < 80:
            recommendations.append("전체 성공률이 80% 미만입니다. 주요 실패 시나리오를 검토하세요.")
        
        # 성능 기반 권고
        avg_time = sum(r.execution_time for r in results) / len(results)
        if avg_time > 60:  # 60초 초과
            recommendations.append("평균 실행 시간이 1분을 초과합니다. 성능 최적화가 필요합니다.")
        
        # 오류 패턴 분석
        common_errors = {}
        for result in results:
            for error in result.errors:
                common_errors[error] = common_errors.get(error, 0) + 1
        
        if common_errors:
            most_common = max(common_errors, key=common_errors.get)
            recommendations.append(f"가장 빈번한 오류: {most_common}")
        
        return recommendations
    
    async def _generate_html_report(self, report_data: Dict[str, Any]) -> str:
        """HTML 보고서 생성"""
        html_template = f'''
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>MCP 시나리오 테스트 보고서</title>
    <style>
        body {{ font-family: 'Arial', sans-serif; margin: 20px; background-color: #f5f5f5; }}
        .container {{ max-width: 1200px; margin: 0 auto; background: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; border-radius: 10px; margin-bottom: 30px; }}
        .metrics {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin-bottom: 30px; }}
        .metric-card {{ background: #f8f9fa; padding: 20px; border-radius: 8px; text-align: center; border-left: 4px solid #007bff; }}
        .metric-value {{ font-size: 2em; font-weight: bold; color: #007bff; }}
        .scenario-grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 20px; }}
        .scenario-card {{ background: white; border: 1px solid #ddd; border-radius: 8px; padding: 15px; }}
        .status-success {{ border-left: 4px solid #28a745; }}
        .status-failed {{ border-left: 4px solid #dc3545; }}
        .status-partial {{ border-left: 4px solid #ffc107; }}
        .recommendations {{ background: #e9ecef; padding: 20px; border-radius: 8px; margin-top: 30px; }}
        .chart-container {{ margin: 20px 0; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🚀 MCP 시나리오 테스트 보고서</h1>
            <p>생성 시간: {report_data['test_summary']['timestamp']}</p>
            <p>사용자별 시나리오 기반 테스트 결과</p>
        </div>
        
        <div class="metrics">
            <div class="metric-card">
                <div class="metric-value">{report_data['test_summary']['total_scenarios']}</div>
                <div>총 시나리오</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">{report_data['test_summary']['success_rate']:.1f}%</div>
                <div>성공률</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">{report_data['test_summary']['average_execution_time']:.1f}s</div>
                <div>평균 실행시간</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">{report_data['user_journey_analysis']['total_journeys']}</div>
                <div>사용자 여정</div>
            </div>
        </div>
        
        <h2>📊 시나리오별 결과</h2>
        <div class="scenario-grid">
'''
        
        # 시나리오 결과 카드 생성
        for result in report_data['scenario_results']:
            status_class = f"status-{result['status']}"
            status_emoji = "✅" if result['status'] == 'success' else "❌" if result['status'] == 'failed' else "⚠️"
            
            html_template += f'''
            <div class="scenario-card {status_class}">
                <h3>{status_emoji} {result['scenario_id']}</h3>
                <p><strong>역할:</strong> {result['user_role']}</p>
                <p><strong>상태:</strong> {result['status']}</p>
                <p><strong>실행시간:</strong> {result['execution_time']:.1f}초</p>
                <p><strong>완료도:</strong> {result['steps_completed']}/{result['total_steps']} 단계</p>
                {'<p><strong>오류:</strong> ' + str(len(result['errors'])) + '건</p>' if result['errors'] else ''}
            </div>
            '''
        
        html_template += f'''
        </div>
        
        <div class="recommendations">
            <h2>💡 개선 권고사항</h2>
            <ul>
'''
        
        # 권고사항 추가
        for recommendation in report_data['recommendations']:
            html_template += f'<li>{recommendation}</li>'
        
        html_template += '''
            </ul>
        </div>
    </div>
</body>
</html>
'''
        
        return html_template

# CLI 인터페이스
async def main():
    """메인 실행 함수"""
    import argparse
    
    parser = argparse.ArgumentParser(description='MCP 시나리오 테스트 러너')
    parser.add_argument('--scenario', help='실행할 시나리오 ID')
    parser.add_argument('--role', help='사용자 역할')
    parser.add_argument('--suite', help='시나리오 스위트 파일 경로')
    parser.add_argument('--all', action='store_true', help='모든 시나리오 실행')
    
    args = parser.parse_args()
    
    runner = MCPScenarioRunner()
    
    if args.scenario and args.role:
        # 단일 시나리오 실행
        result = await runner.execute_scenario(args.scenario, args.role)
        print(f"시나리오 실행 결과: {result.status}")
        
    elif args.all:
        # 모든 주요 시나리오 실행
        scenarios = [
            {'scenario_id': 'admin_initial_setup', 'user_role': 'admin'},
            {'scenario_id': 'secretary_project_creation', 'user_role': 'secretary'},
            {'scenario_id': 'evaluator_ai_assisted_evaluation', 'user_role': 'evaluator'},
            {'scenario_id': 'complete_evaluation_lifecycle', 'user_role': 'cross'}
        ]
        
        results = await runner.run_scenario_suite(scenarios)
        report_file = await runner.generate_comprehensive_report(results)
        print(f"종합 보고서 생성: {report_file}")
    
    else:
        print("사용법: python mcp_scenario_runner.py --scenario <ID> --role <ROLE> 또는 --all")

if __name__ == "__main__":
    asyncio.run(main())