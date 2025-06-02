#!/usr/bin/env python3
"""
간단한 배포 상태 확인 스크립트
"""

import requests
import subprocess
import json
import time
import sys

def check_docker_containers():
    """Docker 컨테이너 상태 확인"""
    print("🐳 Docker 컨테이너 상태 확인...")
    try:
        result = subprocess.run(['docker', 'ps', '--format', 'json'], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            containers = []
            for line in result.stdout.strip().split('\n'):
                if line.strip():
                    try:
                        containers.append(json.loads(line))
                    except:
                        pass
            
            print(f"✅ 실행 중인 컨테이너: {len(containers)}개")
            for container in containers:
                name = container.get('Names', 'Unknown')
                status = container.get('Status', 'Unknown')
                ports = container.get('Ports', 'No ports')
                print(f"   📦 {name}: {status}")
                print(f"       포트: {ports}")
            return len(containers) > 0
        else:
            print("❌ Docker 컨테이너 조회 실패")
            return False
    except Exception as e:
        print(f"❌ Docker 확인 중 오류: {str(e)}")
        return False

def check_backend_service():
    """백엔드 서비스 확인"""
    print("\n🔗 백엔드 서비스 확인...")
    try:
        # 헬스 체크
        response = requests.get('http://localhost:8080/health', timeout=5)
        if response.status_code == 200:
            print("✅ 백엔드 헬스 체크 성공")
            print(f"   응답: {response.json()}")
            return True
        else:
            print(f"❌ 백엔드 헬스 체크 실패: HTTP {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ 백엔드 서비스에 연결할 수 없습니다")
        return False
    except Exception as e:
        print(f"❌ 백엔드 확인 중 오류: {str(e)}")
        return False

def check_frontend_service():
    """프론트엔드 서비스 확인"""
    print("\n🌐 프론트엔드 서비스 확인...")
    try:
        response = requests.get('http://localhost:3000', timeout=5)
        if response.status_code == 200:
            print("✅ 프론트엔드 서비스 정상")
            return True
        else:
            print(f"❌ 프론트엔드 서비스 오류: HTTP {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ 프론트엔드 서비스에 연결할 수 없습니다")
        return False
    except Exception as e:
        print(f"❌ 프론트엔드 확인 중 오류: {str(e)}")
        return False

def check_databases():
    """데이터베이스 서비스 확인"""
    print("\n🗄️ 데이터베이스 서비스 확인...")
    
    # Redis 확인
    try:
        import redis
        r = redis.Redis(host='localhost', port=6379, decode_responses=True)
        r.ping()
        print("✅ Redis 연결 성공")
        redis_ok = True
    except Exception as e:
        print(f"❌ Redis 연결 실패: {str(e)}")
        redis_ok = False
    
    # MongoDB 확인
    try:
        from pymongo import MongoClient
        client = MongoClient('mongodb://admin:password123@localhost:27017/', 
                           serverSelectionTimeoutMS=5000)
        client.admin.command('ismaster')
        print("✅ MongoDB 연결 성공")
        mongodb_ok = True
        client.close()
    except Exception as e:
        print(f"❌ MongoDB 연결 실패: {str(e)}")
        mongodb_ok = False
    
    return redis_ok and mongodb_ok

def restart_services():
    """서비스 재시작"""
    print("\n🔄 서비스 재시작 중...")
    try:
        # 컨테이너 중지
        subprocess.run(['docker-compose', 'down'], check=True)
        print("✅ 서비스 중지 완료")
        
        # 환경변수 파일 복사
        try:
            subprocess.run(['copy', '.env.production', '.env'], 
                         shell=True, check=True)
            print("✅ 환경변수 파일 설정 완료")
        except:
            print("⚠️ 환경변수 파일 복사 실패 (기존 파일 사용)")
        
        # 서비스 시작
        subprocess.run(['docker-compose', 'up', '-d'], check=True)
        print("✅ 서비스 시작 완료")
        
        # 잠시 대기
        print("⏳ 서비스 초기화 대기 중... (30초)")
        time.sleep(30)
        
        return True
    except Exception as e:
        print(f"❌ 서비스 재시작 실패: {str(e)}")
        return False

def main():
    """메인 함수"""
    print("🚀 온라인 평가 시스템 배포 상태 확인")
    print("=" * 50)
    
    # 1. Docker 컨테이너 확인
    docker_ok = check_docker_containers()
    
    # 2. 백엔드 서비스 확인
    backend_ok = check_backend_service()
    
    # 3. 프론트엔드 서비스 확인
    frontend_ok = check_frontend_service()
    
    # 4. 데이터베이스 확인
    db_ok = check_databases()
    
    # 결과 요약
    print("\n📊 상태 요약")
    print("=" * 30)
    print(f"Docker 컨테이너: {'✅ OK' if docker_ok else '❌ 문제'}")
    print(f"백엔드 서비스: {'✅ OK' if backend_ok else '❌ 문제'}")
    print(f"프론트엔드 서비스: {'✅ OK' if frontend_ok else '❌ 문제'}")
    print(f"데이터베이스: {'✅ OK' if db_ok else '❌ 문제'}")
    
    all_ok = docker_ok and backend_ok and frontend_ok and db_ok
    
    if all_ok:
        print("\n🎉 모든 서비스가 정상적으로 실행 중입니다!")
        print("📱 웹 애플리케이션: http://localhost:3000")
        print("🔗 API 서버: http://localhost:8080")
        return 0
    else:
        print("\n⚠️ 일부 서비스에 문제가 있습니다.")
        
        # 자동 복구 시도
        if input("\n🔧 서비스를 재시작하시겠습니까? (y/N): ").lower() == 'y':
            if restart_services():
                print("\n🔄 재시작 완료. 다시 확인합니다...")
                # 재확인
                time.sleep(5)
                return main()
            else:
                print("\n❌ 재시작 실패")
                return 1
        else:
            return 1

if __name__ == "__main__":
    sys.exit(main())
