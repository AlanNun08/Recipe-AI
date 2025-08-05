# Double API Prefix Fix

## Problem Identified
After deployment, frontend was making requests to `https://buildyoursmartcart.com/api/api/auth/login` instead of `https://buildyoursmartcart.com/api/auth/login`.

## Root Cause
- Frontend environment variable: `REACT_APP_BACKEND_URL=https://buildyoursmartcart.com/api`
- Frontend code pattern: `${API}/api/auth/login`
- Result: `https://buildyoursmartcart.com/api/api/auth/login` (double /api prefix)

## Fix Applied
Updated environment variables to remove the `/api` suffix:

**Before:**
```
REACT_APP_BACKEND_URL=https://buildyoursmartcart.com/api
```

**After:**
```  
REACT_APP_BACKEND_URL=https://buildyoursmartcart.com
```

## Files Updated
1. `/app/frontend/.env`
2. `/app/frontend/.env.production` 
3. `/app/cloudbuild.yaml`

## Result
Now API calls will correctly resolve to:
- `https://buildyoursmartcart.com/api/auth/login` ✅
- `https://buildyoursmartcart.com/api/recipes/generate` ✅
- `https://buildyoursmartcart.com/api/auth/register` ✅

## Deployment Steps
1. Commit these changes
2. Push to GitHub (triggers Google Cloud Build)
3. New deployment will have correct API endpoints

## Verification
After deployment, check browser network tab to confirm requests go to:
- `https://buildyoursmartcart.com/api/...` ✅ (single /api prefix)
- NOT `https://buildyoursmartcart.com/api/api/...` ❌ (double /api prefix)