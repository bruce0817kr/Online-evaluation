#!/usr/bin/env python3
"""
ConPort MCP 시스템 진단 스크립트

ConPort MCP 환경의 모든 구성 요소를 체크하고 문제점을 식별합니다.
데이터베이스 상태, 환경 설정, 파일 구조 등을 종합적으로 진단합니다.

사용법:
    python diagnose_conport.py [database_path]

매개변수:
    database_path: 데이터베이스 파일 경로 (기본값: context_portal/context.db)
"""

import sqlite3
import os
import sys
from pathlib import Path
import json

def check_environment():
    """환경 설정 확인"""
    print("🔍 ConPort MCP 환경 진단 시작...\n")
    
    # Python 버전 확인
    python_version = sys.version.split()[0]
    print(f"🐍 Python 버전: {python_version}")
    
    # 작업 디렉토리 확인
    current_dir = os.getcwd()
    print(f"📁 현재 작업 디렉토리: {current_dir}")
    
    # 중요 파일들 존재 여부 확인
    important_files = [
        'context_portal/context.db',
        'alembic.ini',
        'context-portal/src/context_portal_mcp/main.py',
        '.env'
    ]
    
    print("\n📋 중요 파일 존재 여부:")
    all_exist = True
    for file_path in important_files:
        if os.path.exists(file_path):
            print(f"  ✅ {file_path}")
        else:
            print(f"  ❌ {file_path} (누락)")
            all_exist = False
    
    return all_exist

def check_database(db_path="context_portal/context.db"):
    """데이터베이스 상태 확인"""
    print(f"\n🗄️ 데이터베이스 상태 확인: {db_path}")
    
    try:
        # 데이터베이스 파일 존재 확인
        if not os.path.exists(db_path):
            print(f"  ❌ 데이터베이스 파일이 없습니다: {db_path}")
            return False
        
        conn = sqlite3.connect(db_path)
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
            'conport_items_links', 'vector_data'
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
    
    issues = []
    
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
                    issues.append("LOG_LEVEL을 대문자로 변경 필요")
                else:
                    print("  ℹ️ LOG_LEVEL 설정을 찾을 수 없음")
        except Exception as e:
            print(f"  ❌ .env 파일 읽기 오류: {e}")
            issues.append(f".env 파일 읽기 오류: {e}")
    else:
        print("  ❌ .env 파일이 존재하지 않음")
        issues.append(".env 파일 누락")
    
    return len(issues) == 0, issues

def check_conport_server():
    """ConPort 서버 상태 확인"""
    print("\n🖥️ ConPort 서버 확인:")
    
    issues = []
    
    # 가상환경 확인 (여러 경로 시도)
    venv_paths = [
        'context-portal/.venv/Scripts/python.exe',
        'context-portal/venv/Scripts/python.exe',
        'context-portal/.venv/bin/python',
        'context-portal/venv/bin/python'
    ]
    
    venv_found = False
    for venv_path in venv_paths:
        if os.path.exists(venv_path):
            print(f"  ✅ 가상환경 Python: {venv_path}")
            venv_found = True
            break
    
    if not venv_found:
        print("  ❌ 가상환경 Python을 찾을 수 없음")
        issues.append("가상환경 Python 누락")
    
    # ConPort 메인 스크립트 확인
    main_script_paths = [
        'context-portal/src/context_portal_mcp/main.py',
        'context-portal/context_portal_mcp/main.py'
    ]
    
    script_found = False
    for script_path in main_script_paths:
        if os.path.exists(script_path):
            print(f"  ✅ ConPort 메인 스크립트: {script_path}")
            script_found = True
            break
    
    if not script_found:
        print("  ❌ ConPort 메인 스크립트를 찾을 수 없음")
        issues.append("ConPort 메인 스크립트 누락")
    
    return len(issues) == 0, issues

def provide_fix_suggestions(all_issues):
    """수정 방법 제안"""
    if not all_issues:
        return
    
    print("\n🔧 수정 방법:")
    
    for issue in all_issues:
        if "LOG_LEVEL" in issue:
            print("  1. .env 파일에서 LOG_LEVEL=info를 LOG_LEVEL=INFO로 수정")
        elif "가상환경" in issue:
            print("  2. ConPort 가상환경 설정:")
            print("     cd context-portal")
            print("     python -m venv .venv")
            print("     .venv\\Scripts\\activate")
            print("     pip install -r requirements.txt")
        elif "데이터베이스" in issue or "테이블" in issue:
            print("  3. 데이터베이스 초기화:")
            print("     python init_conport_db.py")
        elif ".env 파일" in issue:
            print("  4. .env 파일 생성:")
            print("     LOG_LEVEL=INFO")
            print("     DATABASE_URL=sqlite:///context_portal/context.db")

def main():
    """메인 진단 함수"""
    print("=" * 60)
    print("🏥 ConPort MCP 시스템 진단 도구")
    print("=" * 60)
    
    all_issues = []
    
    # 명령행 인수로 데이터베이스 경로 받기
    db_path = "context_portal/context.db"
    if len(sys.argv) > 1:
        db_path = sys.argv[1]
    
    # 각 항목별 진단 실행
    env_ok = check_environment()
    db_ok = check_database(db_path)
    env_vars_ok, env_issues = check_env_variables()
    server_ok, server_issues = check_conport_server()
    
    all_issues.extend(env_issues)
    all_issues.extend(server_issues)
    
    # 종합 결과
    print("\n" + "=" * 60)
    print("📊 진단 결과 요약:")
    print("=" * 60)
    
    results = {
        "환경 설정": env_ok,
        "데이터베이스": db_ok, 
        "환경 변수": env_vars_ok,
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
        print("\n📝 다음 단계:")
        print("  1. ConPort MCP 서버 실행:")
        print("     cd context-portal")
        print("     python -m context_portal_mcp")
        print("  2. MCP 클라이언트에서 ConPort 도구 사용")
    else:
        print("⚠️ 일부 문제가 발견되었습니다.")
        provide_fix_suggestions(all_issues)
    
    print("=" * 60)
    
    return 0 if all_ok else 1

if __name__ == "__main__":
    sys.exit(main())
