# Mailjet Email Verification Setup Guide

## Overview
When a user creates an account in Recipe-AI, a verification code is automatically sent via **Mailjet Email API**. This document explains how the email sending system works and how to set it up.

## How It Works

### 1. **User Registration Flow**
```
User creates account
    ↓
Backend generates 6-digit verification code
    ↓
Backend saves code to verification_codes collection (expires in 15 mins)
    ↓
Backend calls send_verification_email(email, code)
    ↓
Email is sent via Mailjet API ✉️
    ↓
User receives email with verification code
    ↓
User enters code to verify account
```

### 2. **Email Content**
The verification email includes:
- **Subject**: "Verify Your Recipe-AI Account"
- **HTML Template**: Beautiful branded email with verification code prominently displayed
- **Plain Text**: Fallback text version for email clients that don't support HTML
- **Code Display**: 6-digit code in large, monospace font for easy reading
- **Expiration Notice**: "This code expires in 15 minutes"
- **Security Message**: "If you didn't create this account, you can safely ignore this email"

### 3. **Email Template Preview**
```
┌─────────────────────────────────────────┐
│  🍳 Welcome to Recipe-AI!               │
├─────────────────────────────────────────┤
│                                         │
│  Thank you for creating an account.    │
│  Please verify your email using the    │
│  code below:                           │
│                                         │
│  ┌─────────────────────────────────┐  │
│  │  123456                         │  │
│  └─────────────────────────────────┘  │
│                                         │
│  This code expires in 15 minutes.      │
│                                         │
│  If you didn't create this account,    │
│  you can safely ignore this email.     │
│                                         │
│  © 2025 Recipe-AI. All rights reserved.│
└─────────────────────────────────────────┘
```

## Environment Setup

### Required Environment Variables
Add these to your `.env` file or set them in your hosting platform:

```bash
# Mailjet API Credentials (https://app.mailjet.com/account/api_keys)
MAILJET_API_KEY=your_mailjet_api_key_here
MAILJET_SECRET_KEY=your_mailjet_secret_key_here

# Sender Email (should be a verified sender on Mailjet)
SENDER_EMAIL=noreply@buildyoursmartcart.com
```

### Getting Mailjet Credentials

1. **Create a Mailjet Account**
   - Go to https://www.mailjet.com
   - Sign up for a free account
   - Verify your email address

2. **Get API Keys**
   - Log in to Mailjet dashboard
   - Go to "Account" → "API Keys"
   - Copy your "API Key" and "Secret Key"
   - Add them to your `.env` file

3. **Verify Sender Email**
   - Go to "Account" → "Verified Senders"
   - Add your sender email (e.g., `noreply@buildyoursmartcart.com`)
   - Verify the email address (Mailjet will send a verification link)

4. **Update App Settings (Optional)**
   - Go to "Account" → "Settings"
   - Set up SPF/DKIM records for better deliverability
   - Configure bounce/complaint handling

## Code Implementation

### Backend Function: `send_verification_email()`
Located in `backend/server.py` (lines 277-358)

```python
async def send_verification_email(email: str, code: str) -> bool:
    """Send verification email using Mailjet API"""
    
    # Check if credentials are configured
    if not mailjet_api_key or not mailjet_secret_key:
        logger.warning(f"Mailjet credentials not configured")
        # In dev mode, just log the code instead of sending
        return True
    
    # Create Mailjet client
    mailjet = Client(auth=(mailjet_api_key, mailjet_secret_key))
    
    # Prepare email data
    data = {
        "Messages": [{
            "From": {
                "Email": sender_email,
                "Name": "Recipe-AI Team"
            },
            "To": [{
                "Email": email,
                "Name": "User"
            }],
            "Subject": "Verify Your Recipe-AI Account",
            "TextPart": text_content,
            "HTMLPart": html_content
        }]
    }
    
    # Send via Mailjet API
    result = mailjet.send.create(data=data)
    
    return result.status_code == 200
```

### Integration Points

#### 1. **Registration Endpoint** (`POST /api/auth/register`)
```python
# Step 1: Generate verification code
verification_code = generate_verification_code()

# Step 2: Save to database
await verification_codes_collection.insert_one({
    "email": request.email,
    "code": verification_code,
    "created_at": datetime.utcnow(),
    "expires_at": datetime.utcnow() + timedelta(minutes=15),
    "used": False
})

# Step 3: Send email with code
email_sent = await send_verification_email(request.email, verification_code)

# Step 4: Return response to frontend
return {
    "status": "success",
    "email_sent": email_sent,
    ...
}
```

#### 2. **Login - Unverified User** (`POST /api/auth/login`)
```python
# If user not verified
if not user.get("is_verified"):
    # Generate new verification code
    verification_code = generate_verification_code()
    
    # Send verification email again
    await send_verification_email(request.email, verification_code)
    
    return {
        "status": "verification_required",
        "message": "Please check your email for verification code"
    }
```

