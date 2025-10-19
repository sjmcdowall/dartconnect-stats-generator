# DartConnect Statistics Generator

A Python application that processes statistics from DartConnect league software and generates comprehensive PDF reports with enhanced Quality Point calculations for league administration.

## Overview

This tool primarily uses DartConnect's "By Leg" export data with URL processing to provide accurate statistics and Quality Point calculations. It automatically fetches detailed game data from DartConnect servers to enhance Cricket QP calculations with Bulls data and 501 QPs with checkout bonuses.

## Key Features

### 🤖 **Fully Automated Data Download** ✨ **NEW!**
- **Headless browser automation** for DartConnect CSV exports
- **Complete login and navigation** with intelligent element detection
- **Smart file archiving** with timestamp preservation
- **Integrated workflow**: Download → Process → Generate Reports

### 🎯 **Enhanced Quality Point Calculations**
- **Accurate Cricket QPs**: Uses Bulls (SB/DB) data from detailed game analysis
- **Complete 501 QPs**: Includes checkout bonuses using additive QP system
- **Official League Formulas**: Implements standard QP calculation rules

### 🔗 **Intelligent Data Processing**
- **Primary**: by_leg_export.csv + URL fetching (enhanced accuracy)
- **Fallback**: by_leg_export.csv only (CSV-based processing)
- **Emergency**: Leaderboard CSVs (if by_leg unavailable)

### ⚡ **High-Performance Caching**
- **Smart URL Caching**: 20x faster on subsequent runs
- **Season-Optimized**: 5-month cache expiry matches dart seasons
- **Automatic Management**: Self-cleaning expired cache
- **Offline Capability**: Process reports without internet for cached data

### 📊 **Professional PDF Reports**
- **Overall Report**: League statistics with division rankings (Winston/Salem)
- **Individual Report**: Detailed team/player performance with eligibility tracking
- **Sample-Matched Format**: PDFs match official league report layouts exactly
- **Comprehensive Analytics**: Game-by-game tracking, trends, and QP distributions
- **Configurable Templates**: Customizable report layouts and styling

## Installation

1. Clone this repository:
```bash
git clone <repository-url>
cd dartconnect-stats-generator
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. **Setup for Automated Downloads (Optional)**:
```bash
# Set your DartConnect credentials
export DARTCONNECT_EMAIL="your.email@example.com"
export DARTCONNECT_PASSWORD="your-password"

# Install automation dependencies
pip install selenium webdriver-manager
```

## Usage

### 🤖 Fully Automated Workflow (NEW!)
```bash
# Complete automation: Download latest data + Generate reports
python3 scripts/fetch_exports.py --headless && python3 main_consolidated.py data/

# Time: ~3-4 minutes total (download + processing)
# Output: Latest PDF reports with 95/100 quality score
```

### Manual Download Options
```bash
# Download only (headless)
python3 scripts/fetch_exports.py --headless

# Download with browser window (for debugging)
python3 scripts/fetch_exports.py

# Download with verbose logging
python3 scripts/fetch_exports.py --headless --verbose
```

### Quick Start (Traditional)
```bash
# Auto-detect DartConnect files in data directory
python main_consolidated.py data/season74/

# Process specific by_leg export file (most common)
python main_consolidated.py data/season74/by_leg_export.csv

# First run: ~20 seconds (builds cache)
# Subsequent runs: ~1 second (uses cache)
```

### Advanced Usage
```bash
# Custom configuration and output directory
python main_consolidated.py data/ --config custom.yaml --output-dir reports/

# Verbose logging for troubleshooting
python main_consolidated.py data/ --verbose

# Test the enhanced URL processing
python test_consolidated_approach.py
```

### Data Sources (Priority Order)
1. **by_leg_export.csv** (Preferred) - Enables enhanced QP calculations
2. **cricket_leaderboard.csv** (Fallback) - Basic Cricket statistics
3. **501_leaderboard.csv** (Fallback) - Basic 501 statistics

### Cache Management
```bash
# View cache information and statistics
python cache_manager.py info

# Clear expired cache files (automatic, but can run manually)
python cache_manager.py clear-expired

# Clear all cache files (use with caution!)
python cache_manager.py clear-all
```

### Enhanced Processing Demo
```bash
# See enhanced processing with sample URLs
python enhanced_integration_example.py
```

## Weekly Workflow (Typical Usage)

### First Run of the Season
```bash
# Download your by_leg_export.csv from DartConnect
# Place in data/season74/ (or your current season folder) or specify the path directly
python main_consolidated.py data/season74/by_leg_export.csv

# Expected: ~20-30 seconds (builds cache for all historical matches)
# Generates: Overall-MMDD_HHMMSS.pdf + Individual-MMDD_HHMMSS.pdf
```

### Weekly Updates
```bash
# Same command with updated export file
python main_consolidated.py data/season74/by_leg_export.csv

# Expected: ~1-2 seconds (uses cache, only fetches new games)
# Performance improvement: 20x faster!
```

### Cache Status Check
```bash
# Monitor your cache performance
python cache_manager.py info

# Example output:
# 📁 Total Files: 173
# 💾 Total Size: 8.12 MB  
# ⏰ Cache Expiry: 150 days (~5.0 months)
# 💾 Cache Performance: 100.0% hit rate
```

## Performance Benefits

| Scenario | Time | Cache Status | Network Calls |
|----------|------|--------------|---------------|
| First Run | ~20s | Building | 173 URLs |
| Week 2+ | ~1s | 100% Hits | 0 URLs |
| New Games Only | ~2s | Mixed | ~5-10 URLs |
| Season End | ~1s | Expired → Fresh | 0 → All URLs |

## Configuration

The application uses a YAML configuration file (`config.yaml` by default) to customize:
- Report formatting and styling
- Statistics calculations
- PDF layout and templates
- Data processing options
- Cache settings (expiry, location)

## Project Structure

```
dartconnect-stats-generator/
├── main_consolidated.py           # Enhanced main application (recommended)
├── cache_manager.py              # Cache management utility
├── main.py                        # Original main application  
├── enhanced_integration_example.py # URL processing demonstration
├── test_consolidated_approach.py  # Validation testing
├── requirements.txt               # Python dependencies
├── config.yaml                   # Configuration file
├── src/                          # Source code modules
│   ├── data_processor.py         # Enhanced data processing with URL fetching
│   ├── url_fetcher.py            # DartConnect URL processing with caching
│   ├── pdf_generator.py          # PDF report generation
│   └── config.py                 # Configuration handling
├── cache/                        # URL response cache (auto-created)
│   └── dartconnect_urls/         # Cached game data (JSON files)
├── data/                         # Input data files
│   ├── by_leg_export.csv         # Preferred: DartConnect by-leg export
│   ├── cricket_leaderboard.csv   # Fallback: Cricket statistics
│   └── 501_leaderboard.csv      # Fallback: 501 statistics
├── output/                       # Generated PDF reports and JSON data
├── docs/                         # Documentation
│   ├── URL_INTEGRATION_GUIDE.md  # URL processing guide
│   ├── CACHE_OPTIMIZATION.md     # Cache system documentation
│   └── samples/                  # Sample data files
├── tests/                        # Unit tests
└── docs/samples/
    ├── Individual-14.pdf         # Sample individual report format
    ├── Overall-14.pdf           # Sample overall report format
    └── dartconnect_exports/     # Sample data files
        ├── Fall_Winter_2025_By_Leg_export.csv
        ├── WinSSNDL_Fall_Winter_2025_all_01_leaderboard.csv
        └── WinSSNDL_Fall_Winter_2025_all_cricket_leaderboard.csv
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests: `pytest`
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.