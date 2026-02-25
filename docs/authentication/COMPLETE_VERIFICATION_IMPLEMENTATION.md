# Complete Email Verification Implementation Guide

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Recipe-AI Authentication                 │
└─────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────┐
│                    Frontend (React)                           │
├──────────────────────────────────────────────────────────────┤
│                                                               │
│  LoginComponent          VerificationPage        Dashboard    │
│  ├─ Email input       ├─ Auto-send code        └─ User data  │
│  ├─ Password input    ├─ Code validation                     │
│  └─ Login handler     ├─ Resend button                       │
│                       └─ Back to login                       │
│                                                               │
│         App.js (Router & State Management)                   │
│         ├─ verificationEmail state                          │
│         ├─ handleVerificationRequired()                     │
│         └─ handleVerificationSuccess()                      │
│                                                               │
└──────────────────────────────────────────────────────────────┘
                           ↕ HTTPS/JSON
                      
┌──────────────────────────────────────────────────────────────┐
│                   Backend (FastAPI)                           │
├──────────────────────────────────────────────────────────────┤
│                                                               │
│  POST /auth/login                                            │
│  ├─ Verify credentials                                       │
│  ├─ Check is_verified flag                                   │
│  ├─ Generate code if unverified                              │
│  └─ Send email via Mailjet                                   │
│                                                               │
│  POST /auth/resend-verification                              │
│  ├─ Generate new 6-digit code                                │
│  ├─ Save to database                                         │
│  └─ Send via Mailjet                                         │
│                                                               │
│  POST /auth/verify                                           │
│  ├─ Validate code vs database                                │
│  ├─ Check expiration (15 min)                                │
│  ├─ Mark user verified                                       │
│  └─ Return success                                           │
│                                                               │
│                 Mailjet Email Service                        │
│                 └─ Beautiful HTML templates                  │
│                                                               │
└──────────────────────────────────────────────────────────────┘
                           ↕ HTTPS
                      
┌──────────────────────────────────────────────────────────────┐
│                  MongoDB Database                             │
├──────────────────────────────────────────────────────────────┤
│                                                               │
│  users collection                                            │
│  ├─ email (unique)                                           │
│  ├─ password_hash (bcrypt)                                   │
│  ├─ is_verified (boolean)                                    │
│  ├─ verified_at (timestamp)                                  │
│  └─ ... 30+ other fields                                     │
│                                                               │
│  verification_codes collection                               │
│  ├─ email                                                    │
│  ├─ code (6 digits)                                          │
│  ├─ created_at                                               │
│  ├─ expires_at (15 minutes)                                  │
│  └─ used (boolean)                                           │
│                                                               │
└──────────────────────────────────────────────────────────────┘
```

## Detailed Implementation

### Frontend Implementation

#### 1. Auth Service (`frontend/src/services/auth.js`)

```javascript
export const authService = {
  // Verify code against backend
  async verifyCode(email, verificationCode) {
    const response = await fetch('/api/auth/verify', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, verification_code: verificationCode }),
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.detail || 'Verification failed');
    return data;
  },

  // Resend verification code
  async resendVerificationCode(email) {
    const response = await fetch('/api/auth/resend-verification', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email }),
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.detail || 'Failed to resend code');
    return data;
  },

  // localStorage helpers for pending verification
  getPendingVerification() {
    const stored = localStorage.getItem('pendingVerification');
    return stored ? JSON.parse(stored) : null;
  },

  setPendingVerification(data) {
    localStorage.setItem('pendingVerification', JSON.stringify(data));
  },

  clearPendingVerification() {
    localStorage.removeItem('pendingVerification');
  }
};
```

#### 2. VerificationPage Component (`frontend/src/components/VerificationPage.js`)

**Key Features:**
- Accepts `email` prop from App.js
- Auto-sends verification code on mount
- 6-digit code input with auto-formatting
- Resend code button
- Success/error messaging
- Back to login option

```javascript
const VerificationPage = ({ email, onVerificationSuccess, onBackToLogin }) => {
  const [verificationCode, setVerificationCode] = useState('');
  const [loading, setLoading] = useState(false);
  const [codeSent, setCodeSent] = useState(false);

  // Auto-send when component mounts
  useEffect(() => {
    if (email) {
      sendVerificationCode();
    }
  }, [email]);

  // Send or resend code
  const sendVerificationCode = async () => {
    try {
      await authService.resendVerificationCode(email);
      setCodeSent(true);
      setError('');
    } catch (error) {
      setError('Failed to send verification code');
    }
  };

  // Verify code submission
  const handleVerification = async (e) => {
    e.preventDefault();
    
    if (verificationCode.length !== 6) {
      setError('Please enter a valid 6-digit code.');
      return;
    }

    setLoading(true);
    try {
      const result = await authService.verifyCode(email, verificationCode);
      if (onVerificationSuccess) {
        onVerificationSuccess(result);
      }
    } catch (error) {
      setError(error.message);
    } finally {
      setLoading(false);
    }
  };

  // Resend code handler
  const handleResendCode = async () => {
    setResendLoading(true);
    try {
      await sendVerificationCode();
    } finally {
      setResendLoading(false);
    }
  };

  return (
    // UI with form, buttons, and messaging
  );
};
```

#### 3. App.js Integration

```javascript
const [verificationEmail, setVerificationEmail] = useState('');

