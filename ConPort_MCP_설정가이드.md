# ConPort MCP 설정 및 문제 해결 가이드

## 개요

ConPort MCP(Context Portal Model Context Protocol)는 AI 어시스턴트와 개발 도구가 프로젝트 컨텍스트를 체계적으로 관리할 수 있게 해주는 데이터베이스 기반 서버입니다. 이 가이드는 ConPort MCP를 성공적으로 설치하고 실행하기 위한 단계별 과정과 발생할 수 있는 문제들의 해결 방법을 제공합니다.

## ConPort MCP란?

ConPort는 프로젝트의 "메모리 뱅크" 역할을 합니다:
- 프로젝트 결정사항, 진행상황, 시스템 설계를 추적
- 사용자 정의 프로젝트 데이터 저장 (용어집, 명세서 등)
- AI가 관련 프로젝트 정보를 빠르게 찾을 수 있도록 지원
- RAG(Retrieval Augmented Generation)를 통한 컨텍스트 인식 응답 제공
- 파일 기반 메모리 뱅크보다 효율적인 관리, 검색, 업데이트 기능

## 주요 기능

### 핵심 기능
- SQLite 기반 구조화된 컨텍스트 저장 (워크스페이스당 하나의 DB)
- Python/FastAPI로 구축된 MCP 서버
- IDE와 긴밀한 통합을 위한 STDIO 모드
- 벡터 데이터 저장 및 시맨틱 검색 기능
- 동적 프로젝트 지식 그래프 구축
- Alembic을 통한 데이터베이스 스키마 진화 관리

### 사용 가능한 도구 (30개 이상)
- **Product Context 관리**: 프로젝트 목표, 기능, 아키텍처
- **Active Context 관리**: 현재 작업 포커스, 최근 변경사항, 미해결 이슈
- **Decision Logging**: 아키텍처 및 구현 결정사항 기록
- **Progress Tracking**: 작업 상태 및 개발 진행상황
- **System Pattern 관리**: 코딩 패턴 및 규약
- **Custom Data 관리**: 프로젝트별 용어집 및 명세서
- **Semantic Search**: 모든 컨텍스트 데이터에 대한 벡터 기반 검색
- **Import/Export**: 마크다운 기반 데이터 교환
- **Relationship Mapping**: 명시적 항목 관계를 가진 지식 그래프

## 설치 및 설정

### 전제 조건
- Python 3.8 이상
- uv (권장): 빠른 Python 환경 및 패키지 관리자

### 개발자용 설치 (Git 리포지토리에서)

1. **리포지토리 클론**:
```bash
git clone https://github.com/GreatScottyMac/context-portal.git
cd context-portal
```

2. **가상 환경 생성 및 활성화**:
```bash
# uv 사용
uv venv

# 환경 활성화
# Linux/macOS:
source .venv/bin/activate
# Windows (PowerShell):
.venv\Scripts\Activate.ps1
```

3. **의존성 설치**:
```bash
uv pip install -r requirements.txt
```

4. **설치 확인**:
```bash
uv run python src/context_portal_mcp/main.py --help
```

## 발생한 문제들과 해결 방법

### 문제 1: IndentationError in database.py

**오류 메시지**:
```
IndentationError: expected an indented block after 'if' statement on line 275
```

**원인**: `database.py` 파일의 `finally:` 블록에서 들여쓰기된 코드가 누락됨

**해결 방법**:
`context-portal/src/context_portal_mcp/db/database.py` 파일의 275번째 줄 근처를 수정:

```python
# 수정 전 (잘못된 형태):
    finally:
        if cursor:
def get_active_context(workspace_id: str) -> models.ActiveContext:

# 수정 후 (올바른 형태):
    finally:
        if cursor:
            cursor.close()

def get_active_context(workspace_id: str) -> models.ActiveContext:
```

### 문제 2: Log Level Validation Error

**오류 메시지**:
```
pydantic_core._pydantic_core.ValidationError: 1 validation error for Settings
log_level
  Input should be 'DEBUG', 'INFO', 'WARNING', 'ERROR' or 'CRITICAL' [type=literal_error, input_value='info', input_type=str]
```

**원인**: `.env` 파일에서 `LOG_LEVEL=info` (소문자)로 설정되어 있었지만, Pydantic 검증에서는 대문자를 요구함

**해결 방법**:
프로젝트 루트의 `.env` 파일을 수정:

```properties
# 수정 전:
LOG_LEVEL=info

# 수정 후:
LOG_LEVEL=INFO
```

**주의사항**: 다른 환경 변수도 확인해야 할 수 있습니다:
- `FASTMCP_LOG_LEVEL`
- `FASTMCP_SERVER_LOG_LEVEL`

### 문제 3: 환경 변수 충돌

**확인 방법**:
```powershell
# 로그 관련 환경 변수 확인
Get-ChildItem Env: | Where-Object {$_.Name -like "*log*" -or $_.Name -like "*LOG*"}

# FASTMCP 관련 환경 변수 확인
Get-ChildItem Env: | Where-Object {$_.Name -like "*FASTMCP*"}
```

**해결 방법**:
문제가 되는 환경 변수 제거:
```powershell
Remove-Item env:LOG_LEVEL
Remove-Item env:LOG_FILE
```

## 실행 및 테스트

### HTTP 모드로 실행 (테스트용)
```bash
python src/context_portal_mcp/main.py --mode http --workspace_id "C:\Your\Project\Path" --log-level INFO --port 8001
```

