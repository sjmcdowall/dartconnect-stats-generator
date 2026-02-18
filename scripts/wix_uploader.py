#!/usr/bin/env python3
"""CLI tool to upload PDFs to Wix website.

Automates the process of uploading Individual and Overall PDF reports to the
Wix website STATISTICS page, including creating weekly folders and linking icons.

Usage:
    # Upload latest PDFs from output/ folder
    python3 scripts/wix_uploader.py

    # Specify different PDF folder
    python3 scripts/wix_uploader.py --pdf-dir output/

    # Assisted mode (manual 2FA entry)
    python3 scripts/wix_uploader.py --assist

    # Run headless (requires saved session)
    python3 scripts/wix_uploader.py --headless

    # Verbose logging
    python3 scripts/wix_uploader.py --verbose

Setup:
    1. Set environment variables:
       export WIX_EMAIL="your.email@example.com"
       export WIX_PASSWORD="your-password"
       # Note: 2FA OTP must be entered manually (--assist mode)

    2. Run this script:
       python3 scripts/wix_uploader.py --assist

Workflow:
    1. Login to Wix (email, password, manual 2FA)
    2. Navigate to Edit Site → STATISTICS page
    3. Create Week-XX folder in SEASON folder
    4. Upload Individual and Overall PDFs
    5. Link Individual icon to Individual PDF
    6. Link Overall icon to Overall PDF
    7. Publish changes

Requirements:
    - PDFs must exist in output/ folder (Individual-*.pdf, Overall-*.pdf)
    - Week number calculated from PDF data
    - Wix credentials in environment variables
    - Manual 2FA OTP entry (--assist mode recommended)
"""

import sys
import os

# Add parent directory to path so we can import src modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import argparse
import logging
from pathlib import Path
from datetime import datetime
import pandas as pd
import yaml


