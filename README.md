# DartConnect Statistics Generator

A Python application that processes statistics from DartConnect league software and generates PDF reports for upload to league websites hosted on platforms like Wix.

## Overview

This tool takes DartConnect league data as input and produces two different PDF reports with various statistics and analytics that can be easily uploaded to your league's website.

## Features

- Process DartConnect league statistics
- Calculate custom derived statistics
- Generate two different PDF report formats
- Configurable report templates
- Command-line interface for easy automation

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

Basic usage:
```bash
python main.py path/to/dartconnect-data.csv
```

With custom configuration:
```bash
python main.py path/to/dartconnect-data.csv --config custom-config.yaml --output-dir reports
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
├── main.py                 # Main application entry point
├── requirements.txt        # Python dependencies
├── config.yaml            # Configuration file
├── src/                   # Source code modules
│   ├── data_processor.py  # Data processing and statistics
│   ├── pdf_generator.py   # PDF report generation
│   └── config.py          # Configuration handling
├── data/                  # Input data files
├── output/                # Generated PDF reports
├── docs/                  # Documentation
└── tests/                 # Unit tests
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests: `pytest`
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.