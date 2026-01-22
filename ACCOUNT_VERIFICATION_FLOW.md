# Account Verification Flow Guide

## Overview
This document explains the complete flow when an unverified user tries to log in to Recipe-AI. The user is automatically sent a verification code via email and prompted to verify their account.

## Complete Workflow

### Step 1: User Attempts to Login
```
User enters email & password
    ↓
Clicks "Login to Dashboard"
    ↓
Frontend sends POST /api/auth/login
```

### Step 2: Backend Validates Credentials
```
Backend checks if user exists
    ↓
Backend verifies password
    ↓
Backend checks is_verified flag
```

### Step 3a: If Account is NOT Verified ❌
```
Backend generates new 6-digit verification code
    ↓
Backend saves code to verification_codes collection (expires in 15 mins)
    ↓
Backend calls send_verification_email() via Mailjet
    ↓
Backend returns HTTP 403 with status: "verification_required"
    ↓
Response includes:
  - email: user's email
  - user_id: user's ID
  - status: "verification_required"
  - message: "Account not verified. Please check your email..."
  - verification_code: code (dev only)
```

### Step 3b: If Account IS Verified ✅
```
Backend updates last_login timestamp
    ↓
Backend returns HTTP 200 with user data
    ↓
User is logged in and sent to dashboard
```

### Step 4: Frontend Handles Verification Required
```
LoginComponent receives 403 response
    ↓
LoginComponent calls onVerificationRequired(data)
    ↓
App.js handleVerificationRequired():
  - setVerificationEmail(data.email)
  - setCurrentView('verification')
  - Shows notification
```

### Step 5: VerificationPage Mounts
```
VerificationPage receives email as prop
    ↓
useEffect runs with email dependency
    ↓
VerificationPage calls sendVerificationCode(email)
    ↓
This sends POST /api/auth/resend-verification
    ↓
Email is sent AGAIN to ensure user has code
    ↓
setCodeSent(true) - shows "✅ Code sent!" message
```

### Step 6: User Enters Verification Code
```
User checks email inbox
    ↓
User sees verification code email from Recipe-AI
    ↓
User copies 6-digit code
    ↓
User pastes into VerificationPage input
    ↓
Code is automatically formatted (digits only, max 6)
```

### Step 7: User Submits Verification Code
```
User clicks "Verify Account" button
    ↓
Frontend validates code (must be 6 digits)
    ↓
Frontend sends POST /api/auth/verify with:
  - email: user's email
  - verification_code: the code entered
```

### Step 8: Backend Verifies Code
```
Backend finds verification code in database
    ↓
Backend checks if code matches
    ↓
Backend checks if code is expired (must be < 15 mins old)
```

### Step 9a: Valid Code ✅
```
Backend updates user document:
  - is_verified = true
  - verified = true (legacy)
  - verified_at = current timestamp
    ↓
Backend marks verification code as used
    ↓
Backend returns HTTP 200 with status: "success"
```

### Step 9b: Invalid Code ❌
```
Backend returns HTTP 400 with error message:
  - "Invalid verification code"
  - "Verification code expired"
```

### Step 10: Frontend Handles Verification Success
```
VerificationPage receives success response
    ↓
onVerificationSuccess callback is called
    ↓
App.js handleVerificationSuccess():
  - setCurrentView('dashboard')
  - setUser(userData with verified: true)
  - Shows success notification
```

### Step 11: User is Logged In and Verified
```
User is redirected to dashboard
    ↓
User can now access all features
    ↓
Account is fully active ✅
```

## Key Components

### 1. LoginComponent
- **File**: `frontend/src/components/LoginComponent.js`
- **Purpose**: Handles login form and credentials validation
- **When user not verified**: Passes verification data to `onVerificationRequired`
- **Response handling**:
  ```javascript
  if (response.status === 403 && data.status === 'verification_required') {
    onVerificationRequired(data)  // Triggers verification page
  }
  ```

### 2. VerificationPage
- **File**: `frontend/src/components/VerificationPage.js`
- **Props**:
  - `email`: User's email address (passed from login)
  - `onVerificationSuccess`: Callback when verification succeeds
  - `onBackToLogin`: Callback for back button
