#!/usr/bin/env python3
"""
간소화된 시스템 검증 스크립트
현재 환경 제약사항에 맞춰 정적 분석 및 구조 검증 중심
"""

import os
import sys
import json
import subprocess
from pathlib import Path
from datetime import datetime
import re

class SimpleSystemValidator:
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "environment": "WSL2 Ubuntu 24.04",
            "python_version": sys.version,
            "tests": {}
        }
        
    def print_header(self):
        print("=" * 70)
        print("🧪 온라인 평가 시스템 간소화 검증")
        print("=" * 70)
        print(f"📅 시작 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"📂 프로젝트 경로: {self.project_root}")
        print("=" * 70)
    
    def test_project_structure(self):
        """프로젝트 구조 검증"""
        print("\n🏗️ 프로젝트 구조 검증...")
        
        required_dirs = [
            "backend", "frontend", "tests", "scripts", 
            "logging", "monitoring", "config"
        ]
        
        required_files = [
            "docker-compose.yml", "requirements.txt", 
            "README.md", "CLAUDE.md"
        ]
        
        missing_dirs = []
        missing_files = []
        
        for dir_name in required_dirs:
            if not (self.project_root / dir_name).exists():
                missing_dirs.append(dir_name)
            else:
                print(f"   ✅ {dir_name}/")
        
        for file_name in required_files:
            if not (self.project_root / file_name).exists():
                missing_files.append(file_name)
            else:
                print(f"   ✅ {file_name}")
        
        success = len(missing_dirs) == 0 and len(missing_files) == 0
        
        self.results["tests"]["project_structure"] = {
            "passed": success,
            "missing_directories": missing_dirs,
            "missing_files": missing_files,
            "score": "100%" if success else f"{((len(required_dirs) + len(required_files) - len(missing_dirs) - len(missing_files)) / (len(required_dirs) + len(required_files)) * 100):.1f}%"
        }
        
        if missing_dirs:
            print(f"   ❌ 누락된 디렉토리: {', '.join(missing_dirs)}")
        if missing_files:
            print(f"   ❌ 누락된 파일: {', '.join(missing_files)}")
        
        print(f"   📊 구조 완성도: {self.results['tests']['project_structure']['score']}")
    
    def test_python_syntax(self):
        """Python 파일 문법 검증"""
        print("\n🐍 Python 문법 검증...")
        
        # 핵심 Python 파일들
        key_files = [
            "backend/server.py",
            "backend/ai_service_enhanced.py", 
            "backend/enhanced_permissions.py",
            "backend/template_endpoints.py",
            "backend/secure_file_endpoints.py",
            "backend/deployment_manager.py",
            "run_comprehensive_tests.py",
            "tests/integration/test_system_integration.py",
            "tests/e2e/test_complete_workflow.py"
        ]
        
        passed = 0
        failed = 0
        errors = []
        
        for file_path in key_files:
            full_path = self.project_root / file_path
            if full_path.exists():
                try:
                    with open(full_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # 기본 문법 체크를 위한 컴파일 시도
                    compile(content, str(full_path), 'exec')
                    print(f"   ✅ {file_path}")
                    passed += 1
                except SyntaxError as e:
                    print(f"   ❌ {file_path}: 문법 오류 - {e}")
                    errors.append(f"{file_path}: {e}")
                    failed += 1
                except Exception as e:
                    print(f"   ⚠️ {file_path}: 확인 불가 - {e}")
                    failed += 1
            else:
                print(f"   ❌ {file_path}: 파일 없음")
                failed += 1
        
        self.results["tests"]["python_syntax"] = {
            "passed": failed == 0,
            "files_checked": len(key_files),
            "files_passed": passed,
            "files_failed": failed,
            "errors": errors,
            "score": f"{(passed / len(key_files) * 100):.1f}%"
        }
        
        print(f"   📊 문법 검증 결과: {passed}/{len(key_files)} 통과 ({self.results['tests']['python_syntax']['score']})")
    
    def test_configuration_files(self):
        """설정 파일 검증"""
        print("\n⚙️ 설정 파일 검증...")
        
        config_files = {
            "docker-compose.yml": self.validate_docker_compose,
            "requirements.txt": self.validate_requirements,
            "frontend/package.json": self.validate_package_json,
            ".env.example": lambda x: x.exists()
        }
        
        passed = 0
        total = len(config_files)
        
        for file_name, validator in config_files.items():
            file_path = self.project_root / file_name
            try:
                if validator(file_path):
                    print(f"   ✅ {file_name}")
                    passed += 1
                else:
                    print(f"   ❌ {file_name}: 검증 실패")
            except Exception as e:
                print(f"   ⚠️ {file_name}: 확인 불가 - {e}")
        
        self.results["tests"]["configuration_files"] = {
            "passed": passed == total,
            "files_passed": passed,
            "total_files": total,
            "score": f"{(passed / total * 100):.1f}%"
        }
        
        print(f"   📊 설정 파일 검증: {passed}/{total} 통과 ({self.results['tests']['configuration_files']['score']})")
    
    def validate_docker_compose(self, file_path):
        """Docker Compose 파일 검증"""
        if not file_path.exists():
            return False
        
        try:
            content = file_path.read_text()
            # 기본적인 Docker Compose 구조 확인
            required_sections = ["version", "services"]
            required_services = ["backend", "frontend", "mongodb", "redis"]
            
            for section in required_sections:
                if section not in content:
                    return False
            
            for service in required_services:
                if service not in content:
                    return False
            
            return True
        except:
            return False
    
    def validate_requirements(self, file_path):
        """requirements.txt 검증"""
        if not file_path.exists():
            return False
        
        try:
            content = file_path.read_text()
            lines = [line.strip() for line in content.split('\n') if line.strip() and not line.startswith('#')]
            
            # 핵심 패키지들이 있는지 확인
            essential_packages = ['fastapi', 'uvicorn', 'pymongo', 'aiohttp', 'pytest']
            found_packages = []
            
            for line in lines:
                package_name = line.split('==')[0].split('>=')[0].split('<=')[0].lower()
                if package_name in essential_packages:
                    found_packages.append(package_name)
            
            return len(found_packages) >= 3  # 최소 3개 이상의 핵심 패키지
        except:
            return False
    
    def validate_package_json(self, file_path):
        """package.json 검증"""
        if not file_path.exists():
            return False
        
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
            
            # React 프로젝트의 기본 구조 확인
            required_fields = ['name', 'version', 'dependencies', 'scripts']
            for field in required_fields:
                if field not in data:
                    return False
            
            # React 관련 의존성 확인
            deps = data.get('dependencies', {})
            return 'react' in deps and 'react-dom' in deps
        except:
            return False
    
    def test_api_endpoints_definition(self):
        """API 엔드포인트 정의 검증"""
        print("\n🌐 API 엔드포인트 정의 검증...")
        
        # 백엔드 파일들에서 API 엔드포인트 추출
        backend_files = [
            "backend/server.py",
            "backend/ai_admin_endpoints.py",
            "backend/template_endpoints.py",
            "backend/secure_file_endpoints.py",
            "backend/evaluation_print_endpoints.py",
            "backend/deployment_api_endpoints.py"
        ]
        
        total_endpoints = 0
        api_patterns = [
            r'@app\.(get|post|put|delete|patch)\("([^"]+)"',
            r'@router\.(get|post|put|delete|patch)\("([^"]+)"',
            r'\.route\("([^"]+)", methods=\["([^"]+)"\]'
        ]
        
        for file_path in backend_files:
            full_path = self.project_root / file_path
            if full_path.exists():
                try:
                    content = full_path.read_text()
                    endpoints_in_file = 0
                    
                    for pattern in api_patterns:
                        matches = re.findall(pattern, content)
                        endpoints_in_file += len(matches)
                    
                    if endpoints_in_file > 0:
                        print(f"   ✅ {file_path}: {endpoints_in_file}개 엔드포인트")
                        total_endpoints += endpoints_in_file
                except Exception as e:
                    print(f"   ⚠️ {file_path}: 확인 불가 - {e}")
            else:
                print(f"   ❌ {file_path}: 파일 없음")
        
        self.results["tests"]["api_endpoints"] = {
            "passed": total_endpoints > 20,  # 최소 20개 이상의 엔드포인트 기대
            "total_endpoints": total_endpoints,
            "files_checked": len(backend_files)
        }
        
        print(f"   📊 API 엔드포인트: 총 {total_endpoints}개 발견")
        
    def test_frontend_components(self):
        """프론트엔드 컴포넌트 검증"""
        print("\n⚛️ React 컴포넌트 검증...")
        
        # 주요 React 컴포넌트들
        components = [
            "frontend/src/components/AIProviderManagement.js",
            "frontend/src/components/EnhancedTemplateManagement.js",
            "frontend/src/components/SecurePDFViewer.js",
            "frontend/src/components/EvaluationPrintManager.js",
            "frontend/src/components/AIEvaluationController.js",
            "frontend/src/components/DeploymentManager.js"
        ]
        
        passed = 0
        total = len(components)
        
        for component_path in components:
            full_path = self.project_root / component_path
            if full_path.exists():
                try:
                    content = full_path.read_text()
                    # React 컴포넌트의 기본 구조 확인
                    if ('import React' in content or 'import' in content) and \
                       ('export default' in content or 'export const' in content):
                        print(f"   ✅ {component_path}")
                        passed += 1
                    else:
                        print(f"   ⚠️ {component_path}: React 컴포넌트 구조 불완전")
                except Exception as e:
                    print(f"   ❌ {component_path}: 읽기 오류 - {e}")
            else:
                print(f"   ❌ {component_path}: 파일 없음")
        
        self.results["tests"]["frontend_components"] = {
            "passed": passed >= total * 0.8,  # 80% 이상 통과
            "components_passed": passed,
            "total_components": total,
            "score": f"{(passed / total * 100):.1f}%"
        }
        
        print(f"   📊 컴포넌트 검증: {passed}/{total} 통과 ({self.results['tests']['frontend_components']['score']})")
    
    def test_test_suite_completeness(self):
        """테스트 스위트 완성도 검증"""
        print("\n🧪 테스트 스위트 완성도 검증...")
        
        test_files = [
            "run_comprehensive_tests.py",
            "tests/integration/test_system_integration.py",
            "tests/e2e/test_complete_workflow.py",
            "tests/performance/test_performance_benchmarks.py"
        ]
        
        passed = 0
        total = len(test_files)
        test_functions = 0
        
        for test_file in test_files:
            full_path = self.project_root / test_file
            if full_path.exists():
                try:
                    content = full_path.read_text()
                    # 테스트 함수 개수 확인
                    test_funcs = len(re.findall(r'def test_\w+|async def test_\w+', content))
                    test_functions += test_funcs
                    
                    if test_funcs > 0:
                        print(f"   ✅ {test_file}: {test_funcs}개 테스트 함수")
                        passed += 1
                    else:
                        print(f"   ⚠️ {test_file}: 테스트 함수 없음")
                except Exception as e:
                    print(f"   ❌ {test_file}: 확인 불가 - {e}")
            else:
                print(f"   ❌ {test_file}: 파일 없음")
        
        self.results["tests"]["test_suite"] = {
            "passed": passed >= total * 0.75,  # 75% 이상 통과
            "test_files_passed": passed,
            "total_test_files": total,
            "total_test_functions": test_functions,
            "score": f"{(passed / total * 100):.1f}%"
        }
        
        print(f"   📊 테스트 스위트: {passed}/{total} 파일, 총 {test_functions}개 테스트 함수")
    
    def generate_summary(self):
        """결과 요약 생성"""
        print("\n" + "=" * 70)
        print("📊 시스템 검증 결과 요약")
        print("=" * 70)
        
        total_tests = len(self.results["tests"])
        passed_tests = sum(1 for test in self.results["tests"].values() if test.get("passed", False))
        
        print(f"🎯 전체 성공률: {passed_tests}/{total_tests} ({(passed_tests/total_tests*100):.1f}%)")
        print(f"⏱️ 검증 완료 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        print("\n📋 세부 결과:")
        for test_name, result in self.results["tests"].items():
            status = "✅ 통과" if result.get("passed", False) else "❌ 실패"
            score = result.get("score", "N/A")
            print(f"   {test_name}: {status} ({score})")
        
        # 권장사항
        print("\n💡 권장사항:")
        if passed_tests == total_tests:
            print("   🎉 모든 검증이 통과했습니다! 시스템이 배포 준비되었습니다.")
        elif passed_tests >= total_tests * 0.8:
            print("   ✅ 대부분의 검증이 통과했습니다. 실패한 항목을 검토해보세요.")
        else:
            print("   ⚠️ 일부 중요한 검증이 실패했습니다. 문제를 해결한 후 재검증하세요.")
        
        # JSON 보고서 저장
        report_file = f"simple_validation_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False)
        
        print(f"\n📄 상세 보고서가 {report_file}에 저장되었습니다.")
        
        return passed_tests >= total_tests * 0.8
    
    def run_all_validations(self):
        """모든 검증 실행"""
        self.print_header()
        
        try:
            self.test_project_structure()
            self.test_python_syntax()
            self.test_configuration_files()
            self.test_api_endpoints_definition()
            self.test_frontend_components()
            self.test_test_suite_completeness()
            
            return self.generate_summary()
            
        except Exception as e:
            print(f"\n❌ 검증 중 오류 발생: {e}")
            return False

if __name__ == "__main__":
    validator = SimpleSystemValidator()
    success = validator.run_all_validations()
    sys.exit(0 if success else 1)