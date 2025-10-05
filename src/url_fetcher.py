"""URL fetcher module for extracting detailed DartConnect game data.

This module fetches turn-by-turn game data from DartConnect recap URLs to enable
enhanced quality point calculations, particularly for Cricket games where
bulls and marks need to be combined for accurate QP scoring.
"""

import requests
import json
import re
import html
from typing import Dict, List, Optional, Any
from urllib.parse import urlparse
import logging


class DartConnectURLFetcher:
    """Fetches and parses detailed game data from DartConnect recap URLs."""
    
    def __init__(self, timeout: int = 30):
        """
        Initialize the URL fetcher.
        
        Args:
            timeout: Request timeout in seconds
        """
        self.timeout = timeout
        self.logger = logging.getLogger(__name__)
        self.session = requests.Session()
        
        # Set a proper user agent to avoid blocking
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        })
    
    def fetch_game_data(self, url: str) -> Optional[Dict[str, Any]]:
        """
        Fetch detailed game data from a DartConnect recap URL.
        
        Args:
            url: DartConnect recap URL (e.g., https://recap.dartconnect.com/games/68aba220f978cb217a4c55cb)
            
        Returns:
            Dictionary containing game data or None if fetch failed
        """
        try:
            self.logger.info(f"Fetching game data from: {url}")
            
            # Validate URL format
            if not self._is_valid_dartconnect_url(url):
                self.logger.warning(f"Invalid DartConnect URL format: {url}")
                return None
            
            # Fetch the page
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()
            
            # Extract JSON data from the page
            game_data = self._extract_game_data_from_html(response.text)
            
            if game_data:
                self.logger.info(f"Successfully fetched game data for match: {game_data.get('matchInfo', {}).get('id', 'unknown')}")
                return game_data
            else:
                self.logger.warning(f"No game data found in URL: {url}")
                return None
                
        except requests.RequestException as e:
            self.logger.error(f"Request failed for URL {url}: {e}")
            return None
        except Exception as e:
            self.logger.error(f"Error fetching game data from {url}: {e}")
            return None
    
    def _is_valid_dartconnect_url(self, url: str) -> bool:
        """Validate if URL is a proper DartConnect recap URL."""
        try:
            parsed = urlparse(url)
            return (
                parsed.netloc == 'recap.dartconnect.com' and
                (
                    (parsed.path.startswith('/games/') and len(parsed.path.split('/')) >= 3) or
                    (parsed.path.startswith('/history/report/match/') and len(parsed.path.split('/')) >= 5)
                )
            )
        except Exception:
            return False
    
    def _extract_game_data_from_html(self, html_content: str) -> Optional[Dict[str, Any]]:
        """Extract game data from the HTML page's data-page attribute."""
        try:
            # Find the data-page attribute
            pattern = r'data-page="([^"]+)"'
            match = re.search(pattern, html_content)
            
            if not match:
                self.logger.warning("Could not find data-page attribute in HTML")
                return None
            
            # Decode HTML entities
            json_data = html.unescape(match.group(1))
            
            # Parse JSON
            page_data = json.loads(json_data)
            
            # Extract the props which contain the game data
            if 'props' in page_data:
                return page_data['props']
            else:
                self.logger.warning("No props found in page data")
                return None
                
        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to parse JSON data: {e}")
            return None
        except Exception as e:
            self.logger.error(f"Error extracting game data from HTML: {e}")
            return None
    
    def extract_cricket_stats(self, game_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Extract Cricket-specific statistics from game data.
        
        Args:
            game_data: Game data dictionary from fetch_game_data()
            
        Returns:
            List of cricket game statistics with enhanced metrics
        """
        cricket_games = []
        
        try:
            segments = game_data.get('segments', {})
            
            # Process each segment (usually just one empty key)
            for segment_key, segment_games in segments.items():
                if not isinstance(segment_games, list):
                    continue
                    
                # Process each game group
                for game_group in segment_games:
                    if not isinstance(game_group, list):
                        continue
                        
                    # Process each individual game
                    for game in game_group:
                        if game.get('game_name') == 'Cricket':
                            cricket_stats = self._parse_cricket_game(game)
                            if cricket_stats:
                                cricket_games.append(cricket_stats)
            
            return cricket_games
            
        except Exception as e:
            self.logger.error(f"Error extracting cricket stats: {e}")
            return []
    
    def _parse_cricket_game(self, game: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Parse individual Cricket game for detailed statistics."""
        try:
            turns = game.get('turns', [])
            if not turns:
                return None
            
            # Get game-level ending marks first
            home_ending_marks = game.get('home', {}).get('ending_marks', 0)
            away_ending_marks = game.get('away', {}).get('ending_marks', 0)
            
            # Initialize player stats
            players = {}
            player_names = set()
            
            # Collect all player names first
            for turn in turns:
                home_player = turn.get('home', {})
                away_player = turn.get('away', {})
                
                if home_player.get('name'):
                    player_names.add(home_player.get('name'))
                if away_player.get('name'):
                    player_names.add(away_player.get('name'))
            
            # Initialize players with ending marks
            player_list = list(player_names)
            for i, name in enumerate(player_list):
                # Assign ending marks based on home/away position
                # This is a simplification - in reality we'd need to track which player is home/away
                ending_marks = home_ending_marks if i == 0 else away_ending_marks
                if len(player_list) > 2:  # Multiple players, distribute marks
                    ending_marks = ending_marks // (len(player_list) // 2) if len(player_list) > 1 else ending_marks
                
                players[name] = {
                    'name': name,
                    'ending_marks': ending_marks,
                    'total_bulls': 0,
                    'single_bulls': 0,
                    'double_bulls': 0,
                    'big_hits': 0,
                    'turns': 0,
                    'misses': 0
                }
            
            # Process each turn for bulls and other stats
            for turn in turns:
                home_player = turn.get('home', {})
                away_player = turn.get('away', {})
                
                for player_data in [home_player, away_player]:
                    if not player_data:
                        continue
                        
                    name = player_data.get('name')
                    if not name or name not in players:
                        continue
                    
                    # Count bulls in turn score
                    turn_score = player_data.get('turn_score', '')
                    if turn_score:
                        players[name]['total_bulls'] += self._count_bulls_in_turn(turn_score)
                        players[name]['single_bulls'] += turn_score.count('SB')
                        players[name]['double_bulls'] += turn_score.count('DB')
                        players[name]['turns'] += 1
                    
                    # Check for notable achievements
                    notable = player_data.get('notable', '')
                    if notable:
                        if 'M' in notable:  # Mark count (e.g., "7M")
                            marks = int(notable.replace('M', ''))
                            if marks >= 5:  # Big hit threshold
                                players[name]['big_hits'] += 1
                        elif 'B' in notable:  # Bull count (e.g., "3B")
                            # Already counted in turn_score
                            pass
                    
                    # Check for misses
                    if player_data.get('color') == 'MISS':
                        players[name]['misses'] += 1
            
            # Add game-level information
            game_info = {
                'game_name': 'Cricket',
                'winner_index': game.get('winner_index'),
                'duration': game.get('duration'),
                'home_mpr': game.get('home', {}).get('mpr'),
                'away_mpr': game.get('away', {}).get('mpr'),
                'home_ending_marks': home_ending_marks,
                'away_ending_marks': away_ending_marks,
                'players': list(players.values())
            }
            
            return game_info
            
        except Exception as e:
            self.logger.error(f"Error parsing cricket game: {e}")
            return None
    
    def _count_bulls_in_turn(self, turn_score: str) -> int:
        """Count total bulls (SB + DB) in a turn score string."""
        if not turn_score:
            return 0
        
        # Count single bulls (SB) and double bulls (DB)
        single_bulls = turn_score.count('SB')
        double_bulls = turn_score.count('DB')
        
        # Each DB counts as 2 bulls, SB counts as 1
        return single_bulls + (double_bulls * 2)
    
    def calculate_cricket_qp(self, player_stats: Dict[str, Any]) -> int:
        """
        Calculate Cricket Quality Points using the official league system.
        
        QP levels based on combinations of Hits (H) and Bulls (B):
        1: 5H, 3H+1B, 2B+2H
        2: 6H, 3B, 1H+3B, 3H+2B, 4H+1B  
        3: 7H, 4B, 1H+4B, 2H+3B, 4H+2B, 5H+1B
        4: 8H, 5B, 2H+4B, 3H+3B, 5H+2B, 6H+1B
        5: 9H, 6B, 3H+4B, 6H+2B
        
        Args:
            player_stats: Player statistics from cricket game
            
        Returns:
            QP level (1-5) or 0 if no QP earned
        """
        try:
            # Get actual ending marks (hits) and bulls from game data
            hits = player_stats.get('ending_marks', 0)  # Actual marks scored in game
            bulls = player_stats.get('total_bulls', 0)  # Bulls hit during game
            
            # Convert ending marks to "hits" for QP calculation
            # In Cricket, marks represent closed numbers, we need to convert to hit count
            # This is an approximation - ending_marks is a score, not hit count
            # We'll need to derive hits from the mark score (rough estimate)
            if hits >= 190:  # High score suggests many hits
                hits = hits // 20  # Rough conversion
            elif hits >= 100:
                hits = hits // 15
            else:
                hits = hits // 10
                
            hits = max(0, hits)  # Ensure non-negative
            
            # QP Level 5 checks
            if (hits >= 9 or 
                bulls >= 6 or
                (hits >= 3 and bulls >= 4) or
                (hits >= 6 and bulls >= 2)):
                return 5
            
            # QP Level 4 checks  
            elif (hits >= 8 or
                  bulls >= 5 or
                  (hits >= 2 and bulls >= 4) or
                  (hits >= 3 and bulls >= 3) or
                  (hits >= 5 and bulls >= 2) or
                  (hits >= 6 and bulls >= 1)):
                return 4
            
            # QP Level 3 checks
            elif (hits >= 7 or
                  bulls >= 4 or
                  (hits >= 1 and bulls >= 4) or
                  (hits >= 2 and bulls >= 3) or
                  (hits >= 4 and bulls >= 2) or
                  (hits >= 5 and bulls >= 1)):
                return 3
            
            # QP Level 2 checks
            elif (hits >= 6 or
                  bulls >= 3 or
                  (hits >= 1 and bulls >= 3) or
                  (hits >= 3 and bulls >= 2) or
                  (hits >= 4 and bulls >= 1)):
                return 2
            
            # QP Level 1 checks
            elif (hits >= 5 or
                  (hits >= 3 and bulls >= 1) or
                  (hits >= 2 and bulls >= 2)):
                return 1
            
            # No QP earned
            else:
                return 0
            
        except Exception as e:
            self.logger.error(f"Error calculating cricket QP: {e}")
            return 0
    
    def calculate_501_qp(self, total_score: int, checkout_score: Optional[int] = None) -> int:
        """
        Calculate 501 Quality Points using the official league system.
        
        QPs are ADDITIVE - player earns QPs from BOTH columns if they qualify:
        
        Total Score QPs:        Checkout QPs:
        1: 95-115              1: 61-84 out
        2: 116-131             2: 85-106 out  
        3: 132-147             3: 107-128 out
        4: 148-163             4: 129-150 out
        5: 164-180             5: 151-170 out
        
        Example: 132 total + 132 checkout = 3 + 4 = 7 total QPs
        
        Args:
            total_score: Total points scored in the game
            checkout_score: Points scored on checkout (optional)
            
        Returns:
            Total QPs earned (sum of both columns)
        """
        try:
            total_qps = 0
            
            # QPs from total score column
            if 164 <= total_score <= 180:
                total_qps += 5
            elif 148 <= total_score <= 163:
                total_qps += 4  
            elif 132 <= total_score <= 147:
                total_qps += 3
            elif 116 <= total_score <= 131:
                total_qps += 2
            elif 95 <= total_score <= 115:
                total_qps += 1
            
            # QPs from checkout score column (if available)
            if checkout_score is not None:
                if 151 <= checkout_score <= 170:
                    total_qps += 5
                elif 129 <= checkout_score <= 150:
                    total_qps += 4
                elif 107 <= checkout_score <= 128:
                    total_qps += 3
                elif 85 <= checkout_score <= 106:
                    total_qps += 2
                elif 61 <= checkout_score <= 84:
                    total_qps += 1
            
            return total_qps
            
        except Exception as e:
            self.logger.error(f"Error calculating 501 QP: {e}")
            return 0
