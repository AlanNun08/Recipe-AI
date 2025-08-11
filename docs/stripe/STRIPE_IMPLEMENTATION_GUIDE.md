# Stripe Payment System - Implementation Guide

## 🎯 Overview

This guide provides step-by-step instructions for implementing the complete Stripe payment system fix for the AI Recipe + Grocery Delivery App.

## 📋 Prerequisites

### Required Stripe Account Setup
1. **Create Stripe Account**: https://dashboard.stripe.com/register
2. **Verify Business Information**
3. **Obtain API Keys**:
   - Test Secret Key: `sk_test_...`
   - Test Publishable Key: `pk_test_...`
   - Live Secret Key: `sk_live_...` (for production)
   - Live Publishable Key: `pk_live_...` (for production)

### Environment Variables Required
```bash
# Backend .env file
STRIPE_API_KEY=sk_test_your_actual_key_here
STRIPE_PUBLISHABLE_KEY=pk_test_your_actual_key_here
STRIPE_WEBHOOK_SECRET=whsec_your_webhook_secret_here
```

## 🔧 Implementation Steps

### Step 1: Backend Service Layer Creation

Create dedicated Stripe service files for clean separation of concerns:

#### A. Stripe Service (`/app/backend/stripe/stripe_service.py`)
```python
from emergentintegrations.payments.stripe.checkout import StripeCheckout
from typing import Dict, Any
import os
import logging

logger = logging.getLogger(__name__)

class StripeService:
    def __init__(self):
        self.api_key = os.environ.get('STRIPE_API_KEY')
        self.webhook_secret = os.environ.get('STRIPE_WEBHOOK_SECRET')
        
        if not self.api_key:
            raise ValueError("STRIPE_API_KEY environment variable is required")
            
        self.stripe_checkout = StripeCheckout(
            api_key=self.api_key,
            webhook_url=""  # Will be set per request
        )
    
    async def create_subscription_checkout(self, user_data: Dict[str, Any], origin_url: str) -> Dict[str, str]:
        """Create a Stripe checkout session for subscription"""
        try:
            # Implementation details in actual file
            pass
        except Exception as e:
            logger.error(f"Stripe checkout creation failed: {e}")
            raise
```

#### B. Subscription Handlers (`/app/backend/stripe/subscription_handlers.py`)
```python
from datetime import datetime, timedelta
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

class SubscriptionHandler:
    def __init__(self, db):
        self.db = db
        self.users_collection = db.users
    
    async def can_create_checkout(self, user_id: str) -> tuple[bool, str]:
        """Check if user can create a new checkout session"""
        # Implementation details in actual file
        pass
    
    async def update_subscription_status(self, user_id: str, payment_data: Dict[str, Any]) -> bool:
        """Update user subscription after successful payment"""
        # Implementation details in actual file
        pass
```

### Step 2: Fixed Backend Endpoints

#### A. Enhanced Create Checkout Endpoint
```python
@api_router.post("/subscription/create-checkout")
async def create_subscription_checkout(request: SubscriptionCheckoutRequest):
    """Create Stripe checkout session for subscription - FIXED VERSION"""
    try:
        # Validate Stripe configuration
        if not STRIPE_API_KEY or STRIPE_API_KEY == "your-str************here":
            logger.error("Invalid Stripe API key configuration")
            raise HTTPException(
                status_code=500, 
                detail="Payment system not configured. Please contact support."
            )
        
        # Validate user exists
        user = await users_collection.find_one({"id": request.user_id})
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Check subscription eligibility
        subscription_handler = SubscriptionHandler(db)
        can_checkout, reason = await subscription_handler.can_create_checkout(request.user_id)
        
        if not can_checkout:
            raise HTTPException(status_code=400, detail=reason)
        
        # Create checkout session
        stripe_service = StripeService()
        session_data = await stripe_service.create_subscription_checkout(
            user_data={
                "user_id": request.user_id,
                "email": request.user_email
            },
            origin_url=request.origin_url
        )
        
        return session_data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Checkout creation error: {e}")
        raise HTTPException(status_code=500, detail="Failed to create checkout session")
```

#### B. Webhook Handler Endpoint
```python
@api_router.post("/webhook/stripe")
async def stripe_webhook(request: Request):
    """Handle Stripe webhook events"""
    try:
        payload = await request.body()
        sig_header = request.headers.get('stripe-signature')
        
        webhook_handler = WebhookHandler(db)
        await webhook_handler.process_webhook(payload, sig_header)
        
        return {"received": True}
        
    except Exception as e:
        logger.error(f"Webhook processing error: {e}")
        raise HTTPException(status_code=400, detail="Webhook processing failed")
```

### Step 3: Frontend Integration Updates

