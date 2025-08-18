#!/usr/bin/env python3
"""
Production startup script specifically designed for Google Cloud Run
"""
import os
import sys
import time
import signal
import logging
from datetime import datetime

# Configure production logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

def setup_signal_handlers():
    """Setup signal handlers for graceful shutdown"""
    def signal_handler(signum, frame):
        logger.info(f"🛑 Received signal {signum}, shutting down gracefully...")
        sys.exit(0)
    
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)

def validate_environment():
    """Validate critical environment variables"""
    logger.info("🔍 VALIDATING ENVIRONMENT VARIABLES")
    
    # Get port from Google Cloud Run
    port = os.environ.get('PORT', '8080')
    logger.info(f"📍 Port: {port}")
    
    # Check NODE_ENV
    node_env = os.environ.get('NODE_ENV', 'development')
    logger.info(f"🌍 Environment: {node_env}")
    
    # Critical variables (log if missing but don't fail)
    critical_vars = ['MONGO_URL', 'DB_NAME']
    missing_vars = []
    
    for var in critical_vars:
        value = os.environ.get(var)
        if value:
            # Mask sensitive info
            if 'URL' in var:
                masked = f"{value[:20]}...{value[-10:]}" if len(value) > 30 else "***"
                logger.info(f"  ✅ {var}: {masked}")
            else:
                logger.info(f"  ✅ {var}: {value}")
        else:
            logger.warning(f"  ⚠️ {var}: NOT SET")
            missing_vars.append(var)
    
    # Log optional variables
    optional_vars = [
        'OPENAI_API_KEY', 'STRIPE_SECRET_KEY', 'MAILJET_API_KEY',
        'WALMART_CONSUMER_ID', 'SECRET_KEY'
    ]
    
    for var in optional_vars:
        value = os.environ.get(var)
        if value and not any(placeholder in value for placeholder in ['your-', 'placeholder', 'here']):
            logger.info(f"  ✅ {var}: Configured")
        else:
            logger.info(f"  ⚠️ {var}: Using placeholder/default")
    
    return port, missing_vars

def start_application():
    """Start the FastAPI application"""
    logger.info("🚀 STARTING APPLICATION")
    
    try:
        # Get port
        port, missing_vars = validate_environment()
        
        # Import the application
        logger.info("📦 Importing application...")
        
        # Set minimal defaults if variables are missing (for startup)
        if 'MONGO_URL' not in os.environ:
            os.environ['MONGO_URL'] = 'mongodb://localhost:27017'
            logger.warning("⚠️ Using default MONGO_URL for startup")
        
        if 'DB_NAME' not in os.environ:
            os.environ['DB_NAME'] = 'buildyoursmartcart_production'
        
        # Import main application
        from main import app
        logger.info("✅ Application imported successfully")
        
        # Start uvicorn server
        import uvicorn
        
        config = {
            "host": "0.0.0.0",
            "port": int(port),
            "workers": 1,
            "log_level": "info",
            "access_log": False,  # Reduce noise in Cloud Run logs
            "server_header": False,
            "date_header": False,
            "loop": "auto"
        }
        
        logger.info(f"🌐 Starting server on {config['host']}:{config['port']}")
        logger.info("🎯 Application ready to receive traffic")
        
        # Start the server
        uvicorn.run(app, **config)
        
    except Exception as e:
        logger.error(f"❌ STARTUP FAILED: {e}")
        import traceback
        logger.error(f"📋 Traceback:\n{traceback.format_exc()}")
        
        # Wait a bit before exiting to allow logs to flush
        time.sleep(2)
        sys.exit(1)

def main():
    """Main entry point"""
    logger.info("🔥 GOOGLE CLOUD RUN STARTUP")
    logger.info(f"📅 Timestamp: {datetime.utcnow().isoformat()}")
    logger.info(f"🐍 Python version: {sys.version.split()[0]}")
    logger.info(f"📁 Working directory: {os.getcwd()}")
    
    # Setup signal handlers
    setup_signal_handlers()
    
    # Start the application
    start_application()

if __name__ == "__main__":
    main()