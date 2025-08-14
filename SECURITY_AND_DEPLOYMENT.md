# 🔒 Security & Deployment Guide

## 🚨 CRITICAL SECURITY NOTICE

**⚠️ NO HARDCODED API KEYS IN CODEBASE**

This application is designed with security-first principles:
- ✅ All API keys stored as environment variables only
- ✅ Placeholder values in `.env` files
- ✅ Production keys set in Google Cloud Run environment
- ✅ Validation prevents placeholder values in production

## 🔑 API Key Management

### Environment Variable Structure
All sensitive credentials follow this pattern:

**Local Development (.env files):**
```bash
API_KEY_NAME="your-api-key-placeholder-here"
```

**Production (Google Cloud Run Environment Variables):**
```bash
API_KEY_NAME=actual-production-api-key-value
```

### Required API Keys

#### **Payment Processing (Stripe)**
```bash
STRIPE_API_KEY=your-stripe-secret-key-from-dashboard     # Get from Stripe Dashboard → API Keys
STRIPE_PUBLISHABLE_KEY=your-stripe-publishable-key-from-dashboard   # Get from Stripe Dashboard → API Keys
```

> **Note**: Get your actual keys from https://dashboard.stripe.com → Developers → API Keys

#### **AI Services (OpenAI)**
```bash
OPENAI_API_KEY=sk-...               # OpenAI API key for recipe generation
```

#### **E-commerce Integration (Walmart)**
```bash
WALMART_CONSUMER_ID=...             # Walmart API consumer ID
WALMART_KEY_VERSION=1               # API version
WALMART_PRIVATE_KEY="-----BEGIN PRIVATE KEY-----
...                                 # Full private key for authentication
-----END PRIVATE KEY-----"
```

#### **Email Services (Mailjet)**
```bash
MAILJET_API_KEY=...                 # Mailjet API key
MAILJET_SECRET_KEY=...              # Mailjet secret key
SENDER_EMAIL=noreply@yourdomain.com # Sender email address
```

#### **Database (MongoDB)**
```bash
MONGO_URL=mongodb+srv://...         # MongoDB Atlas connection string
DB_NAME=production_database_name    # Database name
```

#### **Application Security**
```bash
SECRET_KEY=...                      # JWT token signing key (long random string)
```

## 🛡️ Security Validation

### Startup Validation
The application validates all API keys on startup:

1. **Format Validation**: Ensures keys match expected patterns
2. **Placeholder Detection**: Rejects development placeholder values
3. **Connection Testing**: Validates API connectivity where possible

### Example Validation (Stripe)
```python
# Automatic validation in stripe_native.py
if stripe.api_key in ["your-stripe-secret-key-here", "your-str************here"]:
    raise ValueError("Please set a valid Stripe API key in environment variables")

if not (stripe.api_key.startswith('sk_test_') or stripe.api_key.startswith('sk_live_')):
    raise ValueError("Invalid Stripe API key format")
```

## 🚀 Google Cloud Run Deployment

### Step 1: Prepare Environment Variables
Create a file `env-vars.yaml`:
```yaml
MONGO_URL: "mongodb+srv://username:password@cluster.mongodb.net/dbname"
DB_NAME: "buildyoursmartcart_production"
OPENAI_API_KEY: "sk-your-openai-key"
STRIPE_API_KEY: "sk_live_your-stripe-key"
STRIPE_PUBLISHABLE_KEY: "pk_live_your-stripe-key"
WALMART_CONSUMER_ID: "your-walmart-id"
WALMART_KEY_VERSION: "1"
WALMART_PRIVATE_KEY: |
  -----BEGIN PRIVATE KEY-----
  your-full-private-key-content-here
  -----END PRIVATE KEY-----
MAILJET_API_KEY: "your-mailjet-key"
MAILJET_SECRET_KEY: "your-mailjet-secret"
SENDER_EMAIL: "noreply@yourdomain.com"
SECRET_KEY: "your-jwt-secret-key"
```

