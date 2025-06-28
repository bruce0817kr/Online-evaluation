#!/usr/bin/env python3
"""
Project Management UI Improvements Verification Test
테스트: 프로젝트 관리 UI 개선 (불필요한 필드 제거) 확인
"""

import re
import os
from pathlib import Path

def test_project_ui_improvements():
    """프로젝트 관리 UI 개선사항 검증"""
    
    print("=== 프로젝트 관리 UI 개선사항 검증 ===")
    
    # App.js 파일 경로
    app_js_path = Path("/mnt/c/project/Online-evaluation/frontend/src/App.js")
    
    if not app_js_path.exists():
        print("❌ App.js 파일을 찾을 수 없습니다.")
        return False
    
    with open(app_js_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    tests_passed = 0
    tests_failed = 0
    
    def log_test(test_name, passed, details=""):
        nonlocal tests_passed, tests_failed
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status} {test_name}")
        if details:
            print(f"     {details}")
        if passed:
            tests_passed += 1
        else:
            tests_failed += 1
    
    print(f"\n1. 프로젝트 Form State 검증")
    
    # formData state가 단순화되었는지 확인
    simplified_form_pattern = r"formData.*setState.*{\s*name:\s*'',\s*description:\s*'',\s*deadline:\s*''\s*}"
    if re.search(simplified_form_pattern, content):
        log_test("FormData 상태 단순화", True, "name, description, deadline만 포함")
    else:
        log_test("FormData 상태 단순화", False, "여전히 불필요한 필드가 포함되어 있음")
    
    # 제거된 필드들이 더 이상 없는지 확인
    removed_fields = ['status', 'start_date', 'end_date', 'budget']
    all_removed = True
    for field in removed_fields:
        field_pattern = f"formData\\.{field}|{field}:\s*''"
        if re.search(field_pattern, content):
            log_test(f"불필요한 필드 제거 ({field})", False, f"{field} 필드가 여전히 존재함")
            all_removed = False
    
    if all_removed:
        log_test("모든 불필요한 필드 제거", True, "status, start_date, end_date, budget 필드 제거됨")
    
    print(f"\n2. 프로젝트 Form UI 검증")
    
    # 마감일 필드가 추가되었는지 확인
    deadline_field_pattern = r'<input[^>]*type="date"[^>]*value=\{formData\.deadline\}'
    if re.search(deadline_field_pattern, content):
        log_test("마감일 필드 추가", True, "date 타입의 deadline 입력 필드 존재")
    else:
        log_test("마감일 필드 추가", False, "마감일 입력 필드를 찾을 수 없음")
    
    # 제거된 form 필드들이 없는지 확인
    removed_form_elements = [
        (r'예산.*\(원\)', "예산 필드"),
        (r'상태.*<select', "상태 선택 필드"),
        (r'시작일.*type="date"', "시작일 필드"),
        (r'종료일.*type="date"', "종료일 필드")
    ]
    
    for pattern, field_name in removed_form_elements:
        if not re.search(pattern, content):
            log_test(f"{field_name} 제거", True, f"{field_name}가 form에서 제거됨")
        else:
            log_test(f"{field_name} 제거", False, f"{field_name}가 여전히 존재함")
    
    print(f"\n3. 프로젝트 테이블 구조 검증")
    
    # 테이블 헤더가 단순화되었는지 확인
    simplified_headers = ["프로젝트명", "마감일", "생성일", "작업"]
    header_pattern = r'<th[^>]*>([^<]+)</th>'
    headers = re.findall(header_pattern, content)
    
    if len(headers) >= 4:
        actual_headers = [h.strip() for h in headers[-4:]]  # 마지막 4개 헤더 확인
        if actual_headers == simplified_headers:
            log_test("테이블 헤더 단순화", True, f"헤더: {', '.join(actual_headers)}")
        else:
            log_test("테이블 헤더 단순화", False, f"예상: {simplified_headers}, 실제: {actual_headers}")
    else:
        log_test("테이블 헤더 구조", False, "충분한 테이블 헤더를 찾을 수 없음")
    
    # colSpan이 4로 업데이트되었는지 확인 (6개 열에서 4개 열로 변경)
    colspan_pattern = r'colSpan="4"'
    if re.search(colspan_pattern, content):
        log_test("Table ColSpan 업데이트", True, "colSpan이 4로 수정됨 (6→4)")
    else:
        log_test("Table ColSpan 업데이트", False, "colSpan이 업데이트되지 않음")
    
    print(f"\n4. 테이블 데이터 표시 검증")
    
    # 마감일과 생성일이 표시되는지 확인
    deadline_display_pattern = r'project\.deadline.*toLocaleDateString'
    created_display_pattern = r'project\.created_at.*toLocaleDateString'
    
    if re.search(deadline_display_pattern, content):
        log_test("마감일 데이터 표시", True, "project.deadline을 테이블에 표시")
    else:
        log_test("마감일 데이터 표시", False, "마감일 표시 로직을 찾을 수 없음")
    
    if re.search(created_display_pattern, content):
        log_test("생성일 데이터 표시", True, "project.created_at을 테이블에 표시")
    else:
        log_test("생성일 데이터 표시", False, "생성일 표시 로직을 찾을 수 없음")
    
    # 제거된 테이블 데이터들이 없는지 확인
    removed_data_patterns = [
        (r'project\.status', "상태 데이터"),
        (r'project\.start_date', "시작일 데이터"),
        (r'project\.end_date', "종료일 데이터"),
        (r'project\.budget', "예산 데이터")
    ]
    
    for pattern, data_name in removed_data_patterns:
        if not re.search(pattern, content):
            log_test(f"{data_name} 제거", True, f"{data_name} 표시 로직이 제거됨")
        else:
            log_test(f"{data_name} 제거", False, f"{data_name} 표시 로직이 여전히 존재함")
    
    print(f"\n5. openEditModal 함수 검증")
    
    # openEditModal이 새로운 구조에 맞게 업데이트되었는지 확인
    edit_modal_pattern = r'setFormData\(\{\s*name:\s*project\.name,\s*description:\s*project\.description,\s*deadline:\s*project\.deadline'
    if re.search(edit_modal_pattern, content):
        log_test("편집 모달 데이터 매핑", True, "편집 시 올바른 필드만 매핑됨")
    else:
        log_test("편집 모달 데이터 매핑", False, "편집 모달 매핑이 업데이트되지 않음")
    
    # 결과 요약
    print(f"\n" + "="*60)
    print(f"프로젝트 관리 UI 개선사항 검증 결과")
    print(f"="*60)
    print(f"✓ 성공: {tests_passed}")
    print(f"✗ 실패: {tests_failed}")
    print(f"총 테스트: {tests_passed + tests_failed}")
    
    if tests_failed == 0:
        print(f"\n🎉 모든 테스트 통과! 프로젝트 관리 UI가 성공적으로 개선되었습니다.")
        print(f"\n📋 개선된 사항:")
        print(f"1. ✅ 불필요한 Form 필드 제거 - status, start_date, end_date, budget")
        print(f"2. ✅ 핵심 필드만 유지 - name, description, deadline")
        print(f"3. ✅ 테이블 컬럼 단순화 - 6개 → 4개 컬럼")
        print(f"4. ✅ 백엔드 모델과 일치 - ProjectCreate 모델에 맞춤")
        print(f"5. ✅ 사용자 경험 개선 - 복잡성 감소, 직관성 향상")
        print(f"\n🔧 기술적 개선:")
        print(f"• Form 상태 관리 단순화")
        print(f"• 불필요한 UI 컴포넌트 제거")
        print(f"• 데이터 일관성 확보")
        print(f"• 유지보수성 향상")
        return True
    else:
        print(f"\n❌ {tests_failed}개의 테스트가 실패했습니다. 추가 수정이 필요합니다.")
        return False

if __name__ == "__main__":
    success = test_project_ui_improvements()
    exit(0 if success else 1)