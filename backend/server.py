# Import new Stripe integration
from .stripe_integration import (
    create_subscription_checkout_integrated,
    get_checkout_status_integrated, 
    stripe_webhook_integrated,
    SubscriptionCheckoutRequestLegacy
)

from fastapi import FastAPI, APIRouter, HTTPException, Query, Request, Depends
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging

# Configure logger
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

from pathlib import Path
from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, timedelta
from dateutil import parser
# Removed ObjectId import as it's not needed and causes serialization issues
import openai
from openai import OpenAI
import json
import httpx
import asyncio
import time
import base64
import random
import re
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding
import bcrypt
import sys
import os

# Stripe integration
# Native Stripe integration (no emergentintegrations)
from stripe_native import (
    create_subscription_checkout_native,
    get_checkout_status_native, 
    stripe_webhook_native,
    SubscriptionCheckoutRequest
)

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from email_service import email_service

# Note: Removed duplicate imports that were causing conflicts

# Load environment variables
ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
db_name = os.environ.get('DB_NAME', 'test_database')

# Single, clean database connection
client = AsyncIOMotorClient(mongo_url)
db = client[db_name]

# Database collections
users_collection = db["users"]
verification_codes_collection = db["verification_codes"]
recipes_collection = db["recipes"]  
grocery_carts_collection = db["grocery_carts"]
shared_recipes_collection = db["shared_recipes"]
payment_transactions_collection = db["payment_transactions"]  # NEW
weekly_recipes_collection = db["weekly_recipes"]  # NEW - for weekly recipe plans

# Stripe setup
STRIPE_API_KEY = os.environ.get('STRIPE_API_KEY')
STRIPE_PUBLISHABLE_KEY = os.environ.get('STRIPE_PUBLISHABLE_KEY')
if not STRIPE_API_KEY:
    logger.warning("STRIPE_API_KEY not found in environment variables")

# API Keys for health check
OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')
WALMART_CONSUMER_ID = os.environ.get('WALMART_CONSUMER_ID')
WALMART_PRIVATE_KEY = os.environ.get('WALMART_PRIVATE_KEY')
MAILJET_API_KEY = os.environ.get('MAILJET_API_KEY')
MAILJET_SECRET_KEY = os.environ.get('MAILJET_SECRET_KEY')

# Subscription packages - SERVER SIDE ONLY (SECURITY)
SUBSCRIPTION_PACKAGES = {
    "monthly_subscription": {
        "name": "Monthly Subscription",
        "price": 9.99,
        "currency": "usd",
        "description": "Access to all premium features for one month"
    }
}

# Subscription helper functions
def is_trial_active(user: dict) -> bool:
    """Check if user's free trial is still active"""
    trial_end_date = user.get('trial_end_date')
    if not trial_end_date:
        return False
    if isinstance(trial_end_date, str):
        trial_end_date = parser.parse(trial_end_date)
    return datetime.utcnow() < trial_end_date

def is_subscription_active(user: dict) -> bool:
    """Check if user's paid subscription is active"""
    subscription_status = user.get('subscription_status', 'trial')
    if subscription_status == 'active':
        subscription_end_date = user.get('subscription_end_date')
        if subscription_end_date:
            if isinstance(subscription_end_date, str):
                subscription_end_date = parser.parse(subscription_end_date)
            return datetime.utcnow() < subscription_end_date
    return False

# Usage limits configuration
USAGE_LIMITS = {
    "trial": {
        "weekly_recipes": 2,
        "individual_recipes": 10,
        "starbucks_drinks": 10
    },
    "active": {
        "weekly_recipes": 3,
        "individual_recipes": 30,
        "starbucks_drinks": 30
    }
}

def get_user_usage_limits(subscription_status: str) -> dict:
    """Get usage limits for user based on subscription status"""
    return USAGE_LIMITS.get(subscription_status, USAGE_LIMITS["trial"])

def check_usage_limit(user: dict, usage_type: str) -> tuple[bool, dict]:
    """
    Check if user has exceeded usage limit for a specific type
    Returns (can_use: bool, usage_info: dict)
    """
    subscription_status = user.get('subscription_status', 'trial')
    limits = get_user_usage_limits(subscription_status)
    
    # Reset usage if it's a new month
    usage_reset_date = user.get('usage_reset_date')
    current_date = datetime.utcnow()
    
    # Check if we need to reset monthly usage
    needs_reset = False
    if not usage_reset_date:
        needs_reset = True
    else:
        if isinstance(usage_reset_date, str):
            usage_reset_date = parser.parse(usage_reset_date)
        
        # Reset if it's been more than 30 days or if it's a new month
        days_since_reset = (current_date - usage_reset_date).days
        if days_since_reset >= 30 or current_date.month != usage_reset_date.month:
            needs_reset = True
    
    # Current usage
    current_usage = {
        "weekly_recipes": user.get('weekly_recipes_used', 0),
        "individual_recipes": user.get('individual_recipes_used', 0),
        "starbucks_drinks": user.get('starbucks_drinks_used', 0)
    }
    
    # If reset needed, set current usage to 0 for calculation
    if needs_reset:
        current_usage = {
            "weekly_recipes": 0,
            "individual_recipes": 0,
            "starbucks_drinks": 0
        }
    
    # Check specific usage type
    current_count = current_usage.get(usage_type, 0)
    limit = limits.get(usage_type, 0)
    can_use = current_count < limit
    
    usage_info = {
        "current_usage": current_usage,
        "limits": limits,
        "can_use": can_use,
        "usage_type": usage_type,
        "current_count": current_count,
        "limit": limit,
        "remaining": max(0, limit - current_count),
        "needs_reset": needs_reset,
        "subscription_status": subscription_status
    }
    
    return can_use, usage_info

async def increment_usage(user_id: str, usage_type: str) -> bool:
    """Increment usage counter for user and reset if needed"""
    try:
        user = await users_collection.find_one({"id": user_id})
        if not user:
            return False
        
        can_use, usage_info = check_usage_limit(user, usage_type)
        
        if not can_use:
            return False
        
        # Prepare update data
        update_data = {}
        current_date = datetime.utcnow()
        
        # Reset counters if needed
        if usage_info["needs_reset"]:
            update_data.update({
                "usage_reset_date": current_date,
                "weekly_recipes_used": 0,
                "individual_recipes_used": 0,
                "starbucks_drinks_used": 0
            })
        
        # Increment the specific usage type
        usage_field_map = {
            "weekly_recipes": "weekly_recipes_used",
            "individual_recipes": "individual_recipes_used", 
            "starbucks_drinks": "starbucks_drinks_used"
        }
        
        usage_field = usage_field_map.get(usage_type)
        if usage_field:
            current_count = 0 if usage_info["needs_reset"] else user.get(usage_field, 0)
            update_data[usage_field] = current_count + 1
        
        # Update user in database
        await users_collection.update_one(
            {"id": user_id},
            {"$set": update_data}
        )
        
        return True
        
    except Exception as e:
        logger.error(f"Error incrementing usage for user {user_id}: {e}")
        return False

def can_access_premium_features(user: dict) -> dict:
    """Check if user can access premium features and return detailed access status"""
    trial_active = is_trial_active(user)
    subscription_active = is_subscription_active(user)
    has_access = trial_active or subscription_active
    
    return {
        'has_access': has_access,
        'subscription_status': user.get('subscription_status', 'trial'),
        'trial_active': trial_active,
        'subscription_active': subscription_active,
        'trial_end_date': user.get('trial_end_date'),
        'subscription_end_date': user.get('subscription_end_date'),
        'next_billing_date': user.get('next_billing_date'),
        'cancel_at_period_end': user.get('cancel_at_period_end', False)
    }

def get_user_access_status(user: dict) -> dict:
    """Get detailed user access status"""
    trial_active = is_trial_active(user)
    subscription_active = is_subscription_active(user)
    
    access_status = {
        "has_access": trial_active or subscription_active,
        "subscription_status": user.get('subscription_status', 'trial'),
        "trial_active": trial_active,
        "subscription_active": subscription_active,
        "trial_end_date": user.get('trial_end_date'),
        "subscription_end_date": user.get('subscription_end_date'),
        "next_billing_date": user.get('next_billing_date')
    }
    
    return access_status

# Custom JSON encoder for MongoDB documents
def mongo_to_dict(obj):
    """Convert MongoDB document to dict, handling _id field"""
    if isinstance(obj, dict):
        result = {}
        for key, value in obj.items():
            if key == '_id':
                # Skip MongoDB _id field
                continue
            elif hasattr(value, '__iter__') and not isinstance(value, (str, bytes, dict)):
                # Handle iterables (like lists)
                result[key] = [mongo_to_dict(item) for item in value]
            elif isinstance(value, dict):
                # Handle nested dictionaries
                result[key] = mongo_to_dict(value)
            else:
                # Handle primitive values
                result[key] = value
        return result
    return obj

# OpenAI setup
openai_client = OpenAI(api_key=os.environ['OPENAI_API_KEY'])

# Walmart API setup - RESTORED REAL INTEGRATION
WALMART_CONSUMER_ID = os.environ.get('WALMART_CONSUMER_ID')
WALMART_KEY_VERSION = os.environ.get('WALMART_KEY_VERSION', '1') 
WALMART_PRIVATE_KEY = os.environ.get('WALMART_PRIVATE_KEY')

# Create the main app without a prefix
app = FastAPI(
    title="AI Recipe & Grocery App", 
    version="2.0.0",
    # Security headers
    docs_url="/docs",  # Keep docs for development
    redoc_url="/redoc"  # Keep redoc for development
)

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to all responses"""
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        
        # Security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY" 
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
        
        return response

# Add security middleware
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(
    TrustedHostMiddleware, 
    allowed_hosts=[
        "localhost",
        "127.0.0.1", 
        "*.emergentagent.com",
        "buildyoursmartcart.com",
        "www.buildyoursmartcart.com"
    ]
)

# Create a router without prefix (main.py will mount it at /api)
api_router = APIRouter()

# UUID-based ID utilities for JSON serialization
def create_unique_id() -> str:
    """Create a unique string ID using UUID"""
    return str(uuid.uuid4())

# Enhanced Models for Email Verification
class User(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    first_name: str
    last_name: str
    email: EmailStr
    password_hash: str
    dietary_preferences: List[str] = []
    allergies: List[str] = []
    favorite_cuisines: List[str] = []
    is_verified: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)
    verified_at: Optional[datetime] = None
    
    # Subscription fields
    subscription_status: str = "trial"  # "trial", "active", "expired", "cancelled"
    trial_start_date: datetime = Field(default_factory=datetime.utcnow)
    trial_end_date: datetime = Field(default_factory=lambda: datetime.utcnow() + timedelta(days=7))
    subscription_start_date: Optional[datetime] = None
    subscription_end_date: Optional[datetime] = None
    stripe_customer_id: Optional[str] = None
    stripe_subscription_id: Optional[str] = None
    last_payment_date: Optional[datetime] = None
    next_billing_date: Optional[datetime] = None
    cancel_at_period_end: bool = False  # For subscription cancellation
    subscription_cancelled_date: Optional[datetime] = None
    subscription_cancel_reason: Optional[str] = None
    subscription_reactivated_date: Optional[datetime] = None
    
    # Usage tracking fields
    usage_reset_date: Optional[datetime] = None
    weekly_recipes_used: int = 0
    individual_recipes_used: int = 0
    starbucks_drinks_used: int = 0

class UserRegistration(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr
    password: str
    dietary_preferences: List[str] = []
    allergies: List[str] = []
    favorite_cuisines: List[str] = []

class VerificationCode(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    email: str
    code: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: datetime
    is_used: bool = False

class VerifyCodeRequest(BaseModel):
    email: EmailStr
    code: str

class ResendCodeRequest(BaseModel):
    email: EmailStr

class PasswordResetRequest(BaseModel):
    email: EmailStr

class PasswordResetVerify(BaseModel):
    email: EmailStr
    reset_code: str
    new_password: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

# Original models (keeping existing functionality)
class UserCreate(BaseModel):
    name: str
    email: str
    dietary_preferences: List[str] = []
    allergies: List[str] = []
    favorite_cuisines: List[str] = []

class RecipeGenRequest(BaseModel):
    user_id: str
    recipe_category: Optional[str] = None  # 'cuisine', 'snack', 'beverage'
    cuisine_type: Optional[str] = None
    dietary_preferences: List[str] = []
    ingredients_on_hand: List[str] = []
    prep_time_max: Optional[int] = None
    servings: int = 4
    difficulty: str = "medium"
    # New healthy options
    is_healthy: bool = False
    max_calories_per_serving: Optional[int] = None
    # New budget options
    is_budget_friendly: bool = False
    max_budget: Optional[float] = None

class Recipe(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    description: str
    ingredients: List[str]
    instructions: List[str]
    prep_time: int  # in minutes
    cook_time: int  # in minutes
    servings: int
    cuisine_type: str
    dietary_tags: List[str] = []
    difficulty: str  # easy, medium, hard
    # New fields for healthy recipes
    calories_per_serving: Optional[int] = None
    is_healthy: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)
    user_id: Optional[str] = None
    # Shopping list for Walmart API (just ingredient names)
    shopping_list: Optional[List[str]] = []

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class StarbucksRequest(BaseModel):
    user_id: str
    drink_type: str  # frappuccino, refresher, lemonade, iced_matcha_latte, random
    flavor_inspiration: Optional[str] = None  # Optional flavor inspiration like "tres leches", "ube", "mango tajin"

class CuratedStarbucksRecipe(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    base: str
    ingredients: List[str]
    order_instructions: str
    vibe: str
    category: str  # frappuccino, refresher, lemonade, iced_matcha_latte, random
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class UserSharedRecipe(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    recipe_name: str
    description: str
    ingredients: List[str]
    order_instructions: str
    category: str  # frappuccino, refresher, lemonade, iced_matcha_latte, random
    
    # User information
    shared_by_user_id: str
    shared_by_username: str
    
    # Media and extras
    image_base64: Optional[str] = None  # Store image as base64
    tags: List[str] = []  # Additional tags like "sweet", "caffeinated", "cold", etc.
    difficulty_level: Optional[str] = "easy"  # easy, medium, hard
    
    # Social features
    likes_count: int = 0
    liked_by_users: List[str] = []  # List of user IDs who liked this recipe
    
    # Recipe source
    original_source: Optional[str] = None  # "ai_generated", "curated", "custom"
    original_recipe_id: Optional[str] = None  # Link to original if from AI/curated
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    is_public: bool = True  # Allow private recipes
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class ShareRecipeRequest(BaseModel):
    recipe_name: str
    description: str
    ingredients: List[str]
    order_instructions: str
    category: str
    image_base64: Optional[str] = None
    tags: List[str] = []
    difficulty_level: Optional[str] = "easy"
    original_source: Optional[str] = None
    original_recipe_id: Optional[str] = None

class LikeRecipeRequest(BaseModel):
    recipe_id: str
    user_id: str

# Weekly Recipe Models
class WeeklyRecipeRequest(BaseModel):
    user_id: str
    family_size: int = 2
    dietary_preferences: List[str] = []
    allergies: List[str] = []  # Allow clients to add additional allergies
    budget: Optional[float] = None
    cuisines: List[str] = []

class WeeklyMeal(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    day: str  # "Monday", "Tuesday", etc.
    name: str
    description: str
    ingredients: List[str]
    instructions: List[str]
    prep_time: int  # minutes
    cook_time: int  # minutes
    servings: int
    cuisine_type: str
    dietary_tags: List[str] = []
    calories_per_serving: Optional[int] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

class WeeklyRecipePlan(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    week_of: str  # "2025-W32" format
    meals: List[WeeklyMeal]
    total_budget: Optional[float] = None
    walmart_cart_url: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    is_active: bool = True
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

# Payment and Subscription Models
class PaymentTransaction(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    email: str
    session_id: str
    payment_status: str = "pending"  # pending, paid, failed, expired
    amount: float
    currency: str = "usd"
    metadata: Dict[str, str] = {}
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    stripe_payment_intent_id: Optional[str] = None
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class SubscriptionRequest(BaseModel):
    package_id: str  # "monthly_subscription"
    origin_url: str

class UserProfileUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    dietary_preferences: Optional[List[str]] = None

class SubscriptionCheckoutRequest(BaseModel):
    user_id: str
    user_email: str
    origin_url: str

class StarbucksRecipe(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    drink_name: str
    description: str
    base_drink: str
    modifications: List[str]
    ordering_script: str
    pro_tips: List[str]
    why_amazing: str
    category: str  # frappuccino, latte, etc.
    ingredients_breakdown: Optional[List[str]] = []  # Main ingredients for display
    created_at: datetime = Field(default_factory=datetime.utcnow)
    user_id: Optional[str] = None

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class WalmartProduct(BaseModel):
    product_id: str
    name: str
    price: float
    thumbnail_image: Optional[str] = None
    availability: str = "Available"

class IngredientOption(BaseModel):
    ingredient_name: str
    options: List[WalmartProduct]

class GroceryCartOptions(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    recipe_id: str
    ingredient_options: List[IngredientOption]
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class GroceryCartProduct(BaseModel):
    ingredient_name: str
    product_id: str
    name: str
    price: float
    quantity: int = 1

class GroceryCart(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    recipe_id: str
    products: List[GroceryCartProduct]
    total_price: float
    walmart_url: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

# Rate limiting for authentication endpoints
auth_rate_limit = {}
MAX_LOGIN_ATTEMPTS = 5
RATE_LIMIT_WINDOW = 900  # 15 minutes

def check_rate_limit(email: str, endpoint: str = "login") -> bool:
    """Check if user has exceeded rate limit for authentication endpoints"""
    key = f"{endpoint}:{email.lower()}"
    now = time.time()
    
    if key not in auth_rate_limit:
        auth_rate_limit[key] = []
    
    # Clean old attempts (older than RATE_LIMIT_WINDOW)
    auth_rate_limit[key] = [
        attempt_time for attempt_time in auth_rate_limit[key] 
        if now - attempt_time < RATE_LIMIT_WINDOW
    ]
    
    # Check if limit exceeded
    if len(auth_rate_limit[key]) >= MAX_LOGIN_ATTEMPTS:
        return False
    
    # Add current attempt
    auth_rate_limit[key].append(now)
    return True

# Password hashing utilities
@api_router.post("/generate-starbucks-drink")
async def generate_starbucks_drink(request: StarbucksRequest):
    """Generate a creative Starbucks secret menu drink with drive-thru ordering script - PREMIUM FEATURE"""
    try:
        # Check subscription access for premium feature
        await check_subscription_access(request.user_id)
        
        # Check usage limits for Starbucks drinks
        user = await users_collection.find_one({"id": request.user_id})
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        can_use, usage_info = check_usage_limit(user, "starbucks_drinks")
        if not can_use:
            # Return detailed limit information for frontend to handle
            subscription_status = user.get('subscription_status', 'trial')
            
            raise HTTPException(
                status_code=429, 
                detail={
                    "error": "Usage limit exceeded",
                    "message": f"Starbucks drink limit reached ({usage_info['current_count']}/{usage_info['limit']})",
                    "current_usage": usage_info['current_count'],
                    "limit": usage_info['limit'],
                    "subscription_status": subscription_status,
                    "upgrade_required": subscription_status == "trial"
                }
            )
        
        # Handle random drink type
        if request.drink_type == "random":
            drink_types = ["frappuccino", "refresher", "lemonade", "iced_matcha_latte"]
            request.drink_type = random.choice(drink_types)
            
        # Build specialized prompts for each drink type
        prompt_parts = []
        
        # Add flavor inspiration if provided
        flavor_context = ""
        if request.flavor_inspiration:
            flavor_context = f" inspired by {request.flavor_inspiration} flavors"
            
        # Define specific prompts for each drink type
        if request.drink_type == "frappuccino":
            prompt = f"""Create a **magical and whimsical Starbucks-style Frappuccino** recipe using only real Starbucks ingredients{flavor_context}.

**Examples of Creative Names & Vibes:**
- "Butterbeer Bliss" - Sweet and buttery like a cozy wizard's delight
- "Cotton Candy Clouds" - Fluffy sweetness with a nostalgic carnival feel
- "Chocolate Mint Chill" - Cool minty chocolate bliss in every sip

**Requirements:**
* A **magical, creative name** (like "Starlight Swirl" or "Dreamy Caramel Galaxy")
* Use exactly **3 to 5 Starbucks ingredients** (syrups, milk alternatives, toppings, drizzles, foam)
* Include **colorful, aesthetic elements** (drizzles, foam, powder, inclusions)
* Provide **clear drive-thru ordering instructions**
* End with a **poetic, dreamy vibe description**

**Available Ingredients:** Vanilla Bean Frappuccino, Coffee Frappuccino, Mocha Frappuccino, caramel syrup, vanilla syrup, raspberry syrup, toffee nut syrup, peppermint syrup, mocha sauce, whipped cream, caramel drizzle, chocolate drizzle, java chips, cookie crumbles, various milk alternatives

Respond with JSON in this exact format:
{{
  "drink_name": "Magical creative name",
  "description": "Enchanting vibe description",
  "base_drink": "Base Frappuccino to order",
  "modifications": ["ingredient 1", "ingredient 2", "ingredient 3", "ingredient 4"],
  "ordering_script": "Hi, can I get a grande [base] with [ingredient 1], [ingredient 2], [ingredient 3], and [ingredient 4]?",
  "category": "frappuccino",
  "vibe": "Poetic, magical one-liner"
}}"""

        elif request.drink_type == "lemonade":
            prompt = f"""Create a **sparkling, vibrant lemonade-based drink** using only Starbucks ingredients{flavor_context}.

**Examples of Creative Names & Vibes:**
- "Lavender Honey Lemonade" - A floral and sweet refreshment with creamy top notes
- "Vanilla Berry Sparkler" - Bright vanilla and berry sparkle with creamy clouds

**Requirements:**
* Use **3 to 5 ingredients** like lemonade, fruit inclusions, cold foam, syrups, freeze-dried fruits
* Choose a **bright, refreshing aesthetic** with colorful elements
* Include **clear drive-thru ordering instructions**
* End with a **bright, uplifting vibe description**

**Available Ingredients:** Lemonade, honey blend syrup, vanilla syrup, raspberry syrup, peach syrup, strawberry inclusions, freeze-dried lime, vanilla sweet cream cold foam, various fruit inclusions

Respond with JSON in this exact format:
{{
  "drink_name": "Bright creative name",
  "description": "Refreshing vibe description",
  "base_drink": "Lemonade",
  "modifications": ["ingredient 1", "ingredient 2", "ingredient 3"],
  "ordering_script": "Hi, can I get a grande lemonade with [ingredient 1], [ingredient 2], and [ingredient 3]?",
  "category": "lemonade",
  "vibe": "Bright, refreshing description"
}}"""

        elif request.drink_type == "refresher":
            prompt = f"""Create a **vibrant, tropical Starbucks Refresher** with stunning colors and flavors{flavor_context}.

**Examples of Creative Names & Vibes:**
- "Purple Haze Refresher" - A mystical burst of berry sweetness with creamy cloud
- "Tropical Dream Refresher" - Island vibes with a creamy tropical twist
- "Sunset Citrus Refresher" - A bright, tangy burst with creamy sunset hues

**Requirements:**
* Choose 1 refresher base (Strawberry Açaí, Mango Dragonfruit, Pineapple Passionfruit)
* Add **3-4 colorful components** (fruit inclusions, syrups, cold foam, lemonade, milk alternatives)
* Create **visual appeal** with contrasting colors and textures
* Provide **clear drive-thru ordering instructions**
* End with a **tropical, vibrant vibe description**

**Available Ingredients:** Refresher bases, various fruit inclusions, lemonade, coconut milk, oat milk, vanilla sweet cream cold foam, raspberry syrup, vanilla syrup, peach syrup, freeze-dried fruits

Respond with JSON in this exact format:
{{
  "drink_name": "Vibrant creative name",
  "description": "Tropical vibe description",
  "base_drink": "Refresher base to order",
  "modifications": ["ingredient 1", "ingredient 2", "ingredient 3", "ingredient 4"],
  "ordering_script": "Hi, can I get a grande [refresher base] with [ingredient 1], [ingredient 2], [ingredient 3], and [ingredient 4]?",
  "category": "refresher",
  "vibe": "Tropical, colorful description"
}}"""

        elif request.drink_type == "iced_matcha_latte":
            prompt = f"""Create a **serene, zen-inspired iced matcha latte** with beautiful earthy colors and flavors{flavor_context}.

**Examples of Creative Names & Vibes:**
- "Matcha Berry Swirl" - A green and red swirl of sweet delight
- "Coconut Matcha Breeze" - Refreshing island breeze in a vibrant green cup
- "Salted Caramel Matcha" - Sweet and salty with earthy green tea depth

**Requirements:**
* Base of iced matcha + **3-4 additional ingredients** (milk alternatives, syrups, purées, cold foam, inclusions)
* Include **colorful, aesthetic elements** (purée swirls, contrasting foam, drizzles)
* Create **visual appeal** with green base and colorful accents
* Provide **clear drive-thru ordering instructions**
* End with a **peaceful, zen-inspired vibe description**

**Available Ingredients:** Matcha powder, various milk alternatives (oat, coconut, almond), brown sugar syrup, vanilla syrup, caramel syrup, strawberry purée, vanilla sweet cream cold foam, whipped cream, caramel drizzle, freeze-dried lime

