#!/usr/bin/env python3
"""
Minimal debug script to test Google Cloud Run container startup
"""
import os
import sys
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def debug_environment():
    """Debug environment variables and system info"""
    logger.info("🔍 DEBUGGING CONTAINER STARTUP")
    logger.info(f"📅 Timestamp: {datetime.utcnow().isoformat()}")
    logger.info(f"🐍 Python version: {sys.version}")
    logger.info(f"📁 Working directory: {os.getcwd()}")
    logger.info(f"📂 Directory contents: {os.listdir('.')}")
    
    # Check critical environment variables
    logger.info("🌍 ENVIRONMENT VARIABLES:")
    critical_vars = [
        'PORT', 'NODE_ENV', 'MONGO_URL', 'DB_NAME', 
        'OPENAI_API_KEY', 'STRIPE_SECRET_KEY', 'MAILJET_API_KEY'
    ]
    
    for var in critical_vars:
        value = os.environ.get(var)
        if value:
            # Mask sensitive values
            if 'KEY' in var or 'URL' in var:
                masked_value = f"{value[:10]}...{value[-4:]}" if len(value) > 14 else "***"
                logger.info(f"  ✅ {var}: {masked_value}")
            else:
                logger.info(f"  ✅ {var}: {value}")
        else:
            logger.warning(f"  ❌ {var}: NOT SET")
    
    # Check if we can import key modules
    logger.info("📦 TESTING IMPORTS:")
    try:
        import fastapi
        logger.info(f"  ✅ FastAPI: {fastapi.__version__}")
    except Exception as e:
        logger.error(f"  ❌ FastAPI import failed: {e}")
    
    try:
        import uvicorn
        logger.info(f"  ✅ Uvicorn: {uvicorn.__version__}")
    except Exception as e:
        logger.error(f"  ❌ Uvicorn import failed: {e}")
    
    try:
        from motor.motor_asyncio import AsyncIOMotorClient
        logger.info("  ✅ Motor (MongoDB): Available")
    except Exception as e:
        logger.error(f"  ❌ Motor import failed: {e}")

def test_basic_server():
    """Test if we can start a basic FastAPI server"""
    logger.info("🚀 TESTING BASIC SERVER STARTUP")
    
    try:
        from fastapi import FastAPI
        import uvicorn
        
        # Create minimal app
        app = FastAPI()
        
        @app.get("/")
        async def root():
            return {
                "status": "healthy",
                "message": "Debug server running",
                "port": os.environ.get("PORT", "8080"),
                "timestamp": datetime.utcnow().isoformat()
            }
        
        @app.get("/health")
        async def health():
            return {"status": "healthy", "debug": True}
        
        # Get port
        port = int(os.environ.get("PORT", 8080))
        logger.info(f"🌐 Starting debug server on 0.0.0.0:{port}")
        
        # Start server
        uvicorn.run(
            app,
            host="0.0.0.0",
            port=port,
            log_level="info",
            access_log=True
        )
        
    except Exception as e:
        logger.error(f"❌ BASIC SERVER FAILED: {e}")
        import traceback
        logger.error(f"📋 Traceback: {traceback.format_exc()}")
        sys.exit(1)

if __name__ == "__main__":
    debug_environment()
    test_basic_server()