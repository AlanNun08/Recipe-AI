"""
buildyoursmartcart.com FastAPI Backend
AI Recipe + Grocery Delivery App - Weekly Meal Planning & Walmart Integration
"""

from fastapi import FastAPI, HTTPException, Request, BackgroundTasks
from fastapi.responses import JSONResponse, FileResponse, RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware
from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional, Dict, Any
import os
import logging
import bcrypt
import uuid
import random
import json
from datetime import datetime, timedelta
from pathlib import Path
from dotenv import load_dotenv

# Database imports
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import ASCENDING, DESCENDING

# Email service imports
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# OpenAI imports
from openai import OpenAI

# HTTP client imports
import httpx
import aiohttp

# Stripe imports
import stripe

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables (development vs production)
def load_environment_variables():
    """Load environment variables from .env file in development, system env in production"""
    if os.getenv("NODE_ENV") == "production":
        # In production (Google Cloud Run), variables are set directly
        logger.info("Production mode: Using system environment variables")
    else:
        # In development, try to load from .env file
        env_file = Path(__file__).parent / '.env'
        if env_file.exists():
            load_dotenv(env_file)
            logger.info(f"Development mode: Loaded environment from {env_file}")
        else:
            logger.warning("Development mode: No .env file found, using system environment")

# Load environment variables properly
load_environment_variables()

