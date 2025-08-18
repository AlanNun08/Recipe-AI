# 🚀 GitHub + Google Cloud Build Triggers Setup

## 📋 **Overview**
Set up automatic deployment from your GitHub repository to Google Cloud using Cloud Build triggers. Every time you push code to GitHub, it will automatically build and deploy your application.

## 🔧 **Step 1: Enable Required APIs**

```bash
# Enable necessary Google Cloud services
gcloud services enable cloudbuild.googleapis.com
gcloud services enable containerregistry.googleapis.com
gcloud services enable run.googleapis.com
gcloud services enable appengine.googleapis.com
```

## 🔗 **Step 2: Connect GitHub Repository**

### **Option A: Using Google Cloud Console (Recommended)**

1. **Go to Cloud Build Triggers**
   - Visit: https://console.cloud.google.com/cloud-build/triggers
   - Click "Connect Repository"

2. **Select Source**
   - Choose "GitHub (Cloud Build GitHub App)"
   - Click "Continue"

3. **Authenticate GitHub**
   - Sign in to your GitHub account
   - Authorize Google Cloud Build
   - Select your repository

4. **Repository Connection**
   - Choose your repository: `your-username/buildyoursmartcart`
   - Click "Connect Repository"

### **Option B: Using gcloud CLI**

```bash
# Connect your GitHub repository
gcloud source repos create buildyoursmartcart
gcloud source repos clone buildyoursmartcart
```

## ⚙️ **Step 3: Create Build Triggers**

I've created **two build configurations** for you to choose from:

### **Option A: App Engine Deployment (RECOMMENDED)** ✅
Uses `cloudbuild-appengine.yaml` - More reliable, fewer issues

### **Option B: Cloud Run Deployment**
Uses `cloudbuild-cloudrun.yaml` - More scalable, but had container issues

## 🎯 **Step 4A: Set Up App Engine Trigger (RECOMMENDED)**

### **Create the Trigger:**
1. **Go to Cloud Build Triggers**
2. **Click "Create Trigger"**
3. **Configure:**
   ```
   Name: deploy-buildyoursmartcart-appengine
   Event: Push to a branch
   Repository: your-username/buildyoursmartcart
   Branch: ^main$ (or ^master$)
   Configuration: Cloud Build configuration file (yaml or json)
   Cloud Build configuration file location: cloudbuild-appengine.yaml
   ```

### **Environment Variables:**
The trigger will use your `app.yaml` file which contains:
```yaml
env_variables:
  MONGO_URL: "YOUR_MONGODB_ATLAS_CONNECTION_STRING"
  STRIPE_SECRET_KEY: "YOUR_STRIPE_SECRET_KEY"
  STRIPE_PUBLISHER_API_KEY: "YOUR_STRIPE_PUBLISHER_API_KEY"
  # ... all your other variables
```

## 🎯 **Step 4B: Set Up Cloud Run Trigger (Alternative)**

### **First, Set Environment Variables:**
```bash
# Set all your environment variables in Cloud Run
gcloud run services update buildyoursmartcart \
  --region=us-central1 \
  --set-env-vars="MONGO_URL=your-mongodb-url,OPENAI_API_KEY=your-openai-key,STRIPE_SECRET_KEY=your-stripe-key,STRIPE_PUBLISHER_API_KEY=your-stripe-publisher-key,MAILJET_API_KEY=your-mailjet-key,MAILJET_SECRET_KEY=your-mailjet-secret,SENDER_EMAIL=noreply@buildyoursmartcart.com,SECRET_KEY=your-secret,NODE_ENV=production"
```

### **Create the Trigger:**
1. **Go to Cloud Build Triggers**
2. **Click "Create Trigger"**
3. **Configure:**
   ```
   Name: deploy-buildyoursmartcart-cloudrun
   Event: Push to a branch
   Repository: your-username/buildyoursmartcart
   Branch: ^main$ (or ^master$)
   Configuration: Cloud Build configuration file (yaml or json)
   Cloud Build configuration file location: cloudbuild-cloudrun.yaml
   ```

