# Stripe Payment System - Testing Procedures

## 🧪 Testing Overview

This document outlines comprehensive testing procedures for the Stripe payment system, covering unit tests, integration tests, and end-to-end testing scenarios.

## 📋 Testing Checklist

### Pre-Testing Setup
- [ ] Valid Stripe test API keys configured
- [ ] Backend service running on port 8001
- [ ] Frontend service running on port 3000
- [ ] MongoDB connection established
- [ ] Test database cleaned/reset

### Core Functionality Tests
- [ ] User subscription status retrieval
- [ ] Checkout session creation (trial users)
- [ ] Checkout session creation (expired trial users)
- [ ] Checkout session blocking (active subscribers)
- [ ] Payment completion and subscription activation
- [ ] Webhook event processing
- [ ] Error handling and edge cases

## 🔬 Unit Testing

### Backend Unit Tests

#### Test File: `/app/tests/stripe/test_stripe_service.py`

```python
import pytest
import asyncio
from unittest.mock import Mock, patch
from stripe.stripe_service import StripeService

class TestStripeService:
    
    def test_stripe_service_initialization_valid_key(self):
        """Test StripeService initializes with valid API key"""
        with patch.dict('os.environ', {'STRIPE_API_KEY': 'sk_test_valid_key'}):
            service = StripeService()
            assert service.api_key == 'sk_test_valid_key'
            assert service.is_test_mode() == True
    
    def test_stripe_service_initialization_invalid_key(self):
        """Test StripeService fails with invalid API key"""
        with patch.dict('os.environ', {'STRIPE_API_KEY': 'invalid_key'}):
            with pytest.raises(ValueError, match="Invalid Stripe API key format"):
                StripeService()
    
    def test_stripe_service_initialization_placeholder_key(self):
        """Test StripeService fails with placeholder key"""
        with patch.dict('os.environ', {'STRIPE_API_KEY': 'your-str************here'}):
            with pytest.raises(ValueError, match="placeholder value detected"):
                StripeService()
    
    @pytest.mark.asyncio
    async def test_create_subscription_checkout_success(self):
        """Test successful checkout session creation"""
        with patch.dict('os.environ', {'STRIPE_API_KEY': 'sk_test_valid_key'}):
            service = StripeService()
            
            # Mock Stripe response
            mock_session = Mock()
            mock_session.url = "https://checkout.stripe.com/test_session"
            mock_session.session_id = "cs_test_session_id"
            
            with patch.object(service, '_get_stripe_checkout') as mock_checkout:
                mock_checkout.return_value.create_checkout_session = Mock(return_value=mock_session)
                
                result = await service.create_subscription_checkout(
                    user_data={"user_id": "test_user", "email": "test@example.com"},
                    origin_url="http://localhost:3000"
                )
                
                assert result["url"] == "https://checkout.stripe.com/test_session"
                assert result["session_id"] == "cs_test_session_id"
```

#### Test File: `/app/tests/stripe/test_subscription_handlers.py`

```python
import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, Mock
from stripe.subscription_handlers import SubscriptionHandler

class TestSubscriptionHandler:
    
    @pytest.fixture
    def mock_db(self):
        """Mock database for testing"""
        db = Mock()
        db.users = AsyncMock()
        db.payment_transactions = AsyncMock()
        return db
    
    @pytest.fixture
    def subscription_handler(self, mock_db):
        """Create SubscriptionHandler instance for testing"""
        return SubscriptionHandler(mock_db)
    
    @pytest.mark.asyncio
    async def test_can_create_checkout_trial_user(self, subscription_handler, mock_db):
        """Test trial user can create checkout"""
        # Mock user data
        mock_user = {
            "id": "test_user",
            "subscription_status": "trial",
            "trial_end_date": datetime.utcnow() + timedelta(days=5)
        }
        mock_db.users.find_one.return_value = mock_user
        
        can_create, reason = await subscription_handler.can_create_checkout("test_user")
        
        assert can_create == True
        assert "trial" in reason.lower()
    
    @pytest.mark.asyncio
    async def test_cannot_create_checkout_active_subscription(self, subscription_handler, mock_db):
        """Test active subscriber cannot create new checkout"""
        # Mock user with active subscription
        mock_user = {
            "id": "test_user",
            "subscription_status": "active",
            "subscription_end_date": datetime.utcnow() + timedelta(days=15)
        }
        mock_db.users.find_one.return_value = mock_user
        
        can_create, reason = await subscription_handler.can_create_checkout("test_user")
        
        assert can_create == False
        assert "already has an active subscription" in reason
    
    @pytest.mark.asyncio
    async def test_update_subscription_status_success(self, subscription_handler, mock_db):
        """Test successful subscription status update"""
        mock_db.users.update_one.return_value = Mock(modified_count=1)
        
        payment_data = {
            "customer_id": "cus_test",
            "subscription_id": "sub_test",
            "amount": 9.99,
            "currency": "usd"
        }
        
        success = await subscription_handler.update_subscription_status("test_user", payment_data)
        
        assert success == True
        mock_db.users.update_one.assert_called_once()
```

