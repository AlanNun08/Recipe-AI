#!/bin/bash

# secure-deploy.sh - Secure deployment script using Google Secret Manager
# This script deploys your app while keeping sensitive data secure

set -e

echo "🔐 Secure Google Cloud deployment for AI Recipe App..."
echo "====================================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

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

# Check prerequisites
if ! command -v gcloud &> /dev/null; then
    print_error "Google Cloud SDK not found. Please install it first."
    exit 1
fi

PROJECT_ID=$(gcloud config get-value project)
if [ -z "$PROJECT_ID" ]; then
    print_error "No Google Cloud project set. Please run: gcloud config set project YOUR_PROJECT_ID"
    exit 1
fi

print_info "Using Google Cloud project: $PROJECT_ID"

# Function to get secret value
get_secret() {
    local secret_name=$1
    gcloud secrets versions access latest --secret="$secret_name" --project="$PROJECT_ID" --quiet
}

# Function to check if secret exists
secret_exists() {
    local secret_name=$1
    gcloud secrets describe "$secret_name" --project="$PROJECT_ID" >/dev/null 2>&1
}

# Check if secrets exist
print_info "Checking for required secrets..."
REQUIRED_SECRETS=(
    "mongodb-connection-string"
    "openai-api-key"
    "walmart-consumer-id"
    "walmart-private-key"
    "mailjet-api-key"
    "mailjet-secret-key"
    "sender-email"
    "stripe-api-key"
    "jwt-secret-key"
)

MISSING_SECRETS=()
for secret in "${REQUIRED_SECRETS[@]}"; do
    if ! secret_exists "$secret"; then
        MISSING_SECRETS+=("$secret")
    fi
done

if [ ${#MISSING_SECRETS[@]} -gt 0 ]; then
    print_error "Missing required secrets:"
    for secret in "${MISSING_SECRETS[@]}"; do
        echo "  - $secret"
    done
    print_info "Please run ./setup-secrets.sh first to create the secrets"
    exit 1
fi

print_status "All required secrets found"

# Build frontend
print_info "Building React frontend..."
cd frontend
npm install
npm run build
cd ..

print_status "Frontend build completed"

# Create temporary app.yaml with secrets
print_info "Creating secure app.yaml with secrets from Secret Manager..."

cat > app.yaml << EOF
runtime: python39

env_variables:
  # Database Configuration
  MONGO_URL: "$(get_secret mongodb-connection-string)"
  DB_NAME: "buildyoursmartcart_production"
  
  # OpenAI API Configuration
  OPENAI_API_KEY: "$(get_secret openai-api-key)"
  
  # Walmart API Configuration
  WALMART_CONSUMER_ID: "$(get_secret walmart-consumer-id)"
  WALMART_KEY_VERSION: "1"
  WALMART_PRIVATE_KEY: "$(get_secret walmart-private-key)"
  
  # Mailjet Email Service Configuration
  MAILJET_API_KEY: "$(get_secret mailjet-api-key)"
  MAILJET_SECRET_KEY: "$(get_secret mailjet-secret-key)"
  SENDER_EMAIL: "$(get_secret sender-email)"
  
  # Stripe Configuration
  STRIPE_API_KEY: "$(get_secret stripe-api-key)"
  
  # JWT Secret Key
  SECRET_KEY: "$(get_secret jwt-secret-key)"
  
  # Application settings
  ENVIRONMENT: "production"
  DEBUG: "False"

handlers:
  - url: /.*
    script: auto

automatic_scaling:
  min_instances: 0
  max_instances: 3
  target_cpu_utilization: 0.6
  target_throughput_utilization: 0.6

resources:
  cpu: 1
  memory_gb: 0.5
  disk_size_gb: 10
EOF

print_status "Secure app.yaml created"

# Deploy to App Engine
print_info "Deploying to Google App Engine..."
gcloud app deploy --quiet

# Clean up temporary file
rm -f app.yaml
print_status "Temporary app.yaml cleaned up"

print_info "Getting app URL..."
APP_URL=$(gcloud app browse --no-launch-browser)

print_status "Deployment completed successfully!"
print_info "Your app is now live at: $APP_URL"

# Show post-deployment commands
echo ""
print_info "Useful post-deployment commands:"
echo "  View logs: gcloud app logs tail -s default"
echo "  View app: gcloud app browse"
echo "  Check status: gcloud app describe"

# Security reminder
echo ""
print_warning "Security reminder:"
print_info "1. Secrets are now stored securely in Google Secret Manager"
print_info "2. No sensitive data is in your code repository"
print_info "3. Monitor your app logs for any security issues"
print_info "4. Regularly rotate your API keys"

print_status "Secure deployment process completed! 🚀"