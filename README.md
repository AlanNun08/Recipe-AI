# AI Chef - Recipe Generator & Grocery Delivery Platform

A comprehensive AI-powered recipe generation and grocery delivery platform that integrates with Walmart for seamless shopping experiences. Built with React, FastAPI, and MongoDB with modern architecture patterns.

## 🚀 Quick Start

```bash
# Clone and setup
git clone <repository-url>
cd buildyoursmartcart

# Backend setup
cd backend && pip install -r requirements.txt
uvicorn server:app --host 0.0.0.0 --port 8001 --reload

# Frontend setup (new terminal)
cd frontend && yarn install && yarn start
```

## 📋 Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Features & Capabilities](#features--capabilities)  
3. [Tech Stack & Dependencies](#tech-stack--dependencies)
4. [Environment Setup](#environment-setup)
5. [Component Documentation](#component-documentation)
6. [API Reference](#api-reference)
7. [Feature Integration Guide](#feature-integration-guide)
8. [Testing Strategy](#testing-strategy)
9. [Deployment Guide](#deployment-guide)
10. [Troubleshooting](#troubleshooting)

## 🏗️ Architecture Overview

### System Architecture
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   React Frontend │◄──►│  FastAPI Backend │◄──►│   MongoDB Atlas │
│   (Port 3000)   │    │   (Port 8001)   │    │   (Database)    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                        │                        │
         │                        ▼                        │
         ▼              ┌─────────────────┐                ▼
┌─────────────────┐    │  External APIs  │    ┌─────────────────┐
│   User Browser  │    │  • OpenAI GPT   │    │   File Storage  │
│   (Interface)   │    │  • Walmart API  │    │   (Local/Cloud) │
└─────────────────┘    │  • Stripe API   │    └─────────────────┘
                        │  • Mailjet API  │
                        └─────────────────┘
```

### Key Design Principles
- **Component-Based Architecture**: Modular React components with clear responsibilities
- **API-First Design**: RESTful APIs with comprehensive error handling
- **State Management**: React hooks with context where needed
- **Responsive Design**: Mobile-first approach with Tailwind CSS
- **Security First**: Environment variables, API key protection, secure authentication
- **Error Boundaries**: Graceful error handling at every level

## ✨ Features & Capabilities

### Core Features
- 🤖 **AI Recipe Generation**: Personalized recipes using OpenAI GPT
- 🛒 **Walmart Integration**: Real-time product search and cart creation
- 📅 **Weekly Meal Planning**: 7-day meal plans with shopping lists
- ☕ **Starbucks Secret Menu**: Custom drink recipe generator
- 📚 **Recipe Management**: Save, organize, filter, and delete recipes
- 💳 **Subscription Model**: Stripe integration with 7-day free trial
- 📱 **Responsive Design**: Works on all devices
- 🔐 **User Authentication**: Secure login/registration system

### Premium Features
- Weekly meal plan generation
- Unlimited recipe saves
- Advanced filtering options
- Priority customer support

## 🛠️ Tech Stack & Dependencies

### Frontend Stack
```json
{
  "framework": "React 18",
  "styling": "Tailwind CSS",
  "state": "React Hooks + Context",
  "routing": "React Router (built into App.js)",
  "http": "Fetch API",
  "build": "Create React App + Craco"
}
```

### Backend Stack
```json
{
  "framework": "FastAPI",
  "language": "Python 3.9+",
  "database": "MongoDB Atlas",
  "auth": "JWT Tokens",
  "validation": "Pydantic",
  "cors": "FastAPI CORS Middleware"
}
```

### External Services
- **OpenAI GPT**: Recipe generation and content creation
- **Walmart API**: Product search and cart integration
- **Stripe**: Payment processing and subscription management
- **Mailjet**: Email notifications and transactional emails

## 🔧 Environment Setup

### Required API Keys
Before starting, obtain these API keys:

1. **OpenAI API Key**: [Get from OpenAI](https://platform.openai.com/api-keys)
2. **Stripe Keys**: [Get from Stripe Dashboard](https://dashboard.stripe.com/apikeys)
3. **Walmart API**: [Apply at Walmart Developer](https://developer.walmart.com/)
4. **Mailjet**: [Register at Mailjet](https://app.mailjet.com/signup)
5. **MongoDB Atlas**: [Create cluster](https://cloud.mongodb.com/)

### Backend Environment (`.env` in `/backend/`)
```env
# AI Services
OPENAI_API_KEY=sk-...

# Payment Processing
STRIPE_API_KEY=sk_test_...

# Email Services
MAILJET_API_KEY=your_mailjet_key
MAILJET_SECRET_KEY=your_mailjet_secret

# Walmart Integration
WALMART_CONSUMER_ID=your_consumer_id
WALMART_PRIVATE_KEY="-----BEGIN PRIVATE KEY-----
your_private_key_content
-----END PRIVATE KEY-----"

# Database
MONGO_URL=mongodb+srv://username:password@cluster.mongodb.net/

# Security
JWT_SECRET_KEY=your_secure_random_string
```

### Frontend Environment (`.env` in `/frontend/`)
```env
# Backend API URL
REACT_APP_BACKEND_URL=http://localhost:8001

# Optional: Analytics, error reporting
REACT_APP_ENVIRONMENT=development
```

## 📖 Component Documentation

### Core Components Overview

| Component | Purpose | Key Features | Documentation |
|-----------|---------|--------------|---------------|
| **App.js** | Main router & state | Navigation, auth, notifications | [View Docs](/docs/components/APP_COMPONENT.md) |
| **RecipeHistoryScreen** | Recipe management | List, filter, delete recipes | [View Docs](/docs/components/RECIPE_HISTORY.md) |
| **RecipeDetailScreen** | Recipe viewing | Ingredients, instructions, cart | [View Docs](/docs/components/RECIPE_DETAIL.md) |
| **RecipeGeneratorScreen** | AI recipe creation | Form, generation, customization | [View Docs](/docs/components/RECIPE_GENERATOR.md) |
| **WeeklyRecipesScreen** | Meal planning | 7-day plans, bulk operations | [View Docs](/docs/components/WEEKLY_RECIPES.md) |
| **StarbucksGeneratorScreen** | Drink creation | Custom drinks, modifications | [View Docs](/docs/components/STARBUCKS_GENERATOR.md) |
| **SubscriptionScreen** | Payment flow | Stripe integration, trial | [View Docs](/docs/components/SUBSCRIPTION.md) |

### Component Integration Pattern
All components follow this standard pattern:

```javascript
function ComponentName({ 
  // Required props
  user, onBack, showNotification,
  // Component-specific props
  specificProp1, specificProp2 
}) {
  // State management
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  
  // API calls
  useEffect(() => {
    // Fetch data on mount
  }, [dependencies]);
  
  // Event handlers
  const handleAction = async () => {
    // Implementation
  };
  
  // Render with loading/error states
  if (loading) return <LoadingComponent />;
  if (error) return <ErrorComponent error={error} onRetry={refetch} />;
  return <MainComponent data={data} onAction={handleAction} />;
}
```

## 🔗 API Reference

### Base Configuration
```javascript
const API = process.env.REACT_APP_BACKEND_URL;
// All API calls use: `${API}/api/endpoint`
```

### Authentication Endpoints
```http
POST /api/auth/register
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "securepassword"
}

Response: {
  "user": { "id": "uuid", "email": "user@example.com" },
  "token": "jwt_token"
}
```

```http
POST /api/auth/login
Content-Type: application/json

{
  "email": "user@example.com", 
  "password": "securepassword"
}

Response: {
  "user": { "id": "uuid", "email": "user@example.com" },
  "token": "jwt_token"
}
```

### Recipe Endpoints
```http
GET /api/recipes/history/{user_id}
Response: {
  "recipes": [
    {
      "id": "uuid",
      "title": "Recipe Name",
      "description": "Recipe description",
      "cuisine_type": "italian",
      "prep_time": "30 minutes",
      "cook_time": "25 minutes", 
      "servings": 4,
      "difficulty": "medium",
      "created_at": "2025-01-01T12:00:00Z",
      "ingredients": ["ingredient1", "ingredient2"],
      "instructions": ["step1", "step2"]
    }
  ],
  "total_count": 25
}

POST /api/recipes/generate
Content-Type: application/json

{
  "cuisine_type": "italian",
  "dietary_preferences": ["vegetarian"],
  "cooking_time": "30 minutes",
  "servings": 4,
  "difficulty": "medium"
}

DELETE /api/recipes/{recipe_id}
Response: { "success": true, "message": "Recipe deleted successfully" }
```

### Walmart Integration
```http
POST /api/v2/walmart/weekly-cart-options?recipe_id={recipe_id}
Response: {
  "ingredient_matches": [
    {
      "ingredient": "tomatoes",
      "products": [
        {
          "id": "walmart_product_id",
          "name": "Fresh Tomatoes",
          "price": 2.99,
          "image": "https://walmart.com/image.jpg"
        }
      ]
    }
  ],
  "total_products": 15,
  "estimated_total": 45.67
}
```

For complete API documentation, see: [API_REFERENCE.md](/docs/API_REFERENCE.md)

## 🔄 Feature Integration Guide

### Adding a New Component

1. **Create Component File**
```javascript
// /frontend/src/components/NewFeatureScreen.js
import React, { useState, useEffect } from 'react';

const API = process.env.REACT_APP_BACKEND_URL;

function NewFeatureScreen({ user, onBack, showNotification }) {
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(true);
  
  useEffect(() => {
    // Fetch data
  }, [user?.id]);
  
  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-purple-50">
      {/* Component content */}
    </div>
  );
}

export default NewFeatureScreen;
```

2. **Add to App.js**
```javascript
// Add import
import NewFeatureScreen from './components/NewFeatureScreen';

// Add to switch statement
case 'new-feature':
  return <NewFeatureScreen 
    user={user}
    onBack={() => setCurrentScreen('dashboard')}
    showNotification={showNotification}
  />;
```

3. **Add Navigation**
```javascript
// Add to dashboard or navigation menu
<button onClick={() => setCurrentScreen('new-feature')}>
  New Feature
</button>
```

### Adding a New API Endpoint

1. **Backend Implementation**
```python
# In server.py
@api_router.get("/new-endpoint")
async def new_endpoint():
    try:
        # Implementation
        return {"success": True, "data": result}
    except Exception as e:
        logger.error(f"New endpoint error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
```

2. **Frontend Integration**
```javascript
// In component
const fetchNewData = async () => {
  try {
    const response = await fetch(`${API}/api/new-endpoint`);
    if (!response.ok) throw new Error('Failed to fetch');
    const data = await response.json();
    setData(data);
  } catch (error) {
    showNotification('Error loading data', 'error');
  }
};
```

For detailed integration guides, see: [FEATURE_INTEGRATION_GUIDE.md](/docs/FEATURE_INTEGRATION_GUIDE.md)

## 🧪 Testing Strategy

### Test Structure
```
/tests/
├── unit/              # Individual component tests
├── integration/       # API endpoint tests  
├── e2e/              # End-to-end user flows
└── utils/            # Test utilities and mocks
```

### Running Tests
```bash
# Backend tests
cd backend && python -m pytest tests/

# Frontend tests  
cd frontend && yarn test

# Integration tests
python run_all_tests.py

# E2E tests
yarn test:e2e
```

### Writing New Tests
Follow the established patterns in `/docs/TESTING_GUIDE.md`

## 🚀 Deployment Guide

### Development Deployment
```bash
# Start all services
docker-compose up -d

# Or individually
cd backend && uvicorn server:app --reload
cd frontend && yarn start
```

### Production Deployment (Google Cloud Run)
```bash
# Build and deploy
./deploy-production.sh

# Verify deployment
./verify_production.sh
```

For detailed deployment instructions, see: [DEPLOYMENT_GUIDE.md](/docs/DEPLOYMENT_GUIDE.md)

## 🔧 Troubleshooting

### Common Issues

**Frontend won't load**
- Check `REACT_APP_BACKEND_URL` in `/frontend/.env`
- Verify backend is running on correct port
- Check browser console for errors

**API calls failing**
- Verify API keys in `/backend/.env`
- Check MongoDB connection string
- Review backend logs: `tail -f /var/log/supervisor/backend.out.log`

**Walmart integration not working**
- Verify `WALMART_CONSUMER_ID` and `WALMART_PRIVATE_KEY`
- Check API rate limits
- Review Walmart API documentation

For comprehensive troubleshooting, see: [TROUBLESHOOTING_GUIDE.md](/docs/TROUBLESHOOTING_GUIDE.md)

## 📚 Additional Documentation

- [Component Architecture](/docs/COMPONENT_ARCHITECTURE.md)
- [Database Schema](/docs/DATABASE_SCHEMA.md)
- [Security Guidelines](/docs/SECURITY_GUIDE.md)
- [Performance Optimization](/docs/PERFORMANCE_GUIDE.md)
- [Mobile Considerations](/docs/MOBILE_GUIDE.md)

## 🤝 Contributing

### Development Workflow
1. Create feature branch from `main`
2. Follow coding standards in `/docs/CODING_STANDARDS.md`
3. Write tests for new features
4. Update documentation
5. Submit pull request with clear description

### Code Review Checklist
- [ ] Follows component architecture patterns
- [ ] Includes appropriate error handling
- [ ] Has loading states and user feedback
- [ ] Updates relevant documentation
- [ ] Passes all tests
- [ ] Handles edge cases

## 📄 License

This project is proprietary software. All rights reserved.

---

## 📞 Support

For technical support or questions:
- Review documentation in `/docs/`
- Check troubleshooting guide
- Contact development team

**Last Updated**: January 2025
**Version**: 2.0.0