### Frontend Unit Tests

#### Test File: `/app/frontend/src/tests/components/SubscriptionScreen.test.js`

```javascript
import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import SubscriptionScreen from '../../components/SubscriptionScreen';

// Mock fetch
global.fetch = jest.fn();

const mockProps = {
  user: {
    id: 'test-user-id',
    email: 'test@example.com'
  },
  onClose: jest.fn(),
  onSubscriptionUpdate: jest.fn()
};

describe('SubscriptionScreen', () => {
  beforeEach(() => {
    fetch.mockClear();
    jest.clearAllMocks();
  });

  test('renders subscription screen correctly', () => {
    render(<SubscriptionScreen {...mockProps} />);
    
    expect(screen.getByText('Subscription Management')).toBeInTheDocument();
    expect(screen.getByText('Monthly Plan')).toBeInTheDocument();
    expect(screen.getByText('$9.99')).toBeInTheDocument();
  });

  test('handles successful checkout creation', async () => {
    // Mock successful subscription status fetch
    fetch
      .mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({
          has_access: true,
          subscription_status: 'trial',
          trial_active: true,
          subscription_active: false
        })
      })
      // Mock successful checkout creation
      .mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({
          url: 'https://checkout.stripe.com/test',
          session_id: 'cs_test'
        })
      });

    // Mock window.location.href
    delete window.location;
    window.location = { href: '' };

    render(<SubscriptionScreen {...mockProps} />);

    // Wait for subscription status to load
    await waitFor(() => {
      expect(screen.getByText('🎉 Free Trial Active')).toBeInTheDocument();
    });

    // Click subscribe button
    const subscribeButton = screen.getByText(/Subscribe Now/);
    fireEvent.click(subscribeButton);

    // Wait for checkout creation
    await waitFor(() => {
      expect(fetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/subscription/create-checkout'),
        expect.objectContaining({
          method: 'POST',
          headers: { 'Content-Type': 'application/json' }
        })
      );
    });

    // Should redirect to Stripe checkout
    expect(window.location.href).toBe('https://checkout.stripe.com/test');
  });

  test('handles checkout creation error', async () => {
    // Mock subscription status
    fetch
      .mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({
          subscription_status: 'trial',
          subscription_active: false
        })
      })
      // Mock checkout error
      .mockResolvedValueOnce({
        ok: false,
        status: 500,
        json: () => Promise.resolve({
          detail: 'Payment system not configured'
        })
      });

    render(<SubscriptionScreen {...mockProps} />);

    await waitFor(() => {
      const subscribeButton = screen.getByText(/Subscribe Now/);
      fireEvent.click(subscribeButton);
    });

    await waitFor(() => {
      expect(screen.getByText(/Payment system is temporarily unavailable/)).toBeInTheDocument();
    });
  });
});
```

## 🔗 Integration Testing

### Backend Integration Tests

#### Test File: `/app/tests/stripe/test_payment_integration.py`

