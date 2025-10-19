#!/usr/bin/env python3
"""
DartConnect Statistics Generator - Consolidated Approach

This version primarily uses _by_leg_export.csv with URL fetching for enhanced
statistics, with intelligent fallback to leaderboard CSVs when needed.
"""

import argparse
import sys
from pathlib import Path
import logging
from typing import Optional, Dict, Any

from src.config import Config
from src.data_processor import DataProcessor
from src.pdf_generator import PDFGenerator


def setup_logging(verbose: bool = False):
    """Setup logging configuration."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )


def find_data_files(data_dir: Path) -> Dict[str, Optional[Path]]:
    """
    Automatically find DartConnect export files.
    
    Priority order:
    1. *_by_leg_export.csv (preferred - has URLs)
    2. *_cricket_leaderboard.csv (fallback)
    3. *_501_leaderboard.csv (fallback)
    """
    files = {
        'by_leg': None,
        'cricket_leaderboard': None,
        'dart_501_leaderboard': None
    }
    
    if not data_dir.exists():
        return files
    
    # Search for files with common DartConnect naming patterns
    csv_files = list(data_dir.glob('*.csv'))
    
    for csv_file in csv_files:
        name_lower = csv_file.name.lower()
        
        if ('by_leg' in name_lower or 'by leg' in name_lower) and 'archived' not in name_lower:
            # Always use the newest by_leg file (in case there are multiple)
            if files['by_leg'] is None or csv_file.stat().st_mtime > files['by_leg'].stat().st_mtime:
                files['by_leg'] = csv_file
        elif 'cricket' in name_lower and 'leaderboard' in name_lower:
            files['cricket_leaderboard'] = csv_file
        elif '501' in name_lower and 'leaderboard' in name_lower:
            files['dart_501_leaderboard'] = csv_file
    
    # Log which files were found
    import logging
    logger = logging.getLogger(__name__)
    
    for file_type, file_path in files.items():
        if file_path:
            timestamp = file_path.stat().st_mtime
            import datetime
            readable_time = datetime.datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')
            logger.info(f"📄 Found {file_type} file: {file_path.name} (modified: {readable_time})")
    
    return files


def assess_data_quality(results: Dict[str, Any]) -> Dict[str, Any]:
    """Assess the quality and completeness of processed data."""
    assessment = {
        'data_source': 'unknown',
        'quality_score': 0,
        'features_available': [],
        'limitations': [],
        'recommendation': ''
    }
    
    enhanced_data = results.get('enhanced_data', {})
    raw_data = results.get('raw_data')
    
    # Check if URL processing was successful
    urls_processed = enhanced_data.get('urls_processed', 0)
    urls_failed = enhanced_data.get('urls_failed', 0)
    total_urls = urls_processed + urls_failed
    
    if total_urls > 0:
        url_success_rate = urls_processed / total_urls
        if url_success_rate >= 0.8:
            assessment['data_source'] = 'by_leg_with_urls'
            assessment['quality_score'] = 95
            assessment['features_available'] = [
                'Accurate Cricket QPs with Bulls data',
                'Complete 501 QPs with checkout bonuses',
                'Game-by-game analysis',
                'Performance trends',
                'Turn-by-turn statistics'
            ]
            assessment['recommendation'] = 'Excellent data quality - all features available'
        elif url_success_rate >= 0.5:
            assessment['data_source'] = 'by_leg_partial_urls'
            assessment['quality_score'] = 75
            assessment['features_available'] = [
                'Partial Cricket QP enhancement',
                'Basic statistics from CSV',
                'Some game-level data'
            ]
            assessment['limitations'] = [
                f'Only {url_success_rate:.1%} URL success rate',
                'Some QP calculations may be incomplete'
            ]
            assessment['recommendation'] = 'Good data quality with some limitations'
        else:
            assessment['data_source'] = 'by_leg_csv_only'
            assessment['quality_score'] = 60
            assessment['limitations'] = [
                'URL processing mostly failed',
                'Cricket QPs may be incomplete (missing bulls data)',
                '501 checkout bonuses may be missing'
            ]
    else:
        # No URLs available - likely using leaderboard CSVs
        assessment['data_source'] = 'leaderboard_csvs'
        assessment['quality_score'] = 50
        assessment['features_available'] = [
            'Basic player statistics',
            'Season summaries',
            'Standard QP calculations'
        ]
        assessment['limitations'] = [
            'No game-by-game analysis',
            'Cricket QPs incomplete (no bulls data)',
            'Limited 501 checkout detection',
            'No performance trends'
        ]
        assessment['recommendation'] = 'Consider using by_leg_export.csv for enhanced features'
    
    return assessment


def process_data_with_fallback(data_files: Dict[str, Optional[Path]], config: Config) -> Dict[str, Any]:
    """
    Process data with intelligent fallback strategy.
    
    Priority:
    1. by_leg_export.csv + URL fetching (preferred)
    2. by_leg_export.csv only (if URLs fail)
    3. Leaderboard CSVs (if by_leg not available)
    """
    processor = DataProcessor(config)
    logger = logging.getLogger(__name__)
    
    # Strategy 1: Enhanced processing with by_leg export
    if data_files['by_leg']:
        logger.info(f"🎯 Primary strategy: Processing {data_files['by_leg'].name} with URL enhancement")
        try:
            results = processor.process_file(str(data_files['by_leg']))
            assessment = assess_data_quality(results)
            
            if assessment['quality_score'] >= 75:
                logger.info(f"✅ High quality results achieved (score: {assessment['quality_score']})")
                results['processing_strategy'] = 'by_leg_with_urls'
                results['quality_assessment'] = assessment
                return results
            else:
                logger.warning(f"⚠️ URL processing had issues (score: {assessment['quality_score']})")
                logger.info("Results still usable, continuing with current data...")
                results['processing_strategy'] = 'by_leg_partial'
                results['quality_assessment'] = assessment
                return results
                
        except Exception as e:
            logger.error(f"❌ Enhanced processing failed: {e}")
            logger.info("Falling back to alternative strategies...")
    
    # Strategy 2: Use leaderboard CSVs if available
    if data_files['cricket_leaderboard'] or data_files['dart_501_leaderboard']:
        logger.info("🔄 Fallback strategy: Using leaderboard CSV files")
        
        # For now, we'll process the available leaderboard file
        # In a full implementation, you'd want to merge both cricket and 501 data
        primary_file = data_files['cricket_leaderboard'] or data_files['dart_501_leaderboard']
        
        try:
            results = processor.process_file(str(primary_file))
            assessment = assess_data_quality(results)
            results['processing_strategy'] = 'leaderboard_fallback'
            results['quality_assessment'] = assessment
            logger.warning("⚠️ Using fallback processing - some features may be limited")
            return results
            
        except Exception as e:
            logger.error(f"❌ Fallback processing failed: {e}")
    
    # Strategy 3: Error - no usable data found
    raise FileNotFoundError("No usable DartConnect data files found")


def generate_reports(results: Dict[str, Any], config: Config, output_dir: Path) -> None:
    """Generate PDF reports and save JSON results."""
    logger = logging.getLogger(__name__)
    
    try:
        # Create output directory
        output_dir.mkdir(exist_ok=True)
        
        # Generate PDF reports
        logger.info("📄 Generating PDF reports...")
        pdf_generator = PDFGenerator(config, str(output_dir))
        
        # Generate league statistics report
        overall_file = pdf_generator.generate_overall_report(results)
        logger.info(f"✅ Overall report saved: {overall_file}")
        
        # Generate player performance report 
        individual_file = pdf_generator.generate_individual_report(results)
        logger.info(f"✅ Individual report saved: {individual_file}")
        
        # Save detailed JSON results for debugging/analysis
        json_file = output_dir / "processed_results.json"
        save_json_results(results, json_file)
        logger.info(f"✅ Detailed results saved: {json_file}")
        
        # Print summary report
        print_processing_summary(results)
        
    except Exception as e:
        logger.error(f"❌ Report generation failed: {e}")
        raise


def save_json_results(results: Dict[str, Any], json_file: Path) -> None:
    """Save results to JSON with proper serialization."""
    import json
    import pandas as pd
    import numpy as np
    import logging
    from datetime import datetime, date
    
    def flatten_multiindex_columns(df):
        """Flatten MultiIndex columns to strings to avoid tuple key issues."""
        if hasattr(df.columns, 'levels'):  # MultiIndex columns
            df = df.copy()
            df.columns = ['_'.join(map(str, col)) if isinstance(col, tuple) else str(col) for col in df.columns]
        return df
    
    def json_serializer(obj):
        """Custom JSON serializer for pandas and numpy objects."""
        if isinstance(obj, pd.DataFrame):
            # Flatten MultiIndex columns first
            obj_flat = flatten_multiindex_columns(obj)
            return obj_flat.to_dict('records')
        elif isinstance(obj, pd.Series):
            return obj.to_dict()
        elif isinstance(obj, (pd.Timestamp, pd.Period)):
            return str(obj)
        elif isinstance(obj, (datetime, date)):
            return obj.isoformat()
        elif isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        elif isinstance(obj, tuple):
            return str(obj)  # Convert tuples to strings
        elif hasattr(obj, '__dict__'):
            return str(obj)
        else:
            return str(obj)
    
    def clean_data_structure(obj):
        """Recursively clean data structures to remove problematic types."""
        if isinstance(obj, dict):
            cleaned = {}
            for key, value in obj.items():
                # Convert tuple keys to strings
                str_key = str(key) if isinstance(key, tuple) else key
                cleaned[str_key] = clean_data_structure(value)
            return cleaned
        elif isinstance(obj, list):
            return [clean_data_structure(item) for item in obj]
        elif isinstance(obj, pd.DataFrame):
            # Flatten MultiIndex columns and convert to dict
            obj_flat = flatten_multiindex_columns(obj)
            return obj_flat.to_dict('index')
        else:
            return obj
    
    json_results = clean_data_structure(results.copy())
    
    # Convert remaining DataFrames to dictionaries with proper handling
    if 'raw_data' in json_results and hasattr(json_results['raw_data'], 'to_dict'):
        json_results['raw_data'] = flatten_multiindex_columns(json_results['raw_data']).to_dict('records')
    
    if 'derived_metrics' in json_results and 'rankings' in json_results['derived_metrics']:
        rankings = json_results['derived_metrics']['rankings']
        for key, df in rankings.items():
            if hasattr(df, 'to_dict'):
                rankings[key] = flatten_multiindex_columns(df).to_dict('index')
    
    # Convert any player statistics DataFrames
    if 'statistics' in json_results and 'player_statistics' in json_results['statistics']:
        player_stats = json_results['statistics']['player_statistics']
        if hasattr(player_stats, 'to_dict'):
            json_results['statistics']['player_statistics'] = flatten_multiindex_columns(player_stats).to_dict('index')
    
    # Save with robust serialization
    try:
        with open(json_file, 'w') as f:
            json.dump(json_results, f, indent=2, default=json_serializer)
    except Exception as e:
        # If JSON serialization still fails, save a simplified version
        logger = logging.getLogger(__name__)
        logger.warning(f"Full JSON serialization failed: {e}. Saving simplified version.")
        simplified_results = {
            'processing_strategy': json_results.get('processing_strategy', 'unknown'),
            'quality_assessment': json_results.get('quality_assessment', {}),
            'summary': json_results.get('summary', {}),
            'cache_stats': json_results.get('cache_stats', {}),
            'data_overview': {
                'total_records': len(json_results.get('raw_data', [])) if 'raw_data' in json_results else 0,
                'processing_errors': str(e)
            }
        }
        with open(json_file, 'w') as f:
            json.dump(simplified_results, f, indent=2, default=json_serializer)


def print_processing_summary(results: Dict[str, Any]) -> None:
    """Print a summary of the processing results."""
    print("\n" + "=" * 60)
    print("🎯 PROCESSING SUMMARY")
    print("=" * 60)
    
    # Processing strategy used
    strategy = results.get('processing_strategy', 'unknown')
    assessment = results.get('quality_assessment', {})
    
    print(f"\n📊 Data Source: {assessment.get('data_source', 'unknown').replace('_', ' ').title()}")
    print(f"🏆 Quality Score: {assessment.get('quality_score', 0)}/100")
    print(f"🔧 Strategy: {strategy.replace('_', ' ').title()}")
    
    # Basic statistics
    raw_data = results.get('raw_data')
    if raw_data is not None:
        print(f"\n📈 Data Overview:")
        print(f"  Total Records: {len(raw_data)}")
        if 'player_name' in raw_data.columns:
            print(f"  Unique Players: {raw_data['player_name'].nunique()}")
        if 'game_name' in raw_data.columns:
            game_types = raw_data['game_name'].value_counts()
            print(f"  Game Types: {', '.join([f'{game}: {count}' for game, count in game_types.head(3).items()])}")
    
    # URL processing results
    enhanced_data = results.get('enhanced_data', {})
    if enhanced_data:
        urls_processed = enhanced_data.get('urls_processed', 0)
        urls_failed = enhanced_data.get('urls_failed', 0)
        total_urls = urls_processed + urls_failed
        
        if total_urls > 0:
            print(f"\n🔗 URL Processing:")
            print(f"  URLs Processed: {urls_processed}/{total_urls}")
            success_rate = (urls_processed / total_urls) * 100
            print(f"  Success Rate: {success_rate:.1f}%")
            
            cricket_games = len(enhanced_data.get('cricket_qp_data', []))
            if cricket_games > 0:
                print(f"  Enhanced Cricket Games: {cricket_games}")
    
    # Cache statistics
    cache_stats = results.get('cache_stats', {})
    if cache_stats:
        print(f"\n💾 Cache Performance:")
        hits = cache_stats.get('hits', 0)
        misses = cache_stats.get('misses', 0)
        total_requests = hits + misses
        
        if total_requests > 0:
            hit_rate = (hits / total_requests) * 100
            print(f"  Cache Hits: {hits}")
            print(f"  Cache Misses: {misses}")
            print(f"  Hit Rate: {hit_rate:.1f}%")
            print(f"  New Fetches: {cache_stats.get('new_fetches', 0)}")
            print(f"  Expired: {cache_stats.get('expired', 0)}")
    
    # Quality assessment
    if 'features_available' in assessment and assessment['features_available']:
        print(f"\n✅ Available Features:")
        for feature in assessment['features_available']:
            print(f"  • {feature}")
    
    if 'limitations' in assessment and assessment['limitations']:
        print(f"\n⚠️ Limitations:")
        for limitation in assessment['limitations']:
            print(f"  • {limitation}")
    
    print(f"\n💡 Recommendation: {assessment.get('recommendation', 'N/A')}")


def main():
    """Main application entry point."""
    parser = argparse.ArgumentParser(
        description='DartConnect Statistics Generator - Consolidated Approach',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s data/                           # Auto-detect files in data directory
  %(prog)s data/by_leg_export.csv         # Process specific by_leg file
  %(prog)s --data-dir league_data         # Use custom data directory
  %(prog)s --config custom.yaml           # Use custom configuration
        """
    )
    
    parser.add_argument('input_path', nargs='?', default='data',
                        help='Path to data directory or specific CSV file (default: data/)')
    parser.add_argument('--config', '-c', type=str, default='config.yaml',
                        help='Configuration file path (default: config.yaml)')
    parser.add_argument('--output-dir', '-o', type=str, default='output',
                        help='Output directory for reports (default: output/)')
    parser.add_argument('--verbose', '-v', action='store_true',
                        help='Enable verbose logging')
    parser.add_argument('--data-dir', type=str,
                        help='Alternative to input_path for directory scanning')
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(args.verbose)
    logger = logging.getLogger(__name__)
    
    try:
        # Initialize configuration
        config_path = Path(args.config)
        if not config_path.exists():
            logger.warning(f"Configuration file not found: {config_path}, using defaults")
            config = Config()
        else:
            config = Config(str(config_path))
        
        # Determine input path
        input_path = Path(args.data_dir) if args.data_dir else Path(args.input_path)
        output_dir = Path(args.output_dir)
        
        logger.info(f"🚀 Starting DartConnect Statistics Generator")
        logger.info(f"📁 Input: {input_path}")
        logger.info(f"📤 Output: {output_dir}")
        
        # Process data files
        if input_path.is_file():
            # Single file provided - process directly
            logger.info(f"🎯 Processing single file: {input_path.name}")
            processor = DataProcessor(config)
            results = processor.process_file(str(input_path))
            results['processing_strategy'] = 'direct_file'
            results['quality_assessment'] = assess_data_quality(results)
        else:
            # Directory provided - auto-detect files with fallback strategy
            logger.info(f"🔍 Auto-detecting files in: {input_path}")
            data_files = find_data_files(input_path)
            
            # Log found files
            for file_type, file_path in data_files.items():
                if file_path:
                    logger.info(f"  Found {file_type}: {file_path.name}")
                else:
                    logger.debug(f"  Missing {file_type}")
            
            results = process_data_with_fallback(data_files, config)
        
        # Generate reports
        generate_reports(results, config, output_dir)
        
        logger.info("🎉 Processing completed successfully!")
        
    except KeyboardInterrupt:
        logger.info("👋 Processing interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"💥 Fatal error: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()