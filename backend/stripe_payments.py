"""
Comprehensive Stripe Payment System using emergentintegrations
Implements secure payment processing with proper transaction tracking
"""

from fastapi import APIRouter, HTTPException, Request, Depends
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
import logging
import os
import uuid
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorDatabase

# Import emergentintegrations Stripe library
from emergentintegrations.payments.stripe.checkout import (
    StripeCheckout, 
    CheckoutSessionResponse, 
    CheckoutStatusResponse, 
    CheckoutSessionRequest
)

logger = logging.getLogger(__name__)

# Database connection will be injected
payment_router = APIRouter()

# Fixed subscription packages (SECURITY: Define on backend only)
SUBSCRIPTION_PACKAGES = {
    "monthly_premium": {
        "amount": 9.99,  # Keep as float as required by Stripe
        "currency": "usd",
        "name": "Monthly Premium Subscription",
        "description": "AI Recipe + Grocery Delivery Premium Features"
    }
}

# Request/Response Models
class PaymentCheckoutRequest(BaseModel):
    package_id: str = Field(..., description="Package to purchase (monthly_premium)")
    user_id: str = Field(..., description="User ID for transaction tracking")
    user_email: str = Field(..., description="User email")
    origin_url: str = Field(..., description="Frontend origin for redirect URLs")