// Handle unverified user
const handleVerificationRequired = (data) => {
  setVerificationEmail(data.email);
  setCurrentView('verification');
  setNotification({
    type: 'warning',
    message: 'Please verify your email to continue'
  });
};

// Handle verification success
const handleVerificationSuccess = (data) => {
  setCurrentView('dashboard');
  setUser({ ...user, is_verified: true });
  setNotification({
    type: 'success',
    message: 'Account verified! Welcome to Recipe-AI'
  });
};

// Render verification page
case 'verification':
  return (
    <VerificationPage
      email={verificationEmail}
      onVerificationSuccess={handleVerificationSuccess}
      onBackToLogin={() => setCurrentView('login')}
    />
  );
```

### Backend Implementation

#### 1. Verification Code Generation

```python
def generate_verification_code() -> str:
    """Generate 6-digit random code"""
    return str(random.randint(100000, 999999))
```

#### 2. Email Sending via Mailjet

```python
async def send_verification_email(email: str, code: str) -> bool:
    """Send verification email using Mailjet API"""
    
    # Check credentials
    if not mailjet_api_key or not mailjet_secret_key:
        logger.info(f"Code for {email}: {code}")  # Development fallback
        return True
    
    # Prepare email
    mailjet = Client(auth=(mailjet_api_key, mailjet_secret_key))
    
    html_content = f"""
    <html>
        <body style="font-family: Arial; background: #f5f5f5; padding: 20px;">
            <div style="max-width: 600px; margin: auto; background: white; 
                        padding: 30px; border-radius: 10px;">
                <h1>🍳 Verify Your Recipe-AI Account</h1>
                
                <p>Your verification code:</p>
                
                <div style="text-align: center; margin: 30px 0;">
                    <div style="background: #f0f0f0; padding: 20px; 
                                border-radius: 10px; font-family: monospace;">
                        <h2 style="color: #007bff; margin: 0; 
                                   letter-spacing: 5px;">{code}</h2>
                    </div>
                </div>
                
                <p><strong>This code expires in 15 minutes.</strong></p>
            </div>
        </body>
    </html>
    """
    
    # Send via Mailjet
    data = {
        "Messages": [{
            "From": {"Email": sender_email, "Name": "Recipe-AI"},
            "To": [{"Email": email}],
            "Subject": "Verify Your Recipe-AI Account",
            "HTMLPart": html_content,
            "TextPart": f"Code: {code}\n\nExpires in 15 minutes."
        }]
    }
    
    result = mailjet.send.create(data=data)
    return result.status_code == 200
