# 🚀 PRODUCTION DEPLOYMENT CONFIGURATION
## buildyoursmartcart.com

### 🔧 **GOOGLE CLOUD RUN ENVIRONMENT VARIABLES**

Set these environment variables in your Google Cloud Run service:

```bash
# Production API Keys (REQUIRED)
STRIPE_API_KEY=sk_live_your_production_stripe_key  # NOT test key
OPENAI_API_KEY=sk-your-production-openai-key
WALMART_CONSUMER_ID=your_walmart_consumer_id
WALMART_KEY_VERSION=1
WALMART_PRIVATE_KEY=your_walmart_private_key

# Database Configuration
MONGO_URL=mongodb+srv://username:password@your-cluster.mongodb.net/buildyoursmartcart_production
DB_NAME=buildyoursmartcart_production

# Email Service (Production)
MAILJET_API_KEY=your_production_mailjet_api_key
MAILJET_SECRET_KEY=your_production_mailjet_secret_key
SENDER_EMAIL=noreply@buildyoursmartcart.com

# Security
SECRET_KEY=your_long_random_secret_key_for_jwt
NODE_ENV=production
```

### 🌐 **DOMAIN CONFIGURATION**

Your application is configured for:
- **Primary Domain**: `https://buildyoursmartcart.com`
- **WWW Variant**: `https://www.buildyoursmartcart.com`
- **CORS Origins**: Restricted to your domains only
- **Trusted Hosts**: Secure host header validation

### 📋 **DEPLOYMENT CHECKLIST FOR buildyoursmartcart.com**

#### **1. DNS Configuration**
- [ ] Point `buildyoursmartcart.com` to your Google Cloud Run service URL
- [ ] Configure `www.buildyoursmartcart.com` to redirect to main domain
- [ ] Set up SSL certificate (automatic with Google Cloud Run)

#### **2. Google Cloud Run Service Update**
```bash
gcloud run deploy buildyoursmartcart \
  --source . \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars="STRIPE_API_KEY=sk_live_...,OPENAI_API_KEY=sk-...,MONGO_URL=mongodb+srv://..." \
  --memory 2Gi \
  --cpu 2 \
  --timeout 3600 \
  --domain buildyoursmartcart.com
```

#### **3. Frontend Configuration**
Update `/app/frontend/.env.production`:
```env
REACT_APP_BACKEND_URL=https://buildyoursmartcart.com/api
NODE_ENV=production
```

#### **4. Security Verification**
- [ ] HTTPS enforced on buildyoursmartcart.com
- [ ] CORS restricted to your domains only
- [ ] Production Stripe keys configured
- [ ] MongoDB production database secured
- [ ] Remove development/localhost entries

### 🔒 **PRODUCTION SECURITY STATUS**

**CORS Configuration**:
```python
allow_origins=[
    "https://buildyoursmartcart.com",      # ✅ Production domain
    "https://www.buildyoursmartcart.com",  # ✅ WWW variant
    # localhost entries removed for production ✅
]
```

**Trusted Hosts**:
```python
allowed_hosts=[
    "buildyoursmartcart.com",      # ✅ Primary domain
    "www.buildyoursmartcart.com",  # ✅ WWW variant
    # Development hosts removed ✅
]
```

### 💳 **STRIPE PRODUCTION CONFIGURATION**

**Switch to Live Mode**:
1. **Stripe Dashboard**: Switch to "View Live Data"
2. **Get Live API Keys**: 
   - Publishable Key: `pk_live_...`
   - Secret Key: `sk_live_...` (use this in environment variables)
3. **Configure Webhook Endpoints**:
   - URL: `https://buildyoursmartcart.com/api/stripe-webhook`
   - Events: `checkout.session.completed`, `invoice.payment_succeeded`, `customer.subscription.updated`

### 📊 **MONITORING & ANALYTICS**

**Google Cloud Run Monitoring**:
- Enable Cloud Logging
- Set up error alerting
- Monitor CPU/Memory usage
- Track request latency

**Stripe Dashboard**:
- Monitor live payments
- Set up payment failure alerts
- Track subscription metrics
- Review customer disputes

### 🎯 **FINAL PRODUCTION VERIFICATION**

Before going live with `buildyoursmartcart.com`:

1. **Test Payment Flow**: Complete end-to-end payment with real Stripe live keys
2. **Verify Domain Access**: Ensure app loads correctly at buildyoursmartcart.com
3. **Check HTTPS**: Verify SSL certificate is active
4. **Test Email Delivery**: Confirm verification emails work in production
5. **Monitor Error Logs**: Check Google Cloud Run logs for any issues

### 🚀 **DEPLOYMENT COMMAND FOR buildyoursmartcart.com**

```bash
# Deploy with your domain configuration
gcloud run deploy buildyoursmartcart \
  --source . \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --memory 2Gi \
  --cpu 2 \
  --timeout 3600 \
  --set-env-vars="STRIPE_API_KEY=$STRIPE_LIVE_KEY,OPENAI_API_KEY=$OPENAI_KEY,MONGO_URL=$MONGO_PRODUCTION_URL"

# Map custom domain
gcloud run domain-mappings create \
  --service buildyoursmartcart \
  --domain buildyoursmartcart.com \
  --region us-central1
```

Your application is now **PRODUCTION-READY** for `buildyoursmartcart.com`! 🎉