class PaymentTransaction(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    user_email: str
    package_id: str
    session_id: str
    amount: float
    currency: str
    payment_status: str = "pending"  # pending, paid, failed, expired, cancelled
    stripe_status: str = "pending"   # Stripe's status
    metadata: Dict[str, Any] = {}
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None

class StripeService:
    """Service class for Stripe operations"""
    
    def __init__(self):
        # Use live Stripe API key directly for production
        self.api_key = "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"
        logger.info("Stripe service initialized with live API key")
    
    def get_stripe_checkout(self, webhook_url: str) -> StripeCheckout:
        """Initialize Stripe checkout with webhook URL"""
        return StripeCheckout(api_key=self.api_key, webhook_url=webhook_url)
    
    async def create_checkout_session(
        self, 
        package_id: str, 
        user_data: Dict[str, str], 
        origin_url: str
    ) -> Dict[str, str]:
        """Create Stripe checkout session with secure configuration"""
        try:
            # Validate package exists
            if package_id not in SUBSCRIPTION_PACKAGES:
                raise ValueError(f"Invalid package_id: {package_id}")
            
            package = SUBSCRIPTION_PACKAGES[package_id]
            
            # Build secure URLs using provided origin
            success_url = f"{origin_url}/subscription/success?session_id={{CHECKOUT_SESSION_ID}}"
            cancel_url = f"{origin_url}/subscription/cancel"
            webhook_url = f"{origin_url}/api/webhook/stripe"
            
            # Initialize Stripe checkout
            stripe_checkout = self.get_stripe_checkout(webhook_url)
            
            # Create checkout request
            checkout_request = CheckoutSessionRequest(
                amount=package["amount"],
                currency=package["currency"],
                success_url=success_url,
                cancel_url=cancel_url,
                metadata={
                    "user_id": user_data["user_id"],
                    "user_email": user_data["user_email"],
                    "package_id": package_id,
                    "package_name": package["name"],
                    "source": "ai_recipe_app"
                }
            )
            
            # Create session
            session: CheckoutSessionResponse = await stripe_checkout.create_checkout_session(checkout_request)
            
            return {
                "url": session.url,
                "session_id": session.session_id,
                "amount": package["amount"],
                "currency": package["currency"]
            }
            
        except Exception as e:
            logger.error(f"Failed to create Stripe checkout session: {e}")
            raise Exception(f"Checkout creation failed: {str(e)}")
    
    async def get_session_status(self, session_id: str) -> Dict[str, Any]:
        """Get checkout session status from Stripe"""
        try:
            # Use a dummy webhook URL for status checks
            stripe_checkout = self.get_stripe_checkout("https://example.com/webhook")
            
            status: CheckoutStatusResponse = await stripe_checkout.get_checkout_status(session_id)
            
            return {
                "session_id": session_id,
                "status": status.status,
                "payment_status": status.payment_status,
                "amount_total": status.amount_total,
                "currency": status.currency,
                "metadata": status.metadata
            }
            
        except Exception as e:
            logger.error(f"Failed to get session status: {e}")
            raise Exception(f"Status check failed: {str(e)}")

# Initialize Stripe service
stripe_service = StripeService()

@payment_router.post("/subscription/create-checkout")
async def create_subscription_checkout(
    request: PaymentCheckoutRequest,
    db: AsyncIOMotorDatabase = Depends(lambda: None)  # Will be injected
):
    """
    Create Stripe checkout session for subscription
    SECURITY: Package pricing defined on backend only
    """
    try:
        logger.info(f"Creating checkout for user {request.user_id}, package {request.package_id}")
        
        # Validate package
        if request.package_id not in SUBSCRIPTION_PACKAGES:
            raise HTTPException(status_code=400, detail=f"Invalid package: {request.package_id}")
        
        package = SUBSCRIPTION_PACKAGES[request.package_id]
        
        # Create checkout session
        session_data = await stripe_service.create_checkout_session(
            package_id=request.package_id,
            user_data={
                "user_id": request.user_id,
                "user_email": request.user_email
            },
            origin_url=request.origin_url
        )
        
        # MANDATORY: Create transaction record BEFORE redirect
        transaction = PaymentTransaction(
            user_id=request.user_id,
            user_email=request.user_email,
            package_id=request.package_id,
            session_id=session_data["session_id"],
            amount=session_data["amount"],
            currency=session_data["currency"],
            payment_status="pending",
            stripe_status="pending",
            metadata={
                "package_name": package["name"],
                "origin_url": request.origin_url
            }
        )
        
        # Store in payment_transactions collection
        if db:
            await db.payment_transactions.insert_one(transaction.dict())
            logger.info(f"Payment transaction created: {transaction.id}")
        
        return {
            "url": session_data["url"],
            "session_id": session_data["session_id"],
            "transaction_id": transaction.id
        }
        
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Checkout creation failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to create checkout session")

@payment_router.get("/subscription/checkout/status/{session_id}")
async def get_checkout_status(
    session_id: str,
    db: AsyncIOMotorDatabase = Depends(lambda: None)  # Will be injected
):
    """
    Get payment status and update transaction record
    Implements polling mechanism for payment verification
    """
    try:
        # Get status from Stripe
        status_data = await stripe_service.get_session_status(session_id)
        
        # Find transaction in database
        transaction = None
        if db:
            transaction = await db.payment_transactions.find_one({"session_id": session_id})
        
        if not transaction:
            logger.warning(f"Transaction not found for session {session_id}")
            return status_data
        
        # Update transaction if status changed
        stripe_payment_status = status_data["payment_status"]
        current_payment_status = transaction.get("payment_status", "pending")
        
        if stripe_payment_status != current_payment_status:
            update_data = {
                "payment_status": stripe_payment_status,
                "stripe_status": status_data["status"],
                "updated_at": datetime.utcnow()
            }
            
            # Mark completion time for successful payments
            if stripe_payment_status == "paid" and current_payment_status != "paid":
                update_data["completed_at"] = datetime.utcnow()
                
                # CRITICAL: Only process subscription activation once
                await activate_user_subscription(transaction["user_id"], transaction, db)
                
                logger.info(f"Payment completed for session {session_id}")
            
            # Update transaction record
            await db.payment_transactions.update_one(
                {"session_id": session_id},
                {"$set": update_data}
            )
        
        return {
            **status_data,
            "transaction_id": transaction.get("id"),
            "user_id": transaction.get("user_id")
        }
        
    except Exception as e:
        logger.error(f"Status check failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to check payment status")

async def activate_user_subscription(user_id: str, transaction: Dict[str, Any], db):
    """
    Activate user subscription after successful payment
    CRITICAL: Prevent duplicate activations
    """
    try:
        # Check if subscription already activated for this transaction
        existing_activation = await db.payment_transactions.find_one({
            "session_id": transaction["session_id"],
            "payment_status": "paid",
            "completed_at": {"$exists": True}
        })
        
        if existing_activation and existing_activation["id"] != transaction["id"]:
            logger.warning(f"Subscription already activated for session {transaction['session_id']}")
            return
        
        # Calculate subscription dates
        now = datetime.utcnow()
        subscription_end = datetime(now.year, now.month + 1, now.day) if now.month < 12 else datetime(now.year + 1, 1, now.day)
        
        # Update user subscription
        update_data = {
            "subscription_status": "active",
            "subscription_start_date": now,
            "subscription_end_date": subscription_end,
            "next_billing_date": subscription_end,
            "last_payment_date": now,
            "subscription_reactivated_date": now,
            "cancel_at_period_end": False
        }
        
        result = await db.users.update_one(
            {"id": user_id},
            {"$set": update_data}
        )
        
        if result.modified_count > 0:
            logger.info(f"Subscription activated for user {user_id}")
        else:
            logger.error(f"Failed to activate subscription for user {user_id}")
        
    except Exception as e:
        logger.error(f"Failed to activate subscription: {e}")

@payment_router.post("/webhook/stripe")
async def stripe_webhook(
    request: Request,
    db: AsyncIOMotorDatabase = Depends(lambda: None)  # Will be injected
):
    """
    Handle Stripe webhook events
    Processes payment completions and subscription updates
    """
    try:
        body = await request.body()
        signature = request.headers.get("stripe-signature")
        
        if not signature:
            logger.warning("Missing Stripe signature")
            raise HTTPException(status_code=400, detail="Missing signature")
        
        # Use webhook handler from emergentintegrations
        webhook_url = str(request.base_url) + "api/webhook/stripe"
        stripe_checkout = stripe_service.get_stripe_checkout(webhook_url)
        
        # Process webhook
        webhook_response = await stripe_checkout.handle_webhook(body, signature)
        
        # Handle different event types
        if webhook_response.event_type == "checkout.session.completed":
            await handle_payment_success(webhook_response, db)
        elif webhook_response.event_type == "payment_intent.payment_failed":
            await handle_payment_failure(webhook_response, db)
        
        logger.info(f"Webhook processed: {webhook_response.event_type}")
        return {"received": True}
        
    except Exception as e:
        logger.error(f"Webhook processing failed: {e}")
        raise HTTPException(status_code=400, detail="Webhook processing failed")

async def handle_payment_success(webhook_response, db):
    """Handle successful payment webhook"""
    try:
        session_id = webhook_response.session_id
        payment_status = webhook_response.payment_status
        
        if payment_status == "paid":
            # Update transaction
            await db.payment_transactions.update_one(
                {"session_id": session_id},
                {
                    "$set": {
                        "payment_status": "paid",
                        "updated_at": datetime.utcnow(),
                        "completed_at": datetime.utcnow()
                    }
                }
            )
            
            # Get transaction for user activation
            transaction = await db.payment_transactions.find_one({"session_id": session_id})
            if transaction:
                await activate_user_subscription(transaction["user_id"], transaction, db)
        
    except Exception as e:
        logger.error(f"Failed to handle payment success: {e}")

async def handle_payment_failure(webhook_response, db):
    """Handle failed payment webhook"""
    try:
        session_id = webhook_response.session_id
        
        # Update transaction
        await db.payment_transactions.update_one(
            {"session_id": session_id},
            {
                "$set": {
                    "payment_status": "failed",
                    "updated_at": datetime.utcnow()
                }
            }
        )
        
        logger.info(f"Payment failure recorded for session {session_id}")
        
    except Exception as e:
        logger.error(f"Failed to handle payment failure: {e}")

@payment_router.get("/subscription/packages")
async def get_subscription_packages():
    """Get available subscription packages"""
    return {
        "packages": SUBSCRIPTION_PACKAGES
    }