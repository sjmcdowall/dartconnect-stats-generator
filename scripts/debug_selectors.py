#!/usr/bin/env python3
"""Debug script to inspect export page HTML and find reliable selectors."""

import sys
import os
import time
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.export_downloader import DartConnectExporter, SELENIUM_AVAILABLE

if not SELENIUM_AVAILABLE:
    print("❌ Selenium not installed")
    sys.exit(1)

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select, WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager


def main():
    """Navigate to export page and inspect HTML."""
    exporter = DartConnectExporter(headless=False)  # Show browser
    driver = None
    
    try:
        options = webdriver.ChromeOptions()
        options.add_argument("--window-size=1400,900")
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
        
        print("🔑 Logging in...")
        driver.get(exporter.LOGIN_URL)
        time.sleep(1)
        
        # Login
        email_el = driver.find_element(By.CSS_SELECTOR, "input[type='email']")
        email_el.send_keys(exporter.email)
        pwd_el = driver.find_element(By.CSS_SELECTOR, "input[type='password']")
        pwd_el.send_keys(exporter.password)
        btn = driver.find_element(By.XPATH, "//button[contains(., 'Login')]")
        btn.click()
        time.sleep(3)
        
        print("📂 Navigating to Competition Organizer...")
        try:
            dismiss = driver.find_element(By.XPATH, "//button[contains(., 'Dismiss') or contains(., 'Got it')]")
            dismiss.click()
            time.sleep(1)
        except:
            pass
        
        comp = driver.find_element(By.LINK_TEXT, "Competition Organizer")
        comp.click()
        time.sleep(1)
        
        print("🎯 Clicking Manage League...")
        ml = driver.find_element(By.LINK_TEXT, "Manage League")
        ml.click()
        time.sleep(2)
        
        print("📋 Clicking Home tab...")
        home_tab = driver.find_element(By.LINK_TEXT, "Home")
        home_tab.click()
        time.sleep(2)
        
        print("\n" + "="*60)
        print("EXPORT SECTION HTML INSPECTION")
        print("="*60 + "\n")
        
        # Get the page HTML
        page_html = driver.page_source
        
        # Find the export button section
        export_section_start = page_html.find("Export Report")
        if export_section_start > 0:
            # Get 2000 chars around it for context
            start = max(0, export_section_start - 1000)
            end = min(len(page_html), export_section_start + 1500)
            export_section = page_html[start:end]
            
            print("EXPORT BUTTON AREA:")
            print("-" * 60)
            print(export_section)
            print("-" * 60)
        else:
            print("⚠️ 'Export Report' text not found in page!")
        
        # Find all buttons
        print("\n\nALL BUTTONS ON PAGE:")
        print("-" * 60)
        buttons = driver.find_elements(By.TAG_NAME, "button")
        for i, btn in enumerate(buttons):
            print(f"Button {i}:")
            print(f"  Text: {btn.text}")
            print(f"  ID: {btn.get_attribute('id')}")
            print(f"  Class: {btn.get_attribute('class')}")
            print(f"  Type: {btn.get_attribute('type')}")
            print(f"  Name: {btn.get_attribute('name')}")
            print(f"  onclick: {btn.get_attribute('onclick')}")
            print()
        
        # Find all input elements (for selects)
        print("\nALL SELECT ELEMENTS:")
        print("-" * 60)
        selects = driver.find_elements(By.TAG_NAME, "select")
        for i, sel in enumerate(selects):
            print(f"Select {i}:")
            print(f"  ID: {sel.get_attribute('id')}")
            print(f"  Name: {sel.get_attribute('name')}")
            print(f"  Class: {sel.get_attribute('class')}")
            options = sel.find_elements(By.TAG_NAME, "option")
            print(f"  Options ({len(options)}):")
            for opt in options[:10]:  # First 10
                print(f"    - {opt.text} (value={opt.get_attribute('value')})")
            if len(options) > 10:
                print(f"    ... and {len(options)-10} more")
            print()
        
        print("\n✅ Inspection complete. Check the browser for visual confirmation.")
        print("Press Enter to close...")
        input()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if driver:
            driver.quit()
        exporter.close()


if __name__ == '__main__':
    main()
