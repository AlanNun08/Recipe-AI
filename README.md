# 🍳 AI Recipe + Grocery Delivery App

A comprehensive platform for AI-powered recipe generation with integrated grocery shopping and subscription management.

## 🌟 Features

- **AI Recipe Generation**: Create personalized recipes using OpenAI
- **Weekly Meal Planning**: Generate 7-day meal plans with grocery lists
- **Starbucks Secret Menu**: Generate creative Starbucks drink recipes
- **Walmart Integration**: Automated grocery shopping cart generation
- **Subscription Management**: Premium features with usage limits and billing
- **User Profiles**: Dietary preferences and usage tracking
- **Recipe History**: Save and organize your generated recipes

## 🏗️ Tech Stack

- **Backend**: FastAPI (Python) + MongoDB
- **Frontend**: React + Tailwind CSS
- **Payment**: Native Stripe integration
- **Deployment**: Google Cloud Run
- **Database**: MongoDB Atlas

## 🚀 Deployment

### Prerequisites
- Google Cloud account with billing enabled
- MongoDB Atlas database
- API keys for integrations (see environment variables below)

### Environment Variables
Set these in your Google Cloud Run service:

```bash
# Database
MONGO_URL=your-mongodb-connection-string-from-atlas
DB_NAME=your_database_name

# AI Services
OPENAI_API_KEY=your-openai-api-key-from-platform

# Payment Processing
STRIPE_API_KEY=your-stripe-secret-key-from-dashboard
STRIPE_PUBLISHABLE_KEY=your-stripe-publishable-key-from-dashboard

# Walmart Integration
WALMART_CONSUMER_ID=your-walmart-consumer-id-from-developer-portal
WALMART_KEY_VERSION=1
WALMART_PRIVATE_KEY="-----BEGIN PRIVATE KEY-----
your-walmart-private-key-from-developer-portal
-----END PRIVATE KEY-----"

# Email Service
MAILJET_API_KEY=your-mailjet-api-key-from-dashboard
MAILJET_SECRET_KEY=your-mailjet-secret-key-from-dashboard
SENDER_EMAIL=noreply@yourdomain.com

# Security
SECRET_KEY=your-generated-jwt-secret-key
```

### Deploy to Google Cloud Run

1. **Build and Deploy:**
```bash
gcloud run deploy recipe-ai \
  --source . \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --port 8080
```

2. **Set Environment Variables:**
```bash
gcloud run services update recipe-ai \
  --set-env-vars STRIPE_API_KEY=your-actual-stripe-key \
  --set-env-vars MONGO_URL=mongodb+srv://your-connection-string \
  --region us-central1
```

## 💳 Subscription Plans

### Free Trial (7 days)
- 2 weekly recipe plans
- 10 individual recipes
- 10 Starbucks drinks

### Premium Monthly ($9.99/month)
- 3 weekly recipe plans
- 30 individual recipes
- 30 Starbucks drinks
- Unlimited recipe history

## 🔧 Development

### Local Setup
1. **Clone repository:**
```bash
git clone [repository-url]
cd ai-recipe-app
```

2. **Install dependencies:**
```bash
# Backend
cd backend
pip install -r requirements.txt

# Frontend
cd ../frontend
yarn install
```

3. **Set environment variables:**
Copy `/app/backend/.env` and update with your API keys

4. **Run services:**
```bash
# Start backend
python main.py

# Start frontend
cd frontend && yarn start
```

### Project Structure
```
/app/
├── backend/                 # FastAPI backend
│   ├── server.py           # Main API routes
│   ├── stripe_native.py    # Payment processing
│   └── requirements.txt    # Python dependencies
├── frontend/               # React frontend
│   ├── src/
│   │   ├── App.js         # Main app component
│   │   └── components/    # React components
│   └── package.json       # Node dependencies
├── docs/                   # Documentation
├── Dockerfile             # Container configuration
└── main.py                # Application entry point
```

## 🔒 Security Features

- **Environment Variable Security**: All API keys stored in environment variables
- **Payment Security**: PCI-compliant Stripe integration
- **User Authentication**: JWT-based authentication system
- **Input Validation**: Comprehensive request validation
- **Rate Limiting**: Usage limits and API protection

## 📊 Usage Tracking

The app implements comprehensive usage tracking:
- Monthly reset cycles for all quotas
- Real-time usage monitoring
- Upgrade prompts when limits reached
- Analytics dashboard for subscription metrics

## 🛠️ API Documentation

### Key Endpoints

**Authentication:**
- `POST /api/auth/register` - User registration
- `POST /api/auth/login` - User login

**Recipe Generation:**
- `POST /api/recipes/generate` - Generate individual recipe
- `POST /api/weekly-recipes/generate` - Generate weekly meal plan
- `POST /api/generate-starbucks-drink` - Generate Starbucks recipe

**Subscription Management:**
- `POST /api/subscription/create-checkout` - Create payment session
- `GET /api/subscription/status/{user_id}` - Get subscription status
- `POST /api/subscription/cancel/{user_id}` - Cancel subscription

**User Management:**
- `GET /api/user/settings/{user_id}` - Get user settings
- `PUT /api/user/profile/{user_id}` - Update user profile

## 🐛 Troubleshooting

### Common Issues

**Deployment Fails:**
- Check all environment variables are set in Google Cloud Run
- Verify API keys are valid and not placeholder values
- Ensure MongoDB connection string is accessible

**Payment Issues:**
- Confirm Stripe keys match the correct format (sk_live_, pk_live_)
- Check webhook endpoints are configured in Stripe dashboard
- Verify domain is added to Stripe's allowed origins

**Recipe Generation Fails:**
- Validate OpenAI API key and billing status
- Check usage quotas haven't been exceeded
- Verify dietary preferences are properly formatted

## 📞 Support

For deployment and configuration issues, check:
1. Google Cloud Run logs
2. MongoDB connection status  
3. API key validity and format
4. Environment variable configuration

## 📄 License

This project is proprietary software. All rights reserved.