#### 3. **Resend Code Endpoint** (`POST /api/auth/resend-verification`)
```python
# Generate new code
verification_code = generate_verification_code()

# Update in database
await verification_codes_collection.update_one(
    {"email": email},
    {"$set": {
        "code": verification_code,
        "created_at": datetime.utcnow(),
        "expires_at": datetime.utcnow() + timedelta(minutes=15),
        "used": False
    }},
    upsert=True
)

# Send email
await send_verification_email(email, verification_code)
```

## Development vs Production

### Development Mode (No Mailjet Credentials)
When `MAILJET_API_KEY` or `MAILJET_SECRET_KEY` are not set:
- ✅ Email sending doesn't fail (returns `True`)
- ✅ Verification code is logged to console
- ✅ Registration continues normally
- 📝 Look at server logs to see the code: `🔐 Verification code for user@example.com: 123456`

### Production Mode (With Mailjet Credentials)
When credentials are configured:
- ✅ Emails are sent via Mailjet API
- ✅ Actual email appears in user's inbox
- ✅ Full audit trail in Mailjet dashboard
- ⚠️ Email failures are logged but don't block registration

## Troubleshooting

### Issue: Emails not being sent in production

**Check 1: Environment Variables**
```bash
# Verify credentials are set
echo $MAILJET_API_KEY
echo $MAILJET_SECRET_KEY
echo $SENDER_EMAIL
```

**Check 2: Mailjet Dashboard**
- Log in to https://app.mailjet.com
- Go to "Activity" → "Messages"
- Look for your test email
- Check if it shows as "sent", "bounced", or "failed"

**Check 3: Server Logs**
```bash
# Look for email-related logs
docker logs your_container_name | grep -i "mailjet\|email"
```

**Check 4: Sender Email Verified**
- Ensure sender email is verified in Mailjet
- Unverified senders cannot send emails
- Go to Mailjet → Account → Verified Senders

**Check 5: API Rate Limits**
- Mailjet free tier: 200 emails/day
- Check your account quota
- Upgrade if needed

### Issue: Verification code not showing in email

**Solution 1: Check Email Template**
- Verify `html_content` variable includes `{code}`
- Check that code is being passed correctly

**Solution 2: Check Email Client**
- Some email clients strip HTML
- Try plain text version
- Check spam folder

**Solution 3: Test with Mailjet API**
```bash
# Test email sending directly
curl -X POST https://api.mailjet.com/v3.1/send \
  -H 'Content-Type: application/json' \
  -d '{"Messages":[{"From":{"Email":"test@example.com"},"To":[{"Email":"recipient@example.com"}],"Subject":"Test","TextPart":"Hello"}]}' \
  -u "API_KEY:SECRET_KEY"
```

## Monitoring & Analytics

### Mailjet Dashboard
Track your email metrics:
- **Sent**: Total emails sent
- **Delivered**: Emails successfully delivered
- **Opened**: How many users opened the email
- **Clicked**: How many clicked links
- **Bounced**: Failed delivery (hard/soft bounces)
- **Spam Complaints**: Users marked as spam

### Logs
Check server logs for:
```
✅ Verification email sent successfully to user@example.com
❌ Mailjet API error: 401 - Invalid credentials
⚠️ Mailjet credentials not configured. Code would be: 123456
```

## Cost Estimation

### Mailjet Pricing
- **Free Tier**: 200 emails/day (up to 50 recipients per email)
- **Paid Plans**: Starting at $15/month for 30,000 emails/month

For Recipe-AI:
- 1 email per user registration
- 1 email per resend request
- ~100 new users/day = ~100 emails/day
- **Estimated monthly**: 3,000 emails = Within free tier ✅

## Best Practices

1. **Always verify sender email** in Mailjet before going live
2. **Monitor bounce rates** - high bounces indicate list quality issues
3. **Implement rate limiting** on resend endpoint to prevent abuse
4. **Log all email sends** for auditing and debugging
5. **Set up bounce handling** to auto-disable bouncing emails
6. **Test with real email** before production deployment
7. **Keep API keys secret** - never commit to GitHub
8. **Use environment variables** for all credentials
9. **Monitor Mailjet quota** to avoid surprise failures
10. **Implement fallback** - registration shouldn't fail if email fails

## Next Steps

1. ✅ Sign up for Mailjet account
2. ✅ Get API credentials
3. ✅ Verify sender email
4. ✅ Add credentials to `.env` file
5. ✅ Test registration flow
6. ✅ Check server logs for confirmation
7. ✅ Verify email arrives in inbox
8. ✅ Monitor Mailjet dashboard for metrics

## References

- **Mailjet Documentation**: https://dev.mailjet.com/
- **Mailjet Python Library**: https://github.com/mailjet/mailjet-apiv3-python
- **Email Best Practices**: https://docs.mailjet.com/article/email-best-practices
- **Sender Verification**: https://docs.mailjet.com/article/verified-senders
