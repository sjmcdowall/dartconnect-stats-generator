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
