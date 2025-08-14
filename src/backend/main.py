"""
Main FastAPI application
"""
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware
import os
import logging
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.api.auth import router as auth_router
from backend.api.recipes import router as recipes_router
from backend.services.database import db_service

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="buildyoursmartcart.com API",
    description="AI Recipe + Grocery Delivery API - Weekly Meal Planning & Walmart Integration",
    version="3.0.0",
    docs_url="/docs" if os.getenv("NODE_ENV") != "production" else None,
    redoc_url="/redoc" if os.getenv("NODE_ENV") != "production" else None
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure properly for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Trusted host middleware (configure for production)
if os.getenv("NODE_ENV") == "production":
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=["buildyoursmartcart.com", "*.buildyoursmartcart.com"]
    )

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Test database connection
        await db_service.db.command("ping")
        db_status = "healthy"
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        db_status = "unhealthy"
    
    # Check external API configurations
    external_apis = {
        "openai": bool(os.environ.get('OPENAI_API_KEY')),
        "mailjet": bool(os.environ.get('MAILJET_API_KEY') and os.environ.get('MAILJET_SECRET_KEY')),
        "walmart": bool(os.environ.get('WALMART_CONSUMER_ID')),
        "stripe": bool(os.environ.get('STRIPE_API_KEY'))
    }
    
    return JSONResponse(
        status_code=200 if db_status == "healthy" else 503,
        content={
            "status": "healthy" if db_status == "healthy" else "unhealthy",
            "service": "buildyoursmartcart-api",
            "version": "3.0.0",
            "database": db_status,
            "external_apis": external_apis,
            "timestamp": str(datetime.utcnow().isoformat())
        }
    )

# Root endpoint
@app.get("/")
async def root():
    """API root endpoint"""
    return JSONResponse({
        "message": "buildyoursmartcart.com API - Weekly Meal Planning & Walmart Integration",
        "version": "3.0.0",
        "features": [
            "ai-recipe-generation",
            "weekly-meal-planning", 
            "individual-walmart-shopping",
            "starbucks-secret-menu",
            "user-authentication"
        ],
        "docs": "/docs" if os.getenv("NODE_ENV") != "production" else None,
        "health": "/health"
    })

# Include routers
app.include_router(auth_router)
app.include_router(recipes_router)

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )

if __name__ == "__main__":
    import uvicorn
    from datetime import datetime
    
    port = int(os.environ.get("PORT", 8001))
    
    logger.info(f"🚀 Starting buildyoursmartcart.com API v3.0.0 on port {port}")
    logger.info(f"📝 Environment: {os.getenv('NODE_ENV', 'development')}")
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        log_level="info",
        access_log=True,
        workers=1
    )