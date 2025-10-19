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
    
    def download_exports(self, output_dir: str, assist: bool = False) -> Dict[str, Path]:
        """
        Download DartConnect CSV exports.
        
        Args:
            output_dir: Directory to save the CSV files
            assist: If True, opens portal and waits while user clicks Export
            
        Returns:
            Dictionary with file types and their paths: {'by_leg': Path, ...}
        """
        output_path = Path(output_dir).resolve()
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Archive existing by_leg files before downloading new ones
        self._archive_existing_by_leg_files(output_path)
        
        try:
            if assist:
                file_path = self._selenium_assist_download(output_path)
            else:
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
            
            # 2) Navigate to Competition Organizer and click Manage League
            time.sleep(3)
            
            # Dismiss any modal if present
            try:
                dismiss = driver.find_element(By.XPATH, "//button[contains(., 'Dismiss') or contains(., 'Got it') or contains(., 'Ok')]")
                if dismiss.is_displayed():
                    dismiss.click()
                    time.sleep(1)
            except Exception:
                pass
            
            # Click Competition Organizer in the top nav
            comp_clicked = False
            for by, sel in [
                (By.LINK_TEXT, "Competition Organizer"),
                (By.XPATH, "//a[contains(., 'Competition Organizer')]")
            ]:
                try:
                    comp = driver.find_element(by, sel)
                    comp.click(); comp_clicked = True; break
                except Exception:
                    continue
            if not comp_clicked:
                self.logger.debug("Could not click Competition Organizer; continuing")
            time.sleep(1)
            
            # In 'My Leagues' table, click Manage League
            manage_clicked = False
            # Look for the wire:click button for Manage League
            manage_selectors = [
                (By.XPATH, "//button[contains(@wire:click, 'loginLeaguePortal')]"),
                (By.XPATH, "//button[.//span[contains(text(), 'Manage League')]]"),
                (By.XPATH, "//button[contains(., 'Manage League')]"),
                (By.LINK_TEXT, "Manage League"),
                (By.XPATH, "//a[contains(., 'Manage League')]")
            ]
            
            for by, sel in manage_selectors:
                try:
                    ml = driver.find_element(by, sel)
                    ml.click(); manage_clicked = True; break
                except Exception:
                    continue
            if not manage_clicked:
                self.logger.error("Manage League link not found - staying on Competition Organizer page")
                # Don't use direct URL as it redirects back to dashboard
                # Instead, dump the page content to see what's available
                if self.logger.level <= logging.DEBUG:
                    organizer_file = Path("debug_organizer_page.html")
                    with open(organizer_file, "w", encoding="utf-8") as f:
                        f.write(driver.page_source)
                    self.logger.debug(f"Dumped Competition Organizer HTML to {organizer_file}")
            
            # 3) Wait for league portal to fully load (handle "Please wait a moment..." screen)
            self._wait_for_league_portal_load(driver, wait)
            
            # Debug: Dump HTML to understand page structure
            if self.logger.level <= logging.DEBUG:
                html_file = Path("debug_league_page.html")
                with open(html_file, "w", encoding="utf-8") as f:
                    f.write(driver.page_source)
                self.logger.debug(f"Dumped page HTML to {html_file}")
                
                # Log available elements for debugging
                self.logger.debug(f"Current URL: {driver.current_url}")
                self.logger.debug(f"Page title: {driver.title}")
                
                # Find all links and buttons
                links = driver.find_elements(By.TAG_NAME, "a")
                self.logger.debug(f"Found {len(links)} links on page")
                for i, link in enumerate(links[:10]):  # Show first 10
                    try:
                        text = link.text.strip()
                        href = link.get_attribute("href") or ""
                        if text:
                            self.logger.debug(f"  Link {i}: '{text}' -> {href}")
                    except Exception:
                        pass
                        
                buttons = driver.find_elements(By.TAG_NAME, "button")
                self.logger.debug(f"Found {len(buttons)} buttons on page")
                for i, btn in enumerate(buttons[:10]):  # Show first 10
                    try:
                        text = btn.text.strip()
                        onclick = btn.get_attribute("onclick") or ""
                        if text or onclick:
                            self.logger.debug(f"  Button {i}: '{text}' onclick='{onclick[:50]}'")
                    except Exception:
                        pass
            
            # Click Home tab to reveal CSV Reports section
            home_clicked = False
            
            # More specific selectors based on the league portal navigation
            home_selectors = [
                (By.XPATH, "//a[normalize-space(text())='Home' and contains(@href, '#')]"),
                (By.LINK_TEXT, "Home"),
                (By.PARTIAL_LINK_TEXT, "Home"), 
                (By.XPATH, "//a[contains(text(), 'Home')]"),
                (By.CSS_SELECTOR, "a[href='#']"),
                (By.CSS_SELECTOR, "a[href='https://league.dartconnect.com/#']"),
            ]
            
            self.logger.debug("Looking for Home tab...")
            for by, selector in home_selectors:
                try:
                    home_elements = driver.find_elements(by, selector)
                    self.logger.debug(f"Found {len(home_elements)} elements with selector {by}, {selector}")
                    
                    for home_tab in home_elements:
                        if home_tab.is_displayed() and home_tab.is_enabled():
                            text = home_tab.text.strip()
                            href = home_tab.get_attribute('href') or ''
                            self.logger.debug(f"Trying Home tab: text='{text}', href='{href}'")
                            
                            if 'home' in text.lower() or href.endswith('#'):
                                # Use JavaScript click to avoid interception issues
                                driver.execute_script("arguments[0].scrollIntoView({block:'center'});", home_tab)
                                time.sleep(1)  # Wait after scroll
                                driver.execute_script("arguments[0].click();", home_tab)
                                self.logger.debug(f"Clicked Home tab with JavaScript: text '{text}', href '{href}'")
                                home_clicked = True
                                time.sleep(3)  # Wait for content to load
                                break
                                
                    if home_clicked:
                        break
                        
                except Exception as e:
                    self.logger.debug(f"Home selector failed {by}, {selector}: {e}")
                    continue
            
            # If still not found, try to navigate to the Home section directly via URL
            if not home_clicked:
                self.logger.debug("Direct Home tab click failed, trying URL fragment approach")
                try:
                    current_url = driver.current_url
                    if '#' not in current_url:
                        driver.get(current_url + '#')
                        time.sleep(3)
                        home_clicked = True
                        self.logger.debug("Navigated to Home via URL fragment")
                except Exception as e:
                    self.logger.debug(f"URL fragment approach failed: {e}")
                    
            if not home_clicked:
                self.logger.warning("Could not find or click Home tab - CSV Reports may not be accessible")
            
            # 4) Configure CSV Reports dropdowns using specific IDs
            # Use longer timeout for dropdowns
            long_wait = WebDriverWait(driver, 30)
            
            # Scroll to CSV Reports section first
            try:
                csv_section = driver.find_element(By.XPATH, "//div[contains(text(), 'CSV Reports')]")
                driver.execute_script("arguments[0].scrollIntoView({block:'center'});", csv_section)
                time.sleep(2)
            except Exception:
                pass
            
            # Wait for and configure Division dropdown
            try:
                self.logger.debug("Looking for division dropdown...")
                division_dropdown = long_wait.until(EC.presence_of_element_located((By.ID, "report_division_id")))
                self.logger.debug("Found division dropdown, checking if clickable...")
                WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.ID, "report_division_id")))
                Select(division_dropdown).select_by_visible_text("All Divisions")
                self.logger.debug("Selected All Divisions")
            except Exception as e:
                self.logger.debug(f"Division selection failed: {e}")
            
            # Wait for and configure Season dropdown  
            try:
                self.logger.debug("Looking for season dropdown...")
                season_dropdown = long_wait.until(EC.presence_of_element_located((By.ID, "report_season_status")))
                self.logger.debug("Found season dropdown, checking if clickable...")
                WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.ID, "report_season_status")))
                Select(season_dropdown).select_by_visible_text("Regular Season")
                self.logger.debug("Selected Regular Season")
            except Exception as e:
                self.logger.debug(f"Season selection failed: {e}")
            
            # Wait for report selection dropdown to be ready
            time.sleep(2)
            # Wait for and configure Report Type dropdown
            try:
                self.logger.debug("Looking for report selection dropdown...")
                report_dropdown = long_wait.until(EC.presence_of_element_located((By.ID, "report_selection")))
                self.logger.debug("Found report dropdown, checking if clickable...")
                WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.ID, "report_selection")))
                
                # Debug: show available options in the report type dropdown
                if self.logger.level <= logging.DEBUG:
                    opts = report_dropdown.find_elements(By.TAG_NAME, 'option')
                    self.logger.debug(f"Report type dropdown has {len(opts)} options:")
                    for i, opt in enumerate(opts):
                        text = opt.text.strip() or opt.get_attribute('value') or ''
                        self.logger.debug(f"  Option {i}: '{text}'")
            
                # Try multiple strategies to select By Leg
                by_leg_selected = False
                report_select = Select(report_dropdown)
                strategies = [
                    lambda: report_select.select_by_visible_text("By Leg"),
                    lambda: report_select.select_by_partial_text("By Leg"),
                    lambda: report_select.select_by_value("/league-export/seasonperformancebyleg/"),
                ]
                
                for strategy in strategies:
                    try:
                        strategy()
                        by_leg_selected = True
                        self.logger.debug("Successfully selected By Leg option")
                        break
                    except Exception as e:
                        self.logger.debug(f"Selection strategy failed: {e}")
                        continue
                
                if not by_leg_selected:
                    # Manual fallback: find and click option containing 'by leg'
                    opts = report_dropdown.find_elements(By.TAG_NAME, 'option')
                    for opt in opts:
                        text = opt.text.lower()
                        value = opt.get_attribute('value') or ''
                        if 'by leg' in text or 'byleg' in text or 'seasonperformancebyleg' in value:
                            opt.click()
                            by_leg_selected = True
                            self.logger.debug(f"Manually selected option: '{opt.text}' (value: '{value}')")
                            break
                            
                if not by_leg_selected:
                    self.logger.warning("Could not select By Leg option - using default selection")
            except Exception as e:
                self.logger.error(f"Report dropdown configuration failed: {e}")
            
            # 5) Wait and click Export Report button
            time.sleep(2)  # Give page time to update after dropdown selection
            
            export_selectors = [
                (By.ID, "rexport_report"),  # Use the specific ID from the logs
                (By.XPATH, "//button[contains(., 'Export Report')]"),
                (By.XPATH, "//button[contains(text(), 'Export Report')]"),
                (By.XPATH, "//input[@value='Export Report']"),
                (By.XPATH, "//input[@type='submit' and contains(@value, 'Export')]"),
            ]
            
            export_clicked = False
            for by, selector in export_selectors:
                try:
                    # Wait for the button to be clickable
                    export_btn = wait.until(EC.element_to_be_clickable((by, selector)))
                    
                    # Scroll into view and click
                    driver.execute_script("arguments[0].scrollIntoView({block:'center'});", export_btn)
                    time.sleep(1)  # Brief pause after scroll
                    driver.execute_script("arguments[0].click();", export_btn)
                    
                    self.logger.debug(f"Clicked Export Report with selector: {by}, {selector}")
                    export_clicked = True
                    break
                    
                except Exception as e:
                    self.logger.debug(f"Export selector failed {by}, {selector}: {e}")
                    continue
                    
            if not export_clicked:
                # Final debug: show what buttons are actually available
                buttons = driver.find_elements(By.TAG_NAME, "button")
                inputs = driver.find_elements(By.XPATH, "//input[@type='submit' or @type='button']")
                self.logger.error(f"Export button not found. Available buttons: {len(buttons)}, inputs: {len(inputs)}")
                for i, btn in enumerate(buttons):
                    try:
                        text = btn.text.strip()
                        onclick = btn.get_attribute("onclick") or ""
                        if text or onclick:
                            self.logger.error(f"  Button {i}: '{text}' onclick='{onclick[:50]}'")
                    except Exception:
                        pass
                for i, inp in enumerate(inputs):
                    try:
                        value = inp.get_attribute("value") or ""
                        onclick = inp.get_attribute("onclick") or ""
                        if value or onclick:
                            self.logger.error(f"  Input {i}: value='{value}' onclick='{onclick[:50]}'")
                    except Exception:
                        pass
                raise RuntimeError("Could not find any Export Report button")
            
            # Wait for CSV to appear in download_dir (simple poll by newest file)
            self.logger.info("Waiting for CSV download...")
            return self._wait_for_csv(download_dir, timeout=60)
        except Exception as e:
            self.logger.error(f"Selenium workflow failed: {e}")
            return None
        finally:
            if driver:
                driver.quit()
                self.logger.debug("Browser closed")
    
    def _wait_for_league_portal_load(self, driver, wait):
        """Wait for the league portal loading screen to disappear and page to be ready."""
        try:
            # Wait for the loading text to disappear
            wait.until_not(
                EC.text_to_be_present_in_element(
                    (By.TAG_NAME, "body"), 
                    "Please wait a moment"
                )
            )
            self.logger.debug("Loading screen disappeared")
            
            # Additional wait for page elements to be ready
            time.sleep(3)
            
            # Wait for navigation elements to be present
            try:
                wait.until(
                    EC.any_of(
                        EC.presence_of_element_located((By.LINK_TEXT, "Home")),
                        EC.presence_of_element_located((By.TAG_NAME, "select"))
                    )
                )
                self.logger.debug("Page elements loaded")
            except Exception:
                # Fallback - just wait a bit more
                time.sleep(5)
                
        except Exception as e:
            self.logger.debug(f"Loading wait completed with exception: {e}")
            # Continue anyway - might already be loaded
            time.sleep(5)
    
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
    
    def _wait_for_csv(self, download_dir: Path, timeout: int = 60) -> Optional[Path]:
        end = time.time() + timeout
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
        if csv_path:
            self.logger.info(f"CSV downloaded: {csv_path}")
        return csv_path
    
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
    
    def _selenium_assist_download(self, download_dir: Path) -> Optional[Path]:
        """Automated mode: log in, navigate, and export CSV with progress indicators."""
        if not SELENIUM_AVAILABLE:
            print("❌ Selenium not installed. Run: pip install selenium webdriver-manager")
            return None
        
        driver = None
        try:
            print("🔧 Starting browser...")
            options = webdriver.ChromeOptions()
            prefs = {
                "download.default_directory": str(download_dir),
                "download.prompt_for_download": False,
                "safebrowsing.enabled": False
            }
            options.add_experimental_option("prefs", prefs)
            # Use visible browser for now (debugging headless mode)
            options.add_argument("--window-size=1400,900")
            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=options)
            
            print("🔑 Logging into DartConnect...", end=" ")
            driver.get(self.LOGIN_URL)
            time.sleep(2)
            
            # Find and fill login form
            email_el = None
            for by, sel in [
                (By.CSS_SELECTOR, "input[type='email']"),
                (By.CSS_SELECTOR, "input[name*='email']"),
                (By.CSS_SELECTOR, "input[id*='email']"),
                (By.CSS_SELECTOR, "input[type='text']"),
            ]:
                try:
                    email_el = driver.find_element(by, sel)
                    if email_el.is_displayed(): break
                except Exception: continue
            
            if not email_el:
                print("❌ FAILED - Login form not found")
                return None
            
            email_el.clear()
            email_el.send_keys(self.email)
            pwd_el = driver.find_element(By.CSS_SELECTOR, "input[type='password']")
            pwd_el.clear()
            pwd_el.send_keys(self.password)
            btn = driver.find_element(By.XPATH, "//button[contains(., 'Login')]")
            btn.click()
            time.sleep(3)
            print("✅ SUCCESS!")
            
            print("📂 Navigating to Competition Organizer...", end=" ")
            # Dismiss any modal
            try:
                dismiss = driver.find_element(By.XPATH, "//button[contains(., 'Dismiss') or contains(., 'Got it') or contains(., 'Ok')]")
                if dismiss.is_displayed():
                    dismiss.click()
                    time.sleep(1)
            except Exception:
                pass
            
            # Click Competition Organizer
            comp_clicked = False
            for by, sel in [
                (By.LINK_TEXT, "Competition Organizer"),
                (By.XPATH, "//a[contains(., 'Competition Organizer')]")
            ]:
                try:
                    el = driver.find_element(by, sel)
                    el.click()
                    comp_clicked = True
                    break
                except Exception:
                    continue
            
            if not comp_clicked:
                print("❌ FAILED - Could not find Competition Organizer")
                return None
            print("✅ SUCCESS!")
            
            print("🎯 Accessing League Portal...", end=" ")
            time.sleep(2)
            
            # Click Manage League
            manage_clicked = False
            for by, sel in [
                (By.LINK_TEXT, "Manage League"),
                (By.XPATH, "//a[contains(., 'Manage League')]")
            ]:
                try:
                    ml = driver.find_element(by, sel)
                    ml.click()
                    manage_clicked = True
                    break
                except Exception:
                    continue
            
            if not manage_clicked:
                # Fallback: direct URL
                driver.get("https://league.dartconnect.com/")
            
            time.sleep(2)
            print("✅ SUCCESS!")
            
            print("⏳ Waiting for portal to load...", end=" ")
            # Wait for the "Please wait a moment..." loading screen to disappear
            self._wait_for_league_portal_load(driver, WebDriverWait(driver, 30))
            print("✅ SUCCESS!")
            
            print("📊 Configuring CSV Export...", end=" ")
            # Click Home tab to reveal CSV Reports
            try:
                home_tab = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.LINK_TEXT, "Home"))
                )
                home_tab.click()
                time.sleep(2)  # Wait for CSV Reports section to load
            except Exception:
                # Try alternate Home tab selector
                try:
                    home_tab = driver.find_element(By.XPATH, "//a[contains(text(), 'Home')]")
                    home_tab.click()
                    time.sleep(2)
                except Exception:
                    pass  # Continue anyway
            
            # Configure dropdowns with retry logic
            time.sleep(2)
            selects = driver.find_elements(By.TAG_NAME, "select")
            if len(selects) >= 3:
                # Division
                try:
                    Select(selects[0]).select_by_visible_text("All Divisions")
                except Exception:
                    try:
                        Select(selects[0]).select_by_index(0)
                    except Exception:
                        pass
                
                # Season
                try:
                    Select(selects[1]).select_by_visible_text("Regular Season")
                except Exception:
                    try:
                        Select(selects[1]).select_by_index(0)
                    except Exception:
                        pass
                
                # Report Type
                try:
                    Select(selects[2]).select_by_visible_text("By Leg")
                except Exception:
                    # Find option containing 'By Leg'
                    options = selects[2].find_elements(By.TAG_NAME, "option")
                    for opt in options:
                        if 'by leg' in opt.text.lower():
                            opt.click()
                            break
            print("✅ SUCCESS!")
            
            print("📥 Downloading By Leg CSV...", end=" ")
            
            # Wait for any loading spinners to disappear
            try:
                spinner_selectors = [
                    (By.CLASS_NAME, "spinner"),
                    (By.CLASS_NAME, "loading"),
                    (By.XPATH, "//*[contains(@class,'spinner')]"),
                    (By.XPATH, "//*[contains(@class,'loading')]"),
                    (By.TAG_NAME, "ngx-spinner"),
                ]
                
                for by, selector in spinner_selectors:
                    try:
                        WebDriverWait(driver, 5).until(
                            EC.invisibility_of_element_located((by, selector))
                        )
                        self.logger.debug(f"Loading spinner disappeared: {selector}")
                    except:
                        pass  # Spinner not found or already gone
                
                # Extra wait to ensure page is fully rendered
                time.sleep(2)
            except:
                pass
            
            # Click Export Report
            try:
                # Wait for Export Report button to appear after Home tab click
                export_btn = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Export Report')]")))  
                driver.execute_script("arguments[0].scrollIntoView({block:'center'});", export_btn)
                driver.execute_script("arguments[0].click();", export_btn)
            except Exception as e:
                # Try input type Export button
                try:
                    export_btn = driver.find_element(By.XPATH, "//input[@value='Export Report']")
                    driver.execute_script("arguments[0].click();", export_btn)
                except Exception:
                    print(f"❌ FAILED - Export button: {e}")
                    return None
            
            # Wait for CSV with timeout
            csv = self._wait_for_csv(download_dir, timeout=30)
            if csv:
                print("✅ SUCCESS!")
                return csv
            else:
                print("❌ FAILED - CSV not downloaded in time")
                return None
                
        except Exception as e:
            print(f"❌ FAILED - {e}")
            return None
        finally:
            if driver:
                driver.quit()
    
    def _archive_existing_by_leg_files(self, output_dir: Path) -> None:
        """
        Archive existing by_leg CSV files with timestamp before downloading new ones.
        
        Files are moved to an 'archive' subdirectory to keep the main data folder clean.
        """
        try:
            # Find existing by_leg files
            by_leg_files = []
            for pattern in ['*by_leg*.csv', '*By_Leg*.csv', '*by-leg*.csv']:
                by_leg_files.extend(list(output_dir.glob(pattern)))
            
            if not by_leg_files:
                self.logger.debug("No existing by_leg files to archive")
                return
            
            # Create archive directory if it doesn't exist
            archive_dir = output_dir / "archive"
            archive_dir.mkdir(exist_ok=True)
            
            # Create timestamp for archiving
            from datetime import datetime
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            
            archived_count = 0
            for file_path in by_leg_files:
                try:
                    # Create archived filename with timestamp
                    name_parts = file_path.stem.split('.')
                    archived_name = f"{name_parts[0]}_archived_{timestamp}.csv"
                    archived_path = archive_dir / archived_name
                    
                    # Move the file to archive directory
                    file_path.rename(archived_path)
                    archived_count += 1
                    self.logger.info(f"📁 Archived: {file_path.name} → archive/{archived_name}")
                    
                except Exception as e:
                    self.logger.warning(f"Could not archive {file_path.name}: {e}")
            
            if archived_count > 0:
                self.logger.info(f"✅ Archived {archived_count} existing by_leg file(s) to archive/ folder")
                
        except Exception as e:
            self.logger.warning(f"File archiving failed: {e} - continuing with download")
    
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