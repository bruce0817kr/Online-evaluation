#!/bin/bash

# Docker Security Hardening Script for Online Evaluation System
# This script implements Docker security best practices for production deployment

set -euo pipefail

echo "🔒 Starting Docker Security Hardening for Online Evaluation System"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Security hardening functions

harden_docker_daemon() {
    echo -e "${YELLOW}🔧 Hardening Docker daemon configuration...${NC}"
    
    # Create Docker daemon configuration
    sudo mkdir -p /etc/docker
    
    cat > /tmp/daemon.json << EOF
{
    "live-restore": true,
    "userland-proxy": false,
    "no-new-privileges": true,
    "seccomp-profile": "/etc/docker/seccomp-profile.json",
    "apparmor-profile": "docker-default",
    "selinux-enabled": true,
    "disable-legacy-registry": true,
    "experimental": false,
    "metrics-addr": "127.0.0.1:9323",
    "log-driver": "json-file",
    "log-opts": {
        "max-size": "10m",
        "max-file": "3"
    },
    "storage-driver": "overlay2",
    "storage-opts": [
        "overlay2.override_kernel_check=true"
    ],
    "default-ulimits": {
        "nofile": {
            "name": "nofile",
            "hard": 64000,
            "soft": 64000
        }
    }
}
EOF
    
    sudo cp /tmp/daemon.json /etc/docker/daemon.json
    
    echo -e "${GREEN}✅ Docker daemon configuration hardened${NC}"
}

