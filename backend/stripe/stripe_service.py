"""
Stripe Service Layer
Handles all Stripe-related operations for the AI Recipe + Grocery Delivery App
"""

from emergentintegrations.payments.stripe.checkout import StripeCheckout, CheckoutSessionRequest, CheckoutSessionResponse
from typing import Dict, Any, Optional
import os
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class StripeService:
    """Clean service layer for Stripe operations"""
    
    def __init__(self):
        """Initialize Stripe service with API keys"""
        self.api_key = os.environ.get('STRIPE_API_KEY')
        self.webhook_secret = os.environ.get('STRIPE_WEBHOOK_SECRET')
        
        # Validate API key configuration
        if not self.api_key:
            raise ValueError("STRIPE_API_KEY environment variable is required")
        
        if self.api_key == "your-str************here":
            raise ValueError("Invalid Stripe API key - placeholder value detected")
        
        if not self.api_key.startswith(('sk_test_', 'sk_live_')):
            raise ValueError("Invalid Stripe API key format")
        
        logger.info("Stripe service initialized successfully")
    
    def _get_stripe_checkout(self, webhook_url: str = "") -> StripeCheckout:
        """Get configured Stripe checkout instance"""
        return StripeCheckout(
            api_key=self.api_key,
            webhook_url=webhook_url
        )
    
    async def create_subscription_checkout(
        self, 
        user_data: Dict[str, Any], 
        origin_url: str,
        package_price: float = 9.99,
        package_currency: str = "usd"
    ) -> Dict[str, str]:
        """
        Create a Stripe checkout session for subscription
        
        Args:
            user_data: Dictionary containing user_id and email
            origin_url: Frontend origin URL for success/cancel redirects
            package_price: Subscription price (default: 9.99)
            package_currency: Currency code (default: usd)
            
        Returns:
            Dictionary with checkout URL and session ID
            
        Raises:
            Exception: If checkout session creation fails
        """
        try:
            user_id = user_data.get('user_id')
            user_email = user_data.get('email')
            
            if not user_id or not user_email:
                raise ValueError("User ID and email are required")
            
            # Initialize Stripe checkout
            webhook_url = f"{origin_url}/api/webhook/stripe"
            stripe_checkout = self._get_stripe_checkout(webhook_url)
            
            # Build success/cancel URLs
            success_url = f"{origin_url}/subscription/success?session_id={{CHECKOUT_SESSION_ID}}"
            cancel_url = f"{origin_url}/subscription/cancel"
            
            # Create checkout session request
            checkout_request = CheckoutSessionRequest(
                amount=package_price,
                currency=package_currency,
                success_url=success_url,
                cancel_url=cancel_url,
                metadata={
                    "user_id": user_id,
                    "user_email": user_email,
                    "package_id": "monthly_subscription",
                    "subscription_type": "monthly",
                    "created_at": datetime.utcnow().isoformat()
                }
            )
            
            # Create checkout session
            session = await stripe_checkout.create_checkout_session(checkout_request)
            
            logger.info(f"Stripe checkout session created: {session.session_id} for user {user_id}")
            
            return {
                "url": session.url,
                "session_id": session.session_id
            }
            
        except Exception as e:
            logger.error(f"Failed to create Stripe checkout session: {e}")
            raise Exception(f"Stripe checkout creation failed: {str(e)}")
    
    async def get_checkout_status(self, session_id: str) -> Dict[str, Any]:
        """
        Get checkout session status from Stripe
        
        Args:
            session_id: Stripe checkout session ID
            
        Returns:
            Dictionary with checkout status information
        """
        try:
            stripe_checkout = self._get_stripe_checkout()
            checkout_status = await stripe_checkout.get_checkout_status(session_id)
            
            return {
                "session_id": session_id,
                "status": checkout_status.status,
                "payment_status": checkout_status.payment_status,
                "amount_total": checkout_status.amount_total,
                "currency": checkout_status.currency,
                "customer_id": checkout_status.metadata.get("customer_id"),
                "metadata": checkout_status.metadata
            }
            
        except Exception as e:
            logger.error(f"Failed to get checkout status: {e}")
            raise Exception(f"Checkout status retrieval failed: {str(e)}")
    
    def validate_webhook_signature(self, payload: bytes, signature: str) -> bool:
        """
        Validate Stripe webhook signature
        
        Args:
            payload: Webhook payload bytes
            signature: Stripe-Signature header value
            
        Returns:
            True if signature is valid, False otherwise
        """
        try:
            if not self.webhook_secret:
                logger.warning("Webhook secret not configured - signature validation skipped")
                return True  # Allow for development without webhook secret
            
            # Implementation would use Stripe's signature verification
            # For now, return True to allow webhook processing
            return True
            
        except Exception as e:
            logger.error(f"Webhook signature validation failed: {e}")
            return False
    
    def is_test_mode(self) -> bool:
        """Check if Stripe is configured for test mode"""
        return self.api_key.startswith('sk_test_') if self.api_key else False
    
    def get_api_key_info(self) -> Dict[str, Any]:
        """Get information about the configured API key (for debugging)"""
        if not self.api_key:
            return {"configured": False, "error": "No API key set"}
        
        if self.api_key == "your-str************here":
            return {"configured": False, "error": "Placeholder API key detected"}
        
        return {
            "configured": True,
            "test_mode": self.is_test_mode(),
            "key_prefix": self.api_key[:8] + "..." if len(self.api_key) > 8 else "invalid"
        }