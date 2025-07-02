#!/bin/bash

# Fast Build Script - Target: <30s
echo "🚀 Starting fast build process..."

# Enable BuildKit
export DOCKER_BUILDKIT=1
export COMPOSE_DOCKER_CLI_BUILD=1

# Start timing
start_time=$(date +%s)

# Clean up and prepare
echo "📦 Preparing build environment..."
cd frontend

# Install dependencies if needed (with npm for speed)
if [ ! -d "node_modules" ] || [ "package.json" -nt "node_modules" ]; then
    echo "📦 Installing dependencies..."
    npm ci --silent --no-audit --no-fund
fi

# Run optimized build
echo "🏗️  Building frontend (optimized)..."
export NODE_OPTIONS="--max-old-space-size=4096"
npm run build:fast

cd ..

# Build Docker images in parallel
echo "🐳 Building Docker images..."
docker build --target production -f Dockerfile.frontend -t online-evaluation-frontend:latest --cache-from online-evaluation-frontend:latest . &
docker build --target production -f Dockerfile.backend -t online-evaluation-backend:latest --cache-from online-evaluation-backend:latest . &

wait

# Calculate time
end_time=$(date +%s)
elapsed=$((end_time - start_time))

echo "✅ Build completed in ${elapsed}s"

if [ $elapsed -lt 30 ]; then
    echo "🎯 SUCCESS: Build time under 30s target!"
else
    echo "⚠️  WARNING: Build time exceeds 30s target"
fi