def calculate_week_number_from_csv(csv_path: Path) -> int:
    """
    Calculate week number from CSV data.

    Uses the same logic as PDF generator:
    - Find earliest and latest match dates
    - Calculate weeks between them: (days_diff // 7) + 1

    Args:
        csv_path: Path to CSV file

    Returns:
        Week number (1-based)
    """
    try:
        # Read CSV - the Date column should be column 30 (index 29)
        # Read with minimal parsing for speed
        df = pd.read_csv(csv_path, usecols=['Date'], parse_dates=['Date'])

        if len(df) == 0 or 'Date' not in df.columns:
            return 1

        # Get unique dates
        unique_dates = df['Date'].dt.date.unique()

        if len(unique_dates) > 0:
            # Sort dates to get first and last
            sorted_dates = sorted(unique_dates)
            first_match_date = sorted_dates[0]  # Season start (Week 1)
            most_recent_date = sorted_dates[-1]  # Current week

            # Calculate the number of weeks between first and last match
            days_diff = (most_recent_date - first_match_date).days
            week_number = (days_diff // 7) + 1  # +1 because first week is Week 1, not Week 0

            return max(1, week_number)  # At least week 1

        return 1  # Default to week 1

    except Exception as e:
        # If we can't read the CSV, default to week 1
        return 1


def main():
    """Main entry point for wix_uploader.py"""
    parser = argparse.ArgumentParser(
        description='Upload PDF reports to Wix website',
        epilog=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        '--pdf-dir', '-p',
        type=str,
        default='output',
        help='Directory containing PDF files to upload (default: output/)'
    )
    parser.add_argument(
        '--data-dir', '-d',
        type=str,
        default='data',
        help='Directory containing data files for week number calculation (default: data/)'
    )
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose logging'
    )
    parser.add_argument(
        '--headless',
        action='store_true',
        help='Run browser headless (default: false, not recommended for first run)'
    )
    parser.add_argument(
        '--check-creds',
        action='store_true',
        help='Check if credentials are properly configured and exit'
    )
    parser.add_argument(
        '--assist',
        action='store_true',
        help='Assisted mode: pauses for manual 2FA OTP entry (RECOMMENDED)'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Dry run: show what would be uploaded without making changes'
    )
    parser.add_argument(
        '--api-mode',
        action='store_true',
        help='Use Wix REST API instead of Selenium (requires WIX_API_KEY and WIX_SITE_ID)'
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

    # Check credentials based on mode
    if args.check_creds:
        if args.api_mode:
            # Check API credentials
            api_key = os.getenv('WIX_API_KEY')
            site_id = os.getenv('WIX_SITE_ID')

            if api_key and site_id:
                print("✅ Wix API credentials are configured")
                print(f"   API Key: {api_key[:8]}...{api_key[-4:]}" if len(api_key) > 12 else "   API Key: ***")
                print(f"   Site ID: {site_id}")
                print("\n✅ No 2FA required with API mode!")
                return 0
            else:
                print("❌ Wix API credentials are NOT configured")
                print("\nTo set API credentials, run:")
                print("  export WIX_API_KEY='your-api-key'")
                print("  export WIX_SITE_ID='your-site-id'")
                print("\nGet API key from: https://manage.wix.com/account/api-keys")
                print("Get Site ID from: dashboard URL after '/dashboard/'")
                return 1
        else:
            # Check Selenium credentials
            email = os.getenv('WIX_EMAIL')
            password = os.getenv('WIX_PASSWORD')

            if email and password:
                print("✅ Wix Selenium credentials are configured")
                print(f"   Email: {email[:3]}...{email[-8:]}")
                print("\n⚠️  Note: 2FA OTP must be entered manually during upload")
                print("   Use --assist mode for best experience")
                return 0
            else:
                print("❌ Wix Selenium credentials are NOT configured")
                print("\nTo set credentials, run:")
                print("  export WIX_EMAIL='your.email@example.com'")
                print("  export WIX_PASSWORD='your-password'")
                print("\n⚠️  2FA OTP will be required during upload (use --assist mode)")
                print("\nTip: Use --api-mode to avoid 2FA entirely!")
                return 1

    # Check if PDF directory exists
    pdf_dir = Path(args.pdf_dir)
    if not pdf_dir.exists():
        print(f"❌ PDF directory not found: {pdf_dir}")
        print("\nGenerate PDFs first:")
        print("  python3 main_consolidated.py data/")
        return 1

    # Find PDFs
    individual_pdfs = sorted(pdf_dir.glob('Individual-*.pdf'), reverse=True)
    overall_pdfs = sorted(pdf_dir.glob('Overall-*.pdf'), reverse=True)

    if not individual_pdfs or not overall_pdfs:
        print(f"❌ PDFs not found in {pdf_dir}")
        print("\nExpected files:")
        print("  - Individual-MMDD_HHMMSS.pdf")
        print("  - Overall-MMDD_HHMMSS.pdf")
        print("\nGenerate PDFs first:")
        print("  python3 main_consolidated.py data/")
        return 1

    # Get most recent PDFs
    individual_pdf = individual_pdfs[0]
    overall_pdf = overall_pdfs[0]

    print("\n📄 Found PDFs:")
    print(f"  • Individual: {individual_pdf.name}")
    print(f"  • Overall: {overall_pdf.name}")

    if args.dry_run:
        print("\n🔍 DRY RUN - No changes will be made")
        print("\nWould upload:")
        print(f"  1. {individual_pdf.name}")
        print(f"  2. {overall_pdf.name}")
        print("\nTo actual upload:")
        print("  python3 scripts/wix_uploader.py --assist")
        return 0

    # Calculate week number from the most recent CSV file
    data_dir = Path(args.data_dir) if hasattr(args, 'data_dir') and args.data_dir else Path('data')

    # Look for by_leg export first (best source) - case insensitive search
    all_csvs = list(data_dir.glob('*.csv'))
    csv_files = [f for f in all_csvs if 'by_leg' in f.name.lower() and 'export' in f.name.lower()]
    csv_files = sorted([f for f in csv_files if 'archive' not in str(f).lower()], reverse=True)

    if not csv_files:
        # Fallback to any CSV (exclude samples and archives)
        csv_files = sorted(data_dir.glob('*.csv'), reverse=True)
        csv_files = [f for f in csv_files if 'archive' not in str(f).lower() and 'sample' not in f.name.lower()]

    week_number = 1  # Default
    if csv_files:
        week_number = calculate_week_number_from_csv(csv_files[0])
        logger.info(f"📅 Calculated week number: {week_number} from {csv_files[0].name}")

    # Load Wix folder name from config
    wix_folder = None
    config_path = Path('config.yaml')
    if config_path.exists():
        try:
            with open(config_path) as f:
                config = yaml.safe_load(f)
            wix_folder = config.get('directories', {}).get('wix_folder')
            if wix_folder:
                logger.info(f"📁 Using Wix folder from config: {wix_folder}")
        except Exception as e:
            logger.warning(f"Could not read config.yaml: {e}")

    # Choose uploader based on mode
    if args.api_mode:
        # API Mode - No 2FA required!
        print("\n📡 Using Wix REST API (no 2FA required)")

        try:
            from src.wix_api_uploader import WixAPIUploader
        except ImportError as e:
            logger.error(f"❌ Failed to import WixAPIUploader: {e}")
            logger.error("Install dependencies: pip install requests")
            return 1

        # Create API uploader
        try:
            uploader = WixAPIUploader()
        except ValueError as e:
            logger.error(f"❌ {e}")
            return 1

        # Run upload workflow
        print(f"\n🚀 Starting API upload for Week-{week_number:02d}...")
        print(f"   Individual: {individual_pdf.name}")
        print(f"   Overall: {overall_pdf.name}")
        print()

        upload_kwargs = {
            'individual_pdf': individual_pdf,
            'overall_pdf': overall_pdf,
            'week_number': week_number
        }
        if wix_folder:
            upload_kwargs['season_name'] = wix_folder
        
        success = uploader.upload_weekly_pdfs(**upload_kwargs)

    else:
        # Selenium Mode - Requires 2FA
        print("\n🌐 Using Selenium browser automation (2FA required)")

        try:
            from src.wix_uploader_core import WixUploader
        except ImportError as e:
            logger.error(f"❌ Failed to import WixUploader: {e}")
            logger.error("Install dependencies: pip install selenium webdriver-manager")
            return 1

        # Check Selenium credentials
        email = os.getenv('WIX_EMAIL')
        password = os.getenv('WIX_PASSWORD')

        if not email or not password:
            logger.error("❌ Selenium credentials not configured")
            logger.error("Set WIX_EMAIL and WIX_PASSWORD environment variables")
            logger.error("\nTip: Use --api-mode to avoid 2FA!")
            return 1

        # Create Selenium uploader
        uploader = WixUploader(
            email=email,
            password=password,
            headless=args.headless,
            assist_mode=args.assist
        )

        # Run upload workflow
        print(f"\n🚀 Starting Selenium upload for Week-{week_number:02d}...")
        print(f"   Individual: {individual_pdf.name}")
        print(f"   Overall: {overall_pdf.name}")
        print()

        success = uploader.upload_weekly_pdfs(
            individual_pdf=individual_pdf,
            overall_pdf=overall_pdf,
            week_number=week_number
        )

    if success:
        print("\n✅ Upload completed successfully!")
        return 0
    else:
        print("\n❌ Upload failed - check logs above")
        return 1


if __name__ == '__main__':
    sys.exit(main())
