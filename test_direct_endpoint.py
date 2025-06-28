#!/usr/bin/env python3

import requests
import json

def test_direct_endpoint():
    """테스트 엔드포인트 호출"""
    
    base_url = "http://localhost:8080"
    test_url = f"{base_url}/api/test/direct"
    
    try:
        print("🔍 Direct endpoint 테스트 시작...")
        print(f"📡 URL: {test_url}")
        
        response = requests.post(test_url, timeout=10)
        
        print(f"📊 상태 코드: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Direct endpoint 성공!")
            print(f"📄 응답: {result}")
        else:
            print("❌ Direct endpoint 실패:")
            print(f"📄 응답 내용: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ 연결 실패: 서버가 실행 중인지 확인하세요")
    except requests.exceptions.Timeout:
        print("❌ 타임아웃: 서버 응답이 느립니다")
    except Exception as e:
        print(f"❌ 오류 발생: {e}")

if __name__ == "__main__":
    test_direct_endpoint()