## 🔒 **Step 5: Grant Necessary Permissions**

```bash
# Get your project number
PROJECT_NUMBER=$(gcloud projects describe $PROJECT_ID --format="value(projectNumber)")

# Grant Cloud Build service account necessary permissions
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:${PROJECT_NUMBER}@cloudbuild.gserviceaccount.com" \
    --role="roles/appengine.appAdmin"

gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:${PROJECT_NUMBER}@cloudbuild.gserviceaccount.com" \
    --role="roles/run.admin"

gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:${PROJECT_NUMBER}@cloudbuild.gserviceaccount.com" \
    --role="roles/iam.serviceAccountUser"
```

## 🧪 **Step 6: Test the Trigger**

### **Method 1: Push to GitHub**
```bash
# Make a small change and push
echo "# Auto-deployment test" >> README.md
git add README.md
git commit -m "Test auto-deployment"
git push origin main
```

### **Method 2: Manual Trigger**
1. Go to Cloud Build Triggers
2. Find your trigger
3. Click "Run Trigger"

## 📊 **Step 7: Monitor Deployment**

### **View Build Logs:**
- **Cloud Build**: https://console.cloud.google.com/cloud-build/builds
- **Real-time logs**: Click on your build to see progress

### **Expected Build Steps:**
```
✅ Step 1: Install frontend dependencies
✅ Step 2: Build frontend for production  
✅ Step 3: Deploy to App Engine/Cloud Run
✅ Build completed successfully
```

### **Verify Deployment:**
```bash
# For App Engine
curl https://your-project.appspot.com/health

# For Cloud Run  
curl https://buildyoursmartcart-xxx-uc.a.run.app/health
```

## 📁 **File Structure for GitHub Repository**

Make sure your repository has:
```
your-repo/
├── app.yaml                      # App Engine config (if using App Engine)
├── cloudbuild-appengine.yaml     # Build config for App Engine
├── cloudbuild-cloudrun.yaml      # Build config for Cloud Run  
├── Dockerfile                    # Container config (if using Cloud Run)
├── main.py                       # Application entry point
├── requirements.txt              # Python dependencies
├── backend/
│   ├── server.py                # Backend API
│   └── .env                     # Local development only
├── frontend/
│   ├── package.json             # Frontend dependencies
│   ├── src/                     # React source code
│   └── public/                  # Static assets
└── README.md
```

## 🎯 **Workflow After Setup**

1. **Develop locally** and test your changes
2. **Push to GitHub** (`git push origin main`)
3. **Automatic trigger** starts Cloud Build
4. **Build process** runs (install deps, build frontend, deploy)
5. **Deployment complete** - your app is live!

## 🔍 **Troubleshooting**

### **If Build Fails:**
1. **Check Cloud Build logs** for specific error messages
2. **Verify repository connection** in Cloud Build console
3. **Check file paths** in cloudbuild.yaml
4. **Verify permissions** for Cloud Build service account

### **If Deployment Fails:**
1. **Check environment variables** are set correctly
2. **Test locally** first to ensure code works
3. **Review application logs** in App Engine/Cloud Run console

## ✅ **Benefits of This Setup**

- ✅ **Automatic deployment** on every Git push
- ✅ **No manual deployment** commands needed
- ✅ **Build history** and rollback capability
- ✅ **Integrated with GitHub** - see build status in PRs
- ✅ **Scalable** - handles multiple developers and branches

## 🚀 **Choose Your Approach**

**For most reliable deployment:**
- Use **App Engine** with `cloudbuild-appengine.yaml`
- Environment variables defined in `app.yaml`
- Less configuration, more reliable

**For maximum scalability:**
- Use **Cloud Run** with `cloudbuild-cloudrun.yaml`  
- Environment variables set via `gcloud run services update`
- More configuration, more scalable

**Ready to set up automatic deployment from GitHub!** 🎉