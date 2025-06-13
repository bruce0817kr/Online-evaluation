#!/usr/bin/env python3
"""
온라인 평가 시스템 최종 종합 테스트
Final Comprehensive Test for Online Evaluation System
"""

import asyncio
import httpx
import json
import time
from datetime import datetime
import sys

async def final_comprehensive_test():
    """최종 종합 테스트"""
    print("🎯 온라인 평가 시스템 최종 종합 테스트")
    print("=" * 60)
    print(f"테스트 시작 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    backend_url = "http://localhost:8080"
    frontend_url = "http://localhost:3000"
    
    results = {
        "backend_tests": {},
        "frontend_tests": {},
        "integration_tests": {},
        "performance_tests": {}
    }
    
    # 1. 백엔드 테스트
    print("\n🔧 백엔드 API 테스트")
    print("-" * 40)
    
    backend_endpoints = [
        ("/", "API 루트"),
        ("/health", "헬스체크"),
        ("/docs", "API 문서"),
        ("/api/health/detailed", "상세 헬스체크"),
        ("/api/health/liveness", "생존 확인"),
        ("/api/health/readiness", "준비 상태")
    ]
    
    for endpoint, name in backend_endpoints:
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                start_time = time.time()
                response = await client.get(f"{backend_url}{endpoint}")
                response_time = (time.time() - start_time) * 1000
                
                success = response.status_code in [200, 307]  # 307은 리다이렉트
                results["backend_tests"][endpoint] = {
                    "success": success,
                    "status_code": response.status_code,
                    "response_time_ms": round(response_time, 2)
                }
                
                status = "✅" if success else "❌"
                print(f"   {status} {name}: {response.status_code} ({response_time:.1f}ms)")
                
        except Exception as e:
            results["backend_tests"][endpoint] = {
                "success": False,
                "error": str(e),
                "response_time_ms": None
            }
            print(f"   ❌ {name}: 오류 - {str(e)}")
    
    # 2. 프론트엔드 테스트
    print("\n🖥️ 프론트엔드 접근성 테스트")
    print("-" * 40)
    
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            start_time = time.time()
            response = await client.get(frontend_url)
            response_time = (time.time() - start_time) * 1000
            
            success = response.status_code == 200
            results["frontend_tests"]["main_page"] = {
                "success": success,
                "status_code": response.status_code,
                "response_time_ms": round(response_time, 2)
            }
            
            status = "✅" if success else "❌"
            print(f"   {status} 메인 페이지: {response.status_code} ({response_time:.1f}ms)")
            
    except Exception as e:
        results["frontend_tests"]["main_page"] = {
            "success": False,
            "error": str(e)
        }
        print(f"   ❌ 메인 페이지: 오류 - {str(e)}")
    
    # 3. 통합 테스트 (CORS 및 API 호출)
    print("\n🔗 통합 테스트")
    print("-" * 40)
    
    try:
        # CORS 프리플라이트 요청 시뮬레이션
        async with httpx.AsyncClient(timeout=10) as client:
            headers = {
                "Origin": frontend_url,
                "Access-Control-Request-Method": "GET",
                "Access-Control-Request-Headers": "Content-Type"
            }
            response = await client.options(f"{backend_url}/health", headers=headers)
            
            cors_success = response.status_code in [200, 204]
            results["integration_tests"]["cors"] = {
                "success": cors_success,
                "status_code": response.status_code
            }
            
            status = "✅" if cors_success else "❌"
            print(f"   {status} CORS 설정: {response.status_code}")
            
    except Exception as e:
        results["integration_tests"]["cors"] = {
            "success": False,
            "error": str(e)
        }
        print(f"   ❌ CORS 설정: 오류 - {str(e)}")
    
    # 4. 성능 테스트
    print("\n⚡ 성능 테스트")
    print("-" * 40)
    
    # 연속 요청 테스트
    try:
        response_times = []
        for i in range(5):
            async with httpx.AsyncClient(timeout=10) as client:
                start_time = time.time()
                response = await client.get(f"{backend_url}/health")
                response_time = (time.time() - start_time) * 1000
                response_times.append(response_time)
        
        avg_response_time = sum(response_times) / len(response_times)
        results["performance_tests"]["average_response_time"] = {
            "avg_ms": round(avg_response_time, 2),
            "samples": response_times
        }
        
        performance_status = "✅" if avg_response_time < 1000 else "⚠️" if avg_response_time < 3000 else "❌"
        print(f"   {performance_status} 평균 응답 시간: {avg_response_time:.1f}ms")
        
    except Exception as e:
        results["performance_tests"]["average_response_time"] = {
            "success": False,
            "error": str(e)
        }
        print(f"   ❌ 성능 테스트: 오류 - {str(e)}")
    
    # 5. 결과 요약
    print("\n" + "=" * 60)
    print("📊 최종 테스트 결과 요약")
    print("=" * 60)
    
    # 백엔드 성공률 계산
    backend_total = len(results["backend_tests"])
    backend_success = sum(1 for test in results["backend_tests"].values() if test.get("success", False))
    backend_rate = (backend_success / backend_total * 100) if backend_total > 0 else 0
    
    # 프론트엔드 성공률 계산
    frontend_total = len(results["frontend_tests"])
    frontend_success = sum(1 for test in results["frontend_tests"].values() if test.get("success", False))
    frontend_rate = (frontend_success / frontend_total * 100) if frontend_total > 0 else 0
    
    # 통합 성공률 계산
    integration_total = len(results["integration_tests"])
    integration_success = sum(1 for test in results["integration_tests"].values() if test.get("success", False))
    integration_rate = (integration_success / integration_total * 100) if integration_total > 0 else 0
    
    print(f"🔧 백엔드 테스트: {backend_success}/{backend_total} ({backend_rate:.1f}%)")
    print(f"🖥️ 프론트엔드 테스트: {frontend_success}/{frontend_total} ({frontend_rate:.1f}%)")
    print(f"🔗 통합 테스트: {integration_success}/{integration_total} ({integration_rate:.1f}%)")
    
    # 전체 성공률
    total_tests = backend_total + frontend_total + integration_total
    total_success = backend_success + frontend_success + integration_success
    overall_rate = (total_success / total_tests * 100) if total_tests > 0 else 0
    
    print(f"\n🎯 전체 성공률: {total_success}/{total_tests} ({overall_rate:.1f}%)")
    
    # 최종 판정
    if overall_rate >= 90:
        print("🎉 시스템이 우수한 상태입니다!")
        status_emoji = "🎉"
        status_text = "우수"
    elif overall_rate >= 80:
        print("👍 시스템이 양호한 상태입니다!")
        status_emoji = "👍"
        status_text = "양호"
    elif overall_rate >= 70:
        print("⚠️ 시스템에 일부 문제가 있습니다.")
        status_emoji = "⚠️"
        status_text = "주의"
    else:
        print("❌ 시스템에 심각한 문제가 있습니다.")
        status_emoji = "❌"
        status_text = "문제"
    
    # 결과 저장
    final_report = {
        "test_date": datetime.now().isoformat(),
        "overall_success_rate": overall_rate,
        "status": status_text,
        "detailed_results": results
    }
    
    with open("final_comprehensive_test_report.json", "w", encoding="utf-8") as f:
        json.dump(final_report, f, indent=2, ensure_ascii=False)
    
    print(f"\n📄 상세 결과가 'final_comprehensive_test_report.json'에 저장되었습니다.")
    print(f"🕒 테스트 완료 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    return overall_rate

if __name__ == "__main__":
    print("🚀 서버들이 실행 중인지 확인하세요:")
    print("   - 백엔드: http://localhost:8080")
    print("   - 프론트엔드: http://localhost:3000")
    print("-" * 50)
    
    try:
        final_rate = asyncio.run(final_comprehensive_test())
        sys.exit(0 if final_rate >= 80 else 1)
    except KeyboardInterrupt:
        print("\n❌ 테스트가 중단되었습니다.")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 테스트 오류: {str(e)}")
        sys.exit(1)
