#!/usr/bin/env python3
"""
Integration example showing how URL fetching enhances CSV data processing.

This demonstrates how the DartConnect URL fetcher can be used alongside
the existing CSV data to provide enhanced Quality Point calculations.
"""

import sys
from pathlib import Path

# Add src directory to path for imports
sys.path.append(str(Path(__file__).parent / 'src'))

from url_fetcher import DartConnectURLFetcher


def analyze_sample_csv_data():
    """
    Example of how URL data could enhance CSV processing.
    
    This shows the potential integration between CSV exports (which contain URLs)
    and detailed game data fetching for enhanced QP calculations.
    """
    
    print("🎯 DartConnect Enhanced QP Analysis")
    print("=" * 60)
    
    # Sample data that might come from CSV processing
    sample_csv_row = {
        'player_name': 'Megan Ferguson',
        'game_type': 'Cricket',
        'game_url': 'https://recap.dartconnect.com/games/68aba220f978cb217a4c55cb',
        'basic_mpr': '3.4',
        'basic_marks': '190'  # This is from the CSV but doesn't show bulls
    }
    
    print(f"📊 Analyzing player: {sample_csv_row['player_name']}")
    print(f"🎮 Game type: {sample_csv_row['game_type']}")
    print(f"🔗 URL: {sample_csv_row['game_url']}")
    print()
    
    # Create URL fetcher
    fetcher = DartConnectURLFetcher()
    
    # Fetch detailed game data
    print("🔍 Fetching detailed game data...")
    game_data = fetcher.fetch_game_data(sample_csv_row['game_url'])
    
    if not game_data:
        print("❌ Could not fetch detailed game data")
        return
    
    print("✅ Successfully fetched detailed data")
    
    # Extract Cricket games
    cricket_games = fetcher.extract_cricket_stats(game_data)
    
    if not cricket_games:
        print("❌ No Cricket games found")
        return
    
    print(f"🏏 Found {len(cricket_games)} Cricket games")
    print()
    
    # Analyze QP opportunities
    print("🏆 Enhanced Quality Point Analysis")
    print("-" * 40)
    
    total_csv_data = len(cricket_games)  # Representing multiple CSV rows
    enhanced_qp_possible = 0
    
    for i, game in enumerate(cricket_games, 1):
        print(f"\n🎯 Game {i} Analysis:")
        print(f"   Duration: {game.get('duration')}")
        print(f"   Home MPR: {game.get('home_mpr')}")
        print(f"   Away MPR: {game.get('away_mpr')}")
        
        players = game.get('players', [])
        
        for player in players:
            name = player.get('name')
            ending_marks = player.get('ending_marks', 0)
            bulls = player.get('total_bulls', 0)
            single_bulls = player.get('single_bulls', 0)
            double_bulls = player.get('double_bulls', 0)
            
            # Calculate official QP
            qp_level = fetcher.calculate_cricket_qp(player)
            
            print(f"   👤 {name}:")
            print(f"      📈 Ending Marks: {ending_marks}")
            print(f"      🎯 Bulls: {bulls} (SB: {single_bulls}, DB: {double_bulls})")
            print(f"      🏆 QP Level: {qp_level}")
            
            # Show what CSV alone couldn't provide
            if bulls > 0:
                enhanced_qp_possible += 1
                print(f"      ⭐ Enhanced data: Bulls info not available in CSV!")
            
            # Show QP breakdown
            if qp_level > 0:
                print(f"      💎 Qualifies for QP Level {qp_level}")
            else:
                print(f"      ❌ No QP earned")
    
    # Summary
    print("\n" + "=" * 60)
    print("📋 ENHANCEMENT SUMMARY")
    print("=" * 60)
    print(f"📊 Total games analyzed: {total_csv_data}")
    print(f"🎯 Games with bull data (enhanced): {enhanced_qp_possible}")
    print(f"📈 Enhancement rate: {(enhanced_qp_possible/total_csv_data)*100:.1f}%")
    
    print("\n🔧 INTEGRATION BENEFITS:")
    print("• ✅ Accurate Cricket QP calculations (H + B combinations)")
    print("• ✅ Turn-by-turn performance insights")
    print("• ✅ Bulls tracking (impossible from CSV alone)")
    print("• ✅ Miss counting and big hit detection")
    print("• ✅ Enhanced statistics for league reports")
    
    print("\n🚀 NEXT STEPS:")
    print("• Integrate URL fetcher into DataProcessor")
    print("• Add URL column detection in CSV mapping")
    print("• Create enhanced PDF reports with detailed QPs")
    print("• Add caching for URL data to avoid repeated fetches")
    print("• Implement batch processing for multiple URLs")


def show_qp_tables():
    """Display the official QP calculation tables."""
    
    print("\n📋 OFFICIAL QP CALCULATION TABLES")
    print("=" * 50)
    
    print("\n🏏 CRICKET QPs (Hits + Bulls):")
    print("Level 1: 5H, 3H+1B, 2B+2H")
    print("Level 2: 6H, 3B, 1H+3B, 3H+2B, 4H+1B")  
    print("Level 3: 7H, 4B, 1H+4B, 2H+3B, 4H+2B, 5H+1B")
    print("Level 4: 8H, 5B, 2H+4B, 3H+3B, 5H+2B, 6H+1B")
    print("Level 5: 9H, 6B, 3H+4B, 6H+2B")
    print("(H = Hits/Marks, B = Bulls)")
    
    print("\n🎯 501 QPs (ADDITIVE - Both Columns):")
    print("Total Score QPs:      Checkout QPs:")
    print("1: 95-115            1: 61-84 out")
    print("2: 116-131           2: 85-106 out") 
    print("3: 132-147           3: 107-128 out")
    print("4: 148-163           4: 129-150 out")
    print("5: 164-180           5: 151-170 out")
    print("\n💡 Example: 132 total + 132 checkout = 3 + 4 = 7 QPs!")


if __name__ == "__main__":
    analyze_sample_csv_data()
    show_qp_tables()