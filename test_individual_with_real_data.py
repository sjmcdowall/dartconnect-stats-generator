#!/usr/bin/env python3
"""
Test script to generate Individual PDF with REAL data from CSV.
"""

from src.config import Config
from src.data_processor import DataProcessor
from src.pdf_generator import PDFGenerator

if __name__ == "__main__":
    print("🔄 Processing real CSV data for Individual report...")
    config = Config()
    processor = DataProcessor(config)
    
    # Process the real data
    results = processor.process_file("docs/samples/dartconnect_exports/Fall_Winter_2025_By_Leg_export.csv")
    
    print(f"✅ Processed {len(results['raw_data'])} rows")
    print(f"📊 Found {results['raw_data']['Division'].nunique()} divisions")
    print(f"👥 Found {results['raw_data']['player_name'].nunique()} players")
    
    # Generate the Individual PDF
    print("\n🎨 Generating Individual PDF...")
    generator = PDFGenerator(config, output_dir="output")
    
    try:
        pdf_path = generator.generate_individual_report(results)
        print(f"\n✅ PDF generated successfully!")
        print(f"📄 Location: {pdf_path}")
        print(f"\n💡 Opening PDF...")
        
        import subprocess
        subprocess.run(["open", pdf_path])
        
    except Exception as e:
        print(f"\n❌ Error generating PDF: {e}")
        import traceback
        traceback.print_exc()
