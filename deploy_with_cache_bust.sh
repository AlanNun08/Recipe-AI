#!/bin/bash

# 🚀 Google Cloud Run Deployment with Cache Busting
# buildyoursmartcart.com - Weekly Recipe & Walmart Integration Update

echo "🚀 DEPLOYING BUILDYOURSMARTCART.COM WITH CACHE BUSTING"
echo "=" * 60

# Set build variables
PROJECT_ID=$(gcloud config get-value project)
SERVICE_NAME="buildyoursmartcart"
REGION="us-central1"
BUILD_ID=$(date +%Y%m%d-%H%M%S)
VERSION="2.2.1-navigation-fix"

echo "📋 Deployment Configuration:"
echo "   Project ID: $PROJECT_ID"
echo "   Service: $SERVICE_NAME"
echo "   Region: $REGION"
echo "   Build ID: $BUILD_ID"
echo "   Version: $VERSION"
echo ""

# Confirm deployment
read -p "🤔 Deploy to production? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "❌ Deployment cancelled"
    exit 1
fi

echo "🏗️ Starting Cloud Run deployment with cache busting..."

# Submit build to Cloud Build (this uses cloudbuild.yaml)
echo "📦 Building and deploying container..."
gcloud builds submit . \
    --config=cloudbuild.yaml \
    --substitutions=_BUILD_ID=$BUILD_ID,_VERSION=$VERSION

# Check deployment status
if [ $? -eq 0 ]; then
    echo ""
    echo "🎉 DEPLOYMENT SUCCESSFUL!"
    echo "=" * 60
    echo "✅ Cache busting headers added to prevent browser caching"
    echo "✅ Version 2.2.1 with navigation bug fix deployed"
    echo "✅ Weekly recipe system with working 'View Recipe' navigation"
    echo ""
    echo "🌐 Service URL: https://buildyoursmartcart.com"
    echo "🔍 Health Check: https://buildyoursmartcart.com/health"
    echo "📋 API Docs: https://buildyoursmartcart.com/api/docs"
    echo ""
    echo "🧪 Test the integration:"
    echo "   1. Visit https://buildyoursmartcart.com"
    echo "   2. Login/Register → Dashboard"
    echo "   3. Weekly Meal Planner → View Recipe"
    echo "   4. Scroll to Shopping List → Walmart buttons should be visible!"
    echo ""
    echo "💡 Cache headers added:"
    echo "   Cache-Control: no-cache, no-store, must-revalidate"
    echo "   X-Build-Version: $VERSION"
    echo ""
    
    # Test the deployment
    echo "🧪 Testing deployment..."
    echo "Health check:"
    curl -s https://buildyoursmartcart.com/health | jq .
    
    echo ""
    echo "🚀 Deployment complete! Users will now get the latest version."
    
else
    echo ""
    echo "❌ DEPLOYMENT FAILED!"
    echo "Check Cloud Build logs for details:"
    echo "https://console.cloud.google.com/cloud-build/builds"
    exit 1
fi