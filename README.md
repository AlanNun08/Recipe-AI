# BuildYourSmartCart.com - AI-Powered Recipe & Meal Planning Platform

A comprehensive meal planning and recipe generation platform powered by AI, featuring Walmart integration for seamless grocery shopping and Starbucks secret menu generation.

## 🌟 Features

### Core Features
- **AI Recipe Generation**: Create personalized recipes using OpenAI's GPT models
- **Weekly Meal Planning**: Generate complete weekly meal plans with balanced nutrition
- **Starbucks Secret Menu Generator**: Create unique Starbucks drinks with AI
- **Smart Walmart Shopping**: Automatic product matching and cart creation
- **User Authentication**: Secure MongoDB-based user system with email verification
- **Recipe Management**: Save, edit, and organize your favorite recipes

### Advanced Features
- **Community Features**: Share recipes and discover community creations
- **Curated Collections**: Hand-picked Starbucks recipes from our team
- **Nutritional Analysis**: Detailed nutritional information for all recipes
- **Dietary Preferences**: Support for various dietary restrictions
- **Cost Estimation**: Real-time Walmart pricing and budget planning
- **Mobile Responsive**: Optimized for all device types with PWA support

## 🛠️ Technology Stack

### Backend
- **FastAPI**: Modern Python web framework with async support
- **MongoDB**: NoSQL database with Motor async driver
- **OpenAI API**: GPT-3.5/4 for recipe and drink generation
- **Walmart Open API**: Real-time product search and pricing
- **Pydantic**: Data validation and serialization
- **CORS**: Cross-origin resource sharing support

### Frontend
- **React 18**: Modern React with hooks and context
- **Tailwind CSS**: Utility-first CSS framework with custom animations
- **Axios**: HTTP client for API communication
- **Context API**: Global state management
- **PWA Support**: Service workers and offline capabilities

### Infrastructure
- **Google Cloud Run**: Serverless container deployment
- **Docker**: Multi-stage containerization
- **Environment Variables**: Secure configuration management
- **Static File Serving**: Optimized React build serving

## 🚀 Quick Start

### Prerequisites
- Python 3.9+
- Node.js 16+
- MongoDB instance (local or Atlas)
- OpenAI API key
- Walmart API credentials (Consumer ID & Private Key)

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/yourusername/Recipe-AI.git
cd Recipe-AI
```

2. **Environment Setup**
Create a `.env` file in the root directory:
```env
# Database Configuration
MONGO_URL=mongodb://localhost:27017
# Or MongoDB Atlas: mongodb+srv://username:password@cluster.mongodb.net/
DB_NAME=recipe_ai_dev

# API Keys
OPENAI_API_KEY=sk-your_openai_api_key_here
WALMART_CONSUMER_ID=your_walmart_consumer_id_uuid
WALMART_PRIVATE_KEY=your_base64_encoded_private_key
WALMART_KEY_VERSION=1

# Optional API Keys (for future features)
STRIPE_SECRET_KEY=sk_test_your_stripe_key
MAILJET_API_KEY=your_mailjet_api_key
MAILJET_SECRET_KEY=your_mailjet_secret_key

# Development Settings
NODE_ENV=development
PORT=8080
```

3. **Backend Setup**
```bash
# Install Python dependencies
pip install -r requirements.txt
```

4. **Frontend Setup**
```bash
cd frontend
npm install
npm run build
cd ..
```

5. **Run the Application**
```bash
python main.py
```

Visit `http://localhost:8080` to access the application.

## 📁 Project Structure

```
Recipe-AI/
├── main.py                    # Application entry point with static file serving
├── backend/
│   ├── server.py             # FastAPI application with all endpoints
│   ├── models.py             # Pydantic request/response models
│   └── services/
│       ├── openai_service.py # OpenAI integration
│       └── walmart_service.py # Walmart API integration
├── frontend/
│   ├── src/
│   │   ├── components/       # React components
│   │   │   ├── LoginScreen.js
│   │   │   ├── DashboardScreen.js
│   │   │   ├── RecipeGeneratorScreen.js
│   │   │   ├── WeeklyPlanningScreen.js
│   │   │   ├── StarbucksGeneratorScreen.js
│   │   │   └── RecipeDetailScreen.js
│   │   ├── context/          # Context providers
│   │   └── App.js           # Main App with routing
│   └── build/               # Production build
├── .env                     # Environment variables
├── requirements.txt         # Python dependencies
├── Dockerfile              # Container configuration
└── README.md
```

## 🔧 API Endpoints

