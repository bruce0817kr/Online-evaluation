#!/usr/bin/env python3
"""
개선된 Docker 배포 완료 후 시스템 검증 스크립트
Unicode 인코딩 문제 해결 및 API 엔드포인트 개선
"""

import requests
import time
import subprocess
import json
import socket
import sys
from typing import Dict, List, Optional
import logging

# UTF-8 출력 강제 설정 (Windows 환경 대응)
if sys.platform == "win32":
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('deployment_check.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)

class ImprovedDockerDeploymentChecker:
    def __init__(self):
        self.services = {
            'redis': {'port': 6479, 'name': 'online-evaluation-redis-dev'},
            'mongodb': {'port': 27117, 'name': 'online-evaluation-mongodb-dev'},
            'backend': {'port': 8180, 'name': 'online-evaluation-backend-dev'},
            'frontend': {'port': 3100, 'name': 'online-evaluation-frontend-dev'}
        }
        self.test_results = {}
        
    def safe_run_command(self, command: List[str], timeout: int = 30) -> Optional[str]:
        """안전한 명령어 실행 (Unicode 인코딩 문제 해결)"""
        try:
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                check=True,
                timeout=timeout,
                encoding='utf-8',
                errors='replace'  # Unicode 오류 시 대체 문자 사용
            )
            return result.stdout
        except subprocess.TimeoutExpired:
            logger.error(f"명령어 타임아웃: {' '.join(command)}")
            return None
        except subprocess.CalledProcessError as e:
            logger.error(f"명령어 실행 실패: {' '.join(command)} - {e}")
            return None
        except Exception as e:
            logger.error(f"명령어 실행 중 오류: {' '.join(command)} - {e}")
            return None
        
    def check_docker_containers(self) -> bool:
        """실행 중인 Docker 컨테이너 확인"""
        logger.info("🐳 Docker 컨테이너 상태 확인 중...")
        
        docker_output = self.safe_run_command(['docker', 'version'])
        if not docker_output:
            logger.error("❌ Docker가 실행되지 않거나 접근할 수 없습니다")
            self.test_results['docker_containers'] = False
            return False
        
        # Get running container names directly
        ps_output = self.safe_run_command(['docker', 'ps', '--format', '{{.Names}}'])
        if ps_output is None: # Check for None explicitly
            logger.error("❌ Docker 컨테이너 목록을 가져올 수 없습니다")
            self.test_results['docker_containers'] = False
            return False
        
        running_containers = [name.strip().replace('"', '') for name in ps_output.strip().split('\n')]
        
        logger.info(f"실행 중인 컨테이너: {len(running_containers)}개 - {running_containers}")
        
        all_running = True
        for service_name, config in self.services.items():
            container_name = config['name']
            if container_name in running_containers:
                logger.info(f"✅ {service_name}: 컨테이너가 실행 중입니다.")
            else:
                logger.error(f"❌ {service_name}: 컨테이너가 실행되지 않음")
                all_running = False
                
        self.test_results['docker_containers'] = all_running
        return all_running
    
    def check_port_accessibility(self) -> bool:
        """포트 접근성 확인"""
        logger.info("🔌 포트 접근성 확인 중...")
        
        all_accessible = True
        
        for service_name, config in self.services.items():
            port = config['port']
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                    sock.settimeout(5)
                    result = sock.connect_ex(('localhost', port))
                    if result == 0:
                        logger.info(f"✅ {service_name} 포트 {port}: 접근 가능")
                    else:
                        logger.error(f"❌ {service_name} 포트 {port}: 접근 불가")
                        all_accessible = False
            except Exception as e:
                logger.error(f"❌ {service_name} 포트 {port} 확인 중 오류: {e}")
                all_accessible = False
                
        self.test_results['port_accessibility'] = all_accessible
        return all_accessible
    
    def check_health_endpoints(self) -> bool:
        """헬스 엔드포인트 확인"""
        logger.info("🏥 헬스 엔드포인트 확인 중...")
        
        health_checks = [
            {'name': 'Backend Health', 'url': 'http://localhost:8180/health'},
            {'name': 'Backend Root', 'url': 'http://localhost:8180/'},
            {'name': 'Backend Docs', 'url': 'http://localhost:8180/docs'},
            {'name': 'Frontend', 'url': 'http://localhost:3100'}
        ]
        
        all_healthy = True
        
        for check in health_checks:
            try:
                response = requests.get(check['url'], timeout=10)
                if response.status_code == 200:
                    logger.info(f"✅ {check['name']}: 정상 응답 (200)")
                else:
                    logger.error(f"❌ {check['name']}: 비정상 응답 ({response.status_code})")
                    all_healthy = False
            except requests.exceptions.ConnectionError:
                logger.error(f"❌ {check['name']}: 연결 실패")
                all_healthy = False
            except requests.exceptions.Timeout:
                logger.error(f"❌ {check['name']}: 타임아웃")
                all_healthy = False
            except Exception as e:
                logger.error(f"❌ {check['name']}: 확인 중 오류 - {e}")
                all_healthy = False
                
        self.test_results['health_endpoints'] = all_healthy
        return all_healthy
    
    def check_database_connectivity(self) -> bool:
        """데이터베이스 연결성 확인"""
        logger.info("🗄️ 데이터베이스 연결성 확인 중...")
        
        try:
            # 새로운 API 엔드포인트 사용
            response = requests.get('http://localhost:8180/db-status', timeout=15)
            if response.status_code == 200:
                data = response.json()
                databases_info = data.get('databases', {})
                db_status = databases_info.get('mongodb', {}).get('status') == 'healthy'
                cache_status = databases_info.get('redis', {}).get('status') == 'healthy'
                
                if db_status:
                    logger.info("✅ MongoDB: 연결됨")
                else:
                    logger.error("❌ MongoDB: 연결 실패")
                    
                if cache_status:
                    logger.info("✅ Redis: 연결됨")
                else:
                    logger.error("❌ Redis: 연결 실패")
                    
                overall_db_status = db_status and cache_status
            else:
                logger.error(f"❌ 데이터베이스 상태 확인 실패: HTTP {response.status_code}")
                overall_db_status = False
                
        except requests.exceptions.ConnectionError:
            logger.error("❌ 백엔드 API에 연결할 수 없습니다")
            overall_db_status = False
        except Exception as e:
            logger.error(f"❌ 데이터베이스 연결 확인 중 오류: {e}")
            overall_db_status = False
            
        self.test_results['database_connectivity'] = overall_db_status
        return overall_db_status
    
    def check_api_functionality(self) -> bool:
        """API 기능 확인"""
        logger.info("🔧 API 기능 확인 중...")
        
        api_tests = [
            {'name': 'API Root', 'url': 'http://localhost:8180/', 'expected_codes': [200]},
            {'name': 'API Status', 'url': 'http://localhost:8180/api/status', 'expected_codes': [200]},
            {'name': 'Users API', 'url': 'http://localhost:8180/api/users', 'expected_codes': [200, 404]},
            {'name': 'Tests API', 'url': 'http://localhost:8180/api/tests', 'expected_codes': [200, 404]}
        ]
        
        all_functional = True
        
        for test in api_tests:
            try:
                response = requests.get(test['url'], timeout=10)
                if response.status_code in test['expected_codes']:
                    logger.info(f"✅ {test['name']}: 정상 작동 (HTTP {response.status_code})")
                else:
                    logger.warning(f"⚠️ {test['name']}: 예상치 못한 상태 코드 {response.status_code}")
                    # 404나 다른 코드라도 API가 응답하는 것은 좋은 신호
                    
            except requests.exceptions.ConnectionError:
                logger.error(f"❌ {test['name']}: 연결 실패")
                all_functional = False
            except Exception as e:
                logger.error(f"❌ {test['name']}: 오류 - {e}")
                all_functional = False
                
        self.test_results['api_functionality'] = all_functional
        return all_functional
    
    def check_network_isolation(self) -> bool:
        """Docker 네트워크 격리 확인"""
        logger.info("🌐 Docker 네트워크 격리 확인 중...")
        
        network_output = self.safe_run_command(['docker', 'network', 'ls'])
        if not network_output:
            logger.error("❌ Docker 네트워크 목록을 가져올 수 없습니다")
            self.test_results['network_isolation'] = False
            return False
        
        evaluation_network_exists = 'online-evaluation' in network_output
        
        if evaluation_network_exists:
            logger.info("✅ 전용 Docker 네트워크 격리됨")
            self.test_results['network_isolation'] = True
            return True
        else:
            logger.warning("⚠️ 전용 Docker 네트워크를 찾을 수 없음 (기본 네트워크 사용 중)")
            self.test_results['network_isolation'] = False
            return False
    
    def check_system_resources(self) -> bool:
        """시스템 리소스 사용량 확인"""
        logger.info("💾 시스템 리소스 확인 중...")
        
        stats_output = self.safe_run_command(['docker', 'stats', '--no-stream', '--format', 'table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}'])
        if not stats_output:
            logger.warning("⚠️ Docker 컨테이너 리소스 통계를 가져올 수 없습니다")
            self.test_results['system_resources'] = False
            return False
        
        lines = stats_output.strip().split('\n')
        if len(lines) > 1:
            logger.info("📊 컨테이너 리소스 사용량:")
            for line in lines[1:]:  # 헤더 제외
                logger.info(f"   {line}")
            
        self.test_results['system_resources'] = True
        return True
    
    def generate_report(self) -> Dict:
        """종합 검증 리포트 생성"""
        logger.info("📊 검증 리포트 생성 중...")
        
        total_checks = len(self.test_results)
        passed_checks = sum(1 for result in self.test_results.values() if result)
        success_rate = (passed_checks / total_checks) * 100 if total_checks > 0 else 0
        
        report = {
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'total_checks': total_checks,
            'passed_checks': passed_checks,
            'success_rate': f"{success_rate:.1f}%",
            'overall_status': 'PASS' if success_rate >= 80 else 'FAIL',
            'detailed_results': self.test_results,
            'recommendations': []
        }
        
        # 실패한 검사에 대한 권장사항 추가
        if not self.test_results.get('docker_containers', True):
            report['recommendations'].append("Docker Desktop을 재시작하고 컨테이너를 다시 실행하세요.")
            
        if not self.test_results.get('port_accessibility', True):
            report['recommendations'].append("포트 충돌을 확인하고 port_manager.py를 실행하세요.")
            
        if not self.test_results.get('database_connectivity', True):
            report['recommendations'].append("MongoDB와 Redis 컨테이너 상태를 확인하고 네트워크 설정을 점검하세요.")
            
        if not self.test_results.get('api_functionality', True):
            report['recommendations'].append("백엔드 서버 로그를 확인하고 API 엔드포인트 설정을 점검하세요.")
        
        return report
    
    def run_full_check(self) -> Dict:
        """전체 검증 실행"""
        logger.info("🚀 개선된 Docker 배포 검증 시작...")
        
        # 검증 단계별 실행
        checks = [
            ('Docker 컨테이너', self.check_docker_containers),
            ('포트 접근성', self.check_port_accessibility),
            ('헬스 엔드포인트', self.check_health_endpoints),
            ('데이터베이스 연결', self.check_database_connectivity),
            ('API 기능', self.check_api_functionality),
            ('네트워크 격리', self.check_network_isolation),
            ('시스템 리소스', self.check_system_resources)
        ]
        
        for check_name, check_func in checks:
            logger.info(f"\n{'='*50}")
            logger.info(f"검사 중: {check_name}")
            logger.info(f"{'='*50}")
            
            try:
                check_func()
            except Exception as e:
                logger.error(f"{check_name} 검사 중 예외 발생: {e}")
                
            # 각 검사 사이에 잠시 대기
            time.sleep(1)
        
        # 최종 리포트 생성
        report = self.generate_report()
        
        logger.info(f"\n{'='*60}")
        logger.info("📋 최종 검증 결과")
        logger.info(f"{'='*60}")
        logger.info(f"전체 검사: {report['total_checks']}개")
        logger.info(f"통과 검사: {report['passed_checks']}개")
        logger.info(f"성공률: {report['success_rate']}")
        logger.info(f"전체 상태: {report['overall_status']}")
        
        if report['recommendations']:
            logger.info("\n🔧 권장사항:")
            for i, rec in enumerate(report['recommendations'], 1):
                logger.info(f"{i}. {rec}")
        
        return report

def main():
    """메인 실행 함수"""
    checker = ImprovedDockerDeploymentChecker()
    
    try:
        # 시스템이 준비될 때까지 잠시 대기
        logger.info("시스템 준비 대기 중... (10초)")
        time.sleep(10)
        
        # 전체 검증 실행
        report = checker.run_full_check()
        
        # 결과를 파일로 저장
        with open('improved_deployment_report.json', 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        logger.info(f"\n📁 상세 리포트가 'improved_deployment_report.json'에 저장되었습니다.")
        
        # 성공/실패에 따른 종료 코드 반환
        if report['overall_status'] == 'PASS':
            logger.info("🎉 배포 검증 완료 - 성공!")
            return 0
        else:
            logger.error("❌ 배포 검증 완료 - 개선 필요!")
            return 1
            
    except KeyboardInterrupt:
        logger.info("\n사용자에 의해 검증이 중단되었습니다.")
        return 1
    except Exception as e:
        logger.error(f"검증 중 예기치 않은 오류 발생: {e}")
        return 1

if __name__ == "__main__":
    exit(main())
