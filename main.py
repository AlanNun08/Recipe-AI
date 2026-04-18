#!/usr/bin/env python3
"""
Production-ready FastAPI + React app optimized for Google Cloud Run
Serves both backend API and frontend static files
"""
import os
import sys
import signal
import uvicorn
import logging
from pathlib import Path
from datetime import datetime
from fastapi import FastAPI, Request, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

# Configure logging for Cloud Run FIRST
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# Load environment variables from .env file for local development
from dotenv import load_dotenv
if os.getenv("NODE_ENV") != "production":
    load_dotenv()
    logger.info("🔑 Loaded environment variables from .env file")
else:
    logger.info("🔑 Using system environment variables only (production mode)")

# Debug environment variables before importing backend
logger.info("🔍 Environment check before backend import:")
logger.info(f"  OPENAI_API_KEY: {'✅ Set' if os.environ.get('OPENAI_API_KEY') else '❌ Missing'}")
logger.info(f"  MONGO_URL: {'✅ Set' if os.environ.get('MONGO_URL') else '❌ Missing'}")
logger.info(f"  DB_NAME: {'✅ Set' if os.environ.get('DB_NAME') else '❌ Missing'}")

# Create main FastAPI app first (always succeeds)
app = FastAPI(
    title="buildyoursmartcart.com",
    description="AI Recipe + Grocery Delivery App - Weekly Meal Planning & Walmart Integration",
    version="2.2.0",
    docs_url="/api/docs" if os.getenv("NODE_ENV") != "production" else None,
    redoc_url="/api/redoc" if os.getenv("NODE_ENV") != "production" else None
)

logger.info("🚀 Main FastAPI app created successfully")

# Try to import the backend app with better error handling
backend_app = None
backend_available = False

try:
    logger.info("🔄 Attempting to import backend app...")
    
    # Check if backend directory exists
    backend_dir = Path(__file__).parent / "backend"
    if not backend_dir.exists():
        raise ImportError(f"Backend directory not found at: {backend_dir}")
    
    # Check if server.py exists
    server_file = backend_dir / "server.py"
    if not server_file.exists():
        raise ImportError(f"Backend server.py not found at: {server_file}")
    
    logger.info(f"✅ Backend directory found: {backend_dir}")
    logger.info(f"✅ Server file found: {server_file}")
    
    # Import the backend app
    from backend.server import app as imported_backend_app
    backend_app = imported_backend_app
    backend_available = True
    logger.info("✅ Backend app imported successfully")
    
    # Check if routes are registered
    route_count = len(backend_app.routes)
    logger.info(f"📋 Backend app has {route_count} routes registered")
    
    # Log some key routes for debugging
    for route in backend_app.routes[:10]:  # Show first 10 routes
        if hasattr(route, 'methods') and hasattr(route, 'path'):
            logger.info(f"  📌 {list(route.methods)} {route.path}")
    
except ImportError as e:
    logger.error(f"❌ Backend import failed: {e}")
    logger.info("📦 Will create minimal backend fallback...")
    backend_available = False
    backend_app = None

except Exception as e:
    logger.error(f"❌ Unexpected error importing backend: {e}")
    logger.error(f"❌ Error type: {type(e).__name__}")
    
    # Log the full stack trace for debugging
    import traceback
    logger.error(f"❌ Stack trace: {traceback.format_exc()}")
    
    backend_available = False
    backend_app = None

# 🚀 CACHE BUSTING MIDDLEWARE FOR GOOGLE CLOUD RUN
@app.middleware("http")
async def disable_cache(request: Request, call_next):
    """
    Cache busting middleware for Google Cloud Run deployment.
    Ensures users always get the latest version after deployment.
    """
    response = await call_next(request)
    
    # Add cache-control headers to prevent browser caching
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Pragma"] = "no-cache"  
    response.headers["Expires"] = "0"
    
    # Add headers to detect fresh deployments
    response.headers["X-Build-Version"] = "2.2.0-walmart-integration"
    response.headers["X-Last-Modified"] = "2025-08-07T18:50:00Z"
    
    return response

# Health check endpoint for Cloud Run (must be available immediately)
@app.get("/health")
async def health_check():
    """Health check endpoint for Google Cloud Run"""
    
    # Check frontend build
    FRONTEND_BUILD_DIR = None
    if os.path.exists("/app/frontend/build"):
        FRONTEND_BUILD_DIR = Path("/app/frontend/build")
    else:
        FRONTEND_BUILD_DIR = Path(__file__).parent / "frontend" / "build"
    
    return JSONResponse(
        status_code=200,
        content={
            "status": "healthy",
            "service": "buildyoursmartcart", 
            "version": "2.2.1",
            "environment": os.getenv("NODE_ENV", "development"),
            "port": os.getenv("PORT", "8080"),
            "features": {
                "frontend": FRONTEND_BUILD_DIR.exists() if FRONTEND_BUILD_DIR else False,
                "backend_api": backend_available,
                "database": backend_available
            },
            "backend_status": "available" if backend_available else "minimal",
            "backend_error": None if backend_available else "Backend import failed",
            "timestamp": datetime.utcnow().isoformat()
        }
    )

# Mount the backend API with /api prefix - ONLY if we successfully imported it
if backend_app and backend_available:
    app.mount("/api", backend_app)
    logger.info(f"✅ Full backend API mounted at /api with {len(backend_app.routes)} routes")
    
    # Log the actual auth endpoints
    for route in backend_app.routes:
        if hasattr(route, 'path') and 'auth' in route.path:
            methods = list(getattr(route, 'methods', ['N/A']))
            logger.info(f"  🔐 {methods} /api{route.path}")
            
