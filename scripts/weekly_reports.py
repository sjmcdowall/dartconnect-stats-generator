#!/usr/bin/env python3
"""Weekly DartConnect report generation - fully automated.

This script combines export download and report generation:
1. Downloads latest By Leg CSV from DartConnect (headless automation)
2. Processes data with URL enhancement and caching
3. Generates Overall and Individual PDF reports

Usage:
    python3 scripts/weekly_reports.py
    python3 scripts/weekly_reports.py --output-dir data/season74

Setup:
    1. Set credentials in .env:
       DARTCONNECT_EMAIL=your.email@example.com  
       DARTCONNECT_PASSWORD=your-password
    
    2. Run weekly:
       python3 scripts/weekly_reports.py
"""

import sys
import os
import subprocess
from pathlib import Path

# Add parent directory to path so we can import src modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.export_downloader import DartConnectExporter
import argparse
import logging


def main():
    """Main entry point for weekly report generation."""
    parser = argparse.ArgumentParser(
        description='Weekly DartConnect Reports - Download + Generate',
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
        '--reports-dir', '-r',
        type=str,
        default='output',
        help='Output directory for PDF reports (default: output/)'
    )
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose logging'
    )
    parser.add_argument(
        '--skip-download',
        action='store_true',
        help='Skip download, just process existing CSV'
    )
    
    args = parser.parse_args()
    
    # Setup logging (minimal for clean output)
    level = logging.DEBUG if args.verbose else logging.WARNING
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    print("🎯 DartConnect Weekly Reports")
    print("=" * 40)
    
    try:
        csv_path = None
        
        # Step 1: Download CSV
        if not args.skip_download:
            print("📥 Step 1/2: Downloading Latest Export")
            
            exporter = DartConnectExporter(headless=True)
            files = exporter.download_exports(args.output_dir, assist=True)
            
            if not files or 'by_leg' not in files:
                print("❌ Failed to download CSV")
                return 1
            
            csv_path = files['by_leg']
            print(f"   Saved: {csv_path}")
            exporter.close()
        else:
            # Find existing CSV
            data_dir = Path(args.output_dir)
            csvs = list(data_dir.glob("*.csv"))
            if not csvs:
                print(f"❌ No CSV found in {args.output_dir}")
                return 1
            csv_path = sorted(csvs, key=lambda p: p.stat().st_mtime)[-1]  # Most recent
            print(f"📄 Using existing CSV: {csv_path}")
        
        # Step 2: Generate Reports
        print("\n📊 Step 2/2: Generating Reports")
        print("🔧 Starting browser...", end=" ")
        
        # Run main_consolidated.py as subprocess to avoid import issues
        cmd = [
            sys.executable, "main_consolidated.py", 
            str(csv_path),
            "--output-dir", args.reports_dir
        ]
        if args.verbose:
            cmd.append("--verbose")
        
        # Run with suppressed output unless verbose
        if args.verbose:
            result = subprocess.run(cmd, cwd=Path.cwd())
        else:
            result = subprocess.run(cmd, cwd=Path.cwd(), capture_output=True, text=True)
            
            # Parse key results from output
            if result.returncode == 0:
                lines = result.stdout.split('\n')
                
                # Look for key statistics
                for line in lines:
                    if "Total Records:" in line:
                        records = line.split(":")[-1].strip()
                        print(f"✅ Processed {records} records")
                    elif "URLs Processed:" in line:
                        urls = line.split(":")[-1].strip()
                        print(f"✅ Enhanced {urls} games")
                    elif "Generated Overall report:" in line or "Generated Individual report:" in line:
                        pdf_path = line.split(":")[-1].strip()
                        print(f"✅ Generated: {Path(pdf_path).name}")
        
        if result.returncode != 0:
            print("❌ Report generation failed")
            if args.verbose:
                return result.returncode
            else:
                print("   Run with --verbose for details")
                return 1
        
        if not args.verbose:
            print("✅ Reports generated successfully!")
        
        print("\n🎉 Weekly reports complete!")
        print(f"   📁 Data: {csv_path}")
        print(f"   📊 Reports: {args.reports_dir}/")
        
        return 0
        
    except ValueError as e:
        print(f"\n❌ Configuration Error:")
        print(f"   {e}")
        print("\nTo fix, set your credentials:")
        print("  cp .env.example .env")
        print("  # Edit .env with your DartConnect email/password")
        return 1
    except Exception as e:
        print(f"\n❌ Error: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1


if __name__ == '__main__':
    exit(main())