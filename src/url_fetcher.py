"""URL fetcher module for extracting detailed DartConnect game data.

This module fetches turn-by-turn game data from DartConnect recap URLs to enable
enhanced quality point calculations, particularly for Cricket games where
bulls and marks need to be combined for accurate QP scoring.
"""

import requests
import json
import re
import html
import hashlib
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from urllib.parse import urlparse
import logging


class DartConnectURLFetcher:
    """Fetches and parses detailed game data from DartConnect recap URLs."""

    def __init__(
        self,
        timeout: int = 30,
        cache_dir: str = "cache/dartconnect_urls",
        cache_expiry_days: int = 150,
    ):
        """
        Initialize the URL fetcher.

        Args:
            timeout: Request timeout in seconds
            cache_dir: Directory to store cached responses
            cache_expiry_days: Number of days before cache expires (default: 150 - about 5 months for dart season)
        """
        self.timeout = timeout
        self.cache_dir = Path(cache_dir)
        self.cache_expiry_days = cache_expiry_days
        self.logger = logging.getLogger(__name__)
        self.session = requests.Session()

        # Create cache directory if it doesn't exist
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        # Set a proper user agent to avoid blocking
        self.session.headers.update(
            {
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
            }
        )

        # Track cache stats for reporting
        self.cache_stats = {"hits": 0, "misses": 0, "expired": 0, "new_fetches": 0}

    def fetch_game_data(self, url: str) -> Optional[Dict[str, Any]]:
        """
        Fetch detailed game data from a DartConnect recap URL with caching.

        Args:
            url: DartConnect recap URL (e.g., https://recap.dartconnect.com/games/68aba220f978cb217a4c55cb)

        Returns:
            Dictionary containing game data or None if fetch failed
        """
        try:
            # Validate URL format first
            if not self._is_valid_dartconnect_url(url):
                self.logger.warning(f"Invalid DartConnect URL format: {url}")
                return None

            # Check cache first
            cached_data = self._get_cached_data(url)
            if cached_data is not None:
                self.cache_stats["hits"] += 1
                match_id = cached_data.get("matchInfo", {}).get("id", "unknown")
                self.logger.info(f"Using cached game data for match: {match_id}")
                return cached_data

            # Cache miss - fetch from web
            self.logger.info(f"Fetching game data from: {url}")
            self.cache_stats["misses"] += 1

            # Fetch the page
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()

            # Extract JSON data from the page
            game_data = self._extract_game_data_from_html(response.text)

            if game_data:
                match_id = game_data.get("matchInfo", {}).get("id", "unknown")
                self.logger.info(
                    f"Successfully fetched game data for match: {match_id}"
                )

                # Cache the successful response
                self._cache_data(url, game_data)
                self.cache_stats["new_fetches"] += 1

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
            return parsed.netloc == "recap.dartconnect.com" and (
                (parsed.path.startswith("/games/") and len(parsed.path.split("/")) >= 3)
                or (
                    parsed.path.startswith("/history/report/match/")
                    and len(parsed.path.split("/")) >= 5
                )
            )
        except Exception:
            return False

    def _get_cache_filename(self, url: str) -> str:
        """Generate a unique cache filename for a URL."""
        # Extract match ID from URL for readable filenames
        match_id = None
        if "/games/" in url:
            match_id = url.split("/games/")[-1]
        elif "/match/" in url:
            match_id = url.split("/match/")[-1]

        if match_id:
            # Clean match ID of any query parameters
            match_id = match_id.split("?")[0].split("#")[0]
            return f"{match_id}.json"
        else:
            # Fallback to URL hash if we can't extract match ID
            url_hash = hashlib.md5(url.encode()).hexdigest()
            return f"url_{url_hash}.json"

    def _get_cached_data(self, url: str) -> Optional[Dict[str, Any]]:
        """Get cached data for a URL if it exists and is not expired."""
        try:
            cache_file = self.cache_dir / self._get_cache_filename(url)

            if not cache_file.exists():
                return None

            # Check if cache is expired
            file_age = datetime.now() - datetime.fromtimestamp(
                cache_file.stat().st_mtime
            )
            if file_age > timedelta(days=self.cache_expiry_days):
                self.logger.debug(
                    f"Cache expired for {url} (age: {file_age.days} days)"
                )
                self.cache_stats["expired"] += 1
                # Remove expired cache file
                cache_file.unlink()
                return None

            # Load and return cached data
            with open(cache_file, "r", encoding="utf-8") as f:
                cached_data = json.load(f)
                return cached_data.get("game_data")

        except Exception as e:
            self.logger.warning(f"Error reading cache for {url}: {e}")
            return None

    def _cache_data(self, url: str, game_data: Dict[str, Any]) -> None:
        """Cache game data for a URL."""
        try:
            cache_file = self.cache_dir / self._get_cache_filename(url)

            cache_entry = {
                "url": url,
                "cached_at": datetime.now().isoformat(),
                "game_data": game_data,
            }

            with open(cache_file, "w", encoding="utf-8") as f:
                json.dump(cache_entry, f, indent=2, ensure_ascii=False)

            self.logger.debug(f"Cached data for {url}")

        except Exception as e:
            self.logger.warning(f"Error caching data for {url}: {e}")

    def get_cache_stats(self) -> Dict[str, int]:
        """Get cache performance statistics."""
        return self.cache_stats.copy()

    def get_cache_info(self) -> Dict[str, Any]:
        """Get detailed cache information including size and age statistics."""
        try:
            if not self.cache_dir.exists():
                return {
                    "total_files": 0,
                    "total_size_mb": 0,
                    "oldest_file": None,
                    "newest_file": None,
                }

            cache_files = list(self.cache_dir.glob("*.json"))
            if not cache_files:
                return {
                    "total_files": 0,
                    "total_size_mb": 0,
                    "oldest_file": None,
                    "newest_file": None,
                }

            total_size = sum(f.stat().st_size for f in cache_files)
            file_times = [
                (f, datetime.fromtimestamp(f.stat().st_mtime)) for f in cache_files
            ]

            oldest_file = min(file_times, key=lambda x: x[1])
            newest_file = max(file_times, key=lambda x: x[1])

            return {
                "total_files": len(cache_files),
                "total_size_mb": round(total_size / (1024 * 1024), 2),
                "oldest_file": {
                    "name": oldest_file[0].name,
                    "date": oldest_file[1].isoformat(),
                    "age_days": (datetime.now() - oldest_file[1]).days,
                },
                "newest_file": {
                    "name": newest_file[0].name,
                    "date": newest_file[1].isoformat(),
                    "age_days": (datetime.now() - newest_file[1]).days,
                },
                "expiry_days": self.cache_expiry_days,
            }
        except Exception as e:
            self.logger.error(f"Error getting cache info: {e}")
            return {"error": str(e)}

    def clear_cache(self, older_than_days: Optional[int] = None) -> int:
        """Clear cache files, optionally only those older than specified days."""
        cleared_count = 0

        try:
            if not self.cache_dir.exists():
                return 0

            cutoff_time = None
            if older_than_days is not None:
                cutoff_time = datetime.now() - timedelta(days=older_than_days)

            for cache_file in self.cache_dir.glob("*.json"):
                try:
                    if cutoff_time is None:
                        # Clear all cache files
                        cache_file.unlink()
                        cleared_count += 1
                    else:
                        # Only clear files older than cutoff
                        file_time = datetime.fromtimestamp(cache_file.stat().st_mtime)
                        if file_time < cutoff_time:
                            cache_file.unlink()
                            cleared_count += 1

                except Exception as e:
                    self.logger.warning(f"Error removing cache file {cache_file}: {e}")

            if cleared_count > 0:
                self.logger.info(f"Cleared {cleared_count} cache files")

        except Exception as e:
            self.logger.error(f"Error clearing cache: {e}")

        return cleared_count

    def _extract_game_data_from_html(
        self, html_content: str
    ) -> Optional[Dict[str, Any]]:
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
            if "props" in page_data:
                return page_data["props"]
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
            segments = game_data.get("segments", {})

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
                        if game.get("game_name") == "Cricket":
                            cricket_stats = self._parse_cricket_game(game)
                            if cricket_stats:
                                cricket_games.append(cricket_stats)

            return cricket_games

        except Exception as e:
            self.logger.error(f"Error extracting cricket stats: {e}")
            return []

    def _parse_cricket_game(self, game: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Parse individual Cricket game for detailed statistics and QP calculation."""
        try:
            turns = game.get("turns", [])
            if not turns:
                return None

            # Initialize player stats with turn-by-turn tracking
            players = {}

            # Process each turn to track marks and bulls PER TURN for QP calculation
            for turn in turns:
                home_player = turn.get("home", {})
                away_player = turn.get("away", {})

                for player_data in [home_player, away_player]:
                    if not player_data:
                        continue

                    name = player_data.get("name")
                    if not name:
                        continue

                    # Initialize player if not seen before
                    if name not in players:
                        players[name] = {
                            "name": name,
                            "turn_data": [],  # Store each turn's marks and bulls
                            "max_qp": 0,  # Best single turn QP
                        }

                    # Parse this turn's score to get marks and bulls
                    turn_score = player_data.get("turn_score", "")
                    marks, bulls = self._parse_cricket_turn(turn_score)

                    # Store turn data
                    players[name]["turn_data"].append({"marks": marks, "bulls": bulls})

                    # Calculate QP for this turn
                    turn_qp = self._calculate_turn_qp(marks, bulls)

                    # Track the maximum QP from any single turn
                    if turn_qp > players[name]["max_qp"]:
                        players[name]["max_qp"] = turn_qp

            # Add game-level information
            game_info = {
                "game_name": "Cricket",
                "winner_index": game.get("winner_index"),
                "duration": game.get("duration"),
                "home_mpr": game.get("home", {}).get("mpr"),
                "away_mpr": game.get("away", {}).get("mpr"),
                "home_ending_marks": game.get("home", {}).get("ending_marks", 0),
                "away_ending_marks": game.get("away", {}).get("ending_marks", 0),
                "players": list(players.values()),
            }

            return game_info

        except Exception as e:
            self.logger.error(f"Error parsing cricket game: {e}")
            return None

    def _parse_cricket_turn(self, turn_score: str) -> tuple:
        """Parse a cricket turn score to count marks and bulls.

        Args:
            turn_score: Turn score string like "T20, S20" or "SB, DB, S19"
                        Supports xN multiplier: "SBx2", "DBx3", "S20x2"
                        Supports bare bull format: "B", "Bx2"

        Returns:
            Tuple of (marks, bulls) where:
            - marks = number of marks scored (hits on 15-20)
            - bulls = number of bull marks scored (SB=1, DB=2 per dart)
        """
        if not turn_score:
            return (0, 0)

        marks = 0
        bulls = 0

        # Split by comma and process each dart
        darts = [d.strip() for d in turn_score.split(",")]

        for dart in darts:
            # Determine xN multiplier (e.g., "SBx2" → 2, "T20x3" → 3)
            multiplier = 1
            if "x" in dart:
                try:
                    multiplier = int(dart.split("x")[1])
                except (ValueError, IndexError):
                    pass

            # Count bulls: SB (single bull=1 mark), DB (double bull=2 marks),
            # or bare B (single bull=1 mark)
            if dart.startswith("SB"):
                bulls += 1 * multiplier
            elif dart.startswith("DB"):
                bulls += 2 * multiplier
            elif dart.startswith("B"):
                # Bare "B" without S/D prefix — treat as single bull
                bulls += 1 * multiplier
            # Count marks on cricket numbers (15-20)
            elif any(num in dart for num in ["15", "16", "17", "18", "19", "20"]):
                if dart.startswith("T"):
                    marks += 3 * multiplier
                elif dart.startswith("D"):
                    marks += 2 * multiplier
                elif dart.startswith("S"):
                    marks += 1 * multiplier

        return (marks, bulls)

    def _calculate_turn_qp(self, marks: int, bulls: int) -> int:
        """Calculate QP for a single turn based on marks and bulls.

        QP Rules:
        5 QP: 9H, 6B, 3H+4B, 6H+2B
        4 QP: 8H, 5B, 2H+4B, 3H+3B, 5H+2B, 6H+1B
        3 QP: 7H, 4B, 1H+4B, 2H+3B, 4H+2B, 5H+1B
        2 QP: 6H, 3B, 1H+3B, 3H+2B, 4H+1B
        1 QP: 5H, 3H+1B, 2H+2B
        """
        # QP Level 5
        if (
            marks >= 9
            or bulls >= 6
            or (marks >= 3 and bulls >= 4)
            or (marks >= 6 and bulls >= 2)
        ):
            return 5

        # QP Level 4
        elif (
            marks >= 8
            or bulls >= 5
            or (marks >= 2 and bulls >= 4)
            or (marks >= 3 and bulls >= 3)
            or (marks >= 5 and bulls >= 2)
            or (marks >= 6 and bulls >= 1)
        ):
            return 4

        # QP Level 3
        elif (
            marks >= 7
            or bulls >= 4
            or (marks >= 1 and bulls >= 4)
            or (marks >= 2 and bulls >= 3)
            or (marks >= 4 and bulls >= 2)
            or (marks >= 5 and bulls >= 1)
        ):
            return 3

        # QP Level 2
        elif (
            marks >= 6
            or bulls >= 3
            or (marks >= 1 and bulls >= 3)
            or (marks >= 3 and bulls >= 2)
            or (marks >= 4 and bulls >= 1)
        ):
            return 2

        # QP Level 1
        elif marks >= 5 or (marks >= 3 and bulls >= 1) or (marks >= 2 and bulls >= 2):
            return 1

        # No QP
        else:
            return 0

    def calculate_cricket_qp(self, player_stats: Dict[str, Any]) -> int:
        """
        Get the maximum QP earned by a player in any single turn of the game.

        The QP has already been calculated per-turn in _parse_cricket_game().
        We simply return the max_qp value.

        Args:
            player_stats: Player statistics from cricket game with 'max_qp' field

        Returns:
            Maximum QP earned in any single turn (0-5)
        """
        return player_stats.get("max_qp", 0)

    def calculate_501_qp(
        self, total_score: int, checkout_score: Optional[int] = None
    ) -> int:
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
