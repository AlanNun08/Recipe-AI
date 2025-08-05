# Deployment Troubleshooting Guide

## Common Build Errors and Solutions

### ❌ Node.js Version Incompatibility
```
error @capacitor/cli@7.4.2: The engine "node" is incompatible with this module. Expected version ">=20.0.0". Got "18.20.8"
```

**Cause**: Capacitor mobile dependencies require Node 20+, but we're using Node 18

**Solution Applied**: 
1. Updated Dockerfile to use Node 20
2. Created web-only package.json without mobile dependencies
3. Generated separate yarn.web.lock for cleaner builds

### ❌ Yarn Lockfile Error
```
error Your lockfile needs to be updated, but yarn was run with `--frozen-lockfile`.
```

**Cause**: `package.json` and `yarn.lock` are out of sync

**Solution**: 
1. Regenerate yarn.lock locally:
   ```bash
   cd frontend/
   rm yarn.lock
   yarn install
   git add yarn.lock
   git commit -m "Update yarn.lock"
   ```

2. Or use the improved Dockerfile (already applied) that doesn't use `--frozen-lockfile`

### ❌ Docker Build Context Too Large
**Solution**: Update `.dockerignore` to exclude unnecessary files:
```
node_modules/
*/node_modules/
.git/
*.log
build/
dist/
```

### ❌ Memory Issues During Build
**Solution**: Increase machine type in `cloudbuild.yaml`:
```yaml
options:
  machineType: 'E2_HIGHCPU_8'  # Already set
  diskSizeGb: '100'            # Already set
```

### ❌ Environment Variables Not Set
**Check**: Ensure all environment variables are set in Google Cloud Run:
- MONGO_URL
- DB_NAME (should be: buildyoursmartcart_production)
- OPENAI_API_KEY
- WALMART_CONSUMER_ID, WALMART_KEY_VERSION, WALMART_PRIVATE_KEY
- MAILJET_API_KEY, MAILJET_SECRET_KEY, SENDER_EMAIL
- STRIPE_API_KEY
- SECRET_KEY

### ✅ Testing Builds Locally
Run the test build script:
```bash
./test-build.sh
```

### ✅ Manual Deploy Command
If automatic deploy fails, try manual deployment:
```bash
gcloud run deploy buildyoursmartcart \
  --source . \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --memory 2Gi \
  --cpu 2
```

## Current Status ✅
- ✅ Dockerfile optimized for Cloud Build
- ✅ yarn.lock regenerated and in sync
- ✅ cloudbuild.yaml configured with correct environment variables
- ✅ Production backend tested and working
- ✅ All environment variables confirmed in Google Cloud

## Next Steps
1. Commit all changes to git
2. Push to your connected GitHub repository  
3. Google Cloud Build will automatically trigger
4. Monitor build logs in Google Cloud Console