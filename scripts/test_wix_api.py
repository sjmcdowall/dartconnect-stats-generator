#!/usr/bin/env python3
"""
Simple test script to verify Wix API credentials and connectivity.

Tests:
1. API key and site ID are configured
2. Can authenticate to Wix API
3. Can list folders in Media Manager
4. Can search for season folder

Usage:
    # Set credentials
    export WIX_API_KEY="your-api-key"
    export WIX_SITE_ID="your-site-id"

    # Run test
    python3 scripts/test_wix_api.py
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import logging
from src.wix_api_uploader import WixAPIUploader


def main():
    """Test Wix API connectivity."""
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    logger = logging.getLogger(__name__)

    print("=" * 60)
    print("Wix API Connection Test")
    print("=" * 60)
    print()

    # Check credentials
    api_key = os.getenv('WIX_API_KEY')
    site_id = os.getenv('WIX_SITE_ID')

    if not api_key:
        print("❌ WIX_API_KEY not set")
        print("\nTo set it:")
        print("  export WIX_API_KEY='your-api-key'")
        print("\nGet it from: https://manage.wix.com/account/api-keys")
        return 1

    if not site_id:
        print("❌ WIX_SITE_ID not set")
        print("\nTo set it:")
        print("  export WIX_SITE_ID='your-site-id'")
        print("\nFind it in dashboard URL after '/dashboard/'")
        return 1

    print(f"✅ WIX_API_KEY: {api_key[:8]}...{api_key[-4:]}")
    print(f"✅ WIX_SITE_ID: {site_id}")
    print()

    # Create uploader instance
    try:
        print("🔧 Creating WixAPIUploader instance...")
        uploader = WixAPIUploader(api_key, site_id)
        print("✅ WixAPIUploader created successfully")
        print()
    except Exception as e:
        print(f"❌ Failed to create uploader: {e}")
        return 1

    # Test 1: List folders in media-root
    try:
        print("📁 Test 1: Listing folders in root...")
        folders = uploader.list_folders()  # None = root folder

        print(f"✅ Found {len(folders)} folder(s) in media-root:")
        for folder in folders:
            folder_id = folder.get('id', 'unknown')
            folder_name = folder.get('displayName', 'unnamed')
            print(f"   • {folder_name} (ID: {folder_id})")
        print()

    except Exception as e:
        print(f"❌ Failed to list folders: {e}")
        logger.exception("Full error:")
        return 1

    # Test 2: Search for season folder
    try:
        print("📁 Test 2: Searching for season folders...")
        season_folders = [f for f in folders if 'SEASON' in f.get('displayName', '').upper()]

        if season_folders:
            print(f"✅ Found {len(season_folders)} season folder(s):")
            for folder in season_folders:
                folder_id = folder.get('id')
                folder_name = folder.get('displayName')
                print(f"   • {folder_name} (ID: {folder_id})")
        else:
            print("⚠️  No season folders found")
            print("   Expected folder like: 'SEASON 74 - 2025 Fall'")
        print()

    except Exception as e:
        print(f"❌ Failed to search season folders: {e}")
        return 1

    # Test 3: Get specific folder details
    if season_folders:
        try:
            season_folder = season_folders[0]
            season_name = season_folder.get('displayName')
            season_id = season_folder.get('id')

            print(f"📁 Test 3: Listing contents of '{season_name}'...")
            season_contents = uploader.list_folders(season_id)

            print(f"✅ Found {len(season_contents)} item(s) in season folder:")
            for item in season_contents[:10]:  # Show first 10
                item_name = item.get('displayName', 'unnamed')
                item_id = item.get('id', 'unknown')
                print(f"   • {item_name} (ID: {item_id})")

            if len(season_contents) > 10:
                print(f"   ... and {len(season_contents) - 10} more")
            print()

        except Exception as e:
            print(f"❌ Failed to list season contents: {e}")
            logger.exception("Full error:")
            return 1

    # Summary
    print("=" * 60)
    print("✅ All tests passed!")
    print("=" * 60)
    print()
    print("Your Wix API credentials are working correctly.")
    print("You can now use the full upload workflow:")
    print("  python3 scripts/wix_uploader.py --api-mode")
    print()

    return 0


if __name__ == '__main__':
    sys.exit(main())
