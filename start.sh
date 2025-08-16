#!/bin/bash
# Google Cloud Run startup script

set -e

echo "🚀 Starting buildyoursmartcart.com for Google Cloud Run"
echo "📍 PORT: ${PORT:-8080}"
echo "🌍 NODE_ENV: ${NODE_ENV:-development}"

# Ensure we're in the right directory
cd /app

# Start the application
exec python main.py