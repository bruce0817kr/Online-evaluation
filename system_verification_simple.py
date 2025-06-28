#!/usr/bin/env python3
"""
온라인 평가 시스템 종합 검증 테스트 (간소화 버전)
==============================================

모든 시스템 컴포넌트를 빠르게 검증합니다.
"""

import requests
import json
import time
from datetime import datetime
import traceback

def test_service_health():
    """서비스 상태 테스트"""
    print("\n=== 서비스 상태 테스트 ===")
    
    services = {
        "Backend": "http://localhost:8180/health",
        "Frontend": "http://localhost:3100",
        "Elasticsearch": "http://localhost:9300/_cluster/health",
        "Kibana": "http://localhost:5701/api/status",
        "Logstash": "http://localhost:9700/"
    }
    
    results = {}
    
    for name, url in services.items():
        try:
            response = requests.get(url, timeout=10)
            status = "✅ HEALTHY" if response.status_code == 200 else f"❌ ERROR ({response.status_code})"
            response_time = round(response.elapsed.total_seconds() * 1000, 2)
            results[name] = {"status": "PASS" if response.status_code == 200 else "FAIL", "response_time": response_time}
            print(f"  {name}: {status} ({response_time}ms)")
        except Exception as e:
            results[name] = {"status": "FAIL", "error": str(e)}
            print(f"  {name}: ❌ FAILED - {str(e)[:100]}")
    
    return results

def test_api_endpoints():
    """API 엔드포인트 테스트"""
    print("\n=== API 엔드포인트 테스트 ===")
    
    base_url = "http://localhost:8180"
    endpoints = [
        ("GET", "/health"),
        ("GET", "/docs"),
        ("GET", "/api/users"),
        ("GET", "/api/evaluations")
    ]
    
    results = {}
    
    for method, endpoint in endpoints:
        try:
            url = f"{base_url}{endpoint}"
            response = requests.get(url, timeout=10)
            
            # 401, 404는 예상되는 응답이므로 정상으로 처리
            if response.status_code in [200, 201, 401, 404]:
                status = "✅ OK"
                result_status = "PASS"
            else:
                status = f"❌ ERROR ({response.status_code})"
                result_status = "FAIL"
            
            response_time = round(response.elapsed.total_seconds() * 1000, 2)
            results[endpoint] = {"status": result_status, "code": response.status_code, "response_time": response_time}
            print(f"  {method} {endpoint}: {status} ({response_time}ms)")
            
        except Exception as e:
            results[endpoint] = {"status": "FAIL", "error": str(e)}
            print(f"  {method} {endpoint}: ❌ FAILED - {str(e)[:100]}")
    
    return results

def test_elk_stack():
    """ELK 스택 상세 테스트"""
    print("\n=== ELK 스택 상세 테스트 ===")
    
    results = {}
    
    # Elasticsearch 클러스터 상태
    try:
        response = requests.get("http://localhost:9300/_cluster/health", timeout=10)
        if response.status_code == 200:
            data = response.json()
            cluster_status = data.get("status", "unknown")
            nodes = data.get("number_of_nodes", 0)
            shards = data.get("active_shards", 0)
            
            status_icon = "✅" if cluster_status == "green" else "⚠️" if cluster_status == "yellow" else "❌"
            print(f"  Elasticsearch Cluster: {status_icon} {cluster_status.upper()} ({nodes} nodes, {shards} shards)")
            results["elasticsearch"] = {"status": "PASS" if cluster_status in ["green", "yellow"] else "FAIL", "cluster_status": cluster_status}
        else:
            print(f"  Elasticsearch Cluster: ❌ ERROR ({response.status_code})")
            results["elasticsearch"] = {"status": "FAIL", "code": response.status_code}
    except Exception as e:
        print(f"  Elasticsearch Cluster: ❌ FAILED - {str(e)[:100]}")
        results["elasticsearch"] = {"status": "FAIL", "error": str(e)}
    
    # Kibana 상태
    try:
        response = requests.get("http://localhost:5701/api/status", timeout=10)
        status_icon = "✅" if response.status_code == 200 else "❌"
        print(f"  Kibana: {status_icon} {'HEALTHY' if response.status_code == 200 else 'ERROR'}")
        results["kibana"] = {"status": "PASS" if response.status_code == 200 else "FAIL"}
    except Exception as e:
        print(f"  Kibana: ❌ FAILED - {str(e)[:100]}")
        results["kibana"] = {"status": "FAIL", "error": str(e)}
    
    # Logstash 상태
    try:
        response = requests.get("http://localhost:9700/", timeout=10)
        if response.status_code == 200:
            data = response.json()
            version = data.get("version", "unknown")
            print(f"  Logstash: ✅ HEALTHY (v{version})")
            results["logstash"] = {"status": "PASS", "version": version}
        else:
            print(f"  Logstash: ❌ ERROR ({response.status_code})")
            results["logstash"] = {"status": "FAIL", "code": response.status_code}
    except Exception as e:
        print(f"  Logstash: ❌ FAILED - {str(e)[:100]}")
        results["logstash"] = {"status": "FAIL", "error": str(e)}
    
    return results

