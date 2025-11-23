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

# Common name lists for gender inference
COMMON_MALE_NAMES = {
    "john","michael","david","james","robert","william","richard","thomas","charles","joseph",
    "christopher","daniel","matthew","anthony","mark","donald","steven","paul","andrew","joshua",
    "kenneth","kevin","brian","george","timothy","ronald","edward","jason","ryan","gary",
    "nicholas","eric","stephen","larry","justin","scott","brandon","benjamin","adam","samuel",
    "gregory","alexander","patrick","tyler","frank","peter","marc","marcus","matt","mike","jeff",
    "jeffrey","steve","bryan","bruce","shaun","sean","ian","craig","barry","dave","shane",
    "josh","lee","clifford","landon","blake","erston","chris","casey","bill","rodel","rick",
    "robbie","martin"
}

COMMON_FEMALE_NAMES = {
    "mary","patricia","jennifer","linda","elizabeth","barbara","susan","jessica","sarah","karen",
    "nancy","lisa","betty","margaret","sandra","ashley","kimberly","emily","donna","michelle",
    "carol","amanda","melissa","deborah","stephanie","rebecca","laura","sharon","cynthia","kathleen",
    "amy","angela","rachel","heather","nicole","christine","julie","anna","maria","victoria",
    "bonnie","bonny","samantha","megan","katherine","catherine","jenny","lindsay","lindsey","amber",
    "beth","betsy","jade","sherrie","shannon","misty"
}

# Unisex names to avoid guessing (removed casey, chris, lee since we have manual classifications)
UNISEX_NAMES = {
    "alex","sam","jordan","taylor","jamie","morgan","bailey","skyler","skye","cameron",
    "devon","drew","parker","reese","riley","sydney","syd","avery","quinn","kyle"
}