```

#### 3. Login Endpoint

```python
@app.post("/auth/login")
async def login(request: UserLoginRequest):
    # Find user
    user = await users_collection.find_one({"email": request.email})
    if not user or not verify_password(request.password, user["password_hash"]):
        return JSONResponse(status_code=401, content={"detail": "Invalid credentials"})
    
    # Check if verified
    is_verified = user.get("is_verified") or user.get("verified", False)
    
    if not is_verified:
        # Generate new code
        verification_code = generate_verification_code()
        
        # Save to database
        await verification_codes_collection.update_one(
            {"email": request.email},
            {
                "$set": {
                    "code": verification_code,
                    "created_at": datetime.utcnow(),
                    "expires_at": datetime.utcnow() + timedelta(minutes=15),
                    "used": False
                }
            },
            upsert=True
        )
        
        # Send email
        await send_verification_email(request.email, verification_code)
        
        # Return 403
        return JSONResponse(
            status_code=403,
            content={
                "status": "verification_required",
                "message": "Account not verified. Check email for code.",
                "email": request.email,
                "user_id": user["id"]
            }
        )
    
    # User verified - return success
    return JSONResponse(
        status_code=200,
        content={
            "status": "success",
            "user_id": user["id"],
            "email": user["email"],
            "is_verified": True,
            # ... all user fields
        }
    )
```

#### 4. Resend Endpoint

```python
@app.post("/auth/resend-verification")
async def resend_verification(request: ResendVerificationRequest):
    """Resend verification code to user email"""
    
    # Find user
    user = await users_collection.find_one({"email": request.email})
    if not user:
        return JSONResponse(status_code=404, content={"detail": "User not found"})
    
    # Generate new code
    verification_code = generate_verification_code()
    
    # Save to database
    await verification_codes_collection.update_one(
        {"email": request.email},
        {
            "$set": {
                "code": verification_code,
                "created_at": datetime.utcnow(),
                "expires_at": datetime.utcnow() + timedelta(minutes=15),
                "used": False
            }
        },
        upsert=True
    )
    
    # Send email
    email_sent = await send_verification_email(request.email, verification_code)
    
    return JSONResponse(
        status_code=200,
        content={
            "status": "success",
            "message": "Verification code sent",
            "email": request.email,
            "email_sent": email_sent
        }
    )
```

#### 5. Verify Endpoint

```python
@app.post("/auth/verify")
async def verify_email(request: VerificationRequest):
    """Verify email with code"""
    
    # Find code in database
    code_doc = await verification_codes_collection.find_one({
        "email": request.email,
        "code": request.verification_code
    })
    
    if not code_doc:
        return JSONResponse(status_code=400, content={"detail": "Invalid code"})
    
    # Check expiration
    if datetime.utcnow() > code_doc["expires_at"]:
        return JSONResponse(status_code=400, content={"detail": "Code expired"})
    
    # Check if already used
    if code_doc.get("used"):
        return JSONResponse(status_code=400, content={"detail": "Code already used"})
    
    # Mark user as verified
    await users_collection.update_one(
        {"email": request.email},
        {
            "$set": {
                "is_verified": True,
                "verified": True,  # Legacy field
                "verified_at": datetime.utcnow()
            }
        }
    )
    
    # Mark code as used
    await verification_codes_collection.update_one(
        {"_id": code_doc["_id"]},
        {"$set": {"used": True}}
    )
    
    return JSONResponse(
        status_code=200,
        content={
            "status": "success",
            "message": "Email verified successfully",
            "verified": True
        }
    )
```

## Database Schema

### Users Collection
```json
{
  "_id": ObjectId,
  "email": "user@example.com",
  "password_hash": "bcrypt_hash",
  "id": "uuid",
  "is_verified": false,
  "verified": false,
  "verified_at": null,
  "first_name": "John",
  "last_name": "Doe",
  "subscription_status": "trial",
  "trial_start_date": "2025-12-26",
  "trial_end_date": "2026-02-14",
  "dietary_preferences": [],
  "allergies": [],
  "created_at": "2025-12-26T10:00:00Z",
  "updated_at": "2025-12-26T10:00:00Z"
}
```

### Verification Codes Collection
```json
{
  "_id": ObjectId,
  "email": "user@example.com",
  "code": "123456",
  "created_at": "2025-12-26T10:00:00Z",
  "expires_at": "2025-12-26T10:15:00Z",
  "used": false
}
```

## Deployment Configuration

### Environment Variables Required
```bash
# MongoDB
MONGO_URL=mongodb+srv://user:pass@cluster.mongodb.net/?retryWrites=true
DB_NAME=recipe_ai

