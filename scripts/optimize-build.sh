#!/bin/bash

# Build Optimization Script for Online Evaluation System
# Target: <30s build time

set -e

echo "🚀 Starting build optimization..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to measure time
timer() {
    start_time=$(date +%s)
    "$@"
    end_time=$(date +%s)
    elapsed=$((end_time - start_time))
    echo -e "${GREEN}⏱️  Operation completed in ${elapsed}s${NC}"
    return $elapsed
}

# Enable Docker BuildKit
export DOCKER_BUILDKIT=1
export COMPOSE_DOCKER_CLI_BUILD=1

echo -e "${BLUE}📦 Setting up build environment...${NC}"

# Clean up previous builds to ensure fresh cache
echo -e "${YELLOW}🧹 Cleaning up previous builds...${NC}"
docker system prune -f --filter "until=24h" > /dev/null 2>&1 || true

# Pull base images for cache
echo -e "${BLUE}📥 Pulling base images for cache...${NC}"
docker pull node:20-alpine &
docker pull python:3.11-slim &
docker pull nginx:alpine &
wait

echo -e "${BLUE}🔧 Installing frontend dependencies...${NC}"
cd frontend

# Check if node_modules exists and is up to date
if [ ! -d "node_modules" ] || [ "package.json" -nt "node_modules" ]; then
    echo -e "${YELLOW}📦 Installing/updating dependencies...${NC}"
    timer npm ci --silent --no-audit --no-fund
else
    echo -e "${GREEN}✅ Dependencies already up to date${NC}"
fi

# Build frontend with optimizations
echo -e "${BLUE}🏗️  Building optimized frontend...${NC}"
export NODE_OPTIONS="--max-old-space-size=4096"
export GENERATE_SOURCEMAP=false
export DISABLE_ESLINT_PLUGIN=true
export SKIP_PREFLIGHT_CHECK=true
export CI=true

timer npm run build:fast

cd ..

echo -e "${BLUE}🐳 Building Docker images with cache optimization...${NC}"

# Build images in parallel with cache
echo -e "${YELLOW}🔨 Building backend image...${NC}"
timer docker build \
    --target production \
    --file Dockerfile.backend \
    --tag online-evaluation-backend:latest \
    --cache-from online-evaluation-backend:latest \
    --build-arg BUILDKIT_INLINE_CACHE=1 \
    . &

BACKEND_PID=$!

echo -e "${YELLOW}🔨 Building frontend image...${NC}"
timer docker build \
    --target production \
    --file Dockerfile.frontend \
    --tag online-evaluation-frontend:latest \
    --cache-from online-evaluation-frontend:latest \
    --build-arg BUILDKIT_INLINE_CACHE=1 \
    --build-arg REACT_APP_BACKEND_URL="http://localhost:${BACKEND_PORT:-8002}" \
    --build-arg REACT_APP_WS_URL="ws://localhost:${BACKEND_PORT:-8002}" \
    . &

FRONTEND_PID=$!

# Wait for both builds to complete
wait $BACKEND_PID
BACKEND_TIME=$?
wait $FRONTEND_PID  
FRONTEND_TIME=$?

# Calculate total time
TOTAL_TIME=$((BACKEND_TIME + FRONTEND_TIME))

echo -e "${GREEN}✅ Build optimization completed!${NC}"
echo -e "${BLUE}📊 Build Performance Summary:${NC}"
echo -e "  Backend build: ${BACKEND_TIME}s"
echo -e "  Frontend build: ${FRONTEND_TIME}s"
echo -e "  Total time: ${TOTAL_TIME}s"

if [ $TOTAL_TIME -lt 30 ]; then
    echo -e "${GREEN}🎯 SUCCESS: Build time under 30s target!${NC}"
else
    echo -e "${YELLOW}⚠️  WARNING: Build time exceeds 30s target. Consider further optimizations.${NC}"
fi

# Analyze bundle size
echo -e "${BLUE}📈 Analyzing bundle size...${NC}"
if [ -d "frontend/build/static/js" ]; then
    echo "JavaScript bundle sizes:"
    ls -lh frontend/build/static/js/*.js | awk '{print "  " $9 ": " $5}'
fi

if [ -d "frontend/build/static/css" ]; then
    echo "CSS bundle sizes:"
    ls -lh frontend/build/static/css/*.css | awk '{print "  " $9 ": " $5}'
fi

echo -e "${GREEN}🚀 Build optimization complete!${NC}"