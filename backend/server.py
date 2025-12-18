"""
buildyoursmartcart.com FastAPI Backend
AI Recipe + Grocery Delivery App - Weekly Meal Planning & Walmart Integration
"""

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Tuple, Union
import os
import logging
import uuid
import json
from datetime import datetime, timedelta
from pathlib import Path
from dotenv import load_dotenv
from urllib.parse import urlencode, quote
import random
import re
import httpx
import asyncio
import base64
import hmac
import hashlib
import time

# Configure logging FIRST
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add cryptography imports for proper RSA signing
try:
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import padding
    from cryptography.hazmat.backends import default_backend
    CRYPTOGRAPHY_AVAILABLE = True
except ImportError:
    CRYPTOGRAPHY_AVAILABLE = False
    logger.error("❌ cryptography library not installed - Walmart API will not work")

# Database imports
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId
from pymongo import ASCENDING, DESCENDING

# Email service imports
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# OpenAI imports
from openai import OpenAI

# Stripe imports
import stripe

# Load environment variables from .env file for local development
try:
    load_dotenv()
    logger.info("🔑 Loaded environment variables from .env file")
except Exception as e:
    logger.warning(f"⚠️ Could not load .env file: {e}")
    logger.info("🔑 Using system environment variables only")

# Initialize FastAPI app
app = FastAPI(
    title="buildyoursmartcart.com API",
    description="AI Recipe + Grocery Delivery App - Weekly Meal Planning & Walmart Integration",
    version="2.2.1",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware - properly configured for CORS preflight
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:8080", "http://127.0.0.1:3000"],  # Allow both localhost and 127.0.0.1
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "Accept", "Origin", "User-Agent", "X-Requested-With"],
    expose_headers=["*"]
)

# Global OPTIONS handler for CORS preflight - must be defined BEFORE other routes
@app.options("/{full_path:path}")
async def options_handler(full_path: str):
    """Handle all OPTIONS requests for CORS preflight"""
    return JSONResponse(
        status_code=200,
        content={"message": "OK"},
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type, Authorization, Accept, Origin, User-Agent, X-Requested-With",
            "Access-Control-Max-Age": "86400"
        }
    )

# MongoDB setup with validation
mongo_url = os.environ.get('MONGO_URL')
db_name = os.environ.get('DB_NAME')

if not mongo_url:
    if os.getenv("NODE_ENV") == "production":
        logger.error("❌ MONGO_URL environment variable is required in production")
        raise ValueError("MONGO_URL environment variable is required in production")
    else:
        mongo_url = 'mongodb://localhost:27017'
        logger.warning("⚠️ MONGO_URL not set, using localhost default for development")

if not db_name:
    logger.error("❌ DB_NAME environment variable is required")
    raise ValueError("DB_NAME environment variable is required")

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

# External API setup - only from environment variables
openai_client = None
openai_api_key = os.environ.get('OPENAI_API_KEY')

logger.info(f"🔑 OpenAI API Key present in environment: {bool(openai_api_key)}")

if (openai_api_key and not any(placeholder in openai_api_key for placeholder in ['your-', 'placeholder', 'here'])):
    try:
        openai_client = OpenAI(api_key=openai_api_key)
        logger.info("✅ OpenAI client initialized from environment variables")
    except Exception as e:
        logger.error(f"❌ Failed to initialize OpenAI client: {e}")
        openai_client = None
else:
    logger.warning("⚠️ OpenAI API key not found in environment variables")

# Stripe setup
stripe_secret_key = os.environ.get('STRIPE_SECRET_KEY')
stripe_publisher_key = os.environ.get('STRIPE_PUBLISHER_API_KEY')

if stripe_secret_key and not any(placeholder in stripe_secret_key for placeholder in ['your-', 'placeholder', 'here']):
    stripe.api_key = stripe_secret_key

# Email service setup with validation
mailjet_api_key = os.environ.get('MAILJET_API_KEY')
mailjet_secret_key = os.environ.get('MAILJET_SECRET_KEY')
sender_email = os.environ.get('SENDER_EMAIL', 'noreply@buildyoursmartcart.com')

# Walmart API setup
walmart_consumer_id = os.environ.get('WALMART_CONSUMER_ID')
walmart_private_key = os.environ.get('WALMART_PRIVATE_KEY')
walmart_key_version = os.environ.get('WALMART_KEY_VERSION', '1')
# Debug toggle for Walmart API (set to 'true' to enable extra logs)
walmart_debug = os.environ.get('WALMART_DEBUG', 'false').lower() in ['1', 'true', 'yes']

# Enhanced Walmart API validation and debugging
if walmart_consumer_id and walmart_private_key:
    logger.info("🔧 Walmart API Configuration Check:")
    logger.info(f"  Consumer ID: {walmart_consumer_id[:8]}...{walmart_consumer_id[-4:]}")
    logger.info(f"  Private Key Length: {len(walmart_private_key)} characters")
    logger.info(f"  Private Key Version: {walmart_key_version}")
    logger.info(f"  Private Key Preview: {walmart_private_key[:50]}...")
    
    # Check if private key looks like valid Base64
    import string
    valid_b64_chars = set(string.ascii_letters + string.digits + '+/=')
    invalid_chars = set(walmart_private_key) - valid_b64_chars
    if invalid_chars:
        logger.warning(f"⚠️ Private key contains invalid Base64 characters: {invalid_chars}")
    else:
        logger.info("✅ Private key contains only valid Base64 characters")
    
    # Check padding
    padding_needed = len(walmart_private_key) % 4
    if padding_needed:
        logger.warning(f"⚠️ Private key needs {4 - padding_needed} padding characters")
    else:
        logger.info("✅ Private key has correct Base64 padding")
    if walmart_debug:
        logger.info("🔎 WALMART_DEBUG is enabled — extra Walmart logs will be shown (secrets masked)")
else:
    logger.warning("⚠️ Walmart API credentials not fully configured")

# Pydantic models for recipe creation
class RecipeGenerationRequest(BaseModel):
    user_id: str
    cuisine_type: str
    meal_type: str
    difficulty: str
    servings: int = 4
    prep_time_max: Optional[int] = None
    dietary_preferences: Optional[List[str]] = []
    ingredients_on_hand: Optional[List[str]] = []

class WeeklyPlanRequest(BaseModel):
    user_id: str
    family_size: int
    budget: float
    dietary_preferences: Optional[List[str]] = []
    cuisines: Optional[List[str]] = []
    meal_types: List[str] = ["breakfast", "lunch", "dinner"]
    cooking_time_preference: str = "medium"

class StarbucksDrinkRequest(BaseModel):
    user_id: str
    drink_type: str
    flavor_inspiration: Optional[str] = None

# Pydantic models for authentication
class UserRegistrationRequest(BaseModel):
    email: str
    password: str
    name: str
    phone: Optional[str] = None

class UserLoginRequest(BaseModel):
    email: str
    password: str

class VerificationRequest(BaseModel):
    email: str
    verification_code: str

class EmailVerificationRequest(BaseModel):
    email: str
    verification_code: str

# Authentication functions
import hashlib
import secrets
import bcrypt

def hash_password(password: str) -> str:
    """Hash password using bcrypt (more secure than SHA-256)"""
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')

def verify_password(password: str, hashed: str) -> bool:
    """Verify password against bcrypt hash"""
    try:
        # Handle both bcrypt and SHA-256 for backward compatibility
        if hashed.startswith('$2b$') or hashed.startswith('$2a$'):
            # bcrypt hash
            return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
        else:
            # Legacy SHA-256 hash
            return hashlib.sha256(password.encode()).hexdigest() == hashed
    except Exception as e:
        logger.error(f"Password verification error: {e}")
        return False

def generate_verification_code() -> str:
    """Generate 6-digit verification code"""
    return str(random.randint(100000, 999999))

async def send_verification_email(email: str, code: str) -> bool:
    """Send verification email (placeholder implementation)"""
    try:
        logger.info(f"📧 Sending verification code {code} to {email}")
        # In production, integrate with email service (Mailjet, SendGrid, etc.)
        # For now, just log the code
        logger.info(f"✅ Verification email sent (simulated)")
        return True
    except Exception as e:
        logger.error(f"❌ Failed to send verification email: {e}")
        return False

