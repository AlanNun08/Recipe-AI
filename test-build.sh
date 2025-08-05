#!/bin/bash

# Test build script to verify Docker build works locally
# This helps debug build issues before pushing to Google Cloud

set -e

echo "🔧 Testing Docker build locally..."

# Clean up any existing containers
docker system prune -f

echo "📦 Building Docker image..."
docker build -t test-buildyoursmartcart .

echo "✅ Build completed successfully!"

echo "🧪 Testing container startup..."
# Test that the container starts without errors
docker run --rm -d --name test-container -p 8080:8080 test-buildyoursmartcart &
CONTAINER_ID=$!

# Wait a few seconds for startup
sleep 10

# Check if container is still running
if docker ps | grep test-container; then
    echo "✅ Container started successfully!"
    docker stop test-container
else
    echo "❌ Container failed to start"
    docker logs test-container
    exit 1
fi

echo "🎉 Local build test passed!"