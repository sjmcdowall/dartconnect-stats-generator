#!/usr/bin/env python3
"""
Enhanced integration example showing complete DartConnect URL processing.

This demonstrates the integrated data processing pipeline that:
1. Loads DartConnect CSV exports 
2. Extracts report URLs from the "Report Link" column
3. Fetches detailed game data for enhanced Quality Point calculations
4. Generates comprehensive statistics including Cricket QP analysis
"""

from pathlib import Path
from src.config import Config
from src.data_processor import DataProcessor
from src.pdf_generator import PDFGenerator
from src.url_fetcher import DartConnectURLFetcher
import json
import pandas as pd


def main():
    """Run the complete enhanced statistics generation pipeline."""
    print("🎯 DartConnect Enhanced Statistics Generator")
    print("=" * 60)
    
    # Initialize configuration
    config = Config()
    
    # Use the actual DartConnect export file
    data_file = "docs/samples/dartconnect_exports/Fall_Winter_2025_By_Leg_export.csv"
    
    if not Path(data_file).exists():
        print(f"❌ Sample data file not found: {data_file}")
        print("Please ensure the DartConnect export file exists.")
        return
    
    # Process the data with enhanced URL fetching
    processor = DataProcessor(config)
    try:
        print(f"🔄 Processing DartConnect export: {Path(data_file).name}")
        results = processor.process_file(data_file)
        print(f"✅ Successfully processed {len(results['raw_data'])} records")
        
        # Display basic statistics
        display_basic_stats(results)
        
        # Display enhanced URL processing results
        display_enhanced_stats(results)
        
        # Display top players from both basic and enhanced data
        display_player_rankings(results)
        
        # Generate enhanced PDF report
        generate_reports(results, config)
        
    except Exception as e:
        print(f"❌ Error processing data: {e}")
        raise


def display_basic_stats(results):
    """Display basic statistics from the processed data."""
    print("\n📊 Basic Statistics:")
    print("-" * 30)
    
    stats = results.get('statistics', {})
    raw_data = results.get('raw_data')
    
    if 'league_statistics' in stats:
        league_stats = stats['league_statistics']
        print(f"Total Games: {league_stats.get('total_games', 'N/A')}")
        print(f"Total Players: {league_stats.get('total_players', 'N/A')}")
        print(f"Average Score: {league_stats.get('average_score', 'N/A'):.1f}")
    
    # Show game type breakdown
    if raw_data is not None and 'game_name' in raw_data.columns:
        game_types = raw_data['game_name'].value_counts()
        print(f"\nGame Types:")
        for game_type, count in game_types.head().items():
            print(f"  {game_type}: {count} games")


def display_enhanced_stats(results):
    """Display enhanced statistics from URL processing."""
    enhanced = results.get('enhanced_data', {})
    if not enhanced:
        print("\n⚠️  No enhanced data available (URL processing may have failed)")
        return
    
    print("\n🔗 Enhanced URL Processing Results:")
    print("-" * 40)
    print(f"URLs Processed: {enhanced.get('urls_processed', 0)}")
    print(f"URLs Failed: {enhanced.get('urls_failed', 0)}")
    print(f"Cricket Games Enhanced: {len(enhanced.get('cricket_qp_data', []))}")
    
    # Calculate success rate
    total_urls = enhanced.get('urls_processed', 0) + enhanced.get('urls_failed', 0)
    if total_urls > 0:
        success_rate = (enhanced.get('urls_processed', 0) / total_urls) * 100
        print(f"Success Rate: {success_rate:.1f}%")
    
    # Display enhanced Cricket QP statistics
    enhanced_stats = enhanced.get('enhanced_statistics', {})
    if 'cricket_enhanced_qp' in enhanced_stats:
        display_cricket_qp_analysis(enhanced_stats)


