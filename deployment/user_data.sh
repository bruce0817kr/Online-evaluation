#!/bin/bash

# 🚀 AI 모델 관리 시스템 - EC2 인스턴스 초기화 스크립트
# 백엔드 페르소나 중심의 안정적이고 성능 최적화된 환경 구성

set -euo pipefail

# 변수 설정
ENVIRONMENT="${environment}"
PROJECT_NAME="${project_name}"
LOG_FILE="/var/log/user_data.log"

# 로깅 함수
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" | tee -a "$LOG_FILE"
}

log "🚀 AI 모델 관리 시스템 백엔드 서버 초기화 시작"
log "환경: $ENVIRONMENT, 프로젝트: $PROJECT_NAME"

# 시스템 업데이트
log "📦 시스템 패키지 업데이트"
apt-get update -y
apt-get upgrade -y

# 필수 패키지 설치
log "🔧 필수 패키지 설치"
apt-get install -y \
    curl \
    wget \
    git \
    htop \
    vim \
    unzip \
    jq \
    awscli \
    software-properties-common \
    apt-transport-https \
    ca-certificates \
    gnupg \
    lsb-release

# Docker 설치
log "🐳 Docker 설치"
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg

echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu \
  $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null

apt-get update -y
apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

# Docker 서비스 시작 및 자동 시작 설정
systemctl start docker
systemctl enable docker

# Docker Compose 설치
log "🐙 Docker Compose 설치"
DOCKER_COMPOSE_VERSION="2.24.0"
curl -L "https://github.com/docker/compose/releases/download/v$DOCKER_COMPOSE_VERSION/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose
ln -sf /usr/local/bin/docker-compose /usr/bin/docker-compose

# Node.js 설치 (프론트엔드 빌드용)
log "📦 Node.js 설치"
curl -fsSL https://deb.nodesource.com/setup_18.x | bash -
apt-get install -y nodejs

# Python 설치 및 설정
log "🐍 Python 환경 설정"
apt-get install -y python3 python3-pip python3-venv
ln -sf /usr/bin/python3 /usr/bin/python

# CloudWatch Agent 설치
log "📊 CloudWatch Agent 설치"
wget https://s3.amazonaws.com/amazoncloudwatch-agent/ubuntu/amd64/latest/amazon-cloudwatch-agent.deb
dpkg -i -E ./amazon-cloudwatch-agent.deb
rm -f ./amazon-cloudwatch-agent.deb

# CloudWatch Agent 설정
cat <<EOF > /opt/aws/amazon-cloudwatch-agent/etc/amazon-cloudwatch-agent.json
{
    "agent": {
        "metrics_collection_interval": 60,
        "run_as_user": "cwagent"
    },
    "metrics": {
        "namespace": "AI-Model-Management/$ENVIRONMENT",
        "metrics_collected": {
            "cpu": {
                "measurement": [
                    "cpu_usage_idle",
                    "cpu_usage_iowait",
                    "cpu_usage_user",
                    "cpu_usage_system"
                ],
                "metrics_collection_interval": 60,
                "totalcpu": false
            },
            "disk": {
                "measurement": [
                    "used_percent"
                ],
                "metrics_collection_interval": 60,
                "resources": [
                    "*"
                ]
            },
            "diskio": {
                "measurement": [
                    "io_time"
                ],
                "metrics_collection_interval": 60,
                "resources": [
                    "*"
                ]
            },
            "mem": {
                "measurement": [
                    "mem_used_percent"
                ],
                "metrics_collection_interval": 60
            },
            "netstat": {
                "measurement": [
                    "tcp_established",
                    "tcp_time_wait"
                ],
                "metrics_collection_interval": 60
            },
            "swap": {
                "measurement": [
                    "swap_used_percent"
                ],
                "metrics_collection_interval": 60
            }
        }
    },
    "logs": {
        "logs_collected": {
            "files": {
                "collect_list": [
                    {
                        "file_path": "/var/log/user_data.log",
                        "log_group_name": "/aws/ec2/ai-model-management/$ENVIRONMENT/user-data",
                        "log_stream_name": "{instance_id}",
                        "timezone": "UTC"
                    },
                    {
                        "file_path": "/var/log/docker.log",
                        "log_group_name": "/aws/ec2/ai-model-management/$ENVIRONMENT/docker",
                        "log_stream_name": "{instance_id}",
                        "timezone": "UTC"
                    },
                    {
                        "file_path": "/app/logs/app.log",
                        "log_group_name": "/aws/ec2/ai-model-management/$ENVIRONMENT/application",
                        "log_stream_name": "{instance_id}",
                        "timezone": "UTC"
                    }
                ]
            }
        }
    }
}
EOF

