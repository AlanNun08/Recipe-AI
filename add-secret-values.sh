#!/bin/bash

# add-secret-values.sh - Interactive script to add secret values to Google Secret Manager
# This script helps you securely add your API keys to Google Secret Manager

set -e

echo "🔑 Adding secret values to Google Secret Manager..."
echo "================================================="

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

# Function to add secret value
add_secret_value() {
    local secret_name=$1
    local secret_description=$2
    local secret_example=$3
    
    echo ""
    print_info "Setting up: $secret_name"
    echo "Description: $secret_description"
    if [ -n "$secret_example" ]; then
        echo "Example: $secret_example"
    fi
    
    # Check if secret has existing versions
    if gcloud secrets versions list $secret_name --project=$PROJECT_ID --limit=1 --format="value(name)" 2>/dev/null | grep -q .; then
        print_warning "This secret already has a value. Do you want to add a new version? (y/N)"
        read -r response
        if [[ ! $response =~ ^[Yy]$ ]]; then
            print_info "Skipping $secret_name"
            return 0
        fi
    fi
    
    echo -n "Enter value for $secret_name: "
    read -s secret_value
    echo ""
    
    if [ -z "$secret_value" ]; then
        print_warning "No value entered. Skipping $secret_name"
        return 0
    fi
    
    # Add the secret value
    echo "$secret_value" | gcloud secrets versions add $secret_name \
        --data-file=- \
        --project=$PROJECT_ID
    
    print_status "Added value for $secret_name"
}

# MongoDB Atlas setup
print_info "📗 Setting up MongoDB Atlas connection..."
add_secret_value "mongodb-connection-string" \
    "MongoDB Atlas connection string for your database" \
    "mongodb+srv://username:password@cluster.mongodb.net/database?retryWrites=true&w=majority"

# OpenAI setup
print_info "🤖 Setting up OpenAI API..."
add_secret_value "openai-api-key" \
    "OpenAI API key for recipe generation" \
    "sk-proj-..."

# Walmart setup
print_info "🛒 Setting up Walmart API..."
add_secret_value "walmart-consumer-id" \
    "Walmart API consumer ID (UUID format)" \
    "12345678-1234-1234-1234-123456789abc"

add_secret_value "walmart-private-key" \
    "Walmart API private key (complete PEM format including headers)" \
    "-----BEGIN PRIVATE KEY-----\nMIIEvgIBADANBgkqhkiG9w0BAQEFAASCBKgwggSkAgEAAoIBAQC...\n-----END PRIVATE KEY-----"

# Mailjet setup
print_info "📧 Setting up Mailjet email service..."
add_secret_value "mailjet-api-key" \
    "Mailjet API key for email service" \
    "a1b2c3d4e5f6g7h8i9j0"

add_secret_value "mailjet-secret-key" \
    "Mailjet secret key for email service" \
    "z9y8x7w6v5u4t3s2r1q0"

add_secret_value "sender-email" \
    "Email address for sending notifications" \
    "noreply@yourdomain.com"

# Stripe setup
print_info "💳 Setting up Stripe payment processing..."
add_secret_value "stripe-api-key" \
    "Stripe API key for payment processing" \
    "sk_test_... or sk_live_..."

# JWT secret is auto-generated, so skip interactive input
print_info "🔐 JWT secret key was auto-generated during secret creation"

# Final instructions
echo ""
print_status "Secret values setup completed!"
print_info "Next steps:"
print_info "1. Verify all secrets are correctly set in Google Cloud Console"
print_info "2. Run ./secure-deploy.sh to deploy your app securely"
print_info "3. Test your app functionality after deployment"

print_warning "Security reminders:"
print_info "1. Never commit API keys to version control"
print_info "2. Regularly rotate your API keys"
print_info "3. Monitor your app logs for any security issues"
print_info "4. Use strong, unique passwords for all services"

echo ""
print_status "You can now deploy securely! 🔐"