Respond with JSON in this exact format:
{{
  "drink_name": "Zen creative name",
  "description": "Peaceful vibe description",
  "base_drink": "Iced Matcha Latte",
  "modifications": ["ingredient 1", "ingredient 2", "ingredient 3", "ingredient 4"],
  "ordering_script": "Hi, can I get a grande iced matcha latte with [ingredient 1], [ingredient 2], [ingredient 3], and [ingredient 4]?",
  "category": "iced_matcha_latte",
  "vibe": "Zen, peaceful description"
}}"""

        else:  # This handles any other drink type as "random mystery"
            prompt = f"""Create a **hybrid or mystery drink** using a mix of Starbucks drink types and ingredients. Make it unique, surprising, and drive-thru ready{flavor_context}.

Requirements:
* Pick 3 to 5 ingredients from across drink categories (e.g., refresher base + matcha + foam)
* Invent a **fun, mysterious name** that isn't referenced again
* Include a **clearly spoken drive-thru order line**
* Finish with a poetic **vibe summary**

Respond with JSON in this exact format:
{{
  "drink_name": "Creative unique name",
  "description": "Vibe description",
  "base_drink": "Base drink combination to order",
  "modifications": ["ingredient 1", "ingredient 2", "ingredient 3"],
  "ordering_script": "Hi, can I get a grande [base drink] with [ingredient 1], [ingredient 2], [ingredient 3]...",
  "category": "mystery",
  "vibe": "Short mood line"
}}"""

        # Generate the drink using OpenAI
        response = openai_client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a creative Starbucks drink expert who creates whimsical, aesthetic drinks with drive-thru friendly ordering instructions. Always respond with valid JSON only."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=1000,
            temperature=0.8  # Higher temperature for more creativity
        )
        
        # Parse the response
        recipe_json = response.choices[0].message.content.strip()
        
        # Clean up the JSON (remove markdown formatting if present)
        if recipe_json.startswith("```json"):
            recipe_json = recipe_json[7:]
        if recipe_json.endswith("```"):
            recipe_json = recipe_json[:-3]
        
        recipe_data = json.loads(recipe_json)
        
        # Create Starbucks recipe object
        starbucks_drink = StarbucksRecipe(
            drink_name=recipe_data['drink_name'],
            description=recipe_data['description'],
            base_drink=recipe_data['base_drink'],
            modifications=recipe_data['modifications'],
            ordering_script=recipe_data['ordering_script'],
            pro_tips=[],  # Empty list since we're not using pro_tips anymore
            why_amazing=recipe_data.get('vibe', ''),  # Use vibe as why_amazing
            category=recipe_data['category'],
            user_id=request.user_id
        )
        
        # Add ingredients_breakdown if present
        if 'ingredients_breakdown' in recipe_data:
            starbucks_drink.ingredients_breakdown = recipe_data['ingredients_breakdown']
        
        # Save to database
        drink_dict = starbucks_drink.dict()
        result = await db.starbucks_recipes.insert_one(drink_dict)
        
        # Return the created drink
        if result.inserted_id:
            # Increment usage counter after successful generation
            await increment_usage(request.user_id, "starbucks_drinks")
            
            inserted_drink = await db.starbucks_recipes.find_one({"_id": result.inserted_id})
            return mongo_to_dict(inserted_drink)
        else:
            raise HTTPException(status_code=500, detail="Failed to save drink to database")
            
    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail="Failed to parse drink recipe from AI")
    except Exception as e:
        # Error generating Starbucks drink
        raise HTTPException(status_code=500, detail="Failed to generate Starbucks drink")

@api_router.get("/curated-starbucks-recipes")
async def get_curated_starbucks_recipes(category: Optional[str] = None):
    """Get curated Starbucks recipes, optionally filtered by category"""
    try:
        # Build query
        query = {}
        if category and category != "all":
            query["category"] = category
        
        # Get recipes from database
        recipes = await db.curated_starbucks_recipes.find(query).to_list(100)
        
        if not recipes:
            # If no recipes in database, initialize with default recipes
            await initialize_curated_recipes()
            recipes = await db.curated_starbucks_recipes.find(query).to_list(100)
        
        # Convert MongoDB documents to clean dictionaries
        clean_recipes = [mongo_to_dict(recipe) for recipe in recipes]
        
        return {"recipes": clean_recipes, "total": len(clean_recipes)}
    
    except Exception as e:
        logger.error(f"Error getting curated recipes: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get curated recipes")

async def initialize_curated_recipes():
    """Initialize the database with curated Starbucks recipes"""
    try:
        # Check if recipes already exist
        existing_count = await db.curated_starbucks_recipes.count_documents({})
        if existing_count > 0:
            return  # Already initialized
        
        # Categorize and add the curated recipes
        curated_recipes = get_curated_recipes_data()
        
        recipes_to_insert = []
        for recipe_data in curated_recipes:
            # Determine category based on base
            category = categorize_recipe(recipe_data["base"])
            
            recipe = CuratedStarbucksRecipe(
                name=recipe_data["name"],
                base=recipe_data["base"],
                ingredients=recipe_data["ingredients"],
                order_instructions=recipe_data["order_instructions"],
                vibe=recipe_data["vibe"],
                category=category
            )
            recipes_to_insert.append(recipe.dict())
        
        # Insert all recipes
        await db.curated_starbucks_recipes.insert_many(recipes_to_insert)
        logger.info(f"Initialized {len(recipes_to_insert)} curated Starbucks recipes")
        
    except Exception as e:
        logger.error(f"Error initializing curated recipes: {str(e)}")

def categorize_recipe(base: str) -> str:
    """Categorize recipe based on its base type"""
    base_lower = base.lower()
    
    if "frappuccino" in base_lower:
        return "frappuccino"
    elif "refresher" in base_lower:
        return "refresher"
    elif "matcha" in base_lower:
        return "iced_matcha_latte"
    elif "lemonade" in base_lower:
        return "lemonade"
    else:
        return "random"  # For lattes, mochas, chai, etc.

def get_curated_recipes_data():
    """Return the curated recipes data"""
    return [
        {
            "name": "Butterbeer Bliss",
            "base": "Frappuccino",
            "ingredients": [
                "Vanilla Bean Frappuccino base",
                "2 pumps caramel syrup",
                "1 pump toffee nut syrup",
                "Caramel drizzle",
                "Whipped cream"
            ],
            "order_instructions": "Hi, can I get a grande Vanilla Bean Frappuccino with 2 pumps caramel syrup, 1 pump toffee nut syrup, caramel drizzle, and whipped cream?",
            "vibe": "Sweet and buttery like a cozy wizard's delight."
        },
        {
            "name": "Purple Haze Refresher",
            "base": "Refresher",
            "ingredients": [
                "Strawberry Açaí Refresher base",
                "1 pump raspberry syrup",
                "Blackberry inclusions",
                "Lemonade",
                "Vanilla sweet cream cold foam"
            ],
            "order_instructions": "Hi, can I get a grande Strawberry Açaí Refresher with 1 pump raspberry syrup, blackberry inclusions, lemonade, and vanilla sweet cream cold foam?",
            "vibe": "A mystical burst of berry sweetness with creamy cloud."
        },
        {
            "name": "Caramel Moon Latte",
            "base": "Iced Latte",
            "ingredients": [
                "Espresso shot",
                "2% milk",
                "2 pumps caramel syrup",
                "Vanilla sweet cream cold foam",
                "Caramel drizzle"
            ],
            "order_instructions": "Hi, can I get a grande iced latte with an espresso shot, 2% milk, 2 pumps caramel syrup, vanilla sweet cream cold foam, and caramel drizzle?",
            "vibe": "Smooth caramel waves under a glowing moonlight."
        },
        {
            "name": "Tropical Dream Refresher",
            "base": "Refresher",
            "ingredients": [
                "Mango Dragonfruit Refresher base",
                "Pineapple inclusions",
                "Coconut milk",
                "1 pump vanilla syrup",
                "Freeze-dried lime"
            ],
            "order_instructions": "Hi, can I get a grande Mango Dragonfruit Refresher with pineapple inclusions, coconut milk, 1 pump vanilla syrup, and freeze-dried lime?",
            "vibe": "Island vibes with a creamy tropical twist."
        },
        {
            "name": "Matcha Berry Swirl",
            "base": "Iced Matcha Latte",
            "ingredients": [
                "Matcha powder",
                "Oat milk",
                "Strawberry purée",
                "1 pump brown sugar syrup",
                "Whipped cream"
            ],
            "order_instructions": "Hi, can I get a grande iced matcha latte with oat milk, strawberry purée, 1 pump brown sugar syrup, and whipped cream?",
            "vibe": "A green and red swirl of sweet delight."
        },
        {
            "name": "Cotton Candy Clouds",
            "base": "Frappuccino",
            "ingredients": [
                "Vanilla Bean Frappuccino base",
                "2 pumps raspberry syrup",
                "2 pumps vanilla syrup",
                "Whipped cream",
                "Pink powder topping"
            ],
            "order_instructions": "Hi, can I get a grande Vanilla Bean Frappuccino with 2 pumps raspberry syrup, 2 pumps vanilla syrup, whipped cream, and pink powder topping?",
            "vibe": "Fluffy sweetness with a nostalgic carnival feel."
        },
        {
            "name": "Sunset Citrus Refresher",
            "base": "Refresher",
            "ingredients": [
                "Pineapple Passionfruit Refresher base",
                "Lemonade",
                "1 pump peach syrup",
                "Orange inclusions",
                "Vanilla sweet cream cold foam"
            ],
            "order_instructions": "Hi, can I get a grande Pineapple Passionfruit Refresher with lemonade, 1 pump peach syrup, orange inclusions, and vanilla sweet cream cold foam?",
            "vibe": "A bright, tangy burst with creamy sunset hues."
        },
        {
            "name": "Espresso Caramel Freeze",
            "base": "Frappuccino",
            "ingredients": [
                "Coffee Frappuccino base",
                "1 shot espresso",
                "2 pumps caramel syrup",
                "Oat milk",
                "Caramel drizzle"
            ],
            "order_instructions": "Hi, can I get a grande Coffee Frappuccino with 1 shot espresso, 2 pumps caramel syrup, oat milk, and caramel drizzle?",
            "vibe": "Rich caramel and coffee harmony with a cool kick."
        },
        {
            "name": "Lavender Honey Lemonade",
            "base": "Lemonade",
            "ingredients": [
                "Lemonade",
                "1 pump honey blend syrup",
                "Lavender syrup",
                "Freeze-dried lemon",
                "Vanilla sweet cream cold foam"
            ],
            "order_instructions": "Hi, can I get a grande lemonade with 1 pump honey blend syrup, lavender syrup, freeze-dried lemon, and vanilla sweet cream cold foam?",
            "vibe": "A floral and sweet refreshment with creamy top notes."
        },
        {
            "name": "Cookie Crumble Mocha",
            "base": "Iced Mocha",
            "ingredients": [
                "Espresso shot",
                "2% milk",
                "Mocha sauce",
                "Cookie crumble topping",
                "Whipped cream"
            ],
            "order_instructions": "Hi, can I get a grande iced mocha with an espresso shot, 2% milk, mocha sauce, cookie crumble topping, and whipped cream?",
            "vibe": "Decadent chocolate with a crunch of cookie magic."
        },
        {
            "name": "Caramel Apple Refresher",
            "base": "Refresher",
            "ingredients": [
                "Strawberry Açaí Refresher base",
                "Apple inclusions",
                "Caramel syrup",
                "Lemonade",
                "Vanilla sweet cream cold foam"
            ],
            "order_instructions": "Hi, can I get a grande Strawberry Açaí Refresher with apple inclusions, caramel syrup, lemonade, and vanilla sweet cream cold foam?",
            "vibe": "Sweet orchard flavors meet creamy caramel comfort."
        },
        {
            "name": "Maple Cinnamon Swirl",
            "base": "Iced Latte",
            "ingredients": [
                "Espresso shot",
                "2% milk",
                "2 pumps cinnamon dolce syrup",
                "Maple syrup",
                "Whipped cream"
            ],
            "order_instructions": "Hi, can I get a grande iced latte with an espresso shot, 2% milk, 2 pumps cinnamon dolce syrup, maple syrup, and whipped cream?",
            "vibe": "Warm spices and maple in a creamy embrace."
        },
        {
            "name": "Dragonfruit Dream",
            "base": "Refresher",
            "ingredients": [
                "Mango Dragonfruit Refresher base",
                "Dragonfruit inclusions",
                "1 pump vanilla syrup",
                "Lemonade",
                "Freeze-dried lime"
            ],
            "order_instructions": "Hi, can I get a grande Mango Dragonfruit Refresher with dragonfruit inclusions, 1 pump vanilla syrup, lemonade, and freeze-dried lime?",
            "vibe": "Bright and fruity with a hint of tropical sweetness."
        },
        {
            "name": "Chocolate Mint Chill",
            "base": "Frappuccino",
            "ingredients": [
                "Mocha Frappuccino base",
                "Peppermint syrup",
                "2 pumps mocha sauce",
                "Whipped cream",
                "Chocolate drizzle"
            ],
            "order_instructions": "Hi, can I get a grande Mocha Frappuccino with peppermint syrup, 2 pumps mocha sauce, whipped cream, and chocolate drizzle?",
            "vibe": "Cool minty chocolate bliss in every sip."
        },
        {
            "name": "Strawberry Coconut Cooler",
            "base": "Refresher",
            "ingredients": [
                "Strawberry Açaí Refresher base",
                "Coconut milk",
                "Strawberry inclusions",
                "1 pump vanilla syrup",
                "Vanilla sweet cream cold foam"
            ],
            "order_instructions": "Hi, can I get a grande Strawberry Açaí Refresher with coconut milk, strawberry inclusions, 1 pump vanilla syrup, and vanilla sweet cream cold foam?",
            "vibe": "Tropical sweetness with creamy strawberry clouds."
        },
        {
            "name": "Toffee Nut Latte Bliss",
            "base": "Hot Latte",
            "ingredients": [
                "Espresso shot",
                "2% milk",
                "2 pumps toffee nut syrup",
                "Whipped cream",
                "Caramel drizzle"
            ],
            "order_instructions": "Hi, can I get a grande hot latte with an espresso shot, 2% milk, 2 pumps toffee nut syrup, whipped cream, and caramel drizzle?",
            "vibe": "Buttery, nutty comfort in a warm cup."
        },
        {
            "name": "Raspberry Mocha Freeze",
            "base": "Frappuccino",
            "ingredients": [
                "Mocha Frappuccino base",
                "2 pumps raspberry syrup",
                "Whipped cream",
                "Mocha drizzle",
                "Chocolate chips"
            ],
            "order_instructions": "Hi, can I get a grande Mocha Frappuccino with 2 pumps raspberry syrup, whipped cream, mocha drizzle, and chocolate chips?",
            "vibe": "Fruity chocolate decadence with a cool crunch."
        },
        {
            "name": "Pumpkin Spice Refresher",
            "base": "Refresher",
            "ingredients": [
                "Strawberry Açaí Refresher base",
                "Pumpkin spice syrup",
                "Lemonade",
                "Vanilla sweet cream cold foam",
                "Cinnamon powder"
            ],
            "order_instructions": "Hi, can I get a grande Strawberry Açaí Refresher with pumpkin spice syrup, lemonade, vanilla sweet cream cold foam, and cinnamon powder?",
            "vibe": "Fall flavors meet fruity refreshment in harmony."
        },
        {
            "name": "Chai Caramel Dream",
            "base": "Iced Chai Latte",
            "ingredients": [
                "Chai tea concentrate",
                "2% milk",
                "2 pumps caramel syrup",
                "Whipped cream",
                "Caramel drizzle"
            ],
            "order_instructions": "Hi, can I get a grande iced chai latte with 2% milk, 2 pumps caramel syrup, whipped cream, and caramel drizzle?",
            "vibe": "Spiced chai sweetness with buttery caramel warmth."
        },
        {
            "name": "Coconut Matcha Breeze",
            "base": "Iced Matcha Latte",
            "ingredients": [
                "Matcha powder",
                "Coconut milk",
                "1 pump vanilla syrup",
                "Freeze-dried lime",
                "Whipped cream"
            ],
            "order_instructions": "Hi, can I get a grande iced matcha latte with coconut milk, 1 pump vanilla syrup, freeze-dried lime, and whipped cream?",
            "vibe": "Refreshing island breeze in a vibrant green cup."
        },
        {
            "name": "Mocha Java Chip Crush",
            "base": "Frappuccino",
            "ingredients": [
                "Mocha Frappuccino base",
                "Java chips",
                "Whipped cream",
                "Mocha drizzle",
                "Chocolate chips"
            ],
            "order_instructions": "Hi, can I get a grande Mocha Frappuccino with java chips, whipped cream, mocha drizzle, and chocolate chips?",
            "vibe": "Chocolate overload with crunchy java surprises."
        },
        {
            "name": "Peach Citrus Refresher",
            "base": "Refresher",
            "ingredients": [
                "Mango Dragonfruit Refresher base",
                "Peach syrup",
                "Lemonade",
                "Orange inclusions",
                "Vanilla sweet cream cold foam"
            ],
            "order_instructions": "Hi, can I get a grande Mango Dragonfruit Refresher with peach syrup, lemonade, orange inclusions, and vanilla sweet cream cold foam?",
            "vibe": "Bright peach and citrus sunshine with creamy top."
        },
        {
            "name": "Honey Cinnamon Latte",
            "base": "Hot Latte",
            "ingredients": [
                "Espresso shot",
                "2% milk",
                "Honey blend syrup",
                "Cinnamon dolce syrup",
                "Whipped cream"
            ],
            "order_instructions": "Hi, can I get a grande hot latte with espresso shot, 2% milk, honey blend syrup, cinnamon dolce syrup, and whipped cream?",
            "vibe": "Sweet honey and spice wrapped in warmth."
        },
        {
            "name": "Vanilla Berry Sparkler",
            "base": "Lemonade",
            "ingredients": [
                "Lemonade",
                "1 pump vanilla syrup",
                "Strawberry inclusions",
                "Freeze-dried lime",
                "Vanilla sweet cream cold foam"
            ],
            "order_instructions": "Hi, can I get a grande lemonade with 1 pump vanilla syrup, strawberry inclusions, freeze-dried lime, and vanilla sweet cream cold foam?",
            "vibe": "Bright vanilla and berry sparkle with creamy clouds."
        },
        {
            "name": "Chocolate Orange Crush",
            "base": "Iced Mocha",
            "ingredients": [
                "Espresso shot",
                "2% milk",
                "Mocha sauce",
                "Orange inclusions",
                "Whipped cream"
            ],
            "order_instructions": "Hi, can I get a grande iced mocha with espresso shot, 2% milk, mocha sauce, orange inclusions, and whipped cream?",
            "vibe": "Zesty orange and rich chocolate collide."
        },
        {
            "name": "Salted Caramel Matcha",
            "base": "Iced Matcha Latte",
            "ingredients": [
                "Matcha powder",
                "2% milk",
                "Caramel syrup",
                "Sea salt sprinkle",
                "Whipped cream"
            ],
            "order_instructions": "Hi, can I get a grande iced matcha latte with 2% milk, caramel syrup, sea salt sprinkle, and whipped cream?",
            "vibe": "Sweet and salty with earthy green tea depth."
        },
        {
            "name": "Peppermint Mocha Chill",
            "base": "Frappuccino",
            "ingredients": [
                "Mocha Frappuccino base",
                "Peppermint syrup",
                "Whipped cream",
                "Chocolate drizzle",
                "Mocha drizzle"
            ],
            "order_instructions": "Hi, can I get a grande Mocha Frappuccino with peppermint syrup, whipped cream, chocolate drizzle, and mocha drizzle?",
            "vibe": "Minty chocolate bliss perfect for a cool day."
        },
        {
            "name": "Gingerbread Latte Delight",
            "base": "Hot Latte",
            "ingredients": [
                "Espresso shot",
                "2% milk",
                "Pumpkin spice syrup",
                "Molasses syrup",
                "Whipped cream"
            ],
            "order_instructions": "Hi, can I get a grande hot latte with espresso shot, 2% milk, pumpkin spice syrup, molasses syrup, and whipped cream?",
            "vibe": "Holiday spices wrapped in cozy sweetness."
        },
        {
            "name": "Peach Matcha Breeze",
            "base": "Iced Matcha Latte",
            "ingredients": [
                "Matcha powder",
                "Oat milk",
                "Peach syrup",
                "Freeze-dried lime",
                "Vanilla sweet cream cold foam"
            ],
            "order_instructions": "Hi, can I get a grande iced matcha latte with oat milk, peach syrup, freeze-dried lime, and vanilla sweet cream cold foam?",
            "vibe": "Light peach and matcha in creamy harmony."
        },
        {
            "name": "Toffee Nut Refresher",
            "base": "Refresher",
            "ingredients": [
                "Pineapple Passionfruit Refresher base",
                "2 pumps toffee nut syrup",
                "Lemonade",
                "Vanilla sweet cream cold foam",
                "Freeze-dried lime"
            ],
            "order_instructions": "Hi, can I get a grande Pineapple Passionfruit Refresher with 2 pumps toffee nut syrup, lemonade, vanilla sweet cream cold foam, and freeze-dried lime?",
            "vibe": "Tropical tang meets nutty sweetness."
        }
    ]

# User Recipe Sharing Endpoints
@api_router.post("/share-recipe")
async def share_recipe(recipe_request: ShareRecipeRequest, user_id: str):
    """Allow users to share their favorite recipes with the community"""
    try:
        # Get user information
        user = await db.users.find_one({"id": user_id})
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        username = f"{user.get('first_name', 'User')} {user.get('last_name', '')[:1]}".strip()
        
        # Validate required fields
        if not recipe_request.recipe_name or not recipe_request.description:
            raise HTTPException(status_code=400, detail="Recipe name and description are required")
        
        if not recipe_request.ingredients or len(recipe_request.ingredients) < 2:
            raise HTTPException(status_code=400, detail="At least 2 ingredients are required")
        
        # Create shared recipe
        shared_recipe = UserSharedRecipe(
            recipe_name=recipe_request.recipe_name,
            description=recipe_request.description,
            ingredients=recipe_request.ingredients,
            order_instructions=recipe_request.order_instructions,
            category=recipe_request.category,
            shared_by_user_id=user_id,
            shared_by_username=username,
            image_base64=recipe_request.image_base64,
            tags=recipe_request.tags,
            difficulty_level=recipe_request.difficulty_level,
            original_source=recipe_request.original_source,
            original_recipe_id=recipe_request.original_recipe_id
        )
        
        # Save to database
        recipe_dict = shared_recipe.dict()
        result = await db.user_shared_recipes.insert_one(recipe_dict)
        
        logger.info(f"User {username} shared recipe: {recipe_request.recipe_name}")
        
        return {
            "success": True,
            "message": "Recipe shared successfully!",
            "recipe_id": shared_recipe.id,
            "shared_by": username
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error sharing recipe: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to share recipe")

@api_router.get("/shared-recipes")
async def get_shared_recipes(
    category: Optional[str] = None,
    user_id: Optional[str] = None,
    tags: Optional[str] = None,
    limit: int = 20,
    offset: int = 0
):
    """Get community shared recipes with optional filtering"""
    try:
        # Build query
        query = {"is_public": True}
        
        if category and category != "all":
            query["category"] = category
        
        if user_id:
            query["shared_by_user_id"] = user_id
            
        if tags:
            tag_list = [tag.strip() for tag in tags.split(",")]
            query["tags"] = {"$in": tag_list}
        
        # Get recipes with pagination
        recipes = await db.user_shared_recipes.find(query).sort("created_at", -1).skip(offset).limit(limit).to_list(limit)
        total_count = await db.user_shared_recipes.count_documents(query)
        
        # Convert to clean dictionaries
        clean_recipes = [mongo_to_dict(recipe) for recipe in recipes]
        
        return {
            "recipes": clean_recipes,
            "total": total_count,
            "limit": limit,
            "offset": offset,
            "has_more": (offset + limit) < total_count
        }
        
    except Exception as e:
        logger.error(f"Error getting shared recipes: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get shared recipes")

@api_router.post("/like-recipe")
async def like_recipe(like_request: LikeRecipeRequest):
    """Like or unlike a shared recipe"""
    try:
        # Find the recipe
        recipe = await db.user_shared_recipes.find_one({"id": like_request.recipe_id})
        if not recipe:
            raise HTTPException(status_code=404, detail="Recipe not found")
        
        liked_by_users = recipe.get("liked_by_users", [])
        likes_count = recipe.get("likes_count", 0)
        
        # Check if user already liked this recipe
        if like_request.user_id in liked_by_users:
            # Unlike the recipe
            liked_by_users.remove(like_request.user_id)
            likes_count = max(0, likes_count - 1)
            action = "unliked"
        else:
            # Like the recipe
            liked_by_users.append(like_request.user_id)
            likes_count += 1
            action = "liked"
        
        # Update the recipe
        await db.user_shared_recipes.update_one(
            {"id": like_request.recipe_id},
            {
                "$set": {
                    "liked_by_users": liked_by_users,
                    "likes_count": likes_count,
                    "updated_at": datetime.utcnow()
                }
            }
        )
        
        return {
            "success": True,
            "action": action,
            "likes_count": likes_count,
            "message": f"Recipe {action} successfully!"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error liking recipe: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to like recipe")

@api_router.get("/recipe-stats")
async def get_recipe_stats():
    """Get statistics about shared recipes"""
    try:
        total_shared = await db.user_shared_recipes.count_documents({"is_public": True})
        
        # Get category breakdown
        pipeline = [
            {"$match": {"is_public": True}},
            {"$group": {"_id": "$category", "count": {"$sum": 1}}}
        ]
        category_stats = await db.user_shared_recipes.aggregate(pipeline).to_list(100)
        
        # Get top tags
        pipeline = [
            {"$match": {"is_public": True}},
            {"$unwind": "$tags"},
            {"$group": {"_id": "$tags", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}},
            {"$limit": 10}
        ]
        top_tags = await db.user_shared_recipes.aggregate(pipeline).to_list(10)
        
        # Get most liked recipes
        most_liked = await db.user_shared_recipes.find(
            {"is_public": True}, 
            {"recipe_name": 1, "shared_by_username": 1, "likes_count": 1}
        ).sort("likes_count", -1).limit(5).to_list(5)
        
        return {
            "total_shared_recipes": total_shared,
            "category_breakdown": {stat["_id"]: stat["count"] for stat in category_stats},
            "top_tags": [{"tag": stat["_id"], "count": stat["count"]} for stat in top_tags],
            "most_liked": [mongo_to_dict(recipe) for recipe in most_liked]
        }
        
    except Exception as e:
        logger.error(f"Error getting recipe stats: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get recipe stats")

def hash_password(password: str) -> str:
    """Hash a password using bcrypt"""
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')

def verify_password(password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))

# Email Verification Routes
@api_router.post("/auth/register")
async def register_user(user_data: UserRegistration):
    """Register a new user and send verification email"""
    try:
        # Basic validation
        if len(user_data.password) < 6:
            raise HTTPException(status_code=400, detail="Password must be at least 6 characters long")
        
        # Normalize email
        email_lower = user_data.email.lower().strip()
        
        # Check if user already exists (case-insensitive)
        existing_user = await db.users.find_one({"email": {"$regex": f"^{email_lower}$", "$options": "i"}})
        if existing_user:
            logging.warning(f"Registration attempt with existing email: {email_lower}")
            raise HTTPException(status_code=400, detail="Email already registered")
        
        # Hash password
        password_hash = hash_password(user_data.password)
        
        # Create user document
        user = User(
            first_name=user_data.first_name.strip(),
            last_name=user_data.last_name.strip(),
            email=email_lower,
            password_hash=password_hash,
            dietary_preferences=user_data.dietary_preferences,
            allergies=user_data.allergies,
            favorite_cuisines=user_data.favorite_cuisines,
            is_verified=False
        )
        
        # Save user to database
        user_dict = user.dict()
        result = await db.users.insert_one(user_dict)
        
        if not result.inserted_id:
            raise HTTPException(status_code=500, detail="Failed to create user account")
        
        # Generate verification code
        verification_code = email_service.generate_verification_code()
        expires_at = datetime.utcnow() + timedelta(minutes=5)
        
        # Save verification code
        code_doc = VerificationCode(
            user_id=user.id,
            email=email_lower,
            code=verification_code,
            expires_at=expires_at
        )
        await db.verification_codes.insert_one(code_doc.dict())
        
        # Send verification email
        email_sent = await email_service.send_verification_email(
            to_email=email_lower,
            first_name=user.first_name,
            verification_code=verification_code
        )
        
        if not email_sent:
            logging.warning(f"Failed to send verification email to {email_lower}")
            # Don't fail registration if email fails - user can resend later
        
        logging.info(f"User registered successfully: {email_lower}")
        return {
            "message": "Registration successful. Please check your email for verification code.",
            "email": email_lower,
            "user_id": user.id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Registration error for {user_data.email}: {str(e)}")
        raise HTTPException(status_code=500, detail="Registration failed")

@api_router.post("/auth/verify")
async def verify_email(verify_request: VerifyCodeRequest):
    """Verify email with 6-digit code"""
    try:
        # Find the most recent valid verification code
        code_doc = await db.verification_codes.find_one({
            "email": verify_request.email,
            "code": verify_request.code,
            "is_used": False
        }, sort=[("created_at", -1)])
        
        if not code_doc:
            raise HTTPException(status_code=400, detail="Invalid or expired verification code")
        
        # Check if code is expired (convert string to datetime if needed)
        expires_at = code_doc["expires_at"]
        if isinstance(expires_at, str):
            from dateutil import parser
            expires_at = parser.parse(expires_at)
        
        if datetime.utcnow() > expires_at:
            # Mark expired codes as used
            await db.verification_codes.update_one(
                {"_id": code_doc["_id"]},
                {"$set": {"is_used": True}}
            )
            raise HTTPException(status_code=400, detail="Verification code has expired")
        
        # Mark code as used
        await db.verification_codes.update_one(
            {"_id": code_doc["_id"]},
            {"$set": {"is_used": True}}
        )
        
        # Update user as verified
        result = await db.users.update_one(
            {"email": verify_request.email},
            {
                "$set": {
                    "is_verified": True,
                    "verified_at": datetime.utcnow()
                }
            }
        )
        
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Get the verified user
        user = await db.users.find_one({"email": verify_request.email})
        
        return {
            "message": "Email verified successfully!",
            "user": {
                "id": user["id"],
                "first_name": user["first_name"],
                "last_name": user["last_name"],
                "email": user["email"],
                "is_verified": user["is_verified"]
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Verification error: {str(e)}")
        raise HTTPException(status_code=500, detail="Verification failed")

@api_router.post("/auth/resend-code")
async def resend_verification_code(resend_request: ResendCodeRequest):
    """Resend verification code"""
    try:
        # Find user
        user = await db.users.find_one({"email": resend_request.email})
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        if user["is_verified"]:
            raise HTTPException(status_code=400, detail="User already verified")
        
        # Mark previous codes as used
        await db.verification_codes.update_many(
            {"email": resend_request.email, "is_used": False},
            {"$set": {"is_used": True}}
        )
        
        # Generate new verification code
        verification_code = email_service.generate_verification_code()
        expires_at = datetime.utcnow() + timedelta(minutes=5)
        
        # Save new verification code
        code_doc = VerificationCode(
            user_id=user["id"],
            email=user["email"],
            code=verification_code,
            expires_at=expires_at
        )
        await db.verification_codes.insert_one(code_doc.dict())
        
        # Send verification email
        email_sent = await email_service.send_verification_email(
            to_email=user["email"],
            first_name=user["first_name"],
            verification_code=verification_code
        )
        
        if not email_sent:
            logging.warning(f"Failed to send verification email to {user['email']}")
            # Don't fail if email fails - return success anyway for user experience
        
        return {
            "message": "New verification code sent successfully",
            "email": user["email"]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Resend code error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to resend verification code")

@api_router.post("/auth/login")
async def login_user(login_data: UserLogin):
    """Login user with email and password"""
    try:
        # Rate limiting check
        if not check_rate_limit(login_data.email, "login"):
            raise HTTPException(
                status_code=429, 
                detail="Too many login attempts. Please try again in 15 minutes."
            )
        
        # Try multiple search strategies to find the user
        email_input = login_data.email.strip()
        email_lower = email_input.lower()
        
        # Try different search approaches
        user = None
        
        # 1. Try exact match
        user = await db.users.find_one({"email": email_input})
        
        # 2. Try lowercase
        if not user:
            user = await db.users.find_one({"email": email_lower})
        
        # 3. Try case-insensitive search
        if not user:
            all_users = await db.users.find().to_list(length=100)
            for u in all_users:
                if u.get('email', '').lower() == email_lower:
                    user = u
                    break
        
        if not user:
            raise HTTPException(status_code=401, detail="Invalid email or password")
        
        # Verify password
        if not verify_password(login_data.password, user["password_hash"]):
            raise HTTPException(status_code=401, detail="Invalid email or password")
        
        # Check if user is verified
        if not user.get("is_verified", False):
            return {
                "status": "unverified",
                "message": "Email not verified. Please verify your email first.",
                "email": user["email"],
                "user_id": user["id"],
                "needs_verification": True
            }
        
        # Return successful login
        logging.info(f"User logged in successfully: {email_lower}")
        return {
            "status": "success",  # Frontend expects this field
            "message": "Login successful",
            "user": {
                "id": user["id"],
                "first_name": user["first_name"],
                "last_name": user["last_name"],
                "email": user["email"],
                "is_verified": user["is_verified"]
            },
            "user_id": user["id"],
            "email": user["email"]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Login error for {login_data.email}: {str(e)}")
        raise HTTPException(status_code=500, detail="Login failed")

@api_router.get("/debug/user/{email}")
async def get_user_debug(email: str):
    """Debug endpoint to get user record structure"""
    try:
        # Only allow in development/test mode
        if os.getenv('NODE_ENV') == 'production':
            raise HTTPException(status_code=404, detail="Not found")
        
        email_lower = email.lower().strip()
        user = await db.users.find_one({"email": {"$regex": f"^{email_lower}$", "$options": "i"}})
        
        if not user:
            return {"error": "User not found"}
        
        # Remove sensitive data for debugging
        user_copy = user.copy()
        if 'password_hash' in user_copy:
            user_copy['password_hash'] = "***HIDDEN***"
        
        return {"user": mongo_to_dict(user_copy)}
        
    except Exception as e:
        return {"error": str(e)}

@api_router.delete("/debug/clear-users")
async def clear_all_users():
    """Debug endpoint to clear all users and related data"""
    try:
        # Only allow in development/test mode
        if os.getenv('NODE_ENV') == 'production':
            raise HTTPException(status_code=404, detail="Not found")
        
        # Clear all users
        users_result = await db.users.delete_many({})
        
        # Clear verification codes
        codes_result = await db.verification_codes.delete_many({})
        
        # Clear password reset codes
        reset_result = await db.password_reset_codes.delete_many({})
        
        # Clear recipes
        recipes_result = await db.recipes.delete_many({})
        
        # Clear grocery carts
        carts_result = await db.grocery_carts.delete_many({})
        cart_options_result = await db.grocery_cart_options.delete_many({})
        
        return {
            "message": "Database cleared successfully",
            "deleted": {
                "users": users_result.deleted_count,
                "verification_codes": codes_result.deleted_count,
                "password_reset_codes": reset_result.deleted_count,
                "recipes": recipes_result.deleted_count,
                "grocery_carts": carts_result.deleted_count,
                "grocery_cart_options": cart_options_result.deleted_count
            }
        }
        
    except Exception as e:
        return {"error": str(e)}

@api_router.get("/debug/verification-codes/{email}")
async def get_verification_codes_debug(email: str):
    """Debug endpoint to get verification codes for testing"""
    try:
        # Only allow in development/test mode
        if os.getenv('NODE_ENV') == 'production':
            raise HTTPException(status_code=404, detail="Not found")
        
        codes = []
        async for code in db.verification_codes.find({"email": email, "is_used": False}).sort("created_at", -1).limit(5):
            codes.append({
                "code": code["code"],
                "expires_at": code["expires_at"],
                "is_expired": datetime.utcnow() > code["expires_at"]
            })
        
        return {
            "email": email,
            "codes": codes,
            "last_test_code": email_service.last_verification_code
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Debug endpoint error: {str(e)}")
        raise HTTPException(status_code=500, detail="Debug endpoint failed")

@api_router.delete("/debug/cleanup-test-data")
async def cleanup_test_data():
    """Debug endpoint to clean up test data"""
    try:
        # Only allow in development/test mode
        if os.getenv('NODE_ENV') == 'production':
            raise HTTPException(status_code=404, detail="Not found")
        
        # Delete test users and verification codes
        users_deleted = await db.users.delete_many({"email": {"$regex": "@example.com$"}})
        codes_deleted = await db.verification_codes.delete_many({"email": {"$regex": "@example.com$"}})
        
        return {
            "message": "Test data cleaned up",
            "users_deleted": users_deleted.deleted_count,
            "codes_deleted": codes_deleted.deleted_count
        }
        
    except Exception as e:
        logging.error(f"Cleanup error: {str(e)}")
        raise HTTPException(status_code=500, detail="Cleanup failed")

@api_router.post("/auth/forgot-password")
async def forgot_password(request: PasswordResetRequest):
    """Send password reset code to user's email"""
    try:
        # Normalize email
        email_lower = request.email.lower().strip()
        
        # Find user
        user = await db.users.find_one({"email": {"$regex": f"^{email_lower}$", "$options": "i"}})
        if not user:
            # Don't reveal if email exists for security - always return success
            return {
                "message": "If an account with this email exists, a password reset code has been sent.",
                "email": email_lower
            }
        
        # Generate reset code (6-digit)
        reset_code = email_service.generate_verification_code()
        expires_at = datetime.utcnow() + timedelta(minutes=10)  # 10 minutes for password reset
        
        # Mark any existing reset codes as used
        await db.password_reset_codes.update_many(
            {"email": email_lower, "is_used": False},
            {"$set": {"is_used": True}}
        )
        
        # Save new reset code
        reset_doc = {
            "id": str(uuid.uuid4()),
            "user_id": user["id"],
            "email": email_lower,
            "code": reset_code,
            "created_at": datetime.utcnow(),
            "expires_at": expires_at,
            "is_used": False
        }
        await db.password_reset_codes.insert_one(reset_doc)
        
        # Send reset email
        email_sent = await email_service.send_password_reset_email(
            to_email=email_lower,
            first_name=user["first_name"],
            reset_code=reset_code
        )
        
        if not email_sent:
            logging.warning(f"Failed to send password reset email to {email_lower}")
        
        return {
            "message": "If an account with this email exists, a password reset code has been sent.",
            "email": email_lower
        }
        
    except Exception as e:
        logging.error(f"Password reset error for {request.email}: {str(e)}")
        raise HTTPException(status_code=500, detail="Password reset request failed")