def display_cricket_qp_analysis(enhanced_stats):
    """Display detailed Cricket QP analysis."""
    cricket_qp = enhanced_stats['cricket_enhanced_qp']
    
    print(f"\n🏏 Enhanced Cricket QP Analysis:")
    print("-" * 40)
    print(f"Players Analyzed: {len(cricket_qp)}")
    
    if not cricket_qp:
        print("No Cricket QP data available")
        return
    
    # Show top QP earners
    sorted_players = sorted(
        cricket_qp.items(), 
        key=lambda x: x[1]['total_qp'], 
        reverse=True
    )
    
    print(f"\n🏆 Top 10 Cricket QP Earners:")
    for i, (player, stats) in enumerate(sorted_players[:10], 1):
        avg_qp = stats['total_qp'] / max(stats['enhanced_games'], 1)
        print(f"{i:2d}. {player}: {stats['total_qp']} QP "
              f"({avg_qp:.1f} avg, {stats['enhanced_games']} games)")
    
    # Show QP distribution
    qp_dist = enhanced_stats.get('qp_distribution', {})
    if qp_dist:
        print(f"\n📊 QP Distribution Statistics:")
        print(f"Mean: {qp_dist.get('mean', 0):.1f}")
        print(f"Range: {qp_dist.get('min', 0):.0f} - {qp_dist.get('max', 0):.0f}")
        print(f"Median: {qp_dist.get('percentiles', {}).get('50th', 0):.1f}")
        print(f"75th Percentile: {qp_dist.get('percentiles', {}).get('75th', 0):.1f}")


def display_player_rankings(results):
    """Display player rankings from both basic and enhanced data."""
    print(f"\n🏆 Player Rankings:")
    print("-" * 30)
    
    # Basic rankings
    derived = results.get('derived_metrics', {})
    rankings = derived.get('rankings', {})
    
    if 'by_average' in rankings and not rankings['by_average'].empty:
        print("Top 5 by Average Score (Basic Stats):")
        top_by_avg = rankings['by_average'].head(5)
        for i, (player, stats) in enumerate(top_by_avg.iterrows(), 1):
            print(f"{i}. {player}: {stats['average_score']:.1f} avg "
                  f"({stats['games_played']} games)")
    
    # Enhanced QP rankings (if available)
    enhanced_stats = results.get('enhanced_data', {}).get('enhanced_statistics', {})
    if 'cricket_enhanced_qp' in enhanced_stats:
        cricket_qp = enhanced_stats['cricket_enhanced_qp']
        if cricket_qp:
            print(f"\nTop 5 by Cricket QP (Enhanced):")
            sorted_qp = sorted(cricket_qp.items(), key=lambda x: x[1]['total_qp'], reverse=True)
            for i, (player, stats) in enumerate(sorted_qp[:5], 1):
                avg_qp = stats['total_qp'] / max(stats['enhanced_games'], 1)
                print(f"{i}. {player}: {stats['total_qp']} QP "
                      f"({avg_qp:.1f} avg)")


def generate_reports(results, config):
    """Generate PDF and JSON reports."""
    print("\n📄 Generating Reports:")
    print("-" * 25)
    
    try:
        # Generate PDF report
        print("🔄 Generating PDF report...")
        pdf_generator = PDFGenerator(config)
        pdf_file = "enhanced_dart_league_report.pdf"
        pdf_generator.generate_report(results, pdf_file)
        print(f"✅ PDF report generated: {pdf_file}")
        
        # Save detailed JSON results
        print("🔄 Saving detailed JSON results...")
        json_file = "enhanced_processed_results.json"
        save_json_results(results, json_file)
        print(f"✅ Detailed results saved: {json_file}")
        
    except Exception as e:
        print(f"❌ Error generating reports: {e}")