create_seccomp_profile() {
    echo -e "${YELLOW}🔧 Creating custom seccomp profile...${NC}"
    
    cat > /tmp/seccomp-profile.json << 'EOF'
{
    "defaultAction": "SCMP_ACT_ERRNO",
    "architectures": [
        "SCMP_ARCH_X86_64",
        "SCMP_ARCH_X86",
        "SCMP_ARCH_X32"
    ],
    "syscalls": [
        {
            "names": [
                "accept", "accept4", "access", "adjtimex", "alarm", "bind", "brk", "capget", "capset", "chdir", "chmod", "chown",
                "chroot", "clock_getres", "clock_gettime", "clock_nanosleep", "clone", "close", "connect", "copy_file_range",
                "creat", "dup", "dup2", "dup3", "epoll_create", "epoll_create1", "epoll_ctl", "epoll_pwait", "epoll_wait",
                "eventfd", "eventfd2", "execve", "execveat", "exit", "exit_group", "faccessat", "fadvise64", "fallocate",
                "fanotify_mark", "fchdir", "fchmod", "fchmodat", "fchown", "fchownat", "fcntl", "fdatasync", "fgetxattr",
                "flistxattr", "flock", "fork", "fremovexattr", "fsetxattr", "fstat", "fstatfs", "fsync", "ftruncate",
                "futex", "getcwd", "getdents", "getdents64", "getegid", "geteuid", "getgid", "getgroups", "getitimer",
                "getpeername", "getpgid", "getpgrp", "getpid", "getppid", "getpriority", "getrandom", "getresgid",
                "getresuid", "getrlimit", "get_robust_list", "getrusage", "getsid", "getsockname", "getsockopt", "get_thread_area",
                "gettid", "gettimeofday", "getuid", "getxattr", "inotify_add_watch", "inotify_init", "inotify_init1",
                "inotify_rm_watch", "io_cancel", "ioctl", "io_destroy", "io_getevents", "ioprio_get", "ioprio_set",
                "io_setup", "io_submit", "ipc", "kill", "lchown", "lgetxattr", "link", "linkat", "listen", "listxattr",
                "llistxattr", "lremovexattr", "lseek", "lsetxattr", "lstat", "madvise", "memfd_create", "mincore",
                "mkdir", "mkdirat", "mknod", "mknodat", "mlock", "mlock2", "mlockall", "mmap", "mmap2", "mprotect",
                "mq_getsetattr", "mq_notify", "mq_open", "mq_timedreceive", "mq_timedsend", "mq_unlink", "mremap",
                "msgctl", "msgget", "msgrcv", "msgsnd", "msync", "munlock", "munlockall", "munmap", "nanosleep",
                "newfstatat", "open", "openat", "pause", "pipe", "pipe2", "poll", "ppoll", "prctl", "pread64",
                "preadv", "prlimit64", "pselect6", "ptrace", "pwrite64", "pwritev", "read", "readahead", "readlink",
                "readlinkat", "readv", "recv", "recvfrom", "recvmmsg", "recvmsg", "remap_file_pages", "removexattr",
                "rename", "renameat", "renameat2", "restart_syscall", "rmdir", "rt_sigaction", "rt_sigpending",
                "rt_sigprocmask", "rt_sigqueueinfo", "rt_sigreturn", "rt_sigsuspend", "rt_sigtimedwait", "rt_tgsigqueueinfo",
                "sched_getaffinity", "sched_getattr", "sched_getparam", "sched_get_priority_max", "sched_get_priority_min",
                "sched_getscheduler", "sched_rr_get_interval", "sched_setaffinity", "sched_setattr", "sched_setparam",
                "sched_setscheduler", "sched_yield", "seccomp", "select", "semctl", "semget", "semop", "semtimedop",
                "send", "sendfile", "sendfile64", "sendmmsg", "sendmsg", "sendto", "setfsgid", "setfsuid", "setgid",
                "setgroups", "setitimer", "setpgid", "setpriority", "setregid", "setresgid", "setresuid", "setreuid",
                "setrlimit", "set_robust_list", "setsid", "setsockopt", "set_thread_area", "set_tid_address", "setuid",
                "setxattr", "shmat", "shmctl", "shmdt", "shmget", "shutdown", "sigaltstack", "signalfd", "signalfd4",
                "sigreturn", "socket", "socketcall", "socketpair", "splice", "stat", "statfs", "statx", "symlink",
                "symlinkat", "sync", "sync_file_range", "syncfs", "sysinfo", "syslog", "tee", "tgkill", "time",
                "timer_create", "timer_delete", "timerfd_create", "timerfd_gettime", "timerfd_settime", "timer_getoverrun",
                "timer_gettime", "timer_settime", "times", "tkill", "truncate", "umask", "uname", "unlink", "unlinkat",
                "utime", "utimensat", "utimes", "vfork", "vmsplice", "wait4", "waitid", "waitpid", "write", "writev"
            ],
            "action": "SCMP_ACT_ALLOW"
        }
    ]
}
EOF
    
    sudo cp /tmp/seccomp-profile.json /etc/docker/seccomp-profile.json
    
    echo -e "${GREEN}✅ Seccomp profile created${NC}"
}

setup_docker_security_scanning() {
    echo -e "${YELLOW}🔧 Setting up Docker security scanning...${NC}"
    
    # Install Docker Bench Security
    if ! command -v docker-bench-security &> /dev/null; then
        echo "Installing Docker Bench Security..."
        sudo curl -L https://github.com/docker/docker-bench-security/archive/master.tar.gz | tar -xz
        sudo mv docker-bench-security-master /opt/docker-bench-security
        sudo chmod +x /opt/docker-bench-security/docker-bench-security.sh
    fi
    
    # Install Trivy for container scanning
    if ! command -v trivy &> /dev/null; then
        echo "Installing Trivy..."
        curl -sfL https://raw.githubusercontent.com/aquasecurity/trivy/main/contrib/install.sh | sudo sh -s -- -b /usr/local/bin
    fi
    
    echo -e "${GREEN}✅ Security scanning tools installed${NC}"
}