# CloudWatch Agent 시작
systemctl enable amazon-cloudwatch-agent
systemctl start amazon-cloudwatch-agent

# Prometheus Node Exporter 설치
log "📈 Prometheus Node Exporter 설치"
useradd --no-create-home --shell /bin/false node_exporter
cd /tmp
wget https://github.com/prometheus/node_exporter/releases/download/v1.7.0/node_exporter-1.7.0.linux-amd64.tar.gz
tar xvf node_exporter-1.7.0.linux-amd64.tar.gz
cp node_exporter-1.7.0.linux-amd64/node_exporter /usr/local/bin/
chown node_exporter:node_exporter /usr/local/bin/node_exporter
rm -rf node_exporter-1.7.0*

# Node Exporter systemd 서비스 생성
cat <<EOF > /etc/systemd/system/node_exporter.service
[Unit]
Description=Node Exporter
Wants=network-online.target
After=network-online.target

[Service]
User=node_exporter
Group=node_exporter
Type=simple
ExecStart=/usr/local/bin/node_exporter \
    --web.listen-address=":9100" \
    --collector.systemd \
    --collector.processes

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable node_exporter
systemctl start node_exporter

# Docker 로그 설정 최적화
log "📝 Docker 로깅 설정 최적화"
cat <<EOF > /etc/docker/daemon.json
{
    "log-driver": "json-file",
    "log-opts": {
        "max-size": "10m",
        "max-file": "3"
    },
    "storage-driver": "overlay2",
    "exec-opts": ["native.cgroupdriver=systemd"],
    "live-restore": true,
    "userland-proxy": false,
    "experimental": false
}
EOF

systemctl restart docker

# 애플리케이션 디렉터리 생성
log "📁 애플리케이션 디렉터리 설정"
mkdir -p /app/logs
mkdir -p /app/uploads
mkdir -p /app/config
chmod 755 /app
chmod 755 /app/logs
chmod 755 /app/uploads

# 환경 변수 파일 생성
log "⚙️ 환경 변수 설정"
cat <<EOF > /app/.env
# 환경 설정
NODE_ENV=$ENVIRONMENT
ENVIRONMENT=$ENVIRONMENT
PROJECT_NAME=$PROJECT_NAME

# 로깅 설정
LOG_LEVEL=INFO
LOG_FILE=/app/logs/app.log

# 성능 설정
UVICORN_WORKERS=4
UVICORN_MAX_REQUESTS=1000
UVICORN_MAX_REQUESTS_JITTER=100

# 헬스체크 설정
HEALTH_CHECK_INTERVAL=30
HEALTH_CHECK_TIMEOUT=10
HEALTH_CHECK_RETRIES=3

