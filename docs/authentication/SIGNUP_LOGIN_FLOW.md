# Sign-Up and Login Flow Documentation

## Overview

This document describes the complete sign-up and login workflow for the Recipe AI application, with detailed information about MongoDB database integration, security measures, and error handling.

---

## Sign-Up Flow (Frontend → Backend → MongoDB)

### Frontend: WelcomeOnboarding Component

**File:** `frontend/src/components/WelcomeOnboarding.js`

1. **User Input Collection**
   - First Name
   - Last Name
   - Email
   - Password (minimum 8 characters)
   - Terms & Conditions Agreement
   - Email Updates Opt-in

2. **Validation (Client-side)**
   - ✅ All fields required
   - ✅ Terms must be agreed to
   - ✅ Password minimum 8 characters
   - ✅ Email format validation

3. **Registration Request**
   ```javascript
   POST /api/auth/register
   {
     "email": "user@example.com",
     "password": "SecurePassword123",
     "name": "John Doe",
     "phone": "" // optional
   }
   ```

4. **Logging**
   - 📝 Logs registration attempt
   - 📧 Logs email address (normalized)
   - 📤 Logs request payload
   - 📥 Logs API response
   - ✅ Logs success with user ID and trial end date

---

## Backend: Registration Endpoint

**File:** `backend/server.py` - `/api/auth/register`

### Step-by-Step Process

#### 1. **Input Validation**
```python
# Email format check
if not email or '@' not in email:
    return {"detail": "Invalid email format"}

# Password strength check
if len(password) < 8:
    return {"detail": "Password must be at least 8 characters"}
```

#### 2. **MongoDB Duplicate Check**
```python
# Search MongoDB for existing user with same email
existing_user = await users_collection.find_one({"email": email})
if existing_user:
    return {"detail": "User with this email already exists"}
```
- 🔍 Uses MongoDB `find_one()` query on `users` collection
- 🔑 Searches by normalized lowercase email
- ✅ Indexes on email field for fast lookup

#### 3. **Password Hashing**
```python
# Secure bcrypt hashing (salted)
hashed_password = hash_password(request.password)
```
- 🔐 Uses bcrypt with automatic salt generation
- 🛡️ Industry standard, resistant to rainbow table attacks
- ✅ Stored as `$2b$12$...` format

#### 4. **User Document Creation**
```python
user_document = {
    "id": str(uuid.uuid4()),              # Unique user ID
    "email": email,                        # Normalized lowercase
    "password_hash": hashed_password,     # Bcrypt hash
    "first_name": "John",
    "last_name": "Doe",
    "phone": None,
    
    # Dietary preferences
    "dietary_preferences": [],
    "allergies": [],
    "favorite_cuisines": [],
    
    # Verification
    "is_verified": False,
    "created_at": datetime.utcnow(),
    "verified_at": None,
    
    # Subscription (50-day trial)
    "subscription_status": "trial",
    "trial_start_date": now,
    "trial_end_date": now + 50 days,
    "subscription_start_date": None,
    "subscription_end_date": None,
    
    # Stripe (for future payments)
    "stripe_customer_id": None,
    "stripe_subscription_id": None,
    
    # Additional metadata
    "last_login": None,
    "preferences": {},
    "weekly_budget": None,
    "cooking_skill_level": None,
    "household_size": 4
}
```

#### 5. **MongoDB Insertion**
```python
# Insert into users collection
result = await users_collection.insert_one(user_document)
```
- 💾 Saves complete user document to MongoDB
- 🆔 Returns MongoDB ObjectId (plus custom user.id)
- ✅ Email unique index prevents duplicates

#### 6. **Verification Code Generation**
```python
verification_code = generate_verification_code()  # 6-digit code

verification_document = {
    "email": email,
    "code": verification_code,
    "created_at": datetime.utcnow(),
    "expires_at": datetime.utcnow() + 15 minutes,
    "used": False
}
```
- 📧 Saved to `verification_codes` collection
- ⏰ TTL index auto-removes after 15 minutes
- 📨 Sent to user via email