create_docker_security_scripts() {
    echo -e "${YELLOW}🔧 Creating Docker security scripts...${NC}"
    
    # Create security scanning script
    cat > /tmp/scan-containers.sh << 'EOF'
#!/bin/bash

echo "🔍 Running comprehensive Docker security scan..."

# Scan running containers
echo "📊 Scanning running containers..."
docker ps --format "table {{.Names}}\t{{.Image}}\t{{.Status}}" | tail -n +2 | while read name image status; do
    echo "Scanning container: $name"
    trivy image --severity HIGH,CRITICAL $image
done

# Run Docker Bench Security
echo "🔒 Running Docker Bench Security..."
if [ -f /opt/docker-bench-security/docker-bench-security.sh ]; then
    cd /opt/docker-bench-security
    sudo ./docker-bench-security.sh
fi

# Check for container misconfigurations
echo "⚙️  Checking container configurations..."
docker ps --format "{{.Names}}" | while read container; do
    echo "Checking $container:"
    
    # Check if running as root
    user=$(docker exec $container whoami 2>/dev/null || echo "unknown")
    if [ "$user" = "root" ]; then
        echo "  ⚠️  WARNING: Container $container running as root"
    fi
    
    # Check for privileged mode
    privileged=$(docker inspect $container | jq -r '.[0].HostConfig.Privileged')
    if [ "$privileged" = "true" ]; then
        echo "  ❌ CRITICAL: Container $container running in privileged mode"
    fi
    
    # Check for host network
    network=$(docker inspect $container | jq -r '.[0].HostConfig.NetworkMode')
    if [ "$network" = "host" ]; then
        echo "  ⚠️  WARNING: Container $container using host networking"
    fi
done

echo "✅ Security scan completed"
EOF
    
    chmod +x /tmp/scan-containers.sh
    sudo mv /tmp/scan-containers.sh /usr/local/bin/scan-containers
    
    # Create container hardening script
    cat > /tmp/harden-container.sh << 'EOF'
#!/bin/bash

CONTAINER_NAME=$1
if [ -z "$CONTAINER_NAME" ]; then
    echo "Usage: $0 <container_name>"
    exit 1
fi

echo "🔒 Hardening container: $CONTAINER_NAME"

# Update the container to run with security options
docker update --restart=unless-stopped $CONTAINER_NAME
docker update --pids-limit=100 $CONTAINER_NAME
docker update --memory=1g $CONTAINER_NAME
docker update --cpus="1.0" $CONTAINER_NAME

echo "✅ Container $CONTAINER_NAME hardened"
EOF
    
    chmod +x /tmp/harden-container.sh
    sudo mv /tmp/harden-container.sh /usr/local/bin/harden-container
    
    echo -e "${GREEN}✅ Security scripts created${NC}"
}

