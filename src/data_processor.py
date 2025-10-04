"""Data processing module for DartConnect Statistics Generator."""

import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime
import logging

from .config import Config


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
        
        return {
            'raw_data': df,
            'statistics': statistics,
            'derived_metrics': derived_metrics,
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
        # Remove rows with missing essential data
        essential_columns = ['player_name', 'game_date']
        
        # Check if essential columns exist (flexible column names)
        column_mapping = self._map_columns(df.columns)
        
        # Rename columns to standard names
        df = df.rename(columns=column_mapping)
        
        # Remove rows with missing essential data
        df = df.dropna(subset=['player_name', 'game_date'])
        
        # Convert date column to datetime
        try:
            df['game_date'] = pd.to_datetime(df['game_date'])
        except Exception as e:
            self.logger.warning(f"Could not parse dates: {e}")
        
        # Convert numeric columns
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
            'player_name': ['player', 'name', 'player_name', 'playername'],
            'game_date': ['date', 'game_date', 'gamedate', 'match_date'],
            'score': ['score', 'total_score', 'points'],
            'average': ['avg', 'average', 'dart_average'],
            'checkout_percentage': ['checkout', 'checkout_pct', 'checkout_percentage'],
            'games_played': ['games', 'games_played', 'matches']
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
            # Player statistics
            player_stats = df.groupby('player_name').agg({
                'score': ['count', 'mean', 'std', 'min', 'max'] if 'score' in df.columns else 'count',
                'average': ['mean', 'std'] if 'average' in df.columns else None,
                'checkout_percentage': ['mean'] if 'checkout_percentage' in df.columns else None
            }).round(self.data_config.get('decimal_places', 2))
            
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