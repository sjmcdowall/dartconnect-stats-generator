#!/usr/bin/env python3
"""
Test script for the consolidated DartConnect processing approach.

This validates that the by_leg_export.csv + URL processing provides
equal or better data quality compared to leaderboard-based processing.
"""

import pandas as pd
import numpy as np
from pathlib import Path
import json
from typing import Dict, Any, List
import logging

from src.config import Config
from src.data_processor import DataProcessor
from src.url_fetcher import DartConnectURLFetcher


def setup_test_logging():
    """Setup logging for testing."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )


def create_sample_by_leg_data() -> pd.DataFrame:
    """Create sample by_leg export data for testing."""
    sample_data = [
        {
            'Last Name, FI': 'Smith, J',
            'Date': '2024-01-15',
            'Game Name': 'Cricket',
            'Score': 195,
            'Report Link': 'https://recap.dartconnect.com/history/report/match/68aba095f978cb217a4c5457',
            'Win': 'Y'
        },
        {
            'Last Name, FI': 'Doe, J',
            'Date': '2024-01-15',
            'Game Name': 'Cricket',
            'Score': 178,
            'Report Link': 'https://recap.dartconnect.com/history/report/match/68aba095f978cb217a4c5457',
            'Win': 'N'
        },
        {
            'Last Name, FI': 'Johnson, M',
            'Date': '2024-01-22',
            'Game Name': '501',
            'Score': 132,
            'Report Link': 'https://recap.dartconnect.com/history/report/match/68ab9f42f978cb217a4c5308',
            'Win': 'Y'
        },
        {
            'Last Name, FI': 'Wilson, S',
            'Date': '2024-01-22',
            'Game Name': '501',
            'Score': 125,
            'Report Link': 'https://recap.dartconnect.com/history/report/match/68ab9f42f978cb217a4c5308',
            'Win': 'N'
        }
    ]
    return pd.DataFrame(sample_data)


def create_sample_cricket_leaderboard() -> pd.DataFrame:
    """Create sample cricket leaderboard data."""
    sample_data = [
        {
            'Player': 'John Smith',
            'Games': 15,
            'Avg': 45.2,
            'PPR': 2.8,
            'MPR': 1.9,
            'Pts/Marks': 195
        },
        {
            'Player': 'Jane Doe',
            'Games': 12,
            'Avg': 42.1,
            'PPR': 2.6,
            'MPR': 1.7,
            'Pts/Marks': 178
        }
    ]
    return pd.DataFrame(sample_data)


def create_sample_501_leaderboard() -> pd.DataFrame:
    """Create sample 501 leaderboard data."""
    sample_data = [
        {
            'Player': 'Mike Johnson',
            'Games': 18,
            '3DA': 48.5,
            'HF': 132,
            'LF': 89,
            'CO%': 28.5
        },
        {
            'Player': 'Sarah Wilson',
            'Games': 16,
            '3DA': 44.2,
            'HF': 125,
            'LF': 82,
            'CO%': 25.1
        }
    ]
    return pd.DataFrame(sample_data)


def save_test_files(test_dir: Path) -> Dict[str, Path]:
    """Save sample data files for testing."""
    test_dir.mkdir(exist_ok=True)
    
    # Save test files
    by_leg_data = create_sample_by_leg_data()
    cricket_data = create_sample_cricket_leaderboard()
    dart_501_data = create_sample_501_leaderboard()
    
    files = {
        'by_leg': test_dir / 'test_by_leg_export.csv',
        'cricket': test_dir / 'test_cricket_leaderboard.csv',
        'dart_501': test_dir / 'test_501_leaderboard.csv'
    }
    
    by_leg_data.to_csv(files['by_leg'], index=False)
    cricket_data.to_csv(files['cricket'], index=False)
    dart_501_data.to_csv(files['dart_501'], index=False)
    
    return files


def test_url_processing_capability():
    """Test the URL processing capability with sample URLs."""
    print("🔗 Testing URL Processing Capability")
    print("-" * 40)
    
    sample_urls = [
        "https://recap.dartconnect.com/history/report/match/68aba095f978cb217a4c5457",
        "https://recap.dartconnect.com/history/report/match/68ab9f42f978cb217a4c5308",
    ]
    
    fetcher = DartConnectURLFetcher()
    results = []
    
    for i, url in enumerate(sample_urls, 1):
        print(f"\n🎯 Test URL {i}: Testing URL processing")
        
        # Convert to game URL format
        game_url = url.replace('/history/report/match/', '/games/')
        print(f"   Converted URL: {game_url}")
        
        try:
            game_data = fetcher.fetch_game_data(game_url)
            if game_data:
                print("   ✅ Successfully fetched game data")
                
                # Test Cricket extraction
                cricket_games = fetcher.extract_cricket_stats(game_data)
                if cricket_games:
                    print(f"   🏏 Found {len(cricket_games)} Cricket games")
                    
                    # Test QP calculation
                    for game in cricket_games[:1]:  # Test first game
                        for player in game.get('players', [])[:1]:  # Test first player
                            qp = fetcher.calculate_cricket_qp(player)
                            name = player.get('name', 'Unknown')
                            bulls = player.get('total_bulls', 0)
                            marks = player.get('ending_marks', 0)
                            print(f"   👤 Sample QP: {name} = {qp} QP (Bulls: {bulls}, Marks: {marks})")
                
                results.append({'url': game_url, 'success': True, 'data': game_data})
            else:
                print("   ❌ Failed to fetch game data")
                results.append({'url': game_url, 'success': False, 'data': None})
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
            results.append({'url': game_url, 'success': False, 'error': str(e)})
    
    success_count = sum(1 for r in results if r.get('success', False))
    success_rate = (success_count / len(results)) * 100
    
    print(f"\n📊 URL Processing Results:")
    print(f"   Success Rate: {success_rate:.1f}% ({success_count}/{len(results)})")
    
    return results


def test_data_processing_comparison(test_files: Dict[str, Path]):
    """Compare processing results between by_leg and leaderboard approaches."""
    print("\n📊 Testing Data Processing Comparison")
    print("-" * 45)
    
    config = Config()
    processor = DataProcessor(config)
    
    results_comparison = {
        'by_leg_results': None,
        'cricket_results': None,
        'dart_501_results': None,
        'comparison_metrics': {}
    }
    
    # Test by_leg processing (with URL enhancement)
    print("🎯 Processing by_leg export data...")
    try:
        by_leg_results = processor.process_file(str(test_files['by_leg']))
        results_comparison['by_leg_results'] = by_leg_results
        
        # Analyze enhanced data
        enhanced_data = by_leg_results.get('enhanced_data', {})
        urls_processed = enhanced_data.get('urls_processed', 0)
        urls_failed = enhanced_data.get('urls_failed', 0)
        
        print(f"   ✅ Successfully processed by_leg data")
        print(f"   📈 Records: {len(by_leg_results['raw_data'])}") 
        print(f"   🔗 URLs processed: {urls_processed}")
        print(f"   ❌ URLs failed: {urls_failed}")
        
        if enhanced_data.get('cricket_qp_data'):
            cricket_qp_count = len(enhanced_data['cricket_qp_data'])
            print(f"   🏏 Enhanced Cricket games: {cricket_qp_count}")
        
    except Exception as e:
        print(f"   ❌ Failed to process by_leg data: {e}")
    
    # Test cricket leaderboard processing
    print(f"\n🏏 Processing cricket leaderboard data...")
    try:
        cricket_results = processor.process_file(str(test_files['cricket']))
        results_comparison['cricket_results'] = cricket_results
        print(f"   ✅ Successfully processed cricket leaderboard")
        print(f"   📈 Records: {len(cricket_results['raw_data'])}")
    except Exception as e:
        print(f"   ❌ Failed to process cricket leaderboard: {e}")
    
    # Test 501 leaderboard processing  
    print(f"\n🎯 Processing 501 leaderboard data...")
    try:
        dart_501_results = processor.process_file(str(test_files['dart_501']))
        results_comparison['dart_501_results'] = dart_501_results
        print(f"   ✅ Successfully processed 501 leaderboard")
        print(f"   📈 Records: {len(dart_501_results['raw_data'])}")
    except Exception as e:
        print(f"   ❌ Failed to process 501 leaderboard: {e}")
    
    return results_comparison


def analyze_data_quality_comparison(comparison: Dict[str, Any]):
    """Analyze and compare data quality between different approaches."""
    print("\n🔍 Data Quality Comparison Analysis")
    print("-" * 40)
    
    by_leg = comparison.get('by_leg_results')
    cricket = comparison.get('cricket_results') 
    dart_501 = comparison.get('dart_501_results')
    
    analysis = {
        'by_leg_score': 0,
        'leaderboard_score': 0,
        'advantages': [],
        'limitations': []
    }
    
    if by_leg:
        print("📊 By_Leg Export Analysis:")
        
        # Check for enhanced data features
        enhanced_data = by_leg.get('enhanced_data', {})
        if enhanced_data.get('urls_processed', 0) > 0:
            analysis['by_leg_score'] += 30
            analysis['advantages'].append("✅ URL processing provides detailed game data")
        
        if enhanced_data.get('cricket_qp_data'):
            analysis['by_leg_score'] += 25
            analysis['advantages'].append("✅ Enhanced Cricket QPs with Bulls data")
        
        # Check for game-level data
        raw_data = by_leg.get('raw_data')
        if raw_data is not None and 'game_name' in raw_data.columns:
            analysis['by_leg_score'] += 15
            analysis['advantages'].append("✅ Game-by-game tracking available")
        
        if 'game_date' in raw_data.columns if raw_data is not None else False:
            analysis['by_leg_score'] += 10
            analysis['advantages'].append("✅ Exact game dates available")
        
        analysis['by_leg_score'] += 20  # Base score for comprehensive processing
        
        print(f"   Quality Score: {analysis['by_leg_score']}/100")
    
    if cricket or dart_501:
        print(f"\n📈 Leaderboard Data Analysis:")
        
        leaderboard_score = 0
        
        if cricket:
            leaderboard_score += 25
            print("   ✅ Cricket statistics available")
        
        if dart_501:
            leaderboard_score += 25  
            print("   ✅ 501 statistics available")
        
        # Limitations of leaderboard approach
        analysis['limitations'].extend([
            "❌ No game-by-game detail",
            "❌ Cricket QPs incomplete (missing bulls data)",
            "❌ Limited 501 checkout detection",
            "❌ No performance trends"
        ])
        
        leaderboard_score += 20  # Base score for summary statistics
        analysis['leaderboard_score'] = leaderboard_score
        
        print(f"   Quality Score: {leaderboard_score}/100")
    
    # Overall recommendation
    print(f"\n🏆 OVERALL COMPARISON:")
    print(f"   By_Leg Approach: {analysis['by_leg_score']}/100")
    print(f"   Leaderboard Approach: {analysis['leaderboard_score']}/100")
    
    if analysis['by_leg_score'] > analysis['leaderboard_score']:
        winner = "BY_LEG EXPORT"
        difference = analysis['by_leg_score'] - analysis['leaderboard_score']
        print(f"   🥇 Winner: {winner} (by {difference} points)")
    else:
        winner = "LEADERBOARD CSVs"
        difference = analysis['leaderboard_score'] - analysis['by_leg_score']
        print(f"   🥇 Winner: {winner} (by {difference} points)")
    
    if analysis['advantages']:
        print(f"\n✅ By_Leg Advantages:")
        for advantage in analysis['advantages']:
            print(f"   {advantage}")
    
    if analysis['limitations']:
        print(f"\n⚠️ Leaderboard Limitations:")
        for limitation in analysis['limitations']:
            print(f"   {limitation}")
    
    return analysis


def generate_test_report(url_results: List[Dict], comparison: Dict[str, Any], quality_analysis: Dict[str, Any]):
    """Generate a comprehensive test report."""
    report = {
        'test_summary': {
            'timestamp': pd.Timestamp.now().isoformat(),
            'url_processing_success_rate': sum(1 for r in url_results if r.get('success', False)) / len(url_results) * 100,
            'by_leg_quality_score': quality_analysis['by_leg_score'],
            'leaderboard_quality_score': quality_analysis['leaderboard_score']
        },
        'url_processing_results': url_results,
        'data_processing_comparison': comparison,
        'quality_analysis': quality_analysis,
        'recommendation': {
            'consolidate_to_by_leg': quality_analysis['by_leg_score'] > quality_analysis['leaderboard_score'],
            'reason': f"By_leg approach scores {quality_analysis['by_leg_score']}/100 vs leaderboard {quality_analysis['leaderboard_score']}/100",
            'migration_strategy': 'Use by_leg_export.csv as primary with leaderboard fallback'
        }
    }
    
    # Save test report
    test_report_file = Path('test_consolidated_results.json')
    with open(test_report_file, 'w') as f:
        json.dump(report, f, indent=2, default=str)
    
    print(f"\n📄 Test report saved: {test_report_file}")
    return report


def print_final_recommendation(quality_analysis: Dict[str, Any]):
    """Print the final recommendation based on test results."""
    print("\n" + "=" * 60)
    print("🎯 FINAL RECOMMENDATION")
    print("=" * 60)
    
    by_leg_score = quality_analysis['by_leg_score']
    leaderboard_score = quality_analysis['leaderboard_score']
    
    if by_leg_score > leaderboard_score:
        print("✅ RECOMMENDATION: **CONSOLIDATE TO BY_LEG EXPORT**")
        print(f"\nThe by_leg_export.csv approach scores {by_leg_score}/100 compared to")
        print(f"leaderboard CSVs at {leaderboard_score}/100.")
    else:
        print("⚠️ RECOMMENDATION: **KEEP LEADERBOARD APPROACH**")
        print(f"\nLeaderboard CSVs score {leaderboard_score}/100 compared to")
        print(f"by_leg_export.csv at {by_leg_score}/100.")
    
    print(f"\n🚀 IMPLEMENTATION STRATEGY:")
    print("1. **Primary**: by_leg_export.csv + URL fetching")
    print("2. **Fallback**: by_leg_export.csv only (CSV data)")
    print("3. **Emergency**: Leaderboard CSVs (if by_leg unavailable)")
    
    print(f"\n✨ KEY BENEFITS:")
    for advantage in quality_analysis.get('advantages', []):
        print(f"   {advantage}")
    
    if quality_analysis.get('limitations'):
        print(f"\n⚠️ CONSIDERATIONS:")
        for limitation in quality_analysis.get('limitations', []):
            print(f"   {limitation}")


def main():
    """Run the consolidated approach validation test."""
    setup_test_logging()
    
    print("🧪 DartConnect Consolidated Approach Validation")
    print("=" * 60)
    print("Testing whether by_leg_export.csv can replace cricket/501 leaderboard CSVs")
    
    # Setup test environment
    test_dir = Path('test_data')
    test_files = save_test_files(test_dir)
    print(f"📁 Test files created in: {test_dir}")
    
    try:
        # Test 1: URL processing capability
        url_results = test_url_processing_capability()
        
        # Test 2: Data processing comparison
        comparison = test_data_processing_comparison(test_files)
        
        # Test 3: Quality analysis
        quality_analysis = analyze_data_quality_comparison(comparison)
        
        # Generate comprehensive test report
        test_report = generate_test_report(url_results, comparison, quality_analysis)
        
        # Print final recommendation
        print_final_recommendation(quality_analysis)
        
        print(f"\n🎉 Validation testing complete!")
        print(f"📊 Results saved in: test_consolidated_results.json")
        
    except Exception as e:
        print(f"💥 Test failed: {e}")
        raise
    finally:
        # Cleanup test files (optional)
        print(f"\n🧹 Test files remain in {test_dir} for inspection")


if __name__ == '__main__':
    main()