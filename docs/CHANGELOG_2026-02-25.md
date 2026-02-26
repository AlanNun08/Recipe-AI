# Change Log - 2026-02-25

Date: 2026-02-25

This document summarizes the changes completed in this work session, including logic updates, UI flow fixes, and documentation organization.

## Summary of Changes

### 1. Documentation Reorganization
- Organized documentation into topic-based folders under `docs/`
- Reduced root markdown clutter (kept `README.md` at the repo root)
- Added a docs navigation file

Created directories:
- `docs/authentication/`
- `docs/weekly-recipes/current/`
- `docs/weekly-recipes/root-copies/`
- `docs/ideas/`

Created file:
- `docs/README.md`

Moved docs:
- Authentication / verification docs moved into `docs/authentication/`
- Weekly recipe docs moved into `docs/weekly-recipes/current/`
- Root-level weekly recipe variants moved into `docs/weekly-recipes/root-copies/`
- `docs/new_ideas` moved to `docs/ideas/new_ideas`

Notes:
- No doc content was deleted where files differed; alternate copies were preserved.

### 2. Sign-up Form Password Logic (Front-End)
- Added `Confirm Password` field to sign-up flow
- Added `Show / Hide` toggles for password and confirm password
- Added password mismatch validation (`Passwords do not match`)
- Disabled sign-up submit when passwords do not match
- Switched sign-up submit to proper form `onSubmit` handling

Updated component:
- `frontend/src/components/WelcomeOnboarding.js`

Functions / logic updated:
- `handleRegisterAccount` (validation now checks `confirmPassword` and password match)
- Sign-up form render logic (`renderRegisterStep`) to include confirm password + toggles

### 3. Sign-up -> Email Verification -> Dashboard Flow Fix
- Fixed sign-up flow routing so new accounts do not go straight to dashboard
- Sign-up now routes to verification screen when `verification_required` is returned
- After successful email code verification, app auto-logs the user in and routes to dashboard
- Prevented verification screen from auto-resending a new code on mount (so the original Mailjet code remains valid)

Updated files:
- `frontend/src/App.js`
- `frontend/src/components/WelcomeOnboarding.js`
- `frontend/src/components/VerificationPage.js`

Functions / logic added or updated:
- `frontend/src/App.js`
  - Added `handleRegistrationVerificationRequired(...)`
  - Updated `handleVerificationSuccess(...)` to auto-login after verification
  - Updated `handleLoginSuccess(...)` user normalization
  - Updated `handleVerificationRequired(...)`
- `frontend/src/components/WelcomeOnboarding.js`
  - Added callback support via `onRegistrationVerificationRequired`
  - Updated registration success path to route into verification instead of dashboard
- `frontend/src/components/VerificationPage.js`
  - Updated mount behavior to stop auto-resending verification codes

### 4. Dashboard Cleanup
- Removed the "Account Information" panel from the dashboard UI (Email / Verified / Subscription / Joined card)

Updated file:
- `frontend/src/components/DashboardScreen.js`

### 5. Trial / Subscription Access Logic (7-Day Free Trial)
- Implemented real trial status evaluation in backend (replaced mock response)
- Changed new-user trial duration from `50 days` to `7 days`
- Enforced access rules on generation endpoints (backend-side)
- Users keep access to history/current saved content after trial expires
- Users are blocked from generating new AI content after trial expires unless subscribed

Backend behavior implemented:
- `7-day` free trial on registration
- Generation blocked after trial expiry for:
  - AI recipe generation
  - Weekly plan generation
  - Starbucks drink generation
- Trial status endpoint now returns computed access state:
  - `has_access`
  - `trial_active`
  - `trial_expired`
  - `trial_days_left`
  - `subscription_active`
  - date fields (`trial_start_date`, `trial_end_date`, etc.)

Updated file:
- `backend/server.py`

Functions added (backend):
- `_parse_datetime(value)`
- `_build_access_status(user)`
- `_get_user_access_status(user_id)`
- `_enforce_generation_access(user_id, feature_label)`

Functions updated (backend):
- `register(...)` (7-day trial end date)
- `generate_recipe(...)` (access enforcement)
- `generate_weekly_plan(...)` (access enforcement)
- `generate_starbucks_drink(...)` (access enforcement)
- `get_trial_status(...)` (real status response instead of mock)

### 6. Non-Intrusive Upgrade Prompts (Front-End)
- Added gentle upgrade prompts on generator screens when trial has expired
- Kept history/current content accessible (no hard blocking on browsing saved data)
- Disabled generation actions/buttons after trial expiry while showing clear messaging

Updated files:
- `frontend/src/components/RecipeGeneratorScreen.js`
- `frontend/src/components/WeeklyRecipesScreen.js`

