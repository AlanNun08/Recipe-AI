# Sign-Up & Login Testing Guide

## Prerequisites

1. **MongoDB Running**
   ```bash
   # Mac with Homebrew
   brew services start mongodb-community
   
   # Or Docker
   docker run -d -p 27017:27017 --name mongodb mongo:latest
   ```

2. **Backend Running**
   ```bash
   cd backend
   python -m pip install -r requirements.txt
   python -m uvicorn server:app --reload --host 0.0.0.0 --port 8080
   ```

3. **Frontend Running**
   ```bash
   cd frontend
   npm start
   # Runs on http://localhost:3000
   ```

---

## Test Scenario 1: Complete Sign-Up Flow

### Step 1: Navigate to Sign-Up
1. Open browser to `http://localhost:3000`
2. Click **"Sign Up"** button in header or on landing page
3. Should see WelcomeOnboarding component with registration form

### Step 2: Fill Registration Form
- **First Name:** John
- **Last Name:** Doe
- **Email:** john.doe@example.com
- **Password:** SecureTest123
- **Agree Terms:** Check box
- **Email Updates:** Check box (optional)

### Step 3: Submit Registration
1. Click **"Create Account"** or **"Sign Up"** button
2. **Expected:** 
   - ✅ Loading spinner shows
   - ✅ Success message: "Registration successful"
   - ✅ Redirects to preferences/dashboard
   - ✅ No error messages

### Step 4: Verify Console Logs
Open browser **DevTools** → **Console** tab and check:
```
📝 Registering new user...
  📧 Email: john.doe@example.com
  👤 Name: John Doe
📤 Sending registration request: {...}
📡 Response status: 201
✅ Registration successful!
  👤 User ID: 550e8400-...
```

### Step 5: Verify MongoDB
```bash
# Connect to MongoDB
mongosh

# Use database
use recipe_ai

# Find the new user
db.users.findOne({ email: "john.doe@example.com" })
```

**Expected output:**
```javascript
{
  _id: ObjectId("..."),
  id: "550e8400-e29b-41d4-a716-446655440000",
  email: "john.doe@example.com",
  password_hash: "$2b$12$...",    // bcrypt hash
  first_name: "John",
  last_name: "Doe",
  is_verified: false,
  created_at: ISODate("2026-01-15T..."),
  subscription_status: "trial",
  trial_start_date: ISODate("2026-01-15T..."),
  trial_end_date: ISODate("2026-03-06T..."),
  // ... other fields
}
```

---

## Test Scenario 2: Login with Verified Account

### Step 1: Mark Account as Verified (for testing)
```bash
# In mongosh
db.users.updateOne(
  { email: "john.doe@example.com" },
  { $set: { is_verified: true } }
)
```

### Step 2: Navigate to Login
1. Open browser to `http://localhost:3000`
2. Click **"Sign In"** button in header or modal
3. Should see login form

### Step 3: Enter Credentials
- **Email:** john.doe@example.com
- **Password:** SecureTest123
- **Remember Me:** Check (optional)

### Step 4: Submit Login
1. Click **"Login to Dashboard"** button
2. **Expected:**
   - ✅ Loading spinner shows
   - ✅ Login succeeds
   - ✅ Redirected to dashboard
   - ✅ User data stored in localStorage/sessionStorage

### Step 5: Verify Console Logs
```
🔐 Attempting login...
  📧 Email: john.doe@example.com
📤 Sending login request to backend
📡 Response status: 200
📥 Login response: {...}
✅ Login successful!
  👤 User ID: 550e8400-...
  📧 Email: john.doe@example.com
  ⏰ Subscription: trial
💾 User data saved to localStorage
```

### Step 6: Verify MongoDB Last Login Updated
```bash
# In mongosh
db.users.findOne({ email: "john.doe@example.com" })

# Should see recent last_login timestamp
```

---

## Test Scenario 3: Duplicate Email Registration

