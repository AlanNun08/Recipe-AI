#!/bin/bash

# Production Environment Setup for buildyoursmartcart.com
# This script sets up all required environment variables in Google Cloud Run

set -e

echo "🔧 Setting up production environment variables for buildyoursmartcart.com..."

# Configuration
PROJECT_ID=${GOOGLE_CLOUD_PROJECT:-"your-project-id"}
SERVICE_NAME="buildyoursmartcart"
REGION="us-central1"

# Check if gcloud is authenticated
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | head -1 > /dev/null; then
    echo "❌ Not authenticated with gcloud. Run 'gcloud auth login'"
    exit 1
fi

echo "📋 Setting project to $PROJECT_ID..."
gcloud config set project "$PROJECT_ID"

echo "⚠️  IMPORTANT: You need to provide your actual API keys!"
echo ""
echo "Please provide the following production API keys:"
echo ""

read -p "🔑 Enter your PRODUCTION Stripe API key (sk_live_...): " STRIPE_API_KEY
read -p "🤖 Enter your OpenAI API key (sk-...): " OPENAI_API_KEY
read -p "📧 Enter your Mailjet API key: " MAILJET_API_KEY
read -p "📧 Enter your Mailjet Secret key: " MAILJET_SECRET_KEY
read -p "🛒 Enter your Walmart Consumer ID: " WALMART_CONSUMER_ID
read -p "🛒 Enter your Walmart Private Key: " WALMART_PRIVATE_KEY
read -p "🗄️  Enter your MongoDB production URL: " MONGO_URL

echo ""
echo "🚀 Setting environment variables in Cloud Run..."

gcloud run services update "$SERVICE_NAME" \
    --region="$REGION" \
    --set-env-vars="NODE_ENV=production,PYTHONUNBUFFERED=1,REACT_APP_BACKEND_URL=https://buildyoursmartcart.com,STRIPE_API_KEY=$STRIPE_API_KEY,OPENAI_API_KEY=$OPENAI_API_KEY,MAILJET_API_KEY=$MAILJET_API_KEY,MAILJET_SECRET_KEY=$MAILJET_SECRET_KEY,WALMART_CONSUMER_ID=$WALMART_CONSUMER_ID,WALMART_PRIVATE_KEY=$WALMART_PRIVATE_KEY,MONGO_URL=$MONGO_URL,DB_NAME=buildyoursmartcart_production,SENDER_EMAIL=noreply@buildyoursmartcart.com" \
    --quiet

echo "✅ Environment variables configured successfully!"
echo ""
echo "🧪 Testing the service..."
echo "⏳ Waiting for deployment to update..."
sleep 30

# Test the service
SERVICE_URL="https://buildyoursmartcart.com"
echo "🔗 Testing: $SERVICE_URL/health"

HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$SERVICE_URL/health" || echo "000")

if [ "$HTTP_STATUS" = "200" ]; then
    echo "✅ Service is healthy and ready!"
    echo "🌐 Your app is live at: $SERVICE_URL"
    echo "🏥 Health check: $SERVICE_URL/health"
    echo "📚 API docs: $SERVICE_URL/api/docs"
else
    echo "⚠️ Service returned status: $HTTP_STATUS"
    echo "📋 Check logs: gcloud run logs tail $SERVICE_NAME --region $REGION"
fi

echo ""
echo "🎉 Production environment setup complete!"
echo "📝 Next: Deploy your updated code with './deploy-production.sh'"