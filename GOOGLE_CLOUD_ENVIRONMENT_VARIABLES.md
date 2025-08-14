# Google Cloud Run Environment Variables

## 🔑 Required Environment Variables for Deployment

When deploying to Google Cloud Run, set these environment variables in your Cloud Run service configuration:

### **Stripe Payment Configuration**
```
STRIPE_API_KEY=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
STRIPE_PUBLISHABLE_KEY=pk_live_51RsCXtCSVHHl6aKERazrpCgt9zu82GiYcSxL484QFhxdfoZc1KMJ2LqMR4Ozzq0K2V8kb0sOwRVFk0Xj09xfSpOw00CUkX4dhB
```

### **MongoDB Configuration**
```
MONGO_URL=your-mongodb-connection-string-here
```

### **OpenAI Configuration**
```
OPENAI_API_KEY=your-openai-api-key-here
```

### **Walmart Integration**
```
WALMART_CLIENT_ID=your-walmart-client-id-here
WALMART_CLIENT_SECRET=your-walmart-client-secret-here
```

### **Email Configuration**
```
MAILJET_API_KEY=your-mailjet-api-key-here
MAILJET_SECRET_KEY=your-mailjet-secret-key-here
SENDER_EMAIL=your-sender-email@example.com
```

### **Application Security**
```
SECRET_KEY=your-jwt-secret-key-here
```

## 🚀 Deployment Steps

1. **Set Environment Variables in Google Cloud Run:**
   - Go to Google Cloud Console
   - Navigate to Cloud Run → Your Service
   - Click "Edit & Deploy New Revision"
   - In "Container" tab, scroll to "Environment Variables"
   - Add each variable above with your actual values

2. **Deploy:**
   ```bash
   gcloud run deploy
   ```

## ⚠️ Security Notes

- **Never commit real API keys to Git repositories**
- The `.env` file in this repo contains placeholder values only
- Real keys should only exist in your Google Cloud Run environment variables
- Use live Stripe keys (`sk_live_` and `pk_live_`) for production

## ✅ Validation

The application will validate environment variables on startup:
- Stripe keys must start with `sk_live_` or `sk_test_`
- Placeholder values like "your-stripe-secret-key-here" will be rejected
- Missing required variables will prevent startup

## 📞 Support

If deployment fails, check:
1. All environment variables are set in Google Cloud Run
2. API keys are valid and not placeholder values  
3. MongoDB connection string is accessible from Google Cloud
4. Stripe keys match the format requirements