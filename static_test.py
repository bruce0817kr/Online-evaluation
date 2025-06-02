#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
간단한 시스템 상태 확인 테스트
"""

import os
import sys
from pathlib import Path

def check_project_structure():
    """프로젝트 구조 확인"""
    print("🔍 프로젝트 구조 확인")
    
    required_files = [
        "backend/server.py",
        "backend/export_utils.py", 
        "backend/requirements.txt",
        "frontend/src/App.js",
        "frontend/package.json",
        "README.md",
        "README_KR.md"
    ]
    
    missing_files = []
    for file_path in required_files:
        if Path(file_path).exists():
            print(f"✅ {file_path}")
        else:
            print(f"❌ {file_path}")
            missing_files.append(file_path)
    
    if not missing_files:
        print("🎉 모든 필수 파일이 존재합니다!")
    else:
        print(f"⚠️ 누락된 파일: {len(missing_files)}개")
    
    return len(missing_files) == 0

def check_dependencies():
    """필수 패키지 확인"""
    print("\n📦 필수 패키지 확인")
    
    try:
        # 백엔드 의존성 확인
        with open("backend/requirements.txt", "r", encoding="utf-8") as f:
            requirements = f.read().lower()
        
        required_packages = [
            "fastapi", "uvicorn", "sqlalchemy", "reportlab", 
            "openpyxl", "xlsxwriter", "pandas", "pydantic"
        ]
        
        missing = []
        for package in required_packages:
            if package in requirements:
                print(f"✅ {package}")
            else:
                print(f"❌ {package}")
                missing.append(package)
        
        if not missing:
            print("🎉 모든 필수 패키지가 requirements.txt에 포함되어 있습니다!")
        else:
            print(f"⚠️ 누락된 패키지: {', '.join(missing)}")
            
        return len(missing) == 0
        
    except FileNotFoundError:
        print("❌ backend/requirements.txt 파일을 찾을 수 없습니다.")
        return False
    except Exception as e:
        print(f"❌ 오류: {str(e)}")
        return False

def check_export_module():
    """내보내기 모듈 확인"""
    print("\n📄 내보내기 모듈 확인")
    
    try:
        # 내보내기 유틸리티 파일 읽기
        export_utils_path = Path("backend/export_utils.py")
        if not export_utils_path.exists():
            print("❌ export_utils.py 파일이 존재하지 않습니다.")
            return False
        
        with open(export_utils_path, "r", encoding="utf-8") as f:
            content = f.read()
        
        # 핵심 클래스와 함수 확인
        checks = [
            ("EvaluationExporter", "EvaluationExporter 클래스"),
            ("generate_pdf", "PDF 생성 함수"),
            ("generate_excel", "Excel 생성 함수"),
            ("bulk_export", "대량 내보내기 함수"),
            ("reportlab", "ReportLab import"),
            ("openpyxl", "OpenPyXL import")
        ]
        
        missing = []
        for check, description in checks:
            if check in content:
                print(f"✅ {description}")
            else:
                print(f"❌ {description}")
                missing.append(description)
        
        if not missing:
            print("🎉 내보내기 모듈이 완전히 구현되어 있습니다!")
        else:
            print(f"⚠️ 누락된 기능: {len(missing)}개")
            
        return len(missing) == 0
        
    except Exception as e:
        print(f"❌ 오류: {str(e)}")
        return False

def check_frontend():
    """프론트엔드 확인"""
    print("\n🌐 프론트엔드 확인")
    
    try:
        # App.js 파일 확인
        app_js_path = Path("frontend/src/App.js")
        if not app_js_path.exists():
            print("❌ App.js 파일이 존재하지 않습니다.")
            return False
        
        with open(app_js_path, "r", encoding="utf-8") as f:
            content = f.read()
        
        # 핵심 기능 확인
        checks = [
            ("handleSingleExport", "개별 내보내기 함수"),
            ("handleBulkExport", "대량 내보내기 함수"),
            ("Chart.js", "Chart.js 차트 기능"),
            ("exportProgress", "내보내기 진행 상태"),
            ("isBulkExportModalOpen", "대량 내보내기 모달"),
            ("fetchExportableEvaluations", "내보내기 목록 조회")
        ]
        
        missing = []
        for check, description in checks:
            if check in content:
                print(f"✅ {description}")
            else:
                print(f"❌ {description}")
                missing.append(description)
        
        if not missing:
            print("🎉 프론트엔드가 완전히 구현되어 있습니다!")
        else:
            print(f"⚠️ 누락된 기능: {len(missing)}개")
            
        return len(missing) == 0
        
    except Exception as e:
        print(f"❌ 오류: {str(e)}")
        return False

def main():
    """메인 테스트"""
    print("=" * 60)
    print("🧪 온라인 평가 시스템 - 정적 검증 테스트")
    print("=" * 60)
    
    results = []
    
    # 1. 프로젝트 구조 확인
    results.append(check_project_structure())
    
    # 2. 의존성 확인
    results.append(check_dependencies())
    
    # 3. 내보내기 모듈 확인
    results.append(check_export_module())
    
    # 4. 프론트엔드 확인
    results.append(check_frontend())
    
    # 결과 요약
    print("\n" + "=" * 60)
    print("📊 테스트 결과 요약")
    print("=" * 60)
    
    passed = sum(results)
    total = len(results)
    success_rate = (passed / total * 100) if total > 0 else 0
    
    print(f"총 테스트: {total}개")
    print(f"통과: {passed}개")
    print(f"실패: {total - passed}개")
    print(f"성공률: {success_rate:.1f}%")
    
    if success_rate == 100:
        print("🌟 완벽! 모든 검증을 통과했습니다.")
        print("✨ 시스템이 배포 준비 상태입니다.")
    elif success_rate >= 75:
        print("👍 양호! 대부분의 기능이 구현되어 있습니다.")
        print("🔧 일부 개선사항이 필요할 수 있습니다.")
    else:
        print("⚠️ 주의! 시스템에 중요한 누락사항이 있습니다.")
        print("🔨 추가 개발이 필요합니다.")
    
    print("\n🎯 다음 단계:")
    print("1. 백엔드 서버 실행: cd backend && uvicorn server:app --reload --port 8000")
    print("2. 프론트엔드 실행: cd frontend && npm start")
    print("3. 브라우저에서 http://localhost:3000 접속")
    print("4. 기능 테스트 수행")

if __name__ == "__main__":
    main()
