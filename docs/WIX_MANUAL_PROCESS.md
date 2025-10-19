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
<!-- User will provide steps here -->

### Step 2: Navigation
<!-- User will provide steps here -->

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
