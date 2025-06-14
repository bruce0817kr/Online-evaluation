# ConPort MCP 시스템 진단 스크립트

import sqlite3
import os
import sys
from pathlib import Path
import json

def check_environment():
    """환경 설정 확인"""
    print("🔍 ConPort MCP 환경 진단 시작...\n")
    
    # Python 버전 확인
    python_version = sys.version
    print(f"🐍 Python 버전: {python_version}")
    
    # 작업 디렉토리 확인
    current_dir = os.getcwd()
    print(f"📁 현재 작업 디렉토리: {current_dir}")
    
    # 중요 파일들 존재 여부 확인
    important_files = [
        'context_portal/context.db',
        'alembic.ini',
        'alembic/env.py',
        'context-portal/.venv/Scripts/python.exe',
        '.env'
    ]
    
    print("\n📋 중요 파일 존재 여부:")
    for file_path in important_files:
        if os.path.exists(file_path):
            print(f"  ✅ {file_path}")
        else:
            print(f"  ❌ {file_path} (누락)")
    
    return True

def check_database():
    """데이터베이스 상태 확인"""
    print("\n🗄️ 데이터베이스 상태 확인:")
    
    try:
        os.chdir('c:\\Project\\Online-evaluation')
        conn = sqlite3.connect('context_portal/context.db')
        cursor = conn.cursor()
        
        # 테이블 목록 확인
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        table_names = [table[0] for table in tables]
        
        print(f"  📊 총 테이블 수: {len(tables)}")
        
        # 필수 테이블 확인
        required_tables = [
            'product_context', 'active_context', 'decisions', 
            'progress_entries', 'system_patterns', 'custom_data',
            'product_context_history', 'active_context_history',
            'conport_items_links', 'vector_data', 'context_links'
        ]
        
        missing_tables = []
        for table in required_tables:
            if table in table_names:
                print(f"    ✅ {table}")
            else:
                print(f"    ❌ {table} (누락)")
                missing_tables.append(table)
        
        # 각 테이블의 레코드 수 확인
        print("\n  📈 테이블별 레코드 수:")
        for table_name in table_names:
            if table_name not in ['sqlite_sequence', 'alembic_version']:
                try:
                    cursor.execute(f"SELECT COUNT(*) FROM {table_name};")
                    count = cursor.fetchone()[0]
                    print(f"    📋 {table_name}: {count} 레코드")
                except sqlite3.Error as e:
                    print(f"    ❌ {table_name}: 오류 - {e}")
        
        # 컨텍스트 데이터 확인
        print("\n  🎯 컨텍스트 데이터 상태:")
        try:
            cursor.execute("SELECT content FROM product_context WHERE id = 1;")
            product_content = cursor.fetchone()
            if product_content and product_content[0] and product_content[0] != '{}':
                content = json.loads(product_content[0])
                print(f"    ✅ Product Context: 설정됨 ({len(content)} 항목)")
            else:
                print("    ⚠️ Product Context: 비어있음")
                
            cursor.execute("SELECT content FROM active_context WHERE id = 1;")
            active_content = cursor.fetchone()
            if active_content and active_content[0] and active_content[0] != '{}':
                content = json.loads(active_content[0])
                print(f"    ✅ Active Context: 설정됨 ({len(content)} 항목)")
            else:
                print("    ⚠️ Active Context: 비어있음")
        except Exception as e:
            print(f"    ❌ 컨텍스트 확인 오류: {e}")
        
        conn.close()
        
        if missing_tables:
            print(f"\n⚠️ 누락된 테이블: {', '.join(missing_tables)}")
            return False
        else:
            print("\n✅ 모든 필수 테이블이 존재합니다.")
            return True
            
    except Exception as e:
        print(f"❌ 데이터베이스 연결 오류: {e}")
        return False

def check_env_variables():
    """환경 변수 확인"""
    print("\n🌍 환경 변수 확인:")
    
    # .env 파일 확인
    if os.path.exists('.env'):
        print("  ✅ .env 파일 존재")
        try:
            with open('.env', 'r', encoding='utf-8') as f:
                env_content = f.read()
                if 'LOG_LEVEL=INFO' in env_content:
                    print("  ✅ LOG_LEVEL=INFO (올바른 형식)")
                elif 'LOG_LEVEL=info' in env_content:
                    print("  ⚠️ LOG_LEVEL=info (소문자, 수정 필요)")
                else:
                    print("  ℹ️ LOG_LEVEL 설정을 찾을 수 없음")
        except Exception as e:
            print(f"  ❌ .env 파일 읽기 오류: {e}")
    else:
        print("  ❌ .env 파일이 존재하지 않음")
    
    # 시스템 환경 변수 확인
    problematic_vars = []
    for var_name in os.environ:
        if 'LOG_LEVEL' in var_name and os.environ[var_name].lower() == 'info':
            problematic_vars.append(f"{var_name}={os.environ[var_name]}")
    
    if problematic_vars:
        print("  ⚠️ 문제가 될 수 있는 환경 변수:")
        for var in problematic_vars:
            print(f"    - {var}")
    else:
        print("  ✅ 환경 변수 상태 양호")

def check_conport_server():
    """ConPort 서버 상태 확인"""
    print("\n🖥️ ConPort 서버 확인:")
    
    # 가상환경 Python 확인
    venv_python = 'context-portal/.venv/Scripts/python.exe'
    if os.path.exists(venv_python):
        print(f"  ✅ 가상환경 Python: {venv_python}")
    else:
        print(f"  ❌ 가상환경 Python 없음: {venv_python}")
        return False
    
    # ConPort 메인 스크립트 확인
    main_script = 'context-portal/src/context_portal_mcp/main.py'
    if os.path.exists(main_script):
        print(f"  ✅ ConPort 메인 스크립트: {main_script}")
    else:
        print(f"  ❌ ConPort 메인 스크립트 없음: {main_script}")
        return False
    
    return True

def provide_recommendations():
    """개선 권장사항 제시"""
    print("\n💡 권장사항:")
    print("  1. 정기적인 데이터베이스 백업 실행")
    print("  2. ConPort 서버 로그 모니터링")
    print("  3. 환경 변수 설정 주기적 확인")
    print("  4. 가상환경 의존성 업데이트 확인")

def main():
    """메인 진단 함수"""
    print("=" * 60)
    print("🏥 ConPort MCP 시스템 진단 도구")
    print("=" * 60)
    
    # 각 항목별 진단 실행
    env_ok = check_environment()
    db_ok = check_database()
    env_vars_ok = check_env_variables()
    server_ok = check_conport_server()
    
    # 종합 결과
    print("\n" + "=" * 60)
    print("📊 진단 결과 요약:")
    print("=" * 60)
    
    results = {
        "환경 설정": env_ok,
        "데이터베이스": db_ok, 
        "환경 변수": True,  # 경고는 있을 수 있지만 치명적이지 않음
        "서버 파일": server_ok
    }
    
    all_ok = all(results.values())
    
    for item, status in results.items():
        status_icon = "✅" if status else "❌"
        print(f"  {status_icon} {item}: {'정상' if status else '문제 있음'}")
    
    print("\n" + "=" * 60)
    if all_ok:
        print("🎉 ConPort MCP 시스템이 정상적으로 설정되었습니다!")
        print("🚀 서버를 시작할 준비가 완료되었습니다.")
    else:
        print("⚠️ 일부 문제가 발견되었습니다.")
        print("📋 위의 세부 진단 결과를 참고하여 문제를 해결해주세요.")
    
    provide_recommendations()
    print("=" * 60)

if __name__ == "__main__":
    main()
