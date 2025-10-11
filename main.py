#!/usr/bin/env python3
"""
DartConnect Statistics Generator

This program processes statistics from DartConnect league software
and generates two different PDF reports for upload to the league website.
"""

import argparse
import sys
from pathlib import Path

from src.data_processor import DataProcessor
from src.pdf_generator import PDFGenerator
from src.config import Config


def main():
    """Main entry point for the application."""
    parser = argparse.ArgumentParser(
        description="Generate PDF reports from DartConnect league statistics"
    )
    parser.add_argument(
        "input_file",
        help="Path to the DartConnect data file"
    )
    parser.add_argument(
        "--config",
        default="config.yaml",
        help="Path to configuration file (default: config.yaml)"
    )
    parser.add_argument(
        "--output-dir",
        default="output",
        help="Output directory for PDF files (default: output)"
    )
    
    args = parser.parse_args()
    
    # Check if input file exists
    if not Path(args.input_file).exists():
        print(f"Error: Input file '{args.input_file}' not found.")
        sys.exit(1)
    
    try:
        # Load configuration
        config = Config(args.config)
        
        # Process the data
        processor = DataProcessor(config)
        processed_data = processor.process_file(args.input_file)
        
        # Generate PDF reports
        generator = PDFGenerator(config, args.output_dir)
        
        # Generate both PDF reports
        overall_path = generator.generate_overall_report(processed_data)
        individual_path = generator.generate_individual_report(processed_data)
        
        print(f"Successfully generated reports:")
        print(f"  Overall: {overall_path}")
        print(f"  Individual: {individual_path}")
        
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()