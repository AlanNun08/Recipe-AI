# Google Cloud Run Deployment Guide

## Prerequisites

✅ **Required Setup:**
- Google Cloud account with billing enabled
- `gcloud` CLI installed and configured
- Docker installed (if building locally)
- All API keys ready (see list below)

## Step 1: Prepare Your API Keys

### Required API Keys and Configuration

| Service | Key/Config Required | Where to Get |
|---------|-------------------|--------------|
| **MongoDB** | Connection String | [MongoDB Atlas](https://cloud.mongodb.com/) |
| **OpenAI** | API Key | [OpenAI Platform](https://platform.openai.com/api-keys) |
| **Stripe** | API Key + Publishable Key | [Stripe Dashboard](https://dashboard.stripe.com/apikeys) |
| **Walmart** | Consumer ID + Private Key | [Walmart Developer](https://developer.walmart.com/) |
| **Mailjet** | API Key + Secret Key | [Mailjet Account](https://app.mailjet.com/account/api_keys) |

### Sample Environment Variables Format

```bash
# Database Configuration
MONGO_URL="mongodb+srv://username:password@cluster.mongodb.net/database"
DB_NAME="buildyoursmartcart_production"

# OpenAI Configuration  
OPENAI_API_KEY="sk-proj-your-openai-api-key-here"

# Stripe Configuration
STRIPE_API_KEY="sk_live_your-stripe-secret-key"
STRIPE_PUBLISHABLE_KEY="pk_live_your-stripe-publishable-key"

# Walmart Configuration
WALMART_CONSUMER_ID="your-walmart-consumer-id"
WALMART_KEY_VERSION="1"
WALMART_PRIVATE_KEY="-----BEGIN PRIVATE KEY-----
your-walmart-private-key-content
-----END PRIVATE KEY-----"

# Email Configuration
MAILJET_API_KEY="your-mailjet-api-key"
MAILJET_SECRET_KEY="your-mailjet-secret-key"
SENDER_EMAIL="noreply@buildyoursmartcart.com"

# Security
SECRET_KEY="your-strong-random-jwt-secret-key"

# Production Settings
NODE_ENV="production"
```

## Step 2: Project Setup for Google Cloud Run

### Current Project Structure (✅ Ready for Google Cloud Run)

```
/app/
├── src/backend/              # Backend application
│   ├── api/                  # API routes
│   ├── models/              # Data models
│   ├── services/            # Business logic
│   └── main.py             # FastAPI app
├── frontend/                # React frontend
├── main.py                 # Production server (Cloud Run entry point)
├── Dockerfile              # Container configuration
├── cloudbuild.yaml         # Cloud Build configuration
├── requirements.txt        # Python dependencies
└── .gcloud/service.yaml    # Cloud Run service config
```

### Key Google Cloud Run Optimizations Applied

✅ **Port Configuration**: Uses `PORT` environment variable (default 8080)  
✅ **CORS Configuration**: Production-ready CORS settings  
✅ **Health Checks**: `/health` endpoint for container health monitoring  
✅ **Resource Optimization**: Memory and CPU settings optimized  
✅ **Logging**: Cloud Logging integration  
✅ **Security**: Non-root user, minimal container image  

## Step 3: Deploy to Google Cloud Run

### Option A: Using Google Cloud Console (Recommended)

1. **Go to Google Cloud Console**
   - Navigate to [Cloud Run](https://console.cloud.google.com/run)
   - Click "Create Service"

2. **Container Configuration**
   - **Container Image URL**: `gcr.io/PROJECT_ID/buildyoursmartcart:latest`
   - **Service Name**: `buildyoursmartcart`
   - **Region**: `us-central1` (recommended)
   - **CPU Allocation**: CPU is only allocated during request processing
   - **Ingress**: Allow all traffic
   - **Authentication**: Allow unauthenticated invocations

3. **Container Settings**
   ```
   Port: 8080
   Memory: 2GiB
   CPU: 2
   Request timeout: 300 seconds
   Maximum requests per container: 80
   ```

4. **Environment Variables**
   - Go to "Variables & Secrets" tab
   - Add all environment variables from Step 1
   - **Important**: Use "Add Environment Variable" for each key-value pair

5. **Advanced Settings**
   ```
   Minimum instances: 0
   Maximum instances: 100
   Concurrency: 80
   CPU throttling: Enabled
   Execution environment: Second generation
   ```

### Option B: Using gcloud CLI

```bash
# 1. Build and deploy in one command
gcloud run deploy buildyoursmartcart \
  --source . \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --memory=2Gi \
  --cpu=2 \
  --concurrency=80 \
  --timeout=300 \
  --max-instances=100 \
  --port=8080 \
  --set-env-vars="NODE_ENV=production" \
  --project=YOUR_PROJECT_ID

# 2. Set environment variables (do this after deployment for security)
gcloud run services update buildyoursmartcart \
  --region=us-central1 \
  --set-env-vars="MONGO_URL=your-mongodb-url,OPENAI_API_KEY=your-openai-key,STRIPE_API_KEY=your-stripe-key" \
  --project=YOUR_PROJECT_ID
```

### Option C: Using Cloud Build (CI/CD Pipeline)

```bash
# 1. Enable Cloud Build API
gcloud services enable cloudbuild.googleapis.com

# 2. Submit build (uses cloudbuild.yaml)
gcloud builds submit --config cloudbuild.yaml .

# 3. The cloudbuild.yaml will automatically deploy to Cloud Run
```

## Step 4: Configure Domain and SSL

### Custom Domain Setup

1. **Map Custom Domain**
   ```bash
   gcloud run domain-mappings create \
     --service buildyoursmartcart \
     --domain buildyoursmartcart.com \
     --region us-central1
   ```

2. **Update DNS Records**
   - Add the CNAME record provided by Google Cloud
   - SSL certificate will be automatically provisioned

3. **Update Frontend Configuration**
   ```bash
   # Update your frontend deployment
   REACT_APP_BACKEND_URL=https://buildyoursmartcart.com
   ```

## Step 5: Verify Deployment

### Health Checks

1. **API Health**: `https://your-service-url/health`
   ```json
   {
     "status": "healthy",
     "service": "buildyoursmartcart-api",
     "version": "3.0.0",
     "database": "healthy",
     "external_apis": {
       "openai": true,
       "mailjet": true,
       "walmart": true,
       "stripe": true
     }
   }
   ```

2. **API Documentation**: `https://your-service-url/docs`

3. **Root Endpoint**: `https://your-service-url/`

### Test Key Functionality

```bash
# Test authentication endpoint
curl -X POST "https://your-service-url/api/auth/register" \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"testpass123"}'

# Test recipe generation
curl -X POST "https://your-service-url/api/recipes/generate" \
  -H "Content-Type: application/json" \
  -d '{"user_id":"test-id","cuisine_type":"italian","difficulty":"easy","servings":4}'
```

## Step 6: Production Configuration

### Environment Variables Security

✅ **Never commit real API keys to version control**  
✅ **Use Google Cloud Console for sensitive environment variables**  
✅ **Rotate API keys regularly**  
✅ **Monitor API usage for unusual activity**  

### Monitoring Setup

1. **Cloud Monitoring**
   - CPU and memory usage
   - Request latency
   - Error rates
   - Custom metrics

2. **Cloud Logging**
   - Application logs
   - Error logs
   - Audit logs

3. **Alerting**
   - High error rates
   - High latency
   - Resource usage

### Security Best Practices

```yaml
# Additional security headers (already configured in the app)
- X-Content-Type-Options: nosniff
- X-Frame-Options: DENY
- X-XSS-Protection: 1; mode=block
- Strict-Transport-Security: max-age=31536000; includeSubDomains
```

## Step 7: Troubleshooting

### Common Issues and Solutions

| Issue | Cause | Solution |
|-------|-------|----------|
| **Container fails to start** | Missing environment variables | Check all required env vars are set |
| **502 Bad Gateway** | App not listening on PORT | Verify app uses `PORT` env variable |
| **Database connection fails** | MongoDB Atlas IP restrictions | Allow Google Cloud IPs or use 0.0.0.0/0 |
| **CORS errors** | Frontend domain not allowed | Update CORS settings in main.py |
| **API key errors** | Invalid or expired keys | Verify all API keys are valid |

### Debug Commands

```bash
# View service logs
gcloud run services logs read buildyoursmartcart --region=us-central1

# Get service details
gcloud run services describe buildyoursmartcart --region=us-central1

# List environment variables
gcloud run services describe buildyoursmartcart --region=us-central1 --format="value(spec.template.spec.template.spec.containers[0].env[].name)"
```

### Health Check Debugging

```bash
# Test health endpoint
curl -v https://your-service-url/health

# Test with timeout
curl --max-time 10 https://your-service-url/health
```

## Step 8: Scaling and Performance

### Auto-scaling Configuration

```yaml
# Configured in service.yaml
annotations:
  autoscaling.knative.dev/maxScale: "100"
  autoscaling.knative.dev/minScale: "0"
  run.googleapis.com/cpu-throttling: "true"
```

### Performance Optimization

- **Cold starts**: Minimized with optimized container image
- **Memory usage**: 2GiB allocated for AI processing
- **CPU allocation**: 2 vCPUs for concurrent requests
- **Connection pooling**: MongoDB connection pooling enabled

## Step 9: CI/CD Pipeline (Optional)

### GitHub Actions Integration

```yaml
# .github/workflows/deploy.yml (example)
name: Deploy to Cloud Run
on:
  push:
    branches: [main]
jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: google-github-actions/setup-gcloud@v0
        with:
          service_account_key: ${{ secrets.GCP_SA_KEY }}
          project_id: ${{ secrets.GCP_PROJECT_ID }}
      - run: gcloud builds submit --config cloudbuild.yaml .
```

## Cost Optimization

### Pricing Considerations

- **Request-based pricing**: Pay only for actual requests
- **CPU allocation**: Only billed during request processing
- **Memory**: Optimized at 2GiB for AI workloads
- **Network**: Minimal egress costs

### Cost Monitoring

```bash
# Set up budget alerts
gcloud billing budgets create \
  --billing-account=BILLING_ACCOUNT_ID \
  --display-name="Cloud Run Budget" \
  --budget-amount=100USD
```

## Summary

✅ **Application is now Google Cloud Run ready** with:
- Optimized container configuration
- Production-ready security settings
- Health checks and monitoring
- Auto-scaling capabilities
- Proper environment variable handling

✅ **Key features supported**:
- AI recipe generation
- Walmart shopping integration
- Stripe payment processing
- Email notifications
- User authentication

🚀 **Ready for production deployment** with this configuration!

## Need Help?

If you encounter issues:
1. Check the [troubleshooting section](#step-7-troubleshooting)
2. Review Cloud Run logs in Google Cloud Console
3. Verify all environment variables are correctly set
4. Test individual API endpoints using the `/docs` interface

For additional support, contact the development team or refer to the [Google Cloud Run documentation](https://cloud.google.com/run/docs).