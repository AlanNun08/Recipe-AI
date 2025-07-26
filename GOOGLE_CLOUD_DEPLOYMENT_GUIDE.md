# Google Cloud Deployment Guide

## Prerequisites
- Google Cloud account with billing enabled
- gcloud CLI installed and configured
- Your application API keys ready

## Step 1: Set Up Environment Variables in Google Cloud

### Using Google Cloud Console (Recommended for Cloud Run)
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Navigate to **Cloud Run** → **[Your Service]** → **Edit Container**
3. Go to **Variables & Secrets** tab
4. Add the following environment variables:

#### Required Environment Variables:
```bash
# Database Configuration
MONGO_URL = "your-mongodb-atlas-connection-string"
DB_NAME = "buildyoursmartcart_production"

# OpenAI API Configuration
OPENAI_API_KEY = "sk-proj-your-openai-api-key"

# Walmart API Configuration
WALMART_CONSUMER_ID = "your-walmart-consumer-id"
WALMART_KEY_VERSION = "1"
WALMART_PRIVATE_KEY = "-----BEGIN PRIVATE KEY-----
your-walmart-private-key
-----END PRIVATE KEY-----"

# Mailjet Email Service Configuration
MAILJET_API_KEY = "your-mailjet-api-key"
MAILJET_SECRET_KEY = "your-mailjet-secret-key"
SENDER_EMAIL = "your-sender-email@example.com"

# Stripe Configuration
STRIPE_API_KEY = "sk_test_your-stripe-api-key"

# JWT Secret Key (generate a strong random string)
SECRET_KEY = "your-strong-random-jwt-secret"
```

### Option 2: Using Environment Variables Bulk Upload
1. In Google Cloud Console, go to **Variables & Secrets**
2. Click **Add Environment Variable**
3. In the **Name** field, you can paste your .env file content and it will populate automatically

#### Sample .env Format for Google Cloud:
```
MONGO_URL=mongodb+srv://username:password@cluster.mongodb.net/database
DB_NAME=buildyoursmartcart_production
OPENAI_API_KEY=sk-proj-your-openai-api-key
WALMART_CONSUMER_ID=your-walmart-consumer-id
WALMART_KEY_VERSION=1
WALMART_PRIVATE_KEY=-----BEGIN PRIVATE KEY-----
your-walmart-private-key
-----END PRIVATE KEY-----
MAILJET_API_KEY=your-mailjet-api-key
MAILJET_SECRET_KEY=your-mailjet-secret-key
SENDER_EMAIL=your-sender-email@example.com
STRIPE_API_KEY=sk_test_your-stripe-api-key
SECRET_KEY=your-strong-random-jwt-secret
```

## Step 2: Container Configuration

### Container Settings:
- **Container port**: 8080 (Google Cloud will set the $PORT environment variable)
- **Container command**: Leave blank (uses default from Dockerfile)
- **Container arguments**: Leave blank

### Important Notes:
1. **Port Configuration**: The application is configured to use port 8080 in production (Google Cloud standard)
2. **CORS**: The application is configured to allow requests from your frontend domain
3. **Database**: Make sure to use MongoDB Atlas or another cloud-hosted MongoDB instance

## Step 3: Deploy Your Application

### Using Google Cloud Build:
1. Connect your repository to Google Cloud Build
2. The application will automatically build and deploy when you push changes
3. The environment variables set in Step 1 will be automatically injected

### Using gcloud CLI:
```bash
# Deploy the application
gcloud run deploy your-app-name \
  --source . \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated
```

## Step 4: Update Frontend Configuration

After deployment, you'll get a Cloud Run URL (e.g., `https://your-app-name-xxxxx-uc.a.run.app`)

Update your frontend environment variables:
```bash
# In your frontend deployment (Vercel, Netlify, etc.)
REACT_APP_BACKEND_URL=https://your-app-name-xxxxx-uc.a.run.app
```

## Step 5: Test Your Deployment

1. **Health Check**: Visit `https://your-app-name-xxxxx-uc.a.run.app/docs` to see the API documentation
2. **API Test**: Test the `/api/auth/login` endpoint with demo credentials
3. **Full Integration**: Test recipe generation and Walmart integration

## Security Best Practices

1. **Never commit API keys** to version control
2. **Use strong random secrets** for JWT_SECRET_KEY
3. **Monitor API usage** to detect unusual activity
4. **Regularly rotate API keys** for security
5. **Use Cloud Monitoring** to track application performance

## Troubleshooting

### Common Issues:
1. **MongoDB Connection**: Ensure your MongoDB Atlas allows connections from Google Cloud IPs
2. **API Key Errors**: Double-check all environment variables are set correctly
3. **CORS Issues**: Verify your frontend URL is properly configured
4. **Port Issues**: Google Cloud automatically sets the PORT environment variable

### Debugging:
- Check Cloud Run logs in Google Cloud Console
- Use the `/debug/user/test@example.com` endpoint for development debugging
- Monitor API response times and error rates

## API Keys You'll Need

| Service | Key Required | Where to Get |
|---------|--------------|--------------|
| OpenAI | API Key | https://platform.openai.com/api-keys |
| Walmart | Consumer ID + Private Key | https://developer.walmart.com/ |
| Mailjet | API Key + Secret | https://app.mailjet.com/account/api_keys |
| Stripe | API Key | https://dashboard.stripe.com/apikeys |
| MongoDB | Connection String | https://cloud.mongodb.com/ |

## Need Help?

If you encounter any issues:
1. Check the Cloud Run logs for detailed error messages
2. Verify all environment variables are properly set
3. Test individual API endpoints using the `/docs` interface
4. Contact support if you need assistance with API key setup

---

**Note**: This deployment guide assumes you're using Google Cloud Run. The same principles apply to other deployment platforms - just adapt the environment variable setup to your chosen platform.