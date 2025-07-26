# main.py - Unified Application Entry Point for Google Cloud App Engine
import os
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from starlette.middleware.cors import CORSMiddleware

# Import your existing backend app from the 'backend' directory
from backend.server import app as backend_app

# Initialize the main FastAPI application
app = FastAPI(
    title="AI Recipe + Grocery Delivery App",
    description="AI-powered recipe generation with Walmart grocery integration",
    version="1.0.0"
)

# Configure CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with your actual domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount your existing backend API under the /api path
app.mount("/api", backend_app)

# Serve the React frontend static files
FRONTEND_BUILD_DIR = "frontend/build"

if os.path.exists(FRONTEND_BUILD_DIR):
    # Mount static files (CSS, JS, images)
    app.mount("/static", StaticFiles(directory=f"{FRONTEND_BUILD_DIR}/static"), name="static")
    
    # Serve other static assets (manifest.json, favicon.ico, etc.)
    @app.get("/manifest.json")
    async def serve_manifest():
        return FileResponse(os.path.join(FRONTEND_BUILD_DIR, "manifest.json"))
    
    @app.get("/favicon.ico")
    async def serve_favicon():
        return FileResponse(os.path.join(FRONTEND_BUILD_DIR, "favicon.ico"))
    
    @app.get("/sw.js")
    async def serve_service_worker():
        return FileResponse(os.path.join(FRONTEND_BUILD_DIR, "sw.js"))
    
    # This catch-all route serves your React app's index.html for client-side routing
    @app.get("/{full_path:path}")
    async def serve_react_app(full_path: str):
        # Prevent catching API routes already handled by app.mount("/api", ...)
        if full_path.startswith("api/"):
            raise HTTPException(status_code=404, detail="API endpoint not found")
        
        # Try to serve specific files from the build directory
        if full_path:
            file_path = os.path.join(FRONTEND_BUILD_DIR, full_path)
            if os.path.exists(file_path) and os.path.isfile(file_path):
                return FileResponse(file_path)
        
        # For all other paths, serve the main index.html for React routing
        return FileResponse(os.path.join(FRONTEND_BUILD_DIR, "index.html"))

# Root endpoint handler
@app.get("/")
async def root():
    if os.path.exists(os.path.join(FRONTEND_BUILD_DIR, "index.html")):
        return FileResponse(os.path.join(FRONTEND_BUILD_DIR, "index.html"))
    return {
        "message": "AI Recipe + Grocery Delivery App API",
        "status": "running",
        "version": "1.0.0",
        "features": [
            "AI Recipe Generation",
            "Starbucks Secret Menu",
            "Walmart Grocery Integration",
            "User Authentication",
            "Recipe History"
        ]
    }

# Health check endpoint
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "environment": os.environ.get("GAE_ENV", "development"),
        "frontend_available": os.path.exists(FRONTEND_BUILD_DIR)
    }

# This block is for local development with `python main.py`
# Google Cloud Run will use the `app` object directly
if __name__ == "__main__":
    import uvicorn
    # Google Cloud Run provides the PORT environment variable
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)