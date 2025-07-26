#!/bin/bash
# build_for_deployment.sh - Build the frontend for deployment

echo "🚀 Building AI Recipe + Grocery Delivery App for deployment..."
echo "=" * 60

# Check if we're in the correct directory
if [ ! -f "main.py" ]; then
    echo "❌ Error: Please run this script from the root directory (where main.py is located)"
    exit 1
fi

# Check if frontend directory exists
if [ ! -d "frontend" ]; then
    echo "❌ Error: Frontend directory not found"
    exit 1
fi

# Navigate to frontend directory
cd frontend

echo "📦 Installing frontend dependencies..."
if command -v yarn &> /dev/null; then
    yarn install
else
    npm install
fi

echo "🔧 Building frontend for production..."
if command -v yarn &> /dev/null; then
    yarn build
else
    npm run build
fi

# Check if build was successful
if [ ! -d "build" ]; then
    echo "❌ Error: Frontend build failed"
    exit 1
fi

echo "✅ Frontend build completed successfully!"

# Go back to root directory
cd ..

echo "📋 Verifying environment variables..."
python3 verify_env_vars.py

echo ""
echo "🎉 Build complete! Your application is ready for deployment."
echo ""
echo "📚 Next steps:"
echo "1. Set up environment variables in Google Cloud Console"
echo "2. Deploy using Cloud Build or gcloud CLI"
echo "3. See GOOGLE_CLOUD_DEPLOYMENT_GUIDE.md for detailed instructions"
echo ""
echo "🔗 Deploy to Cloud Run with: gcloud run deploy --source . --allow-unauthenticated"
echo "💡 Remember to set environment variables in Cloud Run Console before deployment"