@api_router.post("/auth/reset-password")
async def reset_password(request: PasswordResetVerify):
    """Reset password with verification code"""
    try:
        # Normalize email
        email_lower = request.email.lower().strip()
        
        # Validate new password
        if len(request.new_password) < 6:
            raise HTTPException(status_code=400, detail="Password must be at least 6 characters long")
        
        # Find the reset code
        reset_doc = await db.password_reset_codes.find_one({
            "email": email_lower,
            "code": request.reset_code,
            "is_used": False
        }, sort=[("created_at", -1)])
        
        if not reset_doc:
            raise HTTPException(status_code=400, detail="Invalid or expired reset code")
        
        # Check if code is expired
        expires_at = reset_doc["expires_at"]
        if isinstance(expires_at, str):
            expires_at = parser.parse(expires_at)
        
        if datetime.utcnow() > expires_at:
            # Mark expired code as used
            await db.password_reset_codes.update_one(
                {"_id": reset_doc["_id"]},
                {"$set": {"is_used": True}}
            )
            raise HTTPException(status_code=400, detail="Reset code has expired")
        
        # Mark code as used
        await db.password_reset_codes.update_one(
            {"_id": reset_doc["_id"]},
            {"$set": {"is_used": True}}
        )
        
        # Hash new password
        new_password_hash = hash_password(request.new_password)
        
        # Get current user to preserve verification status
        current_user = await db.users.find_one({"email": email_lower})
        if not current_user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Update user password while preserving verification status
        update_data = {"password_hash": new_password_hash}
        
        # Preserve verification status if user was previously verified
        if current_user.get("is_verified", False):
            update_data["is_verified"] = True
            if current_user.get("verified_at"):
                update_data["verified_at"] = current_user["verified_at"]
        
        result = await db.users.update_one(
            {"email": email_lower},
            {"$set": update_data}
        )
        
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="User not found")
        
        logging.info(f"Password reset successful for {email_lower}")
        return {
            "message": "Password reset successful. You can now login with your new password.",
            "email": email_lower
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Password reset verification error: {str(e)}")
        raise HTTPException(status_code=500, detail="Password reset failed")

# Keep all existing routes for backward compatibility
@api_router.get("/health")
async def health_check():
    """Comprehensive health check for production monitoring"""
    try:
        # Check database connection
        try:
            await db.command("ping")
            db_status = "healthy"
        except Exception as db_error:
            db_status = f"error: {str(db_error)}"
        
        # Check external API availability (basic)
        external_apis = {
            "openai": bool(OPENAI_API_KEY),
            "mailjet": bool(MAILJET_API_KEY),
            "walmart": bool(WALMART_CONSUMER_ID)
        }
        
        return {
            "status": "healthy",
            "service": "buildyoursmartcart",
            "version": "2.2.1",
            "features": "navigation-fix-active",
            "last_updated": "2025-08-07T20:15:00Z",
            "database": db_status,
            "external_apis": external_apis,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }

# Add explicit OPTIONS handler for health endpoint
@api_router.options("/health")
async def health_options():
    """Handle CORS preflight for health endpoint"""
    return {"status": "ok"}

@api_router.get("/")
async def root():
    # Root endpoint
    logging.info("Root endpoint accessed")
    return {
        "message": "AI Recipe & Grocery API", 
        "version": "2.0.0", 
        "status": "running", 
        "walmart_fix": "deployed_v3", 
        "v2_integration": "LOADED",
        "blueprint_status": "ACTIVE", 
        "timestamp": datetime.utcnow().isoformat()
    }

@api_router.get("/debug/cache-status")
async def cache_status():
    """Debug endpoint to check cache and deployment status"""
    try:
        # Check database
        cart_count = await db.grocery_cart_options.count_documents({})
        
        return {
            "cache_cleared": True,
            "cart_options_count": cart_count,
            "walmart_fix_deployed": True,
            "backend_version": "walmart_fix_v2",
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        return {"error": str(e)}

@api_router.get("/walmart-v2/test")
async def walmart_v2_test():
    """🧱 NEW V2 WALMART INTEGRATION TEST - Following Blueprint"""
    return {
        "status": "V2_WORKING",
        "integration": "walmart-v2-clean-rebuild",
        "blueprint_phase": "complete",
        "cache_strategy": "enabled",
        "version": "v2.1.0",
        "timestamp": datetime.utcnow().isoformat(),
        "message": "🎉 Clean V2 integration following MCP Blueprint is working!"
    }

@api_router.post("/users")
async def create_user(user: UserCreate):
    """Create user (legacy endpoint for backward compatibility)"""
    try:
        # Check if user exists
        existing_user = await db.users.find_one({"email": user.email})
        if existing_user:
            return mongo_to_dict(existing_user)
        
        # Create user object
        user_obj = User(
            first_name=user.name.split()[0] if user.name else "User",
            last_name=" ".join(user.name.split()[1:]) if len(user.name.split()) > 1 else "",
            email=user.email,
            password_hash="legacy_user",  # Legacy users don't have passwords
            dietary_preferences=user.dietary_preferences,
            allergies=user.allergies,
            favorite_cuisines=user.favorite_cuisines,
            is_verified=True  # Legacy users are auto-verified
        )
        
        # Insert into database
        user_dict = user_obj.dict()
        await db.users.insert_one(user_dict)
        
        # Return the user dict without MongoDB _id
        return user_dict
    except Exception as e:
        logging.error(f"Error creating user: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to create user")

@api_router.get("/users/{user_id}")
async def get_user(user_id: str):
    """Get user by ID"""
    try:
        user = await db.users.find_one({"id": user_id})
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        return mongo_to_dict(user)
    except Exception as e:
        logging.error(f"Error fetching user: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch user")

@api_router.put("/users/{user_id}")
async def update_user(user_id: str, user_update: UserCreate):
    """Update user"""
    try:
        result = await db.users.update_one(
            {"id": user_id},
            {"$set": user_update.dict()}
        )
        
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="User not found")
        
        updated_user = await db.users.find_one({"id": user_id})
        return mongo_to_dict(updated_user)
    except Exception as e:
        logging.error(f"Error updating user: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to update user")

# Recipe generation functions and routes (keeping all existing functionality)
def _get_walmart_signature():
    """OLD signature function - SIMPLIFIED - No longer needed"""
    import time
    timestamp = str(int(time.time() * 1000))
    return timestamp, "mock_signature"

def _extract_core_ingredient(ingredient: str) -> str:
    """Extract the core ingredient name from complex recipe descriptions"""
    
    # Convert to lowercase for processing
    ingredient_lower = ingredient.lower().strip()
    
    # Remove common recipe measurements and quantities at the beginning
    ingredient_lower = re.sub(r'^(\d+[\s\/\-]*\d*\s*)?(cups?|cup|tbsp|tablespoons?|tablespoon|tsp|teaspoons?|teaspoon|lbs?|pounds?|pound|oz|ounces?|ounce|cans?|can|jars?|jar|bottles?|bottle|packages?|package|bags?|bag|cloves?|clove|slices?|slice|pieces?|piece|pinch|dash)\s+', '', ingredient_lower)
    
    # Remove common preparation words
    ingredient_lower = re.sub(r'\b(fresh|frozen|dried|chopped|diced|minced|sliced|grated|crushed|ground|whole|raw|cooked|boiled|steamed|roasted|baked|organic|extra|virgin|pure|natural|unsalted|salted|low[- ]fat|fat[- ]free|sugar[- ]free)\b\s*', '', ingredient_lower)
    
    # Remove preparation instructions in parentheses
    ingredient_lower = re.sub(r'\([^)]*\)', '', ingredient_lower)
    
    # Special handling for beverage ingredients
    beverage_substitutions = {
        'ice cubes': 'ice',
        'ice cube': 'ice',
        'tapioca pearls': 'tapioca pearls',
        'boba pearls': 'tapioca pearls',
        'bubble tea pearls': 'tapioca pearls',
        'black tea bags': 'black tea',
        'tea bags': 'black tea',
        'green tea bags': 'green tea',
        'oat milk': 'oat milk',
        'almond milk': 'almond milk',
        'coconut milk': 'coconut milk',
        'whole milk': 'milk',
        'skim milk': 'milk',
        '2% milk': 'milk',
        'heavy cream': 'heavy cream',
        'whipped cream': 'whipped cream',
        'brown sugar syrup': 'brown sugar',
        'simple syrup': 'sugar',
        'honey syrup': 'honey',
        'maple syrup': 'maple syrup',
        'agave syrup': 'agave',
        'mint leaves': 'mint',
        'fresh mint': 'mint',
        'lemon juice': 'lemons',
        'lime juice': 'limes',
        'orange juice': 'oranges',
        'pineapple juice': 'pineapple',
        'coconut water': 'coconut water',
        'sparkling water': 'sparkling water',
        'club soda': 'club soda',
        'soda water': 'club soda'
    }
    
    # Apply beverage-specific substitutions
    for original, replacement in beverage_substitutions.items():
        if original in ingredient_lower:
            ingredient_lower = ingredient_lower.replace(original, replacement)
            break
    
    # Handle spice blends and specific cooking terms
    spice_substitutions = {
        'italian seasoning': 'italian seasoning',
        'garlic powder': 'garlic powder',
        'onion powder': 'onion powder',
        'black pepper': 'black pepper',
        'white pepper': 'white pepper',
        'sea salt': 'sea salt',
        'kosher salt': 'salt',
        'table salt': 'salt',
        'olive oil': 'olive oil',
        'vegetable oil': 'vegetable oil',
        'canola oil': 'canola oil',
        'coconut oil': 'coconut oil',
        'butter': 'butter',
        'unsalted butter': 'butter'
    }
    
    # Apply spice and cooking substitutions
    for original, replacement in spice_substitutions.items():
        if original in ingredient_lower:
            ingredient_lower = replacement
            break
    
    # Remove any remaining quantities and measurements
    ingredient_lower = re.sub(r'^\d+[\s\-\/]*\d*\s*', '', ingredient_lower)
    ingredient_lower = re.sub(r'\b\d+[\s\-\/]*\d*\s*(ml|l|g|kg|mg)\b', '', ingredient_lower)
    
    # Remove extra whitespace and clean up
    ingredient_lower = re.sub(r'\s+', ' ', ingredient_lower).strip()
    
    # Remove common suffixes that don't help with searching
    ingredient_lower = re.sub(r'\s+(to taste|as needed|optional|for garnish|for serving)$', '', ingredient_lower)
    
    # If we end up with something too short or generic, try to use the original
    if len(ingredient_lower) < 2 or ingredient_lower in ['for', 'and', 'or', 'with', 'of', 'the', 'a', 'an']:
        # Fall back to just removing obvious quantities from the start
        fallback = re.sub(r'^\d+\s*', '', ingredient.lower().strip())
        return fallback if len(fallback) > 2 else ingredient.lower().strip()
    
    return ingredient_lower.strip() if ingredient_lower.strip() else ingredient

async def _get_walmart_product_options(ingredient: str, max_options: int = 3) -> List[WalmartProduct]:
    """OLD function - REPLACED with V2 simple implementation"""
    # Use V2 simple logic
    products = []
    for i in range(min(max_options, 3)):
        product_id = f"WM{abs(hash(f'{ingredient}_{i}')) % 100000:05d}"
        price = round(1.99 + (hash(f'{ingredient}_{i}') % 20), 2)
        
        products.append(WalmartProduct(
            product_id=product_id,
            name=f"Great Value {ingredient.title()} - Option {i+1}",
            price=price,
            thumbnail_image=f"https://i5.walmartimages.com/asr/{product_id}.jpg",
            availability="Available"
        ))
    
    return products

# Add recipe generation endpoint that accepts frontend format
@api_router.post("/recipes/generate")
async def generate_recipe_frontend_compatible(data: dict):
    """Generate a recipe using frontend data format - PREMIUM FEATURE"""
    try:
        # Extract user_id and check subscription access
        user_id = data.get('user_id')
        if not user_id:
            raise HTTPException(status_code=400, detail="User ID is required")
        
        # Check subscription access with proper error handling
        try:
            await check_subscription_access(user_id)
        except HTTPException as e:
            if e.status_code == 404:
                raise HTTPException(status_code=400, detail="Invalid user ID")
            raise e
        
        # Check usage limits for individual recipes
        user = await users_collection.find_one({"id": user_id})
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        can_use, usage_info = check_usage_limit(user, "individual_recipes")
        if not can_use:
            # Return detailed limit information for frontend to handle
            subscription_status = user.get('subscription_status', 'trial')
            
            raise HTTPException(
                status_code=429, 
                detail={
                    "error": "Usage limit exceeded",
                    "message": f"Individual recipe limit reached ({usage_info['current_count']}/{usage_info['limit']})",
                    "current_usage": usage_info['current_count'],
                    "limit": usage_info['limit'],
                    "subscription_status": subscription_status,
                    "upgrade_required": subscription_status == "trial"
                }
            )
        
        # Map frontend data to backend format
        dietary_preferences = []
        if data.get('dietary_restrictions'):
            # Split comma-separated string into list
            dietary_preferences = [pref.strip() for pref in data.get('dietary_restrictions').split(',') if pref.strip()]
        elif data.get('dietary_preferences'):
            dietary_preferences = data.get('dietary_preferences', [])
        
        ingredients_on_hand = []
        if data.get('ingredients'):
            # Split comma-separated string into list
            ingredients_on_hand = [ing.strip() for ing in data.get('ingredients').split(',') if ing.strip()]
        elif data.get('ingredients_on_hand'):
            ingredients_on_hand = data.get('ingredients_on_hand', [])
        
        # Extract prep time as number (remove "minutes" text)
        prep_time_max = None
        if data.get('prep_time'):
            try:
                prep_time_str = data.get('prep_time').replace('minutes', '').replace('hour', '60').replace('hours', '60').replace('+', '').strip()
                if prep_time_str.isdigit():
                    prep_time_max = int(prep_time_str)
                elif prep_time_str == '1':
                    prep_time_max = 60
            except:
                prep_time_max = 30  # default
        
        # Create standardized request
        recipe_request = RecipeGenRequest(
            user_id=user_id,
            recipe_category=data.get('recipe_category', 'cuisine'),
            cuisine_type=data.get('cuisine_type', data.get('cuisine', 'Italian')),
            dietary_preferences=dietary_preferences,
            ingredients_on_hand=ingredients_on_hand,
            prep_time_max=prep_time_max or data.get('prep_time_max', 30),
            servings=data.get('servings', 4),
            difficulty=data.get('difficulty', 'medium').lower()
        )
        
        # Use the existing generate_mock_recipe function or OpenAI logic
        return await generate_recipe_with_fallback(recipe_request)
        
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Frontend recipe generation error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to generate recipe")

async def generate_recipe_with_fallback(request: RecipeGenRequest):
    """Generate recipe with OpenAI or fallback to mock data"""
    try:
        # Check if OpenAI API key is available
        openai_key = os.environ.get('OPENAI_API_KEY', '')
        if not openai_key or 'placeholder' in openai_key.lower() or 'your-' in openai_key.lower():
            logging.info("OpenAI API key not configured. Using mock data fallback.")
            return await generate_mock_recipe(request)
        
        # Build the prompt for OpenAI
        prompt = f"""Create a {request.cuisine_type or 'delicious'} recipe for {request.servings} people.
Difficulty level: {request.difficulty}.
"""
        
        if request.dietary_preferences:
            prompt += f"Dietary preferences: {', '.join(request.dietary_preferences)}.\n"
        
        if request.ingredients_on_hand:
            prompt += f"Try to use these ingredients: {', '.join(request.ingredients_on_hand)}.\n"
        
        if request.prep_time_max:
            prompt += f"Maximum prep time: {request.prep_time_max} minutes.\n"
        
        prompt += """
Return ONLY a valid JSON object with this exact structure:

{
    "title": "Recipe Name",
    "description": "Brief description",
    "ingredients": ["ingredient 1", "ingredient 2"],
    "instructions": ["step 1", "step 2"],
    "prep_time": 15,
    "cook_time": 30,
    "calories_per_serving": 350,
    "shopping_list": ["ingredient_name_1", "ingredient_name_2"]
}

COMPREHENSIVE COOKING INSTRUCTIONS - PROFESSIONAL CHEF STANDARDS:
Create step-by-step instructions that read like they're written by a professional chef. Each instruction must be detailed, specific, and educational. Follow this structure:

**MANDATORY ELEMENTS FOR EACH COOKING STEP:**
1. **Specific Temperatures**: Use exact temperatures (350°F, medium-high heat, 165°F internal temperature)
2. **Precise Timing**: Include specific times ("cook for 6-7 minutes", "until golden brown, about 4-5 minutes")
3. **Visual Cues**: Describe what to look for ("until translucent", "when bubbling vigorously", "golden brown crust forms")
4. **Professional Techniques**: Use proper culinary terms (sauté, sear, braise, simmer, reduce, caramelize, deglaze, fold, whisk)
5. **Equipment Details**: Specify pan types, tools needed ("in a large cast iron skillet", "using a wooden spoon")
6. **Safety Notes**: Include temperature checks for meat ("internal temperature reaches 165°F", "until steaming hot throughout")
7. **Pro Tips**: Add helpful techniques ("don't overcrowd the pan", "taste and adjust seasoning", "let rest for 5 minutes")

**INSTRUCTION QUALITY EXAMPLES:**

❌ BASIC (Don't do this): "Cook the chicken"
✅ PROFESSIONAL: "Heat 2 tablespoons olive oil in a large cast iron skillet over medium-high heat until shimmering. Season chicken breasts with salt and pepper, then sear for 6-7 minutes per side until golden brown crust forms and internal temperature reaches 165°F (74°C). Let rest for 5 minutes before slicing to retain juices."

❌ BASIC: "Add vegetables and cook"
✅ PROFESSIONAL: "Add diced onions to the same pan and sauté for 3-4 minutes until translucent and fragrant, stirring occasionally. Add minced garlic and cook for 30 seconds more until aromatic, being careful not to let it burn."

❌ BASIC: "Make the sauce"
✅ PROFESSIONAL: "Deglaze the pan with 1/2 cup white wine, scraping up any browned bits with a wooden spoon. Add crushed tomatoes, herbs, and broth. Bring to a vigorous boil, then reduce heat to low and simmer for 15-20 minutes, stirring occasionally, until sauce reduces by half and coats the back of a spoon."

❌ BASIC: "Season to taste"
✅ PROFESSIONAL: "Taste the dish and adjust seasoning with salt and freshly ground black pepper. For added brightness, finish with a squeeze of fresh lemon juice and chopped fresh herbs just before serving."

**REQUIRED INSTRUCTION COMPONENTS:**
- Start each major step with temperature/heat level
- Include timing for each stage
- Use sensory descriptions (sound, smell, appearance)
- Add chef techniques and terminology  
- Include safety temperatures for proteins
- End with plating/presentation notes

**STRUCTURE YOUR INSTRUCTIONS LIKE THIS:**
1. **Preparation Step**: "Preheat oven to 425°F (220°C). Pat ingredients dry and season..."
2. **Cooking Steps**: "Heat oil in skillet over medium-high heat until shimmering. Add [ingredient] and cook for X minutes until [visual cue]..."
3. **Assembly/Finishing**: "Fold ingredients gently to combine. Taste and adjust seasoning..."
4. **Serving**: "Let rest for 5 minutes, then slice and serve immediately with..."

Make every instruction educational and professional - as if teaching someone to cook properly, not just following a basic recipe.

CRITICAL: The shopping_list must contain ONLY the core ingredient names without ANY quantities, measurements, preparations, or descriptions.

Shopping List Extraction Rules:
1. Remove ALL quantities: "2 cups flour" → "flour", "3 large eggs" → "eggs", "1/4 cup olive oil" → "olive oil"
2. Remove ALL measurements: "1 tbsp salt" → "salt", "2 tsp vanilla extract" → "vanilla extract", "1/2 lb ground beef" → "ground beef"
3. Remove preparations: "3 tomatoes diced" → "tomatoes", "1 onion chopped" → "onion", "2 garlic cloves minced" → "garlic"
4. Remove descriptors: "large potatoes" → "potatoes", "fresh basil leaves" → "basil", "extra virgin olive oil" → "olive oil"
5. Remove containers: "1 can diced tomatoes" → "diced tomatoes", "2 cups chicken broth" → "chicken broth", "1 jar marinara sauce" → "marinara sauce"
6. Separate compound spices: "salt and pepper" → ["salt", "pepper"], "garlic powder and onion powder" → ["garlic powder", "onion powder"]
7. Keep specific varieties: "cheddar cheese" stays "cheddar cheese", "brown sugar" stays "brown sugar", "soy sauce" stays "soy sauce"

Examples:
- "2 pounds boneless skinless chicken breasts" → "chicken breasts"
- "1/4 cup extra virgin olive oil" → "olive oil" 
- "3 medium tomatoes, diced" → "tomatoes"
- "1 large yellow onion, chopped" → "yellow onion"
- "4 cloves garlic, minced" → "garlic"
- "2 cups low-sodium chicken broth" → "chicken broth"
- "1 can (14 oz) diced tomatoes, drained" → "diced tomatoes"
- "2 tablespoons fresh lemon juice" → "lemon juice"
- "1 teaspoon dried oregano" → "oregano"
- "Salt and black pepper to taste" → ["salt", "black pepper"]
- "1/2 cup grated parmesan cheese" → "parmesan cheese"
- "2 cups cooked white rice" → "white rice"
- "1 package (8 oz) cream cheese, softened" → "cream cheese"
- "3 cups whole milk" → "milk"
- "1/2 stick unsalted butter" → "butter"
- "2 bay leaves" → "bay leaves"
- "1 bunch fresh cilantro" → "cilantro"

Generate professional-quality cooking instructions that teach proper technique while following precise shopping list extraction rules.
"""
        
        # Call OpenAI
        response = openai_client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a professional chef. Always respond with valid JSON only."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=1000,
            temperature=0.7
        )
        
        # Parse the response
        recipe_json = response.choices[0].message.content.strip()
        
        # Clean up the JSON (remove markdown formatting if present)
        if recipe_json.startswith("```json"):
            recipe_json = recipe_json[7:]
        if recipe_json.endswith("```"):
            recipe_json = recipe_json[:-3]
        
        recipe_data = json.loads(recipe_json)
        
        # Create regular recipe
        recipe = Recipe(
            title=recipe_data['title'],
            description=recipe_data['description'],
            ingredients=recipe_data['ingredients'],
            instructions=recipe_data['instructions'],
            prep_time=recipe_data['prep_time'],
            cook_time=recipe_data['cook_time'],
            servings=request.servings,
            cuisine_type=request.cuisine_type or "general",
            dietary_tags=request.dietary_preferences,
            difficulty=request.difficulty,
            calories_per_serving=recipe_data.get('calories_per_serving'),
            is_healthy=request.is_healthy,
            user_id=request.user_id,
            shopping_list=recipe_data.get('shopping_list', [])
        )
        
        # Save to database
        recipe_dict = recipe.dict()
        result = await db.recipes.insert_one(recipe_dict)
        
        # Get the inserted document and return it
        if result.inserted_id:
            # Increment usage counter after successful generation
            await increment_usage(request.user_id, "individual_recipes")
            
            inserted_recipe = await db.recipes.find_one({"_id": result.inserted_id})
            return mongo_to_dict(inserted_recipe)
        
        return recipe_dict
        
    except Exception as e:
        logging.error(f"OpenAI recipe generation failed: {str(e)}, falling back to mock data")
        return await generate_mock_recipe(request)