# Mailjet Email Service
MAILJET_API_KEY=your_api_key_here
MAILJET_SECRET_KEY=your_secret_key_here
SENDER_EMAIL=noreply@buildyoursmartcart.com  # Optional, has default

# Other services
OPENAI_API_KEY=sk-...
STRIPE_SECRET_KEY=sk_live_...
```

### Mailjet Setup Steps
1. Create account at mailjet.com
2. Verify sender domain or email
3. Get API key and secret from dashboard
4. Set environment variables
5. Test email sending in staging

### Production Considerations
1. Remove `verification_code` from login response (dev only)
2. Enable rate limiting on resend endpoint
3. Add analytics for verification success rate
4. Monitor Mailjet dashboard for bounce/failure rates
5. Set up alerts for verification failures

## Testing Checklist

- [ ] **New User Registration**
  - [ ] Create account successfully
  - [ ] Verification code generated
  - [ ] Email received (check spam)

- [ ] **Immediate Login (Unverified)**
  - [ ] Try to login immediately
  - [ ] Get 403 verification_required response
  - [ ] Redirect to VerificationPage
  - [ ] See "✅ Code sent!" message
  - [ ] Email with code received

- [ ] **Code Verification**
  - [ ] Enter valid code from email
  - [ ] Account marked as verified
  - [ ] Redirected to dashboard
  - [ ] User data loaded

- [ ] **Second Login (Verified)**
  - [ ] Login again with same credentials
  - [ ] Direct to dashboard (no verification)
  - [ ] No new verification email sent

- [ ] **Resend Code**
  - [ ] Click "Resend Code" button
  - [ ] New email received immediately
  - [ ] New code works, old code rejected

- [ ] **Error Cases**
  - [ ] Wrong code shows error
  - [ ] Expired code shows error
  - [ ] Missing email shows error
  - [ ] Back to login works

## Monitoring & Debugging

### Check Logs
```bash
# Backend logs
docker logs recipe-ai-backend | grep "verification\|email"

# Check specific user
# In MongoDB
db.users.findOne({ email: "user@example.com" })
db.verification_codes.findOne({ email: "user@example.com" })
```

### Mailjet Dashboard
- Check message delivery status
- Monitor bounce rates
- Review failed sends
- View email opens/clicks

### Common Issues
| Issue | Solution |
|-------|----------|
| Email not received | Check spam folder, verify Mailjet credentials |
| Code expired | User needs to click "Resend Code" |
| Wrong code error | Ensure exact 6-digit match from email |
| User not found | User must be registered first |
| Missing email prop | Check App.js is passing email to VerificationPage |

## Performance Optimizations

1. **Code Storage**: Use MongoDB index on `email` + `expires_at` for cleanup
2. **Rate Limiting**: Limit resend to 3 per hour per email
3. **Caching**: Cache verification codes in Redis (optional)
4. **Async**: All operations are async/await
5. **Mailjet Pooling**: Reuse Mailjet client connection

## Security Best Practices

1. ✅ 6-digit random codes (1 in 1,000,000)
2. ✅ 15-minute expiration
3. ✅ One-time use per code
4. ✅ HTTPS/TLS for transmission
5. ✅ Email verification requirement
6. ✅ Bcrypt password hashing
7. ✅ CORS properly configured
8. ✅ Error messages don't leak information

## Next Steps

1. **Immediate**: Set Mailjet credentials in production environment
2. **Testing**: End-to-end test with real users
3. **Monitoring**: Set up alerts for verification failures
4. **Enhancement**: Add SMS option (future)
5. **Analytics**: Track verification success rates
6. **Optimization**: Add rate limiting to resend endpoint
