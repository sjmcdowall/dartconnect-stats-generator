# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

DartConnect Statistics Generator is a Python application that processes DartConnect league data and generates professional PDF reports. The key innovation is enhanced Quality Point (QP) calculations using URL fetching to retrieve turn-by-turn game data.

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
```bash
# Auto-detect and process data files
python main_consolidated.py data/

# Process specific file
python main_consolidated.py data/season74/by_leg_export.csv

# Verbose logging for debugging
python main_consolidated.py data/ --verbose

# Custom output directory
python main_consolidated.py data/ --output-dir reports/
```

### Automated Export Downloads
```bash
# Fully automated workflow (download + process)
python3 scripts/fetch_exports.py --headless && python3 main_consolidated.py data/

# Download only (headless)
python3 scripts/fetch_exports.py --headless

# Download with browser visible (debugging)
python3 scripts/fetch_exports.py

# Assisted mode: Opens portal, waits for manual export click
python3 scripts/fetch_exports.py --assist

# Check credentials
python3 scripts/fetch_exports.py --check-creds
```

### Cache Management
```bash
# View cache statistics
python cache_manager.py info

# Clear expired cache (automatic, but can run manually)
python cache_manager.py clear-expired

# Clear all cache
python cache_manager.py clear-all
```

### Testing
```bash
# Run test suite
pytest

# Test specific components
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

### Export Automation (`src/export_downloader.py`)
Uses Selenium WebDriver to:
1. Log into DartConnect using environment credentials
2. Navigate to league portal via Competition Organizer
3. Click Export button and download by_leg CSV
4. Archive previous exports with timestamps
5. Handle common failure modes with intelligent retries

## Common Workflows

### Weekly Report Generation
```bash
# First run of season (builds cache)
python main_consolidated.py data/season74/by_leg_export.csv
# Expected: ~20-30 seconds

# Weekly updates (uses cache)
python main_consolidated.py data/season74/by_leg_export.csv
# Expected: ~1-2 seconds (20x faster)
```

### Debugging Data Processing
```bash
# Enable verbose logging
python main_consolidated.py data/ --verbose

# Examine enhanced integration
python enhanced_integration_example.py

# Check specific URL fetching
python test_url_fetcher.py
```

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
