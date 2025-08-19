#!/usr/bin/env python3
"""
Universal production startup script for both Cloud Run and App Engine
Optimized for fast startup and scalability
"""
import os
import sys
import uvicorn
import logging
from pathlib import Path

def load_environment_variables():
    """Load environment variables from backend/.env if available"""
    try:
        from dotenv import load_dotenv
        backend_env_path = Path(__file__).parent / "backend" / ".env"
        if backend_env_path.exists():
            load_dotenv(backend_env_path)
            return True
        return False
    except ImportError:
        # python-dotenv not installed
        return False

def setup_logging():
    """Configure production logging"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[logging.StreamHandler(sys.stdout)]
    )
    return logging.getLogger(__name__)

def get_environment_config():
    """Get environment configuration with smart defaults"""
    # Load .env file first
    env_loaded = load_environment_variables()
    
    # Port configuration (Cloud Run uses PORT, App Engine uses PORT)
    port = int(os.environ.get('PORT', 8080))
    
    # Environment detection
    is_production = os.environ.get('NODE_ENV') == 'production'
    is_cloud_run = 'K_SERVICE' in os.environ  # Cloud Run specific env var
    
    # Set required defaults if missing (for development/testing)
    if 'MONGO_URL' not in os.environ:
        os.environ['MONGO_URL'] = 'mongodb://localhost:27017'
    if 'DB_NAME' not in os.environ:
        os.environ['DB_NAME'] = 'buildyoursmartcart_production' if is_production else 'buildyoursmartcart_development'
    
    return {
        'port': port,
        'is_production': is_production,
        'is_cloud_run': is_cloud_run,
        'env_loaded': env_loaded
    }

def create_uvicorn_config(port, is_production, is_cloud_run):
    """Create optimized uvicorn configuration"""
    config = {
        "host": "0.0.0.0",
        "port": port,
        "workers": 1,  # Single worker for both Cloud Run and App Engine
        "loop": "auto",
        "log_level": "info",
        "access_log": not is_production,  # Reduce log noise in production
        "server_header": not is_production,
        "date_header": not is_production,
        "reload": False
    }
    
    # Cloud Run specific optimizations
    if is_cloud_run:
        config.update({
            "log_level": "warning",  # Even less noise for Cloud Run
            "timeout_keep_alive": 2,  # Quick keep-alive
            "timeout_graceful_shutdown": 30
        })
    
    return config

def main():
    """Main entry point"""
    logger = setup_logging()
    
    try:
        # Get configuration
        env_config = get_environment_config()
        logger.info(f"🚀 Starting buildyoursmartcart.com on port {env_config['port']}")
        logger.info(f"🌍 Environment: {'production' if env_config['is_production'] else 'development'}")
        logger.info(f"☁️ Platform: {'Cloud Run' if env_config['is_cloud_run'] else 'App Engine/Local'}")
        logger.info(f"📝 Environment file loaded: {env_config['env_loaded']}")
        
        # Import application
        from main import app
        logger.info("✅ Application loaded successfully")
        
        # Create uvicorn config
        config = create_uvicorn_config(
            env_config['port'], 
            env_config['is_production'], 
            env_config['is_cloud_run']
        )
        
        # Start server
        uvicorn.run(app, **config)
        
    except ImportError as e:
        logger.error(f"❌ Failed to import application: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"❌ Startup failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()