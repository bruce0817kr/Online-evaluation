# Backend Production Dockerfile
FROM python:3.11-slim

# 메타데이터
LABEL maintainer="Online Evaluation System"
LABEL version="2.0.0"
LABEL description="Production Backend for Online Evaluation System"

# 작업 디렉터리 설정
WORKDIR /app

# 시스템 패키지 설치
RUN apt-get update && apt-get install -y \
    curl \
    gcc \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Python 환경 설정
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

# requirements.txt 복사 및 의존성 설치
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# 애플리케이션 소스 복사
COPY . .

# 필요한 디렉터리 생성
RUN mkdir -p uploads logs

# 포트 노출
EXPOSE 8080

# 헬스체크
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

# 프로덕션 서버 시작
CMD ["python", "-m", "uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8080", "--workers", "4"]