Functions / logic added or updated:
- `RecipeGeneratorScreen`
  - Added trial status loading
  - Added `hasGenerationAccess`
  - Added `handleUpgradeClick()`
  - Updated `generateRecipe()` to respect trial access and handle `402` upgrade-required response
- `WeeklyRecipesScreen`
  - Added trial status-based `hasGenerationAccess`
  - Added `handleUpgradeClick()`
  - Updated `generateWeeklyPlan()` to block generation after trial expiry and handle backend `402`
  - Disabled "Generate New Plan" / submit actions after trial expiry

### 7. Trial Messaging Copy Updates (Consistency)
- Updated UI text to consistently say `7-day` trial (instead of `50 days` / `7-week`)

Updated files:
- `frontend/src/components/LandingPage.js`
- `frontend/src/components/SubscriptionScreen.js`
- `frontend/src/components/SubscriptionGate.js`

## Files Updated (Code / UI / Backend)

- `backend/server.py`
- `frontend/src/App.js`
- `frontend/src/components/WelcomeOnboarding.js`
- `frontend/src/components/VerificationPage.js`
- `frontend/src/components/DashboardScreen.js`
- `frontend/src/components/RecipeGeneratorScreen.js`
- `frontend/src/components/WeeklyRecipesScreen.js`
- `frontend/src/components/LandingPage.js`
- `frontend/src/components/SubscriptionScreen.js`
- `frontend/src/components/SubscriptionGate.js`

## Files Created

- `docs/README.md`
- `docs/CHANGELOG_2026-02-25.md` (this file)

## Documentation Structure Changes (Moved)

Moved/organized documentation into:
- `docs/authentication/`
- `docs/weekly-recipes/current/`
- `docs/weekly-recipes/root-copies/`
- `docs/ideas/`

## Validation Performed

- Backend syntax check:
  - `python3 -m py_compile backend/server.py` (passed)

## Deployment Note

These changes require:
1. Committing the relevant files to git
2. Pushing to GitHub
3. Running the Google deployment pipeline (or Cloud Build trigger) from GitHub

---

## Addendum - 2026-02-26 (Trial Countdown UI + Daily DB Sync)

Date: 2026-02-26

### A. Dashboard Trial Visibility + Countdown Prompt
- Added trial banner to the dashboard for logged-in users
- Shows active trial countdown (`X days left`)
- Shows a gentle expired-trial prompt (non-intrusive) with CTA to view subscription plans
- CTA opens the existing subscription modal from the dashboard

Updated files:
- `frontend/src/components/DashboardScreen.js`
- `frontend/src/components/TrialStatusBanner.js`

Functions / UI logic updated:
- `DashboardScreen`
  - Added `showSubscriptionModal` state
  - Rendered `TrialStatusBanner` for logged-in users
  - Wired `onUpgradeClick` to open `SubscriptionScreen`
- `TrialStatusBanner`
  - Updated expired-trial prompt styling and copy to be calmer / less aggressive
  - Updated expired CTA label to `View Plans`

### B. Trial Countdown DB Sync (Once Per Day)
- Added backend logic to persist trial countdown/status fields to the user document
- Updates occur at most once per UTC day per user when trial status is checked or access is evaluated
- Also initializes countdown fields at registration for new users

Updated file:
- `backend/server.py`

Functions added (backend):
- `_sync_trial_countdown_fields(user, access_status)`

Functions updated (backend):
- `_get_user_access_status(user_id)` (now triggers countdown sync)
- `_build_access_status(user)` (improved expired-trial handling)
- `register(...)` (initializes trial countdown fields on user creation)
- `get_trial_status(...)` (uses synced access-status helper)

User DB fields maintained:
- `trial_days_left`
- `trial_active`
- `trial_expired`
- `trial_countdown_last_updated_date`
- `trial_last_synced_at`

Validation performed:
- `python3 -m py_compile backend/server.py` (passed)

### C. Front-End URL Routing / Page Path Sync
- Added URL-to-component routing sync in the front-end app shell so direct page URLs load the correct screens
- Browser path now updates when switching screens in-app
- Browser back/forward navigation now syncs with the current component view

Examples now supported:
- `/signup` -> sign-up flow (`welcome` view)
- `/login` -> login screen
- `/verify` -> verification screen
- `/dashboard` -> dashboard screen
- `/weekly-recipes` -> weekly planner
- `/recipe-generator` -> recipe generator

Updated file:
- `frontend/src/App.js`

Functions / logic added:
- `VIEW_TO_PATH` mapping
- `PATH_ALIASES` mapping
- `getViewFromPath(pathname)`
- `popstate` listener to sync browser navigation with app state
- URL sync effect to push route changes when `currentView` changes

Git commit:
- `cce2623` (`feat(frontend): sync component views with URL routes`)
