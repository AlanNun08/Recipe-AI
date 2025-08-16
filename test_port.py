#!/usr/bin/env python3
"""
Test script to isolate Google Cloud Run port binding issue
"""
import os
import uvicorn
from fastapi import FastAPI

app = FastAPI()

@app.get("/")
async def root():
    return {"message": "Test app running", "port": os.getenv("PORT", "8080")}

@app.get("/health")
async def health():
    return {"status": "healthy", "port": os.getenv("PORT", "8080")}

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    print(f"🚀 Starting test app on 0.0.0.0:{port}")
    
    uvicorn.run(
        "test_port:app",
        host="0.0.0.0",
        port=port,
        log_level="info"
    )