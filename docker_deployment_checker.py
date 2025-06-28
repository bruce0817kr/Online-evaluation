#!/usr/bin/env python3
"""
Docker 배포 완료 후 시스템 검증 스크립트
포트 충돌 해결 및 가상화 환경 개선 검증
"""

import requests
import time
import subprocess
import json
import socket
from typing import Dict, List, Optional
import logging

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class DockerDeploymentChecker:
    def __init__(self):
        self.services = {
            'redis': {'port': 6379, 'name': 'online-evaluation-redis'},
            'mongodb': {'port': 27017, 'name': 'online-evaluation-mongodb'},
            'backend': {'port': 8080, 'name': 'online-evaluation-backend'},
            'frontend': {'port': 3000, 'name': 'online-evaluation-frontend'}
        }
        self.test_results = {}

    def check_docker_containers(self) -> bool:
        """실행 중인 Docker 컨테이너 확인"""
        logger.info("🐳 Docker 컨테이너 상태 확인 중...")
        try:
            result = subprocess.run(
                ['docker', 'ps', '--format', 'json'], 
                capture_output=True, 
                text=True, 
                check=True,
                encoding='utf-8',
                errors='ignore'
            )
            
            containers = []
            for line in result.stdout.strip().split('\n'):
                if line:
                    containers.append(json.loads(line))
            
            running_containers = {}
            for container in containers:
                name = container.get('Names', '')
                status = container.get('Status', '')
                running_containers[name] = status
                
            logger.info(f"실행 중인 컨테이너: {len(running_containers)}개")
            
            all_running = True
            for service_name, config in self.services.items():
                container_name = config['name']
                if container_name in running_containers:
                    logger.info(f"✅ {service_name}: {running_containers[container_name]}")
                else:
                    logger.error(f"❌ {service_name}: 컨테이너가 실행되지 않음")
                    all_running = False
                    
            self.test_results['docker_containers'] = all_running
            return all_running
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Docker 명령 실행 실패: {e}")
            self.test_results['docker_containers'] = False
            return False
        except Exception as e:
            logger.error(f"컨테이너 확인 중 오류: {e}")
            self.test_results['docker_containers'] = False
            return False
    
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
            {'name': 'Backend Health', 'url': 'http://localhost:8080/health'},
            {'name': 'Backend Docs', 'url': 'http://localhost:8080/docs'},
            {'name': 'Frontend', 'url': 'http://localhost:3000'}
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
            # MongoDB 연결 확인 (백엔드 API를 통해)
            response = requests.get('http://localhost:8080/api/status', timeout=10)
            if response.status_code == 200:
                data = response.json()
                db_status = data.get('database', {}).get('status') == 'connected'
                cache_status = data.get('cache', {}).get('status') == 'connected'
                
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
                logger.error(f"❌ 데이터베이스 상태 확인 실패: {response.status_code}")
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
            {'name': 'API Root', 'url': 'http://localhost:8080/', 'method': 'GET'},
            {'name': 'Users List', 'url': 'http://localhost:8080/api/users', 'method': 'GET'},
            {'name': 'Tests List', 'url': 'http://localhost:8080/api/tests', 'method': 'GET'}
        ]
        
        all_functional = True
        
        for test in api_tests:
            try:
                if test['method'] == 'GET':
                    response = requests.get(test['url'], timeout=10)
                else:
                    continue
                    
                if response.status_code in [200, 201]:
                    logger.info(f"✅ {test['name']}: 정상 작동")
                else:
                    logger.warning(f"⚠️ {test['name']}: 상태 코드 {response.status_code}")
                    
            except Exception as e:
                logger.error(f"❌ {test['name']}: 오류 - {e}")
                all_functional = False
                
        self.test_results['api_functionality'] = all_functional
        return all_functional
    
    def check_network_isolation(self) -> bool:
        """Docker 네트워크 격리 확인"""
        logger.info("🌐 Docker 네트워크 격리 확인 중...")
        
        try:
            # Docker 네트워크 확인
            result = subprocess.run(
                ['docker', 'network', 'ls', '--format', 'json'], 
                capture_output=True, 
                text=True, 
                check=True
            )
            
            networks = []
            for line in result.stdout.strip().split('\n'):
                if line:
                    networks.append(json.loads(line))
            
            evaluation_network_exists = any(
                'online-evaluation' in network.get('Name', '') 
                for network in networks
            )
            
            if evaluation_network_exists:
                logger.info("✅ 전용 Docker 네트워크 격리됨")
                self.test_results['network_isolation'] = True
                return True
            else:
                logger.warning("⚠️ 전용 Docker 네트워크를 찾을 수 없음")
                self.test_results['network_isolation'] = False
                return False
                
        except Exception as e:
            logger.error(f"❌ 네트워크 격리 확인 중 오류: {e}")
            self.test_results['network_isolation'] = False
            return False
    
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
            report['recommendations'].append("Docker 컨테이너 상태를 확인하고 재시작하세요.")
            
        if not self.test_results.get('port_accessibility', True):
            report['recommendations'].append("포트 충돌을 확인하고 포트 관리자를 실행하세요.")
            
        if not self.test_results.get('database_connectivity', True):
            report['recommendations'].append("데이터베이스 연결 설정과 MongoDB/Redis 상태를 확인하세요.")
            
        if not self.test_results.get('network_isolation', True):
            report['recommendations'].append("Docker Compose 네트워크 설정을 확인하세요.")
        
        return report
    
    def run_full_check(self) -> Dict:
        """전체 검증 실행"""
        logger.info("🚀 Docker 배포 검증 시작...")
        
        # 검증 단계별 실행
        checks = [
            ('Docker 컨테이너', self.check_docker_containers),
            ('포트 접근성', self.check_port_accessibility),
            ('헬스 엔드포인트', self.check_health_endpoints),
            ('데이터베이스 연결', self.check_database_connectivity),
            ('API 기능', self.check_api_functionality),
            ('네트워크 격리', self.check_network_isolation)
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
            time.sleep(2)
        
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
    checker = DockerDeploymentChecker()
    
    try:
        # 시스템이 준비될 때까지 잠시 대기
        logger.info("시스템 준비 대기 중... (30초)")
        time.sleep(30)
        
        # 전체 검증 실행
        report = checker.run_full_check()
        
        # 결과를 파일로 저장
        with open('docker_deployment_report.json', 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        logger.info(f"\n📁 상세 리포트가 'docker_deployment_report.json'에 저장되었습니다.")
        
        # 성공/실패에 따른 종료 코드 반환
        if report['overall_status'] == 'PASS':
            logger.info("🎉 배포 검증 완료 - 성공!")
            exit(0)
        else:
            logger.error("❌ 배포 검증 완료 - 실패!")
            exit(1)
            
    except KeyboardInterrupt:
        logger.info("\n사용자에 의해 검증이 중단되었습니다.")
        exit(1)
    except Exception as e:
        logger.error(f"검증 중 예기치 않은 오류 발생: {e}")
        exit(1)

if __name__ == "__main__":
    main()
