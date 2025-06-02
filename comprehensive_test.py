#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
온라인 평가 시스템 종합 테스트 스크립트
모든 주요 기능에 대한 포괄적인 테스트를 수행합니다.
"""

import requests
import json
import time
import os
import sys
from pathlib import Path

# 테스트 설정
BASE_URL = "http://localhost:8000"
TEST_RESULTS = []

def log_test(test_name, success, message=""):
    """테스트 결과 로깅"""
    status = "✅ 성공" if success else "❌ 실패"
    result = f"{status} | {test_name}"
    if message:
        result += f" | {message}"
    print(result)
    TEST_RESULTS.append({
        "test": test_name,
        "success": success,
        "message": message
    })

def test_server_connection():
    """서버 연결 테스트"""
    try:
        response = requests.get(f"{BASE_URL}/", timeout=5)
        log_test("서버 연결", response.status_code == 200, f"응답 코드: {response.status_code}")
        return True
    except Exception as e:
        log_test("서버 연결", False, f"오류: {str(e)}")
        return False

def test_api_documentation():
    """API 문서 접근 테스트"""
    try:
        response = requests.get(f"{BASE_URL}/docs", timeout=5)
        log_test("API 문서 접근", response.status_code == 200, "Swagger UI 접근 가능")
        return True
    except Exception as e:
        log_test("API 문서 접근", False, f"오류: {str(e)}")
        return False

def test_user_registration():
    """사용자 등록 테스트"""
    try:
        test_user = {
            "username": "test_user_comprehensive",
            "email": "test_comprehensive@example.com",
            "password": "testpass123",
            "role": "evaluator",
            "company": "테스트 회사"
        }
        
        response = requests.post(f"{BASE_URL}/api/register", json=test_user, timeout=10)
        success = response.status_code in [200, 201, 400]  # 400은 이미 존재하는 경우
        
        if response.status_code == 400:
            message = "사용자가 이미 존재함 (정상)"
        else:
            message = f"응답 코드: {response.status_code}"
            
        log_test("사용자 등록", success, message)
        return success
    except Exception as e:
        log_test("사용자 등록", False, f"오류: {str(e)}")
        return False

def test_user_login():
    """사용자 로그인 테스트"""
    try:
        login_data = {
            "username": "test_user_comprehensive",
            "password": "testpass123"
        }
        
        response = requests.post(f"{BASE_URL}/api/login", json=login_data, timeout=10)
        success = response.status_code == 200
        
        if success:
            data = response.json()
            token = data.get("access_token")
            log_test("사용자 로그인", True, "토큰 발급 성공")
            return token
        else:
            log_test("사용자 로그인", False, f"응답 코드: {response.status_code}")
            return None
    except Exception as e:
        log_test("사용자 로그인", False, f"오류: {str(e)}")
        return None

def test_templates_api(token):
    """템플릿 API 테스트"""
    if not token:
        log_test("템플릿 API", False, "토큰이 없음")
        return False
        
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        # 템플릿 목록 조회
        response = requests.get(f"{BASE_URL}/api/templates", headers=headers, timeout=10)
        log_test("템플릿 목록 조회", response.status_code == 200, f"응답 코드: {response.status_code}")
        
        # 새 템플릿 생성 테스트
        new_template = {
            "name": "종합 테스트 템플릿",
            "description": "자동 테스트용 템플릿",
            "criteria": [
                {
                    "name": "기술적 역량",
                    "description": "기술적 능력 평가",
                    "weight": 40,
                    "max_score": 5
                },
                {
                    "name": "커뮤니케이션",
                    "description": "의사소통 능력",
                    "weight": 30,
                    "max_score": 5
                }
            ]
        }
        
        response = requests.post(f"{BASE_URL}/api/templates", json=new_template, headers=headers, timeout=10)
        template_created = response.status_code in [200, 201]
        log_test("템플릿 생성", template_created, f"응답 코드: {response.status_code}")
        
        return template_created
    except Exception as e:
        log_test("템플릿 API", False, f"오류: {str(e)}")
        return False

def test_evaluations_api(token):
    """평가 API 테스트"""
    if not token:
        log_test("평가 API", False, "토큰이 없음")
        return False
        
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        # 평가 목록 조회
        response = requests.get(f"{BASE_URL}/api/evaluations", headers=headers, timeout=10)
        log_test("평가 목록 조회", response.status_code == 200, f"응답 코드: {response.status_code}")
        
        # 평가 할당 목록 조회
        response = requests.get(f"{BASE_URL}/api/evaluation-assignments", headers=headers, timeout=10)
        log_test("평가 할당 조회", response.status_code == 200, f"응답 코드: {response.status_code}")
        
        return True
    except Exception as e:
        log_test("평가 API", False, f"오류: {str(e)}")
        return False

def test_analytics_api(token):
    """분석 API 테스트"""
    if not token:
        log_test("분석 API", False, "토큰이 없음")
        return False
        
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        # 대시보드 데이터 조회
        response = requests.get(f"{BASE_URL}/api/analytics/dashboard", headers=headers, timeout=10)
        log_test("대시보드 분석", response.status_code == 200, f"응답 코드: {response.status_code}")
        
        # 진행 상황 통계 조회
        response = requests.get(f"{BASE_URL}/api/analytics/progress", headers=headers, timeout=10)
        log_test("진행 상황 분석", response.status_code == 200, f"응답 코드: {response.status_code}")
        
        return True
    except Exception as e:
        log_test("분석 API", False, f"오류: {str(e)}")
        return False

def test_export_functionality(token):
    """내보내기 기능 테스트"""
    if not token:
        log_test("내보내기 기능", False, "토큰이 없음")
        return False
        
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        # 내보내기 가능한 평가 목록 조회
        response = requests.get(f"{BASE_URL}/api/evaluations/export-list", headers=headers, timeout=10)
        export_list_success = response.status_code == 200
        log_test("내보내기 목록 조회", export_list_success, f"응답 코드: {response.status_code}")
        
        if export_list_success and response.json():
            evaluations = response.json()
            if evaluations:
                # 첫 번째 평가로 개별 내보내기 테스트
                eval_id = evaluations[0]["id"]
                
                # PDF 내보내기 테스트
                response = requests.get(
                    f"{BASE_URL}/api/evaluations/{eval_id}/export",
                    headers=headers,
                    params={"format": "pdf"},
                    timeout=30
                )
                log_test("PDF 내보내기", response.status_code == 200, f"응답 코드: {response.status_code}")
                
                # Excel 내보내기 테스트
                response = requests.get(
                    f"{BASE_URL}/api/evaluations/{eval_id}/export",
                    headers=headers,
                    params={"format": "excel"},
                    timeout=30
                )
                log_test("Excel 내보내기", response.status_code == 200, f"응답 코드: {response.status_code}")
            else:
                log_test("개별 내보내기 테스트", False, "내보내기 가능한 평가가 없음")
        
        # 대량 내보내기 테스트
        bulk_export_data = {
            "evaluation_ids": [],  # 빈 배열로 테스트
            "format": "excel",
            "export_type": "individual"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/evaluations/bulk-export",
            json=bulk_export_data,
            headers=headers,
            timeout=30
        )
        log_test("대량 내보내기", response.status_code in [200, 400], f"응답 코드: {response.status_code}")
        
        return True
    except Exception as e:
        log_test("내보내기 기능", False, f"오류: {str(e)}")
        return False

def test_export_utils_module():
    """내보내기 유틸리티 모듈 테스트"""
    try:
        # 내보내기 모듈 파일 존재 확인
        export_utils_path = Path("backend/export_utils.py")
        if export_utils_path.exists():
            log_test("내보내기 모듈 파일", True, "export_utils.py 파일 존재")
            
            # 모듈 import 테스트
            sys.path.append("backend")
            try:
                import export_utils
                log_test("내보내기 모듈 Import", True, "모듈 import 성공")
                
                # EvaluationExporter 클래스 존재 확인
                if hasattr(export_utils, 'EvaluationExporter'):
                    log_test("EvaluationExporter 클래스", True, "클래스 존재 확인")
                    
                    # 인스턴스 생성 테스트
                    exporter = export_utils.EvaluationExporter()
                    log_test("Exporter 인스턴스 생성", True, "인스턴스 생성 성공")
                    
                else:
                    log_test("EvaluationExporter 클래스", False, "클래스가 존재하지 않음")
                    
            except ImportError as e:
                log_test("내보내기 모듈 Import", False, f"Import 오류: {str(e)}")
                
        else:
            log_test("내보내기 모듈 파일", False, "export_utils.py 파일이 존재하지 않음")
            
        return True
    except Exception as e:
        log_test("내보내기 모듈 테스트", False, f"오류: {str(e)}")
        return False

def test_frontend_files():
    """프론트엔드 파일 존재 확인"""
    try:
        frontend_files = [
            "frontend/package.json",
            "frontend/src/App.js",
            "frontend/src/index.js",
            "frontend/public/index.html"
        ]
        
        all_exist = True
        for file_path in frontend_files:
            exists = Path(file_path).exists()
            log_test(f"프론트엔드 파일: {file_path}", exists, "파일 존재" if exists else "파일 없음")
            if not exists:
                all_exist = False
                
        return all_exist
    except Exception as e:
        log_test("프론트엔드 파일 확인", False, f"오류: {str(e)}")
        return False

def test_dependencies():
    """의존성 패키지 확인"""
    try:
        # requirements.txt 파일 확인
        backend_req_path = Path("backend/requirements.txt")
        if backend_req_path.exists():
            with open(backend_req_path, 'r', encoding='utf-8') as f:
                requirements = f.read()
                
            required_packages = ["fastapi", "reportlab", "openpyxl", "xlsxwriter", "pandas"]
            missing_packages = []
            
            for package in required_packages:
                if package not in requirements.lower():
                    missing_packages.append(package)
            
            if not missing_packages:
                log_test("필수 패키지 확인", True, "모든 필수 패키지가 requirements.txt에 포함됨")
            else:
                log_test("필수 패키지 확인", False, f"누락된 패키지: {', '.join(missing_packages)}")
                
        else:
            log_test("requirements.txt 확인", False, "backend/requirements.txt 파일이 존재하지 않음")
            
        # package.json 확인
        package_json_path = Path("frontend/package.json")
        if package_json_path.exists():
            log_test("package.json 확인", True, "frontend/package.json 파일 존재")
        else:
            log_test("package.json 확인", False, "frontend/package.json 파일이 존재하지 않음")
            
        return True
    except Exception as e:
        log_test("의존성 확인", False, f"오류: {str(e)}")
        return False

def generate_test_report():
    """테스트 결과 보고서 생성"""
    total_tests = len(TEST_RESULTS)
    passed_tests = sum(1 for result in TEST_RESULTS if result["success"])
    failed_tests = total_tests - passed_tests
    
    success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
    
    report = f"""
