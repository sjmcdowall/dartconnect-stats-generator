#!/usr/bin/env python3
"""
DartConnect Cache Manager

A utility script to manage and inspect the DartConnect URL cache.
"""

import sys
import json
from pathlib import Path
from src.url_fetcher import DartConnectURLFetcher


def print_cache_info():
    """Print detailed cache information."""
    fetcher = DartConnectURLFetcher()
    cache_info = fetcher.get_cache_info()
    
    print("🗂️  DartConnect Cache Information")
    print("=" * 40)
    
    if 'error' in cache_info:
        print(f"❌ Error: {cache_info['error']}")
        return
    
    if cache_info['total_files'] == 0:
        print("📭 Cache is empty")
        return
    
    print(f"📁 Total Files: {cache_info['total_files']}")
    print(f"💾 Total Size: {cache_info['total_size_mb']} MB")
    print(f"⏰ Cache Expiry: {cache_info['expiry_days']} days (~{cache_info['expiry_days']/30:.1f} months)")
    
    if cache_info['oldest_file']:
        oldest = cache_info['oldest_file']
        print(f"🕰️  Oldest File: {oldest['name']} ({oldest['age_days']} days old)")
        
    if cache_info['newest_file']:
        newest = cache_info['newest_file']
        print(f"🆕 Newest File: {newest['name']} ({newest['age_days']} days old)")
    
    # Calculate estimated cache usage over time
    avg_file_size_mb = cache_info['total_size_mb'] / cache_info['total_files']
    print(f"\n📊 Statistics:")
    print(f"   Average file size: {avg_file_size_mb:.2f} MB")
    print(f"   Estimated weekly growth: ~{avg_file_size_mb * 20:.1f} MB (assuming 20 new games/week)")


def clear_expired_cache():
    """Clear expired cache entries."""
    fetcher = DartConnectURLFetcher()
    cleared = fetcher.clear_cache(older_than_days=fetcher.cache_expiry_days)
    
    if cleared > 0:
        print(f"🧹 Cleared {cleared} expired cache files")
    else:
        print("✨ No expired cache files found")


def clear_all_cache():
    """Clear all cache entries (use with caution!)."""
    response = input("⚠️  Are you sure you want to clear ALL cache files? (type 'yes' to confirm): ")
    if response.lower() == 'yes':
        fetcher = DartConnectURLFetcher()
        cleared = fetcher.clear_cache()
        print(f"🧹 Cleared {cleared} cache files")
    else:
        print("❌ Cache clear cancelled")


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print("Usage: python cache_manager.py [info|clear-expired|clear-all]")
        print()
        print("Commands:")
        print("  info         - Show cache information and statistics")
        print("  clear-expired - Remove cache files older than expiry period")
        print("  clear-all    - Remove all cache files (use with caution!)")
        sys.exit(1)
    
    command = sys.argv[1].lower()
    
    if command == 'info':
        print_cache_info()
    elif command == 'clear-expired':
        clear_expired_cache()
    elif command == 'clear-all':
        clear_all_cache()
    else:
        print(f"❌ Unknown command: {command}")
        sys.exit(1)


if __name__ == '__main__':
    main()