setup_docker_logging() {
    echo -e "${YELLOW}🔧 Setting up secure Docker logging...${NC}"
    
    # Create log rotation configuration
    sudo mkdir -p /etc/logrotate.d
    
    cat > /tmp/docker-logs << 'EOF'
/var/lib/docker/containers/*/*.log {
    rotate 7
    daily
    compress
    size=1M
    missingok
    delaycompress
    copytruncate
}
EOF
    
    sudo mv /tmp/docker-logs /etc/logrotate.d/docker-logs
    
    echo -e "${GREEN}✅ Docker logging configured${NC}"
}

setup_docker_network_security() {
    echo -e "${YELLOW}🔧 Setting up Docker network security...${NC}"
    
    # Create custom networks for isolation
    docker network create --driver bridge --subnet=172.20.0.0/16 online-eval-backend || true
    docker network create --driver bridge --subnet=172.21.0.0/16 online-eval-frontend || true
    docker network create --driver bridge --subnet=172.22.0.0/16 online-eval-database || true
    
    # Enable iptables for Docker
    sudo sysctl net.ipv4.ip_forward=1
    
    echo -e "${GREEN}✅ Docker network security configured${NC}"
}

create_security_monitoring() {
    echo -e "${YELLOW}🔧 Setting up Docker security monitoring...${NC}"
    
    # Create monitoring script
    cat > /tmp/monitor-docker-security.sh << 'EOF'
#!/bin/bash

LOG_FILE="/var/log/docker-security-monitor.log"

while true; do
    TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')
    
    # Check for new containers
    NEW_CONTAINERS=$(docker ps -q --filter "status=running" | wc -l)
    echo "[$TIMESTAMP] Running containers: $NEW_CONTAINERS" >> $LOG_FILE
    
    # Check for privileged containers
    PRIVILEGED=$(docker ps --format "{{.Names}}" | xargs -I {} docker inspect {} | jq -r '.[] | select(.HostConfig.Privileged == true) | .Name' | wc -l)
    if [ $PRIVILEGED -gt 0 ]; then
        echo "[$TIMESTAMP] WARNING: $PRIVILEGED privileged containers detected" >> $LOG_FILE
    fi
    
    # Check for containers running as root
    ROOT_CONTAINERS=0
    docker ps --format "{{.Names}}" | while read container; do
        USER=$(docker exec $container whoami 2>/dev/null || echo "unknown")
        if [ "$USER" = "root" ]; then
            ROOT_CONTAINERS=$((ROOT_CONTAINERS + 1))
        fi
    done
    
    if [ $ROOT_CONTAINERS -gt 0 ]; then
        echo "[$TIMESTAMP] WARNING: $ROOT_CONTAINERS containers running as root" >> $LOG_FILE
    fi
    
    # Check disk usage
    DISK_USAGE=$(df /var/lib/docker | tail -1 | awk '{print $5}' | sed 's/%//')
    if [ $DISK_USAGE -gt 80 ]; then
        echo "[$TIMESTAMP] WARNING: Docker disk usage at $DISK_USAGE%" >> $LOG_FILE
    fi
    
    sleep 300  # Check every 5 minutes
done
EOF
    
    chmod +x /tmp/monitor-docker-security.sh
    sudo mv /tmp/monitor-docker-security.sh /usr/local/bin/monitor-docker-security
    
    # Create systemd service for monitoring
    cat > /tmp/docker-security-monitor.service << 'EOF'
[Unit]
Description=Docker Security Monitor
After=docker.service
Requires=docker.service

[Service]
Type=simple
ExecStart=/usr/local/bin/monitor-docker-security
Restart=always
RestartSec=10
User=root

[Install]
WantedBy=multi-user.target
EOF
    
    sudo mv /tmp/docker-security-monitor.service /etc/systemd/system/
    sudo systemctl daemon-reload
    sudo systemctl enable docker-security-monitor.service
    
    echo -e "${GREEN}✅ Docker security monitoring configured${NC}"
}

create_production_docker_compose() {
    echo -e "${YELLOW}🔧 Creating production Docker Compose configuration...${NC}"
    
    cat > docker-compose.production.yml << 'EOF'
version: '3.8'

services:
  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    image: online-eval/backend:latest
    container_name: online-eval-backend
    restart: unless-stopped
    networks:
      - backend-network
      - database-network
    environment:
      - NODE_ENV=production
      - MONGODB_URL=${MONGODB_URL}
      - REDIS_URL=${REDIS_URL}
      - JWT_SECRET_KEY=${JWT_SECRET_KEY}
    volumes:
      - ./backend/logs:/app/logs:rw
      - backend-uploads:/app/uploads:rw
    ports:
      - "127.0.0.1:8080:8080"
    user: "1000:1000"
    read_only: true
    tmpfs:
      - /tmp:rw,noexec,nosuid,size=100m
    security_opt:
      - no-new-privileges:true
      - seccomp:unconfined
    cap_drop:
      - ALL
    cap_add:
      - CHOWN
      - SETGID
      - SETUID
    ulimits:
      nproc: 65535
      nofile:
        soft: 65535
        hard: 65535
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8080/api/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 2G
        reservations:
          cpus: '1.0'
          memory: 1G

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    image: online-eval/frontend:latest
    container_name: online-eval-frontend
    restart: unless-stopped
    networks:
      - frontend-network
    environment:
      - NODE_ENV=production
      - REACT_APP_BACKEND_URL=${REACT_APP_BACKEND_URL}
    ports:
      - "127.0.0.1:3000:3000"
    user: "1000:1000"
    read_only: true
    tmpfs:
      - /tmp:rw,noexec,nosuid,size=100m
    security_opt:
      - no-new-privileges:true
    cap_drop:
      - ALL
    ulimits:
      nproc: 65535
      nofile:
        soft: 65535
        hard: 65535
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:3000"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
    deploy:
      resources:
        limits:
          cpus: '1.0'
          memory: 1G
        reservations:
          cpus: '0.5'
          memory: 512M

  mongodb:
    image: mongo:7.0
    container_name: online-eval-mongodb
    restart: unless-stopped
    networks:
      - database-network
    environment:
      - MONGO_INITDB_ROOT_USERNAME=${MONGO_ROOT_USERNAME}
      - MONGO_INITDB_ROOT_PASSWORD=${MONGO_ROOT_PASSWORD}
    volumes:
      - mongodb-data:/data/db:rw
      - ./mongodb/mongod.conf:/etc/mongod.conf:ro
      - ./mongodb/init:/docker-entrypoint-initdb.d:ro
    command: ["mongod", "--config", "/etc/mongod.conf"]
    user: "999:999"
    security_opt:
      - no-new-privileges:true
    cap_drop:
      - ALL
    cap_add:
      - CHOWN
      - SETGID
      - SETUID
    ulimits:
      nproc: 65535
      nofile:
        soft: 65535
        hard: 65535
    healthcheck:
      test: ["CMD", "mongosh", "--eval", "db.adminCommand('ping')"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 60s
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 2G
        reservations:
          cpus: '1.0'
          memory: 1G

  redis:
    image: redis:7.2-alpine
    container_name: online-eval-redis
    restart: unless-stopped
    networks:
      - database-network
    command: redis-server --appendonly yes --requirepass ${REDIS_PASSWORD}
    volumes:
      - redis-data:/data:rw
    user: "999:999"
    security_opt:
      - no-new-privileges:true
    cap_drop:
      - ALL
    ulimits:
      nproc: 65535
      nofile:
        soft: 65535
        hard: 65535
    healthcheck:
      test: ["CMD", "redis-cli", "-a", "${REDIS_PASSWORD}", "ping"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 30s
    deploy:
      resources:
        limits:
          cpus: '1.0'
          memory: 1G
        reservations:
          cpus: '0.5'
          memory: 512M

  nginx:
    image: nginx:1.25-alpine
    container_name: online-eval-nginx
    restart: unless-stopped
    networks:
      - frontend-network
      - backend-network
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro
      - ./nginx/ssl:/etc/nginx/ssl:ro
      - nginx-logs:/var/log/nginx:rw
    user: "101:101"
    security_opt:
      - no-new-privileges:true
    cap_drop:
      - ALL
    cap_add:
      - CHOWN
      - SETGID
      - SETUID
    ulimits:
      nproc: 65535
      nofile:
        soft: 65535
        hard: 65535
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 30s
    deploy:
      resources:
        limits:
          cpus: '1.0'
          memory: 512M
        reservations:
          cpus: '0.5'
          memory: 256M

networks:
  frontend-network:
    driver: bridge
    ipam:
      config:
        - subnet: 172.21.0.0/16
  backend-network:
    driver: bridge
    ipam:
      config:
        - subnet: 172.20.0.0/16
  database-network:
    driver: bridge
    internal: true
    ipam:
      config:
        - subnet: 172.22.0.0/16

volumes:
  mongodb-data:
    driver: local
  redis-data:
    driver: local
  backend-uploads:
    driver: local
  nginx-logs:
    driver: local
EOF
    
    echo -e "${GREEN}✅ Production Docker Compose configuration created${NC}"
}

create_nginx_security_config() {
    echo -e "${YELLOW}🔧 Creating secure Nginx configuration...${NC}"
    
    mkdir -p nginx
    
    cat > nginx/nginx.conf << 'EOF'
user nginx;
worker_processes auto;
pid /var/run/nginx.pid;

events {
    worker_connections 1024;
    use epoll;
    multi_accept on;
}

http {
    include /etc/nginx/mime.types;
    default_type application/octet-stream;

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;
    add_header Content-Security-Policy "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:; font-src 'self'; connect-src 'self'" always;
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;

    # Hide Nginx version
    server_tokens off;

    # Logging
    log_format main '$remote_addr - $remote_user [$time_local] "$request" '
                    '$status $body_bytes_sent "$http_referer" '
                    '"$http_user_agent" "$http_x_forwarded_for"';

    access_log /var/log/nginx/access.log main;
    error_log /var/log/nginx/error.log warn;

    # Performance
    sendfile on;
    tcp_nopush on;
    tcp_nodelay on;
    keepalive_timeout 65;
    types_hash_max_size 2048;

    # Security
    client_max_body_size 50M;
    client_body_timeout 10;
    client_header_timeout 10;
    keepalive_requests 10;
    send_timeout 10;

    # Rate limiting
    limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
    limit_req_zone $binary_remote_addr zone=login:10m rate=1r/s;

    # Upstream servers
    upstream backend {
        server backend:8080;
        keepalive 32;
    }

    upstream frontend {
        server frontend:3000;
        keepalive 32;
    }

    # HTTP to HTTPS redirect
    server {
        listen 80;
        server_name _;
        return 301 https://$host$request_uri;
    }

    # Main HTTPS server
    server {
        listen 443 ssl http2;
        server_name _;

        # SSL configuration
        ssl_certificate /etc/nginx/ssl/cert.pem;
        ssl_certificate_key /etc/nginx/ssl/key.pem;
        ssl_protocols TLSv1.2 TLSv1.3;
        ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES256-GCM-SHA384;
        ssl_prefer_server_ciphers off;
        ssl_session_cache shared:SSL:10m;
        ssl_session_timeout 10m;

        # Health check endpoint
        location /health {
            access_log off;
            return 200 "healthy\n";
            add_header Content-Type text/plain;
        }

        # API routes
        location /api/ {
            limit_req zone=api burst=20 nodelay;
            proxy_pass http://backend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            proxy_connect_timeout 5s;
            proxy_send_timeout 10s;
            proxy_read_timeout 10s;
        }

        # Login endpoint with stricter rate limiting
        location /api/auth/login {
            limit_req zone=login burst=5 nodelay;
            proxy_pass http://backend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }

        # Frontend
        location / {
            proxy_pass http://frontend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }

        # Deny access to sensitive files
        location ~ /\. {
            deny all;
            access_log off;
            log_not_found off;
        }

        location ~ \.(env|config|ini|log|sh|sql|tar|gz)$ {
            deny all;
            access_log off;
            log_not_found off;
        }
    }
}
EOF
    
    echo -e "${GREEN}✅ Secure Nginx configuration created${NC}"
}

create_mongodb_security_config() {
    echo -e "${YELLOW}🔧 Creating secure MongoDB configuration...${NC}"
    
    mkdir -p mongodb
    
    cat > mongodb/mongod.conf << 'EOF'
# MongoDB configuration for production security

# Network settings
net:
  port: 27017
  bindIp: 0.0.0.0
  maxIncomingConnections: 100
  wireObjectCheck: true

# Storage settings
storage:
  dbPath: /data/db
  journal:
    enabled: true
  directoryPerDB: true
  wiredTiger:
    engineConfig:
      cacheSizeGB: 1
      directoryForIndexes: true
    collectionConfig:
      blockCompressor: snappy
    indexConfig:
      prefixCompression: true

# Security settings
security:
  authorization: enabled
  javascriptEnabled: false

# Operation profiling
operationProfiling:
  slowOpThresholdMs: 100
  mode: slowOp

# Logging
systemLog:
  destination: file
  logAppend: true
  path: /var/log/mongodb/mongod.log
  logRotate: rename
  component:
    accessControl:
      verbosity: 1
    command:
      verbosity: 1

# Process management
processManagement:
  timeZoneInfo: /usr/share/zoneinfo

# Replication (for production clusters)
# replication:
#   replSetName: "rs0"

# Sharding (for production clusters)
# sharding:
#   clusterRole: shardsvr
EOF
    
    # Create MongoDB initialization script
    cat > mongodb/init/01-init-users.js << 'EOF'
// Initialize MongoDB users for Online Evaluation System

db = db.getSiblingDB('admin');

// Create application user
db.createUser({
  user: process.env.MONGO_APP_USERNAME || 'onlineeval',
  pwd: process.env.MONGO_APP_PASSWORD || 'secure_password_here',
  roles: [
    {
      role: 'readWrite',
      db: 'online_evaluation'
    }
  ]
});

// Create read-only user for monitoring
db.createUser({
  user: 'monitoring',
  pwd: process.env.MONGO_MONITORING_PASSWORD || 'monitoring_password_here',
  roles: [
    {
      role: 'read',
      db: 'online_evaluation'
    },
    {
      role: 'clusterMonitor',
      db: 'admin'
    }
  ]
});

// Switch to application database
db = db.getSiblingDB('online_evaluation');

// Create indexes for performance and security
db.users.createIndex({ "email": 1 }, { unique: true });
db.users.createIndex({ "username": 1 }, { unique: true });
db.users.createIndex({ "createdAt": 1 });

db.sessions.createIndex({ "token": 1 }, { unique: true });
db.sessions.createIndex({ "expiresAt": 1 }, { expireAfterSeconds: 0 });

db.security_events.createIndex({ "timestamp": -1 });
db.security_events.createIndex({ "event_type": 1 });
db.security_events.createIndex({ "ip_address": 1 });
db.security_events.createIndex({ "user_id": 1 });
EOF
    
    echo -e "${GREEN}✅ Secure MongoDB configuration created${NC}"
}

main() {
    echo -e "${GREEN}🚀 Starting Docker Security Hardening Process${NC}"
    
    # Check if running as root
    if [[ $EUID -ne 0 ]]; then
        echo -e "${RED}❌ This script must be run as root${NC}"
        exit 1
    fi
    
    # Create backup of existing configurations
    echo -e "${YELLOW}📦 Creating backup of existing configurations...${NC}"
    mkdir -p /tmp/docker-security-backup
    cp -r /etc/docker /tmp/docker-security-backup/ 2>/dev/null || true
    
    # Run hardening steps
    harden_docker_daemon
    create_seccomp_profile
    setup_docker_security_scanning
    create_docker_security_scripts
    setup_docker_logging
    setup_docker_network_security
    create_security_monitoring
    create_production_docker_compose
    create_nginx_security_config
    create_mongodb_security_config
    
    # Restart Docker daemon
    echo -e "${YELLOW}🔄 Restarting Docker daemon...${NC}"
    sudo systemctl restart docker
    
    # Start security monitoring
    echo -e "${YELLOW}🔄 Starting security monitoring...${NC}"
    sudo systemctl start docker-security-monitor.service
    
    echo -e "${GREEN}✅ Docker Security Hardening Completed Successfully!${NC}"
    echo -e "${GREEN}📋 Summary of changes:${NC}"
    echo -e "  ✅ Docker daemon hardened with security best practices"
    echo -e "  ✅ Custom seccomp profile created"
    echo -e "  ✅ Security scanning tools installed (Trivy, Docker Bench)"
    echo -e "  ✅ Security monitoring service enabled"
    echo -e "  ✅ Production Docker Compose configuration created"
    echo -e "  ✅ Secure Nginx and MongoDB configurations created"
    echo -e "  ✅ Network isolation configured"
    echo -e "  ✅ Log rotation and monitoring setup"
    
    echo -e "${YELLOW}📝 Next steps:${NC}"
    echo -e "  1. Review and customize environment variables in .env files"
    echo -e "  2. Generate SSL certificates for Nginx"
    echo -e "  3. Run security scan: /usr/local/bin/scan-containers"
    echo -e "  4. Deploy with: docker-compose -f docker-compose.production.yml up -d"
    echo -e "  5. Monitor security logs: tail -f /var/log/docker-security-monitor.log"
}

# Run main function
main "$@"
