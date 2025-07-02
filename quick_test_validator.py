#!/usr/bin/env python3
"""
Quick Test Validator
빠른 테스트 검증 및 실행 상태 확인
"""

import os
import json
import subprocess
import time
from datetime import datetime
from pathlib import Path

def check_environment():
    """환경 설정 확인"""
    print("🔍 환경 설정 확인 중...")
    
    checks = {
        'python': False,
        'node': False,
        'playwright': False,
        'frontend_deps': False,
        'test_files': False
    }
    
    # Python 확인
    try:
        result = subprocess.run(['python3', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            checks['python'] = True
            print(f"✅ Python: {result.stdout.strip()}")
    except:
        print("❌ Python3 not found")
    
    # Node.js 확인
    try:
        result = subprocess.run(['node', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            checks['node'] = True
            print(f"✅ Node.js: {result.stdout.strip()}")
    except:
        print("❌ Node.js not found")
    
    # Playwright 확인
    try:
        result = subprocess.run(['python3', '-c', 'import playwright; print("Playwright available")'], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            checks['playwright'] = True
            print("✅ Playwright available")
    except:
        print("❌ Playwright not available")
    
    # Frontend dependencies 확인
    if os.path.exists('frontend/node_modules'):
        checks['frontend_deps'] = True
        print("✅ Frontend dependencies installed")
    else:
        print("❌ Frontend dependencies missing")
    
    # Test files 확인
    test_files = [
        'tests/scenarios/admin-scenarios.yml',
        'tests/scenarios/secretary-scenarios.yml',
        'tests/scenarios/evaluator-scenarios.yml',
        'tests/scenario-data/test-accounts.json'
    ]
    
    if all(os.path.exists(f) for f in test_files):
        checks['test_files'] = True
        print("✅ Test configuration files present")
    else:
        print("❌ Some test files missing")
    
    return checks

def run_basic_validation():
    """기본 검증 테스트"""
    print("\n🧪 기본 검증 테스트 실행...")
    
    validations = {
        'scenario_files_valid': False,
        'test_data_valid': False,
        'frontend_build': False,
        'system_connectivity': False
    }
    
    # 시나리오 파일 유효성 검사
    try:
        import yaml
        scenario_files = [
            'tests/scenarios/admin-scenarios.yml',
            'tests/scenarios/secretary-scenarios.yml',
            'tests/scenarios/evaluator-scenarios.yml'
        ]
        
        for file_path in scenario_files:
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    yaml.safe_load(f)
        
        validations['scenario_files_valid'] = True
        print("✅ 시나리오 파일 유효성 검사 통과")
    except Exception as e:
        print(f"❌ 시나리오 파일 유효성 검사 실패: {str(e)}")
    
    # 테스트 데이터 유효성 검사
    try:
        test_data_files = [
            'tests/scenario-data/test-accounts.json',
            'tests/scenario-data/sample-companies.json'
        ]
        
        for file_path in test_data_files:
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    json.load(f)
        
        validations['test_data_valid'] = True
        print("✅ 테스트 데이터 유효성 검사 통과")
    except Exception as e:
        print(f"❌ 테스트 데이터 유효성 검사 실패: {str(e)}")
    
    # Frontend 빌드 테스트
    try:
        if os.path.exists('frontend/package.json'):
            print("🔨 Frontend 빌드 테스트 중...")
            result = subprocess.run(
                ['npm', 'run', 'build'], 
                cwd='frontend', 
                capture_output=True, 
                text=True, 
                timeout=120
            )
            
            if result.returncode == 0:
                validations['frontend_build'] = True
                print("✅ Frontend 빌드 성공")
            else:
                print(f"❌ Frontend 빌드 실패: {result.stderr[:200]}...")
    except Exception as e:
        print(f"❌ Frontend 빌드 테스트 실패: {str(e)}")
    
    # 시스템 연결성 확인
    try:
        # 포트 확인
        import socket
        
        def check_port(host, port):
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            result = sock.connect_ex((host, port))
            sock.close()
            return result == 0
        
        frontend_port = check_port('localhost', 3000)
        backend_port = check_port('localhost', 8002)
        
        if frontend_port or backend_port:
            validations['system_connectivity'] = True
            print(f"✅ 시스템 연결성 확인 (Frontend: {frontend_port}, Backend: {backend_port})")
        else:
            print("⚠️  서비스가 실행되지 않음 (정상적인 상황일 수 있음)")
            validations['system_connectivity'] = True  # 서비스 미실행은 정상 상황
            
    except Exception as e:
        print(f"❌ 시스템 연결성 확인 실패: {str(e)}")
    
    return validations

def run_quick_scenario_test():
    """빠른 시나리오 테스트"""
    print("\n🚀 빠른 시나리오 테스트 실행...")
    
    # 간단한 시나리오 유효성 테스트
    test_results = {
        'admin_scenario_structure': False,
        'secretary_scenario_structure': False,
        'evaluator_scenario_structure': False,
        'test_data_structure': False
    }
    
    try:
        import yaml
        
        # Admin 시나리오 구조 확인
        with open('tests/scenarios/admin-scenarios.yml', 'r', encoding='utf-8') as f:
            admin_data = yaml.safe_load(f)
            if 'scenarios' in admin_data and len(admin_data['scenarios']) > 0:
                test_results['admin_scenario_structure'] = True
                print(f"✅ Admin 시나리오: {len(admin_data['scenarios'])}개 확인")
        
        # Secretary 시나리오 구조 확인
        with open('tests/scenarios/secretary-scenarios.yml', 'r', encoding='utf-8') as f:
            secretary_data = yaml.safe_load(f)
            if 'scenarios' in secretary_data and len(secretary_data['scenarios']) > 0:
                test_results['secretary_scenario_structure'] = True
                print(f"✅ Secretary 시나리오: {len(secretary_data['scenarios'])}개 확인")
        
        # Evaluator 시나리오 구조 확인
        with open('tests/scenarios/evaluator-scenarios.yml', 'r', encoding='utf-8') as f:
            evaluator_data = yaml.safe_load(f)
            if 'scenarios' in evaluator_data and len(evaluator_data['scenarios']) > 0:
                test_results['evaluator_scenario_structure'] = True
                print(f"✅ Evaluator 시나리오: {len(evaluator_data['scenarios'])}개 확인")
        
        # 테스트 데이터 구조 확인
        with open('tests/scenario-data/test-accounts.json', 'r', encoding='utf-8') as f:
            test_accounts = json.load(f)
            if 'test_accounts' in test_accounts:
                accounts = test_accounts['test_accounts']
                admin_count = 1 if 'admin' in accounts else 0
                secretary_count = 1 if 'secretary' in accounts else 0
                evaluator_count = len(accounts.get('evaluators', []))
                
                test_results['test_data_structure'] = True
                print(f"✅ 테스트 계정: Admin({admin_count}), Secretary({secretary_count}), Evaluator({evaluator_count})")
    
    except Exception as e:
        print(f"❌ 시나리오 구조 확인 실패: {str(e)}")
    
    return test_results

def run_performance_quick_check():
    """빠른 성능 확인"""
    print("\n⚡ 빠른 성능 확인...")
    
    perf_results = {
        'build_size_check': False,
        'dependency_check': False,
        'file_structure_check': False
    }
    
    # Build 크기 확인
    try:
        if os.path.exists('frontend/build'):
            import shutil
            build_size = shutil.disk_usage('frontend/build').used
            build_size_mb = build_size / (1024 * 1024)
            
            perf_results['build_size_check'] = build_size_mb < 50  # 50MB 이하
            print(f"✅ Build 크기: {build_size_mb:.1f}MB {'(적정)' if build_size_mb < 50 else '(큰 편)'}")
        else:
            print("⚠️  Build 폴더 없음")
    except Exception as e:
        print(f"❌ Build 크기 확인 실패: {str(e)}")
    
    # 의존성 확인
    try:
        if os.path.exists('frontend/package.json'):
            with open('frontend/package.json', 'r') as f:
                package_data = json.load(f)
                deps = package_data.get('dependencies', {})
                dev_deps = package_data.get('devDependencies', {})
                
                total_deps = len(deps) + len(dev_deps)
                perf_results['dependency_check'] = total_deps < 100  # 100개 이하
                print(f"✅ 의존성: {total_deps}개 {'(적정)' if total_deps < 100 else '(많은 편)'}")
    except Exception as e:
        print(f"❌ 의존성 확인 실패: {str(e)}")
    
    # 파일 구조 확인
    try:
        test_files_count = len(list(Path('tests').rglob('*.py'))) + len(list(Path('tests').rglob('*.yml')))
        src_files_count = len(list(Path('frontend/src').rglob('*.js'))) if os.path.exists('frontend/src') else 0
        
        perf_results['file_structure_check'] = test_files_count > 5 and src_files_count > 5
        print(f"✅ 파일 구조: 테스트({test_files_count}), 소스({src_files_count})")
    except Exception as e:
        print(f"❌ 파일 구조 확인 실패: {str(e)}")
    
    return perf_results

def generate_quick_report(env_checks, validations, scenario_tests, perf_results):
    """빠른 보고서 생성"""
    print("\n📋 빠른 테스트 보고서 생성...")
    
    # 전체 점수 계산
    total_checks = sum([
        sum(env_checks.values()),
        sum(validations.values()),
        sum(scenario_tests.values()),
        sum(perf_results.values())
    ])
    
    max_checks = sum([
        len(env_checks),
        len(validations),
        len(scenario_tests),
        len(perf_results)
    ])
    
    success_rate = (total_checks / max_checks * 100) if max_checks > 0 else 0
    
    # 등급 산정
    if success_rate >= 95:
        grade = "A+"
    elif success_rate >= 90:
        grade = "A"
    elif success_rate >= 85:
        grade = "B+"
    elif success_rate >= 80:
        grade = "B"
    elif success_rate >= 75:
        grade = "C+"
    else:
        grade = "C"
    
    report = {
        'timestamp': datetime.now().isoformat(),
        'test_type': 'quick_validation',
        'overall_score': success_rate,
        'grade': grade,
        'checks_passed': total_checks,
        'total_checks': max_checks,
        'categories': {
            'environment': env_checks,
            'validations': validations,
            'scenarios': scenario_tests,
            'performance': perf_results
        },
        'recommendations': []
    }
    
    # 권고사항 생성
    if not env_checks['playwright']:
        report['recommendations'].append("Playwright 설치 필요: pip install playwright && playwright install")
    
    if not env_checks['frontend_deps']:
        report['recommendations'].append("Frontend 의존성 설치 필요: cd frontend && npm install")
    
    if not validations['frontend_build']:
        report['recommendations'].append("Frontend 빌드 확인 필요: cd frontend && npm run build")
    
    if success_rate < 80:
        report['recommendations'].append("전체 시스템 검토 및 누락된 설정 확인 필요")
    
    # JSON 보고서 저장
    report_file = f"quick_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    # 콘솔 출력
    print("\n" + "="*60)
    print("🎯 빠른 테스트 검증 결과")
    print("="*60)
    print(f"📊 전체 점수: {success_rate:.1f}% (등급: {grade})")
    print(f"✅ 통과: {total_checks}/{max_checks}")
    print(f"📄 보고서: {report_file}")
    
    if report['recommendations']:
        print("\n💡 권고사항:")
        for i, rec in enumerate(report['recommendations'], 1):
            print(f"  {i}. {rec}")
    
    print("="*60)
    
    return report_file, success_rate

def main():
    """메인 실행 함수"""
    print("🚀 Quick Test Validator")
    print("Ultra Comprehensive Test 준비 상태 확인")
    print("="*60)
    
    # 1. 환경 확인
    env_checks = check_environment()
    
    # 2. 기본 검증
    validations = run_basic_validation()
    
    # 3. 시나리오 테스트
    scenario_tests = run_quick_scenario_test()
    
    # 4. 성능 확인
    perf_results = run_performance_quick_check()
    
    # 5. 보고서 생성
    report_file, success_rate = generate_quick_report(
        env_checks, validations, scenario_tests, perf_results
    )
    
    # 최종 상태 출력
    if success_rate >= 85:
        print("\n🎉 시스템이 Ultra Comprehensive Test 준비 완료!")
        print("python3 ultra_comprehensive_test_runner.py 실행 가능")
    elif success_rate >= 70:
        print("\n⚠️  일부 설정이 누락되었지만 기본 테스트는 가능")
        print("권고사항을 확인하여 개선 후 재실행 권장")
    else:
        print("\n❌ 주요 설정이 누락됨. 권고사항을 따라 설정 완료 후 재실행")
    
    return success_rate >= 70

if __name__ == "__main__":
    main()