```python
import pytest
import asyncio
from httpx import AsyncClient
from motor.motor_asyncio import AsyncIOMotorClient
from server import app

@pytest.fixture
async def test_client():
    """Create test client for API testing"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client

@pytest.fixture
async def test_database():
    """Create isolated test database"""
    client = AsyncIOMotorClient("mongodb://localhost:27017")
    db_name = f"test_stripe_{int(time.time())}"
    db = client[db_name]
    yield db
    await client.drop_database(db_name)
    client.close()

class TestPaymentIntegration:
    
    @pytest.mark.asyncio
    async def test_complete_subscription_flow(self, test_client, test_database):
        """Test complete subscription flow from registration to payment"""
        
        # 1. Register test user
        registration_data = {
            "first_name": "Test",
            "last_name": "User",
            "email": "test@example.com",
            "password": "password123"
        }
        
        response = await test_client.post("/api/auth/register", json=registration_data)
        assert response.status_code == 200
        
        user_data = response.json()
        user_id = user_data["user_id"]
        
        # 2. Verify user (skip email verification for test)
        await test_database.users.update_one(
            {"id": user_id},
            {"$set": {"is_verified": True}}
        )
        
        # 3. Check subscription status
        response = await test_client.get(f"/api/subscription/status/{user_id}")
        assert response.status_code == 200
        
        status_data = response.json()
        assert status_data["subscription_status"] == "trial"
        assert status_data["trial_active"] == True
        
        # 4. Create checkout session
        checkout_request = {
            "user_id": user_id,
            "user_email": "test@example.com",
            "origin_url": "http://localhost:3000"
        }
        
        response = await test_client.post("/api/subscription/create-checkout", json=checkout_request)
        
        if response.status_code == 500:
            # Expected if Stripe API key not configured for testing
            error_data = response.json()
            assert "not configured" in error_data["detail"]
        else:
            assert response.status_code == 200
            checkout_data = response.json()
            assert "url" in checkout_data
            assert "session_id" in checkout_data
    
    @pytest.mark.asyncio
    async def test_webhook_processing(self, test_client, test_database):
        """Test Stripe webhook event processing"""
        
        # Create test user with pending payment
        user_id = "test_user_webhook"
        await test_database.users.insert_one({
            "id": user_id,
            "email": "webhook@example.com",
            "subscription_status": "trial"
        })
        
        # Create test transaction
        session_id = "cs_test_webhook"
        await test_database.payment_transactions.insert_one({
            "user_id": user_id,
            "session_id": session_id,
            "payment_status": "pending"
        })
        
        # Mock Stripe webhook payload
        webhook_payload = {
            "type": "checkout.session.completed",
            "data": {
                "object": {
                    "id": session_id,
                    "payment_status": "paid",
                    "metadata": {
                        "user_id": user_id
                    },
                    "customer": "cus_test",
                    "subscription": "sub_test",
                    "amount_total": 999,  # $9.99 in cents
                    "currency": "usd"
                }
            }
        }
        
        # Send webhook
        response = await test_client.post(
            "/api/webhook/stripe",
            json=webhook_payload,
            headers={"stripe-signature": "test_signature"}
        )
        
        assert response.status_code == 200
        
        # Verify subscription was activated
        user = await test_database.users.find_one({"id": user_id})
        assert user["subscription_status"] == "active"
        
        # Verify transaction was updated
        transaction = await test_database.payment_transactions.find_one({"session_id": session_id})
        assert transaction["payment_status"] == "paid"
```

## 🎭 End-to-End Testing

### Manual Testing Scenarios

#### Scenario 1: Trial User Subscription
```
1. Login as demo user (demo@test.com)
2. Navigate to subscription screen
3. Verify trial status displayed
4. Click "Subscribe Now - Trial Will Continue"
5. Verify redirect to Stripe checkout
6. Complete payment with test card 4242424242424242
7. Return to app and verify subscription activated
8. Check database for updated subscription status
```

#### Scenario 2: Expired Trial User Subscription
```
1. Create user with expired trial in database
2. Login as expired trial user
3. Try to access premium features (should be blocked)
4. Navigate to subscription screen
5. Click "Start Your Subscription"
6. Complete payment flow
7. Verify access to premium features restored
```

#### Scenario 3: Active Subscriber Attempt
```
1. Login as user with active subscription
2. Navigate to subscription screen
3. Verify "✅ You have an active subscription" displayed
4. Verify no subscribe button available
5. Try direct API call to create-checkout (should fail)
```

### Automated E2E Testing

#### Test File: `/app/tests/e2e/test_subscription_flow.py`

```python
import pytest
from playwright.async_api import async_playwright

@pytest.mark.asyncio
async def test_subscription_flow_e2e():
    """End-to-end test of subscription flow"""
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch()
        page = await browser.new_page()
        
        try:
            # 1. Navigate to app
            await page.goto("http://localhost:3000")
            
            # 2. Login as demo user
            await page.click("text=Login")
            await page.fill("input[type=email]", "demo@test.com")
            await page.fill("input[type=password]", "password123")
            await page.click("button:has-text('Login')")
            
            # 3. Wait for dashboard
            await page.wait_for_selector("text=Dashboard")
            
            # 4. Navigate to subscription
            await page.click("text=Subscription")
            
            # 5. Verify subscription screen
            await page.wait_for_selector("text=Subscription Management")
            await page.wait_for_selector("text=🎉 Free Trial Active")
            
            # 6. Click subscribe (will redirect to Stripe)
            await page.click("button:has-text('Subscribe Now')")
            
            # 7. Should redirect to Stripe checkout
            await page.wait_for_url("**/checkout.stripe.com/**", timeout=10000)
            
            # 8. Fill test payment info
            await page.fill("[data-elements-stable-field-name=cardNumber]", "4242424242424242")
            await page.fill("[data-elements-stable-field-name=cardExpiry]", "12/34")
            await page.fill("[data-elements-stable-field-name=cardCvc]", "123")
            await page.fill("[data-elements-stable-field-name=billingName]", "Test User")
            
            # 9. Complete payment
            await page.click("button:has-text('Subscribe')")
            
            # 10. Should redirect back to success page
            await page.wait_for_url("**/subscription/success**", timeout=15000)
            
            # 11. Verify success message
            await page.wait_for_selector("text=Subscription activated")
            
        finally:
            await browser.close()
```