# AWS 메타데이터
INSTANCE_ID=$(curl -s http://169.254.169.254/latest/meta-data/instance-id)
AVAILABILITY_ZONE=$(curl -s http://169.254.169.254/latest/meta-data/placement/availability-zone)
INSTANCE_TYPE=$(curl -s http://169.254.169.254/latest/meta-data/instance-type)
EOF

# AWS CLI 설정 (IAM Role 사용)
log "🔑 AWS CLI 설정"
aws configure set region ap-northeast-2
aws configure set output json

# ECR 로그인 스크립트 생성
log "🔐 ECR 로그인 스크립트 생성"
cat <<'EOF' > /usr/local/bin/ecr-login.sh
#!/bin/bash
REGION="ap-northeast-2"
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
ECR_REGISTRY="$ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com"

aws ecr get-login-password --region $REGION | docker login --username AWS --password-stdin $ECR_REGISTRY
echo "ECR 로그인 완료: $ECR_REGISTRY"
EOF

chmod +x /usr/local/bin/ecr-login.sh

# ECR 로그인 cron job 설정 (토큰 갱신)
echo "0 */6 * * * root /usr/local/bin/ecr-login.sh" >> /etc/crontab

# 배포 스크립트 생성
log "🚀 배포 스크립트 생성"
cat <<'EOF' > /usr/local/bin/deploy-backend.sh
#!/bin/bash

set -euo pipefail

ENVIRONMENT="${ENVIRONMENT:-staging}"
PROJECT_NAME="${PROJECT_NAME:-ai-model-mgmt}"
ECR_REGISTRY="${ECR_REGISTRY}"
IMAGE_TAG="${IMAGE_TAG:-latest}"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*"
}

log "🚀 백엔드 서비스 배포 시작"

# ECR 로그인
/usr/local/bin/ecr-login.sh

# 기존 컨테이너 중지 및 제거
log "🛑 기존 컨테이너 중지"
docker-compose -f /app/docker-compose.yml down || true

# 새 이미지 풀
log "📥 새 이미지 다운로드"
docker pull $ECR_REGISTRY/$PROJECT_NAME/backend:$IMAGE_TAG

# 새 컨테이너 시작
log "🔄 새 컨테이너 시작"
cd /app
docker-compose up -d

# 헬스체크
log "🏥 헬스체크 실행"
sleep 30

for i in {1..12}; do
    if curl -f http://localhost:8000/health; then
        log "✅ 헬스체크 성공"
        exit 0
    fi
    log "⏳ 헬스체크 대기 중... (시도 $i/12)"
    sleep 10
done

log "❌ 헬스체크 실패"
exit 1
EOF

chmod +x /usr/local/bin/deploy-backend.sh

# 시스템 최적화 설정
log "⚡ 시스템 성능 최적화"

# 커널 파라미터 최적화
cat <<EOF >> /etc/sysctl.conf
# 네트워크 성능 최적화
net.core.somaxconn = 65535
net.core.netdev_max_backlog = 5000
net.ipv4.tcp_max_syn_backlog = 8192
net.ipv4.tcp_fin_timeout = 30
net.ipv4.tcp_keepalive_time = 1200
net.ipv4.tcp_keepalive_probes = 9
net.ipv4.tcp_keepalive_intvl = 75

# 메모리 관리 최적화
vm.swappiness = 10
vm.dirty_ratio = 15
vm.dirty_background_ratio = 5

# 파일 핸들러 최적화
fs.file-max = 2097152
EOF

sysctl -p

# 시스템 한계 설정
cat <<EOF >> /etc/security/limits.conf
* soft nofile 65535
* hard nofile 65535
* soft nproc 65535
* hard nproc 65535
EOF

# 방화벽 설정 (기본적인 보안)
log "🔥 방화벽 설정"
ufw --force enable
ufw default deny incoming
ufw default allow outgoing
ufw allow 22/tcp
ufw allow 8000:8002/tcp
ufw allow 9100/tcp

# 자동 업데이트 설정
log "🔄 자동 보안 업데이트 설정"
apt-get install -y unattended-upgrades
echo 'Unattended-Upgrade::Automatic-Reboot "false";' >> /etc/apt/apt.conf.d/50unattended-upgrades

# 로그 로테이션 설정
log "📝 로그 로테이션 설정"
cat <<EOF > /etc/logrotate.d/ai-model-mgmt
/app/logs/*.log {
    daily
    rotate 7
    compress
    delaycompress
    missingok
    notifempty
    create 644 root root
    postrotate
        docker kill -s USR1 \$(docker ps -q --filter label=app=ai-model-backend) 2>/dev/null || true
    endscript
}
EOF

# 시간 동기화 설정
log "⏰ 시간 동기화 설정"
apt-get install -y chrony
systemctl enable chrony
systemctl start chrony

# fail2ban 설치 및 설정 (보안 강화)
log "🛡️ fail2ban 보안 설정"
apt-get install -y fail2ban

cat <<EOF > /etc/fail2ban/jail.local
[sshd]
enabled = true
port = 22
filter = sshd
logpath = /var/log/auth.log
maxretry = 3
bantime = 3600
findtime = 600

[nginx-http-auth]
enabled = true
port = http,https
filter = nginx-http-auth
logpath = /var/log/nginx/error.log
maxretry = 5
bantime = 3600
EOF

systemctl enable fail2ban
systemctl start fail2ban

# 시스템 상태 모니터링 스크립트
log "📊 시스템 모니터링 스크립트 생성"
cat <<'EOF' > /usr/local/bin/system-health-check.sh
#!/bin/bash

INSTANCE_ID=$(curl -s http://169.254.169.254/latest/meta-data/instance-id)
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')

# CPU 사용률
CPU_USAGE=$(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | awk -F'%' '{print $1}')

# 메모리 사용률
MEMORY_USAGE=$(free | grep Mem | awk '{printf("%.1f"), $3/$2 * 100.0}')

# 디스크 사용률
DISK_USAGE=$(df -h | grep -vE '^Filesystem|tmpfs|cdrom' | awk '{print $5}' | head -1 | cut -d'%' -f1)

# Docker 컨테이너 상태
DOCKER_STATUS=$(docker ps --format "table {{.Names}}\t{{.Status}}" | grep -v NAMES | wc -l)

echo "[$TIMESTAMP] Instance: $INSTANCE_ID | CPU: ${CPU_USAGE}% | Memory: ${MEMORY_USAGE}% | Disk: ${DISK_USAGE}% | Containers: $DOCKER_STATUS"

# CloudWatch 사용자 정의 메트릭 전송
aws cloudwatch put-metric-data \
    --namespace "AI-Model-Management/Custom" \
    --metric-data MetricName=HealthCheck,Value=1,Unit=Count,Dimensions=InstanceId=$INSTANCE_ID
EOF

chmod +x /usr/local/bin/system-health-check.sh

# 헬스체크 cron job 설정
echo "*/5 * * * * root /usr/local/bin/system-health-check.sh" >> /etc/crontab

# 최종 시스템 정리
log "🧹 시스템 정리"
apt-get autoremove -y
apt-get autoclean

# 부팅 시 ECR 로그인 설정
echo "@reboot root sleep 60 && /usr/local/bin/ecr-login.sh" >> /etc/crontab

log "✅ AI 모델 관리 시스템 백엔드 서버 초기화 완료"
log "🚀 서버가 배포 준비되었습니다!"

# 시스템 정보 출력
log "📋 시스템 정보:"
log "  - 인스턴스 ID: $(curl -s http://169.254.169.254/latest/meta-data/instance-id)"
log "  - 인스턴스 타입: $(curl -s http://169.254.169.254/latest/meta-data/instance-type)"
log "  - 가용 영역: $(curl -s http://169.254.169.254/latest/meta-data/placement/availability-zone)"
log "  - Docker 버전: $(docker --version)"
log "  - Docker Compose 버전: $(docker-compose --version)"
log "  - Node.js 버전: $(node --version)"
log "  - Python 버전: $(python --version)"

# 서비스 상태 확인
systemctl is-active docker && log "✅ Docker 서비스 활성화" || log "❌ Docker 서비스 비활성화"
systemctl is-active amazon-cloudwatch-agent && log "✅ CloudWatch Agent 활성화" || log "❌ CloudWatch Agent 비활성화"
systemctl is-active node_exporter && log "✅ Node Exporter 활성화" || log "❌ Node Exporter 비활성화"
systemctl is-active fail2ban && log "✅ fail2ban 활성화" || log "❌ fail2ban 비활성화"

log "🎯 백엔드 페르소나를 위한 최적화된 환경 구성 완료"
log "   - 성능 최적화: 커널 파라미터, 시스템 한계 조정"
log "   - 보안 강화: 방화벽, fail2ban, 최소 권한"
log "   - 모니터링: CloudWatch, Prometheus, 시스템 헬스체크"
log "   - 자동화: ECR 로그인, 배포 스크립트, 로그 로테이션"

# 초기화 완료 신호
touch /var/log/user_data_completed
log "🏁 사용자 데이터 스크립트 실행 완료"