@app.post("/auth/register")
async def register(request: UserRegistrationRequest):
    """Register new user"""
    try:
        logger.info(f"👤 Registration attempt for email: {request.email}")
        
        # Check if user already exists
        existing_user = await users_collection.find_one({"email": request.email})
        if (existing_user):
            logger.warning(f"⚠️ User already exists: {request.email}")
            return JSONResponse(
                status_code=400,
                content={"detail": "User with this email already exists"}
            )
        
        # Hash password
        hashed_password = hash_password(request.password)
        
        # Generate verification code
        verification_code = generate_verification_code()
        
        # Create user document
        user_id = str(uuid.uuid4())
        user_document = {
            "id": user_id,
            "email": request.email,
            "password_hash": hashed_password,
            "name": request.name,
            "phone": request.phone,
            "verified": False,
            "created_at": datetime.utcnow(),
            "last_login": None,
            "preferences": {},
            "subscription_status": "free"
        }
        
        # Save user to database
        await users_collection.insert_one(user_document)
        
        # Save verification code
        verification_document = {
            "email": request.email,
            "code": verification_code,
            "created_at": datetime.utcnow(),
            "expires_at": datetime.utcnow() + timedelta(minutes=15),
            "used": False
        }
        await verification_codes_collection.insert_one(verification_document)
        
        # Send verification email
        email_sent = await send_verification_email(request.email, verification_code)
        
        logger.info(f"✅ User registered successfully: {request.email}")
        
        return JSONResponse(
            status_code=201,
            content={
                "status": "success",
                "message": "User registered successfully. Please check your email for verification code.",
                "user_id": user_id,
                "email": request.email,
                "verification_required": True,
                "email_sent": email_sent
            }
        )
        
    except Exception as e:
        logger.error(f"❌ Registration failed: {e}")
        return JSONResponse(
            status_code=500,
            content={"detail": f"Registration failed: {str(e)}"}
        )

@app.post("/auth/login")
async def login(request: UserLoginRequest):
    """Login user with proper verification and error handling"""
    try:
        logger.info(f"🔐 Login attempt for email: {request.email}")
        
        # Find user in database
        user = await users_collection.find_one({"email": request.email})
        if not user:
            logger.warning(f"⚠️ User not found: {request.email}")
            return JSONResponse(
                status_code=401,
                content={"detail": "Invalid email or password"}
            )
        
        logger.info(f"👤 Found user: {request.email}")
        logger.info(f"🔑 User fields: {list(user.keys())}")
        
        # Check if password_hash field exists
        if "password_hash" not in user:
            logger.error(f"❌ User {request.email} missing password_hash field")
            logger.error(f"❌ Available fields: {list(user.keys())}")
            return JSONResponse(
                status_code=500,
                content={
                    "detail": "User account corrupted - missing password field", 
                    "error": "password_hash_missing",
                    "available_fields": list(user.keys())
                }
            )
        
        # Verify password
        stored_hash = user["password_hash"]
        if not stored_hash:
            logger.error(f"❌ User {request.email} has empty password_hash")
            return JSONResponse(
                status_code=500,
                content={"detail": "User account corrupted - empty password"}
            )
        
        # Check password using the same hash function
        if not verify_password(request.password, stored_hash):
            logger.warning(f"⚠️ Invalid password for: {request.email}")
            logger.info(f"🔐 Request hash: {hash_password(request.password)[:20]}...")
            logger.info(f"🔐 Stored hash: {stored_hash[:20]}...")
            return JSONResponse(
                status_code=401,
                content={"detail": "Invalid email or password"}
            )
        
        # Check if user is verified
        if not user.get("verified", False):
            logger.warning(f"⚠️ User not verified: {request.email}")
            
            # Generate new verification code
            verification_code = generate_verification_code()
            
            # Update verification code in database
            await verification_codes_collection.update_one(
                {"email": request.email},
                {
                    "$set": {
                        "code": verification_code,
                        "created_at": datetime.utcnow(),
                        "expires_at": datetime.utcnow() + timedelta(minutes=15),
                        "used": False
                    }
                },
                upsert=True
            )
            
            # Send verification email
            await send_verification_email(request.email, verification_code)
            
            return JSONResponse(
                status_code=403,
                content={
                    "status": "verification_required",
                    "message": "Account not verified. Please check your email for verification code.",
                    "email": request.email,
                    "user_id": user["id"],
                    "verification_code": verification_code  # For development only
                }
            )
        
        # Update last login
        await users_collection.update_one(
            {"email": request.email},
            {"$set": {"last_login": datetime.utcnow()}}
        )
        
        logger.info(f"✅ Login successful: {request.email}")
        
        return JSONResponse(
            status_code=200,
            content={
                "status": "success",
                "message": "Login successful",
                "user_id": user["id"],
                "email": user["email"],
                "name": user.get("name", "User"),
                "verified": user["verified"],
                "subscription_status": user.get("subscription_status", "free")
            }
        )
        
    except Exception as e:
        logger.error(f"❌ Login failed: {e}")
        logger.error(f"❌ Error type: {type(e).__name__}")
        import traceback
        logger.error(f"❌ Stack trace: {traceback.format_exc()}")
        return JSONResponse(
            status_code=500,
            content={"detail": f"Login failed: {str(e)}"}
        )

@app.post("/auth/verify")
async def verify_email(request: EmailVerificationRequest):
    """Verify user email with verification code"""
    try:
        logger.info(f"🔍 Verification attempt for email: {request.email}")
        
        # Find verification code
        verification = await verification_codes_collection.find_one({
            "email": request.email,
            "used": False
        })
        
        if not verification:
            logger.warning(f"⚠️ No valid verification code found for: {request.email}")
            return JSONResponse(
                status_code=400,
                content={"detail": "Invalid or expired verification code"}
            )
        
        # Check if code matches
        if verification["code"] != request.verification_code:
            logger.warning(f"⚠️ Invalid verification code for: {request.email}")
            return JSONResponse(
                status_code=400,
                content={"detail": "Invalid verification code"}
            )
        
        # Check if code is expired
        if datetime.utcnow() > verification["expires_at"]:
            logger.warning(f"⚠️ Verification code expired for: {request.email}")
            return JSONResponse(
                status_code=400,
                content={"detail": "Verification code expired"}
            )
        
        # Mark user as verified
        result = await users_collection.update_one(
            {"email": request.email},
            {"$set": {"verified": True}}
        )
        
        if result.matched_count == 0:
            return JSONResponse(
                status_code=404,
                content={"detail": "User not found"}
            )
        
        # Mark verification code as used
        await verification_codes_collection.update_one(
            {"_id": verification["_id"]},
            {"$set": {"used": True}}
        )
        
        logger.info(f"✅ Email verified successfully: {request.email}")
        
        return JSONResponse(
            status_code=200,
            content={
                "status": "success",
                "message": "Email verified successfully",
                "email": request.email,
                "verified": True
            }
        )
        
    except Exception as e:
        logger.error(f"❌ Email verification failed: {e}")
        return JSONResponse(
            status_code=500,
            content={"detail": f"Verification failed: {str(e)}"}
        )

@app.post("/auth/resend-verification")
async def resend_verification(request: dict):
    """Resend verification code"""
    try:
        email = request.get("email")
        if not email:
            return JSONResponse(
                status_code=400,
                content={"detail": "Email is required"}
            )
        
        logger.info(f"📧 Resending verification code for: {email}")
        
        # Check if user exists
        user = await users_collection.find_one({"email": email})
        if not user:
            return JSONResponse(
                status_code=404,
                content={"detail": "User not found"}
            )
        
        # Generate new verification code
        verification_code = generate_verification_code()
        
        # Update verification code in database
        await verification_codes_collection.update_one(
            {"email": email},
            {
                "$set": {
                    "code": verification_code,
                    "created_at": datetime.utcnow(),
                    "expires_at": datetime.utcnow() + timedelta(minutes=15),
                    "used": False
                }
            },
            upsert=True
        )
        
        # Send verification email
        email_sent = await send_verification_email(email, verification_code)
        
        return JSONResponse(
            status_code=200,
            content={
                "status": "success",
                "message": "Verification code sent",
                "email": email,
                "email_sent": email_sent
            }
        )
        
    except Exception as e:
        logger.error(f"❌ Failed to resend verification: {e}")
        return JSONResponse(
            status_code=500,
            content={"detail": f"Failed to resend verification: {str(e)}"}
        )

@app.post("/user/preferences")
async def save_user_preferences(request: dict):
    """Save user preferences from onboarding"""
    try:
        user_id = request.get("user_id")
        preferences = request.get("preferences", {})
        
        if not user_id:
            return JSONResponse(
                status_code=400,
                content={"detail": "User ID is required"}
            )
        
        logger.info(f"💾 Saving preferences for user: {user_id}")
        
        # Update user preferences
        result = await users_collection.update_one(
            {"id": user_id},
            {"$set": {"preferences": preferences, "onboarding_completed": True}}
        )
        
        if result.matched_count == 0:
            return JSONResponse(
                status_code=404,
                content={"detail": "User not found"}
            )
        
        logger.info(f"✅ Preferences saved for user: {user_id}")
        
        return JSONResponse(
            status_code=200,
            content={
                "status": "success",
                "message": "Preferences saved successfully",
                "user_id": user_id
            }
        )
        
    except Exception as e:
        logger.error(f"❌ Failed to save preferences: {e}")
        return JSONResponse(
            status_code=500,
            content={"detail": f"Failed to save preferences: {str(e)}"}
        )