else:
    # Create minimal fallback API if backend import failed
    logger.warning("⚠️ Creating minimal API fallback due to backend import failure")
    
    from fastapi import FastAPI as MinimalFastAPI
    minimal_backend = MinimalFastAPI(title="Minimal Backend API")
    
    @minimal_backend.get("/")
    async def minimal_root():
        return {
            "status": "minimal", 
            "message": "Backend features not available", 
            "backend_available": backend_available,
            "import_error": "Backend import failed"
        }
    
    @minimal_backend.get("/health")
    async def minimal_health():
        return {
            "status": "minimal", 
            "backend_available": False,
            "message": "Backend import failed"
        }
    
    # No auth endpoints in minimal backend to avoid conflicts
    
    app.mount("/api", minimal_backend)
    logger.warning("⚠️ Minimal fallback API mounted at /api")

# Root API endpoint
@app.get("/api")
async def api_root():
    """API root endpoint"""
    return JSONResponse({
        "message": "buildyoursmartcart.com API - Weekly Meal Planning & Walmart Integration", 
        "version": "2.2.0",
        "backend_mode": "full" if backend_available else "minimal",
        "features": [
            "ai-recipe-generation",
            "weekly-meal-planning", 
            "individual-walmart-shopping",
            "starbucks-secret-menu",
            "community-sharing"
        ] if backend_available else ["basic-api"],
        "docs": "/api/docs" if os.getenv("NODE_ENV") != "production" else None,
        "health": "/health"
    })

# Static files configuration
# Use different paths for local vs container
if os.path.exists("/app/frontend/build"):
    FRONTEND_BUILD_DIR = Path("/app/frontend/build")  # Container path
else:
    FRONTEND_BUILD_DIR = Path(__file__).parent / "frontend" / "build"  # Local path

logger.info(f"📁 Looking for frontend at: {FRONTEND_BUILD_DIR}")

if FRONTEND_BUILD_DIR.exists():
    logger.info("✅ Frontend build directory found")
    
    # Mount static files
    app.mount("/static", StaticFiles(directory=FRONTEND_BUILD_DIR / "static"), name="static")

    def serve_frontend_file(filename: str) -> FileResponse:
        file_path = FRONTEND_BUILD_DIR / filename
        if file_path.exists():
            return FileResponse(file_path)
        raise HTTPException(status_code=404, detail=f"{filename} not found")
    
    # Serve manifest.json, favicon.ico, sw.js
    @app.get("/manifest.json")
    async def manifest():
        return serve_frontend_file("manifest.json")
    
    @app.get("/favicon.ico")
    async def favicon():
        return serve_frontend_file("favicon.ico")
    
    @app.get("/sw.js")
    async def service_worker():
        return serve_frontend_file("sw.js")

    @app.get("/privacy")
    @app.get("/privacy.html")
    async def privacy_policy():
        return serve_frontend_file("privacy.html")

    @app.get("/terms")
    @app.get("/terms.html")
    async def terms_of_service():
        return serve_frontend_file("terms.html")

    @app.get("/security")
    @app.get("/security.html")
    async def security_page():
        return serve_frontend_file("security.html")
    
    # Serve React app for all other routes
    @app.exception_handler(404)
    async def not_found_handler(request: Request, exc: HTTPException):
        # Don't serve React app for API routes
        if request.url.path.startswith("/api/"):
            return JSONResponse(status_code=404, content={"detail": "API endpoint not found"})
        
        # Serve React app for frontend routes
        index_path = FRONTEND_BUILD_DIR / "index.html"
        if index_path.exists():
            return FileResponse(index_path)
        
        return JSONResponse(
            status_code=404,
            content={"detail": "Page not found"}
        )
    
    @app.get("/")
    async def serve_react_app():
        """Serve the React application"""
        index_path = FRONTEND_BUILD_DIR / "index.html"
        if index_path.exists():
            return FileResponse(index_path)
        raise HTTPException(status_code=500, detail="Frontend not available")

else:
    logger.warning("⚠️ Frontend build directory not found - serving API only")
    
    @app.get("/")
    async def api_only():
        return JSONResponse({
            "message": "buildyoursmartcart.com API",
            "status": "API Only - Frontend not built",
            "version": "2.2.0",
            "docs": "/api/docs",
            "health": "/health"
        })

# Graceful shutdown handler
def signal_handler(signum, frame):
    logger.info(f"Received signal {signum}, shutting down gracefully...")
    sys.exit(0)

signal.signal(signal.SIGTERM, signal_handler)
signal.signal(signal.SIGINT, signal_handler)

if __name__ == "__main__":
    # Google Cloud Run uses PORT environment variable
    port = int(os.environ.get("PORT", 8080))
    
    logger.info(f"🌐 Starting on port {port}")
    logger.info(f"📁 Frontend build dir exists: {FRONTEND_BUILD_DIR.exists() if 'FRONTEND_BUILD_DIR' in locals() else False}")
    logger.info(f"🔧 Backend available: {backend_available}")
    
    # Cloud Run configuration (simplified for reliability)
    uvicorn_config = {
        "host": "0.0.0.0",
        "port": port,
        "workers": 1,
        "log_level": "info",
        "access_log": True,
        "reload": False,
        "timeout_keep_alive": 30,
        "timeout_graceful_shutdown": 30
    }
    
    # Production optimizations
    if os.getenv("NODE_ENV") == "production":
        uvicorn_config.update({
            "log_level": "info",
            "access_log": True,
        })
        logger.info("🌐 Production mode enabled")
    
    logger.info(f"🚀 Starting buildyoursmartcart.com server...")
    
    try:
        uvicorn.run(app, **uvicorn_config)
    except Exception as e:
        logger.error(f"❌ Server startup failed: {e}")
        # Don't re-raise in Cloud Run, let the container exit gracefully
        sys.exit(1)
