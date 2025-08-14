"""
Application configuration
"""
import os
from pathlib import Path
from typing import List, Optional

class Settings:
    """Application settings"""
    
    # Environment
    ENV: str = os.getenv("NODE_ENV", "development")
    DEBUG: bool = ENV == "development"
    
    # Database
    MONGO_URL: str = os.getenv("MONGO_URL", "mongodb://localhost:27017")
    DB_NAME: str = os.getenv("DB_NAME", "buildyoursmartcart_development")
    
    # API Keys
    OPENAI_API_KEY: Optional[str] = os.getenv("OPENAI_API_KEY")
    STRIPE_API_KEY: Optional[str] = os.getenv("STRIPE_API_KEY")
    STRIPE_PUBLISHABLE_KEY: Optional[str] = os.getenv("STRIPE_PUBLISHABLE_KEY")
    MAILJET_API_KEY: Optional[str] = os.getenv("MAILJET_API_KEY")
    MAILJET_SECRET_KEY: Optional[str] = os.getenv("MAILJET_SECRET_KEY")
    WALMART_CONSUMER_ID: Optional[str] = os.getenv("WALMART_CONSUMER_ID")
    WALMART_PRIVATE_KEY: Optional[str] = os.getenv("WALMART_PRIVATE_KEY")
    
    # Email
    SENDER_EMAIL: str = os.getenv("SENDER_EMAIL", "noreply@buildyoursmartcart.com")
    
    # Security
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-here")
    
    # CORS
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:3000",
        "https://buildyoursmartcart.com",
        "https://*.buildyoursmartcart.com"
    ]
    
    # Subscription limits
    TRIAL_LIMITS = {
        "weekly_recipes": 2,
        "individual_recipes": 10,
        "starbucks_drinks": 10
    }
    
    PREMIUM_LIMITS = {
        "weekly_recipes": 8,  # 2 per week * 4 weeks
        "individual_recipes": 30,
        "starbucks_drinks": 30
    }
    
    # Subscription packages
    SUBSCRIPTION_PACKAGES = {
        "monthly_premium": {
            "amount": 9.99,
            "currency": "usd",
            "name": "Monthly Premium Subscription",
            "description": "AI Recipe + Grocery Delivery Premium Features"
        }
    }

# Create settings instance
settings = Settings()