# Google Cloud Deployment Checklist - AI Recipe + Grocery Delivery App

## Pre-deployment Preparation

### ✅ 1. Prerequisites Installed
- [ ] Google Cloud SDK installed and authenticated
- [ ] Node.js and npm/yarn installed
- [ ] Python 3.9+ installed
- [ ] Git configured

### ✅ 2. Google Cloud Project Setup
- [ ] Create or select a Google Cloud Project
- [ ] Enable App Engine API
- [ ] Enable required APIs (if using Cloud services)
- [ ] Set up billing account

### ✅ 3. Files Created (Already Done)
- [x] `app.yaml` - App Engine configuration
- [x] `main.py` - Unified entry point
- [x] `.gcloudignore` - Deployment exclusions
- [x] `requirements.txt` - Python dependencies

## Deployment Steps

### Step 1: Update Environment Variables
**IMPORTANT**: Before deployment, update the environment variables in `app.yaml`:

```yaml
env_variables:
  # Update MongoDB connection for production
  MONGO_URL: "your-production-mongodb-connection-string"
  
  # Verify all API keys are correct
  OPENAI_API_KEY: "your-openai-api-key"
  WALMART_CONSUMER_ID: "your-walmart-consumer-id"
  WALMART_PRIVATE_KEY: "your-walmart-private-key"
  MAILJET_API_KEY: "your-mailjet-api-key"
  MAILJET_SECRET_KEY: "your-mailjet-secret-key"
  
  # Generate a strong secret key for JWT
  SECRET_KEY: "generate-a-strong-random-secret-key-here"
```

### Step 2: Build React Frontend
```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Build production version
npm run build

# Navigate back to root
cd ..
```

### Step 3: Set Google Cloud Project
```bash
# Set your project ID
gcloud config set project YOUR_PROJECT_ID

# Initialize App Engine (first time only)
gcloud app create --region=us-central1
```

### Step 4: Deploy to App Engine
```bash
# Deploy from root directory
gcloud app deploy

# Optional: Deploy with specific version
gcloud app deploy --version=v1 --no-promote
```

### Step 5: View Your App
```bash
# Open the deployed app in browser
gcloud app browse
```

## Post-Deployment Verification

### ✅ Check App Functionality
- [ ] Landing page loads correctly
- [ ] User registration/login works
- [ ] AI recipe generation works
- [ ] Starbucks generator works
- [ ] Walmart integration works
- [ ] Recipe history displays

### ✅ Monitor and Logs
```bash
# View application logs
gcloud app logs tail -s default

# Check app status
gcloud app describe
```

## Production Considerations

### Database Migration
- [ ] Set up production MongoDB instance (MongoDB Atlas recommended)
- [ ] Update MONGO_URL in app.yaml
- [ ] Migrate existing data if needed

### Security
- [ ] Update CORS origins in main.py to specific domains
- [ ] Use Google Secret Manager for sensitive data
- [ ] Enable HTTPS (automatic with App Engine)

### Performance
- [ ] Configure scaling parameters in app.yaml
- [ ] Set up monitoring and alerts
- [ ] Optimize static file serving

### Domain Configuration
- [ ] Configure custom domain if needed
- [ ] Set up DNS records
- [ ] Configure SSL certificate

## Troubleshooting

### Common Issues
1. **Build fails**: Check that frontend/build directory exists
2. **API endpoints not working**: Verify /api prefix in routes
3. **Environment variables not loaded**: Check app.yaml syntax
4. **Database connection fails**: Verify MongoDB connection string

### Debug Commands
```bash
# Check deployment status
gcloud app describe

# View recent logs
gcloud app logs tail -s default

# Check app versions
gcloud app versions list
```

## Useful Commands

### App Engine Management
```bash
# Stop a version
gcloud app versions stop VERSION_ID

# Delete a version
gcloud app versions delete VERSION_ID

# Set traffic allocation
gcloud app services set-traffic default --splits=v1=100
```

### Local Testing
```bash
# Test locally before deployment
python main.py

# Access at http://localhost:8080
```

## Environment Variables Reference

Your app uses these environment variables:
- `MONGO_URL` - MongoDB connection string
- `DB_NAME` - Database name
- `OPENAI_API_KEY` - OpenAI API key
- `WALMART_CONSUMER_ID` - Walmart API consumer ID
- `WALMART_KEY_VERSION` - Walmart API key version
- `WALMART_PRIVATE_KEY` - Walmart API private key
- `MAILJET_API_KEY` - Mailjet API key
- `MAILJET_SECRET_KEY` - Mailjet secret key
- `SENDER_EMAIL` - Email sender address
- `STRIPE_API_KEY` - Stripe API key
- `SECRET_KEY` - JWT secret key

## Support Resources

- [Google Cloud App Engine Documentation](https://cloud.google.com/appengine/docs)
- [FastAPI Deployment Guide](https://fastapi.tiangolo.com/deployment/)
- [React Deployment Guide](https://create-react-app.dev/docs/deployment/)