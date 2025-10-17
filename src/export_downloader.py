"""DartConnect export downloader - automated CSV retrieval with secure credentials.

This module handles:
- Logging into DartConnect with email/password
- Navigating to export pages using Selenium (for JavaScript rendering)
- Downloading CSV files (by_leg_export)
- Saving to local data directory
- Credential security (environment variables, no repo storage)

Credentials are loaded from environment variables:
- DARTCONNECT_EMAIL: Your DartConnect email/username
- DARTCONNECT_PASSWORD: Your DartConnect password

Requirements:
- selenium (pip install selenium)
- webdriver-manager (pip install webdriver-manager)

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

try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import Select, WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.chrome.service import Service
    from webdriver_manager.chrome import ChromeDriverManager
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False


class DartConnectExporter:
    """Handles automated downloading of DartConnect CSV exports."""
    
    BASE_URL = "https://my.dartconnect.com"
    LOGIN_URL = f"{BASE_URL}/"
    
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
        output_path = Path(output_dir).resolve()
        output_path.mkdir(parents=True, exist_ok=True)
        
        try:
            # Full Selenium-driven workflow: login + navigate + export
            file_path = self._selenium_download_by_leg(output_path)
            return {'by_leg': file_path} if file_path else {}
        except Exception as e:
            self.logger.error(f"❌ Export download failed: {e}")
            return {}
    
    def _selenium_download_by_leg(self, download_dir: Path) -> Optional[Path]:
        """Login via Selenium and download the By Leg CSV to download_dir.
        
        Flow:
        1) Open my.dartconnect.com and log in with email/password
        2) Dismiss any modal, click Manage League to enter league.dartconnect.com
        3) Ensure Home tab active
        4) In CSV Reports, set All Divisions / Regular Season / By Leg
        5) Click Export Report and wait for CSV to appear in download_dir
        """
        if not SELENIUM_AVAILABLE:
            self.logger.error("Selenium not installed. pip install selenium webdriver-manager")
            return None
        
        driver = None
        try:
            options = webdriver.ChromeOptions()
            prefs = {
                "download.default_directory": str(download_dir),
                "download.prompt_for_download": False,
                "safebrowsing.enabled": False
            }
            options.add_experimental_option("prefs", prefs)
            if self.headless:
                options.add_argument("--headless=new")
            options.add_argument("--window-size=1400,900")
            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=options)
            wait = WebDriverWait(driver, 20)
            
            # 1) Login at my.dartconnect.com
            self.logger.info("Opening My DartConnect login page...")
            driver.get(self.LOGIN_URL)
            
            # Find email/username field
            def find_email_input():
                candidates = [
                    (By.CSS_SELECTOR, "input[type='email']"),
                    (By.CSS_SELECTOR, "input[name*='email']"),
                    (By.CSS_SELECTOR, "input[id*='email']"),
                    (By.CSS_SELECTOR, "input[placeholder*='Email']"),
                    (By.CSS_SELECTOR, "input[type='text']")
                ]
                for by, sel in candidates:
                    try:
                        el = driver.find_element(by, sel)
                        if el.is_displayed():
                            return el
                    except Exception:
                        continue
                return None
            
            email_el = find_email_input()
            if not email_el:
                # The site might load via JS; wait briefly and retry
                time.sleep(2)
                email_el = find_email_input()
            if not email_el:
                raise RuntimeError("Could not locate email/username input on login page")
            email_el.clear(); email_el.send_keys(self.email)
            
            # Password field
            pwd_el = None
            for by, sel in [
                (By.CSS_SELECTOR, "input[type='password']"),
                (By.CSS_SELECTOR, "input[name*='password']"),
                (By.CSS_SELECTOR, "input[id*='password']"),
            ]:
                try:
                    pwd_el = driver.find_element(by, sel)
                    if pwd_el.is_displayed():
                        break
                except Exception:
                    continue
            if not pwd_el:
                raise RuntimeError("Could not locate password input on login page")
            pwd_el.clear(); pwd_el.send_keys(self.password)
            
            # Click Login button
            login_btn = None
            for by, sel in [
                (By.XPATH, "//button[contains(., 'Login')]"),
                (By.XPATH, "//input[@type='submit' and (contains(@value,'Login') or contains(@value,'Sign'))]")
            ]:
                try:
                    login_btn = driver.find_element(by, sel)
                    if login_btn.is_displayed():
                        break
                except Exception:
                    continue
            if not login_btn:
                raise RuntimeError("Could not find Login button")
            login_btn.click()
            
            # 2) Wait for competition organizer page and click Manage League
            # Possible direct landing to Competition Organizer
            time.sleep(3)
            
            # Dismiss any modal if present
            try:
                dismiss = driver.find_element(By.XPATH, "//button[contains(., 'Dismiss') or contains(., 'Got it') or contains(., 'Ok')]")
                if dismiss.is_displayed():
                    dismiss.click()
                    time.sleep(1)
            except Exception:
                pass
            
            # Click Manage League in "My Leagues" table
            try:
                manage_link = driver.find_element(By.LINK_TEXT, "Manage League")
                manage_link.click()
            except Exception:
                # If already in league portal, ignore
                self.logger.debug("Manage League link not found; assuming already in league portal")
            
            # 3) Ensure Home tab
            try:
                home_tab = wait.until(EC.element_to_be_clickable((By.LINK_TEXT, "Home")))
                home_tab.click()
            except Exception:
                pass
            
            # 4) Configure CSV Reports dropdowns
            # Gather selects present in order
            selects = wait.until(EC.presence_of_all_elements_located((By.TAG_NAME, "select")))
            if len(selects) < 3:
                raise RuntimeError("CSV Reports selectors not found")
            try:
                Select(selects[0]).select_by_visible_text("All Divisions")
            except Exception:
                pass
            try:
                Select(selects[1]).select_by_visible_text("Regular Season")
            except Exception:
                pass
            try:
                # Some pages prefix report type group like "Season Analysis – By Leg"
                Select(selects[2]).select_by_visible_text("By Leg")
            except Exception:
                # Fallback: pick first option that contains 'By Leg'
                opts = selects[2].find_elements(By.TAG_NAME, 'option')
                for o in opts:
                    if 'by leg' in o.text.lower():
                        o.click(); break
            
            # 5) Click Export Report
            export_btn = driver.find_element(By.XPATH, "//button[contains(., 'Export Report')]")
            export_btn.click()
            
            # Wait for CSV to appear in download_dir (simple poll by newest file)
            self.logger.info("Waiting for CSV download...")
            end = time.time() + 30
            last_size = -1
            csv_path = None
            while time.time() < end:
                csvs = sorted(download_dir.glob("*.csv"), key=lambda p: p.stat().st_mtime, reverse=True)
                if csvs:
                    latest = csvs[0]
                    size = latest.stat().st_size
                    if size > 0 and size == last_size:
                        csv_path = latest
                        break
                    last_size = size
                time.sleep(1)
            if not csv_path:
                raise RuntimeError("CSV download not detected in time")
            self.logger.info(f"CSV downloaded: {csv_path}")
            return csv_path
        except Exception as e:
            self.logger.error(f"Selenium workflow failed: {e}")
            return None
        finally:
            if driver:
                driver.quit()
                self.logger.debug("Browser closed")
    
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