@app.post("/recipes/generate")
async def generate_recipe(request: RecipeGenerationRequest):
    """Generate AI recipe using OpenAI"""
    try:
        logger.info(f"🤖 Recipe generation request for user: {request.user_id}")
        logger.info(f"🍳 Recipe details: {request.cuisine_type} {request.meal_type} ({request.difficulty})")
        logger.info(f"📊 Request object received: {request.dict()}")
        logger.info(f"📊 Servings: {request.servings}, Prep time max: {request.prep_time_max}")
        logger.info(f"🥗 Dietary preferences: {request.dietary_preferences}")
        logger.info(f"🥘 Ingredients on hand: {request.ingredients_on_hand}")
        
        if not openai_client:
            logger.error("❌ OpenAI client not available")
            return JSONResponse(
                status_code=503,
                content={"detail": "AI recipe generation is currently unavailable. Please contact support."}
            )
        
        # Create comprehensive prompt for recipe generation
        dietary_text = ", ".join(request.dietary_preferences) if request.dietary_preferences else "none"
        ingredients_text = ", ".join(request.ingredients_on_hand) if request.ingredients_on_hand else "any ingredients"
        prep_time_text = f"maximum {request.prep_time_max} minutes" if request.prep_time_max else "any prep time"
        
        prompt = f"""Create a detailed {request.cuisine_type} {request.meal_type} recipe with the following requirements:
- Difficulty: {request.difficulty}
- Servings: {request.servings}
- Prep time: {prep_time_text}
- Dietary preferences: {dietary_text}
- Preferred ingredients: {ingredients_text}

CRITICAL: You must respond with a valid JSON object with EXACTLY these fields:

{{
    "name": "Recipe name",
    "description": "Brief appetizing description",
    "cuisine_type": "{request.cuisine_type}",
    "meal_type": "{request.meal_type}",
    "difficulty": "{request.difficulty}",
    "prep_time": "X minutes",
    "cook_time": "X minutes",
    "total_time": "X minutes",
    "servings": {request.servings},
    "ingredients": ["ingredient 1", "ingredient 2", "ingredient 3"],
    "ingredients_clean": ["ingredient clean 1", "ingredient clean 2", "ingredient clean 3"],
    "instructions": ["step 1", "step 2", "step 3"],
    "nutrition": {{"calories": "X per serving", "protein": "Xg", "carbs": "Xg", "fat": "Xg"}},
    "cooking_tips": ["tip 1", "tip 2"],
    "estimated_cost": 12.50
}}

IMPORTANT INSTRUCTIONS FOR ingredients_clean:
- This list must have the SAME NUMBER of items as ingredients
- For each ingredient in the "ingredients" list, create a corresponding clean version in "ingredients_clean"
- Clean versions should contain ONLY the ingredient name(s)
- Remove: quantities (1 lb, 2 tbsp), measurements (cups, teaspoons), articles (a, the), descriptors (fresh, dried, chopped, boneless), preparation notes
- Keep: the actual ingredient name that can be searched on Walmart.com
- Examples:
  * "1 lb beef sirloin, thinly sliced" → "beef sirloin"
"""

        logger.info("🤖 Sending request to OpenAI with explicit instructions for ingredients_clean...")
        
        # Call OpenAI API with better error handling
        try:
            response = openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a professional chef and recipe creator. You MUST always respond with valid JSON and include the ingredients_clean field with simplified ingredient names for product search."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=2500,
                temperature=0.7
            )
            
            logger.info("✅ OpenAI response received")
            logger.info(f"📊 OpenAI response object: {response}")
            logger.info(f"📊 OpenAI response choices: {len(response.choices)} choices")
            logger.info(f"📊 OpenAI response usage: {response.usage}")
            
        except Exception as openai_error:
            logger.error(f"❌ OpenAI API error: {openai_error}")
            logger.error(f"❌ OpenAI error type: {type(openai_error).__name__}")
            return JSONResponse(
                status_code=500,
                content={"detail": f"OpenAI API error: {str(openai_error)}"}
            )
        
        # Parse response
        recipe_text = response.choices[0].message.content.strip()
        logger.info(f"📝 Raw AI response length: {len(recipe_text)} characters")
        logger.info(f"📝 First 300 chars of response: {recipe_text[:300]}")
        logger.info(f"📝 Last 300 chars of response: {recipe_text[-300:]}")
        
        # Clean up JSON (remove markdown formatting if present)
        if recipe_text.startswith("```json"):
            recipe_text = recipe_text[7:]
        if recipe_text.endswith("```"):
            recipe_text = recipe_text[:-3]
        
        logger.info("🔄 Parsing JSON response...")
        
        try:
            recipe_data = json.loads(recipe_text)
            logger.info("✅ JSON parsed successfully")
        except json.JSONDecodeError as json_error:
            logger.error(f"❌ JSON parsing failed: {json_error}")
            logger.error(f"❌ Raw text (first 500 chars): {recipe_text[:500]}")
            return JSONResponse(
                status_code=500,
                content={"detail": f"Failed to parse AI response as JSON: {str(json_error)}"}
            )
        
        # FALLBACK: If ingredients_clean is missing, generate it from ingredients
        if "ingredients_clean" not in recipe_data or not recipe_data["ingredients_clean"]:
            logger.warning("⚠️ ingredients_clean not provided by ChatGPT, generating fallback...")
            
            ingredients_to_clean = recipe_data.get("ingredients", [])
            ingredients_clean = []
            
            for ingredient in ingredients_to_clean:
                # Use the same cleaning logic we have in clean_ingredient_for_search
                cleaned = clean_ingredient_for_search(ingredient)
                ingredients_clean.append(cleaned)
            
            recipe_data["ingredients_clean"] = ingredients_clean
            logger.info(f"✅ Generated {len(ingredients_clean)} clean ingredients as fallback")
            logger.info(f"   Sample: {ingredients_to_clean[0] if ingredients_to_clean else 'none'} → {ingredients_clean[0] if ingredients_clean else 'none'}")
        
        # Generate unique ID for the recipe
        recipe_id = str(uuid.uuid4())
        
        # Add metadata to the recipe data
        recipe_data.update({
            "id": recipe_id,
            "user_id": request.user_id,
            "created_at": datetime.utcnow().isoformat(),
            "ai_generated": True,
            "source": "openai"
        })
        
        logger.info(f"💾 Saving recipe to database: {recipe_data.get('name', 'Unknown')}")
        logger.info(f"💾 Recipe data keys before save: {list(recipe_data.keys())}")
        logger.info(f"💾 Recipe ingredients count: {len(recipe_data.get('ingredients', []))}")
        logger.info(f"💾 Recipe ingredients_clean count: {len(recipe_data.get('ingredients_clean', []))}")
        logger.info(f"💾 Recipe instructions count: {len(recipe_data.get('instructions', []))}")
        
        # DEBUG: Check recipe_data BEFORE database operation
        logger.info("🔍 DEBUG: recipe_data keys BEFORE database save:")
        logger.info(f"  Keys: {list(recipe_data.keys())}")
        logger.info(f"  Has _id: {'_id' in recipe_data}")
        logger.info(f"  Object ID type check: {type(recipe_data.get('_id', 'NOT_FOUND'))}")
        
        # DEEP COPY to completely isolate the database object from response object
        import copy
        db_recipe_data = copy.deepcopy(recipe_data)
        
        logger.info("🔍 DEBUG: Created deep copy for database")
        logger.info(f"  Original object id: {id(recipe_data)}")
        logger.info(f"  Copy object id: {id(db_recipe_data)}")
        
        try:
            # Save to database - this should only affect db_recipe_data
            result = await recipes_collection.insert_one(db_recipe_data)
            logger.info(f"✅ Recipe saved to database with ObjectId: {result.inserted_id}")
            logger.info(f"✅ Inserted ID type: {type(result.inserted_id)}")
            
            # DEBUG: Check both objects AFTER database operation
            logger.info("🔍 DEBUG: AFTER database save:")
            logger.info(f"  Original recipe_data keys: {list(recipe_data.keys())}")
            logger.info(f"  Original has _id: {'_id' in recipe_data}")
            logger.info(f"  Copy db_recipe_data keys: {list(db_recipe_data.keys())}")
            logger.info(f"  Copy has _id: {'_id' in db_recipe_data}")
            
            # If the original object got contaminated, we'll see it here
            if '_id' in recipe_data:
                logger.error("🚨 PROBLEM FOUND: Original recipe_data was contaminated with _id!")
                logger.error(f"  _id type: {type(recipe_data['_id'])}")
                logger.error(f"  _id value: {recipe_data['_id']}")
                
                # Remove the _id from the response object manually
                del recipe_data['_id']
                logger.info("🔧 FIX: Removed _id from response object")
            
        except Exception as db_error:
            logger.error(f"❌ Database save failed: {db_error}")
            logger.error(f"❌ Database error type: {type(db_error).__name__}")
            # Continue anyway - we can still return the recipe even if save fails
            logger.warning("⚠️ Continuing without database save")
        
        # DEBUG: Final check before returning
        logger.info("🔍 DEBUG: Final recipe_data before JSONResponse:")
        logger.info(f"  Keys: {list(recipe_data.keys())}")
        logger.info(f"  Has _id: {'_id' in recipe_data}")
        logger.info(f"  Has ingredients: {'ingredients' in recipe_data}")
        logger.info(f"  Has ingredients_clean: {'ingredients_clean' in recipe_data}")
        if 'ingredients' in recipe_data:
            logger.info(f"  ingredients count: {len(recipe_data['ingredients'])}")
            logger.info(f"  ingredients sample: {recipe_data['ingredients'][:2] if recipe_data['ingredients'] else []}")
        if 'ingredients_clean' in recipe_data:
            logger.info(f"  ingredients_clean count: {len(recipe_data['ingredients_clean'])}")
            logger.info(f"  ingredients_clean sample: {recipe_data['ingredients_clean'][:2] if recipe_data['ingredients_clean'] else []}")
        else:
            logger.error("⚠️ WARNING: ingredients_clean field is missing! ChatGPT may not have returned it")
        
        logger.info(f"✅ About to return recipe: {recipe_data['name']}")
        logger.info(f"✅ Recipe ID: {recipe_data.get('id')}")
        logger.info(f"✅ User ID: {recipe_data.get('user_id')}")
        
        # Test JSON serialization before returning
        try:
            test_json = json.dumps(recipe_data, default=str)
            logger.info(f"✅ JSON serialization test passed, size: {len(test_json)} bytes")
        except Exception as json_test_error:
            logger.error(f"❌ JSON serialization test FAILED: {json_test_error}")
            logger.error(f"  Error type: {type(json_test_error).__name__}")
            
            # If there's still a serialization issue, let's find and fix it
            problematic_keys = []
            for key, value in recipe_data.items():
                try:
                    json.dumps({key: value}, default=str)
                except:
                    problematic_keys.append(key)
                    logger.error(f"  Problematic key: {key} = {type(value)} = {str(value)[:100]}")
            
            if problematic_keys:
                logger.error(f"❌ Problematic keys found: {problematic_keys}")
                # Remove problematic keys
                for key in problematic_keys:
                    del recipe_data[key]
                logger.info("🔧 FIX: Removed problematic keys")
        
        logger.info(f"✅ Recipe generated and saved: {recipe_data['name']}")
        logger.info(f"✅ Returning response with status 200")
        
        # Return the clean recipe data
        return JSONResponse(
            status_code=200,
            content=recipe_data
        )
        
    except Exception as e:
        logger.error(f"❌ Recipe generation failed: {e}")
        logger.error(f"❌ Error type: {type(e).__name__}")
        import traceback
        logger.error(f"❌ Stack trace: {traceback.format_exc()}")
        return JSONResponse(
            status_code=500,
            content={"detail": f"Failed to generate recipe: {str(e)}"}
        )

