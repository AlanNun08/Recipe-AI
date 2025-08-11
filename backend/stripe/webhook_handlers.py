"""
Stripe Webhook Handlers
Processes Stripe webhook events for subscription management
"""

import json
import logging
from typing import Dict, Any, Optional
from datetime import datetime
from stripe.subscription_handlers import SubscriptionHandler

logger = logging.getLogger(__name__)

class WebhookHandler:
    """Handles Stripe webhook events"""
    
    def __init__(self, db):
        """Initialize webhook handler with database connection"""
        self.db = db
        self.subscription_handler = SubscriptionHandler(db)
        self.payment_transactions_collection = db.payment_transactions
    
    async def process_webhook(self, payload: bytes, signature: str) -> bool:
        """
        Process Stripe webhook event
        
        Args:
            payload: Webhook payload from Stripe
            signature: Stripe signature header
            
        Returns:
            True if processing successful, False otherwise
        """
        try:
            # Parse webhook payload
            try:
                event = json.loads(payload.decode('utf-8'))
            except json.JSONDecodeError as e:
                logger.error(f"Invalid JSON in webhook payload: {e}")
                return False
            
            event_type = event.get('type')
            event_data = event.get('data', {}).get('object', {})
            
            logger.info(f"Processing Stripe webhook event: {event_type}")
            
            # Route to appropriate handler
            if event_type == 'checkout.session.completed':
                return await self._handle_checkout_completed(event_data)
            elif event_type == 'invoice.payment_succeeded':
                return await self._handle_payment_succeeded(event_data)
            elif event_type == 'invoice.payment_failed':
                return await self._handle_payment_failed(event_data)
            elif event_type == 'customer.subscription.updated':
                return await self._handle_subscription_updated(event_data)
            elif event_type == 'customer.subscription.deleted':
                return await self._handle_subscription_cancelled(event_data)
            else:
                logger.info(f"Unhandled webhook event type: {event_type}")
                return True  # Success for unhandled events
                
        except Exception as e:
            logger.error(f"Webhook processing error: {e}")
            return False
    
    async def _handle_checkout_completed(self, checkout_session: Dict[str, Any]) -> bool:
        """Handle successful checkout completion"""
        try:
            session_id = checkout_session.get('id')
            payment_status = checkout_session.get('payment_status')
            metadata = checkout_session.get('metadata', {})
            user_id = metadata.get('user_id')
            
            if not user_id:
                logger.error(f"No user_id in checkout session metadata: {session_id}")
                return False
            
            # Update transaction status
            await self.payment_transactions_collection.update_one(
                {"session_id": session_id},
                {
                    "$set": {
                        "payment_status": payment_status,
                        "updated_at": datetime.utcnow().isoformat(),
                        "completed_at": datetime.utcnow().isoformat() if payment_status == 'paid' else None
                    }
                }
            )
            
            # If payment successful, update subscription
            if payment_status == 'paid':
                payment_data = {
                    "customer_id": checkout_session.get('customer'),
                    "subscription_id": checkout_session.get('subscription'),
                    "amount": checkout_session.get('amount_total', 0) / 100,  # Convert from cents
                    "currency": checkout_session.get('currency', 'usd')
                }
                
                success = await self.subscription_handler.update_subscription_status(
                    user_id, payment_data
                )
                
                if success:
                    logger.info(f"Subscription activated via webhook for user {user_id}")
                else:
                    logger.error(f"Failed to activate subscription via webhook for user {user_id}")
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error handling checkout completion: {e}")
            return False
    
    async def _handle_payment_succeeded(self, invoice: Dict[str, Any]) -> bool:
        """Handle successful payment (subscription renewal)"""
        try:
            customer_id = invoice.get('customer')
            subscription_id = invoice.get('subscription')
            amount_paid = invoice.get('amount_paid', 0) / 100  # Convert from cents
            
            # Find user by Stripe customer ID
            user = await self.db.users.find_one({"stripe_customer_id": customer_id})
            if not user:
                logger.error(f"No user found for Stripe customer {customer_id}")
                return False
            
            # Update subscription with payment
            update_data = {
                "last_payment_date": datetime.utcnow(),
                "subscription_status": "active"
            }
            
            # If this is a renewal, extend subscription end date
            current_end = user.get('subscription_end_date')
            if current_end:
                from dateutil import parser
                from datetime import timedelta
                
                if isinstance(current_end, str):
                    current_end = parser.parse(current_end)
                
                # Extend by 30 days from current end date
                new_end = current_end + timedelta(days=30)
                update_data["subscription_end_date"] = new_end
                update_data["next_billing_date"] = new_end
            
            await self.db.users.update_one(
                {"id": user["id"]},
                {"$set": update_data}
            )
            
            logger.info(f"Payment processed for user {user['id']}: ${amount_paid}")
            return True
            
        except Exception as e:
            logger.error(f"Error handling payment success: {e}")
            return False
    
    async def _handle_payment_failed(self, invoice: Dict[str, Any]) -> bool:
        """Handle failed payment"""
        try:
            customer_id = invoice.get('customer')
            attempt_count = invoice.get('attempt_count', 0)
            
            # Find user by Stripe customer ID
            user = await self.db.users.find_one({"stripe_customer_id": customer_id})
            if not user:
                logger.error(f"No user found for Stripe customer {customer_id}")
                return False
            
            # Update user with payment failure info
            update_data = {
                "last_payment_attempt": datetime.utcnow(),
                "payment_failure_count": attempt_count
            }
            
            # If final attempt failed, mark subscription as expired
            if attempt_count >= 3:  # Stripe typically tries 3 times
                update_data["subscription_status"] = "expired"
                logger.warning(f"Subscription expired due to payment failure for user {user['id']}")
            
            await self.db.users.update_one(
                {"id": user["id"]},
                {"$set": update_data}
            )
            
            logger.info(f"Payment failed for user {user['id']} (attempt {attempt_count})")
            return True
            
        except Exception as e:
            logger.error(f"Error handling payment failure: {e}")
            return False
    
    async def _handle_subscription_updated(self, subscription: Dict[str, Any]) -> bool:
        """Handle subscription updates"""
        try:
            customer_id = subscription.get('customer')
            status = subscription.get('status')
            
            # Find user by Stripe customer ID
            user = await self.db.users.find_one({"stripe_customer_id": customer_id})
            if not user:
                logger.error(f"No user found for Stripe customer {customer_id}")
                return False
            
            # Map Stripe status to our status
            status_mapping = {
                'active': 'active',
                'canceled': 'cancelled',
                'incomplete': 'pending',
                'incomplete_expired': 'expired',
                'past_due': 'past_due',
                'unpaid': 'expired'
            }
            
            new_status = status_mapping.get(status, status)
            
            update_data = {
                "subscription_status": new_status,
                "stripe_subscription_status": status  # Keep original Stripe status
            }
            
            await self.db.users.update_one(
                {"id": user["id"]},
                {"$set": update_data}
            )
            
            logger.info(f"Subscription updated for user {user['id']}: {status}")
            return True
            
        except Exception as e:
            logger.error(f"Error handling subscription update: {e}")
            return False
    
    async def _handle_subscription_cancelled(self, subscription: Dict[str, Any]) -> bool:
        """Handle subscription cancellation"""
        try:
            customer_id = subscription.get('customer')
            
            # Find user by Stripe customer ID
            user = await self.db.users.find_one({"stripe_customer_id": customer_id})
            if not user:
                logger.error(f"No user found for Stripe customer {customer_id}")
                return False
            
            # Update subscription status
            success = await self.subscription_handler.handle_subscription_cancellation(
                user["id"], "stripe_cancellation"
            )
            
            if success:
                logger.info(f"Subscription cancelled for user {user['id']}")
            else:
                logger.error(f"Failed to cancel subscription for user {user['id']}")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error handling subscription cancellation: {e}")
            return False