"""Data processing module for DartConnect Statistics Generator."""

import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime
import logging
from urllib.parse import urlparse

from .config import Config
from .url_fetcher import DartConnectURLFetcher


class DataProcessor:
    """Processes DartConnect league data and calculates statistics."""
    
    def __init__(self, config: Config):
        """
        Initialize data processor.
        
        Args:
            config: Configuration object
        """
        self.config = config
        self.data_config = config.get_data_processing_config()
        self.stats_config = config.get_statistics_config()
        self.logger = logging.getLogger(__name__)
        self.url_fetcher = DartConnectURLFetcher()
    
    def process_file(self, file_path: str) -> Dict[str, Any]:
        """
        Process DartConnect data file and return calculated statistics.
        
        Args:
            file_path: Path to the input data file
            
        Returns:
            Dictionary containing processed data and statistics
        """
        self.logger.info(f"Processing file: {file_path}")
        
        # Load data
        df = self._load_data(file_path)
        
        # Clean and validate data
        df = self._clean_data(df)
        
        # Calculate statistics
        statistics = self._calculate_statistics(df)
        
        # Generate derived metrics
        derived_metrics = self._calculate_derived_metrics(df)
        
        # Process URLs if available
        enhanced_data = self._process_dartconnect_urls(df)
        
        # Add cache statistics if URL processing was done
        cache_stats = {}
        if hasattr(self.url_fetcher, 'get_cache_stats'):
            cache_stats = self.url_fetcher.get_cache_stats()
        
        return {
            'raw_data': df,
            'statistics': statistics,
            'derived_metrics': derived_metrics,
            'enhanced_data': enhanced_data,
            'cache_stats': cache_stats,
            'summary': self._generate_summary(df, statistics),
            'processed_at': datetime.now().isoformat()
        }
    
    def _load_data(self, file_path: str) -> pd.DataFrame:
        """Load data from various file formats."""
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"Data file not found: {file_path}")
        
        # Determine file format and load accordingly
        if file_path.suffix.lower() == '.csv':
            df = pd.read_csv(file_path)
        elif file_path.suffix.lower() in ['.xlsx', '.xls']:
            df = pd.read_excel(file_path)
        else:
            raise ValueError(f"Unsupported file format: {file_path.suffix}")
        
        self.logger.info(f"Loaded {len(df)} rows from {file_path}")
        return df
    
    def _clean_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean and validate the data."""
        # Check if essential columns exist (flexible column names)
        column_mapping = self._map_columns(df.columns)
        
        # Rename columns to standard names
        df = df.rename(columns=column_mapping)
        
        # Create full player name if we have separate first/last names
        if 'player_name' not in df.columns and 'last_name' in df.columns:
            first_name = df.get('player_name', '') if 'player_name' in df.columns else ''
            last_name = df.get('last_name', '') if 'last_name' in df.columns else ''
            # For DartConnect exports, often the last name column contains "Last, F" format
            # Check what the actual first name column is called after mapping
            first_name_col = 'player_name' if 'player_name' in df.columns else 'First Name'
            df['player_name'] = df.apply(lambda row: 
                self._create_full_name(row.get('last_name', ''), row.get(first_name_col, '')), axis=1)
        
        # Remove rows with missing essential data
        essential_columns = ['player_name'] if 'player_name' in df.columns else []
        if 'game_date' in df.columns:
            essential_columns.append('game_date')
        
        if essential_columns:
            df = df.dropna(subset=essential_columns)
        
        # Convert date column to datetime
        try:
            df['game_date'] = pd.to_datetime(df['game_date'])
        except Exception as e:
            self.logger.warning(f"Could not parse dates: {e}")
        
        # Convert numeric columns (only if they exist)
        numeric_columns = ['score', 'average', 'checkout_percentage', 'games_played']
        for col in numeric_columns:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        self.logger.info(f"Cleaned data: {len(df)} rows remaining")
        return df
    
    def _map_columns(self, columns: List[str]) -> Dict[str, str]:
        """Map DartConnect column names to standard names."""
        column_mapping = {}
        
        # Common DartConnect column patterns
        patterns = {
            'player_name': ['player', 'name', 'player_name', 'playername', 'first name'],
            'last_name': ['last name, fi', 'lastname', 'last_name'],
            'game_date': ['date', 'game_date', 'gamedate', 'match_date'],
            'score': ['score', 'total_score', 'points', 'pts/marks'],
            'average': ['avg', 'average', 'dart_average', '3da'],
            'checkout_percentage': ['checkout', 'checkout_pct', 'checkout_percentage'],
            'games_played': ['games', 'games_played', 'matches'],
            'game_name': ['game name', 'game_name', 'game_type'],
            'win': ['win', 'result', 'w/l'],
            'darts': ['darts', 'dart_count'],
            'report_url': ['report link', 'report_link', 'report_url'],
            'event_url': ['event link', 'event_link', 'event_url']
        }
        
        for standard_name, possible_names in patterns.items():
            for col in columns:
                if col.lower() in [name.lower() for name in possible_names]:
                    column_mapping[col] = standard_name
                    break
        
        return column_mapping
    
    def _calculate_statistics(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Calculate basic statistics from the data."""
        stats = {}
        
        if 'player_name' in df.columns:
            # Player statistics (only include columns that exist)
            agg_dict = {'player_name': 'count'}  # Always available
            if 'score' in df.columns:
                agg_dict['score'] = ['count', 'mean', 'std', 'min', 'max']
            if 'average' in df.columns:
                agg_dict['average'] = ['mean', 'std']
            if 'checkout_percentage' in df.columns:
                agg_dict['checkout_percentage'] = ['mean']
            
            player_stats = df.groupby('player_name').agg(agg_dict).round(self.data_config.get('decimal_places', 2))
            
            stats['player_statistics'] = player_stats
            
            # Overall league statistics
            if 'score' in df.columns:
                stats['league_statistics'] = {
                    'total_games': len(df),
                    'total_players': df['player_name'].nunique(),
                    'average_score': df['score'].mean(),
                    'highest_score': df['score'].max(),
                    'lowest_score': df['score'].min()
                }
        
        # Time-based statistics
        if 'game_date' in df.columns:
            stats['time_statistics'] = self._calculate_time_statistics(df)
        
        return stats
    
    def _calculate_derived_metrics(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Calculate derived metrics and advanced statistics."""
        metrics = {}
        
        if 'player_name' in df.columns and 'score' in df.columns:
            # Player rankings
            player_summary = df.groupby('player_name').agg({
                'score': ['count', 'mean', 'sum']
            }).round(self.data_config.get('decimal_places', 2))
            
            # Flatten column names
            player_summary.columns = ['games_played', 'average_score', 'total_score']
            
            # Filter players with minimum games
            min_games = self.data_config.get('min_games_threshold', 5)
            qualified_players = player_summary[player_summary['games_played'] >= min_games]
            
            # Rankings
            metrics['rankings'] = {
                'by_average': qualified_players.sort_values('average_score', ascending=False),
                'by_total': qualified_players.sort_values('total_score', ascending=False),
                'by_games': qualified_players.sort_values('games_played', ascending=False)
            }
            
            # Performance trends
            if self.stats_config.get('calculate_trends', True):
                metrics['trends'] = self._calculate_trends(df)
            
            # Percentile calculations
            if self.stats_config.get('calculate_percentiles', True):
                metrics['percentiles'] = self._calculate_percentiles(df)
        
        return metrics
    
    def _calculate_time_statistics(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Calculate time-based statistics."""
        time_stats = {}
        
        # Games per month/week
        df['month'] = df['game_date'].dt.to_period('M')
        df['week'] = df['game_date'].dt.to_period('W')
        
        time_stats['games_per_month'] = df.groupby('month').size().to_dict()
        time_stats['games_per_week'] = df.groupby('week').size().to_dict()
        
        # Recent activity (last 30 days)
        recent_cutoff = df['game_date'].max() - pd.Timedelta(days=30)
        recent_games = df[df['game_date'] >= recent_cutoff]
        
        time_stats['recent_activity'] = {
            'total_games': len(recent_games),
            'active_players': recent_games['player_name'].nunique() if 'player_name' in df.columns else 0,
            'games_per_day': len(recent_games) / 30
        }
        
        return time_stats
    
    def _calculate_trends(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Calculate performance trends for players."""
        trends = {}
        
        if 'player_name' in df.columns and 'score' in df.columns and 'game_date' in df.columns:
            window = self.stats_config.get('rolling_window_games', 10)
            
            for player in df['player_name'].unique():
                player_data = df[df['player_name'] == player].sort_values('game_date')
                
                if len(player_data) >= window:
                    player_data['rolling_avg'] = player_data['score'].rolling(window=window).mean()
                    
                    # Calculate trend direction
                    recent_avg = player_data['rolling_avg'].tail(window//2).mean()
                    earlier_avg = player_data['rolling_avg'].head(window//2).mean()
                    
                    trends[player] = {
                        'trend_direction': 'improving' if recent_avg > earlier_avg else 'declining',
                        'recent_average': recent_avg,
                        'earlier_average': earlier_avg,
                        'improvement_rate': ((recent_avg - earlier_avg) / earlier_avg * 100) if earlier_avg > 0 else 0
                    }
        
        return trends
    
    def _calculate_percentiles(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Calculate percentile statistics."""
        percentiles = {}
        
        if 'score' in df.columns:
            score_percentiles = np.percentile(df['score'].dropna(), [25, 50, 75, 90, 95])
            percentiles['score_percentiles'] = {
                '25th': score_percentiles[0],
                '50th': score_percentiles[1],
                '75th': score_percentiles[2],
                '90th': score_percentiles[3],
                '95th': score_percentiles[4]
            }
        
        return percentiles
    
    def _generate_summary(self, df: pd.DataFrame, stats: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a summary of the processed data."""
        summary = {
            'total_records': len(df),
            'date_range': {
                'start': df['game_date'].min().isoformat() if 'game_date' in df.columns else None,
                'end': df['game_date'].max().isoformat() if 'game_date' in df.columns else None
            },
            'data_quality': {
                'missing_values': df.isnull().sum().to_dict(),
                'duplicate_rows': df.duplicated().sum()
            }
        }
        
        return summary
    
    def _create_full_name(self, last_name_field: str, first_name_field: str) -> str:
        """Create full name from DartConnect name fields."""
        if not last_name_field and not first_name_field:
            return ''
        
        # Handle "Last, F" format common in DartConnect exports
        if last_name_field and ',' in last_name_field:
            parts = last_name_field.split(',')
            last_name = parts[0].strip()
            first_initial = parts[1].strip() if len(parts) > 1 else ''
            
            # Use full first name if available, otherwise use initial
            if first_name_field.strip():
                return f"{first_name_field.strip()} {last_name}"
            else:
                return f"{first_initial} {last_name}" if first_initial else last_name
        
        # Standard first + last name combination
        first = first_name_field.strip() if first_name_field else ''
        last = last_name_field.strip() if last_name_field else ''
        return f"{first} {last}".strip()
    
    def _process_dartconnect_urls(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Process DartConnect URLs to fetch detailed game data."""
        enhanced_data = {
            'urls_processed': 0,
            'urls_failed': 0,
            'enhanced_games': [],
            'cricket_qp_data': [],
            'enhanced_statistics': {}
        }
        
        if 'report_url' not in df.columns:
            self.logger.info("No report URLs found in data")
            return enhanced_data
        
        # Get unique URLs to avoid duplicate fetching
        unique_urls = df[df['report_url'].notna()]['report_url'].unique()
        
        self.logger.info(f"Processing {len(unique_urls)} unique DartConnect URLs")
        
        url_to_game_data = {}
        
        # Fetch detailed data for each URL
        for url in unique_urls:
            try:
                # Convert match report URL to game URL format if needed
                game_url = self._convert_to_game_url(url)
                game_data = self.url_fetcher.fetch_game_data(game_url)
                
                if game_data:
                    url_to_game_data[url] = game_data
                    enhanced_data['urls_processed'] += 1
                    
                    # Extract Cricket games for enhanced QP calculation
                    cricket_games = self.url_fetcher.extract_cricket_stats(game_data)
                    if cricket_games:
                        enhanced_data['cricket_qp_data'].extend(cricket_games)
                else:
                    enhanced_data['urls_failed'] += 1
                    
            except Exception as e:
                self.logger.error(f"Failed to process URL {url}: {e}")
                enhanced_data['urls_failed'] += 1
        
        # Enhanced quality point calculations for Cricket games
        if enhanced_data['cricket_qp_data']:
            enhanced_data['enhanced_statistics'] = self._calculate_enhanced_qp_stats(
                df, enhanced_data['cricket_qp_data']
            )
        
        # Store enhanced games data
        enhanced_data['enhanced_games'] = list(url_to_game_data.values())
        
        self.logger.info(f"Enhanced data processing complete: "
                        f"{enhanced_data['urls_processed']} successful, "
                        f"{enhanced_data['urls_failed']} failed")
        
        return enhanced_data
    
    def _convert_to_game_url(self, report_url: str) -> str:
        """Convert DartConnect report URL to game URL format."""
        if '/history/report/match/' in report_url:
            # Extract match ID from report URL
            match_id = report_url.split('/history/report/match/')[-1]
            # Convert to game URL format expected by url_fetcher
            return f"https://recap.dartconnect.com/games/{match_id}"
        return report_url
    
    def _calculate_enhanced_qp_stats(self, df: pd.DataFrame, cricket_games: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate enhanced quality point statistics using detailed game data."""
        enhanced_stats = {
            'cricket_enhanced_qp': {},
            'player_enhanced_stats': {},
            'qp_distribution': {}
        }
        
        # Create player QP tracking
        player_qp_totals = {}
        
        for game in cricket_games:
            for player_stats in game.get('players', []):
                player_name = player_stats.get('name')
                if not player_name:
                    continue
                
                # Calculate enhanced Cricket QP using detailed data
                qp = self.url_fetcher.calculate_cricket_qp(player_stats)
                
                if player_name not in player_qp_totals:
                    player_qp_totals[player_name] = {
                        'total_qp': 0,
                        'cricket_games': 0,
                        'enhanced_games': 0
                    }
                
                player_qp_totals[player_name]['total_qp'] += qp
                player_qp_totals[player_name]['cricket_games'] += 1
                player_qp_totals[player_name]['enhanced_games'] += 1
        
        # Calculate QP distribution
        qp_values = [stats['total_qp'] for stats in player_qp_totals.values()]
        if qp_values:
            enhanced_stats['qp_distribution'] = {
                'mean': np.mean(qp_values),
                'std': np.std(qp_values),
                'min': np.min(qp_values),
                'max': np.max(qp_values),
                'percentiles': {
                    '25th': np.percentile(qp_values, 25),
                    '50th': np.percentile(qp_values, 50),
                    '75th': np.percentile(qp_values, 75)
                }
            }
        
        enhanced_stats['cricket_enhanced_qp'] = player_qp_totals
        
        return enhanced_stats