@app.get("/recipes/history/{user_id}")
async def get_user_recipe_history(user_id: str):
    """Get user's recipe history from MongoDB"""
    try:
        # Query recipes collection for user's recipes
        recipes_cursor = recipes_collection.find({"user_id": user_id})
        recipes = []
        
        async for recipe in recipes_cursor:
            # id normalization (support both stored uuid id or Mongo _id)
            raw_id = recipe.get("id") if recipe.get("id") else recipe.get("_id")
            try:
                rid = str(raw_id)
            except Exception:
                rid = ""

            # created_at normalization
            created_at = recipe.get("created_at", "")
            if isinstance(created_at, datetime):
                created_at = created_at.isoformat()

            # infer category/type for frontend filtering
            category = recipe.get("category")
            rtype = recipe.get("type")
            if not category and recipe.get("is_starbucks_drink"):
                category = "starbucks"
            if not rtype and recipe.get("is_starbucks_drink"):
                rtype = "starbucks"

            recipe_data = {
                "id": rid,
                "_id": rid,
                "name": recipe.get("name", ""),
                "drink_name": recipe.get("drink_name", recipe.get("name", "")),
                "description": recipe.get("description", ""),
                "ingredients": recipe.get("ingredients", []),
                "instructions": recipe.get("instructions", []),
                "prep_time": recipe.get("prep_time", recipe.get("prep_time_minutes", "")),
                "cook_time": recipe.get("cook_time", ""),
                "servings": recipe.get("servings", ""),
                "difficulty": recipe.get("difficulty", ""),
                "cuisine_type": recipe.get("cuisine_type", ""),
                "meal_type": recipe.get("meal_type", ""),
                "estimated_cost": recipe.get("estimated_cost", recipe.get("estimated_cost_usd", "")),
                "nutrition": recipe.get("nutrition", {}),
                "cooking_tips": recipe.get("cooking_tips", []),
                "drink_type": recipe.get("drink_type", ""),
                "starbucks_data": recipe.get("starbucks_data", {}),
                "user_id": recipe.get("user_id", ""),
                "created_at": created_at,
                "ai_generated": recipe.get("ai_generated", False),
                "is_starbucks_drink": recipe.get("is_starbucks_drink", False),
                "category": category,
                "type": rtype
            }

            recipes.append(recipe_data)
        
        logger.info(f"📚 Found {len(recipes)} recipes for user {user_id}")
        
        return JSONResponse(
            status_code=200,
            content={
                "status": "success",
                "recipes": recipes,
                "total": len(recipes)
            }
        )
        
    except Exception as e:
        logger.error(f"❌ Error fetching recipe history: {e}")
        return JSONResponse(
            status_code=500,
            content={"detail": f"Failed to fetch recipe history: {str(e)}"}
        )


# API compatibility aliases used by frontend (prefix /api)
@app.get("/api/recipes/history/{user_id}")
async def api_get_user_recipe_history(user_id: str):
    return await get_user_recipe_history(user_id)

@app.delete("/api/recipes/{recipe_id}")
async def api_delete_recipe(recipe_id: str):
    return await delete_recipe(recipe_id)

@app.get("/api/recipes/{recipe_id}/detail")
async def api_get_recipe_detail(recipe_id: str):
    return await get_recipe_detail(recipe_id)

@app.get("/recipes/{recipe_id}/detail")
async def get_recipe_detail(recipe_id: str):
    """Get detailed recipe information including Starbucks drinks"""
    try:
        from bson import ObjectId
        
        # Try to find recipe by ObjectId or string ID
        try:
            recipe = await recipes_collection.find_one({"_id": ObjectId(recipe_id)})
        except:
            recipe = await recipes_collection.find_one({"id": recipe_id})
        
        if not recipe:
            return JSONResponse(
                status_code=404,
                content={"detail": "Recipe not found"}
            )
        
        recipe_data = {
            "id": str(recipe.get("_id", recipe.get("id", ""))),
            "name": recipe.get("name", ""),
            "description": recipe.get("description", ""),
            "cuisine_type": recipe.get("cuisine_type", ""),
            "meal_type": recipe.get("meal_type", ""),
            "difficulty": recipe.get("difficulty", ""),
            "prep_time": recipe.get("prep_time", ""),
            "cook_time": recipe.get("cook_time", ""),
            "total_time": recipe.get("total_time", ""),
            "servings": recipe.get("servings", 0),
            "ingredients": recipe.get("ingredients", []),
            "ingredients_clean": recipe.get("ingredients_clean", []),
            "instructions": recipe.get("instructions", []),
            "nutrition": recipe.get("nutrition", {}),
            "cooking_tips": recipe.get("cooking_tips", []),
            "estimated_cost": recipe.get("estimated_cost", 0),
            "created_at": recipe.get("created_at", ""),
            "ai_generated": recipe.get("ai_generated", True)
        }
        
        # Log what we're returning
        logger.info(f"📋 Returning recipe detail for: {recipe_data['name']}")
        logger.info(f"  Has ingredients_clean: {'ingredients_clean' in recipe_data and len(recipe_data['ingredients_clean']) > 0}")
        if recipe_data['ingredients_clean']:
            logger.info(f"  Clean ingredients count: {len(recipe_data['ingredients_clean'])}")
            logger.info(f"  Clean ingredients sample: {recipe_data['ingredients_clean'][:3]}")
        else:
            logger.warning(f"  ⚠️ No ingredients_clean found in database!")
        
        return JSONResponse(
            status_code=200,
            content=recipe_data
        )
        
    except Exception as e:
        logger.error(f"❌ Error fetching recipe detail: {e}")
        return JSONResponse(
            status_code=500,
            content={"detail": f"Failed to fetch recipe detail: {str(e)}"}
        )

@app.delete("/recipes/{recipe_id}")
async def delete_recipe(recipe_id: str):
    """Delete a recipe"""
    try:
        from bson import ObjectId
        
        # Try to delete by ObjectId or string ID
        try:
            result = await recipes_collection.delete_one({"_id": ObjectId(recipe_id)})
        except:
            result = await recipes_collection.delete_one({"id": recipe_id})
        
        if result.deleted_count == 0:
            return JSONResponse(
                status_code=404,
                content={"detail": "Recipe not found"}
            )
        
        logger.info(f"🗑️ Recipe {recipe_id} deleted successfully")
        
        return JSONResponse(
            status_code=200,
            content={"status": "success", "message": "Recipe deleted"}
        )
        
    except Exception as e:
        logger.error(f"❌ Error deleting recipe: {e}")
        return JSONResponse(
            status_code=500,
            content={"detail": f"Failed to delete recipe: {str(e)}"}
        )

