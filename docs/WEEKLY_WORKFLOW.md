# Weekly Workflow Guide

Complete guide for generating and publishing weekly dart league reports.

## Overview

The system provides a semi-automated workflow that:
1. ✅ **Automatically downloads** latest data from DartConnect
2. ✅ **Automatically generates** PDF reports with 100% gender accuracy
3. ✅ **Automatically uploads** PDFs to Wix (creates folders, uploads files)
4. ⚠️ **Manually re-link** icons on the Statistics page (Wix API limitation)

**Time Required:** ~5-10 minutes total (mostly automated)

---

## Quick Start

### One-Command Full Workflow

```bash
# 1. Download data, generate reports, and upload to Wix (with 2FA prompt)
source .env && python3 scripts/weekly_reports.py && python3 scripts/wix_uploader.py --api-mode --assist
```

### Step-by-Step Workflow

#### Step 1: Download Latest Data & Generate Reports (2-3 minutes)

```bash
# Load credentials
source .env

# Download latest By Leg export and generate PDFs
python3 scripts/weekly_reports.py
```

**What happens:**
- Downloads latest CSV from DartConnect (headless browser)
- Archives previous week's data
- Processes 3,900+ records with URL enhancement
- Applies gender normalization (100% coverage)
- Generates two PDFs: `Overall-MMDD_HHMMSS.pdf` and `Individual-MMDD_HHMMSS.pdf`
- **Output:** PDFs saved in `output/` directory

#### Step 2: Upload PDFs to Wix (2-3 minutes)

```bash
# Upload to Wix using API (recommended)
python3 scripts/wix_uploader.py --api-mode --assist
```

**What happens:**
- Calculates current week number from CSV data
- Creates folder: `Week {N} - {Date Range}` (e.g., "Week 14 - Oct 28-Nov 03")
- Uploads Overall and Individual PDFs to the folder
- Files are stored but **not yet linked** to icons

**Options:**
- `--api-mode`: Uses Wix REST API (faster, more reliable)
- `--assist`: Pauses for 2FA OTP entry (recommended)
- `--dry-run`: Preview what would be uploaded without making changes

#### Step 3: Manually Re-Link Icons (2-3 minutes)

⚠️ **This step is required** due to Wix API limitations (feature request pending)

1. Go to https://your-wix-site.com/dashboard
2. Navigate to **Site → Pages → Statistics page**
3. Click **Edit** on the Statistics page
4. For each icon (Overall Reports, Individual Reports):
   - Click the icon
   - Click the link/gear icon
   - Select **Document** from dropdown
   - Navigate to the newest week folder
   - Select the corresponding PDF file
   - Click **Done**
5. **Publish** the page

---

## Complete Weekly Commands

### Standard Workflow (Recommended)

```bash
# 1. Generate reports
source .env
python3 scripts/weekly_reports.py

# 2. Upload to Wix (with 2FA prompt)
python3 scripts/wix_uploader.py --api-mode --assist

# 3. Then manually re-link icons (see Step 3 above)
```

### Alternative: Manual Download

If automated download fails, manually download from DartConnect:

```bash
# 1. Manually download By_Leg_export.csv from DartConnect
# 2. Save to data/ folder
# 3. Generate reports only
python3 main_consolidated.py data/ --verbose

# 4. Upload to Wix
python3 scripts/wix_uploader.py --api-mode --assist
```

### Dry Run (Test Upload Without Changes)

```bash
# Preview what would be uploaded
python3 scripts/wix_uploader.py --api-mode --assist --dry-run
```

---

## Features & Capabilities

### 🤖 Automated Export Download
- Headless browser automation using Selenium
- Intelligent Match Log validation (aborts if errors found)
- Automatic archiving with timestamp preservation
- ~95% reliability, handles dynamic content

### 🎯 Enhanced Quality Point Calculations
- **Accurate Cricket QPs**: Uses Bulls (SB/DB) data from detailed game analysis
- **Complete 501 QPs**: Includes checkout bonuses using additive QP system
- **URL Enhancement**: 20x faster with smart caching (297 URLs processed in ~1 second)
- **Quality Score**: 95/100 with full URL enhancement

### ⚡ Gender Data Management (100% Coverage)
- **Gender Normalization**: Uses most recent gender value per player
  - Fixes inconsistent gender across games (e.g., Bryan Windham: 61 records corrected)
  - Fills missing gender when player has partial data (8 players normalized)
- **Gender Inference**: Name-based inference for missing data (30 players inferred)
  - High-confidence matches from curated name lists
  - Manual classifications for ambiguous names (Casey, Chris, Lee, etc.)
  - Conservative approach: skips unisex names
- **Placeholder Filtering**: Removes Ghost Player records (14 records filtered)
- **Result**: All 112 players have gender data across 3,935 records

### 📊 Professional PDF Reports
- **Overall Report**: League statistics with division rankings (Winston/Salem)
- **Individual Report**: Detailed team/player performance with eligibility tracking
- **Sample-Matched Format**: PDFs match official league report layouts exactly
- **Special QP Register**: Formatted with first name + last initial, text wrapping

