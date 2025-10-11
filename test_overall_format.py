#!/usr/bin/env python3
"""
Test script to generate Overall PDF with sample data to check formatting.
"""

from src.config import Config
from src.pdf_generator import PDFGenerator

# Sample data matching the structure
sample_data = {
    'raw_data': None,  # Will use sample teams
    'statistics': {},
    'derived_metrics': {},
}

# Create sample teams for testing
def get_sample_teams():
    """Sample teams for Winston Division to test formatting."""
    return [
        {
            "name": "DARK HORSE",
            "players": [
                {
                    "name": "Danny Roark",
                    "legs": 93,
                    "games": 39,
                    "qualify": 0,
                    "eligibility": "QUALIFIED",
                    "s01_w": 5, "s01_l": 6,
                    "sc_w": 5, "sc_l": 4,
                    "d01_w": 2, "d01_l": 7,
                    "dc_w": 7, "dc_l": 3,
                    "total_w": 19, "total_l": 20,
                    "win_pct": "48.72%",
                    "qps": 108,
                    "qp_pct": "116.13%",
                    "rating": "2.1356"
                },
                {
                    "name": "Jeff Maelin",
                    "legs": 39,
                    "games": 16,
                    "qualify": 2,
                    "eligibility": "INELIGIBLE",
                    "s01_w": 1, "s01_l": 0,
                    "sc_w": 4, "sc_l": 4,
                    "d01_w": 0, "d01_l": 3,
                    "dc_w": 2, "dc_l": 2,
                    "total_w": 7, "total_l": 9,
                    "win_pct": "43.75%",
                    "qps": 30,
                    "qp_pct": "76.92%",
                    "rating": "1.6442"
                },
                {
                    "name": "Cissy Mealin",
                    "legs": 41,
                    "games": 18,
                    "qualify": 0,
                    "eligibility": "QUALIFIED",
                    "s01_w": 4, "s01_l": 2,
                    "sc_w": 3, "sc_l": 0,
                    "d01_w": 1, "d01_l": 4,
                    "dc_w": 3, "dc_l": 1,
                    "total_w": 11, "total_l": 7,
                    "win_pct": "61.11%",
                    "qps": 23,
                    "qp_pct": "56.10%",
                    "rating": "1.7832"
                }
            ]
        },
        {
            "name": "KBTN",
            "players": [
                {
                    "name": "James Shelton",
                    "legs": 84,
                    "games": 37,
                    "qualify": 0,
                    "eligibility": "QUALIFIED",
                    "s01_w": 5, "s01_l": 4,
                    "sc_w": 6, "sc_l": 4,
                    "d01_w": 5, "d01_l": 4,
                    "dc_w": 6, "dc_l": 3,
                    "total_w": 22, "total_l": 15,
                    "win_pct": "59.46%",
                    "qps": 118,
                    "qp_pct": "140.48%",
                    "rating": "2.5940"
                },
                {
                    "name": "Ellen Lee",
                    "legs": 58,
                    "games": 24,
                    "qualify": 0,
                    "eligibility": "QUALIFIED",
                    "s01_w": 5, "s01_l": 3,
                    "sc_w": 1, "sc_l": 4,
                    "d01_w": 7, "d01_l": 1,
                    "dc_w": 1, "dc_l": 2,
                    "total_w": 14, "total_l": 10,
                    "win_pct": "58.33%",
                    "qps": 26,
                    "qp_pct": "44.83%",
                    "rating": "1.6149"
                }
            ]
        }
    ]

# Patch the _get_division_teams method to return our sample data
def patched_get_division_teams(self, data, division_name):
    if "WINSTON" in division_name:
        return get_sample_teams()
    return []

# Main test
if __name__ == "__main__":
    config = Config()
    generator = PDFGenerator(config, output_dir="output")
    
    # Temporarily replace the method
    PDFGenerator._get_division_teams = patched_get_division_teams
    
    # Generate the PDF
    try:
        pdf_path = generator.generate_overall_report(sample_data)
        print(f"✅ PDF generated successfully: {pdf_path}")
        print(f"Open it to check the formatting!")
    except Exception as e:
        print(f"❌ Error generating PDF: {e}")
        import traceback
        traceback.print_exc()
