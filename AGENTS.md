# AGENTS.md

Instructions for AI agents (Warp, Claude, etc.) working on this project.

## Project Overview

DartConnect Statistics Generator is a Python application that processes DartConnect league data and generates professional PDF reports. The key innovation is enhanced Quality Point (QP) calculations using URL fetching to retrieve turn-by-turn game data.

## New Season Setup Checklist

When starting a new dart league season, complete these steps:

### 1. Update `config.yaml`

Update the following fields:

```yaml
league:
  season: '2026'              # Current year
  contact_info: 'board@wssndl.com'

season:
  number: '75th'              # Increment from previous (74th → 75th)
  name: 'Spring/Summer 2026'  # Season name (Spring/Summer or Fall/Winter + year)

directories:
  data: 'data/season75'       # Update season number
  output: 'output/season75'   # Update season number
  wix_folder: 'SEASON 75 - 2026 Spring'  # Wix Media Manager folder
```

### 2. Create Season Directories

```bash
mkdir -p data/seasonNN output/seasonNN
```

Replace `NN` with the new season number.

### 3. Archive Previous Season

Move old season data and reports to their season folder:

```bash
# Move data files
mv data/*_export.csv data/seasonPREV/
mv data/*_players*.csv data/seasonPREV/

# Move reports
mkdir -p output/seasonPREV
mv output/*.pdf output/*.json output/seasonPREV/
```

### 4. Update `weekly.sh`

Update the directory variables at the top of `weekly.sh`:

```bash
DATA_DIR="data/seasonNN"
OUTPUT_DIR="output/seasonNN"
```

Also update the banner text:
```bash
echo "🎯 Season NN Weekly Update - Season Name Year"
```

### 5. Verify DartConnect Credentials

Ensure credentials are set for automated downloads:

```bash
python3 scripts/fetch_exports.py --check-creds
```

If not configured:
```bash
export DARTCONNECT_EMAIL="your.email@example.com"
export DARTCONNECT_PASSWORD="your-password"
```

### 6. Test the Setup

Run a quick test to ensure everything works:

```bash
./weekly.sh --download  # Test download only
```

### 7. Re-link Wix Icons (One-time per season)

After the first upload to a new season folder, manually re-link the PDF icons on the Wix Statistics page:
1. Go to Wix Editor → Statistics page
2. Click the Individual report icon → Link to `Current/Individual.pdf` in the new season folder
3. Click the Overall report icon → Link to `Current/Overall.pdf` in the new season folder
4. Publish the site

(Wix API cannot update icon links - this must be done manually once per season)

## Weekly Workflow

After initial setup, the weekly process is simple:

```bash
./weekly.sh              # Full workflow: download + reports + upload to Wix
./weekly.sh --reports    # Reports + upload (skip download)
./weekly.sh --download   # Download only
./weekly.sh --no-upload  # Download + reports, skip Wix upload
```

**Requirements for Wix upload:**
- `.env` file with `WIX_API_KEY` and `WIX_SITE_ID` configured
- See `scripts/wix_uploader.py --api-mode --check-creds` to verify

## Directory Structure

```
data/
  season74/           # Previous season data
  season75/           # Current season data
  archive/            # Old/backup files

output/
  season74/           # Previous season reports
  season75/           # Current season reports
```

## Season History

| Season | Name              | Directory    |
|--------|-------------------|--------------|
| 74     | Fall/Winter 2025  | season74/    |
| 75     | Spring/Summer 2026| season75/    |

---

## Core Architecture

### Three-Tier Data Processing Pipeline

1. **Data Input Layer** (`src/data_processor.py`)
   - Primary: `*_by_leg_export.csv` (includes game URLs for enhanced processing)
   - Fallback: `*_cricket_leaderboard.csv` and `*_501_leaderboard.csv`
   - Auto-detection logic in `find_data_files()` prioritizes by_leg exports

2. **URL Fetching & Caching** (`src/url_fetcher.py`)
   - Fetches turn-by-turn game data from DartConnect recap URLs
   - Smart caching system: 150-day expiry (~5 months, matches dart season)
   - Cache location: `cache/dartconnect_urls/`
   - **Critical**: Bulls data for Cricket QP, checkout bonuses for 501 QP
   - Performance: First run ~20s, subsequent runs ~1s (20x improvement)

3. **Report Generation** (`src/pdf_generator.py`)
   - Overall Report: Team standings with player details (landscape, letter size)
   - Individual Report: Player rankings and achievements (portrait, letter size)
   - Uses ReportLab for PDF generation

### Key Quality Point (QP) Calculations

**Cricket QP** (requires URL data):
- Based on marks AND bulls (singles/doubles)
- Formula: `_calculate_turn_qp(marks, bulls)` in `url_fetcher.py`
- URL data essential because CSV only has marks, not bulls

**501 QP** (enhanced with URL data):
- Base points from total score
- Bonus points for checkouts (requires URL data)
- Formula: `calculate_501_qp(total_score, checkout_score)` in `url_fetcher.py`

**Rating Formula**: `((Wins × 2) / Games Played) + (QPs / Legs Played)`

## Development Commands

