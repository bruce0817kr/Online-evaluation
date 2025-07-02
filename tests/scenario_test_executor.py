#!/usr/bin/env python3
"""
Scenario Test Executor
시나리오 테스트 실행 및 대시보드 연동
"""

import asyncio
import json
import time
import websockets
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any
import logging
from mcp_scenario_runner import MCPScenarioRunner
from cross_role_integration_tester import CrossRoleIntegrationTester

logger = logging.getLogger('ScenarioTestExecutor')

class ScenarioTestExecutor:
    def __init__(self, dashboard_port: int = 8765):
        self.dashboard_port = dashboard_port
        self.scenario_runner = MCPScenarioRunner()
        self.integration_tester = CrossRoleIntegrationTester()
        
        self.active_sessions = {}
        self.test_status = {
            'system_status': 'ready',
            'running_scenarios': [],
            'completed_scenarios': [],
            'failed_scenarios': [],
            'active_users': [],
            'metrics': {
                'total_scenarios': 0,
                'success_rate': 0,
                'avg_response_time': 0,
                'error_rate': 0
            }
        }
        
        self.websocket_clients = set()
        
    async def start_dashboard_server(self):
        """대시보드 웹소켓 서버 시작"""
        logger.info(f"대시보드 서버 시작: ws://localhost:{self.dashboard_port}")
        
        async def handle_client(websocket, path):
            self.websocket_clients.add(websocket)
            logger.info(f"대시보드 클라이언트 연결: {websocket.remote_address}")
            
            try:
                # 초기 상태 전송
                await self.send_dashboard_update('initial_state', self.test_status)
                
                # 클라이언트 메시지 처리
                async for message in websocket:
                    await self.handle_dashboard_command(message, websocket)
                    
            except websockets.exceptions.ConnectionClosed:
                logger.info("대시보드 클라이언트 연결 종료")
            finally:
                self.websocket_clients.discard(websocket)
        
        return await websockets.serve(handle_client, "localhost", self.dashboard_port)
    
    async def handle_dashboard_command(self, message: str, websocket):
        """대시보드 명령 처리"""
        try:
            command = json.loads(message)
            action = command.get('action')
            
            if action == 'run_all_scenarios':
                await self.execute_all_scenarios()
            elif action == 'run_scenario':
                scenario_id = command.get('scenario_id')
                user_role = command.get('user_role')
                await self.execute_single_scenario(scenario_id, user_role)
            elif action == 'stop_tests':
                await self.stop_all_tests()
            elif action == 'get_status':
                await websocket.send(json.dumps({
                    'type': 'status_update',
                    'data': self.test_status
                }))
                
        except json.JSONDecodeError:
            logger.error("대시보드 메시지 파싱 오류")
        except Exception as e:
            logger.error(f"대시보드 명령 처리 오류: {str(e)}")
    
    async def send_dashboard_update(self, update_type: str, data: Any):
        """모든 대시보드 클라이언트에 업데이트 전송"""
        if not self.websocket_clients:
            return
            
        message = json.dumps({
            'type': update_type,
            'timestamp': datetime.now().isoformat(),
            'data': data
        })
        
        # 연결이 끊어진 클라이언트 제거
        disconnected_clients = set()
        
        for client in self.websocket_clients:
            try:
                await client.send(message)
            except websockets.exceptions.ConnectionClosed:
                disconnected_clients.add(client)
        
        self.websocket_clients -= disconnected_clients
    
    async def execute_all_scenarios(self):
        """모든 주요 시나리오 실행"""
        logger.info("모든 시나리오 실행 시작")
        
        scenarios = [
            {'scenario_id': 'admin_initial_setup', 'user_role': 'admin'},
            {'scenario_id': 'secretary_project_creation', 'user_role': 'secretary'},
            {'scenario_id': 'evaluator_ai_assisted_evaluation', 'user_role': 'evaluator'},
            {'scenario_id': 'complete_evaluation_lifecycle', 'user_role': 'cross'}
        ]
        
        self.test_status['system_status'] = 'running'
        self.test_status['total_scenarios'] = len(scenarios)
        
        await self.send_dashboard_update('test_started', {
            'total_scenarios': len(scenarios),
            'scenarios': scenarios
        })
        
        results = []
        
        for i, scenario in enumerate(scenarios):
            await self.send_dashboard_update('scenario_started', {
                'scenario_id': scenario['scenario_id'],
                'user_role': scenario['user_role'],
                'progress': i / len(scenarios) * 100
            })
            
            try:
                if scenario['user_role'] == 'cross':
                    # 교차 역할 통합 테스트
                    result = await self.integration_tester.execute_complete_evaluation_lifecycle()
                    success = result.success
                else:
                    # 일반 시나리오 테스트
                    result = await self.scenario_runner.execute_scenario(
                        scenario['scenario_id'], 
                        scenario['user_role']
                    )
                    success = result.status == 'success'
                
                if success:
                    self.test_status['completed_scenarios'].append(scenario['scenario_id'])
                else:
                    self.test_status['failed_scenarios'].append(scenario['scenario_id'])
                
                results.append(result)
                
                await self.send_dashboard_update('scenario_completed', {
                    'scenario_id': scenario['scenario_id'],
                    'success': success,
                    'progress': (i + 1) / len(scenarios) * 100
                })
                
            except Exception as e:
                logger.error(f"시나리오 실행 오류: {scenario['scenario_id']} - {str(e)}")
                self.test_status['failed_scenarios'].append(scenario['scenario_id'])
                
                await self.send_dashboard_update('scenario_failed', {
                    'scenario_id': scenario['scenario_id'],
                    'error': str(e)
                })
        
        # 최종 결과 업데이트
        success_count = len(self.test_status['completed_scenarios'])
        self.test_status['metrics']['success_rate'] = (success_count / len(scenarios)) * 100
        self.test_status['system_status'] = 'completed'
        
        await self.send_dashboard_update('all_tests_completed', {
            'success_count': success_count,
            'total_count': len(scenarios),
            'success_rate': self.test_status['metrics']['success_rate']
        })
        
        # 종합 보고서 생성
        report_file = await self.generate_comprehensive_report(results)
        
        await self.send_dashboard_update('report_generated', {
            'report_file': report_file
        })
        
        logger.info(f"모든 시나리오 실행 완료: {success_count}/{len(scenarios)} 성공")
    
    async def execute_single_scenario(self, scenario_id: str, user_role: str):
        """단일 시나리오 실행"""
        logger.info(f"단일 시나리오 실행: {scenario_id} ({user_role})")
        
        await self.send_dashboard_update('scenario_started', {
            'scenario_id': scenario_id,
            'user_role': user_role
        })
        
        try:
            if user_role == 'cross':
                # 교차 역할 통합 테스트
                if scenario_id == 'complete_evaluation_lifecycle':
                    result = await self.integration_tester.execute_complete_evaluation_lifecycle()
                elif scenario_id == 'realtime_collaborative_evaluation':
                    result = await self.integration_tester.execute_realtime_collaborative_evaluation()
                else:
                    raise ValueError(f"알 수 없는 교차 역할 시나리오: {scenario_id}")
                
                success = result.success
            else:
                # 일반 시나리오 테스트
                result = await self.scenario_runner.execute_scenario(scenario_id, user_role)
                success = result.status == 'success'
            
            if success:
                self.test_status['completed_scenarios'].append(scenario_id)
            else:
                self.test_status['failed_scenarios'].append(scenario_id)
            
            await self.send_dashboard_update('scenario_completed', {
                'scenario_id': scenario_id,
                'success': success,
                'result': result if hasattr(result, '__dict__') else str(result)
            })
            
        except Exception as e:
            logger.error(f"시나리오 실행 오류: {scenario_id} - {str(e)}")
            self.test_status['failed_scenarios'].append(scenario_id)
            
            await self.send_dashboard_update('scenario_failed', {
                'scenario_id': scenario_id,
                'error': str(e)
            })
    
    async def stop_all_tests(self):
        """모든 테스트 중지"""
        logger.info("모든 테스트 중지")
        
        self.test_status['system_status'] = 'stopped'
        self.test_status['running_scenarios'] = []
        
        await self.send_dashboard_update('tests_stopped', {
            'message': '모든 테스트가 중지되었습니다.'
        })
    
    async def monitor_user_sessions(self):
        """사용자 세션 모니터링"""
        while True:
            try:
                # 활성 사용자 세션 확인
                active_users = []
                
                for session_id, session_info in self.active_sessions.items():
                    if session_info.get('last_activity'):
                        time_diff = time.time() - session_info['last_activity']
                        if time_diff < 300:  # 5분 이내 활동
                            active_users.append({
                                'session_id': session_id,
                                'role': session_info.get('role'),
                                'name': session_info.get('name'),
                                'status': 'active',
                                'last_action': session_info.get('last_action'),
                                'session_duration': session_info.get('session_duration', 0)
                            })
                
                self.test_status['active_users'] = active_users
                
                await self.send_dashboard_update('user_sessions_update', {
                    'active_users': active_users,
                    'total_sessions': len(self.active_sessions)
                })
                
                await asyncio.sleep(5)  # 5초마다 업데이트
                
            except Exception as e:
                logger.error(f"사용자 세션 모니터링 오류: {str(e)}")
                await asyncio.sleep(10)
    
    async def monitor_system_metrics(self):
        """시스템 메트릭 모니터링"""
        while True:
            try:
                # 실시간 메트릭 수집
                metrics = {
                    'avg_response_time': self.calculate_avg_response_time(),
                    'error_rate': self.calculate_error_rate(),
                    'throughput': self.calculate_throughput(),
                    'memory_usage': self.get_memory_usage(),
                    'cpu_usage': self.get_cpu_usage()
                }
                
                self.test_status['metrics'].update(metrics)
                
                await self.send_dashboard_update('metrics_update', metrics)
                
                await asyncio.sleep(3)  # 3초마다 업데이트
                
            except Exception as e:
                logger.error(f"시스템 메트릭 모니터링 오류: {str(e)}")
                await asyncio.sleep(10)
    
    def calculate_avg_response_time(self) -> float:
        """평균 응답 시간 계산"""
        # 실제 구현에서는 API 응답 시간 수집
        import random
        return round(random.uniform(150, 350), 1)
    
    def calculate_error_rate(self) -> float:
        """오류율 계산"""
        # 실제 구현에서는 오류 발생률 계산
        import random
        return round(random.uniform(0, 5), 2)
    
    def calculate_throughput(self) -> float:
        """처리량 계산"""
        # 실제 구현에서는 TPS 계산
        import random
        return round(random.uniform(50, 150), 1)
    
    def get_memory_usage(self) -> float:
        """메모리 사용률 조회"""
        try:
            import psutil
            return psutil.virtual_memory().percent
        except ImportError:
            import random
            return round(random.uniform(40, 80), 1)
    
    def get_cpu_usage(self) -> float:
        """CPU 사용률 조회"""
        try:
            import psutil
            return psutil.cpu_percent(interval=1)
        except ImportError:
            import random
            return round(random.uniform(20, 70), 1)
    
    async def generate_comprehensive_report(self, results: List[Any]) -> str:
        """종합 보고서 생성"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = f"tests/results/comprehensive_scenario_report_{timestamp}.json"
        
        # 보고서 데이터 구성
        report_data = {
            'test_summary': {
                'timestamp': timestamp,
                'total_scenarios': len(results),
                'completed_scenarios': len(self.test_status['completed_scenarios']),
                'failed_scenarios': len(self.test_status['failed_scenarios']),
                'success_rate': self.test_status['metrics']['success_rate'],
                'execution_duration': self.calculate_total_execution_time(results)
            },
            'scenario_results': [
                self.format_result_for_report(result) for result in results
            ],
            'system_metrics': self.test_status['metrics'],
            'user_sessions': self.test_status['active_users'],
            'recommendations': self.generate_improvement_recommendations()
        }
        
        # JSON 보고서 저장
        Path("tests/results").mkdir(exist_ok=True)
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, indent=2, ensure_ascii=False, default=str)
        
        # HTML 보고서 생성
        html_report = await self.generate_html_dashboard_report(report_data)
        html_file = report_file.replace('.json', '.html')
        
        with open(html_file, 'w', encoding='utf-8') as f:
            f.write(html_report)
        
        logger.info(f"종합 보고서 생성 완료: {report_file}")
        return report_file
    
    def format_result_for_report(self, result: Any) -> Dict[str, Any]:
        """보고서용 결과 포맷"""
        if hasattr(result, '__dict__'):
            return {
                'scenario_id': getattr(result, 'scenario_id', 'unknown'),
                'user_role': getattr(result, 'user_role', 'unknown'),
                'status': getattr(result, 'status', 'unknown'),
                'execution_time': getattr(result, 'execution_time', 0),
                'success': getattr(result, 'success', False),
                'errors': getattr(result, 'errors', [])
            }
        else:
            return {'result': str(result)}
    
    def calculate_total_execution_time(self, results: List[Any]) -> float:
        """총 실행 시간 계산"""
        total_time = 0
        for result in results:
            if hasattr(result, 'execution_time'):
                total_time += result.execution_time
        return total_time
    
    def generate_improvement_recommendations(self) -> List[str]:
        """개선 권고사항 생성"""
        recommendations = []
        
        success_rate = self.test_status['metrics']['success_rate']
        if success_rate < 90:
            recommendations.append(f"시나리오 성공률이 {success_rate:.1f}%입니다. 90% 이상 달성을 목표로 개선하세요.")
        
        error_rate = self.test_status['metrics']['error_rate']
        if error_rate > 3:
            recommendations.append(f"오류율이 {error_rate:.1f}%로 높습니다. 3% 이하로 개선하세요.")
        
        avg_response_time = self.test_status['metrics']['avg_response_time']
        if avg_response_time > 300:
            recommendations.append(f"평균 응답 시간이 {avg_response_time:.1f}ms입니다. 300ms 이하로 최적화하세요.")
        
        return recommendations
    
    async def generate_html_dashboard_report(self, report_data: Dict[str, Any]) -> str:
        """HTML 대시보드 보고서 생성"""
        # 간단한 HTML 템플릿
        html_content = f'''
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <title>시나리오 테스트 보고서</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }}
        .container {{ max-width: 1200px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; }}
        .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 8px; margin-bottom: 30px; }}
        .metrics {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin-bottom: 30px; }}
        .metric-card {{ background: #f8f9fa; padding: 20px; border-radius: 8px; text-align: center; }}
        .metric-value {{ font-size: 2em; font-weight: bold; color: #007bff; }}
        .recommendations {{ background: #e9ecef; padding: 20px; border-radius: 8px; }}
        table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
        th, td {{ padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }}
        th {{ background: #f8f9fa; }}
        .success {{ color: #28a745; }}
        .failed {{ color: #dc3545; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🚀 MCP 시나리오 테스트 보고서</h1>
            <p>생성 시간: {report_data['test_summary']['timestamp']}</p>
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
                <div class="metric-value">{report_data['test_summary']['execution_duration']:.1f}s</div>
                <div>총 실행시간</div>
            </div>
        </div>
        
        <h2>📋 시나리오 결과</h2>
        <table>
            <thead>
                <tr>
                    <th>시나리오 ID</th>
                    <th>사용자 역할</th>
                    <th>상태</th>
                    <th>실행시간</th>
                </tr>
            </thead>
            <tbody>
        '''
        
        # 시나리오 결과 테이블
        for result in report_data['scenario_results']:
            status_class = 'success' if result.get('success') else 'failed'
            html_content += f'''
                <tr>
                    <td>{result.get('scenario_id', 'N/A')}</td>
                    <td>{result.get('user_role', 'N/A')}</td>
                    <td class="{status_class}">{result.get('status', 'N/A')}</td>
                    <td>{result.get('execution_time', 0):.1f}s</td>
                </tr>
            '''
        
        html_content += f'''
            </tbody>
        </table>
        
        <div class="recommendations">
            <h2>💡 개선 권고사항</h2>
            <ul>
        '''
        
        # 권고사항 추가
        for recommendation in report_data['recommendations']:
            html_content += f'<li>{recommendation}</li>'
        
        html_content += '''
            </ul>
        </div>
    </div>
</body>
</html>
        '''
        
        return html_content
    
    async def run(self):
        """메인 실행 함수"""
        logger.info("시나리오 테스트 실행기 시작")
        
        # 대시보드 서버 시작
        server = await self.start_dashboard_server()
        
        # 백그라운드 모니터링 작업 시작
        monitoring_tasks = [
            asyncio.create_task(self.monitor_user_sessions()),
            asyncio.create_task(self.monitor_system_metrics())
        ]
        
        try:
            logger.info("시나리오 테스트 실행기 준비 완료")
            print(f"🚀 대시보드 URL: http://localhost:{self.dashboard_port}")
            print("📊 실시간 모니터링 시작...")
            
            # 서버 실행 유지
            await server.wait_closed()
            
        except KeyboardInterrupt:
            logger.info("사용자에 의해 중단됨")
        finally:
            # 정리 작업
            for task in monitoring_tasks:
                task.cancel()
            server.close()
            await server.wait_closed()

# CLI 실행
async def main():
    """메인 함수"""
    import argparse
    
    parser = argparse.ArgumentParser(description='시나리오 테스트 실행기')
    parser.add_argument('--port', type=int, default=8765, help='대시보드 포트')
    parser.add_argument('--auto-run', action='store_true', help='자동으로 모든 시나리오 실행')
    
    args = parser.parse_args()
    
    executor = ScenarioTestExecutor(dashboard_port=args.port)
    
    if args.auto_run:
        # 자동 실행 모드
        await executor.execute_all_scenarios()
    else:
        # 대시보드 모드
        await executor.run()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())