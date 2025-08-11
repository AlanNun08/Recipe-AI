# Stripe Payment System - Troubleshooting Guide

## 🔧 Common Issues & Solutions

### 1. "Payment system not configured" Error

**Symptoms:**
- Users see "Payment system not configured. Please contact support."
- Backend logs show "Invalid Stripe API key configuration"

**Root Causes:**
- `STRIPE_API_KEY` environment variable not set
- `STRIPE_API_KEY` contains placeholder value `your-str************here`
- Invalid API key format

**Solutions:**
```bash
# Check current API key
echo $STRIPE_API_KEY

# Update with valid key
export STRIPE_API_KEY=sk_test_your_actual_key_here

# Restart backend
sudo supervisorctl restart backend
```

**Prevention:**
- Always validate API keys on service startup
- Use proper key format validation
- Set up monitoring for configuration issues

### 2. "User already has active subscription" Error

**Symptoms:**
- Users with trial status cannot subscribe
- Error occurs even during free trial period

**Root Causes:**
- Incorrect subscription status logic
- Database inconsistency
- Cached subscription data

**Solutions:**
```python
# Check user's actual subscription status
user = await users_collection.find_one({"email": "user@example.com"})
print(user.get('subscription_status'))
print(user.get('trial_end_date'))

# Fix subscription logic in create_checkout endpoint
# Use SubscriptionHandler.can_create_checkout() method
```

**Prevention:**
- Use centralized subscription logic
- Regular database consistency checks
- Clear subscription state management

### 3. Webhook Processing Failures

**Symptoms:**
- Payments succeed but subscriptions don't activate
- Stripe dashboard shows webhook failures
- Users charged but still see trial status

**Root Causes:**
- Missing webhook endpoint configuration
- Invalid webhook signature verification
- Database update failures

**Solutions:**
```bash
# Check webhook endpoint in Stripe dashboard
# URL should be: https://your-domain.com/api/webhook/stripe

# Test webhook endpoint
curl -X POST https://your-domain.com/api/webhook/stripe \
  -H "Content-Type: application/json" \
  -d '{"type":"test"}'

# Check backend logs for webhook errors
tail -f /var/log/supervisor/backend.err.log | grep webhook
```

**Prevention:**
- Set up webhook monitoring
- Implement proper error handling
- Use webhook event logging

### 4. Frontend Checkout Flow Issues

**Symptoms:**
- Checkout button doesn't work
- "Processing..." state never clears
- Network errors during checkout creation

**Root Causes:**
- CORS configuration issues
- Frontend API URL misconfiguration
- Network connectivity problems

**Solutions:**
```javascript
// Check frontend API configuration
console.log(process.env.REACT_APP_BACKEND_URL);

// Test API connectivity
fetch(`${process.env.REACT_APP_BACKEND_URL}/api/health`)
  .then(response => response.json())
  .then(data => console.log('API Status:', data));

// Check browser network tab for failed requests
```

**Prevention:**
- Proper environment variable configuration
- Network connectivity monitoring
- Frontend error boundary implementation

## 🔍 Debugging Procedures

### Backend Debugging

**1. Check Service Configuration:**
```python
# Add to server.py startup
from stripe.stripe_service import StripeService

try:
    stripe_service = StripeService()
    logger.info(f"Stripe configured: {stripe_service.get_api_key_info()}")
except Exception as e:
    logger.error(f"Stripe configuration error: {e}")
```

**2. Monitor Payment Flow:**
```bash
# Watch backend logs
tail -f /var/log/supervisor/backend.*.log | grep -i stripe

# Check database records
# Connect to MongoDB and check payment_transactions collection
```

**3. Test Endpoints Manually:**
```bash
# Test subscription status
curl -X GET "http://localhost:8001/api/subscription/status/user_id_here"

# Test checkout creation
curl -X POST "http://localhost:8001/api/subscription/create-checkout" \
  -H "Content-Type: application/json" \
  -d '{"user_id":"test","user_email":"test@example.com","origin_url":"http://localhost:3000"}'
```

### Frontend Debugging

