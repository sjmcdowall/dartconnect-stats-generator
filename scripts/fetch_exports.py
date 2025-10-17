#!/usr/bin/env python3
"""CLI tool to fetch DartConnect CSV exports.

This is the standalone export downloader tool. It can be run independently
or invoked by main_consolidated.py with the --download-first flag.

Usage (Standalone):
    python3 scripts/fetch_exports.py
    python3 scripts/fetch_exports.py --output-dir data/season74
    python3 scripts/fetch_exports.py --verbose

Usage (From main program):
    python3 main_consolidated.py --download-first

Setup:
    1. Set environment variables:
       export DARTCONNECT_EMAIL="your.email@example.com"
       export DARTCONNECT_PASSWORD="your-password"
    
    2. Run this script:
       python3 scripts/fetch_exports.py
"""

import sys
import os

# Add parent directory to path so we can import src modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.export_downloader import DartConnectExporter
import argparse
import logging


def main():
    """Main entry point for fetch_exports.py"""
    parser = argparse.ArgumentParser(
        description='Fetch DartConnect CSV exports',
        epilog=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        '--output-dir', '-o',
        type=str,
        default='data',
        help='Output directory for CSV files (default: data/)'
    )
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose logging'
    )
    parser.add_argument(
        '--headless',
        action='store_true',
        help='Run browser headless (default: false)'
    )
    parser.add_argument(
        '--check-creds',
        action='store_true',
        help='Check if credentials are properly configured and exit'
    )
    parser.add_argument(
        '--assist',
        action='store_true',
        help='Assisted mode: opens portal and waits while you click Export'
    )
    
    args = parser.parse_args()
    
    # Setup logging
    level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    logger = logging.getLogger(__name__)
    
    # Check if credentials are configured
    email = os.getenv('DARTCONNECT_EMAIL')
    password = os.getenv('DARTCONNECT_PASSWORD')
    
    if args.check_creds:
        if email and password:
            print("✅ DartConnect credentials are configured")
            print(f"   Email: {email[:3]}...{email[-8:]}")  # Show partial email for privacy
            return 0
        else:
            print("❌ DartConnect credentials are NOT configured")
            print("\nTo set credentials, run:")
            print("  export DARTCONNECT_EMAIL='your.email@example.com'")
            print("  export DARTCONNECT_PASSWORD='your-password'")
            return 1
    
    # Download exports
    try:
        logger.info("🚀 Starting DartConnect export downloader")
        
        exporter = DartConnectExporter(headless=args.headless)
        files = exporter.download_exports(args.output_dir, assist=args.assist)
        
        if files:
            print(f"\n✅ Successfully downloaded {len(files)} file(s):")
            for file_type, path in files.items():
                print(f"  • {file_type}: {path}")
            print(f"\nExports saved to: {os.path.abspath(args.output_dir)}")
        else:
            print("\n⚠️ No files were downloaded")
            return 1
        
        exporter.close()
        return 0
        
    except ValueError as e:
        print(f"\n❌ Configuration Error:")
        print(f"   {e}")
        print("\nTo fix, set your credentials:")
        print("  export DARTCONNECT_EMAIL='your.email@example.com'")
        print("  export DARTCONNECT_PASSWORD='your-password'")
        return 1
    except Exception as e:
        logger.error(f"❌ Download failed: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1


if __name__ == '__main__':
    exit(main())
