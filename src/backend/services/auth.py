"""
Authentication service
"""
import bcrypt
import uuid
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from ..models.user import UserRegistration, UserLogin, UserProfile, VerificationCode
from .database import get_db_service
from .email import email_service

logger = logging.getLogger(__name__)

class AuthService:
    """Authentication service"""
    
    @staticmethod
    def hash_password(password: str) -> str:
        """Hash password with bcrypt"""
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
    
    @staticmethod
    def verify_password(password: str, hashed: str) -> bool:
        """Verify password against hash"""
        return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
    
    @staticmethod
    def generate_verification_code() -> str:
        """Generate 6-digit verification code"""
        import random
        return str(random.randint(100000, 999999))
    
    @staticmethod
    async def register_user(registration: UserRegistration) -> Dict[str, Any]:
        """Register a new user"""
        # Check if user already exists
        existing_user = await get_db_service().users_collection.find_one({"email": registration.email})
        if existing_user:
            raise ValueError("User already exists")
        
        # Create user profile
        user = UserProfile(
            email=registration.email,
            subscription={
                "status": "trialing",
                "trial_starts_at": datetime.utcnow().isoformat(),
                "trial_ends_at": (datetime.utcnow() + timedelta(days=7)).isoformat()
            },
            usage_limits={
                "weekly_recipes": {"used": 0, "limit": 2},
                "individual_recipes": {"used": 0, "limit": 10},
                "starbucks_drinks": {"used": 0, "limit": 10},
                "last_reset": datetime.utcnow().replace(day=1).isoformat()
            }
        )
        
        # Hash password and store
        hashed_password = AuthService.hash_password(registration.password)
        user_data = user.dict()
        user_data["password"] = hashed_password
        
        # Insert user
        await get_db_service().users_collection.insert_one(user_data)
        
        # Generate and store verification code
        code = AuthService.generate_verification_code()
        verification = VerificationCode(
            user_id=user.id,
            code=code,
            expires_at=datetime.utcnow() + timedelta(hours=24)
        )
        
        await get_db_service().verification_codes_collection.insert_one(verification.dict())
        
        # Send verification email
        try:
            await email_service.send_verification_email(registration.email, code)
        except Exception as e:
            logger.warning(f"Failed to send verification email: {e}")
        
        return {
            "user_id": user.id,
            "email": user.email,
            "message": "Registration successful. Please check your email for verification code."
        }
    
    @staticmethod
    async def login_user(login: UserLogin) -> Dict[str, Any]:
        """Login user"""
        # Find user
        user = await get_db_service().users_collection.find_one({"email": login.email})
        if not user:
            raise ValueError("Invalid credentials")
        
        # Verify password
        if not AuthService.verify_password(login.password, user["password"]):
            raise ValueError("Invalid credentials")
        
        # Return user data (without password)
        user_data = {k: v for k, v in user.items() if k != "password"}
        return {
            "status": "success",
            "user": user_data
        }
    
    @staticmethod
    async def verify_user_email(user_id: str, code: str) -> Dict[str, Any]:
        """Verify user email with code"""
        # Find verification code
        verification = await get_db_service().verification_codes_collection.find_one({
            "user_id": user_id,
            "code": code
        })
        
        if not verification:
            raise ValueError("Invalid verification code")
        
        # Check if code is expired
        if datetime.utcnow() > verification["expires_at"]:
            raise ValueError("Verification code expired")
        
        # Update user as verified
        await get_db_service().users_collection.update_one(
            {"id": user_id},
            {"$set": {"is_verified": True, "updated_at": datetime.utcnow()}}
        )
        
        # Remove verification code
        await get_db_service().verification_codes_collection.delete_one({"user_id": user_id})
        
        return {"message": "Email verified successfully"}
    
    @staticmethod
    async def get_user_profile(user_id: str) -> Optional[Dict[str, Any]]:
        """Get user profile"""
        user = await get_db_service().users_collection.find_one({"id": user_id})
        if user:
            # Remove password from response
            return {k: v for k, v in user.items() if k != "password"}
        return None

# Create service instance
auth_service = AuthService()