- **Auto-sends code**: When component mounts, automatically sends verification code
- **Features**:
  - Displays email address verification code was sent to
  - Shows "✅ Code sent!" message
  - Validates code format (6 digits only)
  - Resend code button (on each click, new code sent and email sent)
  - Error handling with user-friendly messages

### 3. Auth Service
- **File**: `frontend/src/services/auth.js`
- **Methods**:
  - `verifyCode(email, code)`: Calls POST /api/auth/verify
  - `resendVerificationCode(email)`: Calls POST /api/auth/resend-verification
  - `getPendingVerification()`: Gets stored verification data
  - `setPendingVerification(data)`: Stores verification data
  - `clearPendingVerification()`: Clears stored verification data

### 4. Backend Endpoints

#### POST /api/auth/login
```python
# Request
{
  "email": "user@example.com",
  "password": "password123"
}

# Response (Unverified User) - HTTP 403
{
  "status": "verification_required",
  "message": "Account not verified. Please check your email for verification code.",
  "email": "user@example.com",
  "user_id": "uuid-here",
  "verification_code": "123456"  # Dev only
}

# Response (Verified User) - HTTP 200
{
  "status": "success",
  "message": "Login successful",
  "user_id": "uuid-here",
  "email": "user@example.com",
  "is_verified": true,
  "subscription_status": "trial",
  ...
}
```

#### POST /api/auth/resend-verification
```python
# Request
{
  "email": "user@example.com"
}

# Response - HTTP 200
{
  "status": "success",
  "message": "Verification code sent",
  "email": "user@example.com",
  "email_sent": true
}
```

#### POST /api/auth/verify
```python
# Request
{
  "email": "user@example.com",
  "verification_code": "123456"
}

# Response (Success) - HTTP 200
{
  "status": "success",
  "message": "Email verified successfully",
  "email": "user@example.com",
  "verified": true
}

# Response (Error) - HTTP 400
{
  "detail": "Invalid verification code"
}
```

## Verification Code Specifications

### Code Generation
- **Length**: 6 digits
- **Format**: Numeric only (0-9)
- **Example**: `123456`
- **Generated by**: `generate_verification_code()` function
- **Randomness**: Uses `random.randint()` for each digit

### Code Storage
**Collection**: `verification_codes`
```javascript
{
  _id: ObjectId,
  email: "user@example.com",
  code: "123456",
  created_at: ISODate,
  expires_at: ISODate,  // 15 minutes from creation
  used: false
}
```

### Code Expiration
- **Duration**: 15 minutes
- **After expiration**: Code becomes invalid
- **Error message**: "Verification code expired"
- **Solution**: User clicks "Resend Code" to get new code

### Code Validation
1. Find code in database by email
2. Check if code matches (exact match required)
3. Check if not expired (current time < expires_at)
4. Check if not already used (used = false)
5. All checks must pass

## Email Sending Flow

### When Code is Sent
1. User registers (sends initial code)
2. User tries to login (unverified - sends new code)
3. User clicks "Resend Code" (sends new code)

### Email Content
- **Subject**: "Verify Your Recipe-AI Account"
- **Template**: HTML with:
  - Welcome message
  - 6-digit code in large font
  - Expiration notice (15 minutes)
  - Security message
  - Action: User must enter code on verification page

### Email Service
- **Provider**: Mailjet
- **Method**: HTTPS API
- **Credentials**: MAILJET_API_KEY, MAILJET_SECRET_KEY
- **Sender**: noreply@buildyoursmartcart.com

## User Experience Flow

```
UNVERIFIED USER TRIES TO LOGIN
├─ Enter email: user@example.com
├─ Enter password: ••••••••
├─ Click "Login to Dashboard"
└─ ❌ Account not verified
   
VERIFICATION PAGE APPEARS
├─ Shows: "We sent a 6-digit code to user@example.com"
├─ Shows: "✅ Verification code sent!"
├─ Input field: "Enter 6-digit code"
├─ Button: "Verify Account" (disabled until 6 digits)
└─ Link: "Resend Code"

USER CHECKS EMAIL
├─ Opens email from Recipe-AI
├─ Sees: "Verify Your Recipe-AI Account"
├─ Sees code: 123456 (in large font)
└─ Copies code

USER ENTERS CODE
├─ Pastes code into input field
├─ Field auto-formats to: 123456
├─ "Verify Account" button enables
└─ Clicks "Verify Account"

VERIFICATION SUCCEEDS
├─ Shows: "✅ Account verified!"
├─ Redirects to dashboard
├─ User is logged in ✅
└─ Can access all features

OR VERIFICATION FAILS
├─ Shows error: "Invalid verification code"
├─ User can try again
├─ User can click "Resend Code"
└─ New code is sent to email
```