### Step 1: Try to Register with Same Email
1. Click Sign Up again
2. Fill form with **same email:** john.doe@example.com
3. Different password: DifferentPass123
4. Submit form

### Step 2: Expected Result
- ❌ Error message: "User with this email already exists"
- ❌ No redirect
- ❌ Form stays visible

### Step 3: Verify Console
```
📝 Registering new user...
  📧 Email: john.doe@example.com
📤 Sending registration request: {...}
📡 Response status: 400
📥 Registration response: { detail: "User with this email already exists" }
❌ Registration failed: 400, {...}
```

---

## Test Scenario 4: Unverified Account Login

### Step 1: Reset Account to Unverified
```bash
# In mongosh
db.users.updateOne(
  { email: "john.doe@example.com" },
  { $set: { is_verified: false } }
)
```

### Step 2: Try to Login
1. Go to login page
2. Enter credentials
3. Submit login

### Step 3: Expected Result
- ⚠️ Status: 403 (Verification Required)
- ⚠️ Message: "Account not verified. Please check your email for verification code."
- ⚠️ Shows verification code input field (if implemented)

### Step 4: Verify MongoDB
```bash
# Check verification codes were created
db.verification_codes.findOne({ email: "john.doe@example.com" })

# Should show recent code
```

---

## Test Scenario 5: Invalid Credentials

### Step 1: Try Wrong Password
1. Go to login page
2. Email: john.doe@example.com
3. Password: WrongPassword123
4. Submit login

### Step 2: Expected Result
- ❌ Error: "Invalid email or password"
- ❌ No user data returned
- ❌ Form remains visible

### Step 3: Verify Console
```
🔐 Attempting login...
  📧 Email: john.doe@example.com
📤 Sending login request to backend
📡 Response status: 401
❌ Invalid credentials
```

---

## Test Scenario 6: Non-Existent Email

### Step 1: Try to Login with Non-Existent Email
1. Go to login page
2. Email: notregistered@example.com
3. Password: SomePassword123
4. Submit login

### Step 2: Expected Result
- ❌ Error: "Invalid email or password"
- ❌ No indication if email exists
- ❌ Same error as wrong password (security feature)

### Step 3: Verify Console
```
🔐 Attempting login...
  📧 Email: notregistered@example.com
🔍 Searching MongoDB for user: notregistered@example.com
⚠️ User not found in MongoDB: notregistered@example.com
📡 Response status: 401
```

---

## Test Scenario 7: Remember Me Functionality

### Step 1: Login with Remember Me Checked
1. Login with verified account
2. Make sure "Remember Me" checkbox is ✅ checked
3. Submit login

### Step 2: Verify localStorage
1. Open DevTools → **Application** → **Local Storage**
2. Look for `http://localhost:3000`
3. Should see:
   - `user` = JSON string with user data
   - `rememberMe` = "true"

### Step 3: Close and Reopen Browser
1. Close browser completely
2. Reopen to `http://localhost:3000`
3. Should stay logged in (user data persisted)

---

## Test Scenario 8: Session Storage (Without Remember Me)

### Step 1: Login Without Remember Me
1. Login with verified account
2. Make sure "Remember Me" checkbox is **unchecked**
3. Submit login

### Step 2: Verify sessionStorage
1. Open DevTools → **Application** → **Session Storage**
2. Look for `http://localhost:3000`
3. Should see:
   - `user` = JSON string with user data
   - No `rememberMe` key

### Step 3: Close Browser Tab
1. Close the tab/window
2. Reopen to `http://localhost:3000`
3. Should be logged out (session storage cleared)

---

## Test Scenario 9: Email Case Normalization

### Step 1: Register with Mixed Case Email
1. Sign up with email: **John.Doe@EXAMPLE.COM**
2. Complete registration

### Step 2: Verify Stored as Lowercase
```bash
# In mongosh
db.users.find({ email: /doe/ })

# Should show email stored as: john.doe@example.com
```

### Step 3: Try Login with Different Case
1. Login with: **JOHN.DOE@example.com**
2. Should work (email normalized)

