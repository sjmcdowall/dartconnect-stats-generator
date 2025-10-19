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

### Step 2: Login - Part C (Enter Credentials - DYNAMIC FORM)
**IMPORTANT**: Form is dynamic, fields appear sequentially

**Step C1 - Email**:
- Field: Email address
- Action: Enter email (WIX_EMAIL env var)
- Button: Click "Use Email" button
- Result: Password field appears below

**Step C2 - Password**:
- Field: Password (appears after clicking "Use Email")
- Action: Enter password (WIX_PASSWORD env var)
- Button: Click "Login" button
- Next: 2FA OTP page opens (Part D)

### Step 2: Login - Part D (2FA OTP Authentication)
**Trigger**: After submitting email/password
**Type**: 6-digit OTP code
**Storage**: User keeps OTP secret in 1Password
**Page**: New 2FA OTP page appears
**Action**: Enter 6-digit OTP code and submit
**Automation Note**: Will need "assisted mode" - pause for user to manually enter OTP
**Next**: After successful OTP, lands on "Manage Wix Dashboard" (Part E)

### Step 2: Login - Part E (Manage Wix Dashboard)
**Landing Page**: "Manage Wix Dashboard" (NOT the site editor yet!)
**Note**: This is the management dashboard, not the website editor
**Next Action**: Need to navigate to "Edit Site" (Step 3)

### Step 3: Navigate to Edit Site
**Location**: Upper right area of Manage Dashboard
**Element**: "Edit Site" button
**Action**: Click "Edit Site" button
**Next**: Navigates to site editor (documenting in Step 4)

### Step 4: Site Editor - Navigate to Pages & Menus
**View**: Site editor interface loads
**Navigation Bar**: Left-hand side vertical menu bar
**Target Option**: "Pages & Menus" (3rd main option from top)
**Action**: Click "Pages & Menus" option
**Next**: Pages & Menus panel opens (documenting in Step 5)

### Step 5: Select STATISTICS Page
**Result**: Pages & Menus menu pops up on the left side
**Options Shown**: List of pages in the site
**Target Page**: "STATISTICS" option
**Action**: Click on "STATISTICS"
**Next**: STATISTICS page context loads (documenting in Step 6)

### Step 6: STATISTICS Page Loads
**View**: Page switches to STATISTICS page view
**Content**: 3 main large icons displayed:
  1. "Individual"
  2. "schedule"
  3. "Overall"
**Nav Menu State**: Left nav menu stays open (doesn't auto-close)
**Action**: Click somewhere on the page to close/dismiss the nav menu
**Reason**: Get nav menu out of the way since it's no longer needed
**Next**: Ready to interact with the PDF icons (documenting in Step 7)

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
