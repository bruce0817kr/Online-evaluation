# Universal Port Manager 설치 가이드

## 의존성 설치

### Ubuntu/Debian 시스템
```bash
# 시스템 패키지 설치
sudo apt update
sudo apt install -y python3-pip python3-psutil python3-click python3-yaml

# 또는 pip를 통한 설치
pip3 install -r requirements.txt
```

### CentOS/RHEL/Fedora 시스템
```bash
# 시스템 패키지 설치
sudo yum install -y python3-pip python3-psutil python3-click python3-pyyaml

# 또는 pip를 통한 설치
pip3 install -r requirements.txt
```

### Windows 시스템
```cmd
# pip를 통한 설치
pip install -r requirements.txt
```

### macOS 시스템
```bash
# Homebrew 사용
brew install python3

# pip를 통한 설치
pip3 install -r requirements.txt
```

## CLI 사용법

### 모듈로 실행
```bash
# 기본 사용법
python3 -m universal_port_manager --help

# 포트 할당
python3 -m universal_port_manager --project myproject allocate frontend backend mongodb redis

# 포트 스캔
python3 -m universal_port_manager scan --range 3000-9999

# 프로젝트 상태 확인
python3 -m universal_port_manager --project myproject status
```

### 직접 실행
```bash
# cli.py 직접 실행
python3 universal_port_manager/cli.py --help
```

## 문제 해결

### "Got unexpected extra arguments" 오류
이 오류는 주로 다음 이유로 발생합니다:

1. **__main__.py 파일 누락**: 모듈로 실행하려면 `__main__.py` 파일이 필요합니다.
2. **의존성 누락**: click, psutil, PyYAML 패키지가 설치되지 않았을 때
3. **CLI 구조 문제**: Click 그룹/커맨드 구조가 올바르지 않을 때

### 해결 방법
1. 의존성 설치 확인
2. __main__.py 파일 존재 확인
3. Python 경로 확인

### 디버그 모드
```bash
# 상세 출력으로 실행
python3 -m universal_port_manager --verbose --project myproject allocate frontend backend
```