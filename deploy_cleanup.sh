#!/bin/bash
# Production Account Cleanup Deployment Script
# This script deploys and runs the account cleanup in Google Cloud environment

set -e

echo "🔧 PRODUCTION ACCOUNT CLEANUP DEPLOYMENT"
echo "📧 Target: alannunezsilva0310@gmail.com"
echo "🗄️ Database: buildyoursmartcart_production"
echo "=" * 60

# Check if we're in the right directory
if [ ! -f "production_account_cleanup.py" ]; then
    echo "❌ Error: production_account_cleanup.py not found"
    echo "Please run this script from the directory containing the cleanup script"
    exit 1
fi

# Check if gcloud is installed and authenticated
if ! command -v gcloud &> /dev/null; then
    echo "❌ Error: gcloud CLI not found"
    echo "Please install Google Cloud CLI: https://cloud.google.com/sdk/docs/install"
    exit 1
fi

# Get current project
PROJECT_ID=$(gcloud config get-value project 2>/dev/null)
if [ -z "$PROJECT_ID" ]; then
    echo "❌ Error: No Google Cloud project configured"
    echo "Please run: gcloud config set project YOUR_PROJECT_ID"
    exit 1
fi

echo "✅ Google Cloud Project: $PROJECT_ID"

# Option 1: Run via Cloud Run Job (Recommended)
echo ""
echo "🚀 DEPLOYMENT OPTIONS:"
echo "1. Deploy as Cloud Run Job (Recommended)"
echo "2. Run via Cloud Shell"
echo "3. Deploy to existing Cloud Run service"
echo ""

read -p "Select option (1-3): " OPTION

case $OPTION in
    1)
        echo "🚀 Deploying as Cloud Run Job..."
        
        # Create Dockerfile for the cleanup job
        cat > Dockerfile.cleanup << EOF
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
RUN pip install motor httpx python-dotenv bson

# Copy cleanup script
COPY production_account_cleanup.py .

# Run the cleanup
CMD ["python", "production_account_cleanup.py"]
EOF

        # Build and deploy Cloud Run Job
        echo "📦 Building container image..."
        gcloud builds submit --tag gcr.io/$PROJECT_ID/account-cleanup .

        echo "🚀 Creating Cloud Run Job..."
        gcloud run jobs create account-cleanup \
            --image gcr.io/$PROJECT_ID/account-cleanup \
            --region us-central1 \
            --set-env-vars="MONGO_URL=\$MONGO_URL,DB_NAME=buildyoursmartcart_production" \
            --max-retries 1 \
            --parallelism 1 \
            --task-count 1

        echo "▶️ Executing cleanup job..."
        gcloud run jobs execute account-cleanup --region us-central1

        echo "📋 Check job logs:"
        echo "gcloud run jobs executions logs account-cleanup --region us-central1"
        ;;
        
    2)
        echo "🌐 Running via Cloud Shell..."
        
        # Upload script to Cloud Shell
        echo "📤 Uploading cleanup script..."
        
        # Create a temporary deployment package
        tar -czf cleanup-package.tar.gz production_account_cleanup.py
        
        echo "📋 MANUAL STEPS FOR CLOUD SHELL:"
        echo "1. Upload cleanup-package.tar.gz to Cloud Shell"
        echo "2. Extract: tar -xzf cleanup-package.tar.gz"
        echo "3. Install dependencies: pip install motor httpx python-dotenv bson"
        echo "4. Set environment variables:"
        echo "   export MONGO_URL='your-production-mongodb-url'"
        echo "   export DB_NAME='buildyoursmartcart_production'"
        echo "5. Run: python production_account_cleanup.py"
        ;;
        
    3)
        echo "🔧 Deploying to existing Cloud Run service..."
        
        # This would modify the existing service temporarily
        echo "⚠️ WARNING: This will temporarily modify your production service"
        read -p "Continue? (y/N): " CONFIRM
        
        if [[ $CONFIRM =~ ^[Yy]$ ]]; then
            echo "📦 Creating cleanup deployment..."
            
            # Create a temporary service version with the cleanup script
            cat > main.py << EOF
import asyncio
import sys
from production_account_cleanup import ProductionAccountCleaner

async def main():
    cleaner = ProductionAccountCleaner()
    success = await cleaner.run_complete_cleanup()
    return success

if __name__ == "__main__":
    result = asyncio.run(main())
    sys.exit(0 if result else 1)
EOF

            echo "🚀 Deploying cleanup version..."
            gcloud run deploy buildyoursmartcart \
                --source . \
                --platform managed \
                --region us-central1 \
                --allow-unauthenticated \
                --set-env-vars="CLEANUP_MODE=true"
                
            echo "▶️ Cleanup deployed. Access the service to trigger cleanup."
            echo "⚠️ Remember to redeploy your normal application after cleanup!"
        else
            echo "❌ Deployment cancelled"
        fi
        ;;
        
    *)
        echo "❌ Invalid option selected"
        exit 1
        ;;
esac

echo ""
echo "📋 CLEANUP VERIFICATION STEPS:"
echo "1. Check cleanup logs for success confirmation"
echo "2. Test registration at: https://buildyoursmartcart.com"
echo "3. Try registering with: alannunezsilva0310@gmail.com"
echo "4. Verify no 'email already registered' error"
echo ""
echo "🎉 If successful, the account cleanup is complete!"