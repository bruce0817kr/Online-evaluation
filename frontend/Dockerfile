# Frontend Production Dockerfile
FROM node:18-alpine as builder

# 메타데이터
LABEL maintainer="Online Evaluation System"
LABEL version="2.0.0"
LABEL description="Production Frontend for Online Evaluation System"

# 작업 디렉터리 설정
WORKDIR /app

# 시스템 의존성 설치
RUN apk add --no-cache git

# package.json과 package-lock.json 복사
COPY package*.json ./

# 의존성 설치 (dependency 충돌 해결)
RUN npm install --legacy-peer-deps
# ajv 호환성 문제 해결
RUN npm install ajv@8.12.0 --legacy-peer-deps

# 소스 코드 복사
COPY . .

# 프로덕션 빌드
ENV NODE_ENV=production
ENV GENERATE_SOURCEMAP=false
RUN npm run build

# Production stage
FROM nginx:alpine

# nginx 설정
RUN rm -rf /usr/share/nginx/html/*
COPY --from=builder /app/build /usr/share/nginx/html

# Custom nginx 설정 (있는 경우에만)
RUN echo "user nginx;" > /etc/nginx/nginx.conf && \
    echo "worker_processes auto;" >> /etc/nginx/nginx.conf && \
    echo "error_log /var/log/nginx/error.log warn;" >> /etc/nginx/nginx.conf && \
    echo "pid /var/run/nginx.pid;" >> /etc/nginx/nginx.conf && \
    echo "events { worker_connections 1024; }" >> /etc/nginx/nginx.conf && \
    echo "http {" >> /etc/nginx/nginx.conf && \
    echo "  include /etc/nginx/mime.types;" >> /etc/nginx/nginx.conf && \
    echo "  default_type application/octet-stream;" >> /etc/nginx/nginx.conf && \
    echo "  sendfile on;" >> /etc/nginx/nginx.conf && \
    echo "  keepalive_timeout 65;" >> /etc/nginx/nginx.conf && \
    echo "  server {" >> /etc/nginx/nginx.conf && \
    echo "    listen 3000;" >> /etc/nginx/nginx.conf && \
    echo "    location / {" >> /etc/nginx/nginx.conf && \
    echo "      root /usr/share/nginx/html;" >> /etc/nginx/nginx.conf && \
    echo "      index index.html index.htm;" >> /etc/nginx/nginx.conf && \
    echo "      try_files \$uri \$uri/ /index.html;" >> /etc/nginx/nginx.conf && \
    echo "    }" >> /etc/nginx/nginx.conf && \
    echo "  }" >> /etc/nginx/nginx.conf && \
    echo "}" >> /etc/nginx/nginx.conf

# 포트 노출
EXPOSE 3000

# 헬스체크
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:3000 || exit 1

# nginx 시작
CMD ["nginx", "-g", "daemon off;"]