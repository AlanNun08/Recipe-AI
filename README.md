# buildyoursmartcart.com

**AI Recipe + Grocery Delivery App - Weekly Meal Planning & Walmart Integration**

A comprehensive full-stack application that combines AI-powered recipe generation with grocery delivery integration, featuring weekly meal planning, individual recipe creation, and Starbucks secret menu generation.

## 🚀 Features

- **AI Recipe Generation**: Create personalized recipes using OpenAI GPT
- **Weekly Meal Planning**: Generate 7-day meal plans with grocery integration
- **Walmart Shopping Integration**: Direct product links and cart generation
- **Starbucks Secret Menu**: Curated and AI-generated drink recipes
- **User Authentication**: Secure registration, login, and email verification
- **Subscription Management**: Free trial + premium monthly subscription
- **Usage Limits**: Controlled access to premium features
- **Mobile Responsive**: Optimized for all devices

## 🏗️ Architecture

### Technology Stack

**Backend:**
- FastAPI (Python 3.9+)
- MongoDB with Motor (async driver)
- OpenAI API for recipe generation
- Stripe for payments
- Mailjet for email services
- Walmart API for product search

**Frontend:**
- React 18
- Tailwind CSS
- Axios for API communication
- Responsive design

**Infrastructure:**
- Google Cloud Run (production)
- Docker containerization
- Environment-based configuration

### Project Structure

```
/app/
├── src/backend/              # Backend application
│   ├── api/                  # API route handlers
│   │   ├── auth.py          # Authentication routes
│   │   └── recipes.py       # Recipe routes
│   ├── models/              # Data models
│   │   ├── user.py          # User-related models
│   │   ├── recipe.py        # Recipe models
│   │   └── payment.py       # Payment models
│   ├── services/            # Business logic
│   │   ├── auth.py          # Authentication service
│   │   ├── recipe.py        # Recipe generation service
│   │   ├── database.py      # Database service
│   │   ├── email.py         # Email service
│   │   └── stripe.py        # Payment service
│   └── main.py             # FastAPI application
├── frontend/                # React frontend
│   ├── src/
│   │   ├── components/      # React components
│   │   └── index.js         # App entry point
│   └── public/             # Static assets
├── tests/                   # Test suite
│   ├── unit/               # Unit tests
│   ├── integration/        # Integration tests
│   └── e2e/               # End-to-end tests
├── config/                 # Configuration
│   └── settings.py         # Application settings
├── main.py                 # Production server
├── Dockerfile              # Container configuration
└── pyproject.toml          # Project configuration
```

## 🚀 Quick Start

### Prerequisites

- Python 3.9+
- Node.js 18+
- MongoDB
- Docker (optional)

### Environment Setup

1. **Clone and Setup:**
```bash
git clone <repository>
cd buildyoursmartcart
```

2. **Backend Environment:**
```bash
# Install Python dependencies
pip install -e ".[dev,test]"

# Create backend environment file
cp src/backend/.env.example src/backend/.env
```

3. **Frontend Environment:**
```bash
cd frontend
yarn install

# Create frontend environment file
cp .env.example .env
```

### Environment Variables

**Backend (.env):**
```bash
# Database
MONGO_URL=mongodb://localhost:27017
DB_NAME=buildyoursmartcart_development

# API Keys
OPENAI_API_KEY=your-openai-api-key-here
STRIPE_API_KEY=your-stripe-secret-key-here
STRIPE_PUBLISHABLE_KEY=your-stripe-publishable-key-here
MAILJET_API_KEY=your-mailjet-api-key-here
MAILJET_SECRET_KEY=your-mailjet-secret-key-here
WALMART_CONSUMER_ID=your-walmart-consumer-id-here
WALMART_PRIVATE_KEY=your-walmart-private-key-here

# Email
SENDER_EMAIL=noreply@buildyoursmartcart.com

# Security
SECRET_KEY=your-secret-key-for-jwt-here
```

**Frontend (.env):**
```bash
REACT_APP_BACKEND_URL=http://localhost:8001
```

### Running the Application

**Development Mode:**
```bash
# Terminal 1: Backend
make dev
# or
cd src && uvicorn backend.main:app --host 0.0.0.0 --port 8001 --reload

# Terminal 2: Frontend
cd frontend && yarn start

# Terminal 3: MongoDB (if running locally)
mongod
```

**Production Mode:**
```bash
make run
# or
python main.py
```

**Using Docker:**
```bash
make docker-build
make docker-run
```

## 🧪 Testing

### Running Tests

```bash
# All tests
make test

# Unit tests only
make test-unit

# Integration tests only
make test-integration

# End-to-end tests only
make test-e2e

# With coverage
make test-coverage
```

