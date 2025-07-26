#!/bin/bash

# deploy.sh - Google Cloud Deployment Script for AI Recipe + Grocery Delivery App

echo "🚀 Starting Google Cloud deployment preparation..."
echo "================================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

# Check if we're in the correct directory
if [ ! -f "app.yaml" ]; then
    print_error "app.yaml not found. Please run this script from the root directory."
    exit 1
fi

# Step 1: Check prerequisites
print_info "Step 1: Checking prerequisites..."

if ! command -v gcloud &> /dev/null; then
    print_error "Google Cloud SDK not found. Please install it first."
    exit 1
fi

if ! command -v npm &> /dev/null; then
    print_error "npm not found. Please install Node.js and npm first."
    exit 1
fi

print_status "Prerequisites check passed"

# Step 2: Build React frontend
print_info "Step 2: Building React frontend..."

if [ ! -d "frontend" ]; then
    print_error "frontend directory not found"
    exit 1
fi

cd frontend

if [ ! -f "package.json" ]; then
    print_error "package.json not found in frontend directory"
    exit 1
fi

print_info "Installing frontend dependencies..."
npm install

print_info "Building production version..."
npm run build

if [ ! -d "build" ]; then
    print_error "Build failed - build directory not created"
    exit 1
fi

print_status "Frontend build completed successfully"

# Go back to root directory
cd ..

# Step 3: Verify deployment files
print_info "Step 3: Verifying deployment files..."

required_files=("app.yaml" "main.py" "requirements.txt" ".gcloudignore")

for file in "${required_files[@]}"; do
    if [ ! -f "$file" ]; then
        print_error "Required file $file not found"
        exit 1
    fi
done

print_status "All deployment files verified"

# Step 4: Check Google Cloud configuration
print_info "Step 4: Checking Google Cloud configuration..."

if ! gcloud config get-value project &> /dev/null; then
    print_warning "No Google Cloud project set. Please run: gcloud config set project YOUR_PROJECT_ID"
    exit 1
fi

PROJECT_ID=$(gcloud config get-value project)
print_info "Current Google Cloud project: $PROJECT_ID"

# Step 5: Deployment options
print_info "Step 5: Deployment options"
echo ""
echo "Choose deployment option:"
echo "1) Deploy to production (default service)"
echo "2) Deploy as a new version (no traffic)"
echo "3) Deploy with custom version name"
echo "4) Just validate configuration"
echo ""

read -p "Enter your choice (1-4): " choice

case $choice in
    1)
        print_info "Deploying to production..."
        gcloud app deploy
        ;;
    2)
        print_info "Deploying as new version without traffic..."
        gcloud app deploy --no-promote
        ;;
    3)
        read -p "Enter version name: " version_name
        print_info "Deploying with version name: $version_name"
        gcloud app deploy --version=$version_name --no-promote
        ;;
    4)
        print_info "Validating configuration..."
        gcloud app deploy --dry-run
        ;;
    *)
        print_error "Invalid choice. Exiting."
        exit 1
        ;;
esac

# Step 6: Post-deployment information
if [ $? -eq 0 ]; then
    print_status "Deployment completed successfully!"
    echo ""
    print_info "Useful commands:"
    echo "  View logs: gcloud app logs tail -s default"
    echo "  Open app: gcloud app browse"
    echo "  Check status: gcloud app describe"
    echo ""
    print_info "Your AI Recipe + Grocery Delivery App is now live!"
else
    print_error "Deployment failed. Check the output above for errors."
    exit 1
fi