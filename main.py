#!/usr/bin/env python3
"""
Production-ready FastAPI + React app optimized for Google Cloud Run
Serves both backend API and frontend static files
"""

import os
import logging
import signal
import sys
from pathlib import Path
from datetime import datetime

import uvicorn
from fastapi import FastAPI, Request, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse, Response
from starlette.exceptions import HTTPException as StarletteHTTPException

# Configure logging for Cloud Run
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# Import the backend app
try:
    from backend.server import app as backend_app
    logger.info("✅ Backend app imported successfully")
except ImportError as e:
    logger.error(f"❌ Failed to import backend app: {e}")
    sys.exit(1)

# Create main FastAPI app
app = FastAPI(
    title="buildyoursmartcart.com",
    description="AI Recipe + Grocery Delivery App - Weekly Meal Planning & Walmart Integration",
    version="2.2.0",
    docs_url="/api/docs" if os.getenv("NODE_ENV") != "production" else None,
    redoc_url="/api/redoc" if os.getenv("NODE_ENV") != "production" else None
)

# 🚀 CACHE BUSTING MIDDLEWARE FOR GOOGLE CLOUD RUN
@app.middleware("http")
async def disable_cache(request: Request, call_next):
    """
    Cache busting middleware for Google Cloud Run deployment.
    Ensures users always get the latest version after deployment.
    """
    response: Response = await call_next(request)
    
    # Add cache-control headers to prevent browser caching
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Pragma"] = "no-cache"  
    response.headers["Expires"] = "0"
    
    # Add headers to detect fresh deployments
    response.headers["X-Build-Version"] = "2.2.0-walmart-integration"
    response.headers["X-Last-Modified"] = "2025-08-07T18:50:00Z"
    
    return response

# Health check endpoint for Cloud Run
@app.get("/health")
async def health_check():
    """Health check endpoint for Google Cloud Run"""
    return JSONResponse(
        status_code=200,
        content={
            "status": "healthy",
            "service": "buildyoursmartcart", 
            "version": "2.2.1",
            "features": "navigation-fix-active",
            "last_updated": "2025-08-07T20:15:00Z"
        }
    )

# Mount the backend API with /api prefix
app.mount("/api", backend_app)

# Root endpoint that serves backend API info
@app.get("/api")
async def api_root():
    """API root endpoint"""
    return JSONResponse({
        "message": "buildyoursmartcart.com API - Weekly Meal Planning & Walmart Integration", 
        "version": "2.2.0",
        "features": [
            "ai-recipe-generation",
            "weekly-meal-planning",
            "individual-walmart-shopping",
            "starbucks-secret-menu",
            "community-sharing"
        ],
        "docs": "/api/docs" if os.getenv("NODE_ENV") != "production" else None,
        "health": "/api/health"
    })

# Static files configuration
FRONTEND_BUILD_DIR = Path("/app/frontend/build")

if FRONTEND_BUILD_DIR.exists():
    logger.info("✅ Frontend build directory found")
    
    # Mount static files
    app.mount("/static", StaticFiles(directory=FRONTEND_BUILD_DIR / "static"), name="static")
    
    # Serve manifest.json, favicon.ico, sw.js
    @app.get("/manifest.json")
    async def manifest():
        manifest_path = FRONTEND_BUILD_DIR / "manifest.json"
        if manifest_path.exists():
            return FileResponse(manifest_path, media_type="application/json")
        raise HTTPException(status_code=404, detail="Manifest not found")
    
    @app.get("/favicon.ico")
    async def favicon():
        favicon_path = FRONTEND_BUILD_DIR / "favicon.ico"
        if favicon_path.exists():
            return FileResponse(favicon_path, media_type="image/x-icon")
        raise HTTPException(status_code=404, detail="Favicon not found")
    
    @app.get("/sw.js")
    async def service_worker():
        sw_path = FRONTEND_BUILD_DIR / "sw.js"
        if sw_path.exists():
            return FileResponse(sw_path, media_type="application/javascript")
        raise HTTPException(status_code=404, detail="Service worker not found")
    
    # Serve React app for all other routes
    @app.exception_handler(404)
    async def not_found_handler(request: Request, exc: HTTPException):
        # Don't serve React app for API routes
        if request.url.path.startswith("/api/"):
            return JSONResponse(
                status_code=404,
                content={"detail": "API endpoint not found"}
            )
        
        # Serve React app for frontend routes
        index_path = FRONTEND_BUILD_DIR / "index.html"
        if index_path.exists():
            return FileResponse(index_path, media_type="text/html")
        
        return JSONResponse(
            status_code=404,
            content={"detail": "Page not found"}
        )
    
    @app.get("/")
    async def serve_react_app():
        """Serve the React application"""
        index_path = FRONTEND_BUILD_DIR / "index.html"
        if index_path.exists():
            return FileResponse(index_path, media_type="text/html")
        raise HTTPException(status_code=500, detail="Frontend not available")

else:
    logger.warning("⚠️ Frontend build directory not found - serving API only")
    
    @app.get("/")
    async def api_only():
        return JSONResponse({
            "message": "buildyoursmartcart.com API",
            "docs": "/api/docs",
            "status": "running"
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
    
    # Production configuration for Google Cloud Run
    uvicorn_config = {
        "host": "0.0.0.0",
        "port": port,
        "workers": 1,
        "log_level": "info",
        "access_log": True
    }
    
    # Optimize for production
    if os.getenv("NODE_ENV") == "production":
        uvicorn_config.update({
            "log_level": "warning",
            "access_log": False,  # Use Cloud Logging
            "server_header": False,
            "date_header": False
        })
        logger.info(f"🌐 Google Cloud Run production mode - Port: {port}")
    else:
        logger.info(f"🔧 Development mode - Port: {port}")
    
    uvicorn.run(app, **uvicorn_config)