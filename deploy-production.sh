#!/bin/bash

# Production Deployment Script for buildyoursmartcart.com
# Optimized for Google Cloud Run

set -e  # Exit on any error

echo "🚀 Starting production deployment for buildyoursmartcart.com..."

# Configuration
PROJECT_ID=${GOOGLE_CLOUD_PROJECT:-"your-project-id"}
SERVICE_NAME="buildyoursmartcart"
REGION="us-central1"
IMAGE_NAME="gcr.io/$PROJECT_ID/$SERVICE_NAME"

# Check if gcloud is installed and authenticated
if ! command -v gcloud &> /dev/null; then
    echo "❌ gcloud CLI not found. Please install Google Cloud SDK."
    exit 1
fi

# Verify gcloud authentication
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | head -1 > /dev/null; then
    echo "❌ Not authenticated with gcloud. Run 'gcloud auth login'"
    exit 1
fi

# Set project
echo "📋 Setting project to $PROJECT_ID..."
gcloud config set project "$PROJECT_ID"

# Enable required APIs
echo "🔧 Enabling required Google Cloud APIs..."
gcloud services enable \
    cloudbuild.googleapis.com \
    run.googleapis.com \
    containerregistry.googleapis.com \
    --quiet

echo "🏗️ Building and deploying with Cloud Build..."
gcloud builds submit \
    --tag "$IMAGE_NAME:latest" \
    --timeout=1800s \
    .

echo "⚙️  Before deployment, make sure environment variables are set!"
echo "   Run: ./setup-production-env.sh (if not done already)"
echo ""

# Deploy to Cloud Run with production settings
echo "🚀 Deploying to Cloud Run..."
gcloud run deploy "$SERVICE_NAME" \
    --image "$IMAGE_NAME:latest" \
    --platform managed \
    --region "$REGION" \
    --allow-unauthenticated \
    --memory 2Gi \
    --cpu 2 \
    --concurrency 1000 \
    --timeout 3600 \
    --max-instances 100 \
    --min-instances 0 \
    --port 8080 \
    --update-env-vars "NODE_ENV=production,PYTHONUNBUFFERED=1" \
    --quiet

# Get the service URL
SERVICE_URL=$(gcloud run services describe "$SERVICE_NAME" --region "$REGION" --format "value(status.url)")

echo "✅ Deployment completed successfully!"
echo "🌐 Service URL: $SERVICE_URL"
echo "🏥 Health Check: $SERVICE_URL/health"
echo "📚 API Docs: $SERVICE_URL/api/docs"

# Test the deployment
echo "🧪 Testing deployment..."
HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$SERVICE_URL/health" || echo "000")

if [ "$HTTP_STATUS" = "200" ]; then
    echo "✅ Health check passed! Service is running correctly."
else
    echo "⚠️ Health check returned status: $HTTP_STATUS"
    echo "Check the logs: gcloud run logs tail $SERVICE_NAME --region $REGION"
fi

echo ""
echo "🔧 Next steps:"
echo "1. Set up custom domain mapping for buildyoursmartcart.com"
echo "2. Configure production environment variables:"
echo "   gcloud run services update $SERVICE_NAME --region $REGION \\"
echo "     --set-env-vars 'STRIPE_API_KEY=sk_live_...,OPENAI_API_KEY=sk-...'"
echo "3. Set up monitoring and alerting"
echo "4. Configure DNS for your domain"

echo "🎉 buildyoursmartcart.com is ready for production!"