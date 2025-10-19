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
**Icon Purpose**: Each icon links to corresponding PDF file on published site
**Nav Menu State**: Left nav menu stays open (doesn't auto-close)
**Action**: Click somewhere on the page to close/dismiss the nav menu
**Reason**: Get nav menu out of the way since it's no longer needed
**Next**: Ready to interact with the PDF icons (documenting in Step 7)

### Step 7: Click Icon to Access Options Menu
**Mode**: Editor mode (site editor)
**Action**: Click on one of the icons (e.g., "Individual")
**Result**: Small mini-option menu appears near the icon
**Options Shown**: Various options including "Linked"
**Target Option**: "Linked" (has a URL link icon next to it)
**Note**: Despite the link icon, this is NOT a URL link - it's for linking to files/content
**Next**: Click "Linked" option (documenting in Step 8)

### Step 8: Link Modal Dialog Opens
**Modal Title**: "What do you want to link to?"
**Layout**: Split view - link type options on left, file selection on right

**Left Side - Link Type Options (Radio Buttons)**:
- None
- Page
- Web address
- Section or anchor
- Top/bottom of page
- **Document** ← (THIS ONE - selected)
- Email
- Phone number
- Lightbox

**Right Side - File Selection**:
- Title: "What doc are you linking to?"
- Button: "Choose File" (blue button)
- Currently selected file shown: "Individual-1018_094513.pdf" with green checkmark
- Option link: "Show this PDF in search results"

**Bottom Buttons**:
- "Cancel" (left, gray)
- "Done" (right, blue)

**Action**: Select "Document" radio button (if not already selected)
**Next**: Click "Choose File" button (documenting in Step 9)

### Step 9: Choose a Doc - Media Library
**Dialog Title**: "Choose a Doc"
**View**: Wix media library / file manager interface

**Top Section**:
- Blue button: "+ Upload Media" (top left - KEY BUTTON for uploading)
- Search bar: "Search for business, fashion, fitness & more..."
- Tab: "Site Files" (active)
- View icons: folder view, filter, list view, grid view

**Left Sidebar - MANAGE**:
- Site Files (selected)
- My Boards
- Trash

**Left Sidebar - EXPLORE**:
- AI Image Creator

**Main Content Area**:
- Shows folders organized by season:
  - "SEASON 74 - 2025 Fall"
  - "SEASON 73 - 2025 Spring"
  - "SEASON 72 - 2024 Fall"
  - "SEASON 71 - 2024 Spring"

**Right Panel - Site Files**:
- Actions: "Create New Folder"
- Information: "Organize site files and folders added by you and other site collaborators."

**Bottom**:
- Storage: "368 MB used out of 3.0 GB"
- Links: "Manage Storage" | "Upgrade"
- Button: "Add to Page" (grayed out - bottom right)

**Next**: Navigate to current season folder (documenting in Step 10)

**Important Note - Weekly Workflow**:
This documentation focuses on the WEEKLY UPDATE process (most common use case for automation).
Assumes season folder already exists (e.g., "SEASON 74 - 2025 Fall").
Start-of-season setup can be documented separately if needed.

### Step 10: Navigate to Current Season Folder
**Action**: Click on current season folder (e.g., "SEASON 74 - 2025 Fall")
**Folder Structure**:
- Season folders contain weekly sub-folders
- Each week gets its own folder with PDFs
**Next**: View contents of season folder (documenting in Step 11)

### Step 11: Inside Season Folder - View Weekly Folders
**Breadcrumb**: Site Files > SEASON 74 - 2025 Fall
**Contents Shown**:
- Weekly folders: "Week-08", "Week-07" (numbered folders for each week)
- Loose PDF file: "Individual-00.pdf" (file directly in season folder)

**Naming Convention**: Week folders appear to be named "Week-##" format

**Right Panel - Actions**:
- "Create New Folder" button available

**Weekly Workflow**: For each week, create a new folder (e.g., "Week-09" for week 9)
**Next**: Create new weekly folder (documenting in Step 12)

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