## Troubleshooting

### Issue: User says "I didn't receive an email"

**Check 1: Look at server logs**
```bash
docker logs your_container | grep "verification\|email"
```

**Check 2: Verify user is actually unverified**
```bash
# In MongoDB
db.users.findOne({ email: "user@example.com" })
# Look for is_verified: false
```

**Check 3: Check Mailjet account**
- Log into Mailjet dashboard
- Check "Messages" section
- Look for delivery status (sent, bounced, failed)

**Check 4: User clicks "Resend Code"**
- This sends a fresh email
- New code is generated
- Old code becomes invalid

### Issue: Verification code says "Expired"

**Solution**: User needs to click "Resend Code"
- Old code expires after 15 minutes
- "Resend Code" generates new code with fresh 15-minute timer
- New email is sent immediately

### Issue: User enters wrong code

**Error message**: "Invalid verification code"
**Solution**: 
- Check code from email carefully
- Make sure all 6 digits are correct
- Click "Resend Code" if unsure
- Try the new code from email

## API Response Codes

| Endpoint | Status | Meaning |
|----------|--------|---------|
| /auth/login | 200 | ✅ Verified user logged in |
| /auth/login | 403 | ⚠️ User not verified, send code |
| /auth/login | 401 | ❌ Invalid email or password |
| /auth/login | 500 | ❌ Server error |
| /auth/verify | 200 | ✅ Code valid, account verified |
| /auth/verify | 400 | ❌ Invalid or expired code |
| /auth/resend-verification | 200 | ✅ Code sent |
| /auth/resend-verification | 404 | ❌ User not found |

## Security Considerations

1. **Code is random**: Each code is randomly generated
2. **Code expires**: Codes are invalid after 15 minutes
3. **One-time use**: Code can only be used once
4. **Secure transmission**: Sent via HTTPS/TLS
5. **Email verification**: User must have access to registered email
6. **Rate limiting** (optional): Could add to prevent brute force
7. **Logging**: All verification attempts are logged

## Database Schema Changes

### Users Collection
```javascript
{
  is_verified: true/false,      // NEW: verification status
  verified: true/false,          // LEGACY: backward compatibility
  verified_at: ISODate/null      // NEW: when email was verified
}
```

### Verification Codes Collection
```javascript
{
  email: string,
  code: string,
  created_at: ISODate,
  expires_at: ISODate,
  used: boolean
}
```

## Complete Flow Implementation

### Frontend Components Involved
1. **LoginComponent** → Detects unverified user, triggers verification
2. **App.js** → Routes to VerificationPage, manages state
3. **VerificationPage** → Auto-sends code, validates input, verifies account
4. **AuthService** → Makes API calls to backend endpoints

### Backend Flow
1. **POST /auth/login** → Check verification status
2. **generate_verification_code()** → Create 6-digit code
3. **send_verification_email()** → Send via Mailjet
4. **POST /auth/resend-verification** → Create new code, send email
5. **POST /auth/verify** → Validate code, mark user verified

## Testing the Flow

### Manual Testing Steps
1. Create new account (gets verification code)
2. Try logging in immediately (unverified)
3. Verify you see VerificationPage auto-sends code message
4. Check email for code
5. Enter code into form
6. Verify account and login succeeds
7. Try logging in again with same credentials
8. Verify account is now marked as verified (no verification page)

### Testing Resend Code
1. On VerificationPage, click "Resend Code"
2. Verify new email arrives
3. Use new code to verify account
4. Old code should be invalid

## Next Steps & Enhancements

### Currently Implemented ✅
- Auto-send verification code when VerificationPage mounts
- Code resend functionality
- Email verification with Mailjet
- 15-minute code expiration
- Success/error messaging

### Optional Enhancements ⏳
- Rate limiting on resend endpoint (max 3 per hour)
- Add "Send another email" delay (60 seconds)
- Analytics on verification success rate
- Resend code counter display
- Auto-focus on code input field
- Copy code to clipboard from email
- SMS-based verification option (future)
- Account recovery without email