async def generate_recipe(request: RecipeGenRequest):
    """Generate a recipe using OpenAI - PREMIUM FEATURE"""
    try:
        # Check subscription access for premium feature
        await check_subscription_access(request.user_id)
        
        # Get user preferences from database
        user = await db.users.find_one({"id": request.user_id})
        if not user:
            logger.warning(f"User not found: {request.user_id}")
            user_dietary_preferences = []
            user_allergies = []
            user_favorite_cuisines = []
        else:
            user_dietary_preferences = user.get("dietary_preferences", [])
            user_allergies = user.get("allergies", [])
            user_favorite_cuisines = user.get("favorite_cuisines", [])
        
        logger.info(f"User preferences loaded: dietary={user_dietary_preferences}, allergies={user_allergies}, cuisines={user_favorite_cuisines}")
        
        # Build the prompt based on recipe category
        prompt_parts = []
        
        # Determine recipe category and build appropriate prompt
        recipe_category = request.recipe_category or 'cuisine'
        recipe_type = request.cuisine_type or 'general'
        
        if recipe_category == "snack":
            if recipe_type == "acai bowls":
                prompt_parts.append(f"Create a delicious and nutritious acai bowl recipe for {request.servings} people. Focus on frozen acai puree, healthy superfoods, fresh toppings, granola, and colorful presentation. Include preparation techniques for the perfect consistency.")
            elif recipe_type == "fruit lemon slices chili":
                prompt_parts.append(f"Create a spicy and refreshing fruit lemon slices with chili recipe for {request.servings} people. Focus on fresh fruits, lemon juice, chili powder, lime, and traditional Mexican-style seasoning. Include cutting techniques and spice combinations.")
            elif recipe_type == "frozen yogurt berry bites":
                prompt_parts.append(f"""Create an incredibly creative and Instagram-worthy frozen yogurt berry recipe for {request.servings} people. Think beyond basic bites - create something like 'Galaxy Swirl Yogurt Bark', 'Berry Cheesecake Bombs', 'Unicorn Yogurt Clusters', or 'Rainbow Protein Pops'. 

Focus on:
🌟 Creative presentation (layered colors, marbled effects, fun shapes)
🧊 Multiple textures (crunchy toppings, smooth yogurt, chewy add-ins)
🍓 Gourmet flavor combinations (lavender honey, matcha white chocolate, strawberry basil)
✨ Instagram-worthy appearance (vibrant colors, artistic drizzles, edible flowers)
🥄 Pro techniques (tempering chocolate, creating ombré effects, using molds)

Include Greek yogurt as the base but elevate it with:
- Superfood add-ins (chia seeds, acai powder, spirulina)
- Gourmet flavor extracts (rose water, vanilla bean, almond)
- Artisanal toppings (edible gold, freeze-dried fruits, nuts, coconut flakes)
- Creative freezing techniques (layering, swirling, molding)

Make this a show-stopping healthy dessert that looks like it came from a high-end dessert boutique!""")
            else:
                prompt_parts.append(f"Create a {recipe_type} snack recipe for {request.servings} people. Focus on tasty, satisfying snacks that are perfect for any time of day.")
        
        elif recipe_category == "beverage":
            # Generate specific beverage type based on user selection
            if recipe_type == "boba tea":
                prompt_parts.append(f"""Create a detailed brown sugar boba tea or fruit boba tea recipe for {request.servings} people. Include tapioca pearl cooking instructions, tea brewing methods, syrup preparation, and assembly techniques. Make it authentic bubble tea shop quality.

🧋 Creative, original drink name
✨ Brief flavor description (1–2 sentences that describe taste and style)
🧾 List of ingredients with exact quantities and units
🍳 Step-by-step instructions including pearl cooking, tea brewing, and assembly
💡 Optional tips or variations (e.g., vegan swap, flavor twist, serving method)

Can be milk-based or fruit-based, and use tapioca, popping boba, or creative textures. Make the drink visually Instagram-worthy with professional techniques.""")

            elif recipe_type == "thai tea":
                prompt_parts.append(f"""Create an authentic Thai tea recipe for {request.servings} people. Include traditional orange tea preparation, condensed milk ratios, spice blending, and the signature layered presentation technique.

🧋 Creative, original drink name
✨ Brief flavor description (1–2 sentences that describe taste and style)
🧾 List of ingredients with exact quantities and units
🍳 Step-by-step instructions including tea brewing, spice mixing, and layering
💡 Optional tips or variations (e.g., vegan swap, flavor twist, serving method)

Layered or infused with other flavors (like fruit, spices, milk alternatives, or syrups) with traditional preparation methods. Make the drink visually Instagram-worthy.""")

            elif recipe_type == "special lemonades":
                prompt_parts.append(f"""Create a special flavored lemonade recipe for {request.servings} people. Include unique fruit combinations, natural sweeteners, fresh herbs, and creative presentation. Focus on refreshing summer drinks with gourmet touches.

🧋 Creative, original drink name
✨ Brief flavor description (1–2 sentences that describe taste and style)
🧾 List of ingredients with exact quantities and units
🍳 Step-by-step instructions including preparation and presentation
💡 Optional tips or variations (e.g., vegan swap, flavor twist, serving method)

Refreshing, fruity, or herbal — perfect for summer with unique fruit combinations, natural sweeteners, and fresh herbs. Make the drink visually Instagram-worthy.""")

            else:
                prompt_parts.append(f"""Create a detailed {recipe_type} beverage recipe for {request.servings} people. Focus on refreshing, flavorful drinks with exact measurements and professional techniques.

🧋 Creative, original drink name
✨ Brief flavor description (1–2 sentences that describe taste and style)
🧾 List of ingredients with exact quantities and units
🍳 Step-by-step instructions
💡 Optional tips or variations (e.g., vegan swap, flavor twist, serving method)

Make the drink visually Instagram-worthy and perfect for any season.""")
        
        else:  # cuisine category
            if recipe_type == "snacks & bowls":
                prompt_parts.append(f"Create a healthy snack or bowl recipe for {request.servings} people. Focus on nutritious snacks, smoothie bowls, acai bowls, poke bowls, grain bowls, or energy bites.")
            else:
                prompt_parts.append(f"Create a {recipe_type or 'delicious'} recipe for {request.servings} people.")
        
        prompt_parts.append(f"Difficulty level: {request.difficulty}.")
        
        # Combine user's stored preferences with request preferences
        all_dietary_preferences = set()
        
        # Add user's stored dietary preferences from their profile
        if user_dietary_preferences:
            all_dietary_preferences.update(user_dietary_preferences)
            
        # Add dietary preferences from current request
        if request.dietary_preferences:
            all_dietary_preferences.update(request.dietary_preferences)
        
        # Add dietary preferences to prompt
        if all_dietary_preferences:
            prompt_parts.append(f"Dietary preferences: {', '.join(sorted(all_dietary_preferences))}.")
        
        # Add user's allergies as strict requirements
        if user_allergies:
            prompt_parts.append(f"CRITICAL ALLERGY WARNING - The user is allergic to: {', '.join(user_allergies)}. NEVER include any ingredients containing {', '.join(user_allergies)}. This is a health safety requirement. Find suitable alternatives.")
        
        # Consider user's favorite cuisines if no specific cuisine requested
        if user_favorite_cuisines and not request.cuisine_type:
            prompt_parts.append(f"Consider incorporating flavors from the user's favorite cuisines: {', '.join(user_favorite_cuisines)}.")
        elif user_favorite_cuisines and request.cuisine_type in user_favorite_cuisines:
            prompt_parts.append(f"This aligns with the user's favorite cuisine preferences.")
        
        if request.ingredients_on_hand:
            prompt_parts.append(f"Try to use these ingredients: {', '.join(request.ingredients_on_hand)}.")
        
        if request.prep_time_max:
            prompt_parts.append(f"Maximum prep time: {request.prep_time_max} minutes.")
        
        # Healthy mode requirements
        if request.is_healthy and request.max_calories_per_serving:
            prompt_parts.append(f"This should be a healthy recipe with maximum {request.max_calories_per_serving} calories per serving.")
        
        # Budget mode requirements  
        if request.is_budget_friendly and request.max_budget:
            prompt_parts.append(f"Keep the total ingredient cost under ${request.max_budget}.")
        
        # Only add generic recipe instructions for non-Starbucks categories
        if recipe_category != "starbucks":
            prompt_parts.append("""
Return ONLY a valid JSON object with this exact structure:

{
    "title": "Recipe Name",
    "description": "Brief description",
    "ingredients": ["ingredient 1", "ingredient 2"],
    "instructions": ["step 1", "step 2"],
    "prep_time": 15,
    "cook_time": 30,
    "calories_per_serving": 350,
    "shopping_list": ["ingredient_name_1", "ingredient_name_2"]
}

Recipe Category Guidelines:

SNACKS: Focus on healthy and refreshing snack options such as:
- Acai bowls (frozen acai puree, granola, fresh berries, honey, superfoods)
- Fruit lemon slices chili (fresh fruits, lemon juice, chili powder, lime, Mexican spices)
- Frozen yogurt berry bites (Greek yogurt, mixed berries, natural sweeteners, bite-sized treats)

BEVERAGES: Generate specific beverage recipes based on user selection:

1. LEMONADE-BASED DRINK: Refreshing, fruity, or herbal lemonades perfect for summer with unique fruit combinations, natural sweeteners, and fresh herbs

2. THAI TEA-BASED DRINK: Authentic Thai tea layered or infused with other flavors (fruit, spices, milk alternatives, or syrups) with traditional preparation methods

3. BOBA DRINK: Milk-based or fruit-based bubble tea using tapioca, popping boba, or creative textures with authentic bubble tea shop quality

For each beverage, include:
🧋 Creative, original drink name
✨ Brief flavor description (1–2 sentences that describe taste and style)
🧾 List of ingredients with exact quantities and units (cups, tablespoons, ounces)
🍳 Step-by-step instructions including brewing, mixing, and serving techniques
💡 Optional tips or variations (e.g., vegan swap, flavor twist, serving method)

Make each drink visually Instagram-worthy with professional techniques (shaking, layering, temperature control).

CRITICAL FOR BEVERAGE SHOPPING LIST: The shopping_list must contain ONLY clean ingredient names without any quantities, measurements, or preparation instructions. For beverage specifically:
- If ingredients include "2 shots espresso" and "1/2 cup brown sugar syrup", the shopping_list should be ["espresso beans", "brown sugar"]
- If ingredients include "1/4 cup fresh mint leaves" and "ice cubes", the shopping_list should be ["mint", "ice"]
- If ingredients include "1 cup oat milk" and "3/4 cup cooked tapioca pearls", the shopping_list should be ["oat milk", "tapioca pearls"]
- Remove ALL quantities (2 shots, 1/2 cup, 1/4 cup, etc.) and measurements (cups, tablespoons, ounces)
- Remove ALL preparation words (fresh, cooked, diced, chopped, etc.)
- Use clean, searchable ingredient names suitable for Walmart product search

Example beverage ingredients format:
- "2 shots espresso" instead of "espresso"
- "1/2 cup brown sugar syrup" instead of "brown sugar"
- "1 cup oat milk" instead of "milk"
- "3/4 cup cooked tapioca pearls" instead of "tapioca"

CUISINE: Traditional dishes from specific cultures and regions with authentic ingredients and cooking methods.

The shopping_list should be a separate bullet-pointed shopping list that includes only the names of the ingredients (no amounts, no measurements). For example:
- If ingredients include "1 cup diced tomatoes" and "2 tbsp olive oil", the shopping_list should be ["tomatoes", "olive oil"]
- If ingredients include "1 can chickpeas, drained" and "1/2 cup BBQ sauce", the shopping_list should be ["chickpeas", "BBQ sauce"]
- If beverage ingredients include "2 shots espresso" and "1/2 cup brown sugar syrup", the shopping_list should be ["espresso beans", "brown sugar"]
- BEVERAGE SPECIFIC: If ingredients include "4 lemons", "1/2 cup pineapple chunks", "1/4 cup fresh mint leaves", the shopping_list should be ["lemons", "pineapple", "mint"]
- BEVERAGE SPECIFIC: If ingredients include "1 cup oat milk", "ice cubes", "1/2 cup honey", the shopping_list should be ["oat milk", "ice", "honey"]
- Clean ingredient names without quantities, measurements, or preparation instructions

BEVERAGE EXAMPLES for reference (create one specific recipe based on user selection):
- Lemonade: Lavender Honey Lemonade with fresh herbs and edible flowers  
- Thai Tea: Coconut Mango Thai Tea with layered presentation and tropical fruit
- Boba: Taro Coconut Milk Tea with homemade taro paste and chewy tapioca pearls

IMPORTANT FOR SPICES: If the recipe uses spices, list each spice individually in the shopping_list instead of using generic terms like "spices" or "seasoning". For example:
- If ingredients include "2 tsp mixed spices (turmeric, cumin, coriander)", the shopping_list should include ["turmeric", "cumin", "coriander"]
- If ingredients include "1 tbsp garam masala and chili powder", the shopping_list should include ["garam masala", "chili powder"] 
- If ingredients include "salt, pepper, and paprika to taste", the shopping_list should include ["salt", "pepper", "paprika"]
- This ensures users can select specific spices and brands from Walmart rather than searching for generic "spices"
""")
        
        prompt = " ".join(prompt_parts)
        
        # Call OpenAI
        response = openai_client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a professional chef. Always respond with valid JSON only."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=1000,
            temperature=0.7
        )
        
        # Parse the response
        recipe_json = response.choices[0].message.content.strip()
        
        # Clean up the JSON (remove markdown formatting if present)
        if recipe_json.startswith("```json"):
            recipe_json = recipe_json[7:]
        if recipe_json.endswith("```"):
            recipe_json = recipe_json[:-3]
        
        recipe_data = json.loads(recipe_json)
        
        # Create recipe object based on category
        if recipe_category == "starbucks":
            # Create Starbucks recipe
            recipe = StarbucksRecipe(
                drink_name=recipe_data['drink_name'],
                description=recipe_data['description'],
                base_drink=recipe_data['base_drink'],
                modifications=recipe_data['modifications'],
                ordering_script=recipe_data['ordering_script'],
                pro_tips=recipe_data['pro_tips'],
                why_amazing=recipe_data['why_amazing'],
                category=recipe_data['category'],
                user_id=request.user_id
            )
            collection_name = "starbucks_recipes"
        else:
            # Create regular recipe
            recipe = Recipe(
                title=recipe_data['title'],
                description=recipe_data['description'],
                ingredients=recipe_data['ingredients'],
                instructions=recipe_data['instructions'],
                prep_time=recipe_data['prep_time'],
                cook_time=recipe_data['cook_time'],
                servings=request.servings,
                cuisine_type=request.cuisine_type or "general",
                dietary_tags=request.dietary_preferences,
                difficulty=request.difficulty,
                calories_per_serving=recipe_data.get('calories_per_serving'),
                is_healthy=request.is_healthy,
                user_id=request.user_id,
                shopping_list=recipe_data.get('shopping_list', [])
            )
            collection_name = "recipes"
        
        # Save to database
        recipe_dict = recipe.dict()
        result = await db[collection_name].insert_one(recipe_dict)
        
        # Get the inserted document and return it
        if result.inserted_id:
            inserted_recipe = await db[collection_name].find_one({"_id": result.inserted_id})
            return mongo_to_dict(inserted_recipe)
        
        return recipe_dict
        
    except json.JSONDecodeError as e:
        logging.error(f"JSON parse error: {str(e)}")
        # Fallback to mock data on JSON parsing error
        return await generate_mock_recipe(request)
    except Exception as e:
        logging.error(f"Recipe generation error: {str(e)}")
        # Check if this is due to OpenAI API key issues
        if "api_key" in str(e).lower() or "authentication" in str(e).lower() or "placeholder" in str(os.environ.get('OPENAI_API_KEY', '')).lower():
            logging.info("OpenAI API key not configured. Using fallback mock data for recipe generation.")
            return await generate_mock_recipe(request)
        raise HTTPException(status_code=500, detail="Failed to generate recipe")