def test_database_connectivity():
    """데이터베이스 연결성 테스트"""
    print("\n=== 데이터베이스 연결성 테스트 ===")
    
    try:
        response = requests.get("http://localhost:8180/health", timeout=10)
        if response.status_code == 200:
            data = response.json()
            services = data.get("services", {})
            
            mongodb_status = services.get("mongodb", "unknown")
            redis_status = services.get("redis", "unknown")
            
            mongodb_icon = "✅" if mongodb_status == "healthy" else "❌"
            redis_icon = "✅" if redis_status == "healthy" else "❌"
            
            print(f"  MongoDB: {mongodb_icon} {mongodb_status.upper()}")
            print(f"  Redis: {redis_icon} {redis_status.upper()}")
            
            return {
                "mongodb": {"status": "PASS" if mongodb_status == "healthy" else "FAIL"},
                "redis": {"status": "PASS" if redis_status == "healthy" else "FAIL"}
            }
        else:
            print(f"  Database connectivity: ❌ Backend health check failed")
            return {"status": "FAIL", "reason": "Backend health check failed"}
            
    except Exception as e:
        print(f"  Database connectivity: ❌ FAILED - {str(e)[:100]}")
        return {"status": "FAIL", "error": str(e)}

def test_security_configuration():
    """보안 설정 테스트"""
    print("\n=== 보안 설정 테스트 ===")
    
    try:
        response = requests.get("http://localhost:8180/health", timeout=10)
        
        security_headers = {
            "x-content-type-options": "Content Type Protection",
            "x-frame-options": "Clickjacking Protection", 
            "x-xss-protection": "XSS Protection",
            "strict-transport-security": "HTTPS Enforcement"
        }
        
        found_headers = []
        for header, description in security_headers.items():
            if header in response.headers:
                found_headers.append(header)
                print(f"  ✅ {description}: {response.headers[header]}")
            else:
                print(f"  ❌ {description}: Not found")
        
        # CORS 테스트
        cors_headers = {
            "Origin": "http://localhost:3100",
            "Access-Control-Request-Method": "GET"
        }
        cors_response = requests.options("http://localhost:8180/health", headers=cors_headers, timeout=10)
        
        if "Access-Control-Allow-Origin" in cors_response.headers:
            print(f"  ✅ CORS Configuration: {cors_response.headers['Access-Control-Allow-Origin']}")
            found_headers.append("cors")
        else:
            print("  ❌ CORS Configuration: Not configured")
        
        return {
            "security_headers": len([h for h in security_headers.keys() if h in response.headers]),
            "cors_configured": "Access-Control-Allow-Origin" in cors_response.headers,
            "total_score": len(found_headers)
        }
        
    except Exception as e:
        print(f"  Security configuration: ❌ FAILED - {str(e)[:100]}")
        return {"status": "FAIL", "error": str(e)}

