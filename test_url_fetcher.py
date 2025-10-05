#!/usr/bin/env python3
"""Test script for URL fetcher functionality."""

import sys
import json
from pathlib import Path

# Add src directory to path for imports
sys.path.append(str(Path(__file__).parent / 'src'))

from url_fetcher import DartConnectURLFetcher


def test_url_fetch():
    """Test fetching data from a sample DartConnect URL."""
    # Sample URL from your message
    test_url = "https://recap.dartconnect.com/games/68aba220f978cb217a4c55cb"
    
    print("Testing DartConnect URL Fetcher...")
    print(f"URL: {test_url}")
    print("-" * 60)
    
    # Create fetcher
    fetcher = DartConnectURLFetcher()
    
    # Fetch game data
    print("Fetching game data...")
    game_data = fetcher.fetch_game_data(test_url)
    
    if not game_data:
        print("❌ Failed to fetch game data")
        return
    
    print("✅ Successfully fetched game data")
    
    # Display match info
    match_info = game_data.get('matchInfo', {})
    print(f"\nMatch Info:")
    print(f"  League: {match_info.get('competition_title')}")
    print(f"  Event: {match_info.get('event_title')}")
    print(f"  Home: {match_info.get('home_label')}")
    print(f"  Away: {match_info.get('away_label')}")
    print(f"  Date: {match_info.get('server_match_start_date')}")
    print(f"  Total Games: {match_info.get('total_games')}")
    print(f"  Has Cricket: {match_info.get('has_cricket')}")
    
    # Extract cricket stats
    print("\nExtracting Cricket statistics...")
    cricket_games = fetcher.extract_cricket_stats(game_data)
    
    if not cricket_games:
        print("❌ No Cricket games found")
        return
    
    print(f"✅ Found {len(cricket_games)} Cricket games")
    
    # Display cricket game details
    for i, game in enumerate(cricket_games, 1):
        print(f"\n--- Cricket Game {i} ---")
        print(f"Duration: {game.get('duration')}")
        print(f"Home MPR: {game.get('home_mpr')}")
        print(f"Away MPR: {game.get('away_mpr')}")
        print(f"Home Ending Marks: {game.get('home_ending_marks')}")
        print(f"Away Ending Marks: {game.get('away_ending_marks')}")
        
        # Display player stats
        players = game.get('players', [])
        print(f"\nPlayer Statistics:")
        for player in players:
            name = player.get('name', 'Unknown')
            turns = player.get('turns', 0)
            bulls = player.get('total_bulls', 0)
            single_bulls = player.get('single_bulls', 0)
            double_bulls = player.get('double_bulls', 0)
            big_hits = player.get('big_hits', 0)
            misses = player.get('misses', 0)
            
            # Get ending marks
            ending_marks = player.get('ending_marks', 0)
            
            # Calculate official QP
            qp_level = fetcher.calculate_cricket_qp(player)
            
            print(f"  {name}:")
            print(f"    Ending Marks: {ending_marks}")
            print(f"    Turns: {turns}")
            print(f"    Bulls: {bulls} (SB: {single_bulls}, DB: {double_bulls})")
            print(f"    Big Hits: {big_hits}")
            print(f"    Misses: {misses}")
            print(f"    Official QP Level: {qp_level}")


if __name__ == "__main__":
    test_url_fetch()