#!/usr/bin/env python3
"""
Diagnose the main application startup issues for Google Cloud Run
"""
import os
import sys
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_environment_setup():
    """Test environment variable setup"""
    logger.info("🌍 TESTING ENVIRONMENT SETUP")
    
    # Set minimal required environment variables for testing
    if not os.environ.get('MONGO_URL'):
        os.environ['MONGO_URL'] = 'mongodb://localhost:27017'
        logger.info("  ⚙️ Set default MONGO_URL")
    
    if not os.environ.get('DB_NAME'):
        os.environ['DB_NAME'] = 'buildyoursmartcart_production'
        logger.info("  ⚙️ Set default DB_NAME")
    
    if not os.environ.get('NODE_ENV'):
        os.environ['NODE_ENV'] = 'production'
        logger.info("  ⚙️ Set NODE_ENV=production")
    
    # Set placeholder keys to prevent errors
    placeholder_vars = [
        'OPENAI_API_KEY', 'STRIPE_SECRET_KEY', 'STRIPE_PUBLISHER_API_KEY',
        'MAILJET_API_KEY', 'MAILJET_SECRET_KEY', 'WALMART_CONSUMER_ID',
        'WALMART_PRIVATE_KEY', 'SECRET_KEY'
    ]
    
    for var in placeholder_vars:
        if not os.environ.get(var):
            os.environ[var] = f'placeholder-{var.lower()}'
            logger.info(f"  ⚙️ Set placeholder {var}")

def test_backend_import():
    """Test importing the backend server"""
    logger.info("📦 TESTING BACKEND IMPORT")
    
    try:
        # Test individual components first
        logger.info("  Testing FastAPI import...")
        from fastapi import FastAPI
        logger.info("  ✅ FastAPI imported")
        
        logger.info("  Testing Motor import...")
        from motor.motor_asyncio import AsyncIOMotorClient
        logger.info("  ✅ Motor imported")
        
        logger.info("  Testing backend.server import...")
        from backend.server import app as backend_app
        logger.info("  ✅ Backend server imported successfully")
        return backend_app
        
    except Exception as e:
        logger.error(f"  ❌ Backend import failed: {e}")
        import traceback
        logger.error(f"  📋 Traceback:\n{traceback.format_exc()}")
        return None

def test_main_import():
    """Test importing main.py"""
    logger.info("📦 TESTING MAIN.PY IMPORT")
    
    try:
        # Add current directory to Python path
        if '/app' not in sys.path:
            sys.path.insert(0, '/app')
        
        logger.info("  Testing main import...")
        import main
        logger.info("  ✅ Main module imported")
        
        logger.info("  Testing main.app access...")
        app = getattr(main, 'app', None)
        if app:
            logger.info("  ✅ Main app accessible")
            return app
        else:
            logger.error("  ❌ Main app not found")
            return None
            
    except Exception as e:
        logger.error(f"  ❌ Main import failed: {e}")
        import traceback
        logger.error(f"  📋 Traceback:\n{traceback.format_exc()}")
        return None

def test_uvicorn_startup(app):
    """Test starting the app with uvicorn"""
    logger.info("🚀 TESTING UVICORN STARTUP")
    
    try:
        import uvicorn
        port = int(os.environ.get("PORT", 8080))
        
        logger.info(f"  Starting uvicorn on 0.0.0.0:{port}...")
        
        # Create uvicorn config
        config = {
            "host": "0.0.0.0",
            "port": port,
            "log_level": "info",
            "access_log": True,
            "workers": 1
        }
        
        logger.info(f"  Uvicorn config: {config}")
        
        # Test if we can create the server instance
        server = uvicorn.Server(uvicorn.Config(app, **config))
        logger.info("  ✅ Uvicorn server created successfully")
        
        # Actually start the server
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        logger.info("  🚀 Starting server...")
        server.run()
        
    except Exception as e:
        logger.error(f"  ❌ Uvicorn startup failed: {e}")
        import traceback
        logger.error(f"  📋 Traceback:\n{traceback.format_exc()}")

def main():
    """Main diagnostic function"""
    logger.info("🔍 STARTING GOOGLE CLOUD RUN DIAGNOSTIC")
    logger.info(f"📅 Timestamp: {datetime.utcnow().isoformat()}")
    logger.info(f"📁 Working directory: {os.getcwd()}")
    
    # Step 1: Setup environment
    test_environment_setup()
    
    # Step 2: Test backend import
    backend_app = test_backend_import()
    if not backend_app:
        logger.error("❌ Cannot proceed - backend import failed")
        sys.exit(1)
    
    # Step 3: Test main import
    main_app = test_main_import()
    if not main_app:
        logger.error("❌ Cannot proceed - main import failed")
        sys.exit(1)
    
    # Step 4: Test uvicorn startup
    test_uvicorn_startup(main_app)

if __name__ == "__main__":
    main()