import requests
import json

def check_api_endpoints():
    """API 엔드포인트 확인"""
    base_url = "http://localhost:8000"
    
    print("🔍 API 엔드포인트 검사...")
    print("=" * 50)
    
    # OpenAPI 스펙 확인
    try:
        response = requests.get(f"{base_url}/openapi.json")
        if response.status_code == 200:
            openapi_spec = response.json()
            
            print("📋 사용 가능한 엔드포인트:")
            paths = openapi_spec.get("paths", {})
            for path, methods in paths.items():
                for method, details in methods.items():
                    summary = details.get("summary", "설명 없음")
                    print(f"   {method.upper()} {path} - {summary}")
        else:
            print(f"❌ OpenAPI 스펙 로드 실패: {response.status_code}")
    
    except Exception as e:
        print(f"❌ OpenAPI 스펙 확인 중 오류: {e}")

if __name__ == "__main__":
    check_api_endpoints()
