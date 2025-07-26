#!/usr/bin/env python3
"""
Environment Variables Verification Script
Use this script to verify all required environment variables are set correctly.
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env file (for local development)
load_dotenv('backend/.env')

def verify_environment():
    """Verify all required environment variables are set"""
    
    required_vars = [
        'MONGO_URL',
        'DB_NAME',
        'OPENAI_API_KEY',
        'WALMART_CONSUMER_ID',
        'WALMART_KEY_VERSION',
        'WALMART_PRIVATE_KEY',
        'MAILJET_API_KEY',
        'MAILJET_SECRET_KEY',
        'SENDER_EMAIL',
        'STRIPE_API_KEY',
        'SECRET_KEY'
    ]
    
    print("🔍 Verifying Environment Variables...")
    print("=" * 50)
    
    missing_vars = []
    placeholder_vars = []
    
    for var in required_vars:
        value = os.environ.get(var)
        
        if not value:
            missing_vars.append(var)
            print(f"❌ {var}: NOT SET")
        elif value in ['your-openai-api-key-here', 'your-walmart-consumer-id-here', 
                       'your-walmart-private-key-here', 'your-mailjet-api-key-here',
                       'your-mailjet-secret-key-here', 'your-sender-email@example.com',
                       'your-stripe-api-key-here', 'your-secret-key-for-jwt']:
            placeholder_vars.append(var)
            print(f"⚠️  {var}: PLACEHOLDER VALUE")
        else:
            # Mask sensitive values for display
            if 'KEY' in var or 'SECRET' in var:
                masked_value = value[:10] + "..." if len(value) > 10 else "***"
                print(f"✅ {var}: {masked_value}")
            else:
                print(f"✅ {var}: {value}")
    
    print("=" * 50)
    
    if missing_vars:
        print(f"❌ Missing Variables ({len(missing_vars)}):")
        for var in missing_vars:
            print(f"   - {var}")
    
    if placeholder_vars:
        print(f"⚠️  Placeholder Variables ({len(placeholder_vars)}):")
        for var in placeholder_vars:
            print(f"   - {var}")
    
    if not missing_vars and not placeholder_vars:
        print("🎉 All environment variables are properly set!")
        return True
    else:
        print(f"\n📋 Action Required:")
        if missing_vars:
            print("   1. Set missing environment variables")
        if placeholder_vars:
            print("   2. Replace placeholder values with actual API keys")
        print("   3. For Google Cloud deployment, set these in Cloud Console")
        return False

def check_api_key_formats():
    """Check if API keys have the expected format"""
    print("\n🔑 Checking API Key Formats...")
    print("=" * 50)
    
    # OpenAI API Key format check
    openai_key = os.environ.get('OPENAI_API_KEY', '')
    if openai_key.startswith('sk-'):
        print("✅ OpenAI API Key: Correct format")
    else:
        print("⚠️  OpenAI API Key: Should start with 'sk-'")
    
    # Walmart Consumer ID format check (UUID format)
    walmart_id = os.environ.get('WALMART_CONSUMER_ID', '')
    if len(walmart_id) == 36 and walmart_id.count('-') == 4:
        print("✅ Walmart Consumer ID: Correct format")
    else:
        print("⚠️  Walmart Consumer ID: Should be UUID format")
    
    # Walmart Private Key format check
    walmart_key = os.environ.get('WALMART_PRIVATE_KEY', '')
    if walmart_key.startswith('-----BEGIN PRIVATE KEY-----'):
        print("✅ Walmart Private Key: Correct format")
    else:
        print("⚠️  Walmart Private Key: Should be PEM format")
    
    # Stripe API Key format check
    stripe_key = os.environ.get('STRIPE_API_KEY', '')
    if stripe_key.startswith('sk_test_') or stripe_key.startswith('sk_live_'):
        print("✅ Stripe API Key: Correct format")
    else:
        print("⚠️  Stripe API Key: Should start with 'sk_test_' or 'sk_live_'")

def main():
    """Main function"""
    print("AI Recipe + Grocery Delivery App")
    print("Environment Variables Verification Tool")
    print("=" * 50)
    
    # Verify environment variables
    env_ok = verify_environment()
    
    # Check API key formats
    check_api_key_formats()
    
    print("\n" + "=" * 50)
    if env_ok:
        print("🚀 Your environment is ready for deployment!")
    else:
        print("⚠️  Please fix the issues above before deploying.")
    
    print("\n📚 For deployment help, see: GOOGLE_CLOUD_DEPLOYMENT_GUIDE.md")

if __name__ == "__main__":
    main()