@app.post("/weekly-recipes/generate")
async def generate_weekly_plan(request: WeeklyPlanRequest):
    """Generate weekly meal plan using OpenAI"""
    try:
        logger.info(f"📅 Weekly plan generation for user: {request.user_id}")
        
        if not openai_client:
            return JSONResponse(
                status_code=503,
                content={"detail": "AI meal planning is currently unavailable. Please contact support."}
            )
        
        # Create weekly plan prompt
        dietary_text = ", ".join(request.dietary_preferences) if request.dietary_preferences else "none"
        cuisines_text = ", ".join(request.cuisines) if request.cuisines else "varied cuisines"
        meal_types_text = ", ".join(request.meal_types)
        
        prompt = f"""Create a 7-day meal plan for {request.family_size} people with a ${request.budget} budget:
- Dietary preferences: {dietary_text}
- Preferred cuisines: {cuisines_text}
- Meal types: {meal_types_text}
- Cooking time preference: {request.cooking_time_preference}

Please respond with a JSON object containing:
{{
    "week_of": "2024-XX-XX",
    "family_size": {request.family_size},
    "total_estimated_cost": {request.budget},
    "ai_generated": true,
    "meals": [
        {{
            "day": "Monday",
            "name": "Recipe name",
            "description": "Brief description",
            "cuisine_type": "cuisine",
            "meal_type": "dinner",
            "difficulty": "easy",
            "prep_time": "20 mins",
            "cook_time": "15 mins",
            "servings": {request.family_size},
            "ingredients": ["ingredient 1", "ingredient 2"],
            "instructions": ["step 1", "step 2"],
            "estimated_cost": 12.50,
            "calories_per_serving": 450,
            "dietary_tags": ["tag1", "tag2"],
            "nutrition": {{"protein": "25g", "carbs": "30g", "fat": "15g", "calories": "450"}}
        }}
    ],
    "shopping_list": ["combined ingredient list"]
}}"""

        response = openai_client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a meal planning expert. Create practical, budget-friendly meal plans. Always respond with valid JSON."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=4000,
            temperature=0.7
        )
        
        plan_text = response.choices[0].message.content.strip()
        
        # Clean up JSON
        if plan_text.startswith("```json"):
            plan_text = plan_text[7:]
        if plan_text.endswith("```"):
            plan_text = plan_text[:-3]
        
        plan_data = json.loads(plan_text)
        
        # Add metadata
        plan_data["id"] = str(uuid.uuid4())
        plan_data["user_id"] = request.user_id
        plan_data["created_at"] = datetime.utcnow().isoformat()
        
        # Save to database
        await weekly_recipes_collection.insert_one(plan_data)
        
        logger.info(f"✅ Weekly plan generated: {len(plan_data.get('meals', []))} meals")
        
        return JSONResponse(
            status_code=200,
            content=plan_data
        )
        
    except Exception as e:
        logger.error(f"❌ Weekly plan generation failed: {e}")
        return JSONResponse(
            status_code=500,
            content={"detail": f"Failed to generate weekly plan: {str(e)}"}
        )

@app.get("/weekly-recipes/current/{user_id}")
async def get_current_weekly_plan(user_id: str):
    """Get user's current weekly plan"""
    try:
        # Find the most recent weekly plan
        plan = await weekly_recipes_collection.find_one(
            {"user_id": user_id},
            sort=[("created_at", -1)]
        )
        
        if not plan:
            return JSONResponse(
                status_code=200,
                content={"has_plan": False, "plan": None}
            )
        
        # Convert ObjectId to string
        plan["id"] = str(plan["_id"])
        del plan["_id"]
        
        return JSONResponse(
            status_code=200,
            content={"has_plan": True, "plan": plan}
        )
        
    except Exception as e:
        logger.error(f"❌ Error fetching weekly plan: {e}")
        return JSONResponse(
            status_code=500,
            content={"detail": f"Failed to fetch weekly plan: {str(e)}"}
        )

@app.post("/generate-starbucks-drink")
async def generate_starbucks_drink(request: StarbucksDrinkRequest):
    """Generate Starbucks secret menu drink"""
    try:
        logger.info(f"☕ Starbucks drink generation for user: {request.user_id}")
        logger.info(f"🔍 OpenAI client available: {bool(openai_client)}")
        logger.info(f"🔍 OpenAI API key present: {bool(openai_api_key)}")
        
        if not openai_client:
            logger.error("❌ OpenAI client not available for Starbucks drink generation")
            return JSONResponse(
                status_code=503,
                content={
                    "detail": "AI drink generation is currently unavailable. Please contact support.",
                    "error": "openai_client_not_available",
                    "openai_key_present": bool(openai_api_key)
                }
            )
        
        flavor_text = f" with {request.flavor_inspiration} flavors" if request.flavor_inspiration else ""
        
        prompt = f"""Create a unique Starbucks secret menu {request.drink_type}{flavor_text}:

Please respond with a JSON object containing:
{{
    "drink_name": "Creative drink name",
    "description": "Appetizing description of taste and appearance",
    "category": "{request.drink_type}",
    "base_drink": "Base Starbucks drink to order",
    "modifications": ["modification 1", "modification 2", "modification 3"],
    "ordering_script": "Exact script to tell the barista",
    "flavor_profile": "Taste description",
    "color": "Visual appearance",
    "estimated_price": 5.50,
    "difficulty_level": "easy",
    "best_season": "summer",
    "ai_generated": true
}}"""

        logger.info("🤖 Sending request to OpenAI for Starbucks drink...")
        
        response = openai_client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a Starbucks drink expert who creates viral secret menu drinks. Always respond with valid JSON."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=1500,
            temperature=0.8
        )
        
        logger.info("✅ OpenAI response received for Starbucks drink")
        
        drink_text = response.choices[0].message.content.strip()
        
        # Clean up JSON
        if drink_text.startswith("```json"):
            drink_text = drink_text[7:]
        if drink_text.endswith("```"):
            drink_text = drink_text[:-3]
        
        drink_data = json.loads(drink_text)
        
        # Add metadata
        drink_data["id"] = str(uuid.uuid4())
        drink_data["user_id"] = request.user_id
        drink_data["created_at"] = datetime.utcnow().isoformat()
        
        # Save to database
        await starbucks_recipes_collection.insert_one(drink_data)
        
        logger.info(f"✅ Starbucks drink generated: {drink_data['drink_name']}")
        
        # Convert ObjectId to string if present
        if isinstance(drink_data.get('_id'), ObjectId):
            drink_data['_id'] = str(drink_data['_id'])
        if isinstance(drink_data.get('id'), ObjectId):
            drink_data['id'] = str(drink_data['id'])
            
        return JSONResponse(
            status_code=200,
            content=drink_data
        )
        
    except Exception as e:
        logger.error(f"❌ Starbucks drink generation failed: {e}")
        logger.error(f"❌ Error type: {type(e).__name__}")
        import traceback
        logger.error(f"❌ Stack trace: {traceback.format_exc()}")
        return JSONResponse(
            status_code=500,
            content={
                "detail": f"Failed to generate drink: {str(e)}",
                "error_type": type(e).__name__,
                "openai_client_available": bool(openai_client),
                "openai_key_present": bool(openai_api_key)
            }
        )

@app.get("/user/trial-status/{user_id}")
async def get_trial_status(user_id: str):
    """Get user's trial and subscription status"""
    try:
        user = await users_collection.find_one({"id": user_id})
        
        if not user:
            return JSONResponse(
                status_code=404,
                content={"detail": "User not found"}
            )
        
        # Mock trial status for now
        trial_status = {
            "trial_active": True,
            "trial_days_left": 14,
            "subscription_active": False,
            "subscription_status": user.get("subscription_status", "free"),
            "usage_limits": {
                "recipes_generated": 0,
                "recipes_limit": 50,
                "weekly_plans_generated": 0,
                "weekly_plans_limit": 5
            }
        }
        
        return JSONResponse(
            status_code=200,
            content=trial_status
        )
        
    except Exception as e:
        logger.error(f"❌ Error fetching trial status: {e}")
        return JSONResponse(
            status_code=500,
            content={"detail": f"Failed to fetch trial status: {str(e)}"}
        )

@app.get("/user/dashboard/{user_id}")
async def get_dashboard_data(user_id: str):
    """Get user dashboard statistics"""
    try:
        # Count user's recipes
        total_recipes = await recipes_collection.count_documents({"user_id": user_id})
        total_starbucks = await starbucks_recipes_collection.count_documents({"user_id": user_id})
        total_weekly_plans = await weekly_recipes_collection.count_documents({"user_id": user_id})
        
        dashboard_data = {
            "total_recipes": total_recipes,
            "total_starbucks": total_starbucks,
            "total_shopping_lists": total_recipes,  # Each recipe can have a shopping list
            "total_weekly_plans": total_weekly_plans,
            "recent_activity": []
        }
        
        return JSONResponse(
            status_code=200,
            content=dashboard_data
        )
        
    except Exception as e:
        logger.error(f"❌ Error fetching dashboard data: {e}")
        return JSONResponse(
            status_code=500,
            content={"detail": f"Failed to fetch dashboard data: {str(e)}"}
        )

