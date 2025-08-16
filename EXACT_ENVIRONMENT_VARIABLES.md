# ✅ **EXACT Environment Variables - Google Cloud Run**

## 📋 **Complete List - Deployed in Google Cloud Run Console**

These are the **exact** environment variable names that are set in your Google Cloud Run deployment and accessed by the application:

```bash
# Database Configuration
MONGO_URL = "mongodb+srv://username:password@cluster.mongodb.net/database"
DB_NAME = "buildyoursmartcart_production"

# AI Services
OPENAI_API_KEY = "sk-proj-your-openai-api-key"

# Stripe Payment Processing  
STRIPE_SECRET_KEY = "sk_live_your-stripe-secret-key"
STRIPE_PUBLISHER_API_KEY = "pk_live_your-stripe-publisher-key"

# Email Service
MAILJET_API_KEY = "your-mailjet-api-key"
MAILJET_SECRET_KEY = "your-mailjet-secret-key"  
SENDER_EMAIL = "noreply@buildyoursmartcart.com"

# Walmart Integration
WALMART_CONSUMER_ID = "your-walmart-consumer-id"
WALMART_KEY_VERSION = "1"
WALMART_PRIVATE_KEY = "-----BEGIN PRIVATE KEY-----
your-walmart-private-key-content
-----END PRIVATE KEY-----"

# Security & Configuration
SECRET_KEY = "your-strong-random-jwt-secret"
NODE_ENV = "production"  # Important: Enables production mode
```

## 🔗 **Code Mapping - How Variables Are Used**

### **Database:**
```python
mongo_url = os.environ.get('MONGO_URL')  ✅
db_name = os.environ.get('DB_NAME')  ✅
```

### **AI Services:**
```python
openai_api_key = os.environ.get('OPENAI_API_KEY')  ✅
```

### **Stripe Payment:**
```python
stripe_secret_key = os.environ.get('STRIPE_SECRET_KEY')  ✅
stripe_publisher_key = os.environ.get('STRIPE_PUBLISHER_API_KEY')  ✅
```

### **Email Service:**
```python
mailjet_api_key = os.environ.get('MAILJET_API_KEY')  ✅
mailjet_secret_key = os.environ.get('MAILJET_SECRET_KEY')  ✅
sender_email = os.environ.get('SENDER_EMAIL')  ✅
```

### **Walmart Integration:**
```python
walmart_consumer_id = os.environ.get('WALMART_CONSUMER_ID')  ✅
walmart_key_version = os.environ.get('WALMART_KEY_VERSION')  ✅
walmart_private_key = os.environ.get('WALMART_PRIVATE_KEY')  ✅
```

### **Security:**
```python
secret_key = os.environ.get('SECRET_KEY')  ✅
```

## ✅ **Fixed Variable Names**

### **Stripe Variables (Updated to Match Your Deployment):**
- ❌ **OLD**: `STRIPE_API_KEY` → ✅ **NEW**: `STRIPE_SECRET_KEY`
- ❌ **OLD**: `STRIPE_PUBLISHABLE_KEY` → ✅ **NEW**: `STRIPE_PUBLISHER_API_KEY`

## 🎯 **How It Works:**

### **1. Google Cloud Run Console:**
You set each variable with real production values

### **2. Google Cloud Run Runtime:**
Injects these as system environment variables in the container

### **3. Application Code:**
Uses `os.environ.get('VARIABLE_NAME')` to access the values

### **4. Services Connect:**
- MongoDB connects using `MONGO_URL`
- Stripe processes payments using `STRIPE_SECRET_KEY`
- OpenAI generates recipes using `OPENAI_API_KEY`
- Mailjet sends emails using `MAILJET_API_KEY` & `MAILJET_SECRET_KEY`
- Walmart API works using `WALMART_CONSUMER_ID` & `WALMART_PRIVATE_KEY`

## 📊 **Environment Validation:**

The application logs will show:
```
✅ Production mode: Using system environment variables
✅ 📊 Connecting to MongoDB: *** (credentials masked)
✅ 📧 Email service: Mailjet configured with live keys
✅ Backend initialized with external APIs configured
```

## 🚀 **Deployment Status:**

When you deploy to Google Cloud Run:
1. ✅ **All 12 variables** are set in Google Cloud Console
2. ✅ **Application reads** them via `os.environ.get()`
3. ✅ **All services connect** using the real production values
4. ✅ **No .env files** needed in the production container

## 🔍 **Quick Verification:**

After deployment, check the health endpoint:
```bash
curl https://your-service-url/api/health
```

Should show:
```json
{
  "external_apis": {
    "openai": true,
    "stripe": true, 
    "mailjet": true,
    "walmart": true
  }
}
```

**Perfect! The application now uses the exact same environment variable names that you have deployed in Google Cloud Run.** 🎯

All 12 environment variables will be properly accessed from the Google Cloud Run environment!