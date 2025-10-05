# DartConnect Statistics Generator

A Python application that processes statistics from DartConnect league software and generates comprehensive PDF reports with enhanced Quality Point calculations for league administration.

## Overview

This tool primarily uses DartConnect's "By Leg" export data with URL processing to provide accurate statistics and Quality Point calculations. It automatically fetches detailed game data from DartConnect servers to enhance Cricket QP calculations with Bulls data and 501 QPs with checkout bonuses.

## Key Features

### 🎯 **Enhanced Quality Point Calculations**
- **Accurate Cricket QPs**: Uses Bulls (SB/DB) data from detailed game analysis
- **Complete 501 QPs**: Includes checkout bonuses using additive QP system
- **Official League Formulas**: Implements standard QP calculation rules

### 🔗 **Intelligent Data Processing**
- **Primary**: by_leg_export.csv + URL fetching (enhanced accuracy)
- **Fallback**: by_leg_export.csv only (CSV-based processing)
- **Emergency**: Leaderboard CSVs (if by_leg unavailable)

### 📊 **Comprehensive Analytics**
- Game-by-game performance tracking
- Player improvement trends
- League-wide QP distribution analysis
- Turn-by-turn statistics for Cricket games
- Configurable report templates

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

## Usage

### Quick Start (Recommended)
```bash
# Auto-detect DartConnect files in data directory
python main_consolidated.py data/

# Process specific by_leg export file
python main_consolidated.py data/by_leg_export.csv
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

### Enhanced Processing Demo
```bash
# See enhanced processing with sample URLs
python enhanced_integration_example.py
```

## Configuration

The application uses a YAML configuration file (`config.yaml` by default) to customize:
- Report formatting and styling
- Statistics calculations
- PDF layout and templates
- Data processing options

## Project Structure

```
dartconnect-stats-generator/
├── main_consolidated.py           # Enhanced main application (recommended)
├── main.py                        # Original main application  
├── enhanced_integration_example.py # URL processing demonstration
├── test_consolidated_approach.py  # Validation testing
├── requirements.txt               # Python dependencies
├── config.yaml                   # Configuration file
├── src/                          # Source code modules
│   ├── data_processor.py         # Enhanced data processing with URL fetching
│   ├── url_fetcher.py            # DartConnect URL processing
│   ├── pdf_generator.py          # PDF report generation
│   └── config.py                 # Configuration handling
├── data/                         # Input data files
│   ├── by_leg_export.csv         # Preferred: DartConnect by-leg export
│   ├── cricket_leaderboard.csv   # Fallback: Cricket statistics
│   └── 501_leaderboard.csv      # Fallback: 501 statistics
├── output/                       # Generated PDF reports and JSON data
├── docs/                         # Documentation
│   ├── URL_INTEGRATION_GUIDE.md  # URL processing guide
│   └── samples/                  # Sample data files
└── tests/                        # Unit tests
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests: `pytest`
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.