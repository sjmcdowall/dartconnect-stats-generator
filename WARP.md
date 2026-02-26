# WARP.md

This file provides guidance to WARP (warp.dev) when working with code in this repository.

## Agent startup (required)

If you are an AI agent working in this repo, do this at the start of every new session **before** proposing changes:

**Hard stop:** If you have not read `AGENTS.md`, stop and read it now before responding.

1. Read `WARP.md` and `AGENTS.md`.
2. In your first substantive response, briefly confirm you read them and summarize any constraints that affect the user’s request (1–5 bullets).
3. If the user references a prior session and you do not have the full context, ask them to paste the relevant snippet rather than guessing.

Note: `AGENTS.md` contains additional operational details (weekly workflow, season setup, and “source of truth” behaviors) that are easy to miss if you only skim this file.

## Project Overview

DartConnect Statistics Generator is a comprehensive Python application that provides **fully automated data extraction and processing** from DartConnect league software. The system features headless browser automation for downloading CSV exports, intelligent data processing with URL enhancement, and professional PDF report generation.

**Key Capabilities:**
- 🤖 **Automated CSV Downloads**: Headless browser automation with intelligent navigation
- 🎯 **Enhanced Quality Points**: Accurate Cricket/501 QP calculations with Bulls data and checkout bonuses  
- ⚡ **High-Performance Caching**: 20x faster processing with smart URL caching
- 📊 **Professional Reports**: League-standard PDF reports with comprehensive analytics
- 🗂️ **Smart File Management**: Automatic archiving with timestamp preservation

## Development Commands

### Setup and Installation
```bash
# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# For automated downloads, also install:
pip install selenium webdriver-manager

# Set DartConnect credentials for automation
export DARTCONNECT_EMAIL="your.email@example.com" 
export DARTCONNECT_PASSWORD="your-password"
```

### Running the Application

#### 🤖 **Fully Automated Workflow (Recommended)**
```bash
# Complete automation: Download latest data + Generate reports  
python3 scripts/fetch_exports.py --headless && python3 main_consolidated.py data/

# Time: ~3-4 minutes total, Output: Latest PDF reports with 95/100 quality
```

#### 📥 **Data Download Only**
```bash
# Download latest By Leg export (headless)
python3 scripts/fetch_exports.py --headless

# Download with browser visible (debugging)
python3 scripts/fetch_exports.py

# Download with verbose logging
python3 scripts/fetch_exports.py --headless --verbose
```

#### 📊 **Report Generation Only**
```bash
# Auto-detect newest data and generate reports (enhanced processing)
python3 main_consolidated.py data/ --verbose

# Process specific file
python3 main_consolidated.py data/Fall_Winter_2025_By_Leg_export.csv

# Legacy processing (basic)
python3 main.py data/sample_data.csv --config custom-config.yaml --output-dir reports
```

### Development Tasks
```bash
# Run code formatting
black src/ main.py main_consolidated.py scripts/

# Run linting  
flake8 src/ main.py main_consolidated.py scripts/

# Run tests
pytest
pytest --cov=src  # With coverage

# Test automation system
python3 test_consolidated_approach.py
python3 enhanced_integration_example.py

# Cache management
python3 cache_manager.py info       # View cache status
python3 cache_manager.py clear-all  # Clear all cache

# Debug automation issues
python3 scripts/fetch_exports.py --headless --verbose > debug.log 2>&1
```

## Code Architecture

### Core Components

**🤖 Export Automation System (`scripts/fetch_exports.py`, `src/export_downloader.py`)**
- Headless browser automation using Selenium WebDriver
- Intelligent navigation through DartConnect's complex web interface
- Robust error handling with JavaScript-based clicking and element waiting
- Smart file archiving with timestamp preservation
- **Success Rate**: ~95% reliable downloads, handles dynamic content loading

**⚡ Enhanced Processing Engine (`main_consolidated.py`)**
- **Next-generation workflow** with intelligent data detection
- **High-Performance URL Enhancement**: 20x faster processing with smart caching
- **Advanced Quality Points**: Accurate Cricket/501 calculations with Bulls data
- **Checkout Bonus System**: Proper 501 finish recognition and point allocation
- **Smart File Management**: Auto-detects newest data, ignores archived files

**🏗️ Legacy Core (`main.py` + `src/` modules)**

**Main Entry Point (`main.py`)**
- CLI interface using argparse for basic processing
- Coordinates traditional data processing and PDF generation
- Basic error reporting and output management

**Data Processing Pipeline (`src/data_processor.py`)**
- Flexible column mapping for different DartConnect export formats
- Handles CSV and Excel input files
- Calculates statistics: player rankings, percentiles, trends, time-based analytics
- Implements rolling averages and performance trend analysis
- Data cleaning and validation with configurable thresholds

**PDF Generation (`src/pdf_generator.py`)**
- Uses ReportLab for PDF creation
- Generates two distinct report types:
  - Report 1: League Statistics Report (overall league summary, rankings, percentiles)
  - Report 2: Player Performance Report (individual stats, trends, detailed analytics)
- Configurable styling, fonts, and layout options
- Modular content generation with reusable table styles

**Configuration Management (`src/config.py`)**
- YAML-based configuration with sensible defaults
- Hierarchical config structure: data_processing, pdf_reports, statistics
- Dot-notation access pattern for nested configuration values
- Automatic merging of user config with defaults

### Data Flow Architecture

1. **Input Processing**: CSV/Excel files → DataFrame with column mapping
2. **Data Cleaning**: Missing value handling, type conversion, date parsing
3. **Statistics Calculation**: Player stats, league summaries, time-based analytics
4. **Derived Metrics**: Rankings, trends, percentiles with configurable thresholds
5. **PDF Generation**: Two separate reports with different focus areas

### Key Design Patterns

**Flexible Column Mapping**: The data processor automatically maps various DartConnect column naming conventions to standardized internal names, making it resilient to export format changes.

**Configuration-Driven Behavior**: All major functionality (statistics calculations, PDF formatting, data processing thresholds) is controlled via YAML configuration, enabling easy customization without code changes.

**Modular PDF Generation**: PDF content is generated through separate methods for each report section, enabling easy addition of new report types or modification of existing layouts.

## Configuration Structure

The `config.yaml` file controls:
- **data_processing**: Date formats, decimal precision, minimum games thresholds
- **pdf_reports**: Separate configurations for each report type (titles, styling, chart inclusion)
- **statistics**: Which calculations to perform, rolling window sizes for trends
- **league**: League-specific metadata for report headers

## File Structure Insights

**Input Data**: Expects DartConnect exports with columns for player_name, game_date, score, average, checkout_percentage, games_played. Column names are automatically mapped.

**Output Structure**: PDF files are timestamped and saved to configurable output directory. Generated filenames follow pattern: `{report_type}_{YYYYMMDD_HHMMSS}.pdf`

**Sample Data**: `data/sample_data.csv` provides example data format for testing and development.

## Development Notes

**Error Handling**: The application includes comprehensive error handling for file I/O, data parsing, and PDF generation with informative error messages.

**Statistics Engine**: Implements sophisticated analytics including rolling averages, percentile calculations, and trend analysis. The minimum games threshold prevents statistical noise from occasional players.

**PDF Styling**: Uses ReportLab's advanced features for professional report formatting with custom styles, colors, and table layouts.

**Extensibility**: The modular architecture makes it straightforward to add new statistics calculations, report sections, or input/output formats.