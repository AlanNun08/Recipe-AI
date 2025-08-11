"""
Fixed Stripe Endpoints
Replacement implementation for broken Stripe payment endpoints in server.py

USAGE:
1. Replace the existing Stripe endpoints in server.py with these implementations
2. Ensure proper imports are added at the top of server.py
3. Update environment variables with valid Stripe API keys

ENDPOINTS FIXED:
- POST /api/subscription/create-checkout
- GET /api/subscription/checkout/status/{session_id}  
- POST /api/webhook/stripe (new)
- GET /api/subscription/analytics (new)
"""

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from typing import Dict, Any
from datetime import datetime
import logging
import os
import uuid

# Import our new service classes
from stripe.stripe_service import StripeService
from stripe.subscription_handlers import SubscriptionHandler
from stripe.webhook_handlers import WebhookHandler

logger = logging.getLogger(__name__)

# Request models
class SubscriptionCheckoutRequest(BaseModel):
    user_id: str
    user_email: str
    origin_url: str

class PaymentTransaction(BaseModel):
    id: str
    user_id: str
    email: str
    session_id: str
    payment_status: str = "pending"
    amount: float
    currency: str = "usd"
    metadata: Dict[str, str] = {}
    created_at: str
    updated_at: str
    stripe_payment_intent_id: str = None

