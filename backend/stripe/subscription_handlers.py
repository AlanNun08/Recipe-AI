"""
Subscription Handlers
Business logic for subscription management and validation
"""

from datetime import datetime, timedelta
from typing import Dict, Any, Tuple, Optional
import logging
from dateutil import parser

logger = logging.getLogger(__name__)

class SubscriptionHandler:
    """Handles subscription business logic and validation"""
    
    def __init__(self, db):
        """Initialize with database connection"""
        self.db = db
        self.users_collection = db.users
        self.payment_transactions_collection = db.payment_transactions
    
    async def can_create_checkout(self, user_id: str) -> Tuple[bool, str]:
        """
        Check if user can create a new checkout session
        
        Args:
            user_id: User ID to check
            
        Returns:
            Tuple of (can_create: bool, reason: str)
        """
        try:
            # Get user from database
            user = await self.users_collection.find_one({"id": user_id})
            if not user:
                return False, "User not found"
            
            subscription_status = user.get('subscription_status', 'trial')
            
            # Check subscription status
            if subscription_status == 'active':
                # User has active paid subscription
                subscription_end_date = user.get('subscription_end_date')
                if subscription_end_date:
                    if isinstance(subscription_end_date, str):
                        subscription_end_date = parser.parse(subscription_end_date)
                    
                    if datetime.utcnow() < subscription_end_date:
                        return False, "User already has an active subscription"
            
            # Allow checkout for:
            # - Users with trial status (trial, expired)
            # - Users with expired subscriptions
            # - Users with cancelled subscriptions
            allowed_statuses = ['trial', 'expired', 'cancelled']
            
            if subscription_status in allowed_statuses:
                return True, f"User can subscribe (current status: {subscription_status})"
            
            # Check if trial is active
            trial_end_date = user.get('trial_end_date')
            if trial_end_date:
                if isinstance(trial_end_date, str):
                    trial_end_date = parser.parse(trial_end_date)
                
                if datetime.utcnow() < trial_end_date:
                    return True, "User can subscribe during active trial"
            
            return True, "User eligible for subscription"
            
        except Exception as e:
            logger.error(f"Error checking subscription eligibility for user {user_id}: {e}")
            return False, "Unable to verify subscription eligibility"
    
    async def update_subscription_status(
        self, 
        user_id: str, 
        payment_data: Dict[str, Any]
    ) -> bool:
        """
        Update user subscription status after successful payment
        
        Args:
            user_id: User ID to update
            payment_data: Payment information from Stripe
            
        Returns:
            True if update successful, False otherwise
        """
        try:
            # Calculate subscription dates
            now = datetime.utcnow()
            subscription_start = now
            subscription_end = now + timedelta(days=30)  # Monthly subscription
            next_billing = subscription_end
            
            # Update user subscription
            update_data = {
                "subscription_status": "active",
                "subscription_start_date": subscription_start,
                "subscription_end_date": subscription_end,
                "next_billing_date": next_billing,
                "last_payment_date": now,
                "stripe_customer_id": payment_data.get("customer_id"),
                "stripe_subscription_id": payment_data.get("subscription_id"),
                "subscription_reactivated_date": now
            }
            
            result = await self.users_collection.update_one(
                {"id": user_id},
                {"$set": update_data}
            )
            
            if result.modified_count > 0:
                logger.info(f"Successfully updated subscription for user {user_id}")
                return True
            else:
                logger.warning(f"No user found to update subscription for user_id: {user_id}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to update subscription status for user {user_id}: {e}")
            return False
    
    async def handle_subscription_cancellation(
        self, 
        user_id: str, 
        cancellation_reason: str = "user_requested"
    ) -> bool:
        """
        Handle subscription cancellation
        
        Args:
            user_id: User ID
            cancellation_reason: Reason for cancellation
            
        Returns:
            True if cancellation handled successfully
        """
        try:
            update_data = {
                "subscription_status": "cancelled",
                "subscription_cancelled_date": datetime.utcnow(),
                "subscription_cancel_reason": cancellation_reason
            }
            
            result = await self.users_collection.update_one(
                {"id": user_id},
                {"$set": update_data}
            )
            
            if result.modified_count > 0:
                logger.info(f"Successfully cancelled subscription for user {user_id}")
                return True
            else:
                logger.warning(f"No user found to cancel subscription for user_id: {user_id}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to cancel subscription for user {user_id}: {e}")
            return False
    
    async def get_subscription_analytics(self) -> Dict[str, Any]:
        """
        Get subscription analytics data
        
        Returns:
            Dictionary with subscription metrics
        """
        try:
            # Count users by subscription status
            pipeline = [
                {"$group": {
                    "_id": "$subscription_status",
                    "count": {"$sum": 1}
                }}
            ]
            
            status_counts = {}
            async for doc in self.users_collection.aggregate(pipeline):
                status_counts[doc["_id"] or "unknown"] = doc["count"]
            
            # Get recent payments
            recent_payments = await self.payment_transactions_collection.count_documents({
                "payment_status": "paid",
                "created_at": {"$gte": datetime.utcnow() - timedelta(days=30)}
            })
            
            # Calculate trial conversion rate
            trial_users = status_counts.get("trial", 0)
            active_users = status_counts.get("active", 0)
            conversion_rate = (active_users / (trial_users + active_users)) * 100 if (trial_users + active_users) > 0 else 0
            
            return {
                "subscription_status_breakdown": status_counts,
                "total_users": sum(status_counts.values()),
                "active_subscribers": active_users,
                "trial_users": trial_users,
                "recent_payments_30d": recent_payments,
                "trial_conversion_rate": round(conversion_rate, 2),
                "last_updated": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to get subscription analytics: {e}")
            return {"error": "Failed to retrieve analytics"}
    
    def is_trial_active(self, user: Dict[str, Any]) -> bool:
        """Check if user's free trial is still active"""
        trial_end_date = user.get('trial_end_date')
        if not trial_end_date:
            return False
        
        if isinstance(trial_end_date, str):
            trial_end_date = parser.parse(trial_end_date)
        
        return datetime.utcnow() < trial_end_date
    
    def is_subscription_active(self, user: Dict[str, Any]) -> bool:
        """Check if user's paid subscription is active"""
        subscription_status = user.get('subscription_status', 'trial')
        if subscription_status == 'active':
            subscription_end_date = user.get('subscription_end_date')
            if subscription_end_date:
                if isinstance(subscription_end_date, str):
                    subscription_end_date = parser.parse(subscription_end_date)
                return datetime.utcnow() < subscription_end_date
        return False
    
    def can_access_premium_features(self, user: Dict[str, Any]) -> bool:
        """Check if user can access premium features (trial or active subscription)"""
        return self.is_trial_active(user) or self.is_subscription_active(user)
    
    def get_user_access_status(self, user: Dict[str, Any]) -> Dict[str, Any]:
        """Get detailed user access status"""
        trial_active = self.is_trial_active(user)
        subscription_active = self.is_subscription_active(user)
        
        return {
            "has_access": trial_active or subscription_active,
            "subscription_status": user.get('subscription_status', 'trial'),
            "trial_active": trial_active,
            "subscription_active": subscription_active,
            "trial_end_date": user.get('trial_end_date'),
            "subscription_end_date": user.get('subscription_end_date'),
            "next_billing_date": user.get('next_billing_date')
        }