=== 온라인 평가 시스템 종합 테스트 결과 ===

📊 테스트 요약:
- 총 테스트: {total_tests}개
- 성공: {passed_tests}개
- 실패: {failed_tests}개
- 성공률: {success_rate:.1f}%

📋 상세 결과:
"""
    
    for result in TEST_RESULTS:
        status = "✅" if result["success"] else "❌"
        report += f"{status} {result['test']}"
        if result["message"]:
            report += f" - {result['message']}"
        report += "\n"
    
    report += f"""
🎯 종합 평가:
"""
    
    if success_rate >= 90:
        report += "🌟 우수: 시스템이 매우 안정적으로 작동합니다."
    elif success_rate >= 75:
        report += "👍 양호: 시스템이 대체로 잘 작동하지만 일부 개선이 필요합니다."
    elif success_rate >= 50:
        report += "⚠️ 보통: 시스템에 몇 가지 문제가 있어 주의가 필요합니다."
    else:
        report += "🚨 주의: 시스템에 심각한 문제가 있어 즉시 점검이 필요합니다."
    
    return report

def main():
    """메인 테스트 실행"""
    print("🔍 온라인 평가 시스템 종합 테스트 시작\n")
    
    # 1. 서버 연결 테스트
    print("1️⃣ 서버 연결 테스트")
    if not test_server_connection():
        print("❌ 서버가 실행되지 않았습니다. 테스트를 중단합니다.")
        return
    
    # 2. API 문서 테스트
    print("\n2️⃣ API 문서 테스트")
    test_api_documentation()
    
    # 3. 파일 시스템 테스트
    print("\n3️⃣ 파일 시스템 테스트")
    test_frontend_files()
    test_export_utils_module()
    test_dependencies()
    
    # 4. 사용자 인증 테스트
    print("\n4️⃣ 사용자 인증 테스트")
    test_user_registration()
    token = test_user_login()
    
    # 5. API 기능 테스트
    print("\n5️⃣ API 기능 테스트")
    test_templates_api(token)
    test_evaluations_api(token)
    test_analytics_api(token)
    
    # 6. 내보내기 기능 테스트
    print("\n6️⃣ 내보내기 기능 테스트")
    test_export_functionality(token)
    
    # 7. 테스트 결과 보고서 생성
    print("\n" + "="*50)
    report = generate_test_report()
    print(report)
    
    # 보고서를 파일로 저장
    try:
        with open("comprehensive_test_report.md", "w", encoding="utf-8") as f:
            f.write(report)
        print(f"\n📄 상세 테스트 보고서가 'comprehensive_test_report.md'에 저장되었습니다.")
    except Exception as e:
        print(f"\n❌ 보고서 저장 실패: {str(e)}")

if __name__ == "__main__":
    main()
