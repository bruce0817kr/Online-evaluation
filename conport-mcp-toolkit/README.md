# ConPort MCP Toolkit

ConPort MCP (Model Context Protocol) 설치, 설정, 문제 해결을 위한 종합 툴킷입니다.

## 📁 구성 요소

### 스크립트
- `init_conport_db.py` - 데이터베이스 초기 스키마 생성
- `diagnose_conport.py` - ConPort 환경 진단 도구
- `fix_conport_columns.py` - 스키마 수정 및 컬럼 추가
- `check_db.py` - 데이터베이스 연결 및 테이블 확인

### 설정 파일
- `init_conport_schema.sql` - 완전한 ConPort 데이터베이스 스키마
- `alembic.ini.template` - Alembic 설정 템플릿
- `.env.template` - 환경 변수 템플릿

### 문서
- `README.md` - 이 파일
- `설치가이드.md` - 단계별 설치 가이드
- `문제해결가이드.md` - 일반적인 문제와 해결 방법

## 🚀 빠른 시작

1. **환경 진단**
   ```bash
   python diagnose_conport.py
   ```

2. **데이터베이스 초기화**
   ```bash
   python init_conport_db.py
   ```

3. **ConPort MCP 서버 실행**
   ```bash
   # 프로젝트 루트에서
   cd context-portal
   python -m context_portal_mcp
   ```

## 🔧 사용법

각 스크립트는 독립적으로 실행 가능하며, 프로젝트 상황에 맞게 선택적으로 사용할 수 있습니다.

자세한 사용법은 각 파일의 주석과 문서를 참조하세요.

## 📝 라이선스

이 툴킷은 MIT 라이선스 하에 배포됩니다.
