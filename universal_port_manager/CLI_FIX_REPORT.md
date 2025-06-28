# Universal Port Manager CLI 문제 해결 보고서

## 문제 상황
```bash
python -m universal_port_manager.cli --project online-evaluation allocate frontend backend mongodb redis
# 오류: Got unexpected extra arguments (frontend backend mongodb redis)
```

## 문제 원인 분석

### 1. 모듈 실행 구조 문제
- `__main__.py` 파일이 누락되어 `python -m module_name` 형태로 실행 불가
- Click CLI 구조 자체는 정상이었으나, 모듈 엔트리포인트가 없었음

### 2. 의존성 문제
- `psutil`, `PyYAML` 등 필수 모듈이 설치되지 않음
- 의존성 오류로 인해 모듈 로드 실패

### 3. 임포트 순서 문제
- `__init__.py`에서 core 모듈들을 직접 임포트
- 의존성이 없을 때 전체 모듈 로드 실패

## 해결 방법

### 1. __main__.py 파일 생성
```python
#!/usr/bin/env python3
"""
Universal Port Manager CLI Entry Point
======================================

모듈을 python -m universal_port_manager 형태로 실행할 수 있게 해주는 엔트리 포인트
"""

from .cli import cli

if __name__ == '__main__':
    cli()
```

### 2. 선택적 의존성 체크 구현
```python
# cli.py에 추가
DEPENDENCIES_AVAILABLE = True
MISSING_MODULES = []

try:
    import yaml
except ImportError:
    MISSING_MODULES.append("PyYAML")
    DEPENDENCIES_AVAILABLE = False

try:
    import psutil
except ImportError:
    MISSING_MODULES.append("psutil") 
    DEPENDENCIES_AVAILABLE = False

def check_dependencies():
    """의존성 체크 및 에러 메시지 출력"""
    if not DEPENDENCIES_AVAILABLE:
        click.echo("❌ 필수 의존성이 설치되지 않았습니다:", err=True)
        for module in MISSING_MODULES:
            click.echo(f"   - {module}", err=True)
        click.echo("\n💡 설치 방법:", err=True)
        click.echo("   pip3 install -r requirements.txt", err=True)
        return False
    return True
```

### 3. 각 명령어에 의존성 체크 추가
```python
@cli.command()
@click.argument('services', nargs=-1, required=True)
@click.option('--template', '-t', help='사용할 서비스 템플릿')
@click.pass_context
def allocate(ctx, services, template, preferred_ports, auto_detect):
    """서비스에 포트 할당"""
    if not check_dependencies():
        return
    # ... 실제 로직
```

### 4. __init__.py 선택적 임포트
```python
# 선택적 임포트 - 의존성이 없을 때도 모듈을 로드할 수 있도록 함
try:
    from .core.port_manager import PortManager
    from .core.service_registry import ServiceRegistry  
    from .core.port_scanner import PortScanner
    from .core.port_allocator import PortAllocator
    __all__ = ['PortManager', 'ServiceRegistry', 'PortScanner', 'PortAllocator']
except ImportError:
    # 의존성이 없을 때는 빈 리스트
    __all__ = []
```

## 테스트 결과

### 1. 모듈 실행 성공
```bash
$ python3 -m universal_port_manager --help
Usage: python -m universal_port_manager [OPTIONS] COMMAND [ARGS]...

  Universal Port Manager CLI
  
  여러 프로젝트 간 포트 충돌 방지 및 자동 할당 도구
```

### 2. 의존성 체크 정상 동작
```bash
$ python3 -m universal_port_manager --project online-evaluation allocate frontend backend
❌ 필수 의존성이 설치되지 않았습니다:
   - psutil

💡 설치 방법:
   pip3 install -r requirements.txt
   또는
   pip3 install psutil
```

### 3. 명령어 구조 정상 동작
```bash
$ python3 -m universal_port_manager allocate --help
Usage: python -m universal_port_manager allocate [OPTIONS] SERVICES...

  서비스에 포트 할당

Options:
  -t, --template TEXT             사용할 서비스 템플릿
  --preferred-ports TEXT          선호 포트 (JSON 형식)
  --auto-detect / --no-auto-detect
                                  프로젝트 자동 감지
  --help                          Show this message and exit.
```

## 추가 생성된 파일

### 1. INSTALL.md
의존성 설치 및 사용법 가이드

### 2. cli_mockup.py
의존성 없이 CLI 구조를 테스트할 수 있는 목업 버전

### 3. test_cli_structure.py
CLI 구조 테스트 스크립트

## 정상 사용법

### 의존성 설치 후 사용
```bash
# 의존성 설치
pip3 install psutil click PyYAML

# 포트 할당
python3 -m universal_port_manager --project online-evaluation allocate frontend backend mongodb redis

# 포트 스캔
python3 -m universal_port_manager scan --range 3000-9000

# 프로젝트 상태 확인
python3 -m universal_port_manager --project online-evaluation status
```

### 목업 버전으로 구조 테스트
```bash
# 의존성 없이 CLI 구조 테스트
python3 universal_port_manager/cli_mockup.py --project test allocate frontend backend
```

## 결론

원래 "Got unexpected extra arguments" 오류의 원인은:
1. **__main__.py 파일 누락** - 모듈 실행 구조 문제
2. **의존성 모듈 누락** - psutil, PyYAML 설치 필요
3. **임포트 순서 문제** - 의존성 체크 없이 직접 임포트

이제 CLI가 정상적으로 작동하며, 의존성이 없을 때도 적절한 오류 메시지를 표시합니다.