@app.get("/curated-starbucks-recipes")
async def get_curated_starbucks_recipes(category: str = "all"):
    """Get curated Starbucks recipes"""
    try:
        # Mock curated recipes for now
        curated_recipes = [
            {
                "id": "curated-1",
                "drink_name": "Pink Drink",
                "description": "Refreshing strawberry açaí with coconut milk",
                "category": "refresher",
                "ordering_script": "Can I get a Grande Strawberry Açaí Refresher with coconut milk instead of water?",
                "difficulty_level": "easy",
                "created_at": datetime.utcnow().isoformat()
            },
            {
                "id": "curated-2", 
                "drink_name": "Iced Brown Sugar Oatmilk Shaken Espresso",
                "description": "Sweet and creamy with brown sugar and oat milk",
                "category": "iced_matcha_latte",
                "ordering_script": "Can I get a Grande Iced Brown Sugar Oatmilk Shaken Espresso?",
                "difficulty_level": "easy",
                "created_at": datetime.utcnow().isoformat()
            }
        ]
        
        if category != "all":
            curated_recipes = [r for r in curated_recipes if r["category"] == category]
        
        return JSONResponse(
            status_code=200,
            content={"recipes": curated_recipes}
        )
        
    except Exception as e:
        logger.error(f"❌ Error fetching curated recipes: {e}")
        return JSONResponse(
            status_code=500,
            content={"detail": f"Failed to fetch curated recipes: {str(e)}"}
        )

@app.get("/shared-recipes")
async def get_shared_recipes(category: str = "all", limit: int = 20):
    """Get community shared recipes"""
    try:
        # Query shared recipes from database
        query = {}
        if category != "all":
            query["category"] = category
        
        recipes_cursor = shared_recipes_collection.find(query).sort("created_at", -1).limit(limit)
        recipes = []
        
        async for recipe in recipes_cursor:
            recipe_data = {
                "id": str(recipe["_id"]),
                "recipe_name": recipe.get("recipe_name", ""),
                "description": recipe.get("description", ""),
                "category": recipe.get("category", ""),
                "order_instructions": recipe.get("order_instructions", ""),
                "difficulty_level": recipe.get("difficulty_level", "easy"),
                "likes_count": recipe.get("likes_count", 0),
                "author": recipe.get("author", "Anonymous"),
                "created_at": recipe.get("created_at", ""),
                "tags": recipe.get("tags", [])
            }
            recipes.append(recipe_data)
        
        return JSONResponse(
            status_code=200,
            content={"recipes": recipes}
        )
        
    except Exception as e:
        logger.error(f"❌ Error fetching shared recipes: {e}")
        return JSONResponse(
            status_code=500,
            content={"detail": f"Failed to fetch shared recipes: {str(e)}"}
        )

@app.get("/recipes/{recipe_id}/cart-options")
async def get_recipe_cart_options(recipe_id: str):
    """Get Walmart cart options for a recipe's ingredients"""
    try:
        from bson import ObjectId
        
        logger.info(f"🛒 Getting cart options for recipe: {recipe_id}")
        
        # First, get the recipe to extract ingredients
        try:
            recipe = await recipes_collection.find_one({"_id": ObjectId(recipe_id)})
        except:
            recipe = await recipes_collection.find_one({"id": recipe_id})
        
        if not recipe:
            return JSONResponse(
                status_code=404,
                content={"detail": "Recipe not found"}
            )
        
        ingredients = recipe.get("ingredients_clean")
        
        # For logging and response, we also want to show user-friendly ingredient names
        display_ingredients = recipe.get("ingredients", [])
        
        # DEBUG: Log which list we're using
        logger.info(f"🔍 DEBUG: Ingredient list selection:")
        logger.info(f"  Has ingredients_clean: {'ingredients_clean' in recipe}")
        logger.info(f"  Has ingredients: {'ingredients' in recipe}")
        logger.info(f"  Using clean ingredients: {'ingredients_clean' in recipe}")
        if 'ingredients_clean' in recipe:
            logger.info(f"  Clean ingredients ({len(ingredients)}): {ingredients}")
            logger.info(f"  🎯 USING ingredients_clean for Walmart search ✅")
        else:
            logger.warning(f"  ⚠️ Using fallback ingredients ({len(ingredients)}): {ingredients}")
            logger.warning(f"  ⚠️ FALLBACK: ingredients_clean not found, using full ingredient descriptions")
            logger.warning(f"  ⚠️ This may result in fewer product matches on Walmart")
        
        if not ingredients:
            return JSONResponse(
                status_code=200,
                content={
                    "cart_options": [],
                    "walmart_api_status": "no_ingredients",
                    "message": "No ingredients found in recipe",
                    "ingredients_list": ingredients
                }
            )
        
        logger.info(f"🥘 Found {len(ingredients)} ingredients to search")
        logger.info(f"🔍 Recipe ingredients (using for Walmart): {ingredients[:5]}..." if len(ingredients) > 5 else f"🔍 Recipe ingredients (using for Walmart): {ingredients}")
        
        # Determine search mode
        search_mode = "clean_ingredients" if 'ingredients_clean' in recipe else "fallback_ingredients"
        logger.info(f"🔎 Search mode: {search_mode}")
        if search_mode == "fallback_ingredients":
            logger.warning(f"⚠️ WARNING: Not using clean ingredients - Walmart search may have lower accuracy")
        
        # Check if Walmart API is properly configured
        walmart_api_ready = (
            walmart_consumer_id and 
            walmart_private_key and 
            not any(placeholder in walmart_consumer_id for placeholder in ['your-', 'placeholder', 'here']) and
            not any(placeholder in walmart_private_key for placeholder in ['your-', 'placeholder', 'here']) and
            walmart_consumer_id != 'your_walmart_consumer_id' and
            walmart_private_key != 'your_walmart_private_key'
        )
        
        logger.info(f"🔧 Walmart API ready: {walmart_api_ready}")
        
        if not walmart_api_ready:
            logger.info("⚠️ Walmart API not properly configured")
            
            return JSONResponse(
                status_code=200,
                content={
                    "cart_options": [],
                    "walmart_api_status": "not_configured",
                    "message": "Walmart API not configured - shopping data unavailable",
                    "recipe_name": recipe.get("name", "Unknown Recipe"),
                    "total_ingredients": len(ingredients),
                    "ingredients_list": ingredients,
                    "suggested_stores": [
                        {
                            "store_name": "Walmart",
                            "suggested_action": "Shop manually with ingredient list",
                            "ingredients_list": ingredients
                        }
                    ]
                }
            )
        
        # Real Walmart API integration
        logger.info("🔄 Starting real Walmart API product search...")
        
        products_by_ingredient = {}
        total_products_found = 0
        
        # Process each ingredient
        for ingredient in ingredients[:15]:  # Limit to 15 ingredients for performance
            try:
                logger.info(f"🔍 Searching Walmart for: {ingredient}")
                
                # Ingredient is already clean from ChatGPT's ingredients_clean list
                # No additional cleaning needed
                
                # Search Walmart API
                walmart_products = await search_walmart_products(ingredient, walmart_consumer_id, walmart_private_key)
                
                if walmart_products:
                    # Process and format products
                    formatted_products = []
                    for i, product in enumerate(walmart_products[:3]):  # Max 3 products per ingredient
                        formatted_product = format_walmart_product(product, ingredient, i)
                        if formatted_product:
                            formatted_products.append(formatted_product)
                    
                    if formatted_products:
                        products_by_ingredient[ingredient] = formatted_products
                        total_products_found += len(formatted_products)
                        logger.info(f"✅ Found {len(formatted_products)} products for {ingredient}")
                    else:
                        logger.warning(f"⚠️ No valid products found for {ingredient}")
                else:
                    logger.warning(f"⚠️ No products returned from Walmart API for {ingredient}")
                    
            except Exception as ingredient_error:
                logger.error(f"❌ Error searching for {ingredient}: {ingredient_error}")
                continue
        
        # Create cart response
        if total_products_found > 0:
            # Flatten products for compatibility
            all_products = []
            for ingredient_products in products_by_ingredient.values():
                all_products.extend(ingredient_products)
            
            # Calculate totals
            estimated_total = sum(p.get("price", 0) for p in all_products)
            estimated_savings = sum(p.get("savings_amount", 0) for p in all_products)
            
            cart_response = {
                "cart_options": [{
                    "store_name": "Walmart Supercenter",
                    "store_id": "walmart_api",
                    "distance": "Available nationwide",
                    "store_address": "Find your local Walmart",
                    "total_items": total_products_found,
                    "estimated_total": round(estimated_total, 2),
                    "products": all_products,
                    "productsByIngredient": products_by_ingredient,
                    "pickup_available": True,
                    "delivery_available": True,
                    "pickup_time": "Ready in 2-4 hours",
                    "delivery_time": "Same day or next day",
                    "delivery_fee": 9.95,
                    "minimum_order": 35.00,
                    "coupons_available": total_products_found > 5,
                    "estimated_savings": round(estimated_savings, 2)
                }],
                "walmart_api_status": "success",
                "message": f"Found {total_products_found} products for {len(products_by_ingredient)} ingredients",
                "recipe_name": recipe.get("name", "Unknown Recipe"),
                "total_ingredients": len(ingredients),
                "products_found": len(products_by_ingredient),
                "ingredients_list": ingredients,
                "search_summary": {
                    "ingredients_searched": len(ingredients),
                    "ingredients_with_products": len(products_by_ingredient),
                    "total_products": total_products_found,
                    "coverage_percentage": round((len(products_by_ingredient) / len(ingredients)) * 100, 1)
                }
            }
            
            logger.info(f"✅ Walmart API search complete: {total_products_found} products found")
            return JSONResponse(status_code=200, content=cart_response)
        
        else:
            logger.warning("⚠️ No products found for any ingredients")
            return JSONResponse(
                status_code=200,
                content={
                    "cart_options": [],
                    "walmart_api_status": "no_products_found",
                    "message": "No products found for recipe ingredients",
                    "recipe_name": recipe.get("name", "Unknown Recipe"),
                    "total_ingredients": len(ingredients),
                    "ingredients_list": ingredients,
                    "suggested_action": "Try searching manually on Walmart.com"
                }
            )
        
    except Exception as e:
        logger.error(f"❌ Error getting cart options: {e}")
        import traceback
        logger.error(f"❌ Stack trace: {traceback.format_exc()}")
        return JSONResponse(
            status_code=500,
            content={
                "detail": f"Failed to get cart options: {str(e)}",
                "cart_options": [],
                "walmart_api_status": "error"
            }
        )