#### 7. **Response**
```json
{
    "status": "success",
    "message": "User registered successfully",
    "user_id": "550e8400-e29b-41d4-a716-446655440000",
    "email": "user@example.com",
    "first_name": "John",
    "last_name": "Doe",
    "verification_required": true,
    "email_sent": true,
    "subscription_status": "trial",
    "trial_end_date": "2026-03-06T15:30:00"
}
```

---

## Login Flow (Frontend → Backend → MongoDB)

### Frontend: LandingPage Component

**File:** `frontend/src/components/LandingPage.js`

1. **User Input**
   - Email
   - Password
   - "Remember me" checkbox (optional)

2. **Login Request**
   ```javascript
   POST /api/auth/login
   {
     "email": "user@example.com",
     "password": "SecurePassword123"
   }
   ```

3. **Logging**
   - 🔐 Logs login attempt
   - 📧 Logs normalized email
   - 📤 Logs request payload
   - 📥 Logs response status and data
   - ✅ Logs success with user details

---

## Backend: Login Endpoint

**File:** `backend/server.py` - `/api/auth/login`

### Step-by-Step Process

#### 1. **MongoDB User Lookup**
```python
# Search MongoDB for user by email
user = await users_collection.find_one({"email": email})
if not user:
    return {"detail": "Invalid email or password"} # 401
```
- 🔍 Queries `users` collection with email
- 🆔 Email indexed for O(log n) lookup performance
- ✅ User document contains all profile data

#### 2. **User Found Validation**
```python
# Verify required fields exist
if "password_hash" not in user:
    return {"error": "password_hash_missing"} # 500

if not user["password_hash"]:
    return {"detail": "User account corrupted"} # 500
```

#### 3. **Password Verification**
```python
# Compare provided password with stored bcrypt hash
if not verify_password(request.password, stored_hash):
    return {"detail": "Invalid email or password"} # 401
```
- 🔐 Uses bcrypt constant-time comparison
- 🛡️ Resistant to timing attacks
- ❌ Never reveals if email or password is wrong

#### 4. **Verification Status Check**
```python
is_verified = user.get("is_verified", False)
if not is_verified:
    # Generate new verification code
    verification_code = generate_verification_code()
    
    # Save to MongoDB
    await verification_codes_collection.update_one(
        {"email": email},
        {"$set": {...}},
        upsert=True
    )
    
    # Send verification email
    await send_verification_email(email, verification_code)
    
    return {"status": "verification_required"} # 403
```

#### 5. **Update Last Login**
```python
# Track user activity in MongoDB
await users_collection.update_one(
    {"email": email},
    {"$set": {"last_login": datetime.utcnow()}}
)
```

#### 6. **Success Response**
```json
{
    "status": "success",
    "message": "Login successful",
    "user_id": "550e8400-e29b-41d4-a716-446655440000",
    "email": "user@example.com",
    "first_name": "John",
    "last_name": "Doe",
    "is_verified": true,
    "subscription_status": "trial",
    "trial_start_date": "2026-01-15T10:00:00",
    "trial_end_date": "2026-03-06T10:00:00",
    "dietary_preferences": [],
    "allergies": [],
    "favorite_cuisines": []
}
```

---

## Frontend: After Successful Login

### LandingPage Component Storage

```javascript
// Remember me checkbox: saves to localStorage
if (rememberMe) {
    localStorage.setItem('user', JSON.stringify(userData));
    localStorage.setItem('rememberMe', 'true');
}

// Without remember me: saves to sessionStorage (cleared on browser close)
else {
    sessionStorage.setItem('user', JSON.stringify(userData));
}
```

### User Data Object
```javascript
{
    "user_id": "550e8400-e29b-41d4-a716-446655440000",
    "email": "user@example.com",
    "first_name": "John",
    "last_name": "Doe",
    "verified": true,
    "subscription_status": "trial"
}
```

---

## MongoDB Collections & Indexes

### Users Collection

**Collection Name:** `users`

**Indexes:**
```javascript
// Primary index for login speed
db.users.createIndex({ email: 1 }, { unique: true })

// For user lookups by ID
db.users.createIndex({ id: 1 })

// For Stripe integrations
db.users.createIndex({ stripe_customer_id: 1 }, { sparse: true })
```

