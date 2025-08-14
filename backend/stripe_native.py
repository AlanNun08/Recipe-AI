"""
Native Stripe Payment Implementation
Uses standard Stripe Python library for Google Cloud deployment
"""

import stripe
import os
import logging
import uuid
from datetime import datetime
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

# Initialize Stripe with API key from environment
stripe.api_key = os.environ.get('STRIPE_API_KEY')

# Fixed subscription packages
SUBSCRIPTION_PACKAGES = {
    "monthly_premium": {
        "amount": 9.99,
        "currency": "usd", 
        "name": "Monthly Premium Subscription",
        "description": "AI Recipe + Grocery Delivery Premium Features"
    }
}

# Request Models
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

class NativeStripeService:
    """Native Stripe service using standard Stripe Python library"""
    
    def __init__(self):
        if not stripe.api_key:
            raise ValueError("STRIPE_API_KEY environment variable is required")
        
        # Check for placeholder values
        if stripe.api_key in ["your-stripe-secret-key-here", "your-str************here"]:
            raise ValueError("Please set a valid Stripe API key in environment variables")
        
        # Validate API key format
        if not (stripe.api_key.startswith('sk_test_') or stripe.api_key.startswith('sk_live_')):
            raise ValueError("Invalid Stripe API key format - must start with sk_test_ or sk_live_")
        
        logger.info(f"Native Stripe service initialized with {'live' if stripe.api_key.startswith('sk_live_') else 'test'} API key")
    
    async def create_checkout_session(self, request: SubscriptionCheckoutRequest) -> Dict[str, Any]:
        """Create Stripe checkout session"""
        try:
            package = SUBSCRIPTION_PACKAGES["monthly_premium"]
            
            # Build URLs
            success_url = f"{request.origin_url}/subscription/success?session_id={{CHECKOUT_SESSION_ID}}"
            cancel_url = f"{request.origin_url}/subscription/cancel"
            
            # Create checkout session
            session = stripe.checkout.Session.create(
                payment_method_types=['card'],
                mode='subscription',
                line_items=[{
                    'price_data': {
                        'currency': package['currency'],
                        'product_data': {
                            'name': package['name'],
                            'description': package['description'],
                        },
                        'unit_amount': int(package['amount'] * 100),  # Convert to cents
                        'recurring': {
                            'interval': 'month',
                            'interval_count': 1,
                        },
                    },
                    'quantity': 1,
                }],
                success_url=success_url,
                cancel_url=cancel_url,
                metadata={
                    'user_id': request.user_id,
                    'user_email': request.user_email,
                    'package_id': 'monthly_premium',
                    'source': 'ai_recipe_app'
                }
            )
            
            return {
                'url': session.url,
                'session_id': session.id,
                'amount': package['amount'],
                'currency': package['currency']
            }
            
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error: {e}")
            raise Exception(f"Stripe error: {str(e)}")
        except Exception as e:
            logger.error(f"Checkout creation failed: {e}")
            raise Exception(f"Failed to create checkout: {str(e)}")
    
    async def get_checkout_status(self, session_id: str) -> Dict[str, Any]:
        """Get checkout session status"""
        try:
            session = stripe.checkout.Session.retrieve(session_id)
            
            return {
                'session_id': session_id,
                'status': session.status,
                'payment_status': session.payment_status,
                'amount_total': session.amount_total,
                'currency': session.currency,
                'metadata': session.metadata or {}
            }
            
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error getting status: {e}")
            raise Exception(f"Failed to get status: {str(e)}")
        except Exception as e:
            logger.error(f"Status check failed: {e}")
            raise Exception(f"Status check failed: {str(e)}")

# Global service instance
native_stripe_service = NativeStripeService()

async def create_subscription_checkout_native(request: SubscriptionCheckoutRequest, db, users_collection, payment_transactions_collection):
    """Create subscription checkout using native Stripe"""
    try:
        # Validate user exists
        user = await users_collection.find_one({"id": request.user_id})
        if not user:
            from fastapi import HTTPException
            raise HTTPException(status_code=404, detail="User not found")
        
        # Check subscription eligibility
        subscription_status = user.get('subscription_status', 'trial')
        if subscription_status == 'active':
            from dateutil import parser as date_parser
            subscription_end_date = user.get('subscription_end_date')
            if subscription_end_date:
                if isinstance(subscription_end_date, str):
                    subscription_end_date = date_parser.parse(subscription_end_date)
                
                if datetime.utcnow() < subscription_end_date:
                    from fastapi import HTTPException
                    raise HTTPException(status_code=400, detail="User already has active subscription")
        
        # Create checkout session
        session_data = await native_stripe_service.create_checkout_session(request)
        
        # Create transaction record
        transaction = PaymentTransaction(
            user_id=request.user_id,
            user_email=request.user_email,
            package_id="monthly_premium",
            session_id=session_data["session_id"],
            amount=session_data["amount"],
            currency=session_data["currency"],
            payment_status="pending",
            stripe_status="pending",
            metadata={
                "package_name": SUBSCRIPTION_PACKAGES["monthly_premium"]["name"],
                "origin_url": request.origin_url
            }
        )
        
        await payment_transactions_collection.insert_one(transaction.dict())
        logger.info(f"Payment transaction created: {transaction.id}")
        
        return {
            "url": session_data["url"],
            "session_id": session_data["session_id"]
        }
        
    except Exception as e:
        logger.error(f"Native checkout creation failed: {e}")
        from fastapi import HTTPException
        if "User not found" in str(e):
            raise HTTPException(status_code=404, detail="User not found")
        elif "already has active subscription" in str(e):
            raise HTTPException(status_code=400, detail="User already has active subscription")
        else:
            raise HTTPException(status_code=500, detail="Failed to create checkout session")

