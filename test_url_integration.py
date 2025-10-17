#!/usr/bin/env python3
"""
Quick test to verify URL extraction from DartConnect CSV works correctly.
"""

import pandas as pd
from pathlib import Path
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)

def test_csv_reading():
    """Test that we can read the CSV and extract URLs."""
    csv_file = "data/season74/by_leg_export.csv"
    
    if not Path(csv_file).exists():
        print(f"❌ CSV file not found: {csv_file}")
        return False
    
    print(f"🔍 Testing CSV reading: {csv_file}")
    
    try:
        # Read CSV
        df = pd.read_csv(csv_file)
        print(f"✅ Successfully loaded {len(df)} rows")
        
        # Show column names
        print(f"\n📊 Columns found: {len(df.columns)}")
        for i, col in enumerate(df.columns):
            print(f"  {i+1:2d}. {col}")
        
        # Look for URL columns
        url_columns = [col for col in df.columns if 'link' in col.lower() or 'url' in col.lower()]
        print(f"\n🔗 URL-related columns: {url_columns}")
        
        # Show sample URLs if found
        if url_columns:
            for col in url_columns:
                sample_urls = df[col].dropna().head(3)
                print(f"\n🔗 Sample URLs from '{col}':")
                for i, url in enumerate(sample_urls, 1):
                    print(f"  {i}. {url}")
        
        # Test column mapping
        print("\n🗺️  Testing column mapping:")
        column_mapping = {}
        patterns = {
            'player_name': ['player', 'name', 'player_name', 'playername', 'first name'],
            'last_name': ['last name, fi', 'lastname', 'last_name'],
            'game_date': ['date', 'game_date', 'gamedate', 'match_date'],
            'score': ['score', 'total_score', 'points', 'pts/marks'],
            'average': ['avg', 'average', 'dart_average', '3da'],
            'game_name': ['game name', 'game_name', 'game_type'],
            'report_url': ['report link', 'report_link', 'report_url'],
            'event_url': ['event link', 'event_link', 'event_url']
        }
        
        for standard_name, possible_names in patterns.items():
            for col in df.columns:
                if col.lower() in [name.lower() for name in possible_names]:
                    column_mapping[col] = standard_name
                    print(f"  '{col}' -> '{standard_name}'")
                    break
        
        print(f"\n✅ Column mapping successful: {len(column_mapping)} mappings")
        
        # Test with mapped columns
        df_mapped = df.rename(columns=column_mapping)
        if 'report_url' in df_mapped.columns:
            unique_urls = df_mapped['report_url'].dropna().nunique()
            print(f"🔗 Found {unique_urls} unique report URLs")
            
            # Show URL format
            sample_url = df_mapped['report_url'].dropna().iloc[0]
            print(f"📋 Sample URL: {sample_url}")
            
            # Test URL conversion
            if '/history/report/match/' in sample_url:
                game_url = sample_url.replace('/history/report/match/', '/games/')
                print(f"🔄 Converted to: {game_url}")
                print("✅ URL conversion working")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_imports():
    """Test that all required imports work."""
    print("🔍 Testing imports...")
    
    try:
        from src.config import Config
        print("✅ Config import successful")
        
        from src.data_processor import DataProcessor  
        print("✅ DataProcessor import successful")
        
        from src.url_fetcher import DartConnectURLFetcher
        print("✅ URLFetcher import successful")
        
        # Test initialization
        config = Config()
        processor = DataProcessor(config)
        fetcher = DartConnectURLFetcher()
        
        print("✅ All components initialized successfully")
        return True
        
    except Exception as e:
        print(f"❌ Import error: {e}")
        return False


if __name__ == "__main__":
    print("🧪 DartConnect URL Integration Test")
    print("=" * 50)
    
    # Test imports
    imports_ok = test_imports()
    
    # Test CSV reading
    csv_ok = test_csv_reading()
    
    print("\n" + "=" * 50)
    print("📋 TEST SUMMARY")
    print("=" * 50)
    print(f"Imports: {'✅ PASS' if imports_ok else '❌ FAIL'}")
    print(f"CSV Reading: {'✅ PASS' if csv_ok else '❌ FAIL'}")
    
    if imports_ok and csv_ok:
        print("\n🎉 All tests passed! Integration should work correctly.")
        print("\n🚀 Next steps:")
        print("  1. Run: python enhanced_integration_example.py")
        print("  2. Check generated reports for enhanced statistics")
        print("  3. Compare Cricket QPs with and without URL data")
    else:
        print("\n⚠️  Some tests failed. Please check the errors above.")