def save_json_results(results, filename):
    """Save results to JSON with proper serialization."""
    json_results = results.copy()
    
    # Convert DataFrame to dict
    if 'raw_data' in json_results and hasattr(json_results['raw_data'], 'to_dict'):
        json_results['raw_data'] = json_results['raw_data'].to_dict('records')
    
    # Convert DataFrames in derived metrics
    if 'derived_metrics' in json_results:
        derived = json_results['derived_metrics']
        if 'rankings' in derived:
            for key, df in derived['rankings'].items():
                if hasattr(df, 'to_dict'):
                    derived['rankings'][key] = df.to_dict('index')
    
    # Save with pretty formatting
    with open(filename, 'w') as f:
        json.dump(json_results, f, indent=2, default=str)


def demo_url_processing():
    """Demonstrate URL processing with sample URLs from the CSV."""
    print("\n🔍 URL Processing Demo:")
    print("-" * 30)
    
    # Sample URLs from the actual CSV data
    sample_urls = [
        "https://recap.dartconnect.com/history/report/match/68aba095f978cb217a4c5457",
        "https://recap.dartconnect.com/history/report/match/68ab9f42f978cb217a4c5308",
        "https://recap.dartconnect.com/history/report/match/68aba220f978cb217a4c55cb"
    ]
    
    fetcher = DartConnectURLFetcher()
    
    for i, report_url in enumerate(sample_urls, 1):
        print(f"\n🎯 Testing URL {i}:")
        
        # Convert to game URL format
        game_url = report_url.replace('/history/report/match/', '/games/')
        print(f"URL: {game_url}")
        
        try:
            game_data = fetcher.fetch_game_data(game_url)
            if game_data:
                print("✅ Successfully fetched data")
                
                # Extract Cricket games
                cricket_games = fetcher.extract_cricket_stats(game_data)
                print(f"🏏 Found {len(cricket_games)} Cricket games")
                
                # Show sample QP calculation
                for game in cricket_games[:1]:  # Show first game only
                    for player in game.get('players', [])[:2]:  # Show first 2 players
                        qp = fetcher.calculate_cricket_qp(player)
                        name = player.get('name', 'Unknown')
                        bulls = player.get('total_bulls', 0)
                        marks = player.get('ending_marks', 0)
                        print(f"  👤 {name}: {qp} QP (Bulls: {bulls}, Marks: {marks})")
            else:
                print("❌ Failed to fetch data")
                
        except Exception as e:
            print(f"❌ Error: {e}")


def show_integration_summary():
    """Show summary of integration capabilities."""
    print("\n" + "=" * 60)
    print("🚀 INTEGRATION SUMMARY")
    print("=" * 60)
    
    print("\n✅ CAPABILITIES:")
    print("• Automatic URL extraction from DartConnect CSV exports")
    print("• Detailed game data fetching from DartConnect recap URLs") 
    print("• Enhanced Cricket QP calculations using Bulls + Marks")
    print("• 501 QP calculations with total score + checkout bonuses")
    print("• Player performance analytics with detailed statistics")
    print("• PDF report generation with enhanced data")
    print("• JSON export for further analysis")
    
    print("\n🔧 TECHNICAL FEATURES:")
    print("• Robust URL format handling (both /games/ and /history/report/match/)")
    print("• Turn-by-turn game analysis")
    print("• Bulls counting (SB and DB) for Cricket QPs")
    print("• Error handling and retry logic")
    print("• Efficient batch processing of multiple URLs")
    print("• Data validation and quality checks")
    
    print("\n📊 DATA ENHANCEMENTS:")
    print("• Cricket: Bulls data not available in CSV exports")
    print("• 501: Checkout detection for bonus QPs")
    print("• Match-level statistics (duration, MPR, etc.)")
    print("• Player improvement tracking")
    print("• League-wide performance analysis")


if __name__ == "__main__":
    main()
    print("\n" + "=" * 60)
    
    # Ask if user wants to see the URL processing demo
    try:
        response = input("\n🤔 Would you like to see the URL processing demo? (y/n): ").lower()
        if response in ['y', 'yes']:
            demo_url_processing()
    except (KeyboardInterrupt, EOFError):
        pass
    
    show_integration_summary()
    print("\n✅ Integration example complete!")