**Document Schema:**
```javascript
{
    _id: ObjectId,           // MongoDB internal ID
    id: String,              // Custom UUID
    email: String,           // Unique, lowercase
    password_hash: String,   // Bcrypt hash
    first_name: String,
    last_name: String,
    phone: String,
    
    dietary_preferences: Array,
    allergies: Array,
    favorite_cuisines: Array,
    
    is_verified: Boolean,
    created_at: Date,
    verified_at: Date,
    
    subscription_status: String,  // "trial", "active", "cancelled"
    trial_start_date: Date,
    trial_end_date: Date,
    subscription_start_date: Date,
    subscription_end_date: Date,
    
    stripe_customer_id: String,
    stripe_subscription_id: String,
    last_payment_date: Date,
    next_billing_date: Date,
    
    last_login: Date,
    preferences: Object,
    weekly_budget: Number,
    cooking_skill_level: String,
    household_size: Number
}
```

### Verification Codes Collection

**Collection Name:** `verification_codes`

**Indexes:**
```javascript
// TTL index - auto-delete after 15 minutes
db.verification_codes.createIndex(
    { expires_at: 1 },
    { expireAfterSeconds: 0 }
)

// For code lookup
db.verification_codes.createIndex({ email: 1 })
```

---

## Security Features

### 1. **Password Security**
- ✅ Bcrypt hashing with automatic salt
- ✅ Minimum 8 characters required
- ✅ Constant-time comparison (prevents timing attacks)
- ✅ Never stores plaintext passwords

### 2. **Email Security**
- ✅ Normalized to lowercase before storing
- ✅ Unique constraint in MongoDB
- ✅ Trimmed of whitespace
- ✅ Format validated before processing

### 3. **Verification Process**
- ✅ 6-digit verification code
- ✅ 15-minute expiration
- ✅ Auto-deleted by TTL index
- ✅ One-time use flag
- ✅ Resent on failed login