### Setup
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set credentials for automated downloads (optional)
export DARTCONNECT_EMAIL="your.email@example.com"
export DARTCONNECT_PASSWORD="your-password"
```

### Running the Application

#### Complete Weekly Workflow (Recommended)
```bash
# All-in-one script
./weekly.sh

# Or with individual steps:
./weekly.sh --download  # Download only
./weekly.sh --reports   # Reports only
```

#### Manual Commands
```bash
# Auto-detect and process data files
python main_consolidated.py data/season75/

# Process specific file
python main_consolidated.py data/season75/by_leg_export.csv

# Verbose logging for debugging
python main_consolidated.py data/season75/ --verbose

# Custom output directory
python main_consolidated.py data/season75/ -o output/season75/
```

### Automated Export Downloads
```bash
# Download to current season directory
python3 scripts/fetch_exports.py --headless -o data/season75

# Download with browser visible (debugging)
python3 scripts/fetch_exports.py -o data/season75

# Assisted mode: Opens portal, waits for manual export click
python3 scripts/fetch_exports.py --assist -o data/season75

# Check credentials
python3 scripts/fetch_exports.py --check-creds
```

### Wix PDF Upload (API Mode)
```bash
# Test API connectivity
python3 scripts/test_wix_api.py

# Upload PDFs to Wix (API mode - recommended)
source .env && python3 scripts/wix_uploader.py --api-mode

# Check API credentials
python3 scripts/wix_uploader.py --api-mode --check-creds

# Dry run (show what would be uploaded)
python3 scripts/wix_uploader.py --api-mode --dry-run
```

### Cache Management
```bash
# View cache statistics
python cache_manager.py info

# Clear expired cache
python cache_manager.py clear-expired

# Clear all cache
python cache_manager.py clear-all
```

### Testing
```bash
pytest
python test_url_fetcher.py
python test_consolidated_approach.py
python test_overall_with_real_data.py
python test_individual_with_real_data.py
```

## Configuration

`config.yaml` controls:
- PDF formatting (fonts, page size, styling)
- Season information (season number, name)
- Data processing thresholds
- Statistics calculations
- Directory paths for current season
- **Note**: Week numbers are automatically calculated from match dates in CSV

## Important Implementation Details

### File Auto-Detection Priority
When processing a directory, the system searches for files in this order:
1. Most recent `*_by_leg_export.csv` (excludes archived files)
2. `*_cricket_leaderboard.csv`
3. `*_501_leaderboard.csv`

### Quality Assessment System
The application evaluates data quality after processing:
- Score 95/100: by_leg with >80% successful URL fetches
- Score 75/100: by_leg CSV-only (no URL data)
- Score 60/100: Leaderboard CSVs only

### Division and Team Structure
- Two divisions: Winston Division and Salem Division
- Teams grouped by division in Overall report
- Division headers use color coding (Green/Winston, Blue/Salem)

### Player Eligibility
- Must play 18 games to qualify for tournament
- Rookie indicators: `®` = 1st season, `®®` = 2nd season
- Eligibility status shown as "QUALIFIED" (green) or "INELIGIBLE" (red)

### Gender Inference
DartConnect often has missing gender data. The system automatically infers gender from first names:
- Name lists in `src/data_processor.py`: `COMMON_MALE_NAMES`, `COMMON_FEMALE_NAMES`, `UNISEX_NAMES`
- Check processed results (not raw CSV) to see actual missing count after inference
- **Awards depend on gender** - ensure no players are missing gender before publishing
- To verify: check `processed_results.json` or run reports with `--verbose`
- Add missing names to the appropriate list in `data_processor.py` if needed

## Critical Code Locations

### Quality Point Calculations
- Cricket QP: `src/url_fetcher.py:calculate_cricket_qp()`
- 501 QP: `src/url_fetcher.py:calculate_501_qp()`
- Per-turn QP: `src/url_fetcher.py:_calculate_turn_qp()`
- Total QP aggregation: `src/pdf_generator.py:_calculate_total_qps()`

### Data Flow Entry Points
- Main application: `main_consolidated.py`
- File detection: `main_consolidated.py:find_data_files()`
- Data processing: `src/data_processor.py:process_file()`
- URL enhancement: `src/data_processor.py:_process_dartconnect_urls()`

### Report Generation
- Overall report: `src/pdf_generator.py:generate_overall_report()`
- Individual report: `src/pdf_generator.py:generate_individual_report()`
- Team sections: `src/pdf_generator.py:_create_team_section()`
- Player rankings: `src/pdf_generator.py:_create_ratings_and_qp_register_section()`

## Dependencies

Core libraries:
- pandas: Data manipulation
- reportlab: PDF generation
- requests: HTTP requests for URL fetching
- selenium + webdriver-manager: Automated export downloads
- pyyaml: Configuration management

## Performance Considerations

- **Cache is critical**: 20x performance improvement on subsequent runs
- **URL fetching**: Network-intensive on first run, design for batch processing
- **CSV parsing**: Handles various DartConnect export formats with flexible column mapping
- **Memory**: Entire season data loaded into memory (typically <50MB)
