# 🚀 Production Deployment Guide

## Quick Deploy to Google Cloud Run

### 1. Set Environment Variables
```bash
gcloud run services update buildyoursmartcart \
  --project=sunlit-vortex-466800-q8 \
  --region=us-central1 \
  --set-env-vars="NODE_ENV=production" \
  --set-env-vars="MONGO_URL=YOUR_MONGODB_ATLAS_URL" \
  --set-env-vars="OPENAI_API_KEY=YOUR_OPENAI_KEY" \
  --set-env-vars="STRIPE_SECRET_KEY=YOUR_STRIPE_KEY" \
  --set-env-vars="STRIPE_PUBLISHER_API_KEY=YOUR_STRIPE_PUBLISHABLE_KEY" \
  --set-env-vars="SECRET_KEY=YOUR_32_CHAR_SECRET"
```

### 2. Deploy Application
```bash
gcloud run deploy buildyoursmartcart \
  --source . \
  --project=sunlit-vortex-466800-q8 \
  --region=us-central1 \
  --allow-unauthenticated \
  --memory=2Gi \
  --cpu=2 \
  --timeout=300s \
  --port=8080
```

## Alternative: Google App Engine

### 1. Configure Environment Variables
Edit `config/app.yaml` with your actual API keys.

### 2. Deploy
```bash
gcloud app deploy config/app.yaml --project=sunlit-vortex-466800-q8
```

## Health Check
After deployment, verify:
```bash
curl https://your-service-url/health
```

Expected response:
```json
{"status": "healthy", "service": "buildyoursmartcart"}
```