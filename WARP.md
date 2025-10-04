# WARP.md

This file provides guidance to WARP (warp.dev) when working with code in this repository.

## Project Overview

DartConnect Statistics Generator is a Python application that processes statistics from DartConnect league software and generates two different PDF reports for upload to league websites. The application takes CSV/Excel data files as input and produces formatted PDF reports with statistics, rankings, and analytics.

## Development Commands

### Setup and Installation
```bash
# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Running the Application
```bash
# Basic usage with sample data
python3 main.py data/sample_data.csv

# With custom configuration and output directory
python3 main.py path/to/data.csv --config custom-config.yaml --output-dir reports

# Display help
python3 main.py --help
```

### Development Tasks
```bash
# Run code formatting
black src/ main.py

# Run linting
flake8 src/ main.py

# Run tests (when implemented)
pytest

# Run tests with coverage (when implemented)
pytest --cov=src
```

## Code Architecture

### Core Components

**Main Entry Point (`main.py`)**
- CLI interface using argparse
- Coordinates data processing and PDF generation
- Handles error reporting and output management

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