### STDIO 모드로 실행 (IDE 통합용)
```bash
python src/context_portal_mcp/main.py --mode stdio --workspace_id "C:\Your\Project\Path" --log-level INFO
```

### 실행 확인
HTTP 모드인 경우:
```powershell
# PowerShell에서 테스트
Invoke-WebRequest -Uri "http://127.0.0.1:8001/" -Method GET
```

성공적인 응답:
```json
{"message":"ConPort MCP Server is running. MCP endpoint at /mcp"}
```

## IDE 통합 설정

### uvx를 사용한 MCP 클라이언트 설정

`mcp_settings.json` 파일에 다음 설정 추가:

```json
{
  "mcpServers": {
    "conport": {
      "command": "uvx",
      "args": [
        "--from",
        "context-portal-mcp",
        "conport-mcp",
        "--mode",
        "stdio",
        "--workspace_id",
        "${workspaceFolder}",
        "--log-file",
        "./logs/conport.log",
        "--log-level",
        "INFO"
      ]
    }
  }
}
```

### 수동 설정 (개발자 모드)

로컬에서 클론한 경우:
```json
{
  "mcpServers": {
    "conport": {
      "command": "python",
      "args": [
        "path/to/context-portal/src/context_portal_mcp/main.py",
        "--mode",
        "stdio",
        "--workspace_id",
        "${workspaceFolder}",
        "--log-level",
        "INFO"
      ]
    }
  }
}
```

## 프로젝트 초기화

### 1. projectBrief.md 파일 생성 (권장)

프로젝트 루트에 `projectBrief.md` 파일을 생성하고 다음 내용을 포함:

```markdown
# 프로젝트 개요

## 목표
- 프로젝트의 주요 목표나 목적

## 주요 기능
- 핵심 기능이나 컴포넌트

## 대상 사용자
- 타겟 사용자나 고객

## 기술 스택
- 전체적인 아키텍처 스타일이나 주요 기술

## 기타 중요 정보
- 프로젝트를 정의하는 기타 기본 정보
```

### 2. LLM 에이전트 사용자 지정 지침

적절한 전략 파일을 LLM의 사용자 지정 지침에 추가:

- **범용**: `generic_conport_strategy`
- **Roo Code**: `roo_code_conport_strategy`
- **CLine**: `cline_conport_strategy`
- **Windsurf Cascade**: `cascade_conport_strategy`

## 일반적인 문제 해결

### 1. 모듈 import 오류
```bash
# 프로젝트 루트에서 실행했는지 확인
cd context-portal
python src/context_portal_mcp/main.py --help
```

### 2. 권한 오류
```bash
# 가상 환경이 활성화되었는지 확인
source .venv/bin/activate  # Linux/macOS
.venv\Scripts\Activate.ps1  # Windows PowerShell
```

### 3. 데이터베이스 오류
```bash
# workspace_id가 유효한 절대 경로인지 확인
--workspace_id "C:\Full\Absolute\Path\To\Project"
```

### 4. 로그 확인
```bash
# 로그 파일을 지정하여 디버깅 정보 확인
--log-file "./logs/conport.log" --log-level DEBUG
```

## 다른 프로젝트에 적용하기

### 체크리스트

1. **Python 환경 준비**
   - [ ] Python 3.8+ 설치 확인
   - [ ] uv 설치 (권장)

2. **ConPort MCP 설치**
   - [ ] 리포지토리 클론 또는 uvx 사용
   - [ ] 가상 환경 생성 및 활성화
   - [ ] 의존성 설치

3. **환경 설정 확인**
   - [ ] `.env` 파일의 `LOG_LEVEL=INFO` (대문자) 확인
   - [ ] 충돌하는 환경 변수 제거
   - [ ] 워크스페이스 경로가 절대 경로인지 확인

4. **프로젝트 초기화**
   - [ ] `projectBrief.md` 파일 생성
   - [ ] IDE MCP 클라이언트 설정
   - [ ] LLM 에이전트 사용자 지정 지침 추가

5. **테스트 및 검증**
   - [ ] HTTP 모드로 실행 테스트
   - [ ] STDIO 모드로 실행 테스트
   - [ ] IDE 통합 확인

### 프로젝트별 커스터마이징

1. **워크스페이스 경로 설정**:
   ```bash
   --workspace_id "/absolute/path/to/your/project"
   ```

2. **로그 설정 조정**:
   ```bash
   --log-file "./logs/conport-yourproject.log"
   --log-level DEBUG  # 또는 INFO, WARNING, ERROR, CRITICAL
   ```

3. **포트 설정 (HTTP 모드)**:
   ```bash
   --port 8002  # 다른 서비스와 충돌 방지
   ```

## 결론

ConPort MCP는 AI 어시스턴트와 개발자 도구에게 구조화된 프로젝트 컨텍스트를 제공하는 강력한 도구입니다. 위의 해결 방법들을 따르면 대부분의 설치 및 설정 문제를 해결할 수 있으며, 다양한 프로젝트에서 효과적으로 활용할 수 있습니다.

### 주요 성공 요소
- 올바른 Python 환경 설정
- 환경 변수 충돌 해결
- 절대 경로를 사용한 워크스페이스 지정
- 적절한 IDE 통합 설정

이 가이드를 통해 ConPort MCP를 성공적으로 설치하고 운영하여 프로젝트 개발 효율성을 크게 향상시킬 수 있습니다.