# Placeholder names to exclude from reports
PLACEHOLDER_NAMES = {
    "ghost","placeholder","test","dummy"
}


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

        # Generate comprehensive team statistics after all data is processed
        team_statistics = self.generate_team_statistics(df, enhanced_data)

        return {
            'raw_data': df,
            'statistics': statistics,
            'derived_metrics': derived_metrics,
            'enhanced_data': enhanced_data,
            'team_statistics': team_statistics,
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
        # Preserve First Name column before mapping (needed for gender inference)
        # Clean whitespace from First Name to ensure proper matching
        has_first_name = 'First Name' in df.columns
        if has_first_name:
            # Strip leading/trailing whitespace from first names
            df['First Name'] = df['First Name'].str.strip()
            df['_first_name_original'] = df['First Name']
        
        # Check if essential columns exist (flexible column names)
        column_mapping = self._map_columns(df.columns)
        
        # Rename columns to standard names
        df = df.rename(columns=column_mapping)
        
        # Create full player name from first and last names
        # If we have both last_name and player_name (which is currently first name), create full name
        if 'last_name' in df.columns:
            # player_name currently contains first name from mapping
            # We need to combine it with last_name to get full name
            if 'player_name' in df.columns:
                # Save first name temporarily
                df['first_name_temp'] = df['player_name']
                # Create full name using first name and last name
                df['player_name'] = df.apply(lambda row: 
                    self._create_full_name(row.get('last_name', ''), row.get('first_name_temp', '')), axis=1)
                # Clean up temp column
                df = df.drop(columns=['first_name_temp'])
            else:
                # If only last_name exists, use it as player_name
                df['player_name'] = df['last_name']
        
        # Remove rows with missing essential data
        essential_columns = ['player_name'] if 'player_name' in df.columns else []
        if 'game_date' in df.columns:
            essential_columns.append('game_date')
        
        if essential_columns:
            df = df.dropna(subset=essential_columns)
        
        # Filter out placeholder players
        if '_first_name_original' in df.columns:
            placeholder_mask = df['_first_name_original'].str.lower().isin(PLACEHOLDER_NAMES)
            if placeholder_mask.any():
                removed_count = placeholder_mask.sum()
                self.logger.info(f"🚫 Filtered out {removed_count} placeholder player records (e.g., Ghost Player)")
                df = df[~placeholder_mask]
        
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
        
        # Normalize gender per player (use most recent value)
        if 'M/F' in df.columns and 'player_name' in df.columns and 'game_date' in df.columns:
            df = self._normalize_player_gender(df)
        
        # Infer missing gender from first names
        if 'M/F' in df.columns and 'player_name' in df.columns and '_first_name_original' in df.columns:
            df = self._infer_missing_gender(df)
        
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
    
    def _normalize_player_gender(self, df: pd.DataFrame) -> pd.DataFrame:
        """Normalize gender per player by using the most recent non-empty value.
        
        This handles cases where a player's gender was incorrectly recorded in
        earlier games but corrected in later games. We take the gender from the
        most recent game as the authoritative value.
        """
        if df.empty or 'M/F' not in df.columns or 'player_name' not in df.columns:
            return df
        
        # Ensure game_date is datetime
        if 'game_date' not in df.columns:
            return df
        
        # Track corrections
        corrections = []
        
        # For each player, find their most recent gender value
        for player in df['player_name'].unique():
            player_mask = df['player_name'] == player
            player_df = df[player_mask].copy()
            
            # Get all non-empty gender values
            gender_values = player_df['M/F'].dropna()
            gender_values = gender_values[gender_values.str.strip() != '']
            
            if len(gender_values) == 0:
                continue  # No gender data for this player - will be handled by inference
            
            # Check if there are inconsistencies OR missing values for some rows
            unique_genders = gender_values.unique()
            has_missing = len(gender_values) < len(player_df)  # Some rows missing gender
            
            if len(unique_genders) > 1 or has_missing:
                # Sort by date (most recent first) and get the latest gender
                player_df_sorted = player_df.sort_values('game_date', ascending=False)
                latest_gender = None
                
                for idx, row in player_df_sorted.iterrows():
                    gender = row.get('M/F', '')
                    if pd.notna(gender) and str(gender).strip() != '':
                        latest_gender = str(gender).strip()
                        break
                
                if latest_gender:
                    # Count how many records will be changed
                    old_genders = player_df['M/F'].value_counts().to_dict()
                    corrections.append({
                        'player': player,
                        'old_values': old_genders,
                        'new_value': latest_gender,
                        'records_updated': len(player_df[player_df['M/F'] != latest_gender])
                    })
                    
                    # Update all records for this player
                    df.loc[player_mask, 'M/F'] = latest_gender
        
        # Log corrections
        if corrections:
            self.logger.info(f"🔧 Normalized gender for {len(corrections)} player(s) with inconsistent values:")
            for correction in corrections:
                old_vals_str = ', '.join([f"{k}({v})" for k, v in correction['old_values'].items()])
                self.logger.info(
                    f"  • {correction['player']}: {old_vals_str} → {correction['new_value']} "
                    f"({correction['records_updated']} records updated)"
                )
        
        return df
    
    def _infer_missing_gender(self, df: pd.DataFrame) -> pd.DataFrame:
        """Infer gender for players with missing M/F data based on first name.
        
        Uses common name lists to make educated guesses. Conservative approach:
        only infers when confident, avoids unisex names.
        """
        if df.empty or 'M/F' not in df.columns or '_first_name_original' not in df.columns:
            return df
        
        # Track inferences
        inferences = []
        
        # Find players with missing gender
        for player in df['player_name'].unique():
            player_mask = df['player_name'] == player
            player_df = df[player_mask]
            
            # Check if all rows for this player have missing gender
            gender_values = player_df['M/F'].dropna()
            gender_values = gender_values[gender_values.str.strip() != '']
            
            if len(gender_values) > 0:
                continue  # Player already has gender data
            
            # Get first name
            first_name = player_df['_first_name_original'].iloc[0]
            if pd.isna(first_name) or str(first_name).strip() == '':
                continue
            
            first_name_lower = str(first_name).strip().lower()
            
            # Skip unisex names
            if first_name_lower in UNISEX_NAMES:
                continue
            
            # Infer gender based on name lists
            inferred_gender = None
            confidence = "unknown"
            
            if first_name_lower in COMMON_MALE_NAMES:
                inferred_gender = 'M'
                confidence = "high"
            elif first_name_lower in COMMON_FEMALE_NAMES:
                inferred_gender = 'F'
                confidence = "high"
            elif len(first_name_lower) >= 3 and first_name_lower.endswith('a'):
                # Simple heuristic: names ending in 'a' often female
                inferred_gender = 'F'
                confidence = "low"
            
            if inferred_gender:
                inferences.append({
                    'player': player,
                    'first_name': first_name,
                    'inferred_gender': inferred_gender,
                    'confidence': confidence,
                    'records_updated': len(player_df)
                })
                
                # Update all records for this player
                df.loc[player_mask, 'M/F'] = inferred_gender
        
        # Log inferences
        if inferences:
            high_conf = [i for i in inferences if i['confidence'] == 'high']
            low_conf = [i for i in inferences if i['confidence'] == 'low']
            
            self.logger.info(
                f"🔍 Inferred gender for {len(inferences)} player(s) with missing data "
                f"({len(high_conf)} high confidence, {len(low_conf)} low confidence):"
            )
            
            for inference in inferences:
                conf_icon = "✓" if inference['confidence'] == 'high' else "~"
                self.logger.info(
                    f"  {conf_icon} {inference['player']} (first: {inference['first_name']}) → {inference['inferred_gender']} "
                    f"({inference['records_updated']} records)"
                )
        
        # Clean up temporary column
        if '_first_name_original' in df.columns:
            df = df.drop(columns=['_first_name_original'])
        
        return df
    
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
        
        # Convert Period objects to strings for JSON serialization
        monthly_counts = df.groupby('month').size()
        weekly_counts = df.groupby('week').size()
        
        time_stats['games_per_month'] = {str(period): count for period, count in monthly_counts.items()}
        time_stats['games_per_week'] = {str(period): count for period, count in weekly_counts.items()}
        
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

    def generate_team_statistics(self, df: pd.DataFrame, enhanced_data: Dict[str, Any]) -> Dict[str, List[Dict]]:
        """Generate statistics grouped by division and team."""
        team_stats = {}
        
        if 'Division' not in df.columns:
            self.logger.warning("'Division' column not found, cannot generate team statistics.")
            return {}
            
        divisions = df['Division'].dropna().unique()
        
        for division in divisions:
            division_clean = division.strip()
            
            division_df = df[df['Division'] == division]
            division_teams = sorted(division_df['Team'].dropna().unique())
            
            num_teams = len(division_teams)
            matches_per_team = (num_teams - 1) * 2
            games_to_qualify = int(matches_per_team * 1.5)
            
            teams_data = []
            for team_name in division_teams:
                team_df = df[df['Team'] == team_name]
                
                player_names = team_df['player_name'].unique()
                player_list = []
                for name in player_names:
                    parts = str(name).split()
                    last_name = parts[-1] if parts else str(name)
                    player_list.append((last_name, name))
                
                player_list.sort(key=lambda x: x[0])
                
                players = []
                for _, full_name in player_list:
                    player_data = self._calculate_player_stats(team_df, full_name, games_to_qualify, enhanced_data)
                    players.append(player_data)
                
                teams_data.append({
                    "name": team_name,
                    "players": players
                })
            
            team_stats[division_clean] = teams_data
            
        return team_stats

    def _calculate_player_stats(self, team_df, player_name: str, games_to_qualify_threshold: int, enhanced_data: Dict = None) -> Dict:
        """Calculate comprehensive player statistics."""
        player_df = team_df[team_df['player_name'] == player_name]
        
        if len(player_df) == 0:
            return self._empty_player_stats(player_name, games_to_qualify_threshold)
        
        legs_played = len(player_df)
        games_played = self._estimate_games_played(player_df)
        games_remaining = max(0, games_to_qualify_threshold - games_played)
        eligibility = "QUALIFIED" if games_played >= games_to_qualify_threshold else "INELIGIBLE"
        
        game_stats = self._calculate_game_specific_stats(player_df)
        
        total_wins = sum(stats.get('wins', 0) for stats in game_stats.values())
        total_losses = sum(stats.get('losses', 0) for stats in game_stats.values())
        
        total_games = total_wins + total_losses
        win_pct = f"{(total_wins / total_games * 100):.2f}%" if total_games > 0 else "0.00%"
        
        qps = self._calculate_total_qps(player_df, player_name, enhanced_data)
        qp_pct = f"{(qps / legs_played * 100):.2f}%" if legs_played > 0 else "0.00%"
        
        rating = 0.0
        if games_played > 0 and legs_played > 0:
            rating = ((total_wins * 2) / games_played) + (qps / legs_played)
        
        return {
            "name": player_name, "legs": legs_played, "games": games_played,
            "qualify": games_remaining, "eligibility": eligibility,
            "s01_w": game_stats.get('501 SIDO_S', {}).get('wins', 0),
            "s01_l": game_stats.get('501 SIDO_S', {}).get('losses', 0),
            "sc_w": game_stats.get('Cricket_S', {}).get('wins', 0),
            "sc_l": game_stats.get('Cricket_S', {}).get('losses', 0),
            "d01_w": game_stats.get('501 SIDO_D', {}).get('wins', 0),
            "d01_l": game_stats.get('501 SIDO_D', {}).get('losses', 0),
            "dc_w": game_stats.get('Cricket_D', {}).get('wins', 0),
            "dc_l": game_stats.get('Cricket_D', {}).get('losses', 0),
            "total_w": total_wins, "total_l": total_losses, "win_pct": win_pct,
            "qps": qps, "qp_pct": qp_pct, "rating": f"{rating:.4f}"
        }

    def _estimate_games_played(self, player_df):
        """Calculate actual games played by counting unique Set# combinations."""
        if len(player_df) == 0:
            return 0
        if 'report_url' in player_df.columns and 'Set #' in player_df.columns:
            return player_df.groupby(['report_url', 'Set #']).ngroups
        else:
            return max(1, len(player_df) // 3)

    def _calculate_game_specific_stats(self, player_df):
        """Calculate wins/losses by game type and play format (PF), counting games, not legs."""
        stats = {}
        if 'report_url' not in player_df.columns or 'Set #' not in player_df.columns:
            for game_type in player_df['game_name'].unique():
                for pf in player_df['PF'].unique():
                    game_df = player_df[(player_df['game_name'] == game_type) & (player_df['PF'] == pf)]
                    if not game_df.empty:
                        wins = (game_df['win'] == 'W').sum()
                        losses = (game_df['win'] == 'L').sum()
                        stats[f"{game_type}_{pf}"] = {'wins': wins, 'losses': losses}
            return stats
        
        for game_type in player_df['game_name'].unique():
            for pf in player_df['PF'].unique():
                game_df = player_df[(player_df['game_name'] == game_type) & (player_df['PF'] == pf)]
                if not game_df.empty:
                    wins = 0
                    losses = 0
                    for _, set_data in game_df.groupby(['report_url', 'Set #']):
                        legs_won = (set_data['win'] == 'W').sum()
                        legs_lost = (set_data['win'] == 'L').sum()
                        if legs_won > legs_lost: wins += 1
                        elif legs_lost > legs_won: losses += 1
                    stats[f"{game_type}_{pf}"] = {'wins': wins, 'losses': losses}
        return stats

    def _calculate_total_qps(self, player_df, player_name: str, enhanced_data: Dict = None) -> int:
        """Calculate total Quality Points from 501 (CSV) and Cricket (enhanced data)."""
        total_qps = self._calculate_501_qps_from_csv(player_df)
        if enhanced_data:
            total_qps += self._get_cricket_qps_for_player(player_name, enhanced_data)
        return total_qps

    def _calculate_501_qps_from_csv(self, player_df) -> int:
        """Calculate 501 QPs using Hi Turn and DO columns from CSV."""
        if 'game_name' not in player_df.columns: return 0
        games_501 = player_df[player_df['game_name'] == '501 SIDO']
        total_qps = 0
        for _, row in games_501.iterrows():
            leg_qps = 0
            for col, rules in [('Hi Turn', [(164, 5), (148, 4), (132, 3), (116, 2), (95, 1)]), ('DO', [(151, 5), (129, 4), (107, 3), (85, 2), (61, 1)])]:
                val = row.get(col, 0)
                if pd.notna(val):
                    try:
                        score = float(val)
                        for limit, qp in rules:
                            if score >= limit:
                                leg_qps += qp
                                break
                    except (ValueError, TypeError): pass
            total_qps += leg_qps
        return total_qps

    def _get_cricket_qps_for_player(self, player_name: str, enhanced_data: Dict) -> int:
        """Extract Cricket QPs for a player from enhanced data."""
        if not enhanced_data: return 0
        cricket_qp_data = enhanced_data.get('enhanced_statistics', {}).get('cricket_enhanced_qp', {})
        return cricket_qp_data.get(player_name, {}).get('total_qp', 0)

    def _empty_player_stats(self, player_name: str, games_to_qualify: int):
        """Return empty stats structure for players with no data."""
        return {
            "name": player_name, "legs": 0, "games": 0, "qualify": games_to_qualify, "eligibility": "INELIGIBLE",
            "s01_w": 0, "s01_l": 0, "sc_w": 0, "sc_l": 0, "d01_w": 0, "d01_l": 0, "dc_w": 0, "dc_l": 0,
            "total_w": 0, "total_l": 0, "win_pct": "0.00%", "qps": 0, "qp_pct": "0.00%", "rating": "0.0000"
        }

    def generate_team_statistics(self, df: pd.DataFrame, enhanced_data: Dict[str, Any]) -> Dict[str, List[Dict]]:
        """Generate statistics grouped by division and team."""
        team_stats = {}
        
        if 'Division' not in df.columns:
            return {}
            
        divisions = df['Division'].dropna().unique()
        
        for division in divisions:
            # Map standard division names if needed
            division_clean = division.strip()
            
            # Get teams for this division
            division_df = df[df['Division'] == division]
            division_teams = sorted(division_df['Team'].dropna().unique())
            
            # Calculate games to qualify
            # Round robin: each team plays every other team twice
            # Games to qualify = (number of matches) × 1.5
            num_teams = len(division_teams)
            matches_per_team = (num_teams - 1) * 2
            games_to_qualify = int(matches_per_team * 1.5)
            
            teams_data = []
            for team_name in division_teams:
                team_df = df[df['Team'] == team_name]
                
                # Get unique players for this team
                player_names = team_df['player_name'].unique()
                player_list = []
                for name in player_names:
                    # Extract last name (assumed to be last word)
                    parts = str(name).split()
                    last_name = parts[-1] if parts else str(name)
                    player_list.append((last_name, name))
                
                # Sort by last name
                player_list.sort(key=lambda x: x[0])
                
                players = []
                for _, full_name in player_list:
                    player_data = self._calculate_player_stats(team_df, full_name, games_to_qualify, enhanced_data)
                    players.append(player_data)
                
                teams_data.append({
                    "name": team_name,
                    "players": players
                })
            
            team_stats[division_clean] = teams_data
            
        return team_stats

    def _calculate_player_stats(self, team_df, player_name: str, games_to_qualify_threshold: int, enhanced_data: Dict = None) -> Dict:
        """Calculate comprehensive player statistics."""
        player_df = team_df[team_df['player_name'] == player_name]
        
        if len(player_df) == 0:
            return self._empty_player_stats(player_name, games_to_qualify_threshold)
        
        # Calculate basic stats
        legs_played = len(player_df)
        games_played = self._estimate_games_played(player_df)
        games_remaining = max(0, games_to_qualify_threshold - games_played)
        eligibility = "QUALIFIED" if games_played >= games_to_qualify_threshold else "INELIGIBLE"
        
        # Calculate game-specific W/L records
        game_stats = self._calculate_game_specific_stats(player_df)
        
        # Calculate total wins/losses
        total_wins = sum([game_stats[game]['wins'] for game in game_stats])
        total_losses = sum([game_stats[game]['losses'] for game in game_stats])
        
        # Calculate win percentage
        total_games = total_wins + total_losses
        win_pct = f"{(total_wins / total_games * 100):.2f}%" if total_games > 0 else "0.00%"
        
        # Calculate QPs properly using CSV data for 501 and enhanced data for Cricket
        qps = self._calculate_total_qps(player_df, player_name, enhanced_data)
        qp_pct = f"{(qps / legs_played * 100):.2f}%" if legs_played > 0 else "0.00%"
        
        # Calculate rating
        if games_played > 0:
            rating = ((total_wins * 2) / games_played) + (qps / legs_played)
            rating = f"{rating:.4f}"
        else:
            rating = "0.0000"
        
        return {
            "name": player_name,
            "legs": legs_played,
            "games": games_played,
            "qualify": games_remaining,
            "eligibility": eligibility,
            "s01_w": game_stats.get('501 SIDO_S', {}).get('wins', 0),
            "s01_l": game_stats.get('501 SIDO_S', {}).get('losses', 0),
            "sc_w": game_stats.get('Cricket_S', {}).get('wins', 0),
            "sc_l": game_stats.get('Cricket_S', {}).get('losses', 0),
            "d01_w": game_stats.get('501 SIDO_D', {}).get('wins', 0),
            "d01_l": game_stats.get('501 SIDO_D', {}).get('losses', 0),
            "dc_w": game_stats.get('Cricket_D', {}).get('wins', 0),
            "dc_l": game_stats.get('Cricket_D', {}).get('losses', 0),
            "total_w": total_wins,
            "total_l": total_losses,
            "win_pct": win_pct,
            "qps": qps,
            "qp_pct": qp_pct,
            "rating": rating
        }

    def _estimate_games_played(self, player_df):
        """Calculate actual games played by counting unique Set# combinations."""
        if len(player_df) == 0:
            return 0
        
        # Each unique combination of report_url + Set # represents one game
        if 'report_url' in player_df.columns and 'Set #' in player_df.columns:
            # Count unique games (Set numbers) across all matches
            games = player_df.groupby(['report_url', 'Set #']).ngroups
            return games
        else:
            # Fallback: estimate based on legs (best of 3, so ~2-3 legs per game)
            return max(1, len(player_df) // 3)

    def _calculate_game_specific_stats(self, player_df):
        """Calculate wins/losses by game type and play format (PF), counting games, not legs.
        
        Produces keys like:
          - '501 SIDO_S' (Singles 501)
          - '501 SIDO_D' (Doubles 501)
          - 'Cricket_S'  (Singles Cricket)
          - 'Cricket_D'  (Doubles Cricket)
        """
        stats = {}
        
        if 'report_url' not in player_df.columns or 'Set #' not in player_df.columns:
            # Fallback: count legs if we don't have Set # info
            for game_type in player_df['game_name'].unique():
                for pf in player_df['PF'].unique():
                    game_df = player_df[(player_df['game_name'] == game_type) & (player_df['PF'] == pf)]
                    if len(game_df) == 0:
                        continue
                    wins = len(game_df[game_df['win'] == 'W'])
                    losses = len(game_df[game_df['win'] == 'L'])
                    stats[f"{game_type}_{pf}"] = {'wins': wins, 'losses': losses}
            return stats
        
        # Proper calculation: determine who won each game (Set)
        for game_type in player_df['game_name'].unique():
            for pf in player_df['PF'].unique():
                game_df = player_df[(player_df['game_name'] == game_type) & (player_df['PF'] == pf)]
                if len(game_df) == 0:
                    continue
                wins = 0
                losses = 0
                
                # Group by match and Set to determine game winners
                for (match_url, set_num), set_data in game_df.groupby(['report_url', 'Set #']):
                    # Count legs won in this set
                    legs_won = (set_data['win'] == 'W').sum()
                    legs_lost = (set_data['win'] == 'L').sum()
                    
                    # Determine if player won this game (best of 3/5)
                    if legs_won > legs_lost:
                        wins += 1
                    elif legs_lost > legs_won:
                        losses += 1
                
                stats[f"{game_type}_{pf}"] = {'wins': wins, 'losses': losses}
        
        return stats

    def _calculate_total_qps(self, player_df, player_name: str, enhanced_data: Dict = None) -> int:
        """Calculate total Quality Points from 501 (CSV) and Cricket (enhanced data)."""
        total_qps = 0
        
        # Calculate 501 QPs from CSV columns (Hi Turn and DO)
        total_qps += self._calculate_501_qps_from_csv(player_df)
        
        # Add Cricket QPs from enhanced data if available
        if enhanced_data:
            cricket_qps = self._get_cricket_qps_for_player(player_name, enhanced_data)
            total_qps += cricket_qps
        
        return total_qps

    def _calculate_501_qps_from_csv(self, player_df) -> int:
        """Calculate 501 QPs using Hi Turn and DO columns from CSV.
        
        QP Rules for 501:
        Turn Score QPs (Hi Turn):     Checkout QPs (DO):
        1: 95-115                     1: 61-84 out
        2: 116-131                    2: 85-106 out
        3: 132-147                    3: 107-128 out
        4: 148-163                    4: 129-150 out
        5: 164-180                    5: 151-170 out
        
        QPs are ADDITIVE - a leg can earn QPs from both columns!
        """
        total_qps = 0
        
        # Filter for 501 games only
        if 'game_name' not in player_df.columns:
            return 0
            
        games_501 = player_df[player_df['game_name'] == '501 SIDO']
        
        for _, row in games_501.iterrows():
            leg_qps = 0
            
            # QPs from Hi Turn (high score in one turn)
            hi_turn = row.get('Hi Turn', 0)
            if pd.notna(hi_turn):
                try:
                    hi_turn = float(hi_turn)
                    if 164 <= hi_turn <= 180:
                        leg_qps += 5
                    elif 148 <= hi_turn <= 163:
                        leg_qps += 4
                    elif 132 <= hi_turn <= 147:
                        leg_qps += 3
                    elif 116 <= hi_turn <= 131:
                        leg_qps += 2
                    elif 95 <= hi_turn <= 115:
                        leg_qps += 1
                except (ValueError, TypeError):
                    pass
            
            # QPs from DO (checkout score)
            do_score = row.get('DO', 0)
            if pd.notna(do_score):
                try:
                    do_score = float(do_score)
                    if 151 <= do_score <= 170:
                        leg_qps += 5
                    elif 129 <= do_score <= 150:
                        leg_qps += 4
                    elif 107 <= do_score <= 128:
                        leg_qps += 3
                    elif 85 <= do_score <= 106:
                        leg_qps += 2
                    elif 61 <= do_score <= 84:
                        leg_qps += 1
                except (ValueError, TypeError):
                    pass
            
            total_qps += leg_qps
        
        return total_qps

    def _get_cricket_qps_for_player(self, player_name: str, enhanced_data: Dict) -> int:
        """Extract Cricket QPs for a player from enhanced data."""
        if not enhanced_data:
            return 0
        
        # Check if we have cricket QP data
        cricket_qp_data = enhanced_data.get('enhanced_statistics', {}).get('cricket_enhanced_qp', {})
        
        if player_name in cricket_qp_data:
            return cricket_qp_data[player_name].get('total_qp', 0)
        
        return 0

    def _empty_player_stats(self, player_name: str, games_to_qualify: int):
        """Return empty stats structure for players with no data."""
        return {
            "name": player_name,
            "legs": 0, "games": 0, "qualify": games_to_qualify, "eligibility": "INELIGIBLE",
            "s01_w": 0, "s01_l": 0, "sc_w": 0, "sc_l": 0,
            "d01_w": 0, "d01_l": 0, "dc_w": 0, "dc_l": 0,
            "total_w": 0, "total_l": 0, "win_pct": "0.00%",
            "qps": 0, "qp_pct": "0.00%", "rating": "0.0000"
        }

    def generate_team_statistics(self, df: pd.DataFrame, enhanced_data: Dict[str, Any]) -> Dict[str, List[Dict]]:
        """Generate statistics grouped by division and team."""
        team_stats = {}
        
        if 'Division' not in df.columns:
            return {}
            
        divisions = df['Division'].dropna().unique()
        
        for division in divisions:
            # Map standard division names if needed
            division_clean = division.strip()
            
            # Get teams for this division
            division_df = df[df['Division'] == division]
            division_teams = sorted(division_df['Team'].dropna().unique())
            
            # Calculate games to qualify
            # Round robin: each team plays every other team twice
            # Games to qualify = (number of matches) × 1.5
            num_teams = len(division_teams)
            matches_per_team = (num_teams - 1) * 2
            games_to_qualify = int(matches_per_team * 1.5)
            
            teams_data = []
            for team_name in division_teams:
                team_df = df[df['Team'] == team_name]
                
                # Get unique players for this team
                player_names = team_df['player_name'].unique()
                player_list = []
                for name in player_names:
                    # Extract last name (assumed to be last word)
                    parts = str(name).split()
                    last_name = parts[-1] if parts else str(name)
                    player_list.append((last_name, name))
                
                # Sort by last name
                player_list.sort(key=lambda x: x[0])
                
                players = []
                for _, full_name in player_list:
                    player_data = self._calculate_player_stats(team_df, full_name, games_to_qualify, enhanced_data)
                    players.append(player_data)
                
                teams_data.append({
                    "name": team_name,
                    "players": players
                })
            
            team_stats[division_clean] = teams_data
            
        return team_stats

    def _calculate_player_stats(self, team_df, player_name: str, games_to_qualify_threshold: int, enhanced_data: Dict = None) -> Dict:
        """Calculate comprehensive player statistics."""
        player_df = team_df[team_df['player_name'] == player_name]
        
        if len(player_df) == 0:
            return self._empty_player_stats(player_name, games_to_qualify_threshold)
        
        # Calculate basic stats
        legs_played = len(player_df)
        games_played = self._estimate_games_played(player_df)
        games_remaining = max(0, games_to_qualify_threshold - games_played)
        eligibility = "QUALIFIED" if games_played >= games_to_qualify_threshold else "INELIGIBLE"
        
        # Calculate game-specific W/L records
        game_stats = self._calculate_game_specific_stats(player_df)
        
        # Calculate total wins/losses
        total_wins = sum([game_stats[game]['wins'] for game in game_stats])
        total_losses = sum([game_stats[game]['losses'] for game in game_stats])
        
        # Calculate win percentage
        total_games = total_wins + total_losses
        win_pct = f"{(total_wins / total_games * 100):.2f}%" if total_games > 0 else "0.00%"
        
        # Calculate QPs properly using CSV data for 501 and enhanced data for Cricket
        qps = self._calculate_total_qps(player_df, player_name, enhanced_data)
        qp_pct = f"{(qps / legs_played * 100):.2f}%" if legs_played > 0 else "0.00%"
        
        # Calculate rating
        if games_played > 0:
            rating = ((total_wins * 2) / games_played) + (qps / legs_played)
            rating = f"{rating:.4f}"
        else:
            rating = "0.0000"
        
        return {
            "name": player_name,
            "legs": legs_played,
            "games": games_played,
            "qualify": games_remaining,
            "eligibility": eligibility,
            "s01_w": game_stats.get('501 SIDO_S', {}).get('wins', 0),
            "s01_l": game_stats.get('501 SIDO_S', {}).get('losses', 0),
            "sc_w": game_stats.get('Cricket_S', {}).get('wins', 0),
            "sc_l": game_stats.get('Cricket_S', {}).get('losses', 0),
            "d01_w": game_stats.get('501 SIDO_D', {}).get('wins', 0),
            "d01_l": game_stats.get('501 SIDO_D', {}).get('losses', 0),
            "dc_w": game_stats.get('Cricket_D', {}).get('wins', 0),
            "dc_l": game_stats.get('Cricket_D', {}).get('losses', 0),
            "total_w": total_wins,
            "total_l": total_losses,
            "win_pct": win_pct,
            "qps": qps,
            "qp_pct": qp_pct,
            "rating": rating
        }

    def _estimate_games_played(self, player_df):
        """Calculate actual games played by counting unique Set# combinations."""
        if len(player_df) == 0:
            return 0
        
        # Each unique combination of report_url + Set # represents one game
        if 'report_url' in player_df.columns and 'Set #' in player_df.columns:
            # Count unique games (Set numbers) across all matches
            games = player_df.groupby(['report_url', 'Set #']).ngroups
            return games
        else:
            # Fallback: estimate based on legs (best of 3, so ~2-3 legs per game)
            return max(1, len(player_df) // 3)

    def _calculate_game_specific_stats(self, player_df):
        """Calculate wins/losses by game type and play format (PF), counting games, not legs."""
        stats = {}
        
        if 'report_url' not in player_df.columns or 'Set #' not in player_df.columns:
            # Fallback: count legs if we don't have Set # info
            for game_type in player_df['game_name'].unique():
                for pf in player_df['PF'].unique():
                    game_df = player_df[(player_df['game_name'] == game_type) & (player_df['PF'] == pf)]
                    if len(game_df) == 0:
                        continue
                    wins = len(game_df[game_df['win'] == 'W'])
                    losses = len(game_df[game_df['win'] == 'L'])
                    stats[f"{game_type}_{pf}"] = {'wins': wins, 'losses': losses}
            return stats
        
        # Proper calculation: determine who won each game (Set)
        for game_type in player_df['game_name'].unique():
            for pf in player_df['PF'].unique():
                game_df = player_df[(player_df['game_name'] == game_type) & (player_df['PF'] == pf)]
                if len(game_df) == 0:
                    continue
                wins = 0
                losses = 0
                
                # Group by match and Set to determine game winners
                for (match_url, set_num), set_data in game_df.groupby(['report_url', 'Set #']):
                    # Count legs won in this set
                    legs_won = (set_data['win'] == 'W').sum()
                    legs_lost = (set_data['win'] == 'L').sum()
                    
                    # Determine if player won this game (best of 3/5)
                    if legs_won > legs_lost:
                        wins += 1
                    elif legs_lost > legs_won:
                        losses += 1
                
                stats[f"{game_type}_{pf}"] = {'wins': wins, 'losses': losses}
        
        return stats

    def _calculate_total_qps(self, player_df, player_name: str, enhanced_data: Dict = None) -> int:
        """Calculate total Quality Points from 501 (CSV) and Cricket (enhanced data)."""
        total_qps = 0
        
        # Calculate 501 QPs from CSV columns (Hi Turn and DO)
        total_qps += self._calculate_501_qps_from_csv(player_df)
        
        # Add Cricket QPs from enhanced data if available
        if enhanced_data:
            cricket_qps = self._get_cricket_qps_for_player(player_name, enhanced_data)
            total_qps += cricket_qps
        
        return total_qps

    def _calculate_501_qps_from_csv(self, player_df) -> int:
        """Calculate 501 QPs using Hi Turn and DO columns from CSV."""
        total_qps = 0
        
        # Filter for 501 games only
        if 'game_name' not in player_df.columns:
            return 0
            
        games_501 = player_df[player_df['game_name'] == '501 SIDO']
        
        for _, row in games_501.iterrows():
            leg_qps = 0
            
            # QPs from Hi Turn (high score in one turn)
            hi_turn = row.get('Hi Turn', 0)
            if pd.notna(hi_turn):
                try:
                    hi_turn = float(hi_turn)
                    if 164 <= hi_turn <= 180:
                        leg_qps += 5
                    elif 148 <= hi_turn <= 163:
                        leg_qps += 4
                    elif 132 <= hi_turn <= 147:
                        leg_qps += 3
                    elif 116 <= hi_turn <= 131:
                        leg_qps += 2
                    elif 95 <= hi_turn <= 115:
                        leg_qps += 1
                except (ValueError, TypeError):
                    pass
            
            # QPs from DO (checkout score)
            do_score = row.get('DO', 0)
            if pd.notna(do_score):
                try:
                    do_score = float(do_score)
                    if 151 <= do_score <= 170:
                        leg_qps += 5
                    elif 129 <= do_score <= 150:
                        leg_qps += 4
                    elif 107 <= do_score <= 128:
                        leg_qps += 3
                    elif 85 <= do_score <= 106:
                        leg_qps += 2
                    elif 61 <= do_score <= 84:
                        leg_qps += 1
                except (ValueError, TypeError):
                    pass
            
            total_qps += leg_qps
        
        return total_qps

    def _get_cricket_qps_for_player(self, player_name: str, enhanced_data: Dict) -> int:
        """Extract Cricket QPs for a player from enhanced data."""
        if not enhanced_data:
            return 0
        
        # Check if we have cricket QP data
        cricket_qp_data = enhanced_data.get('enhanced_statistics', {}).get('cricket_enhanced_qp', {})
        
        if player_name in cricket_qp_data:
            return cricket_qp_data[player_name].get('total_qp', 0)
        
        return 0

    def _empty_player_stats(self, player_name: str, games_to_qualify: int):
        """Return empty stats structure for players with no data."""
        return {
            "name": player_name,
            "legs": 0, "games": 0, "qualify": games_to_qualify, "eligibility": "INELIGIBLE",
            "s01_w": 0, "s01_l": 0, "sc_w": 0, "sc_l": 0,
            "d01_w": 0, "d01_l": 0, "dc_w": 0, "dc_l": 0,
            "total_w": 0, "total_l": 0, "win_pct": "0.00%",
            "qps": 0, "qp_pct": "0.00%", "rating": "0.0000"
        }
