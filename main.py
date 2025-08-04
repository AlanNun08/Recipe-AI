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

import uvicorn
from fastapi import FastAPI, Request, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
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
    description="AI Recipe + Grocery Delivery App",
    version="2.0.0",
    docs_url="/api/docs" if os.getenv("NODE_ENV") != "production" else None,
    redoc_url="/api/redoc" if os.getenv("NODE_ENV") != "production" else None
)

# Health check endpoint for Cloud Run
@app.get("/health")
async def health_check():
    """Health check endpoint for Google Cloud Run"""
    return JSONResponse(
        status_code=200,
        content={
            "status": "healthy",
            "service": "buildyoursmartcart",
            "version": "2.0.0"
        }
    )

# Mount the backend API with /api prefix
app.mount("/api", backend_app)

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
    # Get port from environment (Cloud Run sets this)
    port = int(os.environ.get("PORT", 8080))
    
    logger.info(f"🚀 Starting buildyoursmartcart.com on port {port}")
    logger.info(f"📝 Environment: {os.getenv('NODE_ENV', 'development')}")
    
    # Production-optimized uvicorn configuration
    uvicorn_config = {
        "host": "0.0.0.0",
        "port": port,
        "log_level": "info",
        "access_log": True,
        "workers": 1,  # Cloud Run handles scaling
        "loop": "asyncio",
        "http": "h11",
    }
    
    # Add development features only in non-production
    if os.getenv("NODE_ENV") != "production":
        uvicorn_config.update({
            "reload": False,  # Don't use reload in containers
            "log_level": "debug"
        })
    
    uvicorn.run(app, **uvicorn_config)