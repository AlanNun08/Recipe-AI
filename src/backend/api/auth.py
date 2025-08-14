"""
Authentication API routes
"""
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from ..models.user import UserRegistration, UserLogin
from ..services.auth import auth_service
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth", tags=["authentication"])

@router.post("/register")
async def register_user(registration: UserRegistration):
    """Register a new user"""
    try:
        result = await auth_service.register_user(registration)
        return JSONResponse(status_code=201, content=result)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Registration error: {e}")
        raise HTTPException(status_code=500, detail="Registration failed")

@router.post("/login")
async def login_user(login: UserLogin):
    """Login user"""
    try:
        result = await auth_service.login_user(login)
        return JSONResponse(status_code=200, content=result)
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except Exception as e:
        logger.error(f"Login error: {e}")
        raise HTTPException(status_code=500, detail="Login failed")

@router.post("/verify")
async def verify_email(user_id: str, code: str):
    """Verify user email with code"""
    try:
        result = await auth_service.verify_user_email(user_id, code)
        return JSONResponse(status_code=200, content=result)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Verification error: {e}")
        raise HTTPException(status_code=500, detail="Verification failed")

@router.get("/profile/{user_id}")
async def get_user_profile(user_id: str):
    """Get user profile"""
    try:
        profile = await auth_service.get_user_profile(user_id)
        if not profile:
            raise HTTPException(status_code=404, detail="User not found")
        return JSONResponse(status_code=200, content=profile)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Profile error: {e}")
        raise HTTPException(status_code=500, detail="Failed to get profile")