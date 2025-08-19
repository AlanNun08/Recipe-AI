from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr
from datetime import datetime, timedelta
import jwt
import bcrypt
import os
from typing import Optional

from ..database.connection import get_database
from ..models.user import User

router = APIRouter(prefix="/auth", tags=["authentication"])
security = HTTPBearer()

# Pydantic models for request/response
class UserRegister(BaseModel):
    email: EmailStr
    password: str
    name: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class AuthResponse(BaseModel):
    access_token: str
    token_type: str
    user: dict

class UserResponse(BaseModel):
    id: str
    email: str
    name: str
    created_at: datetime

# JWT Configuration
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 1440  # 24 hours

def create_access_token(data: dict):
    """Create JWT access token"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Verify JWT token"""
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials"
            )
        return email
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials"
        )

async def get_current_user(email: str = Depends(verify_token)):
    """Get current authenticated user"""
    db = await get_database()
    user = await db.users.find_one({"email": email})
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )
    return user

@router.post("/register", response_model=AuthResponse)
async def register(user_data: UserRegister):
    """Register a new user"""
    db = await get_database()
    
    # Check if user already exists
    existing_user = await db.users.find_one({"email": user_data.email})
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Hash password
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(user_data.password.encode('utf-8'), salt)
    
    # Create user document
    user_doc = {
        "email": user_data.email,
        "name": user_data.name,
        "password": hashed_password.decode('utf-8'),
        "created_at": datetime.utcnow(),
        "is_active": True
    }
    
    # Insert user
    result = await db.users.insert_one(user_doc)
    
    # Create access token
    access_token = create_access_token(data={"sub": user_data.email})
    
    # Return response
    user_response = {
        "id": str(result.inserted_id),
        "email": user_data.email,
        "name": user_data.name
    }
    
    return AuthResponse(
        access_token=access_token,
        token_type="bearer",
        user=user_response
    )

@router.post("/login", response_model=AuthResponse)
async def login(credentials: UserLogin):
    """Login user and return JWT token"""
    db = await get_database()
    
    # Find user
    user = await db.users.find_one({"email": credentials.email})
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    # Verify password
    if not bcrypt.checkpw(credentials.password.encode('utf-8'), user["password"].encode('utf-8')):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    # Create access token
    access_token = create_access_token(data={"sub": credentials.email})
    
    # Return response
    user_response = {
        "id": str(user["_id"]),
        "email": user["email"],
        "name": user["name"]
    }
    
    return AuthResponse(
        access_token=access_token,
        token_type="bearer",
        user=user_response
    )

@router.get("/me", response_model=UserResponse)
async def get_me(current_user = Depends(get_current_user)):
    """Get current user profile"""
    return UserResponse(
        id=str(current_user["_id"]),
        email=current_user["email"],
        name=current_user["name"],
        created_at=current_user["created_at"]
    )

@router.post("/logout")
async def logout():
    """Logout user (client should remove token)"""
    return {"message": "Successfully logged out"}
