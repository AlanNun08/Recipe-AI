#!/usr/bin/env python3
"""
FAST Cloud Run startup script - minimal logging, quick port binding
"""
import os
import sys
import uvicorn

def main():
    """Start the application immediately"""
    # Get port from Cloud Run
    port = int(os.environ.get('PORT', 8080))
    
    # Set minimal required env vars if missing
    if 'MONGO_URL' not in os.environ:
        os.environ['MONGO_URL'] = 'mongodb://localhost:27017'
    if 'DB_NAME' not in os.environ:
        os.environ['DB_NAME'] = 'buildyoursmartcart_production'
    if 'NODE_ENV' not in os.environ:
        os.environ['NODE_ENV'] = 'production'
    
    # Import and start immediately
    from main import app
    
    # Minimal uvicorn config for fast startup
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port,
        workers=1,
        log_level="warning",  # Reduce startup noise
        access_log=False,
        server_header=False,
        date_header=False
    )

if __name__ == "__main__":
    main()