#### A. Enhanced Subscription Screen (`/app/frontend/src/components/SubscriptionScreen.js`)
```javascript
const SubscriptionScreen = ({ user, onClose, onSubscriptionUpdate }) => {
  const [error, setError] = useState('');
  const [processingPayment, setProcessingPayment] = useState(false);
  
  const handleSubscribe = async () => {
    try {
      setProcessingPayment(true);
      setError('');

      const response = await fetch(`${backendUrl}/api/subscription/create-checkout`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          user_id: user.id,
          user_email: user.email,
          origin_url: window.location.origin
        })
      });

      if (response.ok) {
        const { url } = await response.json();
        window.location.href = url;
      } else {
        const errorData = await response.json();
        
        // Enhanced error handling
        if (response.status === 500 && errorData.detail.includes('not configured')) {
          setError('Payment system is temporarily unavailable. Please try again later or contact support.');
        } else if (response.status === 400) {
          setError(errorData.detail || 'Unable to create subscription at this time.');
        } else {
          setError('An unexpected error occurred. Please try again.');
        }
      }
    } catch (error) {
      setError('Network error. Please check your connection and try again.');
    } finally {
      setProcessingPayment(false);
    }
  };
  
  // Rest of component implementation
};
```

### Step 4: Database Schema Updates

#### A. Enhanced Payment Transaction Model
```python
class PaymentTransaction(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    email: str
    session_id: str
    payment_status: str = "pending"  # pending, paid, failed, expired, cancelled
    amount: float
    currency: str = "usd"
    stripe_customer_id: Optional[str] = None
    stripe_subscription_id: Optional[str] = None
    metadata: Dict[str, str] = {}
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    failure_reason: Optional[str] = None
```

### Step 5: Testing Implementation

#### A. Backend Testing Script
```python
# /app/tests/stripe/test_stripe_integration.py
import pytest
import asyncio
from httpx import AsyncClient

class TestStripeIntegration:
    async def test_create_checkout_with_valid_user(self):
        """Test checkout creation with valid user during trial"""
        # Implementation details
        pass
    
    async def test_create_checkout_with_invalid_api_key(self):
        """Test error handling with invalid Stripe API key"""
        # Implementation details
        pass
    
    async def test_webhook_processing(self):
        """Test Stripe webhook event processing"""
        # Implementation details
        pass
```

## 🚀 Deployment Steps

### Development Environment
1. **Update Environment Variables**
   ```bash
   # In /app/backend/.env
   STRIPE_API_KEY=sk_test_your_test_key_here
   STRIPE_PUBLISHABLE_KEY=pk_test_your_test_key_here
   ```

2. **Restart Backend Service**
   ```bash
   sudo supervisorctl restart backend
   ```

3. **Test Payment Flow**
   - Login as demo user
   - Navigate to subscription screen
   - Attempt to create checkout session
   - Verify success/error handling

### Production Environment
1. **Update Production Environment Variables**
   ```bash
   # In production .env
   STRIPE_API_KEY=sk_live_your_live_key_here
   STRIPE_PUBLISHABLE_KEY=pk_live_your_live_key_here
   ```

2. **Configure Webhook Endpoint**
   - Stripe Dashboard → Webhooks
   - Add endpoint: `https://buildyoursmartcart.com/api/webhook/stripe`
   - Select events: `checkout.session.completed`, `invoice.payment_succeeded`

3. **Deploy Changes**
   ```bash
   # Deploy updated code with API keys
   ./deploy.sh
   ```

## 📊 Success Verification

### Functional Tests
- [ ] User can create checkout during trial
- [ ] User can create checkout after trial expires
- [ ] User with active subscription gets appropriate message
- [ ] Payment success updates subscription status
- [ ] Failed payments are handled gracefully

### Technical Tests
- [ ] Valid API keys configured
- [ ] Webhook endpoint responds correctly
- [ ] Error handling returns appropriate HTTP codes
- [ ] Logging captures all payment events

## 🆘 Troubleshooting

### Common Issues
1. **"Payment system not configured"**
   - Check STRIPE_API_KEY environment variable
   - Verify API key format (starts with sk_test_ or sk_live_)

2. **"User already has active subscription"**
   - Check user's subscription_status in database
   - Verify subscription logic in backend

3. **Webhook failures**
   - Verify webhook endpoint URL
   - Check webhook secret configuration
   - Review Stripe dashboard webhook logs

## 📞 Support

- **Stripe Documentation**: https://stripe.com/docs
- **Integration Issues**: Check backend logs at `/var/log/supervisor/backend.err.log`
- **Testing**: Use Stripe test cards for development

---

**Next Document**: [STRIPE_TROUBLESHOOTING_GUIDE.md](./STRIPE_TROUBLESHOOTING_GUIDE.md)