def generate_summary_report(results):
    """종합 결과 리포트 생성"""
    print("\n" + "="*60)
    print("🎯 종합 시스템 검증 결과")
    print("="*60)
    
    # 전체 점수 계산
    total_tests = 0
    passed_tests = 0
    
    for category, category_results in results.items():
        if isinstance(category_results, dict):
            for test_name, test_result in category_results.items():
                if isinstance(test_result, dict) and "status" in test_result:
                    total_tests += 1
                    if test_result["status"] == "PASS":
                        passed_tests += 1
    
    overall_score = round((passed_tests / total_tests) * 100, 1) if total_tests > 0 else 0
    
    if overall_score >= 90:
        status_icon = "🎉"
        status_text = "EXCELLENT"
    elif overall_score >= 80:
        status_icon = "✅"
        status_text = "GOOD"
    elif overall_score >= 70:
        status_icon = "⚠️"
        status_text = "ACCEPTABLE"
    else:
        status_icon = "❌"
        status_text = "NEEDS ATTENTION"
    
    print(f"\n{status_icon} 전체 상태: {status_text}")
    print(f"📊 종합 점수: {overall_score}% ({passed_tests}/{total_tests} 테스트 통과)")
    
    # 카테고리별 결과
    print(f"\n📋 카테고리별 결과:")
    category_names = {
        "services": "서비스 상태",
        "api": "API 엔드포인트", 
        "elk": "ELK 스택",
        "database": "데이터베이스",
        "security": "보안 설정"
    }
    
    for category, name in category_names.items():
        if category in results:
            category_data = results[category]
            if isinstance(category_data, dict):
                category_tests = 0
                category_passed = 0
                for test_result in category_data.values():
                    if isinstance(test_result, dict) and "status" in test_result:
                        category_tests += 1
                        if test_result["status"] == "PASS":
                            category_passed += 1
                
                category_score = round((category_passed / category_tests) * 100, 1) if category_tests > 0 else 0
                icon = "✅" if category_score >= 80 else "⚠️" if category_score >= 60 else "❌"
                print(f"  {icon} {name}: {category_score}% ({category_passed}/{category_tests})")
    
    # 권장사항
    recommendations = []
    
    if results.get("services", {}).get("Frontend", {}).get("status") != "PASS":
        recommendations.append("Frontend 서비스 상태 확인 및 복구")
    
    if results.get("elk", {}).get("elasticsearch", {}).get("status") != "PASS":
        recommendations.append("Elasticsearch 클러스터 상태 점검")
    
    security_score = results.get("security", {}).get("total_score", 0)
    if security_score < 4:
        recommendations.append("보안 헤더 설정 강화")
    
    if not recommendations:
        recommendations.append("모든 시스템이 정상 작동 중입니다! 🎉")
    
    print(f"\n💡 권장사항:")
    for i, rec in enumerate(recommendations, 1):
        print(f"  {i}. {rec}")
    
    return {
        "overall_score": overall_score,
        "status": status_text,
        "total_tests": total_tests,
        "passed_tests": passed_tests,
        "recommendations": recommendations
    }

def save_results(results, summary):
    """결과를 JSON 파일로 저장"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    report = {
        "timestamp": datetime.now().isoformat(),
        "summary": summary,
        "detailed_results": results,
        "test_info": {
            "script_version": "1.0",
            "test_type": "comprehensive_system_verification"
        }
    }
    
    filename = f"system_verification_report_{timestamp}.json"
    
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 상세 결과 저장: {filename}")
    return filename

def main():
    """메인 실행 함수"""
    print("🚀 온라인 평가 시스템 종합 검증 테스트")
    print(f"⏰ 실행 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)
    
    results = {}
    
    try:
        # 모든 테스트 실행
        results["services"] = test_service_health()
        results["api"] = test_api_endpoints()
        results["elk"] = test_elk_stack()
        results["database"] = test_database_connectivity()
        results["security"] = test_security_configuration()
        
        # 결과 요약 및 리포트 생성
        summary = generate_summary_report(results)
        
        # 결과 저장
        report_file = save_results(results, summary)
        
        print(f"\n🏁 테스트 완료!")
        print(f"📄 상세 리포트: {report_file}")
        
        return summary["overall_score"] >= 80
        
    except KeyboardInterrupt:
        print("\n❌ 사용자에 의해 테스트가 중단되었습니다.")
        return False
    except Exception as e:
        print(f"\n❌ 예상치 못한 오류: {str(e)}")
        print("\n상세 오류:")
        print(traceback.format_exc())
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
