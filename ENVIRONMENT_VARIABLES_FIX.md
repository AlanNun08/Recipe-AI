# 🔧 Environment Variables Fix for Google Cloud Run

## ❌ **THE PROBLEM WAS:**

The application was trying to load environment variables from a `.env` file that **doesn't exist** in the Google Cloud Run container. In production, environment variables are set directly by Google Cloud Run, not loaded from files.

```python
# THIS WAS WRONG:
load_dotenv()  # Tries to load from .env file (doesn't exist in container)
mongo_url = os.environ.get('MONGO_URL')  # Returns None if .env loading fails
```

## ✅ **THE FIX APPLIED:**

### **1. Smart Environment Loading**
```python
# NOW CORRECT:
def load_environment_variables():
    """Load environment variables from .env file in development, system env in production"""
    if os.getenv("NODE_ENV") == "production":
        # In production (Google Cloud Run), variables are set directly
        logger.info("Production mode: Using system environment variables")
    else:
        # In development, try to load from .env file
        env_file = Path(__file__).parent / '.env'
        if env_file.exists():
            load_dotenv(env_file)
            logger.info(f"Development mode: Loaded environment from {env_file}")
        else:
            logger.warning("Development mode: No .env file found, using system environment")
```

### **2. Proper Validation for Critical Variables**

**MongoDB Configuration:**
```python
mongo_url = os.environ.get('MONGO_URL')
if not mongo_url:
    if os.getenv("NODE_ENV") == "production":
        logger.error("❌ MONGO_URL environment variable is required in production")
        raise ValueError("MONGO_URL environment variable is required in production")
    else:
        mongo_url = 'mongodb://localhost:27017'
        logger.warning("⚠️ MONGO_URL not set, using localhost default for development")
```

**Email Service Configuration:**
```python
mailjet_api_key = os.environ.get('MAILJET_API_KEY')
mailjet_secret_key = os.environ.get('MAILJET_SECRET_KEY')
sender_email = os.environ.get('SENDER_EMAIL', 'noreply@buildyoursmartcart.com')

# Proper logging without exposing secrets
if mailjet_api_key and mailjet_secret_key:
    if not any(placeholder in mailjet_api_key for placeholder in ['your-', 'placeholder', 'here']):
        logger.info("📧 Email service: Mailjet configured with live keys")
    else:
        logger.info("📧 Email service: Mailjet configured with placeholder keys (development mode)")
```

### **3. Updated .dockerignore**
```
# Environment files (will be set by Cloud Run)
.env
backend/.env
frontend/.env
```

This ensures `.env` files are **never copied** to the production container.

## 🔍 **How to Set Environment Variables in Google Cloud Run:**

### **Method 1: Google Cloud Console (Recommended)**

1. Go to [Google Cloud Console](https://console.cloud.google.com/run)
2. Select your service (`buildyoursmartcart` or `recipe-ai`)
3. Click **"Edit Container"**
4. Go to **"Variables & Secrets"** tab
5. Click **"Add Environment Variable"**
6. Add each variable:

```bash
# Required Variables:
MONGO_URL = "mongodb+srv://username:password@cluster.mongodb.net/database"
DB_NAME = "buildyoursmartcart_production"
OPENAI_API_KEY = "sk-proj-your-openai-key"
STRIPE_API_KEY = "sk_live_your-stripe-key"
STRIPE_PUBLISHABLE_KEY = "pk_live_your-stripe-key"
MAILJET_API_KEY = "your-mailjet-api-key"
MAILJET_SECRET_KEY = "your-mailjet-secret"
SENDER_EMAIL = "noreply@buildyoursmartcart.com"
SECRET_KEY = "your-strong-random-secret"
NODE_ENV = "production"

# Walmart API (if needed):
WALMART_CONSUMER_ID = "your-walmart-consumer-id"
WALMART_KEY_VERSION = "1"
WALMART_PRIVATE_KEY = "-----BEGIN PRIVATE KEY-----
your-private-key-content
-----END PRIVATE KEY-----"
```

### **Method 2: Using gcloud CLI**

```bash
gcloud run services update buildyoursmartcart \
  --region=us-central1 \
  --set-env-vars="MONGO_URL=your-mongodb-url,OPENAI_API_KEY=your-openai-key,STRIPE_API_KEY=your-stripe-key,MAILJET_API_KEY=your-mailjet-key,MAILJET_SECRET_KEY=your-mailjet-secret,SENDER_EMAIL=noreply@buildyoursmartcart.com,SECRET_KEY=your-secret,NODE_ENV=production"
```

### **Method 3: In cloudbuild.yaml**
```yaml
- name: 'gcr.io/google.com/cloudsdktool/cloud-sdk'
  entrypoint: gcloud
  args:
    - 'run'
    - 'deploy'
    - 'buildyoursmartcart'
    - '--set-env-vars'
    - 'NODE_ENV=production,MONGO_URL=${_MONGO_URL},OPENAI_API_KEY=${_OPENAI_API_KEY}'
```

## 🧪 **Verification:**

After deploying with proper environment variables, check the logs:

```bash
# Check deployment logs
gcloud run services logs read buildyoursmartcart --region=us-central1 --limit=50

# Look for these success messages:
✅ "Production mode: Using system environment variables"
✅ "📊 Connecting to MongoDB: ***"
✅ "📧 Email service: Mailjet configured with live keys"
✅ "📧 Sender email: noreply@buildyoursmartcart.com"
```

## 🚨 **Critical Environment Variables:**

### **Must Have (App won't work without these):**
- ✅ `MONGO_URL` - Database connection
- ✅ `NODE_ENV=production` - Enables production mode

### **Should Have (Features won't work):**
- ✅ `OPENAI_API_KEY` - AI recipe generation
- ✅ `STRIPE_API_KEY` - Payment processing
- ✅ `MAILJET_API_KEY` & `MAILJET_SECRET_KEY` - Email notifications

### **Optional (Fallbacks available):**
- `SENDER_EMAIL` (defaults to noreply@buildyoursmartcart.com)
- `DB_NAME` (defaults to buildyoursmartcart_production)
- `SECRET_KEY` (should be set for security)

## 📋 **Deploy Command (Updated):**

```bash
# 1. First set environment variables in Cloud Console
# 2. Then deploy:
gcloud builds submit --config cloudbuild.yaml .
```

## ✅ **This Fix Resolves:**

✅ **Container startup failures** - Proper environment loading  
✅ **Database connection issues** - MONGO_URL properly loaded  
✅ **Email service failures** - MAILJET keys properly accessed  
✅ **Configuration errors** - Smart dev/prod environment handling  
✅ **Missing .env file errors** - No dependency on .env in production  

**The Google Cloud Run deployment should now properly load all environment variables!** 🎯