### Test Structure

- **Unit Tests**: Test individual functions and classes in isolation
- **Integration Tests**: Test API endpoints and service interactions
- **E2E Tests**: Test complete user workflows

## 🚢 Deployment

### Google Cloud Run

1. **Build and Deploy:**
```bash
# Set environment variables in Google Cloud
gcloud run services update buildyoursmartcart \
  --set-env-vars MONGO_URL=your-production-mongo-url \
  --set-env-vars OPENAI_API_KEY=your-production-openai-key \
  --set-env-vars STRIPE_API_KEY=your-production-stripe-key \
  --region us-central1

# Deploy
gcloud run deploy buildyoursmartcart \
  --source . \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated
```

2. **Environment Variables Required for Production:**
- `NODE_ENV=production`
- `MONGO_URL` (production MongoDB connection)
- `DB_NAME=buildyoursmartcart_production`
- All API keys with production values

### Production Checklist

- [ ] Environment variables configured
- [ ] Database backups configured
- [ ] Monitoring and logging set up
- [ ] SSL certificates configured
- [ ] CORS properly configured
- [ ] Rate limiting enabled
- [ ] Security headers configured

## 🔧 Development

### Code Quality

```bash
# Format code
make format

# Check formatting
make format-check

# Lint code
make lint

# Run all validation
make validate
```

### API Documentation

When running in development mode, API documentation is available at:
- Swagger UI: http://localhost:8001/docs
- ReDoc: http://localhost:8001/redoc

### Database Schema

**Users Collection:**
```javascript
{
  id: "uuid",
  email: "user@example.com",
  password: "hashed_password",
  is_verified: true,
  subscription: {
    status: "trialing|active|expired|cancelled",
    trial_starts_at: "ISO_date",
    trial_ends_at: "ISO_date",
    customer_id: "stripe_customer_id"
  },
  usage_limits: {
    weekly_recipes: {used: 0, limit: 2},
    individual_recipes: {used: 0, limit: 10},
    starbucks_drinks: {used: 0, limit: 10}
  }
}
```

**Recipes Collection:**
```javascript
{
  id: "uuid",
  user_id: "user_uuid",
  name: "Recipe Name",
  description: "Recipe description",
  ingredients: ["ingredient1", "ingredient2"],
  instructions: ["step1", "step2"],
  prep_time: "15 minutes",
  cook_time: "30 minutes",
  servings: 4,
  difficulty: "easy|medium|hard",
  cuisine_type: "italian",
  calories: 500,
  created_at: "ISO_date"
}
```

## 📊 Usage Limits

### Free Trial (7 days)
- Weekly meal plans: 2 per month
- Individual recipes: 10 per month
- Starbucks drinks: 10 per month

### Premium Subscription ($9.99/month)
- Weekly meal plans: 8 per month
- Individual recipes: 30 per month
- Starbucks drinks: 30 per month

## 🔐 Security

### Best Practices Implemented

1. **Environment Variables**: All sensitive data in environment variables
2. **Password Hashing**: Bcrypt for password security
3. **Input Validation**: Pydantic models for request validation
4. **CORS Configuration**: Properly configured allowed origins
5. **Rate Limiting**: API rate limiting (configurable)
6. **Secure Headers**: Security headers in production
7. **Database Security**: Parameterized queries, no SQL injection

### Security Validation

```bash
# Run security scan
make security-scan
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make changes with tests
4. Run validation: `make validate`
5. Submit a pull request

### Development Guidelines

- Follow PEP 8 for Python code
- Use TypeScript for complex frontend logic
- Write tests for new features
- Update documentation
- Use conventional commits

## 📈 Monitoring and Analytics

### Health Checks

- **API Health**: `/health` endpoint
- **Database Health**: MongoDB connection status
- **External APIs**: OpenAI, Stripe, Walmart connectivity

### Logging

- Structured logging with Python logging
- Request/response logging
- Error tracking and alerting

## 🆘 Troubleshooting

### Common Issues

1. **Database Connection**: Check MONGO_URL and database accessibility
2. **API Keys**: Ensure all API keys are valid and not placeholders
3. **CORS Issues**: Verify allowed origins configuration
4. **Port Conflicts**: Ensure ports 8001 (backend) and 3000 (frontend) are available

### Debug Mode

```bash
# Enable debug logging
export LOG_LEVEL=DEBUG
make dev
```

## 📄 License

MIT License - see LICENSE file for details

## 📞 Support

- Email: support@buildyoursmartcart.com
- Documentation: This README
- Issues: GitHub Issues (if applicable)

---

**buildyoursmartcart.com** - Simplifying meal planning with AI-powered recipes and grocery integration.