def clean_ingredient_for_search(ingredient: str) -> str:
    """Clean ingredient name for Walmart search - extract core ingredient name only."""
    import re
    
    # Step 1: Remove everything after comma (descriptors like "boneless and skinless")
    cleaned = ingredient.split(',')[0].strip()
    
    # Step 2: Remove measurements and quantities at the start (e.g., "2 cups", "1 lb")
    # Match patterns like "2 cups", "1 lb", "3 tbsp", etc.
    cleaned = re.sub(r'^\d+(?:\.\d+)?\s*(?:cups?|tablespoons?|tbsp|teaspoons?|tsp|pounds?|lbs?|lb|ounces?|oz|grams?|g|ml|l|pints?|quarts?|gallons?)\s+', '', cleaned, flags=re.IGNORECASE)
    
    # Step 3: Remove descriptor words (fresh, dried, ground, boneless, etc.)
    descriptor_words = [
        'fresh', 'dried', 'ground', 'boneless', 'skinless', 'seedless', 'seeded',
        'chopped', 'diced', 'minced', 'sliced', 'crushed', 'whole', 'raw', 'cooked',
        'ripe', 'unripe', 'canned', 'frozen', 'thawed', 'raw', 'roasted'
    ]
    for desc in descriptor_words:
        cleaned = re.sub(r'\b' + desc + r'\b', '', cleaned, flags=re.IGNORECASE)
    
    # Step 4: Remove common conjunctions and prepositions
    cleaned = re.sub(r'\b(and|or|with|of)\b', '', cleaned, flags=re.IGNORECASE)
    
    # Step 5: Clean up extra spaces
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()
    
    # Step 6: Handle common multi-word ingredients (before and after cleaning)
    ingredient_mappings = {
        'bell pepper': 'bell pepper',
        'red bell pepper': 'bell pepper',
        'green bell pepper': 'bell pepper',
        'yellow bell pepper': 'bell pepper',
        'chicken breast': 'chicken breast',
        'chicken thigh': 'chicken',
        'ground beef': 'ground beef',
        'olive oil': 'olive oil',
        'vegetable oil': 'oil',
        'sesame oil': 'sesame oil',
        'soy sauce': 'soy sauce',
        'fish sauce': 'fish sauce',
        'coconut milk': 'coconut milk',
        'tomato paste': 'tomato paste',
        'tomato sauce': 'tomato sauce',
        'saffron thread': 'saffron',
        'shiitake mushroom': 'mushroom',
        'oyster mushroom': 'mushroom'
    }
    
    # Check if cleaned ingredient matches any mapping
    cleaned_lower = cleaned.lower()
    for key, value in ingredient_mappings.items():
        if key.lower() in cleaned_lower:
            return value
    
    # Step 7: Return result (or fallback to first word if over-cleaned)
    if len(cleaned) < 2:
        # Over-cleaned; extract first meaningful word from original
        words = ingredient.split()
        for word in words:
            if len(word) > 2 and word.lower() not in ['the', 'and', 'or', 'with', 'of', 'cups', 'tbsp', 'tsp', 'lbs', 'oz', 'cup', 'tbsp']:
                return word
        return ingredient
    
    return cleaned

def generate_walmart_signature(consumer_id: str, private_key: str, timestamp: str) -> str:
    """Generate Walmart API signature for authentication following the exact Java logic"""
    try:
        # Create the headers map exactly like the Java code
        headers_to_sign = {
            "WM_CONSUMER.ID": consumer_id,
            "WM_CONSUMER.INTIMESTAMP": timestamp,
            "WM_SEC.KEY_VERSION": walmart_key_version
        }
        
        # Canonicalize exactly like the Java code - sorted keys with newline-separated values
        def canonicalize(headers_map):
            """Replicate the Java canonicalize method exactly"""
            sorted_keys = sorted(headers_map.keys())  # TreeSet behavior
            
            parameter_names = ""
            canonicalized_string = ""
            
            for key in sorted_keys:
                value = str(headers_map[key]).strip()
                parameter_names += key.strip() + ";"
                canonicalized_string += value + "\n"
            
            return [parameter_names, canonicalized_string]
        
        # Get the canonicalized string (use array[1] like Java code)
        canonicalized_array = canonicalize(headers_to_sign)
        string_to_sign = canonicalized_array[1]  # This is the canonicalizedStrBuffer
        
        # Safe debug: log canonicalized string but only when debug enabled
        if walmart_debug:
            logger.info(f"🔐 Java-style canonicalized string: {repr(string_to_sign)}")
            logger.info(f"🔐 Parameter names: {canonicalized_array[0]}")

        # Handle PEM format private key
        cleaned_private_key = private_key.strip()
        
        # If it looks like a broken PEM format (has BEGIN/END but spaces instead of newlines)
        if "-----BEGIN" in cleaned_private_key and "-----END" in cleaned_private_key:
            # Reconstruct proper PEM format
            lines = cleaned_private_key.split(' ')
            pem_lines = []
            current_line = ""
            
            for part in lines:
                if part.startswith("-----BEGIN"):
                    if current_line:
                        pem_lines.append(current_line)
                    pem_lines.append("-----BEGIN PRIVATE KEY-----")
                    current_line = ""
                elif part.endswith("-----"):
                    if current_line:
                        pem_lines.append(current_line)
                    pem_lines.append("-----END PRIVATE KEY-----")
                    break
                elif not part.startswith("-----") and not part.endswith("-----"):
                    current_line += part
                    # Standard PEM line length is 64 characters
                    if len(current_line) >= 64:
                        pem_lines.append(current_line[:64])
                        current_line = current_line[64:]
            
            if current_line:
                pem_lines.append(current_line)
            
            pem_key = "\n".join(pem_lines)
            if walmart_debug:
                masked = (pem_key[:60] + '...') if len(pem_key) > 80 else pem_key[:80]
                logger.info(f"🔄 Reconstructed PEM format from environment variable (masked): {masked}")
            
        else:
            # Extract just the Base64 content without headers for PKCS#8 format
            # The Java code uses Base64.decodxqeBase64(key) directly on the key content
            base64_content = cleaned_private_key.replace("-----BEGIN PRIVATE KEY-----", "")
            base64_content = base64_content.replace("-----END PRIVATE KEY-----", "")
            base64_content = base64_content.replace("\n", "").replace("\r", "").replace(" ", "")
            
            # Add proper PEM headers for Python cryptography library
            pem_key = f"-----BEGIN PRIVATE KEY-----\n{base64_content}\n-----END PRIVATE KEY-----"
            if walmart_debug:
                masked = (base64_content[:60] + '...') if len(base64_content) > 80 else base64_content[:80]
                logger.info(f"🔐 Built PEM from base64 (masked start): {masked}")
        
        if CRYPTOGRAPHY_AVAILABLE:
            try:
                from cryptography.hazmat.primitives import serialization
                
                # Load private key in PKCS#8 format (matches Java "PKCS#8")
                private_key_obj = serialization.load_pem_private_key(
                    pem_key.encode('utf-8'),
                    password=None,
                    backend=default_backend
                )
                
                # Sign using SHA256WithRSA (exactly matches Java "SHA256WithRSA")
                signature = private_key_obj.sign(
                    string_to_sign.encode('utf-8'),
                    padding.PKCS1v15(),
                    hashes.SHA256()
                )
                
                # Base64 encode (matches Java Base64.encodeBase64String)
                signature_b64 = base64.b64encode(signature).decode('utf-8')
                if walmart_debug:
                    logger.info(f"✅ Successfully generated RSA signature (len={len(signature_b64)})")
                else:
                    logger.info("✅ Successfully generated RSA signature")
                return signature_b64
                
            except Exception as crypto_error:
                # Mask PEM preview
                masked_preview = (pem_key[:200] + '...') if pem_key and len(pem_key) > 200 else (pem_key or '')
                logger.error(f"❌ Cryptography signing failed: {crypto_error}")
                logger.error(f"❌ PEM key preview (masked): {masked_preview[:200]}")
                return ""
        else:
            logger.error("❌ Cryptography library not available")
            return ""
            
    except Exception as e:
        logger.error(f"❌ Failed to generate Walmart signature: {e}")
        import traceback
        logger.error(f"❌ Stack trace: {traceback.format_exc()}")
        return ""