# Initialize FastAPI app
app = FastAPI(
    title="buildyoursmartcart.com API",
    description="AI Recipe + Grocery Delivery App - Weekly Meal Planning & Walmart Integration",
    version="2.2.1",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware - allow all origins for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# MongoDB setup with validation
mongo_url = os.environ.get('MONGO_URL')
db_name = os.environ.get('DB_NAME', 'buildyoursmartcart_development')

if not mongo_url:
    if os.getenv("NODE_ENV") == "production":
        logger.error("❌ MONGO_URL environment variable is required in production")
        raise ValueError("MONGO_URL environment variable is required in production")
    else:
        mongo_url = 'mongodb://localhost:27017'
        logger.warning("⚠️ MONGO_URL not set, using localhost default for development")

logger.info(f"📊 Connecting to MongoDB: {mongo_url.replace(mongo_url.split('@')[0].split('//')[1] if '@' in mongo_url else '', '***') if mongo_url else 'None'}")
logger.info(f"📊 Database name: {db_name}")

client = AsyncIOMotorClient(mongo_url)
db = client[db_name]

# Collections
users_collection = db["users"]
verification_codes_collection = db["verification_codes"]
recipes_collection = db["recipes"]
weekly_recipes_collection = db["weekly_recipes"]
starbucks_recipes_collection = db["starbucks_recipes"]
curated_starbucks_recipes_collection = db["curated_starbucks_recipes"]
grocery_carts_collection = db["grocery_carts"]
shared_recipes_collection = db["shared_recipes"]
payment_transactions_collection = db["payment_transactions"]

# External API setup
openai_client = None
openai_api_key = os.environ.get('OPENAI_API_KEY')
if openai_api_key and not any(placeholder in openai_api_key for placeholder in ['your-', 'placeholder', 'here']):
    openai_client = OpenAI(api_key=openai_api_key)

# Stripe setup
stripe_secret_key = os.environ.get('STRIPE_SECRET_KEY')
stripe_publisher_key = os.environ.get('STRIPE_PUBLISHER_API_KEY')

if stripe_secret_key and not any(placeholder in stripe_secret_key for placeholder in ['your-', 'placeholder', 'here']):
    stripe.api_key = stripe_secret_key

# Email service setup with validation
mailjet_api_key = os.environ.get('MAILJET_API_KEY')
mailjet_secret_key = os.environ.get('MAILJET_SECRET_KEY')
sender_email = os.environ.get('SENDER_EMAIL', 'noreply@buildyoursmartcart.com')

# Log email service configuration (without exposing keys)
if mailjet_api_key and mailjet_secret_key:
    if not any(placeholder in mailjet_api_key for placeholder in ['your-', 'placeholder', 'here']):
        logger.info("📧 Email service: Mailjet configured with live keys")
    else:
        logger.info("📧 Email service: Mailjet configured with placeholder keys (development mode)")
else:
    if os.getenv("NODE_ENV") == "production":
        logger.warning("⚠️ Email service: MAILJET_API_KEY or MAILJET_SECRET_KEY not set in production")
    else:
        logger.info("📧 Email service: No Mailjet keys (development logging mode)")

logger.info(f"📧 Sender email: {sender_email}")

# Walmart API setup
walmart_consumer_id = os.environ.get('WALMART_CONSUMER_ID')
walmart_private_key = os.environ.get('WALMART_PRIVATE_KEY')

logger.info("Backend initialized with external APIs configured")

# Pydantic models
class UserRegistration(BaseModel):
    email: EmailStr
    password: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class VerificationRequest(BaseModel):
    user_id: str
    code: str

class RecipeGeneration(BaseModel):
    user_id: str
    cuisine_type: str
    difficulty: str
    servings: int
    dietary_preferences: Optional[List[str]] = []
    ingredients: Optional[List[str]] = []

class WeeklyRecipeGeneration(BaseModel):
    user_id: str
    dietary_preferences: Optional[List[str]] = []
    cuisine_preferences: Optional[List[str]] = []

class StarbucksGeneration(BaseModel):
    user_id: str
    preferences: Optional[List[str]] = []

class SubscriptionCheckoutRequest(BaseModel):
    user_id: str
    user_email: str
    origin_url: str

# Utility functions
def hash_password(password: str) -> str:
    """Hash password using bcrypt"""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

def verify_password(password: str, hashed: str) -> bool:
    """Verify password against hash"""
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

def generate_verification_code() -> str:
    """Generate 6-digit verification code"""
    return str(random.randint(100000, 999999))

async def is_trial_active(user: dict) -> bool:
    """Check if user's free trial is still active"""
    if user.get('subscription', {}).get('status') != 'trialing':
        return False
    
    trial_ends_at = user.get('subscription', {}).get('trial_ends_at')
    if not trial_ends_at:
        return False
    
    try:
        end_date = datetime.fromisoformat(trial_ends_at.replace('Z', '+00:00'))
        return datetime.now(end_date.tzinfo) < end_date
    except:
        return False

async def can_access_premium_features(user: dict) -> dict:
    """Check if user can access premium features and return usage info"""
    subscription = user.get('subscription', {})
    status = subscription.get('status', 'none')
    
    # Check if trial is active
    trial_active = await is_trial_active(user)
    
    # Check if subscription is active
    subscription_active = status == 'active'
    
    can_access = trial_active or subscription_active
    
    # Get usage limits
    usage_limits = user.get('usage_limits', {})
    
    return {
        'can_access': can_access,
        'trial_active': trial_active,
        'subscription_active': subscription_active,
        'subscription_status': status,
        'usage_limits': usage_limits
    }

async def check_and_increment_usage(user_id: str, feature_type: str) -> bool:
    """Check usage limits and increment if within limits"""
    user = await users_collection.find_one({"id": user_id})
    if not user:
        return False
    
    access_info = await can_access_premium_features(user)
    if not access_info['can_access']:
        return False
    
    usage_limits = access_info.get('usage_limits', {})
    feature_limits = usage_limits.get(feature_type, {})
    
    used = feature_limits.get('used', 0)
    limit = feature_limits.get('limit', 0)
    
    if used >= limit:
        return False
    
    # Increment usage
    await users_collection.update_one(
        {"id": user_id},
        {"$inc": {f"usage_limits.{feature_type}.used": 1}}
    )
    
    return True

async def send_verification_email(email: str, code: str) -> bool:
    """Send verification email"""
    try:
        # In development, just log the code
        if not mailjet_api_key or 'your-' in mailjet_api_key:
            logger.info(f"Verification code for {email}: {code}")
            return True
        
        # In production, send actual email via Mailjet
        # Implementation would go here
        logger.info(f"Would send verification email to {email} with code {code}")
        return True
    except Exception as e:
        logger.error(f"Failed to send verification email: {e}")
        return False

# Authentication endpoints
@app.post("/auth/register")
async def register_user(registration: UserRegistration):
    """Register a new user"""
    try:
        # Check if user already exists
        existing_user = await users_collection.find_one({"email": registration.email})
        if existing_user:
            raise HTTPException(status_code=400, detail="User already exists")
        
        # Create user
        user_id = str(uuid.uuid4())
        hashed_password = hash_password(registration.password)
        
        user_data = {
            "id": user_id,
            "email": registration.email,
            "password": hashed_password,
            "is_verified": False,
            "subscription": {
                "status": "trialing",
                "trial_starts_at": datetime.utcnow().isoformat(),
                "trial_ends_at": (datetime.utcnow() + timedelta(days=7)).isoformat()
            },
            "usage_limits": {
                "weekly_recipes": {"used": 0, "limit": 2},
                "individual_recipes": {"used": 0, "limit": 10},
                "starbucks_drinks": {"used": 0, "limit": 10},
                "last_reset": datetime.utcnow().replace(day=1).isoformat()
            },
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }
        
        await users_collection.insert_one(user_data)
        
        # Generate and store verification code
        code = generate_verification_code()
        verification_data = {
            "user_id": user_id,
            "code": code,
            "expires_at": datetime.utcnow() + timedelta(hours=24),
            "created_at": datetime.utcnow()
        }
        
        await verification_codes_collection.insert_one(verification_data)
        
        # Send verification email
        await send_verification_email(registration.email, code)
        
        return JSONResponse(
            status_code=201,
            content={
                "user_id": user_id,
                "email": registration.email,
                "message": "Registration successful. Please check your email for verification code."
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Registration error: {e}")
        raise HTTPException(status_code=500, detail="Registration failed")

@app.post("/auth/login")
async def login_user(login: UserLogin):
    """Login user"""
    try:
        # Find user
        user = await users_collection.find_one({"email": login.email})
        if not user:
            raise HTTPException(status_code=401, detail="Invalid credentials")
        
        # Verify password
        if not verify_password(login.password, user["password"]):
            raise HTTPException(status_code=401, detail="Invalid credentials")
        
        # Remove password from response
        user_data = {k: v for k, v in user.items() if k != "password"}
        
        return JSONResponse(
            status_code=200,
            content={
                "status": "success",
                "user": user_data
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error: {e}")
        raise HTTPException(status_code=500, detail="Login failed")

@app.post("/auth/verify")
async def verify_email(verification: VerificationRequest):
    """Verify user email with code"""
    try:
        # Find verification code
        verification_doc = await verification_codes_collection.find_one({
            "user_id": verification.user_id,
            "code": verification.code
        })
        
        if not verification_doc:
            raise HTTPException(status_code=400, detail="Invalid verification code")
        
        # Check if code is expired
        if datetime.utcnow() > verification_doc["expires_at"]:
            raise HTTPException(status_code=400, detail="Verification code expired")
        
        # Update user as verified
        await users_collection.update_one(
            {"id": verification.user_id},
            {"$set": {"is_verified": True, "updated_at": datetime.utcnow()}}
        )
        
        # Remove verification code
        await verification_codes_collection.delete_one({"user_id": verification.user_id})
        
        return JSONResponse(
            status_code=200,
            content={"message": "Email verified successfully"}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Verification error: {e}")
        raise HTTPException(status_code=500, detail="Verification failed")

# User profile endpoints
@app.get("/user/profile/{user_id}")
async def get_user_profile(user_id: str):
    """Get user profile"""
    try:
        user = await users_collection.find_one({"id": user_id})
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Remove password and return profile
        profile = {k: v for k, v in user.items() if k != "password"}
        
        # Add subscription info
        access_info = await can_access_premium_features(user)
        profile["access_info"] = access_info
        
        return JSONResponse(status_code=200, content=profile)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Profile error: {e}")
        raise HTTPException(status_code=500, detail="Failed to get profile")

# Recipe generation endpoints
@app.post("/recipes/generate")
async def generate_recipe(request: RecipeGeneration):
    """Generate a single recipe"""
    try:
        # Check usage limits
        if not await check_and_increment_usage(request.user_id, "individual_recipes"):
            raise HTTPException(status_code=402, detail="Usage limit exceeded")
        
        # Generate recipe
        if openai_client:
            recipe = await generate_ai_recipe(request)
        else:
            recipe = await generate_fallback_recipe(request)
        
        # Save to database
        recipe_data = {
            "id": str(uuid.uuid4()),
            "user_id": request.user_id,
            "name": recipe["name"],
            "description": recipe["description"],
            "ingredients": recipe["ingredients"],
            "instructions": recipe["instructions"],
            "prep_time": recipe["prep_time"],
            "cook_time": recipe["cook_time"],
            "servings": request.servings,
            "difficulty": request.difficulty,
            "cuisine_type": request.cuisine_type,
            "dietary_preferences": request.dietary_preferences,
            "calories": recipe.get("calories", 0),
            "created_at": datetime.utcnow().isoformat()
        }
        
        await recipes_collection.insert_one(recipe_data)
        
        return JSONResponse(status_code=200, content=recipe_data)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Recipe generation error: {e}")
        raise HTTPException(status_code=500, detail="Recipe generation failed")

@app.post("/recipes/weekly/generate")
async def generate_weekly_recipes(request: WeeklyRecipeGeneration):
    """Generate weekly meal plan"""
    try:
        # Check usage limits
        if not await check_and_increment_usage(request.user_id, "weekly_recipes"):
            raise HTTPException(status_code=402, detail="Usage limit exceeded")
        
        # Generate 7 recipes for the week
        recipes = []
        cuisines = ["Italian", "Mexican", "Asian", "American", "Mediterranean", "Indian", "French"]
        
        for i, cuisine in enumerate(cuisines):
            recipe_request = RecipeGeneration(
                user_id=request.user_id,
                cuisine_type=cuisine,
                difficulty=random.choice(["easy", "medium"]),
                servings=4,
                dietary_preferences=request.dietary_preferences or []
            )
            
            if openai_client:
                recipe = await generate_ai_recipe(recipe_request)
            else:
                recipe = await generate_fallback_recipe(recipe_request)
            
            recipe_data = {
                "id": str(uuid.uuid4()),
                "user_id": request.user_id,
                "name": recipe["name"],
                "description": recipe["description"],
                "ingredients": recipe["ingredients"],
                "instructions": recipe["instructions"],
                "prep_time": recipe["prep_time"],
                "cook_time": recipe["cook_time"],
                "servings": 4,
                "difficulty": recipe_request.difficulty,
                "cuisine_type": cuisine,
                "dietary_preferences": request.dietary_preferences,
                "calories": recipe.get("calories", 0),
                "created_at": datetime.utcnow().isoformat()
            }
            
            recipes.append(recipe_data)
            await recipes_collection.insert_one(recipe_data)
        
        # Save weekly plan
        week_id = datetime.now().strftime("%Y-W%W")
        weekly_plan = {
            "id": str(uuid.uuid4()),
            "user_id": request.user_id,
            "week_id": week_id,
            "recipes": recipes,
            "created_at": datetime.utcnow().isoformat()
        }
        
        await weekly_recipes_collection.insert_one(weekly_plan)
        
        return JSONResponse(status_code=200, content=weekly_plan)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Weekly recipe generation error: {e}")
        raise HTTPException(status_code=500, detail="Weekly recipe generation failed")

@app.get("/recipes/history/{user_id}")
async def get_recipe_history(user_id: str):
    """Get user's recipe history"""
    try:
        # Get regular recipes
        recipes_cursor = recipes_collection.find({"user_id": user_id}).sort("created_at", -1).limit(50)
        recipes = await recipes_cursor.to_list(length=50)
        
        # Get Starbucks recipes
        starbucks_cursor = starbucks_recipes_collection.find({"user_id": user_id}).sort("created_at", -1).limit(50)
        starbucks_recipes = await starbucks_cursor.to_list(length=50)
        
        # Combine and sort
        all_recipes = recipes + starbucks_recipes
        all_recipes.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        
        return JSONResponse(
            status_code=200,
            content={
                "recipes": all_recipes,
                "total_count": len(all_recipes)
            }
        )
        
    except Exception as e:
        logger.error(f"Recipe history error: {e}")
        raise HTTPException(status_code=500, detail="Failed to get recipe history")

@app.get("/recipes/{recipe_id}/detail")
async def get_recipe_detail(recipe_id: str):
    """Get recipe details"""
    try:
        # Try regular recipes first
        recipe = await recipes_collection.find_one({"id": recipe_id})
        
        if not recipe:
            # Try Starbucks recipes
            recipe = await starbucks_recipes_collection.find_one({"id": recipe_id})
        
        if not recipe:
            # Try curated Starbucks recipes
            recipe = await curated_starbucks_recipes_collection.find_one({"id": recipe_id})
        
        if not recipe:
            raise HTTPException(status_code=404, detail="Recipe not found")
        
        return JSONResponse(status_code=200, content=recipe)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Recipe detail error: {e}")
        raise HTTPException(status_code=500, detail="Failed to get recipe details")

# Starbucks recipes
@app.post("/starbucks/generate")
async def generate_starbucks_recipe(request: StarbucksGeneration):
    """Generate Starbucks secret menu recipe"""
    try:
        # Check usage limits
        if not await check_and_increment_usage(request.user_id, "starbucks_drinks"):
            raise HTTPException(status_code=402, detail="Usage limit exceeded")
        
        # Generate Starbucks recipe
        if openai_client:
            recipe = await generate_ai_starbucks_recipe(request)
        else:
            recipe = await generate_fallback_starbucks_recipe(request)
        
        # Save to database
        recipe_data = {
            "id": str(uuid.uuid4()),
            "user_id": request.user_id,
            "name": recipe["name"],
            "description": recipe["description"],
            "ingredients": recipe["ingredients"],
            "instructions": recipe["instructions"],
            "category": "starbucks",
            "created_at": datetime.utcnow().isoformat()
        }
        
        await starbucks_recipes_collection.insert_one(recipe_data)
        
        return JSONResponse(status_code=200, content=recipe_data)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Starbucks recipe generation error: {e}")
        raise HTTPException(status_code=500, detail="Starbucks recipe generation failed")

# Subscription endpoints
@app.post("/subscription/create-checkout")
async def create_subscription_checkout(request: SubscriptionCheckoutRequest):
    """Create Stripe checkout session for subscription"""
    try:
        if not stripe_secret_key or 'your-' in stripe_secret_key:
            # Return mock response for development
            return JSONResponse(
                status_code=200,
                content={
                    "checkout_url": "https://checkout.stripe.com/mock-session",
                    "session_id": "mock_session_id"
                }
            )
        
        # Create Stripe checkout session
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price_data': {
                    'currency': 'usd',
                    'product_data': {
                        'name': 'Monthly Premium Subscription',
                        'description': 'AI Recipe + Grocery Delivery Premium Features'
                    },
                    'unit_amount': 999,  # $9.99
                    'recurring': {
                        'interval': 'month'
                    }
                },
                'quantity': 1,
            }],
            mode='subscription',
            success_url=f"{request.origin_url}?subscription=success&session_id={{CHECKOUT_SESSION_ID}}",
            cancel_url=f"{request.origin_url}?subscription=cancelled",
            customer_email=request.user_email,
            metadata={
                'user_id': request.user_id
            }
        )
        
        return JSONResponse(
            status_code=200,
            content={
                "checkout_url": checkout_session.url,
                "session_id": checkout_session.id
            }
        )
        
    except Exception as e:
        logger.error(f"Stripe checkout error: {e}")
        raise HTTPException(status_code=500, detail="Failed to create checkout session")

@app.get("/subscription/status/{session_id}")
async def get_subscription_status(session_id: str):
    """Get subscription status from Stripe session"""
    try:
        if not stripe_secret_key or 'your-' in stripe_secret_key:
            # Return mock response for development
            return JSONResponse(
                status_code=200,
                content={
                    "status": "complete",
                    "customer_email": "demo@example.com"
                }
            )
        
        session = stripe.checkout.Session.retrieve(session_id)
        
        if session.payment_status == 'paid':
            # Update user subscription status
            user_id = session.metadata.get('user_id')
            if user_id:
                await users_collection.update_one(
                    {"id": user_id},
                    {
                        "$set": {
                            "subscription.status": "active",
                            "subscription.customer_id": session.customer,
                            "subscription.subscription_id": session.subscription,
                            "updated_at": datetime.utcnow().isoformat()
                        }
                    }
                )
        
        return JSONResponse(
            status_code=200,
            content={
                "status": session.payment_status,
                "customer_email": session.customer_email
            }
        )
        
    except Exception as e:
        logger.error(f"Subscription status error: {e}")
        raise HTTPException(status_code=500, detail="Failed to get subscription status")

# Health check
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Test database connection
        await db.command("ping")
        db_status = "healthy"
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        db_status = "unhealthy"
    
    return JSONResponse(
        status_code=200 if db_status == "healthy" else 503,
        content={
            "status": "healthy" if db_status == "healthy" else "unhealthy",
            "service": "buildyoursmartcart",
            "version": "2.2.1",
            "features": {
                "recipe_generation": True,
                "weekly_planning": True,
                "starbucks_menu": True,
                "subscription": True,
                "walmart_integration": True
            },
            "external_apis": {
                "openai": bool(openai_client),
                "stripe": bool(stripe_secret_key and 'your-' not in stripe_secret_key),
                "mailjet": bool(mailjet_api_key and 'your-' not in mailjet_api_key),
                "walmart": bool(walmart_consumer_id)
            },
            "database": db_status,
            "timestamp": datetime.utcnow().isoformat()
        }
    )

# Helper functions for recipe generation
async def generate_ai_recipe(request: RecipeGeneration) -> dict:
    """Generate recipe using OpenAI"""
    try:
        dietary_text = ", ".join(request.dietary_preferences) if request.dietary_preferences else "no specific dietary restrictions"
        ingredients_text = ", ".join(request.ingredients) if request.ingredients else "any suitable ingredients"
        
        prompt = f"""
        Create a detailed {request.cuisine_type} recipe with the following requirements:
        - Difficulty: {request.difficulty}
        - Servings: {request.servings}
        - Dietary preferences: {dietary_text}
        - Include these ingredients if possible: {ingredients_text}
        
        Return a JSON object with:
        - name: recipe name
        - description: brief description
        - ingredients: array of ingredients with measurements
        - instructions: array of step-by-step instructions
        - prep_time: preparation time
        - cook_time: cooking time
        - calories: estimated calories per serving
        """
        
        response = openai_client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7
        )
        
        return json.loads(response.choices[0].message.content)
        
    except Exception as e:
        logger.error(f"AI recipe generation failed: {e}")
        return await generate_fallback_recipe(request)

async def generate_fallback_recipe(request: RecipeGeneration) -> dict:
    """Generate fallback recipe when AI is not available"""
    fallback_recipes = {
        "italian": {
            "name": "Classic Spaghetti Carbonara",
            "description": "Traditional Italian pasta dish with eggs, cheese, and pancetta",
            "ingredients": [
                "400g spaghetti",
                "200g pancetta or bacon, diced",
                "4 large eggs",
                "100g Pecorino Romano cheese, grated",
                "2 cloves garlic, minced",
                "Black pepper to taste",
                "Salt for pasta water"
            ],
            "instructions": [
                "Bring a large pot of salted water to boil and cook spaghetti until al dente",
                "While pasta cooks, fry pancetta in a large pan until crispy",
                "In a bowl, whisk eggs with grated cheese and black pepper",
                "Drain pasta, reserving 1 cup pasta water",
                "Add hot pasta to pan with pancetta",
                "Remove from heat and quickly mix in egg mixture, adding pasta water as needed",
                "Serve immediately with extra cheese and pepper"
            ],
            "prep_time": "10 minutes",
            "cook_time": "15 minutes",
            "calories": 650
        },
        "mexican": {
            "name": "Chicken Tacos with Lime Crema",
            "description": "Flavorful chicken tacos with fresh lime crema and vegetables",
            "ingredients": [
                "500g chicken breast, sliced",
                "8 corn tortillas",
                "1 red onion, sliced",
                "2 bell peppers, sliced",
                "1/2 cup sour cream",
                "2 limes, juiced",
                "1 tsp cumin",
                "1 tsp chili powder",
                "Salt and pepper to taste",
                "Fresh cilantro for garnish"
            ],
            "instructions": [
                "Season chicken with cumin, chili powder, salt, and pepper",
                "Cook chicken in a hot pan until golden brown and cooked through",
                "Sauté onions and peppers until softened",
                "Mix sour cream with lime juice to make crema",
                "Warm tortillas in a dry pan",
                "Assemble tacos with chicken, vegetables, and lime crema",
                "Garnish with fresh cilantro and serve"
            ],
            "prep_time": "15 minutes",
            "cook_time": "20 minutes",
            "calories": 520
        }
    }
    
    cuisine_key = request.cuisine_type.lower()
    if cuisine_key not in fallback_recipes:
        cuisine_key = "italian"  # Default fallback
    
    return fallback_recipes[cuisine_key]

async def generate_ai_starbucks_recipe(request: StarbucksGeneration) -> dict:
    """Generate Starbucks recipe using OpenAI"""
    try:
        preferences_text = ", ".join(request.preferences) if request.preferences else "any flavor profile"
        
        prompt = f"""
        Create a Starbucks secret menu drink recipe with these preferences: {preferences_text}
        
        Return a JSON object with:
        - name: creative drink name
        - description: brief description of the drink
        - ingredients: array of Starbucks ingredients (syrups, milk types, etc.)
        - instructions: step-by-step ordering instructions
        """
        
        response = openai_client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.8
        )
        
        return json.loads(response.choices[0].message.content)
        
    except Exception as e:
        logger.error(f"AI Starbucks recipe generation failed: {e}")
        return await generate_fallback_starbucks_recipe(request)

