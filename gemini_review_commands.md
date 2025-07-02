# Gemini CLI 코드 리뷰 명령어

다음 명령어를 Windows CMD나 PowerShell에서 실행하세요:

## 전체 프로젝트 리뷰
gemini --all_files -p "이 온라인 평가 시스템의 전체 코드를 검토하고 개선점을 제안해주세요. 아키텍처, 보안, 성능, 코드품질 관점에서 분석해주세요."

## 특정 파일들 중점 리뷰  
gemini -p "@backend/server.py @frontend/src/App.js @universal_port_manager/ 이 핵심 파일들을 검토하고 품질을 평가해주세요."

## 보안 중점 리뷰
gemini -p "@backend/security.py @backend/server.py 보안 측면에서 이 코드들을 검토하고 취약점을 찾아주세요."

## 테스트 코드 리뷰
gemini -p "@frontend/src/components/__tests__/ @jest.config.js @playwright.config.js 테스트 설정과 품질을 검토해주세요."

## 성능 최적화 리뷰
gemini -p "@frontend/craco.config.js @docker-compose.yml @fast-build.sh 성능 최적화가 잘 되어있는지 검토해주세요."