async def search_walmart_products(query: str, consumer_id: str, private_key: str) -> list:
    """Search Walmart API for products matching the query"""
    try:
        # Walmart Open API endpoint for product search
        base_url = "https://developer.api.walmart.com/api-proxy/service/affil/product/v2/search?query="

        # Generate timestamp (Unix epoch time in milliseconds)
        timestamp = str(int(time.time() * 1000))

        logger.info(f"🔍 Walmart API request for: {query}")
        logger.info(f"⏰ Using timestamp: {timestamp}")

        # Generate signature for authentication
        signature = generate_walmart_signature(consumer_id, private_key, timestamp)

        if not signature:
            logger.error("❌ Failed to generate signature")
            return []

        # API parameters
        params = {
            'query': query,
            'categoryId': '976759',  # Grocery category
            'numItems': 5,  # Get top 5 results
        }

        # ONLY the 4 required headers from Walmart API documentation
        headers = {
            'WM_CONSUMER.ID': consumer_id,
            'WM_CONSUMER.INTIMESTAMP': timestamp,
            'WM_SEC.KEY_VERSION': walmart_key_version,
            'WM_SEC.AUTH_SIGNATURE': signature
        }
        # Safe debug output: log headers except signature (mask it) and params
        if walmart_debug:
            safe_headers = headers.copy()
            if 'WM_SEC.AUTH_SIGNATURE' in safe_headers:
                safe_headers['WM_SEC.AUTH_SIGNATURE'] = '[MASKED]'
            logger.info(f"🔧 Walmart request headers (masked): {safe_headers}")
            logger.info(f"🔧 Walmart request params: {params}")
        
   
        
        # Enhanced error handling for network issues
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.get(base_url, params=params, headers=headers)
                
                logger.info(f"📊 Walmart API response status: {response.status_code}")
                if walmart_debug:
                    # Truncate response body to avoid huge logs and mask potential PII
                    body = response.text
                    truncated = (body[:1000] + '...') if len(body) > 1000 else body
                    logger.info(f"📄 Walmart response body (truncated): {truncated}")
                
                if response.status_code == 200:
                    data = response.json()
                    products = data.get('items', [])
                    logger.info(f"✅ Walmart API returned {len(products)} products for '{query}'")
                    return products
                elif response.status_code == 401:
                    logger.error(f"❌ Walmart API authentication failed (401): {response.text}")
                    return []
                elif response.status_code == 403:
                    logger.error(f"❌ Walmart API access forbidden (403): {response.text}")
                    return []
                elif response.status_code == 400:
                    logger.error(f"❌ Walmart API bad request (400): {response.text}")
                    return []
                else:
                    logger.error(f"❌ Walmart API error {response.status_code}: {response.text}")
                    return []
            
        except httpx.TimeoutException as timeout_error:
            logger.warning(f"⏰ Walmart API request timed out for '{query}': {timeout_error}")
            return []
            
        except httpx.RequestError as request_error:
            logger.error(f"📡 HTTP request error for '{query}': {request_error}")
            return []
                
    except Exception as e:
        logger.error(f"❌ Walmart API search failed for '{query}': {e}")
        import traceback
        logger.error(f"❌ Stack trace: {traceback.format_exc()}")
        return []

def format_walmart_product(product: dict, ingredient: str, rank: int) -> dict:
    """Format Walmart API product response for our frontend"""
    try:
        # Extract product data
        item_id = product.get('itemId', '')
        name = product.get('name', 'Unknown Product')
        price = float(product.get('salePrice', product.get('msrp', 0)))
        msrp = float(product.get('msrp', price))
        
        # Calculate savings
        savings = max(0, msrp - price)
        is_best_price = rank == 0  # First result is best price
        
        # Get additional details
        brand = product.get('brandName', 'Generic')
        image_url = product.get('thumbnailImage', product.get('mediumImage', ''))
        
        # Determine size from name or use default
        size = extract_size_from_name(name)
        
        # Calculate rating from customer review
        customer_rating = product.get('customerRating', 0)
        if customer_rating:
            rating = round(float(customer_rating), 1)
        else:
            rating = round(4.0 + random.uniform(0, 0.8), 1)  # Fallback rating
        
        # Review count
        review_count = product.get('numReviews', random.randint(50, 500))
        
        # Availability
        availability = "InStock" if product.get('availableOnline', True) else "OutOfStock"
        
        formatted_product = {
            "itemId": item_id,
            "name": name,
            "price": round(price, 2),
            "brand": brand,
            "size": size,
            "image": image_url,
            "ingredient_match": ingredient,
            "availability": availability,
            "rating": rating,
            "reviewCount": int(review_count),
            "search_rank": rank + 1,
            "is_best_price": is_best_price,
            "msrp": round(msrp, 2),
            "savings_amount": round(savings, 2),
            "clearance": product.get('clearance', False),
            "rollback": savings > 0.50,  # Consider rollback if saving more than 50 cents
            "category": categorize_product(name),
            "nutrition_facts": False,  # Walmart API doesn't provide this easily
            "organic": 'organic' in name.lower(),
            "store_brand": brand.lower() in ['great value', 'marketside', 'equate'],
            "walmart_url": product.get('productUrl', f"https://walmart.com/ip/{item_id}"),
            "upc": product.get('upc', ''),
            "model_number": product.get('modelNumber', ''),
            "marketplace": product.get('marketplace', False)
        }
        
        return formatted_product
        
    except Exception as e:
        logger.error(f"❌ Error formatting Walmart product: {e}")
        return None

def extract_size_from_name(name: str) -> str:
    """Extract size information from product name"""
    import re
    
    # Common size patterns
    size_patterns = [
        r'(\d+(?:\.\d+)?\s*(?:oz|lb|lbs|pounds?|ounces?|fl\s*oz|gallon|qt|quart))',
        r'(\d+(?:\.\d+)?\s*(?:g|kg|grams?|kilograms?))',
        r'(\d+\s*(?:pack|ct|count|piece))',
        r'(\d+(?:\.\d+)?\s*(?:L|ml|liter|milliliter))'
    ]
    
    for pattern in size_patterns:
        match = re.search(pattern, name, re.IGNORECASE)
        if match:
            return match.group(1).strip()
    
    return "Standard Size"

def categorize_product(name: str) -> str:
    """Categorize product based on name"""
    name_lower = name.lower()
    
    if any(meat in name_lower for meat in ['chicken', 'beef', 'pork', 'fish', 'turkey', 'lamb', 'seafood']):
        return 'meat'
    elif any(produce in name_lower for produce in ['fresh', 'organic', 'vegetable', 'fruit', 'lettuce', 'tomato', 'onion', 'potato']):
        return 'produce'
    elif any(dairy in name_lower for dairy in ['milk', 'cheese', 'yogurt', 'butter', 'cream', 'eggs']):
        return 'dairy'
    elif any(pantry in name_lower for pantry in ['sauce', 'oil', 'vinegar', 'flour', 'sugar', 'spice', 'canned', 'pasta']):
        return 'pantry'
    else:
        return 'grocery'

# Health check
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return JSONResponse(
        status_code=200,
        content={
            "status": "healthy",
            "service": "buildyoursmartcart-api",
            "version": "2.2.1",
            "features": {
                "authentication": True,
                "recipe_generation": bool(openai_client),
                "database": True,
                "walmart_api": bool(walmart_consumer_id and walmart_private_key)
            },
            "timestamp": datetime.utcnow().isoformat()
        }
    )

# Root endpoint
@app.get("/")
async def root():
    """API root endpoint"""
    return JSONResponse({
        "message": "buildyoursmartcart.com API",
        "version": "2.2.1",
        "status": "operational",
        "endpoints": {
            "auth": ["/auth/register", "/auth/login", "/auth/verify"],
            "recipes": ["/recipes/generate", "/recipes/history/{user_id}", "/recipes/{recipe_id}/detail"],
            "weekly": ["/weekly-recipes/generate", "/weekly-recipes/current/{user_id}"],
            "starbucks": ["/generate-starbucks-drink", "/curated-starbucks-recipes"],
            "user": ["/user/dashboard/{user_id}", "/user/trial-status/{user_id}"]
        },
        "docs": "/docs"
    })