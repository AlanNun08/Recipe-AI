"""
Payment and subscription models
"""
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional
from datetime import datetime
import uuid

class SubscriptionCheckoutRequest(BaseModel):
    user_id: str
    user_email: str
    origin_url: str

class PaymentTransaction(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    user_email: str
    package_id: str
    session_id: str
    amount: float
    currency: str
    payment_status: str = "pending"
    stripe_status: str = "pending"
    metadata: Dict[str, Any] = {}
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None

class SubscriptionPackage(BaseModel):
    id: str
    name: str
    price: float
    currency: str
    description: str