#!/bin/bash

# setup-secrets.sh - Script to securely set up Google Secret Manager secrets
# This script helps you store sensitive API keys securely in Google Secret Manager

set -e

echo "🔐 Setting up Google Secret Manager secrets for AI Recipe App..."
echo "================================================================="

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

# Check if gcloud is installed and authenticated
if ! command -v gcloud &> /dev/null; then
    print_error "Google Cloud SDK not found. Please install it first."
    exit 1
fi

# Get current project
PROJECT_ID=$(gcloud config get-value project)
if [ -z "$PROJECT_ID" ]; then
    print_error "No Google Cloud project set. Please run: gcloud config set project YOUR_PROJECT_ID"
    exit 1
fi

print_info "Using Google Cloud project: $PROJECT_ID"

# Enable Secret Manager API
print_info "Enabling Secret Manager API..."
gcloud services enable secretmanager.googleapis.com

# Function to create a secret
create_secret() {
    local secret_name=$1
    local secret_description=$2
    
    print_info "Creating secret: $secret_name"
    
    # Check if secret already exists
    if gcloud secrets describe $secret_name --project=$PROJECT_ID >/dev/null 2>&1; then
        print_warning "Secret $secret_name already exists. Skipping creation."
        return 0
    fi
    
    # Create the secret
    gcloud secrets create $secret_name \
        --replication-policy="automatic" \
        --project=$PROJECT_ID \
        --labels="app=ai-recipe-app" \
        --description="$secret_description"
    
    print_status "Created secret: $secret_name"
}

# Function to add secret version
add_secret_version() {
    local secret_name=$1
    local secret_value=$2
    
    if [ -z "$secret_value" ]; then
        print_error "No value provided for secret: $secret_name"
        return 1
    fi
    
    echo "$secret_value" | gcloud secrets versions add $secret_name \
        --data-file=- \
        --project=$PROJECT_ID
    
    print_status "Added version to secret: $secret_name"
}

# Create secrets for all API keys
print_info "Creating secrets for API keys..."

# MongoDB
create_secret "mongodb-connection-string" "MongoDB Atlas connection string for AI Recipe App"

# OpenAI
create_secret "openai-api-key" "OpenAI API key for recipe generation"

# Walmart
create_secret "walmart-consumer-id" "Walmart API consumer ID"
create_secret "walmart-private-key" "Walmart API private key for authentication"

# Mailjet
create_secret "mailjet-api-key" "Mailjet API key for email service"
create_secret "mailjet-secret-key" "Mailjet secret key for email service"
create_secret "sender-email" "Email address for sending notifications"

# Stripe
create_secret "stripe-api-key" "Stripe API key for payment processing"

# JWT
create_secret "jwt-secret-key" "JWT secret key for token signing"

print_info "All secrets created successfully!"
print_warning "Now you need to add the actual secret values. You can do this by:"
print_info "1. Using the Google Cloud Console: https://console.cloud.google.com/security/secret-manager"
print_info "2. Using the command line with: gcloud secrets versions add SECRET_NAME --data-file=-"
print_info "3. Running the interactive setup script: ./add-secret-values.sh"

# Generate a strong JWT secret
print_info "Generating a strong JWT secret key..."
JWT_SECRET=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")
echo "$JWT_SECRET" | gcloud secrets versions add jwt-secret-key --data-file=- --project=$PROJECT_ID
print_status "JWT secret key generated and stored securely"

print_info "Setup complete! Remember to:"
print_info "1. Add your actual API keys to the secrets"
print_info "2. Update your service account permissions"
print_info "3. Use the secure deployment script"

echo ""
print_status "Secret Manager setup completed successfully!"