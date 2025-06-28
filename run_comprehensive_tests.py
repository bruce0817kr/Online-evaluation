#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
종합 테스트 실행 스크립트
========================

온라인 평가 시스템의 모든 테스트를 실행하고 결과를 종합 분석하는 스크립트
"""

import os
import sys
import json
import subprocess
import time
from datetime import datetime
from pathlib import Path

def print_header(title):
    """테스트 섹션 헤더 출력"""
    print("\n" + "="*60)
    print(f"🧪 {title}")
    print("="*60)

def run_command(command, description="", timeout=300):
    """명령어 실행 및 결과 반환"""
    print(f"\n🔍 {description}")
    print(f"📝 실행: {command}")
    
    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=timeout
        )
        
        if result.returncode == 0:
            print("✅ 성공")
            return True, result.stdout, result.stderr
        else:
            print("❌ 실패")
            print(f"오류: {result.stderr}")
            return False, result.stdout, result.stderr
            
    except subprocess.TimeoutExpired:
        print(f"⏰ 타임아웃 ({timeout}초)")
        return False, "", "Timeout"
    except Exception as e:
        print(f"💥 예외 발생: {str(e)}")
        return False, "", str(e)

def main():
    """메인 테스트 실행"""
    print_header("온라인 평가 시스템 종합 테스트")
    
    start_time = datetime.now()
    results = {
        "timestamp": start_time.isoformat(),
        "tests": {},
        "summary": {}
    }
    
    # 1. 시스템 유효성 검증
    print_header("시스템 유효성 검증")
    success, stdout, stderr = run_command(
        "python3 simple_system_validation.py",
        "시스템 구조 및 설정 검증"
    )
    results["tests"]["system_validation"] = {
        "success": success,
        "stdout": stdout,
        "stderr": stderr
    }
    
    # 2. 단위 테스트 (pytest)
    print_header("단위 테스트")
    success, stdout, stderr = run_command(
        "cd backend && python3 -m pytest test_*.py -v",
        "백엔드 단위 테스트"
    )
    results["tests"]["unit_tests"] = {
        "success": success,
        "stdout": stdout,
        "stderr": stderr
    }
    
    # 3. 통합 테스트
    print_header("통합 테스트")
    success, stdout, stderr = run_command(
        "python3 tests/integration/test_system_integration.py",
        "시스템 통합 테스트"
    )
    results["tests"]["integration_tests"] = {
        "success": success,
        "stdout": stdout,
        "stderr": stderr
    }
    
    # 4. E2E 테스트 (Playwright)
    print_header("E2E 테스트")
    success, stdout, stderr = run_command(
        "npm test",
        "Playwright E2E 테스트"
    )
    results["tests"]["e2e_tests"] = {
        "success": success,
        "stdout": stdout,
        "stderr": stderr
    }
    
    # 5. 성능 테스트
    print_header("성능 테스트")
    success, stdout, stderr = run_command(
        "python3 tests/performance/test_performance_benchmarks.py",
        "성능 벤치마크 테스트"
    )
    results["tests"]["performance_tests"] = {
        "success": success,
        "stdout": stdout,
        "stderr": stderr
    }
    
    # 6. 배포 검증
    print_header("배포 검증")
    success, stdout, stderr = run_command(
        "python3 simple_system_test.py",
        "간단한 시스템 테스트"
    )
    results["tests"]["deployment_verification"] = {
        "success": success,
        "stdout": stdout,
        "stderr": stderr
    }
    
    # 결과 요약
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()
    
    passed_tests = sum(1 for test in results["tests"].values() if test["success"])
    total_tests = len(results["tests"])
    success_rate = (passed_tests / total_tests) * 100 if total_tests > 0 else 0
    
    results["summary"] = {
        "start_time": start_time.isoformat(),
        "end_time": end_time.isoformat(),
        "duration_seconds": duration,
        "total_tests": total_tests,
        "passed_tests": passed_tests,
        "failed_tests": total_tests - passed_tests,
        "success_rate": success_rate
    }
    
    # 결과 출력
    print_header("테스트 결과 요약")
    print(f"📊 전체 테스트: {total_tests}개")
    print(f"✅ 통과: {passed_tests}개")
    print(f"❌ 실패: {total_tests - passed_tests}개")
    print(f"📈 성공률: {success_rate:.1f}%")
    print(f"⏱️ 소요 시간: {duration:.1f}초")
    
    # 실패한 테스트 상세 정보
    failed_tests = [name for name, result in results["tests"].items() if not result["success"]]
    if failed_tests:
        print("\n❌ 실패한 테스트:")
        for test_name in failed_tests:
            print(f"   • {test_name}")
            stderr = results["tests"][test_name]["stderr"]
            if stderr:
                print(f"     오류: {stderr[:200]}...")
    
    # 결과 파일 저장
    report_file = f"comprehensive_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    try:
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        print(f"\n📄 상세 보고서: {report_file}")
    except Exception as e:
        print(f"\n⚠️ 보고서 저장 실패: {e}")
    
    # 종료 코드 설정
    if success_rate >= 80:
        print("\n🎉 테스트 성공!")
        sys.exit(0)
    else:
        print("\n💥 테스트 실패!")
        sys.exit(1)

if __name__ == "__main__":
    main()