### 🌐 Wix Upload Automation
- **API Mode**: Uses Wix REST API for reliable uploads
- **Smart Folder Management**: Creates weekly folders with proper naming
- **Duplicate Prevention**: Checks for existing files before upload
- **Week Calculation**: Automatically determines week number from CSV data
- **Bulk Operations**: Efficient upload with progress tracking

---

## Configuration

### Environment Variables (.env file)

```bash
# DartConnect Credentials
export DARTCONNECT_EMAIL="your.email@example.com"
export DARTCONNECT_PASSWORD="your-password"

# Wix API Credentials (for API mode)
export WIX_API_KEY="your-wix-api-key"
export WIX_SITE_ID="your-site-id"

# Optional: Wix Credentials (for Selenium mode - not recommended)
export WIX_EMAIL="your-wix-email"
export WIX_PASSWORD="your-wix-password"
```

### Getting Wix API Credentials

1. Go to https://manage.wix.com/account/api-keys
2. Create a new API key with **File Manager** permissions
3. Copy the API key and site ID
4. Add to `.env` file

---

## Troubleshooting

### Download Issues

**Problem:** Match Log validation errors
```
❌ DATA VALIDATION FAILED
   Match Log contains 1 error(s)
```

**Solution:**
1. Log into DartConnect at https://my.dartconnect.com
2. Navigate to Competition Organizer → Manage League → Match Log
3. Fix all errors listed
4. Re-run download: `python3 scripts/weekly_reports.py`

### Gender Issues

**Problem:** Some players missing gender

**Solution:** The system automatically handles this with 100% coverage:
- Normalization: Fills partial data (8 players)
- Inference: Name-based inference (30 players)
- Manual classifications already in code for ambiguous names

If a new player appears with missing gender and unusual name:
1. Check logs for inference skips
2. Add name to `src/data_processor.py` name lists if needed

### Upload Issues

**Problem:** 2FA required for Wix login

**Solution:** Use `--assist` flag:
```bash
python3 scripts/wix_uploader.py --api-mode --assist
```

**Problem:** API upload fails

**Solution:** Check credentials:
```bash
# Verify API key is set
echo $WIX_API_KEY

# Test API connection
python3 scripts/test_wix_api.py
```

---

## Performance Metrics

### First Run (Building Cache)
- **Download**: ~30 seconds
- **Report Generation**: ~20 seconds (297 URL fetches)
- **Upload**: ~10 seconds
- **Total**: ~60 seconds + manual re-linking (2-3 min)

### Subsequent Runs (Cache Active)
- **Download**: ~30 seconds
- **Report Generation**: ~1-2 seconds (100% cache hits)
- **Upload**: ~10 seconds
- **Total**: ~45 seconds + manual re-linking (2-3 min)

### Data Processed
- **Total Records**: 3,935 legs
- **Unique Players**: 112
- **Game Types**: 501 SIDO (1,987), Cricket (1,928), 1001 SIDO (20)
- **Quality Score**: 95/100
- **Gender Coverage**: 100% (112/112 players)

---

## File Structure

```
dartconnect-stats-generator/
├── scripts/
│   ├── weekly_reports.py        # Main workflow script
│   ├── fetch_exports.py         # Download automation
│   ├── wix_uploader.py          # Wix upload CLI
│   └── test_wix_api.py          # API connection test
├── src/
│   ├── data_processor.py        # Gender fixes + processing
│   ├── pdf_generator.py         # PDF report generation
│   ├── export_downloader.py     # Download automation logic
│   └── wix_api_uploader.py      # Wix API client
├── data/                        # CSV data files
│   └── archive/                 # Archived previous weeks
├── output/                      # Generated PDF reports
├── cache/                       # URL response cache
└── .env                         # Credentials (DO NOT COMMIT)
```

---

## Tips & Best Practices

### Weekly Routine

1. **Monday morning**: Download and generate (while drinking coffee ☕)
2. **Upload immediately**: Don't wait - files are timestamped
3. **Re-link icons**: Takes 2-3 minutes, do it right away
4. **Publish**: Make reports available to league

### Verification

After upload, verify:
```bash
# Check output folder
ls -lh output/*.pdf

# Check data was processed
python3 -c "
import pandas as pd
df = pd.read_csv('data/Fall_Winter_2025_By_Leg_export.csv')
print(f'Rows: {len(df)}, Players: {df[\"Last Name, FI\"].nunique()}')
"
```

### Cache Management

Cache improves performance 20x on subsequent runs:
```bash
# View cache stats
python3 cache_manager.py info

# Clear cache if needed (rare)
python3 cache_manager.py clear-all
```

---

## Future Improvements

### When Wix API Supports Icon Linking (Feature Request Pending)
Once Wix adds icon linking to their API:
1. Update `src/wix_api_uploader.py` to include linking logic
2. Remove manual Step 3 from workflow
3. Full automation: one command, zero manual steps! 🎉

### Potential Enhancements
- Email notification when reports are ready
- Slack/Discord bot for league announcements
- Automatic posting to social media
- Historical report archive on website

---

## Support

For issues or questions:
1. Check logs with `--verbose` flag
2. Review troubleshooting section above
3. Check `docs/` folder for detailed documentation

**Enjoy your automated workflow! 🎯📊**