### 4. **Database Security**
- ✅ Indexes for O(log n) lookups
- ✅ Unique constraints prevent duplicates
- ✅ TTL indexes auto-cleanup
- ✅ Proper error messages (don't leak user existence)

---

## Error Handling

### Common Error Scenarios

#### 1. **Email Already Exists**
```
Status: 400
{
    "detail": "User with this email already exists"
}
```

#### 2. **Invalid Credentials**
```
Status: 401
{
    "detail": "Invalid email or password"
}
```
⚠️ Generic message doesn't reveal if email or password is wrong

#### 3. **Account Not Verified**
```
Status: 403
{
    "status": "verification_required",
    "message": "Account not verified. Please check your email for verification code.",
    "email": "user@example.com",
    "user_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

#### 4. **Server Errors**
```
Status: 500
{
    "detail": "Registration/Login failed: [error message]"
}
```

#### 5. **Service Unavailable**
```
Status: 503
{
    "detail": "Authentication service is temporarily unavailable"
}
```

---

## Logging & Debugging

### Backend Logging (Server Side)

All operations are logged with emojis for easy scanning:

```
👤 Registration attempt for email: user@example.com
🔍 Checking if user exists in MongoDB: user@example.com
✅ Email is unique, proceeding with registration: user@example.com
🔐 Hashing password for: user@example.com
✅ Password hashed successfully
📧 Generated verification code for: user@example.com
💾 Inserting user into MongoDB: user@example.com
✅ User inserted successfully with MongoDB ID: ObjectId(...)
✅ Verification code saved for: user@example.com

🔐 Login attempt for email: user@example.com
🔍 Searching MongoDB for user: user@example.com
✅ User found in MongoDB: user@example.com
👤 User ID: 550e8400-e29b-41d4-a716-446655440000
🔐 Verifying password for: user@example.com
✅ Password verified successfully for: user@example.com
⏰ Updating last login for: user@example.com
✅ Last login updated in MongoDB
✅ Login successful for: user@example.com
```

### Frontend Logging (Client Side)

Console logs show user journey:

```
📝 Registering new user...
  📧 Email: user@example.com
  👤 Name: John Doe
  🔗 API URL: http://localhost:8080/api/auth/register
📤 Sending registration request: {...}
📡 Response status: 201
📥 Registration response: {...}
✅ Registration successful!
  👤 User ID: 550e8400-e29b-41d4-a716-446655440000
  📧 Email: user@example.com
  ⏰ Trial End Date: 2026-03-06T...
```

---

## Testing Sign-Up Flow

### Quick Test Checklist

1. **Sign-Up**
   - [ ] Open landing page or welcome screen
   - [ ] Fill in registration form
   - [ ] Submit form
   - [ ] See success message
   - [ ] Check console for logs
   - [ ] Verify email received

2. **MongoDB Verification**
   - [ ] Connect to MongoDB
   - [ ] Query `users` collection
   - [ ] Confirm new user document exists
   - [ ] Verify email is lowercase
   - [ ] Confirm password_hash is bcrypt format

3. **Login with New Account**
   - [ ] Go to login page
   - [ ] Enter registered email & password
   - [ ] Should see verification required message
   - [ ] Check console for login logs
   - [ ] Verify MongoDB last_login updated

4. **Verification Process**
   - [ ] Check email for verification code
   - [ ] Enter code in verification modal
   - [ ] Account should be marked verified
   - [ ] Next login should succeed

---

## Performance Optimization

### Database Indexes Impact

**Without indexes:**
- User lookup: O(n) - slow with many users
- Duplicate check: O(n) - slow

**With indexes:**
- User lookup: O(log n) - fast
- Duplicate check: O(log n) - fast

### Projected Performance
- 1,000 users: ~0ms (index)
- 1,000,000 users: ~3-5ms (index)
- 1,000,000 users without index: ~500-1000ms ❌

---

## Environment Variables Required

```bash
# MongoDB
MONGO_URL=mongodb://localhost:27017
DB_NAME=recipe_ai

# Email (for verification codes)
MAILJET_API_KEY=your_key
MAILJET_SECRET_KEY=your_secret
SENDER_EMAIL=noreply@buildyoursmartcart.com

# Optional: Stripe (for future payments)
STRIPE_SECRET_KEY=sk_test_...
```

---

## Troubleshooting

### Issue: "User not found" during login
- ✅ Verify user was successfully registered
- ✅ Check MongoDB for user document
- ✅ Confirm email is lowercase
- ✅ Check browser console for full error

### Issue: "Invalid password" during login
- ✅ Verify password is correct
- ✅ Check password_hash exists in MongoDB
- ✅ Confirm no special characters in password
- ✅ Password is case-sensitive

### Issue: Verification code not received
- ✅ Check spam/promotions folder
- ✅ Verify email in registration
- ✅ Check server logs for email send status
- ✅ Confirm Mailjet API keys are valid

### Issue: MongoDB connection error
- ✅ Verify MONGO_URL environment variable
- ✅ Check MongoDB service is running
- ✅ Verify DB_NAME is set
- ✅ Check network connectivity

---

## Future Enhancements

1. **OAuth/Social Login**
   - Google Sign-In
   - Facebook Login
   - Apple Sign-In

2. **Multi-Factor Authentication**
   - SMS verification
   - Authenticator apps
   - Recovery codes

3. **Password Reset**
   - Email-based reset
   - Secure token generation
   - Automatic expiration

4. **Session Management**
   - JWT tokens
   - Session storage
   - Auto-logout on inactivity

---

## Summary

✅ **Sign-up process:**
1. Frontend collects user info
2. Validates on client
3. Sends to backend
4. Backend validates & checks MongoDB
5. Creates bcrypt password hash
6. Saves user to MongoDB
7. Generates verification code
8. Sends verification email

✅ **Login process:**
1. Frontend collects credentials
2. Sends to backend
3. Backend searches MongoDB for user
4. Verifies bcrypt password hash
5. Checks verification status
6. Updates last login
7. Returns user data
8. Frontend stores in localStorage/sessionStorage

✅ **Security:**
- Bcrypt password hashing
- Email uniqueness constraint
- Verification code expiration
- Proper error messages
- Database indexes for performance
