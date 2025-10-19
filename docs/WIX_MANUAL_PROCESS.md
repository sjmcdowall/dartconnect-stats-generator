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

### Step 12: Create New Weekly Folder
**Action**: Click "Create New Folder" button
**Button Location**: Right panel under "Actions"
**Button Appearance**: Folder icon with + symbol
**Tooltip**: "Create New Folder"
**Result**: Prompts for folder name

**Step 12B - Name the Folder**:
**Process**: Click "Create New Folder" adds new folder with text input focused
**Action**: Type folder name "Week-XX" where XX is the current week number (e.g., "Week-09")
**Week Number Source**: Based on current week in the season (see WEEK_NUMBER_LOGIC.md)
**Confirmation**: Press Enter to save folder name
**Next**: Double-click the newly created folder to open it (documenting in Step 13)

### Step 13: Inside Empty Weekly Folder - Upload Area
**Breadcrumb**: Site Files > SEASON 74 - ... > Week-09
**View**: Empty folder upload interface

**Main Content Area**:
- Large dashed border rectangle (drag-and-drop zone)
- Icon: Folder with document illustration
- Heading: "Start adding your files"
- Text: "Drag and drop files or upload from your computer."
- Link/Button: "+ Upload Media" (blue text, centered)

**Upload Options**:
1. Drag and drop PDF files into the dashed area
2. Click "+ Upload Media" to browse for files

**Next**: Click "+ Upload Media" to upload PDFs (documenting in Step 14)

### Step 14: Upload Media Dialog Opens
**Action**: Click "+ Upload Media" button
**Result**: "Upload Media" modal dialog appears

**Dialog Layout**:
- Title: "Upload Media"
- Left sidebar with upload source icons:
  - Computer (monitor icon) ← DEFAULT/TARGET
  - Wix
  - Google Drive
  - Facebook
  - Instagram
  - Dropbox
  - Other services...
  - Link/URL
  - Vimeo

**Main Area**:
- Large dashed border (drag-and-drop zone)
- Text: "Drag & drop files here"
- "or"
- Blue button: "Upload from Computer"
- Bottom link: "Want to see which file types are supported? Read more"

**Next**: Click "Upload from Computer" button (documenting in Step 15)

### Step 15: Select PDFs from Computer
**Action**: Click "Upload from Computer" button
**Result**: Opens computer's file browser dialog

**Navigation**:
- Browse to project output folder: `output/`
- Contains generated PDFs with timestamp names (e.g., Individual-1018_094513.pdf, Overall-1018_094512.pdf)

**File Selection**:
- Select BOTH reports: Individual AND Overall
- Can select multiple files at once (Cmd+Click or Ctrl+Click)
- Reason: Upload both together to avoid repeating the process

**PDF Files to Upload**:
1. Individual report (e.g., Individual-1018_094513.pdf)
2. Overall report (e.g., Overall-1018_094512.pdf)

**Next**: Files upload to Week-XX folder (documenting upload progress in Step 16)

### Step 16: Upload Complete - Files in Week-09 Folder
**View**: Back in Week-09 folder view with uploaded files
**Breadcrumb**: Site Files > SEASON 74 - ... > Week-09

**Uploaded Files Displayed**:
- Overall-1018_205119.pdf (27KB) - with PDF icon
- Individual-1018_205120.pdf (6KB) - with PDF icon
- Both files have bookmark and menu icons (••• three dots)

**Upload Completion Notification** (bottom left):
- Dark notification panel: "2 Uploads Completed"
- Shows both files with checkmarks:
  - Individual-1018_205120.pdf (6KB) ✓
  - Overall-1018_205119.pdf (27KB) ✓

**Right Panel**:
- Shows "Overall-10..." (selected file preview)
- Actions, Tags, File Info sections

**Bottom Right**:
- "Add to Page" button (grayed out)

**Important**: Files are now in Week-09 folder. Still in the linking workflow!
**Next**: Select the PDF for the icon being linked (documenting in Step 17)

### Step 17: Select PDF and Link to Icon
**Context**: Still in "Choose a Doc" dialog from Step 7 (clicked Individual icon → Linked)
**Current View**: Week-09 folder with both uploaded PDFs

**Action**: Click on the Individual PDF to select it
- PDF becomes highlighted/selected with blue border
- "Add to Page" button (bottom right) becomes active/clickable

**Next Step**: Click "Add to Page" button (documenting in Step 18)

### Step 18: Add to Page - Return to Link Modal
**Action**: Click "Add to Page" button
**Result**: Returns to the "What do you want to link to?" modal (from Step 8)

**Modal State**:
- "Document" radio button still selected
- Right side now shows selected PDF: "Individual-1018_205120.pdf" with green checkmark
- Bottom right: "Done" button (blue, active)

**Action**: Click "Done" button
**Result**: Completes the linking process for Individual icon
**Next**: Icon is now linked to the Individual PDF (documenting completion in Step 19)

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