### Authentication
- `POST /api/auth/register` - User registration with email verification
- `POST /api/auth/login` - User login with MongoDB validation
- `POST /api/auth/verify` - Email verification
- `POST /api/auth/resend-verification` - Resend verification email

### Recipe Management
- `POST /api/recipes/generate` - Generate new recipe with OpenAI
- `GET /api/recipes/history/{user_id}` - Get user's recipe history
- `GET /api/recipes/{recipe_id}/detail` - Get detailed recipe information
- `DELETE /api/recipes/{recipe_id}` - Delete recipe

### Weekly Meal Planning
- `POST /api/weekly-recipes/generate` - Generate complete weekly meal plan
- `GET /api/weekly-recipes/current/{user_id}` - Get current weekly plan

### Starbucks Secret Menu
- `POST /api/generate-starbucks-drink` - Generate unique Starbucks drinks
- `GET /api/curated-starbucks-recipes` - Get curated drink collection
- `GET /api/shared-recipes` - Get community shared recipes

### Smart Shopping (Walmart Integration)
- `GET /api/recipes/{recipe_id}/cart-options` - Get Walmart products for recipe ingredients
- Real-time product search and pricing
- Automatic cart URL generation

### User Management
- `GET /api/user/dashboard/{user_id}` - Get comprehensive dashboard data
- `POST /api/user/preferences` - Save user dietary preferences
- `GET /api/user/trial-status/{user_id}` - Get trial and subscription status

## 🌟 Key Features Explained

### AI Recipe Generation
- Uses OpenAI GPT models for creative recipe creation
- Supports dietary restrictions and preferences
- Generates nutritional information and cooking tips
- Estimates ingredient costs

### Walmart Smart Shopping
- Real-time product matching for recipe ingredients
- Price comparison and best value selection
- Automatic cart creation with direct Walmart links
- Support for pickup and delivery options

### Starbucks Secret Menu Generator
- AI-powered drink creation with customizable parameters
- Community sharing and rating system
- Curated collections from drink experts
- Detailed ordering instructions for baristas

### Weekly Meal Planning
- Balanced nutrition across the week
- Variety in cuisines and meal types
- Shopping list generation
- Cost optimization

## 🌍 Deployment

### Local Development
```bash
# Start development server
python main.py

# Frontend development (separate terminal)
cd frontend
npm start  # Runs on port 3000
```

### Google Cloud Run Deployment

1. **Prepare for deployment**
```bash
# Build frontend
cd frontend && npm run build && cd ..
```

2. **Deploy to Cloud Run**
```bash
gcloud run deploy buildyoursmartcart \
  --source . \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars NODE_ENV=production
```

3. **Set environment variables**
```bash
gcloud run services update buildyoursmartcart \
  --set-env-vars OPENAI_API_KEY=your_key,MONGO_URL=your_mongo_url,WALMART_CONSUMER_ID=your_id
```

## 🔐 Authentication & Security

- **Secure Password Hashing**: Uses bcrypt for password security
- **Email Verification**: Required for account activation
- **User Session Management**: Secure user context and state
- **Environment Variable Protection**: Sensitive data stored securely
- **CORS Configuration**: Proper cross-origin request handling

## 🛒 Walmart Integration Details

The Walmart integration provides:
- **Product Search**: Real-time ingredient-to-product matching
- **Price Comparison**: Best value product selection
- **Availability Check**: Stock status and store availability
- **Cart Generation**: Direct links to Walmart cart with selected items
- **Multiple Options**: 3 product alternatives per ingredient

## ☕ Starbucks Features

- **Drink Type Selection**: Frappuccinos, Refreshers, Lattes, Lemonades
- **Flavor Inspiration**: Custom flavor combinations
- **Ordering Scripts**: Detailed instructions for baristas
- **Community Sharing**: User-generated drink recipes
- **Curated Collections**: Expert-selected favorites

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🔗 Links

- [Live Demo](https://buildyoursmartcart.com)
- [API Documentation](https://buildyoursmartcart.com/api/docs)
- [Issue Tracker](https://github.com/yourusername/Recipe-AI/issues)

## 📧 Support

For support, email support@buildyoursmartcart.com

## 🚀 Recent Updates

- ✅ **Fixed Authentication**: MongoDB-based user system working
- ✅ **Starbucks Generator**: AI-powered drink generation operational
- ✅ **Walmart Integration**: Real-time product matching and cart creation
- ✅ **Recipe Management**: Full CRUD operations with detailed views
- ✅ **Weekly Planning**: Complete meal planning with shopping integration
- ✅ **Mobile Responsive**: Optimized for all devices

---

Built with ❤️ using React, FastAPI, MongoDB, and OpenAI • **BuildYourSmartCart.com**