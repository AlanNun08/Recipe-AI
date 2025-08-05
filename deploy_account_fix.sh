#!/bin/bash

# IMMEDIATE DEPLOYMENT SCRIPT FOR ACCOUNT FIX
# Deploys and executes the account fix in Google Cloud environment

set -e

echo "🚨 IMMEDIATE ACCOUNT FIX DEPLOYMENT"
echo "📧 Target: alannunezsilva0310@gmail.com"
echo "🎯 Action: Complete account deletion"
echo "🌐 Environment: Google Cloud Production"
echo "=" * 70

# Configuration
PROJECT_ID=${GOOGLE_CLOUD_PROJECT:-"your-project-id"}
REGION="us-central1"
JOB_NAME="account-fix-$(date +%s)"

echo "📋 Project: $PROJECT_ID"
echo "🌍 Region: $REGION"
echo "🔧 Job: $JOB_NAME"

# Check authentication
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | head -1 > /dev/null; then
    echo "❌ Not authenticated with gcloud. Run 'gcloud auth login'"
    exit 1
fi

echo "🔑 Setting project..."
gcloud config set project "$PROJECT_ID"

echo "📦 Creating Cloud Run Job for account fix..."

# Create a temporary Dockerfile for the fix
cat > Dockerfile.fix << EOF
FROM python:3.9-slim

WORKDIR /app

# Install dependencies
RUN pip install motor httpx asyncio

# Copy the fix script
COPY production_account_fix_immediate.py /app/

# Set the entrypoint
CMD ["python3", "production_account_fix_immediate.py"]
EOF

echo "🏗️ Building container image..."
gcloud builds submit --tag gcr.io/$PROJECT_ID/account-fix .

echo "🚀 Creating and executing Cloud Run Job..."
gcloud run jobs create $JOB_NAME \
    --image gcr.io/$PROJECT_ID/account-fix \
    --region $REGION \
    --set-env-vars "MONGO_URL=$MONGO_URL,DB_NAME=buildyoursmartcart_production" \
    --max-retries 1 \
    --parallelism 1 \
    --task-count 1

echo "▶️ Executing the account fix job..."
gcloud run jobs execute $JOB_NAME --region $REGION --wait

echo "📋 Getting job logs..."
gcloud logging read "resource.type=cloud_run_job AND resource.labels.job_name=$JOB_NAME" --limit 50 --format "value(textPayload)"

echo "🧹 Cleaning up job..."
gcloud run jobs delete $JOB_NAME --region $REGION --quiet

echo "🧹 Cleaning up image..."
gcloud container images delete gcr.io/$PROJECT_ID/account-fix --quiet

echo "🧹 Cleaning up Dockerfile..."
rm -f Dockerfile.fix

echo ""
echo "🎉 ACCOUNT FIX DEPLOYMENT COMPLETED!"
echo "✅ Check the logs above for fix results"
echo "✅ alannunezsilva0310@gmail.com should now be available for registration"