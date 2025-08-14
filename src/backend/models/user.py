"""
User data models
"""
from pydantic import BaseModel, Field, EmailStr
from typing import Optional, Dict, Any
from datetime import datetime
import uuid

class UserRegistration(BaseModel):
    email: EmailStr
    password: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserProfile(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    email: EmailStr
    is_verified: bool = False
    subscription: Dict[str, Any] = Field(default_factory=dict)
    usage_limits: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class VerificationCode(BaseModel):
    user_id: str
    code: str
    expires_at: datetime
    created_at: datetime = Field(default_factory=datetime.utcnow)

class UserSubscription(BaseModel):
    user_id: str
    status: str  # 'trialing', 'active', 'expired', 'cancelled'
    trial_starts_at: Optional[datetime] = None
    trial_ends_at: Optional[datetime] = None
    subscription_starts_at: Optional[datetime] = None
    subscription_ends_at: Optional[datetime] = None
    customer_id: Optional[str] = None
    subscription_id: Optional[str] = None