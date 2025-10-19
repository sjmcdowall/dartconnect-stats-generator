# Manual Wix Upload Process Documentation

**Purpose**: Document the step-by-step manual process for uploading PDFs to Wix
**Date**: 2025-10-19
**Status**: IN PROGRESS - Collecting steps from user

## Important Notes
- This document uses TEXT ONLY (no screenshots to avoid size issues)
- Each step will be described in detail with:
  - URL visited
  - Buttons/links clicked
  - Form fields filled
  - Selectors/identifiers where possible

## Steps Documented So Far

### Step 1: Initial Access
**URL**: https://www.wix.com/
**Action**: Navigate to Wix homepage
**Next**: Login process (Step 2)

### Step 2: Login - Part A (Click Login Button)
**Location**: Upper right area of wix.com homepage
**Element**: "Log In" link/button
**Action**: Click the "Log In" button
**Next**: Login form appears (documenting in Part B)

### Step 2: Login - Part B (Login Form)
**URL**: https://users.wix.com/signin
**Query params**:
- view=sign-up
- sendEmail=true
- postLogin=https://manage.wix.com/account/route
- originUrl=https://www.wix.com/
**Action**: Login form page loads
**Next**: Fill in credentials (documenting in Part C)

### Step 2: Login - Part C (Enter Credentials)
**Fields**:
- Email field: User's email address
- Password field: User's password
**Credentials**: Will use WIX_EMAIL and WIX_PASSWORD environment variables
**Action**: Fill in email and password, click submit button
**Next**: 2FA authentication required (documenting in Part D)

### Step 2: Login - Part D (2FA Authentication)
**Trigger**: After submitting email/password
**Action**: 2FA authentication prompt appears
**Type**: (documenting details next - SMS, authenticator app, email code, etc.)

### Step 3: Upload Process
<!-- User will provide steps here -->

### Step 4: Publish/Update
<!-- User will provide steps here -->

---

## Steps Still Needed
<!-- We'll fill this in as we go -->

---

## Technical Implementation Notes

### Selenium Approach
- Similar to `scripts/fetch_exports.py` (DartConnect automation)
- Use Selenium WebDriver for browser automation
- Store credentials in environment variables (WIX_EMAIL, WIX_PASSWORD)
- Handle login, navigation, file upload, and publish

### API Approach (Failed)
- Attempted to use Wix REST API
- Documentation URLs returned 404 errors
- Not pursuing this approach
