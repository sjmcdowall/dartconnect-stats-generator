#!/usr/bin/env python3
"""
Test script to generate Overall PDF with REAL data from CSV.
"""

from src.config import Config
from src.data_processor import DataProcessor
from src.pdf_generator import PDFGenerator

if __name__ == "__main__":
    print("🔄 Processing real CSV data...")
    config = Config()
    processor = DataProcessor(config)
    
    # Process the real data
    results = processor.process_file("data/season74/by_leg_export.csv")
    
    print(f"✅ Processed {len(results['raw_data'])} rows")
    print(f"📊 Found {results['raw_data']['Team'].nunique()} teams")
    print(f"👥 Found {results['raw_data']['player_name'].nunique()} players")
    
    # Check cache stats
    enhanced = results.get('enhanced_data', {})
    if 'urls_processed' in enhanced:
        print(f"\n🌐 Cricket data:")
        print(f"   URLs processed: {enhanced['urls_processed']}")
        print(f"   URLs failed: {enhanced.get('urls_failed', 0)}")
        print(f"   Enhanced games: {len(enhanced.get('enhanced_games', []))}")
    
    # Generate the PDF
    print("\n🎨 Generating Overall PDF...")
    generator = PDFGenerator(config, output_dir="output")
    
    try:
        pdf_path = generator.generate_overall_report(results)
        print(f"\n✅ PDF generated successfully!")
        print(f"📄 Location: {pdf_path}")
        print(f"\n💡 Opening PDF...")
        
        import subprocess
        subprocess.run(["open", pdf_path])
        
    except Exception as e:
        print(f"\n❌ Error generating PDF: {e}")
        import traceback
        traceback.print_exc()