## 📊 Performance Testing

### Load Testing Script

```python
import asyncio
import aiohttp
import time
from concurrent.futures import ThreadPoolExecutor

async def test_checkout_creation_load():
    """Test checkout creation under load"""
    
    async def create_checkout_session(session, user_id):
        """Create single checkout session"""
        start_time = time.time()
        
        try:
            async with session.post(
                "http://localhost:8001/api/subscription/create-checkout",
                json={
                    "user_id": f"test_user_{user_id}",
                    "user_email": f"test{user_id}@example.com",
                    "origin_url": "http://localhost:3000"
                }
            ) as response:
                duration = time.time() - start_time
                return {
                    "status": response.status,
                    "duration": duration,
                    "success": response.status == 200
                }
        except Exception as e:
            duration = time.time() - start_time
            return {
                "status": 0,
                "duration": duration,
                "success": False,
                "error": str(e)
            }
    
    # Test with 50 concurrent requests
    async with aiohttp.ClientSession() as session:
        tasks = [create_checkout_session(session, i) for i in range(50)]
        results = await asyncio.gather(*tasks)
    
    # Analyze results
    successful = sum(1 for r in results if r["success"])
    avg_duration = sum(r["duration"] for r in results) / len(results)
    max_duration = max(r["duration"] for r in results)
    
    print(f"Load Test Results:")
    print(f"  Total Requests: {len(results)}")
    print(f"  Successful: {successful} ({successful/len(results)*100:.1f}%)")
    print(f"  Average Duration: {avg_duration:.2f}s")
    print(f"  Max Duration: {max_duration:.2f}s")
    
    # Performance criteria
    assert successful / len(results) > 0.95  # >95% success rate
    assert avg_duration < 2.0  # <2s average response time
    assert max_duration < 5.0  # <5s max response time

if __name__ == "__main__":
    asyncio.run(test_checkout_creation_load())
```

## 🚀 Test Execution

### Running All Tests

```bash
# Backend unit tests
cd /app/backend
python -m pytest tests/stripe/ -v

# Frontend unit tests  
cd /app/frontend
npm test -- --coverage

# Integration tests
cd /app
python -m pytest tests/integration/ -v

# End-to-end tests
cd /app
python -m pytest tests/e2e/ -v

# Performance tests
cd /app
python tests/performance/load_test.py
```

### Continuous Integration

```yaml
# .github/workflows/stripe-testing.yml
name: Stripe Payment System Tests

on: [push, pull_request]

jobs:
  test-stripe:
    runs-on: ubuntu-latest
    
    env:
      STRIPE_API_KEY: ${{ secrets.STRIPE_TEST_API_KEY }}
      MONGO_URL: mongodb://localhost:27017/test_db
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Start MongoDB
        uses: supercharge/mongodb-github-action@1.8.0
        
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: 3.11
          
      - name: Install dependencies
        run: |
          cd backend
          pip install -r requirements.txt
          pip install pytest pytest-asyncio
          
      - name: Run Stripe unit tests
        run: |
          cd backend
          python -m pytest tests/stripe/ -v
          
      - name: Run integration tests
        run: |
          python -m pytest tests/integration/ -v
```

## ✅ Test Results Validation

### Success Criteria

**Unit Tests:**
- [ ] All service classes pass initialization tests
- [ ] All business logic functions return expected results
- [ ] All error conditions are handled properly

**Integration Tests:**
- [ ] API endpoints return correct HTTP status codes
- [ ] Database operations complete successfully
- [ ] Webhook processing updates subscription status

**End-to-End Tests:**
- [ ] Complete user journey from trial to paid subscription
- [ ] Payment success results in feature access
- [ ] Error scenarios display appropriate messages

**Performance Tests:**
- [ ] >95% success rate under load
- [ ] <2 second average response time
- [ ] <5 second maximum response time

---

**Next Steps**: After all tests pass, proceed with deployment using the implementation guide.

**Document Version**: 1.0  
**Last Updated**: January 2025