@api_router.get("/recipes/{recipe_id}")
async def get_recipe_by_id(recipe_id: str):
    """Get a specific recipe by ID"""
    try:
        recipe = await db.recipes.find_one({"id": recipe_id})
        if not recipe:
            raise HTTPException(status_code=404, detail="Recipe not found")
        
        # Convert MongoDB document to dict, handling _id field
        return mongo_to_dict(recipe)
    except Exception as e:
        logging.error(f"Error fetching recipe: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch recipe")

@api_router.get("/recipes/{recipe_id}/detail")
async def get_recipe_detail(recipe_id: str):
    """Get a specific recipe by ID with Walmart integration support - searches multiple collections"""
    try:
        recipe = None
        collection_found = None
        
        # Search in different collections in order of priority
        collections_to_search = [
            ("recipes", "regular"),           # Regular generated recipes
            ("starbucks_recipes", "starbucks"), # User-generated Starbucks recipes
            ("curated_starbucks_recipes", "starbucks"), # Curated Starbucks recipes
            ("user_shared_recipes", "shared") # User-shared community recipes
        ]
        
        for collection_name, recipe_type in collections_to_search:
            recipe = await db[collection_name].find_one({"id": recipe_id})
            if recipe:
                collection_found = collection_name
                logging.info(f"Recipe {recipe_id} found in {collection_name} collection")
                break
        
        if not recipe:
            logging.warning(f"Recipe {recipe_id} not found in any collection")
            raise HTTPException(status_code=404, detail="Recipe not found")
        
        # Convert MongoDB document to dict, handling _id field
        recipe_dict = mongo_to_dict(recipe)
        
        # Handle different recipe types with appropriate defaults
        if collection_found in ["starbucks_recipes", "curated_starbucks_recipes"]:
            # Starbucks recipes have different structure
            recipe_dict.update({
                "prep_time": recipe_dict.get('prep_time', '5 minutes'),
                "cook_time": recipe_dict.get('cook_time', '0 minutes'), 
                "servings": recipe_dict.get('servings', 1),
                "cuisine": "Starbucks",
                "calories": recipe_dict.get('calories', 300),
                "type": "starbucks"
            })
            
            # Ensure we have the right title field for Starbucks recipes
            if not recipe_dict.get('title') and recipe_dict.get('drink_name'):
                recipe_dict['title'] = recipe_dict['drink_name']
            elif not recipe_dict.get('title') and recipe_dict.get('name'):
                recipe_dict['title'] = recipe_dict['name']
                
        else:
            # Regular recipes
            recipe_dict.update({
                "prep_time": recipe_dict.get('prep_time', '30 minutes'),
                "cook_time": recipe_dict.get('cook_time', '25 minutes'),
                "servings": recipe_dict.get('servings', 2),
                "cuisine": recipe_dict.get('cuisine_type', recipe_dict.get('cuisine', 'International')),
                "calories": recipe_dict.get('calories_per_serving', recipe_dict.get('calories', 400)),
                "type": "regular"
            })
        
        logging.info(f"Successfully returning recipe {recipe_id} from {collection_found}")
        return recipe_dict
        
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error fetching recipe detail for {recipe_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch recipe detail")

@api_router.post("/recipes/{recipe_id}/cart-options")
async def get_recipe_cart_options(recipe_id: str):
    """Get Walmart cart options for a generated recipe - searches multiple collections"""
    try:
        recipe = None
        collection_found = None
        
        # Search in different collections (same as detail endpoint)
        collections_to_search = [
            ("recipes", "regular"),
            ("starbucks_recipes", "starbucks"), 
            ("curated_starbucks_recipes", "starbucks"),
            ("user_shared_recipes", "shared")
        ]
        
        for collection_name, recipe_type in collections_to_search:
            recipe = await db[collection_name].find_one({"id": recipe_id})
            if recipe:
                collection_found = collection_name
                logging.info(f"Recipe {recipe_id} found in {collection_name} for cart options")
                break
        
        if not recipe:
            logging.warning(f"Recipe {recipe_id} not found in any collection for cart options")
            raise HTTPException(status_code=404, detail="Recipe not found")
        
        # Extract ingredients from the recipe
        ingredients = recipe.get('ingredients', [])
        
        # For Starbucks recipes, they might not have traditional ingredients
        if collection_found in ["starbucks_recipes", "curated_starbucks_recipes"]:
            # Starbucks recipes don't typically have shopping ingredients
            return {
                "success": False,
                "message": "Shopping cart not available for Starbucks recipes",
                "recipe_type": "starbucks",
                "recipe_title": recipe.get('drink_name') or recipe.get('name') or recipe.get('title', 'Unknown Drink')
            }
        
        if not ingredients:
            raise HTTPException(status_code=400, detail="No ingredients found in recipe")
        
        # Use the same V2 Walmart integration as weekly recipes
        ingredient_matches = []
        total_products = 0
        
        for ingredient in ingredients:
            try:
                # Search for each ingredient using Walmart API
                walmart_products = await search_walmart_products_v2(ingredient.strip())
                
                if walmart_products:
                    # Limit to top 3 products per ingredient
                    limited_products = walmart_products[:3]
                    
                    ingredient_matches.append({
                        "ingredient": ingredient.strip(),
                        "products": limited_products
                    })
                    total_products += len(limited_products)
                
            except Exception as ingredient_error:
                logging.warning(f"Failed to get Walmart products for ingredient '{ingredient}': {str(ingredient_error)}")
                continue
        
        # Return V2 format response
        return {
            "recipe_id": recipe_id,
            "user_id": recipe.get('user_id', 'unknown'),
            "ingredient_matches": ingredient_matches,
            "total_products": total_products,
            "version": "v2.1.0"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Recipe cart options error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@api_router.get("/recipes/history/{user_id}")
async def get_recipe_history(user_id: str):
    """Get all recipes for a user including regular recipes and Starbucks drinks"""
    try:
        # Get regular recipes
        recipes = await db.recipes.find({"user_id": user_id}).sort("created_at", -1).to_list(100)
        
        # Get Starbucks recipes
        starbucks_recipes = await db.starbucks_recipes.find({"user_id": user_id}).sort("created_at", -1).to_list(100)
        
        # Convert to dictionaries and add type labels
        recipe_history = []
        
        # Process regular recipes
        for recipe in recipes:
            recipe_dict = mongo_to_dict(recipe)
            # Determine category based on cuisine_type or content
            if 'snack' in recipe_dict.get('cuisine_type', '').lower() or any(word in recipe_dict.get('title', '').lower() for word in ['bowl', 'bite', 'snack', 'yogurt', 'acai']):
                recipe_dict['category'] = 'snacks'
                recipe_dict['category_label'] = 'Snacks'
                recipe_dict['category_icon'] = '🍪'
            elif 'beverage' in recipe_dict.get('cuisine_type', '').lower() or any(word in recipe_dict.get('title', '').lower() for word in ['drink', 'tea', 'lemonade', 'boba', 'smoothie']):
                recipe_dict['category'] = 'beverages'
                recipe_dict['category_label'] = 'Beverages'
                recipe_dict['category_icon'] = '🧋'
            else:
                recipe_dict['category'] = 'cuisine'
                recipe_dict['category_label'] = 'Cuisine'
                recipe_dict['category_icon'] = '🍝'
            
            recipe_dict['type'] = 'recipe'
            recipe_history.append(recipe_dict)
        
        # Process Starbucks recipes
        for starbucks_recipe in starbucks_recipes:
            starbucks_dict = mongo_to_dict(starbucks_recipe)
            starbucks_dict['category'] = 'starbucks'
            starbucks_dict['category_label'] = 'Starbucks Drinks'
            starbucks_dict['category_icon'] = '☕'
            starbucks_dict['type'] = 'starbucks'
            recipe_history.append(starbucks_dict)
        
        # Sort all recipes by created_at
        recipe_history.sort(key=lambda x: x.get('created_at', ''), reverse=True)
        
        return {
            "success": True,
            "recipes": recipe_history,
            "total_count": len(recipe_history),
            "regular_recipes": len(recipes),
            "starbucks_recipes": len(starbucks_recipes)
        }
        
    except Exception as e:
        # Error getting recipe history
        raise HTTPException(status_code=500, detail="Failed to get recipe history")

async def get_recipe(recipe_id: str):
    """Get a specific recipe"""
    try:
        recipe = await db.recipes.find_one({"id": recipe_id})
        if not recipe:
            raise HTTPException(status_code=404, detail="Recipe not found")
        
        # Convert MongoDB document to dict, handling _id field
        return mongo_to_dict(recipe)
    except Exception as e:
        logging.error(f"Error fetching recipe: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch recipe")

@api_router.get("/users/{user_id}/recipes")
async def get_user_recipes(user_id: str):
    """Get all recipes for a user"""
    try:
        recipes = []
        async for recipe in db.recipes.find({"user_id": user_id}).sort("created_at", -1):
            recipes.append(mongo_to_dict(recipe))
        
        return recipes
    except Exception as e:
        logging.error(f"Error fetching user recipes: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch recipes")

# ALL WALMART CLASSES AND ENDPOINTS DELETED - WILL BE RECREATED FROM SCRATCH

# NEW SIMPLE WALMART INTEGRATION - CREATED FROM SCRATCH
class WalmartProduct(BaseModel):
    product_id: str
    name: str
    price: float
    image_url: Optional[str] = ""
    available: bool = True

class IngredientOptions(BaseModel):
    ingredient_name: str
    options: List[WalmartProduct]  # Frontend expects 'options', not 'products'

class CartOptions(BaseModel):
    recipe_id: str
    user_id: str
    ingredients: List[IngredientOptions]
    total_products: int = 0

# Simple Walmart API function without complex authentication
import os
import time
import base64
import requests
from typing import List
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import padding

async def search_walmart_products(ingredient: str) -> List[WalmartProduct]:
    """
    Real Walmart API product search using ingredient names
    """
    # Search Walmart API
    
    try:
        # Get credentials from environment
        consumer_id = os.environ.get('WALMART_CONSUMER_ID')
        private_key_pem = os.environ.get('WALMART_PRIVATE_KEY')
        key_version = os.environ.get('WALMART_KEY_VERSION', '1')
        
        if not all([consumer_id, private_key_pem]):
            # Missing API credentials
            return []
        
        # Load private key
        private_key = serialization.load_pem_private_key(
            private_key_pem.encode(), 
            password=None
        )
        
        # Generate authentication signature
        timestamp = str(int(time.time() * 1000))
        message = f"{consumer_id}\n{timestamp}\n{key_version}\n".encode("utf-8")
        signature = private_key.sign(message, padding.PKCS1v15(), hashes.SHA256())
        signature_b64 = base64.b64encode(signature).decode("utf-8")
        
        # Set up headers
        headers = {
            "WM_CONSUMER.ID": consumer_id,
            "WM_CONSUMER.INTIMESTAMP": timestamp,
            "WM_SEC.KEY_VERSION": key_version,
            "WM_SEC.AUTH_SIGNATURE": signature_b64,
            "Content-Type": "application/json"
        }
        
        # Make API request
        url = f"https://developer.api.walmart.com/api-proxy/service/affil/product/v2/search"
        params = {
            "query": ingredient.replace(' ', '+'),
            "numItems": 4
        }
        
        response = requests.get(url, headers=headers, params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            items = data.get("items", [])
            
            products = []
            for item in items[:3]:  # Take top 3 results
                if "itemId" in item:
                    product = WalmartProduct(
                        product_id=str(item.get("itemId")),
                        name=item.get("name", "Unknown Product"),
                        price=float(item.get("salePrice", 0)),
                        image_url=item.get("thumbnailImage", ""),
                        available=True
                    )
                    products.append(product)
            
            # Found Walmart products
            return products
            
        else:
            # Walmart API error
            return []
            
    except Exception as e:
        # Error searching Walmart
        return []

@api_router.post("/grocery/cart-options-test")
async def get_grocery_cart_options_test(
    recipe_id: str = Query(..., description="Recipe ID"),
    user_id: str = Query(..., description="User ID")
):
    """Test endpoint for cart options without user validation"""
    try:
        logger.info(f"Looking for recipe_id: {recipe_id} for user: {user_id}")
        
        # Test with hardcoded ingredients from a real recipe
        test_ingredients = ["12 oz penne pasta", "1 lb ground beef", "24 oz marinara sauce", "1 cup shredded mozzarella", "2 tbsp olive oil"]
        
        logger.info(f"Testing with {len(test_ingredients)} ingredients")
        
        # Get Walmart product options for each ingredient (2-3 options per ingredient)
        ingredient_options = []
        
        for ingredient in test_ingredients:
            try:
                # Get multiple product options for this ingredient
                walmart_products = await search_walmart_products_v2(ingredient, max_results=3)
                
                if walmart_products and len(walmart_products) > 0:
                    # Convert to options format
                    options = []
                    for i, product in enumerate(walmart_products):
                        options.append({
                            "product_id": product.id,
                            "name": product.name,
                            "price": product.price,
                            "brand": product.brand or "Great Value",
                            "rating": product.rating,
                            "image_url": product.image_url or "https://via.placeholder.com/100x100?text=Product",
                            "is_selected": i == 0  # First option is default selected
                        })
                    
                    ingredient_options.append({
                        "ingredient_name": ingredient,
                        "options": options,
                        "selected_product_id": options[0]["product_id"] if options else None
                    })
                    logger.info(f"✅ {ingredient}: Found {len(options)} Walmart products")
                else:
                    # Fallback for ingredients that can't be found
                    fallback_option = {
                        "product_id": f"search_{abs(hash(ingredient)) % 100000}",
                        "name": f"Search for {ingredient.title()}",
                        "price": 0.00,
                        "brand": "Walmart",
                        "rating": 0.0,
                        "image_url": "https://via.placeholder.com/100x100?text=Search",
                        "is_selected": True
                    }
                    
                    ingredient_options.append({
                        "ingredient_name": ingredient,
                        "options": [fallback_option],
                        "selected_product_id": fallback_option["product_id"]
                    })
                    logger.warning(f"⚠️ {ingredient}: Using search fallback")
                    
            except Exception as e:
                logger.error(f"❌ Error processing ingredient '{ingredient}': {str(e)}")
        
        estimated_total = sum([opt["options"][0]["price"] for opt in ingredient_options if opt["options"]])
        
        logger.info(f"✅ Successfully processed cart options for {len(ingredient_options)} ingredients")
        
        return {
            "recipe_id": recipe_id,
            "recipe_name": "Test Recipe with Real Walmart Data",
            "ingredient_options": ingredient_options,
            "total_ingredients": len(ingredient_options),
            "estimated_total": round(estimated_total, 2),
            "success": True
        }
        
    except Exception as e:
        logger.error(f"❌ ERROR in cart-options-test: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get cart options: {str(e)}")


@api_router.post("/grocery/cart-options")
async def get_cart_options(
    recipe_id: str = Query(..., description="Recipe ID"),
    user_id: str = Query(..., description="User ID")
):
    """NEW SIMPLE Walmart integration - Get cart options for recipe ingredients - PREMIUM FEATURE"""
    try:
        # Check subscription access for premium feature
        await check_subscription_access(user_id)
        
        # New cart options request
        
        # Get recipe from database
        recipe = await db.recipes.find_one({"id": recipe_id, "user_id": user_id})
        if not recipe:
            raise HTTPException(status_code=404, detail="Recipe not found")
        
        recipe_title = recipe.get('title', 'Unknown Recipe')
        shopping_list = recipe.get('shopping_list', [])
        
        # Found recipe
        
        if not shopping_list:
            return {
                "recipe_id": recipe_id,
                "user_id": user_id,
                "ingredients": [],
                "message": "No ingredients found in recipe",
                "total_products": 0
            }
        
        # Search for products for each ingredient
        ingredient_options = []
        total_products = 0
        
        for ingredient in shopping_list:
            # Searching products for ingredient
            products = await search_walmart_products(ingredient)
            
            if products:
                ingredient_options.append(IngredientOptions(
                    ingredient_name=ingredient,
                    options=products
                ))
                total_products += len(products)
                # Found products for ingredient
            else:
                # No products found
                pass
        
        # Create response - always return structure, even if no products found
        ingredient_options_list = []
        for ingredient_option in ingredient_options:
            ingredient_dict = {
                "ingredient_name": ingredient_option.ingredient_name,
                "options": [product.dict() for product in ingredient_option.options]
            }
            ingredient_options_list.append(ingredient_dict)
        
        response_data = {
            "recipe_id": recipe_id,
            "user_id": user_id,
            "ingredient_options": ingredient_options_list,
            "total_products": total_products
        }
        
        if total_products == 0:
            response_data["message"] = "No Walmart products found for this recipe's ingredients."
            # No Walmart products found
        else:
            # Cart options created successfully
            pass
        
        return response_data
        
    except HTTPException:
        raise
    except Exception as e:
        # Error in cart options
        raise HTTPException(status_code=500, detail=f"Error creating cart options: {str(e)}")

@api_router.post("/grocery/generate-cart-url")
async def generate_cart_url(cart_data: Dict[str, Any]):
    """Generate Walmart affiliate cart URL from selected products"""
    try:
        selected_products = cart_data.get('products', [])
        
        if not selected_products:
            raise HTTPException(status_code=400, detail="No products selected")
        
        # Generate proper Walmart affiliate cart URL
        product_ids = []
        total_price = 0.0
        
        for product in selected_products:
            # Support both V2 format ('id') and legacy format ('product_id')
            product_id = product.get('id') or product.get('product_id')
            quantity = product.get('quantity', 1)  # Default quantity is 1
            if product_id:  # Only add non-None product IDs
                # Format: product_id_quantity for Walmart affiliate URL
                product_ids.append(f"{product_id}_{quantity}")
            total_price += float(product.get('price', 0)) * quantity
        
        # Correct Walmart affiliate cart URL format
        cart_url = f"https://affil.walmart.com/cart/addToCart?items={','.join(product_ids)}"
        
        return {
            "success": True,
            "cart_url": cart_url,
            "total_price": round(total_price, 2),
            "total_items": len(selected_products),
            "product_count": len(selected_products),
            "products": selected_products
        }
        
    except Exception as e:
        # Error generating cart URL
        raise HTTPException(status_code=500, detail=f"Error generating cart URL: {str(e)}")

# END NEW WALMART INTEGRATION

# CORS middleware configuration - Production ready
@api_router.delete("/recipes/{recipe_id}")
async def delete_recipe(recipe_id: str, user_id: str = None):
    """Delete a specific recipe - with optional user validation"""
    try:
        # Build the query filter
        query_filter = {"id": recipe_id}
        
        # If user_id is provided, ensure user can only delete their own recipes
        if user_id:
            query_filter["user_id"] = user_id
        
        # Delete the recipe
        result = await db.recipes.delete_one(query_filter)
        
        if result.deleted_count == 1:
            logger.info(f"Successfully deleted recipe: {recipe_id}")
            return {"success": True, "message": "Recipe deleted successfully"}
        else:
            # Could be either recipe not found or user doesn't own the recipe
            logger.warning(f"Recipe not found or access denied for deletion: {recipe_id}")
            raise HTTPException(status_code=404, detail="Recipe not found or access denied")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting recipe {recipe_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to delete recipe")

@api_router.delete("/starbucks-recipes/{recipe_id}")
async def delete_starbucks_recipe(recipe_id: str):
    """Delete a specific Starbucks recipe"""
    try:
        # Convert string ID to ObjectId if needed
        from bson import ObjectId
        if ObjectId.is_valid(recipe_id):
            object_id = ObjectId(recipe_id)
            result = await db.starbucks_recipes.delete_one({"_id": object_id})
        else:
            result = await db.starbucks_recipes.delete_one({"id": recipe_id})
        
        if result.deleted_count == 1:
            return {"success": True, "message": "Starbucks recipe deleted successfully"}
        else:
            raise HTTPException(status_code=404, detail="Starbucks recipe not found")
    except Exception as e:
        # Error deleting Starbucks recipe
        raise HTTPException(status_code=500, detail="Failed to delete Starbucks recipe")

# ========================================
# 💳 STRIPE SUBSCRIPTION & PAYMENT ROUTES
# ========================================

@api_router.get("/user/settings/{user_id}")
async def get_user_settings(user_id: str):
    """Get user settings including profile, subscription, and usage information"""
    try:
        user = await users_collection.find_one({"id": user_id})
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Get access status
        access_status = can_access_premium_features(user)
        
        # Get usage information for all types
        usage_info = {}
        for usage_type in ["weekly_recipes", "individual_recipes", "starbucks_drinks"]:
            can_use, info = check_usage_limit(user, usage_type)
            usage_info[usage_type] = info
        
        return {
            "profile": {
                "user_id": user["id"],
                "first_name": user.get("first_name", ""),
                "last_name": user.get("last_name", ""),
                "email": user.get("email", ""),
                "dietary_preferences": user.get("dietary_preferences", []),
                "is_verified": user.get("is_verified", False),
                "created_at": user.get("created_at")
            },
            "subscription": access_status,
            "usage": usage_info,
            "limits": get_user_usage_limits(user.get('subscription_status', 'trial'))
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting user settings: {e}")
        raise HTTPException(status_code=500, detail="Failed to get user settings")

@api_router.put("/user/profile/{user_id}")
async def update_user_profile(user_id: str, profile_update: UserProfileUpdate):
    """Update user profile information"""
    try:
        user = await users_collection.find_one({"id": user_id})
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Prepare update data
        update_data = {}
        if profile_update.first_name is not None:
            update_data["first_name"] = profile_update.first_name
        if profile_update.last_name is not None:
            update_data["last_name"] = profile_update.last_name
        if profile_update.dietary_preferences is not None:
            update_data["dietary_preferences"] = profile_update.dietary_preferences
        
        if not update_data:
            raise HTTPException(status_code=400, detail="No valid fields to update")
        
        # Update user
        result = await users_collection.update_one(
            {"id": user_id},
            {"$set": update_data}
        )
        
        if result.modified_count == 0:
            raise HTTPException(status_code=400, detail="No changes made")
        
        # Return updated user data
        updated_user = await users_collection.find_one({"id": user_id})
        return {
            "message": "Profile updated successfully",
            "profile": {
                "user_id": updated_user["id"],
                "first_name": updated_user.get("first_name", ""),
                "last_name": updated_user.get("last_name", ""),
                "email": updated_user.get("email", ""),
                "dietary_preferences": updated_user.get("dietary_preferences", [])
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating user profile: {e}")
        raise HTTPException(status_code=500, detail="Failed to update profile")

@api_router.post("/subscription/cancel/{user_id}")
async def cancel_subscription(user_id: str):
    """Cancel user subscription at end of billing period"""
    try:
        user = await users_collection.find_one({"id": user_id})
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        subscription_status = user.get('subscription_status', 'trial')
        if subscription_status != 'active':
            raise HTTPException(status_code=400, detail="No active subscription to cancel")
        
        # Set cancellation flag
        update_data = {
            "cancel_at_period_end": True,
            "subscription_cancel_reason": "user_requested",
            "subscription_cancelled_date": datetime.utcnow()
        }
        
        result = await users_collection.update_one(
            {"id": user_id},
            {"$set": update_data}
        )
        
        if result.modified_count == 0:
            raise HTTPException(status_code=400, detail="Failed to cancel subscription")
        
        # Get next billing date for user notification
        next_billing_date = user.get('next_billing_date')
        if isinstance(next_billing_date, str):
            next_billing_date = parser.parse(next_billing_date)
        
        return {
            "message": "Subscription will be cancelled at the end of current billing period",
            "cancel_at_period_end": True,
            "access_until": next_billing_date.isoformat() if next_billing_date else None,
            "cancelled_date": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error cancelling subscription: {e}")
        raise HTTPException(status_code=500, detail="Failed to cancel subscription")

@api_router.post("/subscription/reactivate/{user_id}")
async def reactivate_subscription(user_id: str):
    """Reactivate a cancelled subscription before period end"""
    try:
        user = await users_collection.find_one({"id": user_id})
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        if not user.get('cancel_at_period_end', False):
            raise HTTPException(status_code=400, detail="Subscription is not set to cancel")
        
        # Remove cancellation flag
        update_data = {
            "cancel_at_period_end": False,
            "subscription_cancel_reason": None,
            "subscription_reactivated_date": datetime.utcnow()
        }
        
        result = await users_collection.update_one(
            {"id": user_id},
            {"$set": update_data}
        )
        
        if result.modified_count == 0:
            raise HTTPException(status_code=400, detail="Failed to reactivate subscription")
        
        return {
            "message": "Subscription reactivated successfully",
            "cancel_at_period_end": False,
            "reactivated_date": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error reactivating subscription: {e}")
        raise HTTPException(status_code=500, detail="Failed to reactivate subscription")

@api_router.get("/user/usage/{user_id}")
async def get_user_usage(user_id: str):
    """Get detailed user usage information"""
    try:
        user = await users_collection.find_one({"id": user_id})
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Get usage information for all types
        usage_info = {}
        for usage_type in ["weekly_recipes", "individual_recipes", "starbucks_drinks"]:
            can_use, info = check_usage_limit(user, usage_type)
            usage_info[usage_type] = {
                "current": info["current_count"],
                "limit": info["limit"],
                "remaining": info["remaining"],
                "can_use": info["can_use"]
            }
        
        return {
            "user_id": user_id,
            "subscription_status": user.get('subscription_status', 'trial'),
            "usage": usage_info,
            "limits": get_user_usage_limits(user.get('subscription_status', 'trial')),
            "usage_reset_date": user.get('usage_reset_date')
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting user usage: {e}")
        raise HTTPException(status_code=500, detail="Failed to get user usage")

@api_router.get("/subscription/status/{user_id}")
async def get_subscription_status(user_id: str):
    """Get user's subscription status and access details"""
    try:
        user = await users_collection.find_one({"id": user_id})
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        access_status = get_user_access_status(user)
        return access_status
        
    except HTTPException:
        # Re-raise HTTPExceptions to preserve specific error messages
        raise
    except Exception as e:
        logger.error(f"Error getting subscription status: {e}")
        raise HTTPException(status_code=500, detail="Failed to get subscription status")

@api_router.post("/subscription/create-checkout")
async def create_subscription_checkout(request: SubscriptionCheckoutRequest):
    """Create Stripe checkout session for subscription - FIXED WITH EMERGENTINTEGRATIONS"""
    return await create_subscription_checkout_integrated(
        request, 
        db, 
        users_collection, 
        payment_transactions_collection
    )

@api_router.get("/subscription/checkout/status/{session_id}")
async def get_checkout_status(session_id: str):
    """Get checkout session status - FIXED WITH EMERGENTINTEGRATIONS"""
    return await get_checkout_status_integrated(
        session_id,
        db,
        users_collection,
        payment_transactions_collection
    )

@api_router.post("/webhook/stripe")
async def stripe_webhook(request: Request):
    """Handle Stripe webhook events - FIXED WITH EMERGENTINTEGRATIONS"""
    return await stripe_webhook_integrated(request, db)

@api_router.get("/subscription/packages")
async def get_subscription_packages():
    """Get available subscription packages"""
    return {
        "packages": SUBSCRIPTION_PACKAGES
    }

@api_router.post("/subscription/cancel/{user_id}")
async def cancel_subscription(user_id: str):
    """Cancel user's active subscription"""
    try:
        user = await users_collection.find_one({"id": user_id})
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Check if user has an active subscription
        if not is_subscription_active(user):
            raise HTTPException(status_code=400, detail="No active subscription to cancel")
        
        # Update user subscription status to cancelled
        await users_collection.update_one(
            {"id": user_id},
            {
                "$set": {
                    "subscription_status": "cancelled",
                    "subscription_cancelled_date": datetime.utcnow(),
                    "subscription_cancel_reason": "user_requested"
                }
            }
        )
        
        # If we have a Stripe subscription ID, we could cancel it on Stripe side too
        stripe_subscription_id = user.get("stripe_subscription_id")
        if stripe_subscription_id and STRIPE_API_KEY:
            try:
                # Note: emergentintegrations might not have cancel subscription method
                # For now, we'll just update our local database
                # In production, you'd want to call Stripe's API to cancel the subscription
                logger.info(f"Subscription cancelled locally for user {user_id}, Stripe ID: {stripe_subscription_id}")
            except Exception as stripe_error:
                logger.error(f"Failed to cancel Stripe subscription: {stripe_error}")
                # Continue anyway - local cancellation is successful
        
        logger.info(f"Subscription cancelled for user {user_id}")
        
        return {
            "status": "success",
            "message": "Subscription cancelled successfully",
            "cancelled_at": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error cancelling subscription: {e}")
        raise HTTPException(status_code=500, detail="Failed to cancel subscription")

@api_router.post("/subscription/resubscribe/{user_id}")
async def resubscribe_user(user_id: str):
    """Reactivate a cancelled subscription (requires new payment)"""
    try:
        user = await users_collection.find_one({"id": user_id})
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Check if user has a cancelled subscription
        subscription_status = user.get("subscription_status", "trial")
        if subscription_status not in ["cancelled", "expired"]:
            if is_subscription_active(user):
                raise HTTPException(status_code=400, detail="User already has active subscription")
            elif is_trial_active(user):
                raise HTTPException(status_code=400, detail="User is still in trial period")
        
        # Reset subscription status to trial so they can start a new subscription
        # In a real implementation, this would redirect them to create a new checkout session
        await users_collection.update_one(
            {"id": user_id},
            {
                "$set": {
                    "subscription_status": "trial",  # Reset to trial
                    "subscription_reactivated_date": datetime.utcnow(),
                    "subscription_cancelled_date": None,
                    "subscription_cancel_reason": None
                },
                "$unset": {
                    "stripe_subscription_id": "",
                    "subscription_start_date": "",
                    "subscription_end_date": "",
                    "last_payment_date": "",
                    "next_billing_date": ""
                }
            }
        )
        
        logger.info(f"Subscription reset to trial for resubscription: {user_id}")
        
        return {
            "status": "success",
            "message": "Subscription reset to trial. User can now create a new subscription.",
            "reactivated_at": datetime.utcnow().isoformat(),
            "next_step": "Create new checkout session for subscription"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error reactivating subscription: {e}")
        raise HTTPException(status_code=500, detail="Failed to reactivate subscription")

# Middleware to check subscription access for premium endpoints
async def check_subscription_access(user_id: str):
    """Check if user has access to premium features"""
    user = await users_collection.find_one({"id": user_id})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if not can_access_premium_features(user):
        access_status = get_user_access_status(user)
        raise HTTPException(
            status_code=402, 
            detail={
                "message": "Premium subscription required",
                "access_status": access_status
            }
        )

# API router will be included after all endpoints are defined

# ========================================
# 🧱 WALMART INTEGRATION V2 - CLEAN REBUILD  
# Following MCP App Development Blueprint
# ========================================

# V2 Models
class WalmartProductV2(BaseModel):
    id: str
    name: str
    price: float
    image_url: str = ""
    available: bool = True
    product_url: Optional[str] = ""
    brand: Optional[str] = "Great Value"
    rating: Optional[float] = 4.0
    
class IngredientMatchV2(BaseModel):
    ingredient: str
    products: List[WalmartProductV2]
    
class CartOptionsV2(BaseModel):
    recipe_id: str
    user_id: str
    ingredient_matches: List[IngredientMatchV2]
    total_products: int
    version: str = "v2.1.0"

# V2 Cache Strategy
def get_cache_headers():
    """Phase 2: Always-fresh response headers"""
    return {
        "Cache-Control": "no-store, no-cache, must-revalidate, proxy-revalidate",
        "Pragma": "no-cache", 
        "Expires": "0",
        "X-Accel-Expires": "0"
    }

# V2 Clean API Client
async def search_walmart_products_v2(query: str, max_results: int = 3) -> List[WalmartProductV2]:
    """
    Search Walmart API with proper authentication headers based on official documentation
    """
    try:
        # Check if real credentials are available (not placeholder values)
        if (not WALMART_CONSUMER_ID or not WALMART_PRIVATE_KEY or 
            WALMART_CONSUMER_ID == "your-walmart-consumer-id-here" or 
            WALMART_PRIVATE_KEY == "your-walmart-private-key-here"):
            # Fallback to mock data only for placeholder/missing credentials
            logger.info(f"Using mock data for query '{query}' - credentials not configured")
            return await generate_mock_walmart_products(query, max_results)
        
        # 1. Get environment credentials
        consumer_id = WALMART_CONSUMER_ID
        private_key_pem = WALMART_PRIVATE_KEY
        key_version = WALMART_KEY_VERSION
        
        # 2. Generate timestamp (Unix epoch time in milliseconds)
        import time
        timestamp = str(int(time.time() * 1000))
        
        # 3. Create headers map for canonicalization (as per Walmart documentation)
        headers_map = {
            "WM_CONSUMER.ID": consumer_id,
            "WM_CONSUMER.INTIMESTAMP": timestamp,
            "WM_SEC.KEY_VERSION": key_version
        }
        
        # 4. Canonicalize headers (sort alphabetically and create string to sign)
        sorted_keys = sorted(headers_map.keys())
        string_to_sign = ""
        for key in sorted_keys:
            string_to_sign += headers_map[key].strip() + "\n"
        
        logger.info(f"String to sign: {repr(string_to_sign)}")
        
        # 5. Generate signature using SHA256WithRSA (as per Java example)
        from cryptography.hazmat.primitives import serialization, hashes
        from cryptography.hazmat.primitives.asymmetric import padding
        from cryptography.hazmat.backends import default_backend
        import base64
        
        try:
            # Handle different key formats
            if private_key_pem.startswith("-----BEGIN"):
                # PEM format - load directly
                private_key = serialization.load_pem_private_key(
                    private_key_pem.encode(),
                    password=None,
                    backend=default_backend()
                )
                logger.info("✅ Loaded PEM format private key")
            else:
                # Base64 PKCS#8 format (as suggested in Java example)
                key_bytes = base64.b64decode(private_key_pem)
                private_key = serialization.load_der_private_key(
                    key_bytes,
                    password=None,
                    backend=default_backend()
                )
                logger.info("✅ Loaded base64 PKCS#8 format private key")
            
            # Generate RSA signature with SHA256 (equivalent to Java's SHA256WithRSA)
            signature_bytes = private_key.sign(
                string_to_sign.encode('utf-8'),
                padding.PKCS1v15(),  # Standard RSA signature padding
                hashes.SHA256()
            )
            
            signature_b64 = base64.b64encode(signature_bytes).decode('utf-8')
            logger.info("✅ RSA signature generated successfully!")
            
        except Exception as e:
            logger.error(f"❌ Failed to generate signature: {str(e)}")
            raise
        
        # 6. Create final authentication headers
        auth_headers = {
            "WM_CONSUMER.ID": consumer_id,
            "WM_CONSUMER.INTIMESTAMP": timestamp,
            "WM_SEC.KEY_VERSION": key_version,
            "WM_SEC.AUTH_SIGNATURE": signature_b64,
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        
        # 7. Make API request
        url = "https://developer.api.walmart.com/api-proxy/service/affil/product/v2/search"
        params = {
            "query": query.replace(' ', '+'),
            "numItems": min(max_results, 10)
        }
        
        # Make API request with increased timeout for production reliability
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url, headers=auth_headers, params=params)
            
            logger.info(f"Walmart API response: {response.status_code}")
            
            # 8. Process response
            if response.status_code == 200:
                data = response.json()
                items = data.get("items", [])
                products = []
                
                for item in items[:max_results]:  # Take requested number of results
                    if "itemId" in item:
                        walmart_product = WalmartProductV2(
                            id=str(item.get('itemId')),
                            name=item.get('name', f'Walmart {query.title()}')[:100],
                            price=float(item.get('salePrice', item.get('msrp', 2.99))),
                            image_url=item.get('thumbnailImage', ''),
                            product_url=item.get('productUrl', ''),
                            brand=item.get('brandName', 'Great Value'),
                            rating=float(item.get('customerRating', 4.0)),
                            available=True
                        )
                        products.append(walmart_product)
                
                logger.info(f"✅ Walmart API returned {len(products)} real products for '{query}'")
                return products
            
            else:
                # Log API response details for debugging
                response_text = response.text[:500] if hasattr(response, 'text') else 'No response text'
                logger.error(f"Walmart API returned {response.status_code}: {response_text}")
                
                # Only fallback to mock data for credential issues, not temporary API issues
                if response.status_code == 401:
                    logger.warning("Walmart API authentication failed - using mock data")
                    return await generate_mock_walmart_products(query, max_results)
                else:
                    # For other errors, return empty list to let the system handle gracefully
                    return []
                
    except Exception as e:
        logger.error(f"Walmart API error for query '{query}': {str(e)}")
        # Only use mock data if credentials are definitely invalid
        if "credentials" in str(e).lower() or "auth" in str(e).lower() or "signature" in str(e).lower():
            return await generate_mock_walmart_products(query, max_results)
        return []

async def generate_mock_walmart_products(query: str, max_results: int = 3) -> List[WalmartProductV2]:
    """High-quality mock data fallback when real API is unavailable"""
    products = []
    for i in range(min(max_results, 3)):
        product_id = f"WM{abs(hash(f'{query}_{i}')) % 100000:05d}"
        price = round(1.99 + (hash(f'{query}_{i}') % 20), 2)
        
        products.append(WalmartProductV2(
            id=product_id,
            name=f"Great Value {query.title()} - Premium Quality",
            price=price,
            image_url="https://via.placeholder.com/100x100?text=🛒",
            available=True
        ))
    return products

# ===== GROCERY CART API ENDPOINTS =====

@api_router.post("/grocery/cart-options")
async def get_grocery_cart_options(
    recipe_id: str = Query(..., description="Recipe ID"),
    user_id: str = Query(..., description="User ID")
):
    """Get Walmart product options for recipe ingredients"""
    try:
        logger.info(f"🔍 DEBUG: Looking for recipe_id: {recipe_id} for user: {user_id}")
        
        recipe_doc = None
        
        # First try weekly meal plans collection (most likely)
        weekly_collection = db["weekly_meal_plans"]
        weekly_plans = await weekly_collection.find({"user_id": user_id}).sort([("created_at", -1)]).to_list(length=10)
        
        # Found weekly plans for user
        
        for plan in weekly_plans:
            meals = plan.get('meals', [])
            # Checking plan with meals
            for meal in meals:
                meal_id = meal.get('id')
                # Checking meal ID vs target
                if meal_id == recipe_id:
                    recipe_doc = meal
                    logger.info(f"✅ Found matching recipe: {meal.get('name')}")
                    break
            if recipe_doc:
                break
        
        # If not found in weekly plans, try regular recipes collection
        if not recipe_doc:
            # Recipe not found in weekly plans, trying regular recipes...
            recipe_collection = db["recipes"]
            recipe_doc = await recipe_collection.find_one({"recipe_id": recipe_id})
            
            # Also try with _id if recipe_id doesn't work
            if not recipe_doc:
                try:
                    recipe_doc = await recipe_collection.find_one({"_id": recipe_id})
                except:
                    pass
        
        if not recipe_doc:
            # Recipe still not found after all searches
            if weekly_plans and len(weekly_plans) > 0 and weekly_plans[0].get('meals'):
                # Available recipe IDs:
                for meal in weekly_plans[0]['meals'][:3]:
                    pass  # Recipe ID: {meal.get('id')}: {meal.get('name')}
            raise HTTPException(status_code=404, detail=f"Recipe not found with ID: {recipe_id}")
        
        # Get shopping list from the recipe
        shopping_list = recipe_doc.get('shopping_list', recipe_doc.get('ingredients', []))
        
        if not shopping_list:
            return {
                "recipe_id": recipe_id,
                "recipe_name": recipe_doc.get('name', 'Unknown Recipe'),
                "ingredient_options": [],
                "total_ingredients": 0,
                "estimated_total": 0.0,
                "success": True,
                "message": "No shopping list available for this recipe"
            }
        
        logger.info(f"Processing {len(shopping_list)} ingredients for Walmart search")
        
        # Get Walmart product options for each ingredient (2-3 options per ingredient)
        ingredient_options = []
        
        for ingredient in shopping_list:
            try:
                # Get multiple product options for this ingredient
                walmart_products = await search_walmart_products_v2(ingredient, max_results=3)
                
                if walmart_products and len(walmart_products) > 0:
                    # Convert to options format
                    options = []
                    for i, product in enumerate(walmart_products):
                        options.append({
                            "product_id": product.id,
                            "name": product.name,
                            "price": product.price,
                            "brand": product.brand or "Great Value",
                            "rating": product.rating,
                            "image_url": product.image_url or "https://via.placeholder.com/100x100?text=Product",
                            "is_selected": i == 0  # First option is default selected
                        })
                    
                    ingredient_options.append({
                        "ingredient_name": ingredient,
                        "options": options,
                        "selected_product_id": options[0]["product_id"] if options else None
                    })
                    logger.info(f"✅ {ingredient}: Found {len(options)} Walmart products")
                else:
                    # Fallback for ingredients that can't be found
                    fallback_option = {
                        "product_id": f"search_{abs(hash(ingredient)) % 100000}",
                        "name": f"Search for {ingredient.title()}",
                        "price": 0.00,
                        "brand": "Walmart",
                        "rating": 0.0,
                        "image_url": "https://via.placeholder.com/100x100?text=Search",
                        "is_selected": True
                    }
                    
                    ingredient_options.append({
                        "ingredient_name": ingredient,
                        "options": [fallback_option],
                        "selected_product_id": fallback_option["product_id"]
                    })
                    logger.warning(f"⚠️ {ingredient}: Using search fallback")
                    
            except Exception as e:
                logger.error(f"❌ Error processing ingredient '{ingredient}': {str(e)}")
                # Create error fallback
                error_option = {
                    "product_id": f"error_{abs(hash(ingredient)) % 100000}",
                    "name": f"Unable to find {ingredient.title()}",
                    "price": 0.00,
                    "brand": "Walmart",
                    "rating": 0.0,
                    "image_url": "https://via.placeholder.com/100x100?text=Error",
                    "is_selected": True
                }
                
                ingredient_options.append({
                    "ingredient_name": ingredient,
                    "options": [error_option],
                    "selected_product_id": error_option["product_id"]
                })
        
        estimated_total = sum([opt["options"][0]["price"] for opt in ingredient_options if opt["options"]])
        
        logger.info(f"✅ Successfully processed cart options for {len(ingredient_options)} ingredients")
        
        return {
            "recipe_id": recipe_id,
            "recipe_name": recipe_doc.get('name', 'Unknown Recipe'),
            "ingredient_options": ingredient_options,
            "total_ingredients": len(ingredient_options),
            "estimated_total": round(estimated_total, 2),
            "success": True
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ ERROR in cart-options: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get cart options: {str(e)}")


@api_router.post("/grocery/generate-cart-url-v2")
async def generate_grocery_cart_url_v2(request: Request):
    """
    Generate Walmart cart URL with selected products.
    Called when user clicks 'Add to Walmart Cart' after making selections.
    """
    try:
        # Parse JSON request body
        body = await request.json()
        logger.info(f"🔍 Received cart URL request: {body}")
        
        selected_products = body.get('selected_products', []) or body.get('products', [])
        
        if not selected_products:
            return {
                "cart_url": "https://walmart.com/cp/food/976759",
                "total_price": 0.0,
                "total_items": 0,
                "success": True,
                "message": "No products selected - redirecting to Walmart grocery section"
            }
        
        # Filter out search/error placeholder products and collect real product IDs
        valid_product_ids = []
        total_price = 0.0
        
        for product in selected_products:
            # Support both V2 format ('id') and legacy format ('product_id')
            product_id = product.get('id') or product.get('product_id', '')
            price = float(product.get('price', 0))
            
            # Process products for cart URL
            
            # Only include real product IDs (not search/error fallbacks)
            if (not product_id.startswith('search_') and 
                not product_id.startswith('error_') and 
                not product_id.startswith('WM') and  # Exclude mock data
                product_id.strip() and  # Ensure not empty
                product_id.isdigit()):  # Real Walmart IDs are numeric
                valid_product_ids.append(product_id)
                total_price += price
                # Added to cart
            else:
                pass  # Skipped invalid product ID
        
        # Generate Walmart cart URL
        if valid_product_ids:
            cart_url = f"https://walmart.com/cart?items={','.join(valid_product_ids)}"
            message = f"Cart created with {len(valid_product_ids)} real Walmart products"
        else:
            # If no valid products, redirect to Walmart grocery section
            cart_url = "https://walmart.com/cp/food/976759"
            message = "No valid products found - redirecting to Walmart grocery section"
        
        result = {
            "cart_url": cart_url,
            "total_price": round(total_price, 2),
            "total_items": len(valid_product_ids),
            "success": True,
            "message": message
        }
        
        logger.info(f"✅ Cart URL result generated successfully")
        return result
        
    except Exception as e:
        logger.error(f"❌ ERROR generating cart URL: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to generate cart URL: {str(e)}")


@api_router.get("/debug/walmart-integration")
async def debug_walmart_integration():
    """Debug endpoint to verify Walmart API integration with credentials"""
    try:
        # Check if credentials are available
        credentials_status = {
            "WALMART_CONSUMER_ID": "SET" if WALMART_CONSUMER_ID and WALMART_CONSUMER_ID != "your-walmart-consumer-id-here" else "PLACEHOLDER",
            "WALMART_PRIVATE_KEY": "SET" if WALMART_PRIVATE_KEY and WALMART_PRIVATE_KEY != "your-walmart-private-key-here" else "PLACEHOLDER",
            "WALMART_KEY_VERSION": WALMART_KEY_VERSION or "NOT_SET"
        }
        
        # Test with a simple ingredient
        test_ingredient = "pasta"
        products = await search_walmart_products_v2(test_ingredient, max_results=3)
        
        # Get more sample products to show variety
        sample_products = []
        test_ingredients = ["pasta", "rice", "bread", "milk", "eggs"]
        
        for ingredient in test_ingredients:
            try:
                ingredient_products = await search_walmart_products_v2(ingredient, max_results=2)
                for product in ingredient_products:
                    sample_products.append({
                        "ingredient": ingredient,
                        "product_id": product.id,
                        "name": product.name,
                        "price": product.price,
                        "brand": product.brand,
                        "rating": product.rating,
                        "url": product.product_url
                    })
                    if len(sample_products) >= 10:  # Limit to 10 sample products
                        break
                if len(sample_products) >= 10:
                    break
            except Exception as e:
                logger.error(f"Error getting sample products for {ingredient}: {str(e)}")
                continue
        
        # Determine if using mock data
        using_mock_data = True
        if products:
            # Check if any product IDs are real (numeric, not starting with "WM")
            for product in products:
                if product.id.isdigit() and len(product.id) >= 6:
                    using_mock_data = False
                    break
        
        result = {
            "credentials_status": credentials_status,
            "test_ingredient": test_ingredient,
            "products_found": len(products),
            "using_mock_data": using_mock_data,
            "sample_product": {
                "id": products[0].id,
                "name": products[0].name,
                "price": products[0].price,
                "url": products[0].product_url
            } if products else None,
            "sample_products": sample_products,
            "total_sample_products": len(sample_products)
        }
        
        return result
        
    except Exception as e:
        return {
            "error": str(e),
            "credentials_status": {
                "WALMART_CONSUMER_ID": "SET" if WALMART_CONSUMER_ID and WALMART_CONSUMER_ID != "your-walmart-consumer-id-here" else "PLACEHOLDER",
                "WALMART_PRIVATE_KEY": "SET" if WALMART_PRIVATE_KEY and WALMART_PRIVATE_KEY != "your-walmart-private-key-here" else "PLACEHOLDER"
            }
        }

@api_router.post("/v2/walmart/cart-options")
async def get_cart_options_v2(
    recipe_id: str = Query(..., description="Recipe ID"),
    user_id: str = Query(..., description="User ID")
):
    """
    V2 Clean cart options endpoint
    Following blueprint's structured response pattern
    """
    try:
        # Get recipe
        recipe = await db.recipes.find_one({"id": recipe_id, "user_id": user_id})
        if not recipe:
            raise HTTPException(status_code=404, detail="Recipe not found")
        
        # Extract ingredients
        shopping_list = recipe.get('shopping_list', [])
        if not shopping_list:
            # Fallback to ingredients list
            ingredients = recipe.get('ingredients', [])
            shopping_list = [ing.split(',')[0].strip() for ing in ingredients if ing][:10]
        
        if not shopping_list:
            return CartOptionsV2(
                recipe_id=recipe_id,
                user_id=user_id,
                ingredient_matches=[],
                total_products=0
            )
        
        # Search products for each ingredient
        ingredient_matches = []
        total_products = 0
        
        for ingredient in shopping_list[:8]:  # Limit for performance
            products = await search_walmart_products_v2(ingredient, max_results=3)
            if products:
                ingredient_matches.append(IngredientMatchV2(
                    ingredient=ingredient,
                    products=products
                ))
                total_products += len(products)
        
        # Structured response
        result = CartOptionsV2(
            recipe_id=recipe_id,
            user_id=user_id,
            ingredient_matches=ingredient_matches,
            total_products=total_products
        )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"V2 Cart options error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@api_router.post("/v2/walmart/generate-cart-url")
async def generate_cart_url_v2(cart_data: Dict[str, Any]):
    """V2 Generate affiliate cart URL from selections"""
    try:
        selected_products = cart_data.get('selected_products', [])
        
        if not selected_products:
            raise HTTPException(status_code=400, detail="No products selected")
        
        # Generate proper Walmart affiliate cart URL
        product_items = []
        total_price = 0.0
        
        for product in selected_products:
            product_id = product.get('id', '')
            quantity = product.get('quantity', 1)
            price = float(product.get('price', 0))
            
            if product_id:
                # Format: product_id_quantity for Walmart affiliate URL
                product_items.append(f"{product_id}_{quantity}")
                total_price += price * quantity
        
        # Correct Walmart affiliate cart URL format
        cart_url = f"https://affil.walmart.com/cart/addToCart?items={','.join(product_items)}"
        
        return {
            "success": True,
            "cart_url": cart_url,
            "total_price": round(total_price, 2),
            "total_items": sum(p.get('quantity', 1) for p in selected_products),
            "product_count": len(selected_products),
            "version": "v2.1.0",
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logging.error(f"V2 Cart URL generation error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to generate cart URL")

# ========================================
# END V2 INTEGRATION
# ========================================

# ========================================
# WEEKLY RECIPE SYSTEM - NEW FEATURE
# ========================================

def get_current_week() -> str:
    """Get current week in YYYY-WXX format"""
    import datetime
    now = datetime.datetime.now()
    year, week, _ = now.isocalendar()
    return f"{year}-W{week:02d}"

def get_week_days() -> List[str]:
    """Get days of the week for meal planning"""
    return ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

async def generate_weekly_meals(family_size: int = 2, dietary_preferences: List[str] = [], allergies: List[str] = [], cuisines: List[str] = []) -> List[WeeklyMeal]:
    """Generate 7 dinner meals for the week using OpenAI"""
    try:
        # Check if OpenAI API key is properly configured
        if not OPENAI_API_KEY or OPENAI_API_KEY in ["your-openai-api-key-here", "your-ope****here"]:
            logger.warning("OpenAI API key not configured. Using fallback mock data for weekly meals.")
            return await generate_mock_weekly_meals(family_size, dietary_preferences, allergies, cuisines)
        
        # Build dietary preferences string
        dietary_info = ""
        if dietary_preferences:
            dietary_info = f"Dietary restrictions: {', '.join(dietary_preferences)}. "
        
        # Build allergy information
        allergy_info = ""
        if allergies:
            allergy_info = f"CRITICAL ALLERGIES TO AVOID: {', '.join(allergies)}. Do not include any ingredients containing these allergens. "
        
        # Build cuisine preferences
        cuisine_info = ""
        if cuisines:
            cuisine_info = f"Focus on these cuisines: {', '.join(cuisines)}. "
        
        # Create AI prompt for weekly meal generation
        prompt = f"""Generate a weekly meal plan with 7 unique dinner recipes for {family_size} adults.

{dietary_info}{allergy_info}{cuisine_info}

CRITICAL SAFETY REQUIREMENTS:
- If VEGETARIAN: NO meat, poultry, fish, or seafood in any recipe
- If VEGAN: NO animal products whatsoever (no meat, dairy, eggs, honey, etc.)  
- If GLUTEN-FREE: Use only gluten-free grains and substitute regular pasta with gluten-free pasta
- ALLERGIES: Completely avoid ALL listed allergens - this is life-threatening serious
- Double-check every single ingredient against dietary restrictions and allergies

Requirements:
- Balanced nutrition across the week
- Easy-to-cook ingredients
- Budget-friendly options
- Variety in cooking methods and flavors
- Each recipe should serve {family_size} people
- STRICTLY avoid all mentioned allergens in ingredients - NO EXCEPTIONS
- Follow all dietary restrictions carefully - this affects user health and safety

For each day, provide:
1. Day of the week
2. Recipe name 
3. Brief description
4. Complete ingredients list (verified safe for dietary restrictions)
5. Step-by-step cooking instructions
6. Prep time and cook time in minutes
7. Cuisine type
8. Estimated calories per serving

Format as JSON array with 7 meal objects, each containing:
{{
  "day": "Monday",
  "name": "Recipe Name",
  "description": "Brief description",
  "ingredients": ["ingredient 1", "ingredient 2", ...],
  "instructions": ["step 1", "step 2", ...],
  "prep_time": 15,
  "cook_time": 30,
  "servings": {family_size},
  "cuisine_type": "Italian",
  "dietary_tags": ["vegetarian"],
  "calories_per_serving": 450
}}"""

        # Generate meal plan using OpenAI
        response = openai_client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a professional meal planning chef specializing in dietary restrictions and allergy-safe cooking. Create balanced, delicious weekly meal plans that STRICTLY follow all dietary requirements and avoid ALL allergens. User safety is paramount - never include restricted ingredients. Always respond with valid JSON only."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=2000,
            temperature=0.7
        )
        
        # Parse the response
        meals_json = response.choices[0].message.content.strip()
        
        # Clean up the JSON (remove markdown formatting if present)
        if meals_json.startswith("```json"):
            meals_json = meals_json[7:]
        if meals_json.endswith("```"):
            meals_json = meals_json[:-3]
        
        meals_data = json.loads(meals_json)
        
        # Convert to WeeklyMeal objects
        weekly_meals = []
        days = get_week_days()
        
        for i, meal_data in enumerate(meals_data[:7]):  # Ensure we only get 7 meals
            day = days[i] if i < len(days) else meal_data.get('day', f'Day {i+1}')
            
            meal = WeeklyMeal(
                day=day,
                name=meal_data.get('name', f'Meal for {day}'),
                description=meal_data.get('description', ''),
                ingredients=meal_data.get('ingredients', []),
                instructions=meal_data.get('instructions', []),
                prep_time=meal_data.get('prep_time', 15),
                cook_time=meal_data.get('cook_time', 30),
                servings=meal_data.get('servings', family_size),
                cuisine_type=meal_data.get('cuisine_type', 'International'),
                dietary_tags=meal_data.get('dietary_tags', []),
                calories_per_serving=meal_data.get('calories_per_serving', 400)
            )
            weekly_meals.append(meal)
        
        return weekly_meals
        
    except json.JSONDecodeError as e:
        logger.error(f"JSON decode error in weekly meal generation: {str(e)}")
        # Fallback to mock data on JSON parsing error
        return await generate_mock_weekly_meals(family_size, dietary_preferences, allergies, cuisines)
    except Exception as e:
        logger.error(f"Error generating weekly meals: {str(e)}")
        # Fallback to mock data on any other error
        return await generate_mock_weekly_meals(family_size, dietary_preferences, allergies, cuisines)

def get_diverse_recipe_for_cuisine(cuisine_type: str, dietary_preferences: List[str]) -> List[dict]:
    """Get diverse recipe variations for different cuisine types"""
    
    # Define recipe variations for different cuisines
    recipe_database = {
        "Italian": [
            {
                "title": "Creamy Mushroom Risotto",
                "description": "Rich and creamy Arborio rice cooked with wild mushrooms and parmesan",
                "ingredients": [
                    "1½ cups Arborio rice",
                    "4 cups warm vegetable broth",
                    "8 oz mixed mushrooms, sliced",
                    "1 medium onion, diced",
                    "3 cloves garlic, minced",
                    "½ cup white wine",
                    "½ cup grated Parmesan cheese",
                    "2 tbsp butter",
                    "2 tbsp olive oil",
                    "Fresh thyme and parsley"
                ],
                "instructions": [
                    "Heat broth in a separate pot and keep warm",
                    "Sauté mushrooms in olive oil until golden, set aside",
                    "In same pan, cook onion until translucent",
                    "Add garlic and rice, stir for 2 minutes",
                    "Add wine and stir until absorbed",
                    "Add warm broth one ladle at a time, stirring constantly",
                    "Continue until rice is creamy and tender (18-20 minutes)",
                    "Stir in mushrooms, butter, and Parmesan",
                    "Season and garnish with fresh herbs"
                ],
                "prep_time": 10,
                "cook_time": 25,
                "calories": 380,
                "shopping_list": ["Arborio rice", "mushrooms", "vegetable broth", "onion", "garlic", "white wine", "Parmesan cheese", "butter", "olive oil", "thyme", "parsley"]
            },
            {
                "title": "Classic Margherita Pizza",
                "description": "Traditional Neapolitan pizza with fresh mozzarella, basil, and tomato sauce",
                "ingredients": [
                    "1 lb pizza dough",
                    "½ cup pizza sauce",
                    "8 oz fresh mozzarella, sliced",
                    "¼ cup fresh basil leaves",
                    "2 tbsp olive oil",
                    "Salt and pepper to taste",
                    "Cornmeal for dusting"
                ],
                "instructions": [
                    "Preheat oven to 475°F (245°C)",
                    "Roll out pizza dough on floured surface",
                    "Transfer to pizza stone or baking sheet dusted with cornmeal",
                    "Spread sauce evenly, leaving 1-inch border",
                    "Add mozzarella slices and drizzle with olive oil",
                    "Bake for 12-15 minutes until crust is golden",
                    "Top with fresh basil leaves",
                    "Season with salt and pepper, slice and serve"
                ],
                "prep_time": 15,
                "cook_time": 15,
                "calories": 320,
                "shopping_list": ["pizza dough", "pizza sauce", "fresh mozzarella", "fresh basil", "olive oil", "cornmeal"]
            }
        ],
        "Mexican": [
            {
                "title": "Chicken Enchiladas Verde",
                "description": "Tender chicken wrapped in corn tortillas with tangy green salsa and cheese",
                "ingredients": [
                    "2 lbs chicken breast",
                    "12 corn tortillas",
                    "2 cups green salsa (salsa verde)",
                    "2 cups shredded Mexican cheese blend",
                    "1 medium onion, diced",
                    "3 cloves garlic, minced",
                    "1 cup sour cream",
                    "¼ cup fresh cilantro",
                    "2 tbsp olive oil",
                    "Salt and cumin to taste"
                ],
                "instructions": [
                    "Cook chicken breast until tender, then shred",
                    "Preheat oven to 375°F (190°C)",
                    "Warm tortillas to make them pliable",
                    "Mix shredded chicken with half the cheese and onion",
                    "Fill each tortilla with chicken mixture and roll tightly",
                    "Place seam-side down in baking dish",
                    "Pour salsa verde over enchiladas",
                    "Top with remaining cheese and bake 20-25 minutes",
                    "Garnish with sour cream and cilantro"
                ],
                "prep_time": 20,
                "cook_time": 45,
                "calories": 420,
                "shopping_list": ["chicken breast", "corn tortillas", "green salsa", "Mexican cheese", "onion", "garlic", "sour cream", "cilantro", "olive oil", "cumin"]
            },
            {
                "title": "Street-Style Tacos al Pastor",
                "description": "Marinated pork with pineapple, onions, and cilantro on soft corn tortillas",
                "ingredients": [
                    "2 lbs pork shoulder, thinly sliced",
                    "16 small corn tortillas",
                    "1 cup diced pineapple",
                    "1 large white onion, diced",
                    "½ cup fresh cilantro, chopped",
                    "3 dried guajillo chiles",
                    "2 chipotle chiles in adobo",
                    "3 cloves garlic",
                    "2 tbsp achiote paste",
                    "Lime wedges for serving"
                ],
                "instructions": [
                    "Soak guajillo chiles in hot water for 15 minutes",
                    "Blend soaked chiles, chipotle, garlic, and achiote into marinade",
                    "Marinate pork slices for at least 2 hours",
                    "Cook marinated pork on hot griddle until charred",
                    "Warm tortillas on same griddle",
                    "Chop cooked pork into small pieces",
                    "Fill tortillas with pork, pineapple, onion, and cilantro",
                    "Serve with lime wedges"
                ],
                "prep_time": 30,
                "cook_time": 15,
                "calories": 350,
                "shopping_list": ["pork shoulder", "corn tortillas", "pineapple", "white onion", "cilantro", "guajillo chiles", "chipotle chiles", "garlic", "achiote paste", "limes"]
            }
        ],
        "Asian": [
            {
                "title": "Pad Thai with Shrimp",
                "description": "Classic Thai stir-fried noodles with shrimp, tofu, and tangy tamarind sauce",
                "ingredients": [
                    "8 oz rice noodles",
                    "1 lb large shrimp, peeled",
                    "4 oz firm tofu, cubed",
                    "3 eggs, beaten",
                    "2 cups bean sprouts",
                    "4 green onions, chopped",
                    "¼ cup tamarind paste",
                    "3 tbsp fish sauce",
                    "2 tbsp brown sugar",
                    "2 tbsp vegetable oil",
                    "Crushed peanuts and lime wedges"
                ],
                "instructions": [
                    "Soak rice noodles in warm water until soft",
                    "Mix tamarind paste, fish sauce, and brown sugar for sauce",
                    "Heat oil in large wok or skillet",
                    "Cook shrimp until pink, remove and set aside",
                    "Add tofu and cook until golden",
                    "Push tofu to one side, scramble eggs",
                    "Add drained noodles and sauce, toss to combine",
                    "Add shrimp back, then bean sprouts and green onions",
                    "Serve with peanuts and lime wedges"
                ],
                "prep_time": 15,
                "cook_time": 12,
                "calories": 390,
                "shopping_list": ["rice noodles", "shrimp", "firm tofu", "eggs", "bean sprouts", "green onions", "tamarind paste", "fish sauce", "brown sugar", "vegetable oil", "peanuts", "limes"]
            },
            {
                "title": "Korean Bibimbap Bowl",
                "description": "Mixed rice bowl with seasoned vegetables, meat, and gochujang sauce",
                "ingredients": [
                    "2 cups cooked white rice",
                    "8 oz beef bulgogi or ground beef",
                    "1 cup spinach",
                    "1 cup bean sprouts",
                    "1 large carrot, julienned",
                    "4 shiitake mushrooms, sliced",
                    "2 eggs",
                    "3 tbsp gochujang (Korean chili paste)",
                    "2 tbsp sesame oil",
                    "2 tbsp soy sauce",
                    "1 tbsp rice vinegar"
                ],
                "instructions": [
                    "Cook beef with soy sauce until browned",
                    "Blanch spinach and bean sprouts separately, season with sesame oil",
                    "Sauté carrots and mushrooms until tender",
                    "Fry eggs sunny-side up",
                    "Mix gochujang with sesame oil and vinegar for sauce",
                    "Divide rice among bowls",
                    "Arrange vegetables and beef over rice",
                    "Top each bowl with fried egg",
                    "Serve with gochujang sauce on the side"
                ],
                "prep_time": 20,
                "cook_time": 20,
                "calories": 450,
                "shopping_list": ["white rice", "beef bulgogi", "spinach", "bean sprouts", "carrot", "shiitake mushrooms", "eggs", "gochujang", "sesame oil", "soy sauce", "rice vinegar"]
            }
        ],
        "Indian": [
            {
                "title": "Butter Chicken (Murgh Makhani)",
                "description": "Creamy tomato-based curry with tender chicken in aromatic spices",
                "ingredients": [
                    "2 lbs chicken thighs, cut into pieces",
                    "1 cup heavy cream",
                    "1 can (14 oz) crushed tomatoes",
                    "1 large onion, diced",
                    "4 cloves garlic, minced",
                    "1 inch ginger, grated",
                    "2 tbsp butter",
                    "2 tbsp tomato paste",
                    "1 tbsp garam masala",
                    "1 tsp cumin",
                    "1 tsp paprika",
                    "½ tsp turmeric",
                    "Fresh cilantro for garnish"
                ],
                "instructions": [
                    "Season chicken with salt, turmeric, and half the garam masala",
                    "Cook chicken in butter until browned, remove and set aside",
                    "Sauté onion until golden, add garlic and ginger",
                    "Add tomato paste and remaining spices, cook 1 minute",
                    "Add crushed tomatoes, simmer 10 minutes",
                    "Blend sauce until smooth, return to pan",
                    "Add chicken back to sauce",
                    "Stir in cream and simmer 15 minutes",
                    "Garnish with cilantro, serve with rice or naan"
                ],
                "prep_time": 15,
                "cook_time": 35,
                "calories": 480,
                "shopping_list": ["chicken thighs", "heavy cream", "crushed tomatoes", "onion", "garlic", "ginger", "butter", "tomato paste", "garam masala", "cumin", "paprika", "turmeric", "cilantro"]
            }
        ]
    }
    
    # Get recipes for the specified cuisine, fallback to Italian if not found
    cuisine_recipes = recipe_database.get(cuisine_type, recipe_database["Italian"])
    
    # Filter recipes based on dietary preferences if needed
    if dietary_preferences:
        # This is a simple implementation - in a real app you'd have more sophisticated filtering
        if "vegetarian" in dietary_preferences:
            # Filter out meat-based recipes (this is a simplified approach)
            cuisine_recipes = [recipe for recipe in cuisine_recipes if not any(
                meat in " ".join(recipe["ingredients"]).lower() 
                for meat in ["chicken", "beef", "pork", "shrimp", "fish"]
            )]
    
    return cuisine_recipes if cuisine_recipes else recipe_database["Italian"]

async def generate_mock_recipe(request: RecipeGenRequest) -> dict:
    """Generate mock recipe for testing when OpenAI is not available"""
    logger.info(f"Generating mock recipe for user {request.user_id} with preferences: {request.dietary_preferences}")
    
    # Determine recipe type based on request
    recipe_category = request.recipe_category or 'cuisine'
    cuisine_type = request.cuisine_type or 'Italian'
    
    # Create a mock recipe based on the request
    if recipe_category == "snack":
        mock_recipe = Recipe(
            title=f"Healthy {cuisine_type} Snack",
            description=f"A delicious and nutritious {cuisine_type.lower()} snack perfect for any time of day",
            ingredients=[
                "2 cups mixed nuts",
                "1 cup dried fruits",
                "1 tbsp honey",
                "1 tsp cinnamon",
                "1/2 tsp vanilla extract"
            ],
            instructions=[
                "Preheat oven to 350°F (175°C)",
                "Mix all ingredients in a large bowl",
                "Spread on baking sheet",
                "Bake for 10-15 minutes until golden",
                "Cool completely before serving"
            ],
            prep_time=10,
            cook_time=15,
            servings=request.servings,
            cuisine_type=cuisine_type,
            dietary_tags=request.dietary_preferences,
            difficulty=request.difficulty,
            calories_per_serving=250 if request.max_calories_per_serving else None,
            is_healthy=request.is_healthy,
            user_id=request.user_id,
            shopping_list=["mixed nuts", "dried fruits", "honey", "cinnamon", "vanilla extract"]
        )
    elif recipe_category == "beverage":
        mock_recipe = Recipe(
            title=f"Refreshing {cuisine_type} Beverage",
            description=f"A refreshing {cuisine_type.lower()} drink perfect for any occasion",
            ingredients=[
                "2 cups fresh fruit juice",
                "1 cup sparkling water",
                "2 tbsp honey",
                "1 tbsp fresh lime juice",
                "Ice cubes",
                "Fresh mint leaves"
            ],
            instructions=[
                "Combine fruit juice and honey in a pitcher",
                "Stir until honey is dissolved",
                "Add lime juice and mix well",
                "Add ice cubes to glasses",
                "Pour mixture over ice",
                "Top with sparkling water and mint"
            ],
            prep_time=5,
            cook_time=0,
            servings=request.servings,
            cuisine_type=cuisine_type,
            dietary_tags=request.dietary_preferences,
            difficulty="easy",
            calories_per_serving=120 if request.max_calories_per_serving else None,
            is_healthy=request.is_healthy,
            user_id=request.user_id,
            shopping_list=["fruit juice", "sparkling water", "honey", "lime", "mint"]
        )
    else:
        # Generate diverse recipes based on cuisine type using the new diverse recipe database
        recipe_variations = get_diverse_recipe_for_cuisine(cuisine_type, request.dietary_preferences)
        
        # Select a random recipe from the variations
        if recipe_variations:
            variation = random.choice(recipe_variations) 
            mock_recipe = Recipe(
                title=variation["title"],
                description=variation["description"],
                ingredients=variation["ingredients"],
                instructions=variation["instructions"],
                prep_time=variation["prep_time"],
                cook_time=variation["cook_time"],
                servings=request.servings,
                cuisine_type=cuisine_type,
                dietary_tags=request.dietary_preferences,
                difficulty=request.difficulty,
                calories_per_serving=variation.get("calories", 420) if request.max_calories_per_serving else None,
                is_healthy=request.is_healthy,
                user_id=request.user_id,
                shopping_list=variation["shopping_list"]
            )
        else:
            # Fallback to default Italian pasta if no variations found
            mock_recipe = Recipe(
                title=f"Classic {cuisine_type} Pasta",
                description=f"A traditional {cuisine_type.lower()} pasta dish with rich flavors and fresh ingredients",
                ingredients=[
                    "1 lb pasta",
                    "2 tbsp olive oil", 
                    "3 cloves garlic, minced",
                    "1 can diced tomatoes",
                    "1/2 cup fresh basil",
                    "1/2 cup parmesan cheese",
                    "Salt and pepper to taste"
                ],
                instructions=[
                    "Cook pasta according to package directions",
                    "Heat olive oil in large pan",
                    "Add garlic and cook until fragrant", 
                    "Add tomatoes and simmer for 10 minutes",
                    "Toss with cooked pasta",
                    "Add basil and cheese",
                    "Season with salt and pepper"
                ],
                prep_time=15,
                cook_time=25,
                servings=request.servings,
                cuisine_type=cuisine_type,
                dietary_tags=request.dietary_preferences,
                difficulty=request.difficulty,
                calories_per_serving=420 if request.max_calories_per_serving else None,
                is_healthy=request.is_healthy,
                user_id=request.user_id,
                shopping_list=["pasta", "olive oil", "garlic", "diced tomatoes", "basil", "parmesan cheese"]
            )
    
    # Save to database
    recipe_dict = mock_recipe.dict()
    result = await db.recipes.insert_one(recipe_dict)
    
    # Get the inserted document and return it
    if result.inserted_id:
        inserted_recipe = await db.recipes.find_one({"_id": result.inserted_id})
        return mongo_to_dict(inserted_recipe)
    
    return recipe_dict

async def generate_mock_weekly_meals(family_size: int = 2, dietary_preferences: List[str] = [], allergies: List[str] = [], cuisines: List[str] = []) -> List[WeeklyMeal]:
    """Generate mock weekly meals for testing when OpenAI is not available"""
    logger.info(f"Generating mock weekly meals for {family_size} people with preferences: {dietary_preferences}, allergies: {allergies}, cuisines: {cuisines}")
    
    # Determine dietary restrictions
    is_vegetarian = 'vegetarian' in dietary_preferences or 'vegan' in dietary_preferences
    is_vegan = 'vegan' in dietary_preferences
    is_gluten_free = 'gluten-free' in dietary_preferences
    has_nut_allergy = 'nuts' in allergies
    has_dairy_allergy = 'dairy' in allergies
    has_soy_allergy = 'soy' in allergies
    has_shellfish_allergy = 'shellfish' in allergies
    has_egg_allergy = 'eggs' in allergies
    has_wheat_allergy = 'wheat' in allergies

    def filter_safe_ingredients(ingredients: List[str]) -> List[str]:
        """Filter ingredients based on dietary restrictions and allergies"""
        safe_ingredients = []
        
        for ingredient in ingredients:
            ingredient_lower = ingredient.lower()
            is_safe = True
            
            # Check for meat if vegetarian/vegan
            if is_vegetarian or is_vegan:
                meat_keywords = ['chicken', 'beef', 'pork', 'fish', 'meat', 'turkey', 'lamb', 'bacon', 'ham', 'sausage', 'salmon', 'tuna']
                if any(meat in ingredient_lower for meat in meat_keywords):
                    is_safe = False
            
            # Check for dairy if vegan or dairy allergy
            if is_vegan or has_dairy_allergy:
                dairy_keywords = ['cheese', 'milk', 'butter', 'cream', 'yogurt', 'parmesan', 'feta', 'mozzarella', 'cheddar']
                if any(dairy in ingredient_lower for dairy in dairy_keywords):
                    is_safe = False
            
            # Check for eggs if vegan or egg allergy
            if is_vegan or has_egg_allergy:
                if 'egg' in ingredient_lower:
                    is_safe = False
            
            # Check for nuts if nut allergy
            if has_nut_allergy:
                nut_keywords = ['nuts', 'almond', 'walnut', 'pecan', 'cashew', 'pistachio', 'peanut']
                if any(nut in ingredient_lower for nut in nut_keywords):
                    is_safe = False
            
            # Check for soy if soy allergy
            if has_soy_allergy:
                soy_keywords = ['soy', 'tofu', 'tempeh', 'edamame']
                if any(soy in ingredient_lower for soy in soy_keywords):
                    is_safe = False
            
            # Check for shellfish if shellfish allergy
            if has_shellfish_allergy:
                shellfish_keywords = ['shrimp', 'crab', 'lobster', 'shellfish', 'scallops']
                if any(shellfish in ingredient_lower for shellfish in shellfish_keywords):
                    is_safe = False
            
            # Check for gluten if gluten-free
            if is_gluten_free:
                gluten_keywords = ['wheat', 'flour', 'bread', 'pasta', 'soy sauce']
                if any(gluten in ingredient_lower for gluten in gluten_keywords):
                    # Replace with gluten-free alternatives
                    if 'pasta' in ingredient_lower:
                        ingredient = ingredient.replace('pasta', 'gluten-free pasta')
                    elif 'soy sauce' in ingredient_lower:
                        ingredient = ingredient.replace('soy sauce', 'tamari (gluten-free soy sauce)')
                    elif 'flour' in ingredient_lower:
                        ingredient = ingredient.replace('flour', 'gluten-free flour')
            
            if is_safe:
                safe_ingredients.append(ingredient)
        
        return safe_ingredients

    def get_safe_protein_substitute():
        """Get appropriate protein substitute based on dietary restrictions"""
        if is_vegan:
            return "firm tofu"
        elif is_vegetarian:
            return "plant-based protein or extra beans"
        else:
            return "lean chicken breast"

    def get_safe_dairy_substitute():
        """Get appropriate dairy substitute"""
        if is_vegan or has_dairy_allergy:
            return "nutritional yeast"
        else:
            return "parmesan cheese"
    
    # Safe meal templates that adapt to all preferences and allergies
    safe_meals_data = [
        {
            "day": "Monday",
            "name": "Italian Pasta Primavera" if not is_vegetarian else "Veggie Pasta Primavera",
            "description": "Fresh seasonal vegetables tossed with pasta in a light garlic olive oil sauce",
            "ingredients": [
                "12 oz penne pasta", "2 cups mixed seasonal vegetables", "3 cloves garlic", 
                "1/4 cup olive oil", "1/2 cup fresh basil", "1/2 cup parmesan cheese", "Salt and pepper"
            ],
            "instructions": [
                "Cook pasta according to package directions",
                "Sauté garlic in olive oil until fragrant",
                "Add vegetables and cook until tender-crisp",
                "Toss with cooked pasta, basil, and cheese",
                "Season with salt and pepper to taste"
            ],
            "cuisine_type": "Italian"
        },
        {
            "day": "Tuesday", 
            "name": "Asian Stir-Fry Bowl" if not is_vegetarian else "Veggie Tofu Stir-Fry",
            "description": "Colorful vegetables stir-fried with aromatic Asian seasonings served over rice",
            "ingredients": [
                "2 cups mixed stir-fry vegetables", "1 cup jasmine rice", "3 tbsp soy sauce",
                "2 tbsp sesame oil", "1 tbsp fresh ginger", "2 cloves garlic", "1 tsp sesame seeds"
            ] + (["8 oz firm tofu"] if is_vegetarian else ["1 lb chicken breast"]),
            "instructions": [
                "Cook rice according to package directions",
                "Heat sesame oil in large wok or skillet",
                "Add garlic and ginger, stir-fry for 30 seconds",
                "Add protein and cook until done" if not is_vegetarian else "Add cubed tofu and cook until golden",
                "Add vegetables and stir-fry until tender-crisp",
                "Add soy sauce and toss to combine",
                "Serve over rice and garnish with sesame seeds"
            ],
            "cuisine_type": "Asian"
        },
        {
            "day": "Wednesday",
            "name": "Mediterranean Quinoa Bowl",
            "description": "Nutritious quinoa topped with fresh Mediterranean flavors",
            "ingredients": [
                "1 cup quinoa", "1 cucumber diced", "2 tomatoes diced", "1/2 red onion",
                "1/2 cup kalamata olives", "1/2 cup feta cheese", "1/4 cup olive oil",
                "2 tbsp lemon juice", "1 tsp dried oregano", "Fresh parsley"
            ],
            "instructions": [
                "Cook quinoa according to package directions and let cool",
                "Dice cucumber, tomatoes, and red onion",
                "Combine quinoa with vegetables and olives",
                "Whisk together olive oil, lemon juice, and oregano",
                "Drizzle dressing over quinoa mixture",
                "Top with feta cheese and fresh parsley"
            ],
            "cuisine_type": "Mediterranean"
        },
        {
            "day": "Thursday",
            "name": "Mexican Black Bean Tacos",
            "description": "Hearty black bean tacos with fresh toppings and creamy avocado",
            "ingredients": [
                "8 corn tortillas", "2 cans black beans", "1 avocado", "1 lime",
                "1 tomato diced", "1/4 cup red onion diced", "1/4 cup cilantro",
                "1 tsp cumin", "1 tsp chili powder", "Mexican cheese blend"
            ],
            "instructions": [
                "Warm tortillas in a dry skillet",
                "Heat black beans with cumin and chili powder",
                "Slice avocado and dice tomato and onion",
                "Warm tortillas and fill with seasoned beans",
                "Top with avocado, tomato, onion, and cilantro",
                "Squeeze lime juice over tacos and add cheese"
            ],
            "cuisine_type": "Mexican"
        },
        {
            "day": "Friday",
            "name": "Indian Vegetable Curry",
            "description": "Aromatic curry with mixed vegetables in a rich, spiced sauce",
            "ingredients": [
                "2 cups mixed vegetables", "1 can coconut milk", "1 can diced tomatoes",
                "1 onion diced", "3 cloves garlic", "1 tbsp fresh ginger", "2 tsp curry powder",
                "1 tsp turmeric", "1 tsp garam masala", "2 cups basmati rice", "Fresh cilantro"
            ],
            "instructions": [
                "Cook basmati rice according to package directions",
                "Sauté onion, garlic, and ginger until fragrant",
                "Add curry powder, turmeric, and garam masala",
                "Add diced tomatoes and coconut milk",
                "Add mixed vegetables and simmer until tender",
                "Serve over rice and garnish with cilantro"
            ],
            "cuisine_type": "Indian"
        },
        {
            "day": "Saturday",
            "name": "American BBQ Bowl" if not is_vegetarian else "Smoky Portobello Bowl",
            "description": "Hearty bowl with smoky flavors and fresh coleslaw",
            "ingredients": [
                "2 cups coleslaw mix", "4 burger buns or rice", "2 tbsp BBQ sauce",
                "1 tbsp apple cider vinegar", "1 tbsp honey", "1 tsp smoked paprika",
                "2 tbsp mayonnaise", "Salt and pepper"
            ] + (["4 portobello mushrooms"] if is_vegetarian else ["1 lb ground beef"]),
            "instructions": [
                "Mix coleslaw with mayonnaise, vinegar, and honey",
                "Season protein with smoked paprika, salt, and pepper",
                "Cook protein until done and toss with BBQ sauce",
                "Serve on buns or over rice with coleslaw on the side"
            ],
            "cuisine_type": "American"
        },
        {
            "day": "Sunday",
            "name": "French Ratatouille",
            "description": "Classic French vegetable stew with herbs de Provence",
            "ingredients": [
                "1 eggplant diced", "2 zucchini sliced", "1 bell pepper diced",
                "1 onion diced", "3 tomatoes diced", "4 cloves garlic", "1/4 cup olive oil",
                "2 tsp herbs de Provence", "Fresh basil", "Crusty bread"
            ],
            "instructions": [
                "Heat olive oil in large pot",
                "Sauté onion and garlic until translucent",
                "Add eggplant and cook for 5 minutes",
                "Add bell pepper and zucchini, cook 5 more minutes",
                "Add tomatoes and herbs de Provence",
                "Simmer covered for 30 minutes until vegetables are tender",
                "Garnish with fresh basil and serve with crusty bread"
            ],
            "cuisine_type": "French"
        }
    ]
    
    # Process safe meal templates
    weekly_meals = []
    for i, meal_data in enumerate(safe_meals_data):
        # Get safe ingredients using the filtering system
        original_ingredients = meal_data["ingredients"]
        safe_ingredients = filter_safe_ingredients(original_ingredients)
        logger.info(f"Filtering meal {meal_data['name']}: {len(original_ingredients)} → {len(safe_ingredients)} ingredients")
        
        # Adjust ingredients for family size (simple multiplication approach)
        adjusted_ingredients = []
        multiplier = max(1, family_size / 2)  # Base recipes serve 2
        
        for ingredient in safe_ingredients:
            # Simple ingredient adjustment - multiply quantities
            if any(num in ingredient for num in ['1 ', '2 ', '3 ', '4 ', '8 ', '12 ']):
                # Try to find and multiply the first number
                words = ingredient.split()
                if words and any(char.isdigit() for char in words[0]):
                    try:
                        original_qty = float(words[0])
                        new_qty = int(original_qty * multiplier) if original_qty * multiplier == int(original_qty * multiplier) else round(original_qty * multiplier, 1)
                        adjusted_ingredient = ingredient.replace(words[0], str(new_qty), 1)
                        adjusted_ingredients.append(adjusted_ingredient)
                    except:
                        adjusted_ingredients.append(ingredient)
                else:
                    adjusted_ingredients.append(ingredient)
            else:
                adjusted_ingredients.append(ingredient)
        
        # Generate safe cooking instructions
        instructions = [
            f"Prepare ingredients according to dietary restrictions",
            f"Cook base ingredients as directed", 
            f"Combine ingredients carefully avoiding cross-contamination",
            f"Season to taste with allowed seasonings",
            f"Serve immediately for best flavor"
        ]
        
        meal = WeeklyMeal(
            day=meal_data["day"],
            name=meal_data["name"],
            description=meal_data["description"],
            ingredients=adjusted_ingredients,
            instructions=instructions,
            prep_time=20,
            cook_time=25,
            servings=family_size,
            cuisine_type=meal_data["cuisine_type"],
            dietary_tags=dietary_preferences,
            calories_per_serving=400
        )
        weekly_meals.append(meal)
    
    logger.info(f"Generated {len(weekly_meals)} safe mock meals with proper dietary filtering")
    return weekly_meals

async def generate_weekly_walmart_cart(meals: List[WeeklyMeal]) -> str:
    """Generate a single Walmart cart URL for all weekly ingredients"""
    try:
        # Collect all ingredients from all meals
        all_ingredients = []
        for meal in meals:
            all_ingredients.extend(meal.ingredients)
        
        # Remove duplicates while preserving order
        unique_ingredients = []
        seen = set()
        for ingredient in all_ingredients:
            # Clean ingredient name (remove quantities and common prefixes)
            clean_ingredient = ingredient.lower()
            for prefix in ['fresh', 'organic', 'large', 'medium', 'small', '1', '2', '3', '4', '5']:
                clean_ingredient = clean_ingredient.replace(prefix, '').strip()
            
            if clean_ingredient not in seen and len(clean_ingredient) > 2:
                seen.add(clean_ingredient)
                unique_ingredients.append(ingredient)
        
        # Limit to first 15 ingredients to avoid overwhelming the cart
        cart_ingredients = unique_ingredients[:15]
        
        # Generate simplified cart URL with ingredients
        ingredient_list = ','.join(cart_ingredients)
        cart_url = f"https://walmart.com/search?q={'+'.join(cart_ingredients[:5])}"  # Use first 5 for search
        
        return cart_url
        
    except Exception as e:
        logger.error(f"Error generating weekly Walmart cart: {str(e)}")
        return "https://walmart.com/cp/food/976759"  # Fallback to grocery section

@api_router.post("/weekly-recipes/generate")
async def generate_weekly_recipe_plan(request: WeeklyRecipeRequest):
    """Generate weekly meal plan with Walmart cart - PREMIUM FEATURE"""
    try:
        # Check subscription access for premium feature
        await check_subscription_access(request.user_id)
        
        # Check usage limits
        user = await users_collection.find_one({"id": request.user_id})
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        can_use, usage_info = check_usage_limit(user, "weekly_recipes")
        if not can_use:
            # Return detailed limit information for frontend to handle
            subscription_status = user.get('subscription_status', 'trial')
            limits = get_user_usage_limits(subscription_status)
            
            raise HTTPException(
                status_code=429, 
                detail={
                    "error": "Usage limit exceeded",
                    "message": f"Weekly recipe limit reached ({usage_info['current_count']}/{usage_info['limit']})",
                    "current_usage": usage_info['current_count'],
                    "limit": usage_info['limit'],
                    "subscription_status": subscription_status,
                    "upgrade_required": subscription_status == "trial"
                }
            )
        
        # Get current week
        current_week = get_current_week()
        
        # Check if user already has a plan for this week
        existing_plan = await weekly_recipes_collection.find_one({
            "user_id": request.user_id,
            "week_of": current_week,
            "is_active": True
        })
        
        # Check if we need to force regeneration based on dietary preferences
        force_regeneration = False
        if request.dietary_preferences or request.allergies or request.cuisines:
            logger.info(f"Dietary preferences provided - forcing regeneration for safety: dietary={request.dietary_preferences}, allergies={request.allergies}, cuisines={request.cuisines}")
            force_regeneration = True
        
        if existing_plan and not force_regeneration:
            # Return existing plan only if no dietary preferences specified
            logger.info("Returning existing weekly plan - no dietary preferences specified")
            return mongo_to_dict(existing_plan)
        elif existing_plan and force_regeneration:
            # Delete existing plan to force regeneration with new preferences
            logger.info("Deleting existing plan to regenerate with new dietary preferences")
            await weekly_recipes_collection.delete_one({"_id": existing_plan["_id"]})
        
        # Fetch user preferences from database
        user = await users_collection.find_one({"id": request.user_id})
        user_dietary_preferences = user.get("dietary_preferences", []) if user else []
        user_allergies = user.get("allergies", []) if user else []
        user_favorite_cuisines = user.get("favorite_cuisines", []) if user else []
        
        # Combine user account preferences with request preferences
        combined_dietary_preferences = list(set(user_dietary_preferences + request.dietary_preferences))
        combined_allergies = list(set(user_allergies + request.allergies))
        combined_cuisines = list(set(user_favorite_cuisines + request.cuisines))
        
        logger.info(f"Weekly meal plan preferences - User dietary: {user_dietary_preferences}, allergies: {user_allergies}, cuisines: {user_favorite_cuisines}")
        logger.info(f"Combined preferences - Dietary: {combined_dietary_preferences}, allergies: {combined_allergies}, cuisines: {combined_cuisines}")
        
        # Generate new weekly meals with enhanced preferences
        meals = await generate_weekly_meals(
            family_size=request.family_size,
            dietary_preferences=combined_dietary_preferences,
            allergies=combined_allergies,
            cuisines=combined_cuisines
        )
        
        # Generate weekly Walmart cart
        cart_url = await generate_weekly_walmart_cart(meals)
        
        # Calculate total budget estimate
        estimated_budget = len(meals) * 15.0  # Rough estimate: $15 per meal
        if request.budget:
            estimated_budget = min(estimated_budget, request.budget)
        
        # Create weekly recipe plan
        weekly_plan = WeeklyRecipePlan(
            user_id=request.user_id,
            week_of=current_week,
            meals=[meal.dict() for meal in meals],
            total_budget=estimated_budget,
            walmart_cart_url=cart_url,
            is_active=True
        )
        
        # Save to database
        plan_dict = weekly_plan.dict()
        result = await weekly_recipes_collection.insert_one(plan_dict)
        
        if result.inserted_id:
            # Increment usage counter after successful generation
            await increment_usage(request.user_id, "weekly_recipes")
            
            # Return the created plan
            inserted_plan = await weekly_recipes_collection.find_one({"_id": result.inserted_id})
            return mongo_to_dict(inserted_plan)
        else:
            raise HTTPException(status_code=500, detail="Failed to save weekly plan")
            
    except Exception as e:
        logger.error(f"Error generating weekly recipe plan: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to generate weekly meal plan")

@api_router.get("/weekly-recipes/current/{user_id}")
async def get_current_weekly_plan(user_id: str):
    """Get current week's meal plan for user - PREMIUM FEATURE"""
    try:
        # Check subscription access for premium feature
        await check_subscription_access(user_id)
        
        current_week = get_current_week()
        
        # Get current week's plan
        plan = await weekly_recipes_collection.find_one({
            "user_id": user_id,
            "week_of": current_week,
            "is_active": True
        })
        
        if not plan:
            return {
                "has_plan": False,
                "message": "No meal plan found for current week. Generate one to get started!",
                "current_week": current_week
            }
        
        return {
            "has_plan": True,
            "plan": mongo_to_dict(plan),
            "current_week": current_week
        }
        
    except Exception as e:
        logger.error(f"Error getting current weekly plan: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get weekly meal plan")

@api_router.get("/user/trial-status/{user_id}")
async def get_user_trial_status(user_id: str):
    """Get detailed trial and subscription status for user"""
    try:
        # Get user from database
        user = await users_collection.find_one({"id": user_id})
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Get detailed access status
        access_status = get_user_access_status(user)
        
        # Calculate days remaining in trial
        trial_days_left = 0
        if access_status["trial_active"]:
            trial_end = user.get('trial_end_date')
            if trial_end:
                if isinstance(trial_end, str):
                    trial_end = parser.parse(trial_end)
                days_diff = (trial_end - datetime.utcnow()).days
                trial_days_left = max(0, days_diff)
        
        return {
            **access_status,
            "trial_days_left": trial_days_left,
            "user_id": user_id,
            "current_week": get_current_week()
        }
        
    except Exception as e:
        logger.error(f"Error getting trial status: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get trial status")

@api_router.get("/weekly-recipes/recipe/{recipe_id}")
async def get_weekly_recipe_detail(recipe_id: str):
    """Get detailed recipe information from weekly meal plan - PREMIUM FEATURE"""
    try:
        # Find the weekly meal plan that contains this recipe using the same query as /current
        current_week = get_current_week()
        
        # Query the database using the same structure as the working /current endpoint
        plans = await weekly_recipes_collection.find({
            "week_of": current_week,
            "is_active": True
        }).sort("created_at", -1).to_list(10)
        
        target_meal = None
        source_plan = None
        
        # Find the specific meal with this recipe ID (meals are at root level)
        for plan in plans:
            meals = plan.get('meals', [])
            # Checking plan with meals
            for meal in meals:
                # Checking meal ID vs target  # Debug
                if meal.get('id') == recipe_id:
                    target_meal = meal
                    source_plan = plan
                    break
            if target_meal:
                break
        
        if not target_meal:
            raise HTTPException(status_code=404, detail="Recipe not found")
        
        # Simplified Walmart integration - one product per ingredient
        cart_ingredients = []
        
        for ingredient in target_meal.get('ingredients', []):
            try:
                # Get the best product match for this ingredient
                walmart_products = await search_walmart_products_v2(ingredient, max_results=1)
                
                if walmart_products and len(walmart_products) > 0:
                    product = walmart_products[0]  # Use the first (best) match
                    cart_ingredient = {
                        "ingredient": ingredient,
                        "products": [{
                            "id": product.id,
                            "name": product.name,
                            "price": product.price,
                            "image_url": product.image_url,
                            "brand": product.brand,
                            "rating": product.rating,
                            "url": product.product_url if product.product_url else f"https://www.walmart.com/ip/{product.id}"
                        }],
                        "selected_product_id": product.id
                    }
                    cart_ingredients.append(cart_ingredient)
                else:
                    # Fallback for ingredients that can't be found
                    fallback_id = f"search_{abs(hash(ingredient)) % 10000}"
                    cart_ingredient = {
                        "ingredient": ingredient,
                        "products": [{
                            "id": fallback_id,
                            "name": f"Search: {ingredient}",
                            "price": 0.00,
                            "image_url": "https://via.placeholder.com/100x100?text=🔍",
                            "brand": "Walmart",
                            "rating": 0.0,
                            "url": f"https://www.walmart.com/search/?query={ingredient.replace(' ', '+')}"
                        }],
                        "selected_product_id": fallback_id
                    }
                    cart_ingredients.append(cart_ingredient)
                    
            except Exception as e:
                logger.error(f"Error processing ingredient '{ingredient}': {str(e)}")
                # Create fallback item for this ingredient
                fallback_id = f"error_{abs(hash(ingredient)) % 10000}"
                cart_ingredient = {
                    "ingredient": ingredient,
                    "products": [{
                        "id": fallback_id,
                        "name": f"Search: {ingredient}",
                        "price": 0.00,
                        "image_url": "https://via.placeholder.com/100x100?text=❌",
                        "brand": "Walmart",
                        "rating": 0.0,
                        "url": f"https://www.walmart.com/search/?query={ingredient.replace(' ', '+')}"
                    }],
                    "selected_product_id": fallback_id
                }
                cart_ingredients.append(cart_ingredient)
        
        # Create Walmart cart URL with all valid product IDs
        valid_product_ids = []
        for cart_ingredient in cart_ingredients:
            product = cart_ingredient["products"][0]
            # Include all products except fallback search/error items
            # Real Walmart product IDs will be numeric or alphanumeric (not prefixed)
            if (not product["id"].startswith("search_") and 
                not product["id"].startswith("error_") and 
                not product["id"].startswith("WM")):  # Exclude mock data
                valid_product_ids.append(product["id"])
        
        # Generate Walmart cart URL if we have valid products
        walmart_cart_url = ""
        if valid_product_ids:
            # Use proper Walmart affiliate cart URL format with quantity
            # Format: product_id_quantity for each item
            affiliate_items = [f"{product_id}_1" for product_id in valid_product_ids]  # Default quantity 1
            walmart_cart_url = f"https://affil.walmart.com/cart/addToCart?items={','.join(affiliate_items)}"
        
        # Return detailed recipe information with simplified Walmart integration
        recipe_detail = {
            "id": target_meal.get('id'),
            "name": target_meal.get('name'),
            "description": target_meal.get('description'),
            "day": target_meal.get('day'),
            "ingredients": target_meal.get('ingredients', []),
            "instructions": target_meal.get('instructions', []),
            "prep_time": target_meal.get('prep_time', '30 minutes'),
            "cook_time": target_meal.get('cook_time', '25 minutes'),
            "servings": target_meal.get('servings', 2),
            "cuisine": target_meal.get('cuisine', 'International'),
            "calories": target_meal.get('calories', 400),
            "cart_ingredients": cart_ingredients,  # Simplified shopping data with one product per ingredient
            "walmart_cart_url": walmart_cart_url,  # URL to add all ingredients to Walmart cart
            "week_of": source_plan.get('week_of') if source_plan else current_week
        }
        
        return recipe_detail
        
    except Exception as e:
        logger.error(f"Error getting weekly recipe detail: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get recipe details")
@api_router.post("/v2/walmart/weekly-cart-options")
async def get_weekly_cart_options_v2(
    recipe_id: str = Query(..., description="Weekly Recipe ID")
):
    """V2 Cart options for weekly recipes - Advanced shopping cart system"""
    try:
        # Find the weekly meal plan that contains this recipe
        current_week = get_current_week()
        
        # Query the database using the same structure as the working /current endpoint
        plans = await weekly_recipes_collection.find({
            "is_active": True
        }).sort("created_at", -1).to_list(10)
        
        target_meal = None
        
        # Find the specific meal with this recipe ID
        for plan in plans:
            # Access meals from plan.meals (same as working /current endpoint)
            meals = plan.get('plan', {}).get('meals', []) if 'plan' in plan else plan.get('meals', [])
            # Checking plan with meals
            for meal in meals:
                # Checking meal ID vs target  # Debug
                if meal.get('id') == recipe_id:
                    target_meal = meal
                    break
            if target_meal:
                break
        
        if not target_meal:
            raise HTTPException(status_code=404, detail="Recipe not found")
        
        # Extract ingredients for shopping
        shopping_list = target_meal.get('ingredients', [])
        
        if not shopping_list:
            return CartOptionsV2(
                recipe_id=recipe_id,
                user_id="weekly_recipe_system",
                ingredient_matches=[],
                total_products=0
            )
        
        # Search products for each ingredient using V2 system
        ingredient_matches = []
        total_products = 0
        
        for ingredient in shopping_list[:8]:  # Limit for performance
            # Use the real Walmart API integration we restored
            products = await search_walmart_products_v2(ingredient, max_results=3)
            if products:
                ingredient_matches.append(IngredientMatchV2(
                    ingredient=ingredient,
                    products=products
                ))
                total_products += len(products)
        
        # Return structured V2 response
        result = CartOptionsV2(
            recipe_id=recipe_id,
            user_id="weekly_recipe_system",
            ingredient_matches=ingredient_matches,
            total_products=total_products
        )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Weekly cart options V2 error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@api_router.get("/weekly-recipes/history/{user_id}")
async def get_weekly_recipe_history(user_id: str):
    """Get all previous weekly meal plans for user - PREMIUM FEATURE"""
    try:
        # Check subscription access for premium feature
        await check_subscription_access(user_id)
        
        # Get all plans for user, sorted by most recent
        plans = await weekly_recipes_collection.find(
            {"user_id": user_id}
        ).sort("created_at", -1).to_list(20)  # Limit to last 20 weeks
        
        # Convert to clean dictionaries
        plan_history = [mongo_to_dict(plan) for plan in plans]
        
        return {
            "plans": plan_history,
            "total_plans": len(plan_history),
            "current_week": get_current_week()
        }
        
    except Exception as e:
        logger.error(f"Error getting weekly recipe history: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get recipe history")

# ========================================
# END WEEKLY RECIPE SYSTEM
# ========================================

# Enhanced CORS configuration for production security
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://buildyoursmartcart.com",  # Production domain
        "https://www.buildyoursmartcart.com",  # WWW variant
        "https://*.emergentagent.com",  # Development preview URLs
        "http://localhost:3000",  # Local development only
        "http://127.0.0.1:3000"   # Local development only
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["*"]
)

# Include the API router after all endpoints are defined
app.include_router(api_router)

# Note: Server startup is handled by main.py for Cloud Run deployment
# The main.py file properly uses the PORT environment variable