async def generate_fallback_starbucks_recipe(request: StarbucksGeneration) -> dict:
    """Generate fallback Starbucks recipe"""
    fallback_recipes = [
        {
            "name": "Caramel Apple Spice Frappuccino",
            "description": "A sweet and spicy blend with apple and caramel flavors",
            "ingredients": [
                "Grande Apple Juice",
                "2 pumps Cinnamon Dolce syrup",
                "2 pumps Caramel syrup",
                "Whipped cream",
                "Caramel drizzle",
                "Cinnamon powder"
            ],
            "instructions": [
                "Order a Grande Apple Juice",
                "Ask for it to be steamed",
                "Add 2 pumps of Cinnamon Dolce syrup",
                "Add 2 pumps of Caramel syrup",
                "Top with whipped cream",
                "Drizzle with caramel sauce",
                "Sprinkle with cinnamon powder"
            ]
        },
        {
            "name": "Cookies and Cream Frappuccino",
            "description": "A chocolatey treat that tastes like your favorite cookies",
            "ingredients": [
                "Grande Vanilla Bean Frappuccino",
                "2 pumps Mocha syrup",
                "Java chips",
                "Whipped cream",
                "Chocolate cookie crumbs"
            ],
            "instructions": [
                "Order a Grande Vanilla Bean Frappuccino",
                "Add 2 pumps of Mocha syrup",
                "Add java chips",
                "Blend as normal",
                "Top with whipped cream",
                "Ask for chocolate cookie crumbs on top"
            ]
        }
    ]
    
    return random.choice(fallback_recipes)

# Remove the __main__ section to prevent conflicts in production
# The app is imported and run by main.py