async def get_checkout_status_native(session_id: str, db, users_collection, payment_transactions_collection):
    """Get checkout status using native Stripe"""
    try:
        # Get status from Stripe
        status_data = await native_stripe_service.get_checkout_status(session_id)
        
        # Find transaction in database
        transaction = await payment_transactions_collection.find_one({"session_id": session_id})
        
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
            
            # Mark completion for successful payments
            if stripe_payment_status == "paid" and current_payment_status != "paid":
                update_data["completed_at"] = datetime.utcnow()
                
                # Activate user subscription
                await activate_user_subscription_native(
                    transaction["user_id"], 
                    transaction, 
                    users_collection
                )
                
                logger.info(f"Payment completed for session {session_id}")
            
            # Update transaction
            await payment_transactions_collection.update_one(
                {"session_id": session_id},
                {"$set": update_data}
            )
        
        return {
            **status_data,
            "transaction_id": transaction.get("id"),
            "user_id": transaction.get("user_id")
        }
        
    except Exception as e:
        logger.error(f"Native status check failed: {e}")
        from fastapi import HTTPException
        raise HTTPException(status_code=500, detail="Failed to check payment status")

async def activate_user_subscription_native(user_id: str, transaction: dict, users_collection):
    """Activate user subscription after successful payment"""
    try:
        import calendar
        now = datetime.utcnow()
        
        # Calculate subscription end date (30 days from now)
        if now.month == 12:
            subscription_end = datetime(now.year + 1, 1, now.day)
        else:
            next_month = now.month + 1
            next_year = now.year
            try:
                subscription_end = datetime(next_year, next_month, now.day)
            except ValueError:
                # Handle month-end edge cases
                last_day_of_next_month = calendar.monthrange(next_year, next_month)[1]
                subscription_end = datetime(next_year, next_month, min(now.day, last_day_of_next_month))
        
        # Update user subscription
        update_data = {
            "subscription_status": "active",
            "subscription_start_date": now,
            "subscription_end_date": subscription_end,
            "next_billing_date": subscription_end,
            "last_payment_date": now,
            "subscription_reactivated_date": now,
            "cancel_at_period_end": False,
            # Reset usage counters
            "usage_reset_date": now,
            "weekly_recipes_used": 0,
            "individual_recipes_used": 0,
            "starbucks_drinks_used": 0
        }
        
        result = await users_collection.update_one(
            {"id": user_id},
            {"$set": update_data}
        )
        
        if result.modified_count > 0:
            logger.info(f"Subscription activated for user {user_id}")
        else:
            logger.error(f"Failed to activate subscription for user {user_id}")
        
    except Exception as e:
        logger.error(f"Failed to activate subscription: {e}")

async def stripe_webhook_native(request, db):
    """Handle Stripe webhooks using native Stripe"""
    try:
        from fastapi import HTTPException
        
        payload = await request.body()
        sig_header = request.headers.get('stripe-signature')
        
        if not sig_header:
            raise HTTPException(status_code=400, detail="Missing signature")
        
        # Verify webhook (for production, add webhook secret verification)
        try:
            # For now, just process the webhook payload
            import json
            event = json.loads(payload.decode('utf-8'))
            
            event_type = event.get('type')
            event_data = event.get('data', {}).get('object', {})
            
            if event_type == 'checkout.session.completed':
                session_id = event_data.get('id')
                if session_id:
                    # Update transaction status
                    await db.payment_transactions.update_one(
                        {"session_id": session_id},
                        {"$set": {
                            "payment_status": "paid",
                            "updated_at": datetime.utcnow(),
                            "completed_at": datetime.utcnow()
                        }}
                    )
                    
                    # Get transaction and activate subscription
                    transaction = await db.payment_transactions.find_one({"session_id": session_id})
                    if transaction:
                        await activate_user_subscription_native(
                            transaction["user_id"], 
                            transaction, 
                            db.users
                        )
            
            logger.info(f"Webhook processed: {event_type}")
            return {"received": True}
            
        except Exception as e:
            logger.error(f"Webhook processing error: {e}")
            raise HTTPException(status_code=400, detail="Webhook processing failed")
        
    except Exception as e:
        logger.error(f"Webhook error: {e}")
        raise HTTPException(status_code=400, detail="Webhook failed")