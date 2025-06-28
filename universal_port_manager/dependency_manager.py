#!/usr/bin/env python3
"""
의존성 관리자
============

Universal Port Manager의 의존성을 동적으로 관리하고 
누락된 의존성에 대한 대안을 제공하는 모듈
"""

import sys
import subprocess
import importlib
import logging
from typing import Dict, List, Tuple, Optional
from pathlib import Path

logger = logging.getLogger(__name__)

class DependencyManager:
    """
    의존성 관리 및 자동 설치 도우미
    
    기능:
    - 의존성 상태 확인
    - 자동 설치 시도
    - 대안 제공
    - 기능별 의존성 그룹 관리
    """
    
    # 의존성 그룹 정의
    DEPENDENCY_GROUPS = {
        'minimal': {
            'description': '기본 기능 (포트 스캔, 할당, CLI)',
            'packages': ['click'],
            'optional': []
        },
        'advanced': {
            'description': '고급 기능 (향상된 포트 스캔)',
            'packages': ['click'],
            'optional': ['psutil']
        },
        'docker': {
            'description': 'Docker Compose 파일 생성',
            'packages': ['click'],
            'optional': ['PyYAML']
        },
        'full': {
            'description': '모든 기능',
            'packages': ['click'],
            'optional': ['psutil', 'PyYAML', 'requests']
        }
    }
    
    # 패키지별 대안 기능
    PACKAGE_ALTERNATIVES = {
        'psutil': {
            'description': '향상된 시스템 정보 수집',
            'alternatives': [
                'subprocess를 이용한 ss/netstat 명령',
                'socket 기반 기본 포트 스캔',
                '수동 포트 지정'
            ],
            'install_command': 'pip install psutil'
        },
        'PyYAML': {
            'description': 'YAML 파일 처리 (Docker Compose)',
            'alternatives': [
                'JSON 형식 설정 파일 생성',
                '기본 텍스트 기반 YAML 생성',
                '수동 Docker Compose 파일 작성'
            ],
            'install_command': 'pip install PyYAML'
        },
        'requests': {
            'description': 'HTTP 기반 서비스 상태 확인',
            'alternatives': [
                'socket 기반 연결 테스트',
                '수동 서비스 상태 확인'
            ],
            'install_command': 'pip install requests'
        }
    }
    
    def __init__(self):
        """의존성 관리자 초기화"""
        self._available_packages = {}
        self._check_all_dependencies()
    
    def _check_all_dependencies(self):
        """모든 의존성 상태 확인"""
        all_packages = set()
        for group_info in self.DEPENDENCY_GROUPS.values():
            all_packages.update(group_info['packages'])
            all_packages.update(group_info['optional'])
        
        for package in all_packages:
            self._available_packages[package] = self._check_package(package)
    
    def _check_package(self, package_name: str) -> bool:
        """패키지 설치 상태 확인"""
        try:
            importlib.import_module(package_name.lower())
            return True
        except ImportError:
            # 일부 패키지는 import 이름이 다를 수 있음
            alternative_names = {
                'PyYAML': 'yaml',
                'psutil': 'psutil'
            }
            
            if package_name in alternative_names:
                try:
                    importlib.import_module(alternative_names[package_name])
                    return True
                except ImportError:
                    pass
            
            return False
    
    def get_dependency_status(self, group: str = 'full') -> Dict:
        """의존성 그룹의 상태 반환"""
        if group not in self.DEPENDENCY_GROUPS:
            raise ValueError(f"알 수 없는 의존성 그룹: {group}")
        
        group_info = self.DEPENDENCY_GROUPS[group]
        status = {
            'group': group,
            'description': group_info['description'],
            'required': {},
            'optional': {},
            'missing_required': [],
            'missing_optional': [],
            'available_features': []
        }
        
        # 필수 패키지 확인
        for package in group_info['packages']:
            available = self._available_packages.get(package, False)
            status['required'][package] = available
            if not available:
                status['missing_required'].append(package)
        
        # 선택적 패키지 확인
        for package in group_info['optional']:
            available = self._available_packages.get(package, False)
            status['optional'][package] = available
            if not available:
                status['missing_optional'].append(package)
            else:
                status['available_features'].extend(
                    self._get_features_for_package(package)
                )
        
        status['is_functional'] = len(status['missing_required']) == 0
        status['completeness'] = self._calculate_completeness(status)
        
        return status
    
    def _get_features_for_package(self, package: str) -> List[str]:
        """패키지가 제공하는 기능 목록"""
        features = {
            'psutil': ['고급 포트 스캔', '프로세스 정보', 'Docker 컨테이너 감지'],
            'PyYAML': ['Docker Compose 생성', 'YAML 설정 파일', '구조화된 설정'],
            'requests': ['웹 서비스 상태 확인', 'HTTP 헬스체크'],
            'click': ['CLI 인터페이스', '명령어 처리', '사용자 상호작용']
        }
        return features.get(package, [])
    
    def _calculate_completeness(self, status: Dict) -> float:
        """기능 완성도 계산 (0.0 ~ 1.0)"""
        total_packages = len(status['required']) + len(status['optional'])
        available_packages = (
            len([p for p in status['required'].values() if p]) +
            len([p for p in status['optional'].values() if p])
        )
        
        if total_packages == 0:
            return 1.0
        
        return available_packages / total_packages
    
    def install_missing_dependencies(self, group: str = 'minimal', 
                                   auto_install: bool = False) -> Dict:
        """누락된 의존성 설치 시도"""
        status = self.get_dependency_status(group)
        results = {
            'attempted': [],
            'successful': [],
            'failed': [],
            'skipped': []
        }
        
        missing_packages = status['missing_required']
        
        # 선택적 패키지도 포함 (advanced 이상 그룹)
        if group in ['advanced', 'docker', 'full']:
            missing_packages.extend(status['missing_optional'])
        
        for package in missing_packages:
            if not auto_install:
                results['skipped'].append({
                    'package': package,
                    'reason': 'auto_install=False'
                })
                continue
            
            try:
                results['attempted'].append(package)
                install_cmd = self.PACKAGE_ALTERNATIVES[package]['install_command']
                
                result = subprocess.run(
                    install_cmd.split(),
                    capture_output=True,
                    text=True,
                    timeout=60
                )
                
                if result.returncode == 0:
                    # 설치 후 재확인
                    if self._check_package(package):
                        self._available_packages[package] = True
                        results['successful'].append(package)
                    else:
                        results['failed'].append({
                            'package': package,
                            'error': '설치 후에도 import 실패'
                        })
                else:
                    results['failed'].append({
                        'package': package,
                        'error': result.stderr
                    })
                    
            except subprocess.TimeoutExpired:
                results['failed'].append({
                    'package': package,
                    'error': '설치 타임아웃'
                })
            except Exception as e:
                results['failed'].append({
                    'package': package,
                    'error': str(e)
                })
        
        return results
    
    def get_installation_guide(self, group: str = 'minimal') -> str:
        """설치 가이드 텍스트 생성"""
        status = self.get_dependency_status(group)
        
        if status['is_functional'] and status['completeness'] >= 0.8:
            return "✅ 모든 의존성이 충족되었습니다!"
        
        guide = []
        guide.append(f"📦 Universal Port Manager - {status['description']}")
        guide.append("=" * 50)
        
        # 필수 패키지
        if status['missing_required']:
            guide.append("\n❌ 누락된 필수 패키지:")
            for package in status['missing_required']:
                cmd = self.PACKAGE_ALTERNATIVES[package]['install_command']
                guide.append(f"  • {package}: {cmd}")
        
        # 선택적 패키지
        if status['missing_optional']:
            guide.append("\n⚠️  누락된 선택적 패키지:")
            for package in status['missing_optional']:
                cmd = self.PACKAGE_ALTERNATIVES[package]['install_command']
                desc = self.PACKAGE_ALTERNATIVES[package]['description']
                guide.append(f"  • {package} ({desc}): {cmd}")
                
                # 대안 기능 표시
                alternatives = self.PACKAGE_ALTERNATIVES[package]['alternatives']
                if alternatives:
                    guide.append(f"    대안: {', '.join(alternatives)}")
        
        # 설치 명령어 모음
        if status['missing_required'] or status['missing_optional']:
            all_missing = status['missing_required'] + status['missing_optional']
            all_commands = []
            for package in all_missing:
                cmd = self.PACKAGE_ALTERNATIVES[package]['install_command']
                all_commands.append(cmd.replace('pip install ', ''))
            
            guide.append(f"\n🚀 한 번에 설치:")
            guide.append(f"   pip install {' '.join(all_commands)}")
        
        # 그룹별 설치 옵션
        guide.append(f"\n📋 설치 옵션:")
        guide.append(f"   pip install universal-port-manager[minimal]  # 기본 기능만")
        guide.append(f"   pip install universal-port-manager[advanced] # 고급 기능")
        guide.append(f"   pip install universal-port-manager[full]     # 모든 기능")
        
        return "\n".join(guide)
    
    def create_dependency_report(self) -> Dict:
        """전체 의존성 보고서 생성"""
        report = {
            'timestamp': str(Path(__file__).stat().st_mtime),
            'python_version': sys.version,
            'groups': {}
        }
        
        for group_name in self.DEPENDENCY_GROUPS:
            report['groups'][group_name] = self.get_dependency_status(group_name)
        
        # 권장사항
        recommendations = []
        
        # 기본 기능이 동작하지 않는 경우
        minimal_status = report['groups']['minimal']
        if not minimal_status['is_functional']:
            recommendations.append({
                'priority': 'critical',
                'message': '기본 기능을 위해 click 패키지가 필요합니다.',
                'action': 'pip install click'
            })
        
        # 고급 기능 권장
        if minimal_status['is_functional']:
            advanced_status = report['groups']['advanced']
            if not advanced_status['optional'].get('psutil', False):
                recommendations.append({
                    'priority': 'recommended',
                    'message': '더 정확한 포트 스캔을 위해 psutil 설치를 권장합니다.',
                    'action': 'pip install psutil'
                })
            
            docker_status = report['groups']['docker']
            if not docker_status['optional'].get('PyYAML', False):
                recommendations.append({
                    'priority': 'recommended',
                    'message': 'Docker Compose 파일 생성을 위해 PyYAML 설치를 권장합니다.',
                    'action': 'pip install PyYAML'
                })
        
        report['recommendations'] = recommendations
        return report


def main():
    """의존성 관리자 CLI"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Universal Port Manager 의존성 관리')
    parser.add_argument('--group', default='minimal', 
                       choices=['minimal', 'advanced', 'docker', 'full'],
                       help='확인할 의존성 그룹')
    parser.add_argument('--install', action='store_true',
                       help='누락된 의존성 자동 설치 시도')
    parser.add_argument('--report', action='store_true',
                       help='전체 의존성 보고서 생성')
    
    args = parser.parse_args()
    
    dm = DependencyManager()
    
    if args.report:
        report = dm.create_dependency_report()
        import json
        print(json.dumps(report, indent=2, ensure_ascii=False))
    elif args.install:
        results = dm.install_missing_dependencies(args.group, auto_install=True)
        print(f"설치 시도: {len(results['attempted'])}개")
        print(f"성공: {len(results['successful'])}개")
        print(f"실패: {len(results['failed'])}개")
        if results['failed']:
            for fail in results['failed']:
                print(f"  - {fail['package']}: {fail['error']}")
    else:
        guide = dm.get_installation_guide(args.group)
        print(guide)


if __name__ == '__main__':
    main()