### Step 2: Deploy with Environment Variables
```bash
# Deploy and set environment variables
gcloud run deploy recipe-ai \
  --source . \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --port 8080 \
  --env-vars-file env-vars.yaml
```

### Step 3: Verify Deployment
```bash
# Check service status
gcloud run services describe recipe-ai --region us-central1

# View logs for validation
gcloud logs read --service recipe-ai --region us-central1
```

## 🔐 Best Practices

### Development Environment
1. **Never commit `.env` files** with real values
2. **Use placeholder values** in version control
3. **Keep real keys** in secure password manager
4. **Rotate keys regularly** (quarterly recommended)

### Production Environment
1. **Set environment variables** in Google Cloud Run console
2. **Use separate keys** for development and production
3. **Monitor API usage** for unusual activity
4. **Set up alerts** for failed authentication attempts

### Code Security
1. **No hardcoded secrets** anywhere in codebase
2. **Validate all inputs** on server side
3. **Use HTTPS only** for all communications
4. **Implement rate limiting** on all endpoints

## 🚨 Security Incident Response

### If API Keys Are Compromised:

#### Immediate Actions:
1. **Revoke compromised keys** in respective service dashboards
2. **Generate new keys** with different values
3. **Update environment variables** in Google Cloud Run
4. **Redeploy service** to activate new keys
5. **Monitor usage** for unauthorized activity

#### Service-Specific Actions:

**Stripe Keys Compromised:**
1. Revoke keys in Stripe Dashboard → Developers → API Keys
2. Generate new Live keys
3. Update `STRIPE_API_KEY` and `STRIPE_PUBLISHABLE_KEY`
4. Test payment flow after deployment

**MongoDB Access Compromised:**
1. Change database password in MongoDB Atlas
2. Update `MONGO_URL` with new credentials
3. Consider rotating to new cluster if necessary

**OpenAI Key Compromised:**
1. Revoke key in OpenAI Dashboard → API Keys
2. Generate new key with appropriate usage limits
3. Update `OPENAI_API_KEY` environment variable

## 📊 Monitoring & Alerting

### Set Up Monitoring:
```bash
# Enable Cloud Run logging
gcloud logging sinks create recipe-ai-errors \
  bigquery.googleapis.com/projects/YOUR_PROJECT/datasets/app_logs \
  --log-filter='resource.type="cloud_run_revision" AND severity>=ERROR'
```

### Key Metrics to Monitor:
- API key validation failures
- Unusual API usage patterns  
- Failed authentication attempts
- Database connection errors
- Payment processing failures

## ✅ Security Checklist

### Pre-Deployment:
- [ ] All API keys are environment variables
- [ ] No hardcoded secrets in codebase
- [ ] Placeholder values in `.env` files
- [ ] Real keys configured in Google Cloud Run
- [ ] Startup validation tests pass

### Post-Deployment:
- [ ] Service starts successfully
- [ ] All integrations working (Stripe, OpenAI, MongoDB)
- [ ] API key validation logs show success
- [ ] No error logs related to authentication
- [ ] Payment flow tested end-to-end

### Ongoing Maintenance:
- [ ] Regular key rotation schedule
- [ ] Monitor API usage dashboards
- [ ] Review access logs monthly
- [ ] Update dependencies for security patches
- [ ] Backup and disaster recovery tested

## 📞 Emergency Contacts

### Service Providers:
- **Stripe Support**: https://support.stripe.com
- **OpenAI Support**: https://help.openai.com
- **MongoDB Support**: https://cloud.mongodb.com/support
- **Google Cloud Support**: https://cloud.google.com/support

### Internal Escalation:
1. **Development Team**: For code-related security issues
2. **Infrastructure Team**: For deployment and access issues  
3. **Security Team**: For incident response and key rotation

---

**Remember**: Security is everyone's responsibility. When in doubt, err on the side of caution! 🛡️