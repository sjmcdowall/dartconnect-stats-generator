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
    email = os.getenv('WIX_EMAIL')
    password = os.getenv('WIX_PASSWORD')

    if args.check_creds:
        if email and password:
            print("✅ Wix credentials are configured")
            print(f"   Email: {email[:3]}...{email[-8:]}")  # Show partial email for privacy
            print("\n⚠️  Note: 2FA OTP must be entered manually during upload")
            print("   Use --assist mode for best experience")
            return 0
        else:
            print("❌ Wix credentials are NOT configured")
            print("\nTo set credentials, run:")
            print("  export WIX_EMAIL='your.email@example.com'")
            print("  export WIX_PASSWORD='your-password'")
            print("\n⚠️  2FA OTP will be required during upload (use --assist mode)")
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

    # TODO: Implement actual upload
    print("\n⚠️  Upload functionality not yet implemented")
    print("\nNext steps:")
    print("  1. Implement WixUploader class in src/")
    print("  2. Add Selenium automation for login, navigation, upload, linking, publish")
    print("  3. Handle 2FA OTP with --assist mode")

    return 1


if __name__ == '__main__':
    sys.exit(main())
