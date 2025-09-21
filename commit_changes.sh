#!/bin/bash

# Git commit script for BuildYourSmartCart.com updates
# This script will commit all recent changes with a comprehensive commit message

echo "🚀 Committing BuildYourSmartCart.com updates to git..."

# Navigate to project directory
cd /Users/alannunezsilva/Documents/Recipe-AI

# Add all changes
echo "📝 Adding all changes..."
git add .

# Create comprehensive commit message
COMMIT_MESSAGE="🎉 Major BuildYourSmartCart.com Updates - Full Stack Recipe & Starbucks Platform

✅ **Authentication System**
- Fixed MongoDB-based user registration and login
- Secure bcrypt password hashing
- Email verification system
- User session management

✅ **AI Recipe Generation** 
- OpenAI GPT integration for personalized recipes
- Recipe history and management
- Detailed recipe views with ingredients & instructions
- Recipe deletion functionality

✅ **Starbucks Secret Menu Generator**
- AI-powered unique drink creation
- Customizable drink types (Frappuccino, Refresher, Lemonade, etc.)
- Flavor inspiration input
- Detailed ordering scripts for baristas
- Separate collection for Starbucks drinks

✅ **Weekly Meal Planning**
- Complete 7-day meal plan generation
- Budget-conscious planning
- Shopping list integration
- Family size customization

✅ **Walmart Shopping Integration**
- Real-time product search via Walmart Open API
- Ingredient-to-product matching
- Price comparison and savings calculation
- Automatic cart generation
- RSA signature authentication

✅ **Frontend Enhancements**
- React 18 with modern hooks and context
- Tailwind CSS responsive design
- Animated UI components
- Mobile-optimized interface
- Beautiful gradient designs

✅ **Backend Infrastructure**
- FastAPI with async/await support
- MongoDB with Motor async driver
- Proper CORS configuration
- Error handling and logging
- ObjectId serialization fixes

✅ **Database Schema**
- Users collection with verification
- Recipes collection for food recipes
- Starbucks_recipes collection for drinks
- Weekly_recipes collection for meal plans
- Proper indexing and relationships

✅ **Security & Performance**
- Environment variable protection
- Secure API key management
- Request validation with Pydantic
- Async database operations
- Proper error responses

🔧 **Technical Improvements**
- Fixed JSON serialization issues
- Enhanced error logging
- Improved API response formats
- Better ingredient search algorithms
- Walmart API signature generation

📱 **User Experience**
- Intuitive navigation between screens
- Real-time feedback and notifications
- Smooth loading states
- Professional error handling
- Clean data separation

🌐 **Deployment Ready**
- Google Cloud Run compatibility
- Docker containerization support
- Production environment configuration
- Health check endpoints
- API documentation

This commit represents a fully functional AI-powered recipe and meal planning platform with Walmart integration and Starbucks drink generation capabilities."

# Commit with the comprehensive message
echo "💾 Committing changes..."
git commit -m "$COMMIT_MESSAGE"

# Check if we have a remote repository
if git remote -v | grep -q origin; then
    echo "🌐 Pushing to remote repository..."
    git push origin main 2>/dev/null || git push origin master 2>/dev/null || echo "⚠️ Push failed - please check remote repository"
else
    echo "ℹ️ No remote repository configured. Changes committed locally."
fi

echo "✅ Git commit completed!"
echo ""
echo "📊 Recent commits:"
git log --oneline -3

echo ""
echo "🔍 Repository status:"
git status --short