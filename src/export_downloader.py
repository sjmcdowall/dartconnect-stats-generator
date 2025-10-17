"""DartConnect export downloader - automated CSV retrieval with secure credentials.

This module handles:
- Logging into DartConnect with email/password
- Navigating to export pages
- Downloading CSV files (by_leg_export, leaderboards)
- Saving to local data directory
- Credential security (environment variables, no repo storage)

Credentials are loaded from environment variables:
- DARTCONNECT_EMAIL: Your DartConnect email/username
- DARTCONNECT_PASSWORD: Your DartConnect password

Example:
    export DARTCONNECT_EMAIL="your.email@example.com"
    export DARTCONNECT_PASSWORD="your-password"
    
    from src.export_downloader import DartConnectExporter
    exporter = DartConnectExporter()
    files = exporter.download_exports("output/data")
"""

import os
import logging
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import re


class DartConnectExporter:
    """Handles automated downloading of DartConnect CSV exports."""
    
    BASE_URL = "https://my.dartconnect.com"
    LOGIN_URL = f"{BASE_URL}/default.aspx"
    
    # File patterns to look for when downloading
    EXPORT_PATTERNS = {
        'by_leg': r'by.?leg|by_leg',
        'cricket_leaderboard': r'cricket.*leaderboard|all_cricket_leaderboard',
        '501_leaderboard': r'(501|dartconnect).*leaderboard|all_01_leaderboard'
    }
    
    def __init__(self, timeout: int = 30, headless: bool = True):
        """
        Initialize the DartConnect exporter.
        
        Args:
            timeout: Request timeout in seconds
            headless: Whether to run browser in headless mode (if using Selenium)
        """
        self.timeout = timeout
        self.headless = headless
        self.logger = logging.getLogger(__name__)
        
        # Load credentials from environment
        self.email = os.getenv('DARTCONNECT_EMAIL')
        self.password = os.getenv('DARTCONNECT_PASSWORD')
        
        if not self.email or not self.password:
            raise ValueError(
                "DartConnect credentials not found in environment variables.\n"
                "Please set:\n"
                "  export DARTCONNECT_EMAIL='your.email@example.com'\n"
                "  export DARTCONNECT_PASSWORD='your-password'\n"
                "For security, never commit these to git."
            )
        
        # Create a session with retry strategy
        self.session = self._create_session()
        
        self.logger.info("DartConnectExporter initialized")
    
    def _create_session(self) -> requests.Session:
        """Create a requests session with retry strategy."""
        session = requests.Session()
        
        # Retry strategy: retry on connection errors, timeouts, and specific HTTP errors
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "OPTIONS", "POST"]
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        # Set user agent
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        })
        
        return session
    
    def login(self) -> bool:
        """
        Log into DartConnect.
        
        Returns:
            True if login successful, False otherwise
        """
        try:
            self.logger.info("Attempting to log into DartConnect...")
            
            # First, get the login page to extract any necessary tokens/viewstate
            response = self.session.get(self.LOGIN_URL, timeout=self.timeout)
            response.raise_for_status()
            
            # Extract ViewState and other ASP.NET form fields if needed
            viewstate = self._extract_viewstate(response.text)
            
            # Prepare login data
            login_data = {
                'txtEmail': self.email,
                'txtPassword': self.password,
                'cmdLogin': 'Login',
                '__VIEWSTATE': viewstate if viewstate else ''
            }
            
            # Submit login form
            response = self.session.post(
                self.LOGIN_URL,
                data=login_data,
                timeout=self.timeout,
                allow_redirects=True
            )
            response.raise_for_status()
            
            # Check if login was successful by looking for common indicators
            if self._is_logged_in(response.text):
                self.logger.info("✅ Successfully logged into DartConnect")
                return True
            else:
                self.logger.error("❌ Login failed - check credentials")
                return False
                
        except Exception as e:
            self.logger.error(f"❌ Login error: {e}")
            return False
    
    def _extract_viewstate(self, html_content: str) -> Optional[str]:
        """Extract ASP.NET __VIEWSTATE from HTML form."""
        try:
            pattern = r'<input[^>]+name="__VIEWSTATE"[^>]+value="([^"]*)"'
            match = re.search(pattern, html_content)
            if match:
                return match.group(1)
        except Exception as e:
            self.logger.debug(f"Could not extract ViewState: {e}")
        return None
    
    def _is_logged_in(self, html_content: str) -> bool:
        """Check if the page indicates successful login."""
        # Look for indicators of successful login
        # This is a basic check - adjust based on actual DartConnect page structure
        indicators = [
            'Dashboard',
            'League',
            'My Performance',
            'logout',  # logout link appears when logged in
            'Statistics'
        ]
        
        content_lower = html_content.lower()
        return any(indicator.lower() in content_lower for indicator in indicators)
    
    def download_exports(self, output_dir: str) -> Dict[str, Path]:
        """
        Download DartConnect CSV exports.
        
        Args:
            output_dir: Directory to save the CSV files
            
        Returns:
            Dictionary with file types and their paths: {'by_leg': Path, ...}
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        downloaded_files = {}
        
        try:
            # Login first
            if not self.login():
                raise RuntimeError("Failed to login to DartConnect")
            
            self.logger.info("🔍 Searching for export links...")
            
            # Find export links - this will need to be updated based on screenshots
            export_links = self._find_export_links()
            
            if not export_links:
                self.logger.warning("⚠️ No export links found on the page")
                return downloaded_files
            
            # Download each export file
            for file_type, url in export_links.items():
                try:
                    self.logger.info(f"📥 Downloading {file_type}...")
                    file_path = self._download_file(url, output_path, file_type)
                    if file_path:
                        downloaded_files[file_type] = file_path
                        self.logger.info(f"✅ Saved: {file_path}")
                except Exception as e:
                    self.logger.error(f"❌ Failed to download {file_type}: {e}")
            
            return downloaded_files
            
        except Exception as e:
            self.logger.error(f"❌ Export download failed: {e}")
            return downloaded_files
    
    def _find_export_links(self) -> Dict[str, str]:
        """
        Find export links on the DartConnect page.
        
        Returns:
            Dictionary mapping file types to download URLs
        """
        # This will be implemented after we see the export page structure
        # For now, returning empty dict as placeholder
        export_links = {}
        
        try:
            # Navigate to league/stats page
            response = self.session.get(f"{self.BASE_URL}/dashboard", timeout=self.timeout)
            
            # Look for export links in the page
            # This needs to be updated based on actual page structure (from screenshots)
            
            self.logger.debug("Searching page for export links...")
            
        except Exception as e:
            self.logger.error(f"Error finding export links: {e}")
        
        return export_links
    
    def _download_file(self, url: str, output_dir: Path, file_type: str) -> Optional[Path]:
        """
        Download a single file.
        
        Args:
            url: Download URL
            output_dir: Directory to save the file
            file_type: Type of file (for naming)
            
        Returns:
            Path to downloaded file, or None if failed
        """
        try:
            response = self.session.get(url, timeout=self.timeout, stream=True)
            response.raise_for_status()
            
            # Extract filename from Content-Disposition header or URL
            filename = self._get_filename(response, url, file_type)
            
            file_path = output_dir / filename
            
            # Download file
            with open(file_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            
            self.logger.info(f"Downloaded {len(response.content)} bytes")
            return file_path
            
        except Exception as e:
            self.logger.error(f"Download failed for {url}: {e}")
            return None
    
    def _get_filename(self, response: requests.Response, url: str, file_type: str) -> str:
        """Extract or generate filename for downloaded file."""
        # Try to get from Content-Disposition header
        if 'Content-Disposition' in response.headers:
            try:
                content_disp = response.headers['Content-Disposition']
                match = re.search(r'filename="?([^"]+)"?', content_disp)
                if match:
                    return match.group(1)
            except Exception:
                pass
        
        # Try to get from URL
        if '/' in url:
            url_filename = url.split('/')[-1]
            if url_filename and '.' in url_filename:
                return url_filename
        
        # Generate filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        return f"{file_type}_{timestamp}.csv"
    
    def close(self):
        """Close the session."""
        self.session.close()
        self.logger.info("Session closed")


def main():
    """Command-line interface for downloading exports."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Download DartConnect CSV exports',
        epilog='Credentials must be set via environment variables: DARTCONNECT_EMAIL, DARTCONNECT_PASSWORD'
    )
    parser.add_argument(
        '--output-dir', '-o',
        type=str,
        default='data',
        help='Output directory for CSV files (default: data/)'
    )
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose logging'
    )
    
    args = parser.parse_args()
    
    # Setup logging
    level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Download exports
    try:
        exporter = DartConnectExporter()
        files = exporter.download_exports(args.output_dir)
        
        if files:
            print(f"\n✅ Downloaded {len(files)} file(s):")
            for file_type, path in files.items():
                print(f"  • {file_type}: {path}")
        else:
            print("\n⚠️ No files were downloaded")
        
        exporter.close()
        
    except ValueError as e:
        print(f"\n❌ Configuration error: {e}")
        return 1
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return 1
    
    return 0


if __name__ == '__main__':
    exit(main())