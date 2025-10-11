#!/usr/bin/env python3
"""
Test script to process real CSV data and verify structure for PDF generation.
"""

from src.config import Config
from src.data_processor import DataProcessor

if __name__ == "__main__":
    config = Config()
    processor = DataProcessor(config)
    
    # Process the sample data
    print("Processing CSV data...")
    results = processor.process_file("docs/samples/dartconnect_exports/Fall_Winter_2025_By_Leg_export.csv")
    
    df = results['raw_data']
    
    print(f"\n✅ Loaded {len(df)} rows")
    print(f"\nColumns after processing: {df.columns.tolist()}")
    
    # Check if key columns exist
    required_cols = ['player_name', 'game_name', 'win', 'Team', 'Division']
    print(f"\n🔍 Checking required columns:")
    for col in required_cols:
        exists = col in df.columns
        print(f"  {col}: {'✅' if exists else '❌'}")
    
    # Show sample data for one player
    print(f"\n📊 Sample data for one player:")
    if 'player_name' in df.columns:
        sample_player = df['player_name'].iloc[0] if len(df) > 0 else None
        if sample_player:
            player_data = df[df['player_name'] == sample_player].head(5)
            print(player_data[['player_name', 'Team', 'game_name', 'win']].to_string())
    
    # Check Winston Division teams
    if 'Division' in df.columns and 'Team' in df.columns:
        winston_teams = sorted(df[df['Division'] == 'Winston']['Team'].unique())
        print(f"\n🏆 Winston Division Teams ({len(winston_teams)}):")
        for team in winston_teams:
            team_size = df[(df['Division'] == 'Winston') & (df['Team'] == team)]['player_name'].nunique() if 'player_name' in df.columns else 0
            print(f"  • {team} ({team_size} players)")
    
    print(f"\n✨ Data processing complete!")
