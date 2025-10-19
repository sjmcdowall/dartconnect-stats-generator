# Development Checkpoint Strategy

**Purpose**: Prevent loss of work due to errors or context resets

## Checkpoint Frequency

### Code Checkpoints (Git Commits)
- **Every 10-15 minutes** of active development
- **After each functional unit** (function, class method, script section)
- **Before risky operations** (major refactoring, API integrations)
- **After successful tests** (even if incomplete)
- **Use WIP commits**: It's okay to commit work-in-progress with `WIP:` prefix

### Progress Documentation
- Update this file after each checkpoint with:
  - What was just completed
  - What's next
  - Any blockers or issues
  - Current thinking/decisions

## Commit Message Format

```
WIP: [component] brief description

- Bullet point of what's working
- What's not working yet
- Next step planned
```

## Current Session Checkpoints

### Checkpoint 1: 2025-10-19 (Initial)
**Status**: Starting Wix PDF upload feature
**Branch**: feature/wix-pdf-upload
**Completed**:
- Checkpoint strategy established
- CHECKPOINTS.md created

**Next Steps**:
- Understand previous Wix upload progress
- Resume implementation

**Notes**:
- Previous session lost due to image size error
- Need to be more defensive with large files

### Checkpoint 2: 2025-10-19 (Manual Process Template)
**Status**: Documented context from previous session
**Completed**:
- Created docs/WIX_MANUAL_PROCESS.md (text-only, no images)
- Established approach: Selenium automation (like fetch_exports.py)
- Confirmed: Wix API approach failed (404s on documentation)

**Next Steps**:
- Collect manual upload steps from user (text descriptions only)
- Build Selenium script incrementally with frequent commits

**Context from Previous Session**:
- Was documenting manual Wix process step-by-step (~2/3 complete)
- Image size error stopped progress
- Goal: Automate PDF upload to Wix website after generation

### Checkpoint 3: 2025-10-19 (Manual Process Steps 1-7 Complete)
**Status**: Documented manual Wix upload process through Step 7
**Completed Steps**:
- Step 1: Navigate to wix.com
- Step 2A-E: Complete login flow (dynamic form, OTP, dashboard)
- Step 3: Navigate to Edit Site
- Step 4: Click Pages & Menus
- Step 5: Select STATISTICS page
- Step 6: View 3 icons (Individual, schedule, Overall)
- Step 7: Click icon, access "Linked" option

**Current Step**: Step 8 - Modal dialog for linking PDFs
**Next**: Document modal dialog and upload process
**Note**: About to view screenshot of modal dialog

### Checkpoint 4: 2025-10-19 (Step 8 Complete - Modal Dialog)
**Status**: Step 8 fully documented with screenshot
**Completed**:
- Step 8: Modal dialog "What do you want to link to?" documented
- Radio button options identified (Document selected)
- "Choose File" button identified
- Screenshot viewed successfully (small size, no issues)

**Current Step**: Step 9 - File picker/upload dialog
**Next**: About to view screenshot of file picker (near size limit - being cautious)
**Safety**: All progress saved before viewing potentially large image

### Checkpoint 5: 2025-10-19 (Week Number Logic Reviewed)
**Status**: Reviewed week calculation logic, Steps 9-12 documented
**Completed**:
- Steps 9-12: Media library, season folder, weekly folder creation
- Reviewed week number calculation in pdf_generator.py
- Created WEEK_NUMBER_LOGIC.md documentation
- Week formula: (days_diff // 7) + 1, first match = Week 1
- PDF filenames: Individual-MMDD_HHMMSS.pdf (timestamp, not week #)
- Week # appears in PDF headers: "74th Season - Fall/Winter 2025 - Week X"

**Current Step**: Step 13 - Upload PDFs to weekly folder
**Next**: Document PDF upload process and linking to page icons
**Key Questions Remaining**:
- Do you click into the Week-XX folder after creating it?
- What PDFs get uploaded (Individual, Overall, both)?
- Do you upload AND separately link to page icons?

### Checkpoint 6: 2025-10-19 (Manual Process COMPLETE!) ✅
**Status**: Full manual workflow documented (Steps 1-20)
**Completed**:
- All 20 steps documented with screenshots
- Complete workflow from login to publish
- Key insights captured:
  - Dynamic login form (email first, then password)
  - 2FA OTP required (needs assisted mode)
  - Two-step upload process (Upload Media → Upload from Computer)
  - Upload both PDFs, then link each icon separately
  - Publish button to make changes live
- Created automation considerations section
- Identified Selenium selector requirements

**Documents Created**:
- WIX_MANUAL_PROCESS.md (complete manual workflow)
- WEEK_NUMBER_LOGIC.md (week calculation for folder naming)
- CHECKPOINTS.md (this file, progress tracking)

**Next Steps**:
- Create wix_uploader.py script skeleton
- Implement Selenium automation with assisted mode
- Test and validate full workflow