---

## Test Scenario 10: Password Strength Validation

### Test Case A: Too Short
1. Try to register with password: "short"
2. Should show error: "Password must be at least 8 characters"

### Test Case B: Exactly 8 Characters
1. Try to register with password: "ValidPas"
2. Should succeed

### Test Case C: Long Password
1. Try to register with password: "VeryLongSecurePassword123!@#"
2. Should succeed

---

## Automated Testing Commands

### Create Test User (CLI)
```bash
# Using curl
curl -X POST http://localhost:8080/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "TestPassword123",
    "name": "Test User",
    "phone": ""
  }'
```

### Login Test User (CLI)
```bash
curl -X POST http://localhost:8080/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "TestPassword123"
  }'
```

### Check MongoDB (CLI)
```bash
mongosh --eval "db.getSiblingDB('recipe_ai').users.findOne({email: 'test@example.com'})"
```

---

## Debugging Tips

### 1. Enable Backend Debug Logging
```python
# In backend/server.py - set logging level
logging.basicConfig(level=logging.DEBUG)
```

### 2. Check API Response Status
```javascript
// In browser console after login attempt
fetch('http://localhost:8080/api/auth/login', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    email: 'test@example.com',
    password: 'TestPassword123'
  })
})
.then(r => r.json())
.then(d => console.log('Status:', response.status, 'Data:', d))
```

### 3. Monitor MongoDB Queries
```bash
# Start MongoDB with profiling
mongosh
db.setProfilingLevel(1)
db.system.profile.find().limit(5).sort({ ts: -1 }).pretty()
```

### 4. Check Network Tab
1. Open DevTools → **Network** tab
2. Perform login
3. Click on `login` request
4. View **Response** tab for full backend response
5. View **Request** tab for what was sent

---

## Common Issues & Solutions

### Issue: "User not found" when user exists
- ✅ Check email normalization (should be lowercase)
- ✅ Verify MongoDB index exists: `db.users.getIndexes()`
- ✅ Check MongoDB connection string in `.env`

### Issue: Password always fails
- ✅ Verify bcrypt hash format (should start with `$2b$`)
- ✅ Check password is trimmed (no leading/trailing spaces)
- ✅ Confirm password case matters (case-sensitive)

### Issue: Verification code not working
- ✅ Check code hasn't expired (15 minutes)
- ✅ Verify code is exactly 6 digits
- ✅ Check `used` flag isn't set to `true`

### Issue: MongoDB connection timeout
- ✅ Verify MongoDB is running: `mongosh`
- ✅ Check MONGO_URL in `.env`
- ✅ Test connection: `mongosh $MONGO_URL`

---

## Performance Benchmarks

| Operation | Without Index | With Index | Target |
|-----------|---------------|-----------|--------|
| Register (duplicate check) | 500-1000ms | <5ms | ✅ <10ms |
| Login (user lookup) | 500-1000ms | <5ms | ✅ <10ms |
| Password verify | 100-200ms | 100-200ms | ✅ <200ms |
| **Total Login** | 1100-2200ms | 200-410ms | ✅ <500ms |

---

## Success Criteria Checklist

- ✅ User can successfully register
- ✅ User document created in MongoDB
- ✅ Email stored as lowercase
- ✅ Password hashed with bcrypt
- ✅ Duplicate emails rejected
- ✅ User can login with correct credentials
- ✅ Wrong password rejected
- ✅ Unverified user requires verification
- ✅ Last login updated on login
- ✅ Remember me works for persistence
- ✅ Session storage clears on browser close
- ✅ All console logs appear
- ✅ API response times < 500ms
- ✅ No errors in browser console
- ✅ Database indexes working

---

## Next Steps

Once testing is complete:

1. **Deploy Backend** to Cloud Run / production
2. **Update Frontend** API URL from localhost
3. **Test in Production** with real email
4. **Monitor** logs for errors
5. **Set up** automated backups for MongoDB