**1. Check API Calls:**
```javascript
// Add debugging to SubscriptionScreen.js
const handleSubscribe = async () => {
  console.log('Starting subscription process...');
  try {
    const response = await fetch(`${backendUrl}/api/subscription/create-checkout`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(checkoutRequest)
    });
    
    console.log('Response status:', response.status);
    console.log('Response headers:', response.headers);
    
    if (response.ok) {
      const data = await response.json();
      console.log('Checkout data:', data);
    } else {
      const error = await response.json();
      console.log('Error response:', error);
    }
  } catch (error) {
    console.error('Network error:', error);
  }
};
```

**2. Validate Environment Variables:**
```javascript
// Add to component or console
console.log('Backend URL:', process.env.REACT_APP_BACKEND_URL);
console.log('Environment:', process.env.NODE_ENV);
```

## 📊 Monitoring & Alerting

### Key Metrics to Monitor

**1. Payment Success Rate:**
- Target: >98% payment success rate
- Alert if: Success rate drops below 95%

**2. Subscription Activation Rate:**
- Target: >99% of successful payments result in subscription activation
- Alert if: Activation rate drops below 95%

**3. Webhook Processing:**
- Target: >99% webhook success rate
- Alert if: Webhook failures increase

**4. API Response Times:**
- Target: <2 seconds for checkout creation
- Alert if: Response time >5 seconds

### Monitoring Implementation

**1. Backend Logging:**
```python
# Add structured logging to payment endpoints
import json

@api_router.post("/subscription/create-checkout")
async def create_subscription_checkout(request: SubscriptionCheckoutRequest):
    start_time = time.time()
    try:
        # ... payment logic ...
        
        duration = time.time() - start_time
        logger.info(json.dumps({
            "event": "checkout_created",
            "user_id": request.user_id,
            "duration": duration,
            "success": True
        }))
        
    except Exception as e:
        duration = time.time() - start_time
        logger.error(json.dumps({
            "event": "checkout_failed",
            "user_id": request.user_id,
            "duration": duration,
            "error": str(e),
            "success": False
        }))
```

**2. Database Monitoring:**
```python
# Monitor subscription status changes
async def log_subscription_change(user_id: str, old_status: str, new_status: str):
    logger.info(json.dumps({
        "event": "subscription_status_change",
        "user_id": user_id,
        "old_status": old_status,
        "new_status": new_status,
        "timestamp": datetime.utcnow().isoformat()
    }))
```

## 🆘 Emergency Procedures

### Critical Payment System Failure

**1. Immediate Actions:**
- Check Stripe dashboard for service status
- Verify API key validity
- Review recent deployments
- Check database connectivity

**2. Temporary Workaround:**
- Enable maintenance mode message
- Direct users to alternative payment method
- Collect email addresses for follow-up

**3. Communication:**
- Notify users of temporary issue
- Provide estimated resolution time
- Update status page if available

### Data Recovery

**If payments succeeded but subscriptions not activated:**
```python
# Recovery script to fix subscription statuses
async def fix_subscription_statuses():
    # Find payments marked as 'paid' but users still on trial
    paid_transactions = await payment_transactions_collection.find({
        "payment_status": "paid"
    }).to_list(None)
    
    for transaction in paid_transactions:
        user = await users_collection.find_one({"id": transaction["user_id"]})
        
        if user and user.get('subscription_status') == 'trial':
            # Fix subscription status
            subscription_handler = SubscriptionHandler(db)
            await subscription_handler.update_subscription_status(
                transaction["user_id"],
                {"customer_id": "recovery", "amount": transaction["amount"]}
            )
            print(f"Fixed subscription for user {transaction['user_id']}")
```

## 📞 Support Contacts

### Internal Support
- **Backend Issues**: Check supervisor logs at `/var/log/supervisor/backend.*.log`
- **Database Issues**: MongoDB connection and query debugging
- **API Issues**: Network connectivity and CORS configuration

### External Support
- **Stripe Support**: https://support.stripe.com
- **Stripe Status**: https://status.stripe.com
- **Stripe Documentation**: https://stripe.com/docs

### Escalation Procedures
1. **Level 1**: Check common issues in this guide
2. **Level 2**: Review system logs and database state
3. **Level 3**: Contact Stripe support with specific error details
4. **Level 4**: Consider temporary system maintenance

---

**Document Version**: 1.0  
**Last Updated**: January 2025  
**Author**: AI Development Team