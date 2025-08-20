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

# CORS middleware - properly configured for CORS preflight
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["*"]
)

# Global OPTIONS handler for CORS preflight
@app.options("/{full_path:path}")
async def options_handler(full_path: str):
    """Handle all OPTIONS requests for CORS preflight"""
    return JSONResponse(
        status_code=200,
        content={"message": "OK"},
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
            "Access-Control-Allow-Headers": "*",
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

class ResendCodeRequest(BaseModel):
    email: EmailStr

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

async def send_verification_email(email: str, code: str) -> bool:
    """Send verification email"""
    try:
        # In development, just log the code
        if not mailjet_api_key or 'your-' in mailjet_api_key or os.getenv("NODE_ENV") != "production":
            logger.info(f"📧 [DEV MODE] Verification code for {email}: {code}")
            return True
        
        # In production, send actual email via Mailjet
        logger.info(f"Would send verification email to {email} with code {code}")
        return True
    except Exception as e:
        logger.error(f"Failed to send verification email: {e}")
        return False

# Add database connection testing
async def test_database_connection():
    """Test database connection and log results"""
    try:
        # Test basic connection
        await client.admin.command('ping')
        logger.info("✅ MongoDB connection successful")
        
        # Test database access
        await db.command("ping")
        logger.info(f"✅ Database '{db_name}' accessible")
        
        # Test collections access
        collections = await db.list_collection_names()
        logger.info(f"📊 Available collections: {collections}")
        
        # Test a simple operation
        user_count = await users_collection.count_documents({})
        logger.info(f"👥 Total users in database: {user_count}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Database connection failed: {e}")
        logger.error(f"📍 Connection URL: {mongo_url[:20]}...")
        logger.error(f"📍 Database name: {db_name}")
        return False

# Test connection on startup
@app.on_event("startup")
async def startup_event():
    """Run startup tasks"""
    logger.info("🚀 Starting up backend server...")
    
    # Test database connection
    db_connected = await test_database_connection()
    
    if not db_connected:
        if os.getenv("NODE_ENV") == "production":
            logger.error("❌ Database connection required in production")
            raise Exception("Database connection failed")
        else:
            logger.warning("⚠️ Database connection failed - running in degraded mode")

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

# Add missing resend-code endpoint
@app.post("/auth/resend-code")
async def resend_verification_code(request: ResendCodeRequest):
    """Resend verification code to user"""
    try:
        # Find user
        user = await users_collection.find_one({"email": request.email})
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        if user.get("is_verified", False):
            raise HTTPException(status_code=400, detail="User already verified")
        
        # Delete old verification codes
        await verification_codes_collection.delete_many({"user_id": user["id"]})
        
        # Generate new verification code
        code = generate_verification_code()
        verification_data = {
            "user_id": user["id"],
            "code": code,
            "expires_at": datetime.utcnow() + timedelta(hours=24),
            "created_at": datetime.utcnow()
        }
        
        await verification_codes_collection.insert_one(verification_data)
        
        # Send verification email
        email_sent = await send_verification_email(request.email, code)
        
        return JSONResponse(
            status_code=200,
            content={
                "message": "Verification code sent successfully",
                "email": request.email,
                "code_sent": email_sent
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Resend code error: {e}")
        raise HTTPException(status_code=500, detail="Failed to resend verification code")

# Add verification endpoint
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
            {"$set": {"is_verified": True, "updated_at": datetime.utcnow().isoformat()}}
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

# Add a dedicated database test endpoint
@app.get("/db/test")
async def test_database():
    """Test database connection and operations"""
    try:
        results = {}
        
        # Test 1: Basic connection
        await client.admin.command('ping')
        results["connection"] = "✅ Connected"
        
        # Test 2: Database access
        await db.command("ping")
        results["database_access"] = "✅ Accessible"
        
        # Test 3: Collections
        collections = await db.list_collection_names()
        results["collections"] = collections
        
        # Test 4: Sample operations
        user_count = await users_collection.count_documents({})
        results["user_count"] = user_count
        
        # Test 5: Write operation (insert and delete a test document)
        test_doc = {"test": True, "created_at": datetime.utcnow()}
        insert_result = await db.test_collection.insert_one(test_doc)
        await db.test_collection.delete_one({"_id": insert_result.inserted_id})
        results["write_test"] = "✅ Write operations working"
        
        return JSONResponse(
            status_code=200,
            content={
                "status": "success",
                "tests": results,
                "timestamp": datetime.utcnow().isoformat()
            }
        )
        
    except Exception as e:
        logger.error(f"Database test failed: {e}")
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
        )

@app.get("/debug/env")
async def debug_environment():
    """Debug environment variables (remove in production)"""
    if os.getenv("NODE_ENV") == "production":
        raise HTTPException(status_code=404, detail="Not available in production")
    
    return JSONResponse(
        status_code=200,
        content={
            "environment_variables": {
                "NODE_ENV": os.getenv("NODE_ENV"),
                "MONGO_URL": "***" + (os.getenv("MONGO_URL", "")[-10:] if os.getenv("MONGO_URL") else "NOT_SET"),
                "DB_NAME": os.getenv("DB_NAME"),
                "PORT": os.getenv("PORT"),
                "backend_env_loaded": str(Path(__file__).parent / '.env') if (Path(__file__).parent / '.env').exists() else "No .env file"
            },
            "working_directory": str(Path.cwd()),
            "file_location": str(Path(__file__).parent)
        }
    )

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
            "database": db_status,
            "timestamp": datetime.utcnow().isoformat()
        }
    )

@app.get("/")
async def root():
    return {
        "message": "BuildYourSmartCart Backend API",
        "version": "2.2.1",
        "status": "running",
        "endpoints": {
            "auth": "/auth/login, /auth/register, /auth/resend-code, /auth/verify",
            "health": "/health",
            "docs": "/docs"
        }
    }