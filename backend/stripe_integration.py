"""
Integration file to connect Stripe payments with existing server.py
This file patches the existing subscription endpoints with the new implementation
"""

import logging
from fastapi import HTTPException, Request
from pydantic import BaseModel
from typing import Optional
from motor.motor_asyncio import AsyncIOMotorDatabase

# Import our comprehensive Stripe implementation
from stripe_payments import (
    stripe_service, 
    PaymentCheckoutRequest, 
    SUBSCRIPTION_PACKAGES,
    activate_user_subscription
)

logger = logging.getLogger(__name__)

class SubscriptionCheckoutRequestLegacy(BaseModel):
    """Legacy request format for backward compatibility"""
    user_id: str
    user_email: str
    origin_url: str

async def create_subscription_checkout_integrated(
    request: SubscriptionCheckoutRequestLegacy,
    db: AsyncIOMotorDatabase,
    users_collection,
    payment_transactions_collection
):
    """
    Integrated version of create checkout that works with existing server.py
    This replaces the broken endpoint in server.py
    """
    try:
        # Validate user exists
        user = await users_collection.find_one({"id": request.user_id})
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Check subscription eligibility (reuse existing logic)
        subscription_status = user.get('subscription_status', 'trial')
        if subscription_status == 'active':
            # Check if subscription is actually active
            from datetime import datetime
            subscription_end_date = user.get('subscription_end_date')
            if subscription_end_date:
                from dateutil import parser as date_parser
                if isinstance(subscription_end_date, str):
                    subscription_end_date = date_parser.parse(subscription_end_date)
                
                if datetime.utcnow() < subscription_end_date:
                    raise HTTPException(status_code=400, detail="User already has active subscription")
        
        # Create new-style request
        new_request = PaymentCheckoutRequest(
            package_id="monthly_premium",  # Fixed package
            user_id=request.user_id,
            user_email=request.user_email,
            origin_url=request.origin_url
        )
        
        # Get package info
        package = SUBSCRIPTION_PACKAGES["monthly_premium"]
        
        # Create checkout session
        session_data = await stripe_service.create_checkout_session(
            package_id="monthly_premium",
            user_data={
                "user_id": request.user_id,
                "user_email": request.user_email
            },
            origin_url=request.origin_url
        )
        
        # Create transaction record (compatible with existing DB structure)
        from datetime import datetime
        import uuid
        
        transaction = {
            "id": str(uuid.uuid4()),
            "user_id": request.user_id,
            "user_email": request.user_email,
            "package_id": "monthly_premium",
            "session_id": session_data["session_id"],
            "amount": session_data["amount"],
            "currency": session_data["currency"],
            "payment_status": "pending",
            "stripe_status": "pending",
            "metadata": {
                "package_name": package["name"],
                "origin_url": request.origin_url,
                "legacy_integration": True
            },
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        # Store in payment_transactions collection
        await payment_transactions_collection.insert_one(transaction)
        logger.info(f"Payment transaction created: {transaction['id']}")
        
        return {
            "url": session_data["url"],
            "session_id": session_data["session_id"]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Integrated checkout creation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create checkout session: {str(e)}")

async def get_checkout_status_integrated(
    session_id: str,
    db: AsyncIOMotorDatabase,
    users_collection,
    payment_transactions_collection
):
    """
    Integrated checkout status checker that works with existing server.py
    """
    try:
        # Get status from Stripe
        status_data = await stripe_service.get_session_status(session_id)
        
        # Find transaction in database
        transaction = await payment_transactions_collection.find_one({"session_id": session_id})
        
        if not transaction:
            logger.warning(f"Transaction not found for session {session_id}")
            return status_data
        
        # Update transaction if status changed
        stripe_payment_status = status_data["payment_status"]
        current_payment_status = transaction.get("payment_status", "pending")
        
        if stripe_payment_status != current_payment_status:
            from datetime import datetime
            
            update_data = {
                "payment_status": stripe_payment_status,
                "stripe_status": status_data["status"],
                "updated_at": datetime.utcnow()
            }
            
            # Mark completion time for successful payments
            if stripe_payment_status == "paid" and current_payment_status != "paid":
                update_data["completed_at"] = datetime.utcnow()
                
                # Activate user subscription using existing users collection
                await activate_user_subscription_legacy(
                    transaction["user_id"], 
                    transaction, 
                    users_collection
                )
                
                logger.info(f"Payment completed for session {session_id}")
            
            # Update transaction record
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
        logger.error(f"Integrated status check failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to check payment status")

async def activate_user_subscription_legacy(user_id: str, transaction: dict, users_collection):
    """
    Activate user subscription - compatible with existing user structure
    """
    try:
        from datetime import datetime
        
        # Calculate subscription dates
        now = datetime.utcnow()
        
        # Add 30 days to current date
        import calendar
        if now.month == 12:
            subscription_end = datetime(now.year + 1, 1, now.day)
        else:
            # Handle month-end edge cases
            next_month = now.month + 1
            next_year = now.year
            try:
                subscription_end = datetime(next_year, next_month, now.day)
            except ValueError:
                # Handle cases where next month doesn't have the same day (e.g., Jan 31 -> Feb 28)
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
            # Reset usage counters for new subscription
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
            logger.info(f"Subscription activated for user {user_id} (legacy integration)")
        else:
            logger.error(f"Failed to activate subscription for user {user_id}")
        
    except Exception as e:
        logger.error(f"Failed to activate subscription (legacy): {e}")

# Webhook handler for integration
async def stripe_webhook_integrated(request: Request, db: AsyncIOMotorDatabase):
    """
    Webhook handler that integrates with existing database structure
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
            await handle_payment_success_integrated(webhook_response, db)
        elif webhook_response.event_type == "payment_intent.payment_failed":
            await handle_payment_failure_integrated(webhook_response, db)
        
        logger.info(f"Webhook processed: {webhook_response.event_type}")
        return {"received": True}
        
    except Exception as e:
        logger.error(f"Webhook processing failed: {e}")
        raise HTTPException(status_code=400, detail="Webhook processing failed")

async def handle_payment_success_integrated(webhook_response, db):
    """Handle successful payment webhook - integrated version"""
    try:
        session_id = webhook_response.session_id
        payment_status = webhook_response.payment_status
        
        if payment_status == "paid":
            from datetime import datetime
            
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
                await activate_user_subscription_legacy(
                    transaction["user_id"], 
                    transaction, 
                    db.users
                )
        
    except Exception as e:
        logger.error(f"Failed to handle payment success (integrated): {e}")

async def handle_payment_failure_integrated(webhook_response, db):
    """Handle failed payment webhook - integrated version"""
    try:
        session_id = webhook_response.session_id
        from datetime import datetime
        
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
        logger.error(f"Failed to handle payment failure (integrated): {e}")