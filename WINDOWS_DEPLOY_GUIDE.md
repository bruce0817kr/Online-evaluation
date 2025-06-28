# Windows 배포 문제 해결 가이드

Windows에서 배치 파일 실행 시 문제가 발생하는 경우 다음 단계를 따라 해결하세요.

## 🔧 문제 해결 단계

### 1단계: 환경 테스트
```cmd
test-env.bat
```
이 명령어로 환경이 올바르게 설정되어 있는지 확인하세요.

### 2단계: 간단한 배포 시도
```cmd
simple-deploy.bat
```
더 간단한 배치 파일로 먼저 시도해보세요.

### 3단계: Python 직접 실행 (추천)
```cmd
python quick-deploy.py
```
가장 안정적인 방법입니다. 모든 플랫폼에서 동작합니다.

## 🐛 일반적인 문제들

### 문제 1: 한글 깨짐
**증상**: 배치 파일에서 한글이 깨져서 나타남
**해결**: 
- 명령 프롬프트를 관리자 권한으로 실행
- `chcp 65001` 명령어 실행 후 배치 파일 재실행

### 문제 2: Python 모듈을 찾을 수 없음
**증상**: `ModuleNotFoundError: No module named 'universal_port_manager'`
**해결**:
```cmd
# 현재 디렉토리 확인
cd /d "C:\Project\Online-evaluation"

# Python 경로 확인
python -c "import sys; print(sys.path)"

# 직접 실행
python -m universal_port_manager.cli doctor
```

### 문제 3: Docker 오류
**증상**: Docker 관련 오류 메시지
**해결**:
1. Docker Desktop이 실행 중인지 확인
2. Docker Desktop을 관리자 권한으로 실행
3. WSL2 백엔드가 활성화되어 있는지 확인

### 문제 4: 권한 오류
**증상**: `Access Denied` 또는 권한 관련 오류
**해결**:
1. 명령 프롬프트를 관리자 권한으로 실행
2. PowerShell을 관리자 권한으로 실행해서 시도

## 🎯 권장 실행 방법

### 방법 1: PowerShell 사용 (권장)
```powershell
# 관리자 권한으로 PowerShell 실행
cd "C:\Project\Online-evaluation"
python quick-deploy.py
```

### 방법 2: 명령 프롬프트 사용
```cmd
# 관리자 권한으로 cmd 실행
cd /d "C:\Project\Online-evaluation"
chcp 65001
python quick-deploy.py
```

### 방법 3: Windows Terminal 사용
```cmd
# Windows Terminal을 관리자 권한으로 실행
wt -d "C:\Project\Online-evaluation" cmd /k "python quick-deploy.py"
```

## 🔍 디버깅 단계

### 1. 환경 확인
```cmd
# Python 버전 확인
python --version

# Docker 버전 확인
docker --version

# 현재 디렉토리 확인
dir

# 포트 매니저 모듈 확인
python -c "from universal_port_manager import cli; print('OK')"
```

### 2. 포트 상태 확인
```cmd
# 현재 사용 중인 포트 확인
netstat -an | findstr LISTEN

# Universal Port Manager로 포트 스캔
python -m universal_port_manager.cli scan --range 3000-9000
```

### 3. Docker 상태 확인
```cmd
# Docker 실행 상태 확인
docker info

# 기존 컨테이너 확인
docker ps -a

# 프로젝트별 컨테이너 확인
docker-compose -p online-evaluation ps
```

## 🚀 성공적인 배포 후 확인

배포가 성공하면 다음 주소들이 열립니다:

- **프론트엔드**: `http://localhost:[할당된포트]`
- **백엔드 API**: `http://localhost:[할당된포트]/docs`

포트 번호는 `ports.json` 파일에서 확인할 수 있습니다.

## 🆘 추가 도움이 필요한 경우

1. **로그 확인**:
   ```cmd
   docker-compose -p online-evaluation logs --tail=50
   ```

2. **서비스 상태 확인**:
   ```cmd
   docker-compose -p online-evaluation ps
   ```

3. **완전 재시작**:
   ```cmd
   docker-compose -p online-evaluation down
   python quick-deploy.py
   ```

4. **시스템 정리 후 재시도**:
   ```cmd
   docker system prune -f
   python quick-deploy.py
   ```

## 💡 팁

- **항상 관리자 권한으로 실행**하세요
- **Windows Defender 실시간 보호**가 방해할 수 있으니 필요시 일시적으로 비활성화
- **WSL2 환경**에서는 Linux 명령어를 사용할 수 있습니다
- **Visual Studio Code**에서 터미널을 열어서 실행하는 것도 좋은 방법입니다