# Fixed Stripe endpoints
async def create_subscription_checkout_fixed(request: SubscriptionCheckoutRequest, db, users_collection, payment_transactions_collection):
    """
    FIXED: Create Stripe checkout session for subscription
    
    CHANGES MADE:
    1. Proper API key validation with helpful error messages
    2. Cleaner subscription eligibility logic using SubscriptionHandler
    3. Better error handling with appropriate HTTP status codes
    4. Enhanced logging for debugging
    5. Separation of concerns using service classes
    """
    try:
        # Initialize services
        try:
            stripe_service = StripeService()
            subscription_handler = SubscriptionHandler(db)
        except ValueError as e:
            logger.error(f"Stripe configuration error: {e}")
            if "placeholder value detected" in str(e):
                raise HTTPException(
                    status_code=500,
                    detail="Payment system not configured. Please contact support."
                )
            raise HTTPException(status_code=500, detail="Payment system configuration error")
        
        # Validate user exists
        user = await users_collection.find_one({"id": request.user_id})
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Check subscription eligibility
        can_checkout, reason = await subscription_handler.can_create_checkout(request.user_id)
        if not can_checkout:
            raise HTTPException(status_code=400, detail=reason)
        
        # Get subscription package info
        package_price = 9.99
        package_currency = "usd"
        
        # Create checkout session
        try:
            session_data = await stripe_service.create_subscription_checkout(
                user_data={
                    "user_id": request.user_id,
                    "email": request.user_email
                },
                origin_url=request.origin_url,
                package_price=package_price,
                package_currency=package_currency
            )
        except Exception as e:
            logger.error(f"Stripe checkout creation failed: {e}")
            raise HTTPException(
                status_code=500, 
                detail="Failed to create payment session. Please try again."
            )
        
        # Create payment transaction record
        transaction = PaymentTransaction(
            id=str(uuid.uuid4()),
            user_id=request.user_id,
            email=request.user_email,
            session_id=session_data["session_id"],
            payment_status="pending",
            amount=package_price,
            currency=package_currency,
            metadata={
                "package_id": "monthly_subscription",
                "subscription_type": "monthly"
            },
            created_at=datetime.utcnow().isoformat(),
            updated_at=datetime.utcnow().isoformat()
        )
        
        await payment_transactions_collection.insert_one(transaction.dict())
        
        logger.info(f"Checkout session created successfully for user {request.user_id}")
        
        return {
            "url": session_data["url"],
            "session_id": session_data["session_id"]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in checkout creation: {e}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred")

async def get_checkout_status_fixed(session_id: str, db, users_collection, payment_transactions_collection):
    """
    FIXED: Get status of checkout session and update subscription if paid
    
    CHANGES MADE:
    1. Better error handling for invalid session IDs
    2. Proper transaction status updates
    3. Enhanced logging
    4. Clean separation of Stripe API calls
    """
    try:
        # Find existing transaction
        transaction = await payment_transactions_collection.find_one({"session_id": session_id})
        if not transaction:
            raise HTTPException(status_code=404, detail="Transaction not found")
        
        # Get checkout status from Stripe
        try:
            stripe_service = StripeService()
            checkout_status = await stripe_service.get_checkout_status(session_id)
        except Exception as e:
            logger.error(f"Failed to get Stripe checkout status: {e}")
            raise HTTPException(status_code=500, detail="Failed to retrieve payment status")
        
        # Update transaction status if changed
        if checkout_status["payment_status"] != transaction["payment_status"]:
            update_data = {
                "payment_status": checkout_status["payment_status"],
                "updated_at": datetime.utcnow().isoformat()
            }
            
            if checkout_status["payment_status"] == "paid":
                update_data["completed_at"] = datetime.utcnow().isoformat()
            
            await payment_transactions_collection.update_one(
                {"session_id": session_id},
                {"$set": update_data}
            )
        
        # Update user subscription if payment succeeded
        if checkout_status["payment_status"] == "paid" and transaction["payment_status"] != "paid":
            subscription_handler = SubscriptionHandler(db)
            success = await subscription_handler.update_subscription_status(
                transaction["user_id"],
                {
                    "customer_id": checkout_status.get("customer_id"),
                    "subscription_id": checkout_status.get("subscription_id"),
                    "amount": checkout_status["amount_total"],
                    "currency": checkout_status["currency"]
                }
            )
            
            if success:
                logger.info(f"Subscription activated for user {transaction['user_id']}")
            else:
                logger.error(f"Failed to activate subscription for user {transaction['user_id']}")
        
        return {
            "session_id": session_id,
            "status": checkout_status["status"],
            "payment_status": checkout_status["payment_status"],
            "amount_total": checkout_status["amount_total"],
            "currency": checkout_status["currency"],
            "metadata": checkout_status["metadata"]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting checkout status: {e}")
        raise HTTPException(status_code=500, detail="Failed to get payment status")

async def stripe_webhook_fixed(request: Request, db):
    """
    NEW: Handle Stripe webhook events
    
    This endpoint processes Stripe webhook events for:
    - Payment completions
    - Subscription updates
    - Failed payments
    - Subscription cancellations
    """
    try:
        payload = await request.body()
        sig_header = request.headers.get('stripe-signature')
        
        if not sig_header:
            raise HTTPException(status_code=400, detail="Missing stripe-signature header")
        
        # Initialize webhook handler
        webhook_handler = WebhookHandler(db)
        
        # Process webhook
        success = await webhook_handler.process_webhook(payload, sig_header)
        
        if success:
            return {"received": True}
        else:
            raise HTTPException(status_code=400, detail="Webhook processing failed")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Webhook processing error: {e}")
        raise HTTPException(status_code=400, detail="Webhook processing failed")

async def get_subscription_analytics_fixed(db):
    """
    NEW: Get subscription analytics
    
    Returns metrics about subscription performance:
    - User status breakdown
    - Conversion rates
    - Recent payments
    """
    try:
        subscription_handler = SubscriptionHandler(db)
        analytics = await subscription_handler.get_subscription_analytics()
        return analytics
        
    except Exception as e:
        logger.error(f"Error getting subscription analytics: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve analytics")

# FastAPI route definitions (to be added to server.py)
STRIPE_ROUTES_TO_ADD = """
# Add these routes to your server.py api_router

@api_router.post("/subscription/create-checkout")
async def create_subscription_checkout(request: SubscriptionCheckoutRequest):
    return await create_subscription_checkout_fixed(
        request, db, users_collection, payment_transactions_collection
    )

@api_router.get("/subscription/checkout/status/{session_id}")
async def get_checkout_status(session_id: str):
    return await get_checkout_status_fixed(
        session_id, db, users_collection, payment_transactions_collection
    )

@api_router.post("/webhook/stripe")
async def stripe_webhook(request: Request):
    return await stripe_webhook_fixed(request, db)

@api_router.get("/subscription/analytics")
async def get_subscription_analytics():
    return await get_subscription_analytics_fixed(db)
"""

# Instructions for implementation
IMPLEMENTATION_INSTRUCTIONS = """
TO IMPLEMENT THESE FIXES:

1. Create the service files:
   - /app/backend/stripe/stripe_service.py
   - /app/backend/stripe/subscription_handlers.py  
   - /app/backend/stripe/webhook_handlers.py

2. Update server.py:
   - Add imports for the new service classes
   - Replace existing Stripe endpoints with the fixed versions above
   - Add the new webhook and analytics endpoints

3. Update environment variables:
   - STRIPE_API_KEY=sk_test_your_actual_key_here
   - STRIPE_WEBHOOK_SECRET=whsec_your_webhook_secret_here

4. Test the implementation:
   - Restart backend service
   - Test checkout creation with demo user
   - Test payment flow end-to-end

5. Deploy to production:
   - Update production environment variables
   - Configure Stripe webhook endpoint
   - Monitor payment processing
"""