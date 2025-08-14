# 🔑 How to Obtain API Keys for Deployment

## 📋 Overview

This document explains how to obtain the actual API keys needed for production deployment. **No real keys are stored in this repository** - you must obtain them from the respective service providers.

## 🔒 Stripe Payment Keys

### Step 1: Create Stripe Account
1. Go to https://stripe.com
2. Sign up for a business account
3. Complete business verification

### Step 2: Get API Keys
1. Login to Stripe Dashboard: https://dashboard.stripe.com
2. Navigate to **Developers** → **API Keys**
3. Copy your keys:
   - **Secret key** (starts with `sk_live_`) → Use for `STRIPE_API_KEY`
   - **Publishable key** (starts with `pk_live_`) → Use for `STRIPE_PUBLISHABLE_KEY`

### Step 3: Configure Webhooks (Optional)
1. Go to **Developers** → **Webhooks**
2. Add endpoint: `https://your-app-url.com/api/webhook/stripe`
3. Select events: `checkout.session.completed`, `invoice.payment_succeeded`

## 🤖 OpenAI API Key

### Step 1: Create OpenAI Account
1. Go to https://openai.com
2. Sign up and verify your account
3. Add billing information

### Step 2: Get API Key
1. Login to OpenAI Platform: https://platform.openai.com
2. Navigate to **API Keys**
3. Create new key → Copy the key (starts with `sk-`) → Use for `OPENAI_API_KEY`

## 🛒 Walmart API Keys

### Step 1: Walmart Developer Account
1. Go to https://developer.walmart.com
2. Apply for API access (business verification required)
3. Wait for approval

### Step 2: Get Credentials
1. Login to Walmart Developer Portal
2. Navigate to **My Account** → **API Keys**
3. Copy:
   - **Consumer ID** → Use for `WALMART_CONSUMER_ID`
   - **Private Key** → Use for `WALMART_PRIVATE_KEY`
   - **Key Version** → Use for `WALMART_KEY_VERSION` (usually "1")

## 📧 Mailjet Email Keys

### Step 1: Create Mailjet Account
1. Go to https://www.mailjet.com
2. Sign up for account
3. Verify your email domain

### Step 2: Get API Keys
1. Login to Mailjet Dashboard
2. Go to **Account Settings** → **Master API Keys & Sub-account API Keys**
3. Copy:
   - **API Key** → Use for `MAILJET_API_KEY`
   - **Secret Key** → Use for `MAILJET_SECRET_KEY`

## 🗄️ MongoDB Connection

### Step 1: Create MongoDB Atlas Account
1. Go to https://cloud.mongodb.com
2. Sign up for free account
3. Create a new cluster

### Step 2: Get Connection String
1. In MongoDB Atlas dashboard, click **Connect**
2. Choose **Connect your application**
3. Copy the connection string → Use for `MONGO_URL`
4. Replace `<password>` with your database password
5. Replace `<dbname>` with your database name

## 🔐 JWT Secret Key

### Generate Random Secret
```bash
# Generate a secure random key (32+ characters)
openssl rand -base64 32
```
Use the output for `SECRET_KEY`

## ⚠️ Security Reminders

### Do NOT:
- ❌ Put real keys in Git repositories
- ❌ Share keys in emails or chat
- ❌ Use the same keys for development and production
- ❌ Store keys in unsecured files

### Do:
- ✅ Store keys in Google Cloud Run environment variables
- ✅ Use different keys for development and production
- ✅ Rotate keys regularly (quarterly recommended)
- ✅ Monitor API usage for unusual activity
- ✅ Keep a secure backup of your keys

## 🚀 Setting Keys in Google Cloud Run

Once you have all keys, set them in Google Cloud Run:

### Option 1: Using Console
1. Go to Google Cloud Console → Cloud Run
2. Select your service → Edit & Deploy New Revision
3. In **Variables** tab, add each environment variable

### Option 2: Using gcloud CLI
```bash
gcloud run services update recipe-ai \
  --set-env-vars STRIPE_API_KEY=your-actual-stripe-key \
  --set-env-vars OPENAI_API_KEY=your-actual-openai-key \
  --set-env-vars MONGO_URL=your-actual-mongo-url \
  --region us-central1
```

### Option 3: Using env-vars.yaml file
```yaml
# Create env-vars.yaml with your actual keys
STRIPE_API_KEY: "your-actual-stripe-secret-key"
STRIPE_PUBLISHABLE_KEY: "your-actual-stripe-publishable-key"
OPENAI_API_KEY: "your-actual-openai-key"
# ... etc

# Deploy with file
gcloud run deploy recipe-ai \
  --source . \
  --env-vars-file env-vars.yaml \
  --region us-central1
```

## 🎯 Key Validation

The application will validate your keys on startup:
- **Format validation**: Ensures keys match expected patterns
- **Connection testing**: Tests API connectivity where possible
- **Placeholder rejection**: Prevents deployment with placeholder values

If deployment fails, check that:
1. All required keys are set
2. Keys have the correct format
3. Keys are active and have proper permissions
4. Services have sufficient quotas/billing enabled

---

**Remember**: Keep your API keys secure and never commit them to version control! 🔒