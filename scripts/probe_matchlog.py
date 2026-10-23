#!/usr/bin/env python3
"""Probe POST /api/league/getMatchLog using the weekly script's login path."""
import json
import os
import sys
import time
from pathlib import Path

ROOT = Path("/Users/stevemcdowall/play/projects/dartconnect-stats-generator")
sys.path.insert(0, str(ROOT))
os.chdir(ROOT)

# load .env without printing
env_path = ROOT / ".env"
if env_path.exists():
    for line in env_path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        k = k.replace("export ", "").strip()
        v = v.strip().strip('"').strip("'")
        os.environ.setdefault(k, v)

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

from src.export_downloader import DartConnectExporter

exporter = DartConnectExporter(headless=True)
options = webdriver.ChromeOptions()
options.add_argument("--headless=new")
options.add_argument("--window-size=1400,900")
service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=options)
wait = WebDriverWait(driver, 20)
summary_path = ROOT / "scripts" / "matchlog_probe_summary.json"

try:
    driver.get(exporter.LOGIN_URL)
    time.sleep(2)

    def find_email_input():
        for by, sel in [
            (By.CSS_SELECTOR, "input[type='email']"),
            (By.CSS_SELECTOR, "input[name*='email']"),
            (By.CSS_SELECTOR, "input[id*='email']"),
            (By.CSS_SELECTOR, "input[placeholder*='Email']"),
            (By.CSS_SELECTOR, "input[type='text']"),
        ]:
            try:
                el = driver.find_element(by, sel)
                if el.is_displayed():
                    return el
            except Exception:
                continue
        return None

    email_el = find_email_input() or (time.sleep(2) or find_email_input())
    if not email_el:
        raise RuntimeError("no email field")
    email_el.clear()
    email_el.send_keys(exporter.email)

    pwd_el = None
    for by, sel in [
        (By.CSS_SELECTOR, "input[type='password']"),
        (By.CSS_SELECTOR, "input[name*='password']"),
        (By.CSS_SELECTOR, "input[id*='password']"),
    ]:
        try:
            el = driver.find_element(by, sel)
            if el.is_displayed():
                pwd_el = el
                break
        except Exception:
            continue
    if not pwd_el:
        raise RuntimeError("no password field")
    pwd_el.clear()
    pwd_el.send_keys(exporter.password)

    login_btn = None
    for by, sel in [
        (By.XPATH, "//button[contains(., 'Login')]"),
        (By.XPATH, "//input[@type='submit' and (contains(@value,'Login') or contains(@value,'Sign'))]"),
    ]:
        try:
            el = driver.find_element(by, sel)
            if el.is_displayed():
                login_btn = el
                break
        except Exception:
            continue
    if not login_btn:
        raise RuntimeError("no login button")
    login_btn.click()
    time.sleep(3)
    exporter._dismiss_modal(driver)

    org_navigated = False
    for by, sel in [
        (By.LINK_TEXT, "Tournaments / Leagues"),
        (By.XPATH, "//a[contains(., 'Tournaments / Leagues')]"),
        (By.LINK_TEXT, "Competition Organizer"),
        (By.XPATH, "//a[contains(., 'Competition Organizer')]"),
    ]:
        try:
            el = driver.find_element(by, sel)
            if el.is_displayed():
                el.click()
                org_navigated = True
                time.sleep(2)
                break
        except Exception:
            continue
    if not org_navigated:
        driver.get("https://my.dartconnect.com/organize")
        time.sleep(3)

    manage_clicked = False
    for kw in ["winston", "wssndl", "sunday night"]:
        try:
            ml = driver.find_element(
                By.XPATH,
                f"//tr[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{kw}')]"
                f"//a[contains(., 'Manage League')]",
            )
            driver.execute_script("arguments[0].scrollIntoView({block:'center'});", ml)
            time.sleep(0.5)
            ml.click()
            manage_clicked = True
            break
        except Exception:
            continue
    if not manage_clicked:
        for by, sel in [
            (By.LINK_TEXT, "Manage League"),
            (By.XPATH, "//a[contains(., 'Manage League')]"),
        ]:
            try:
                driver.find_element(by, sel).click()
                manage_clicked = True
                break
            except Exception:
                continue
    print("manage_clicked", manage_clicked)
    exporter._wait_for_league_portal_load(driver, wait)
    exporter._dismiss_modal(driver)
    time.sleep(2)

    # switch to league window if a new tab opened
    for h in driver.window_handles:
        driver.switch_to.window(h)
        if "league.dartconnect.com" in (driver.current_url or ""):
            break
    print("url", driver.current_url)

    for _ in range(25):
        ready = driver.execute_script(
            "return !!(window.LEAGUE && window.LEAGUE.id && window.CURRENT_SEASON_ID);"
        )
        if ready:
            break
        time.sleep(1)
    ids = driver.execute_script(
        """
        return {
          league_id: (window.LEAGUE && LEAGUE.id) || null,
          season_id: window.CURRENT_SEASON_ID || null,
          league_type: (window.LEAGUE && LEAGUE.league_type) || null,
          has_schedules: !!window.LEAGUE_HAS_SCHEDULES,
          match_format_style: window.MATCH_FORMAT_STYLE || 'LEGACY',
          url: location.href
        };
        """
    )
    print("portal", json.dumps(ids))
    if not ids.get("league_id") or not ids.get("season_id"):
        raise RuntimeError("league/season ids not available")

    result = driver.execute_async_script(
        """
        const done = arguments[0];
        const body = {
          league_id: LEAGUE.id,
          season_id: CURRENT_SEASON_ID,
          admin_filters: (typeof ADMIN_FILTERS !== 'undefined') ? ADMIN_FILTERS : {division: '', rollup_id: null},
          schedule_mode: LEAGUE_HAS_SCHEDULES ? 'SCHEDULER' : 'CALENDAR',
          showApproved: false,
          showApprovedPlayerExceptions: false,
          match_format_style: MATCH_FORMAT_STYLE || 'LEGACY',
          completed_only: false
        };
        fetch('/api/league/getMatchLog', {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          credentials: 'same-origin',
          body: JSON.stringify(body)
        }).then(r => r.json()).then(done).catch(e => done({status: 'ERR', status_text: String(e)}));
        """
    )
    payload = (result or {}).get("payload") or {}
    exceptions = payload.get("exception_matches") or []
    players = payload.get("player_exceptions") or []
    unplayed = payload.get("unplayed_matches") or []
    unsched = payload.get("unschedMatches") or []
    pending = payload.get("pending_matches") or []

    def reasons(m):
        r = []
        st = m.get("status")
        if st in ("Pending", "Incomplete", "Incomplete Unscheduled"):
            r.append("Unsaved" if st == "Pending" else st)
        if m.get("playedOutsideSchedDate"):
            r.append("wrong date")
        if m.get("set_exception"):
            r.append("unexpected sets (%s)" % m.get("sets"))
        if m.get("points_exception"):
            r.append("unexpected league points")
        if (m.get("short_sets") or 0) > 0:
            r.append("%s short set(s)" % m["short_sets"])
        if (m.get("forfeit_sets") or 0) > 0:
            r.append("%s forfeit set(s)" % m["forfeit_sets"])
        if (m.get("missing_player_sets") or 0) > 0:
            r.append("%s set(s) missing players" % m["missing_player_sets"])
        return r or ["flagged"]

    pending_players = [p for p in players if p.get("status") == "P"]
    summary = {
        "api_status": result.get("status"),
        "status_text": result.get("status_text"),
        "exception_count": len(exceptions),
        "pending_player_exceptions": len(pending_players),
        "unplayed_count": len(unplayed),
        "unsched_count": len(unsched),
        "pending_matches": len(pending),
        "completed_count": payload.get("record_count"),
        "exceptions": [
            {
                "division": m.get("division"),
                "round": m.get("round"),
                "home": m.get("home"),
                "away": m.get("away"),
                "status": m.get("status"),
                "sched": m.get("adj_sched_date"),
                "played": m.get("adj_start_date"),
                "reasons": reasons(m),
            }
            for m in exceptions
        ],
        "unplayed": [
            {
                "division": u.get("division") or u.get("division_name"),
                "round": u.get("round"),
                "home": u.get("home"),
                "away": u.get("away"),
                "sched": u.get("sched_date") or u.get("adj_sched_date"),
            }
            for u in unplayed[:50]
        ],
        "player_exceptions": [
            {
                "type": p.get("exception_type"),
                "first": p.get("current_first_name"),
                "last": p.get("current_last_name"),
                "team": p.get("team_name"),
                "division": p.get("division"),
                "status": p.get("status"),
            }
            for p in pending_players[:50]
        ],
    }
    summary_path.write_text(json.dumps(summary, indent=2))
    print("SUMMARY_OK")
    print(json.dumps({k: summary[k] for k in summary if k not in ("exceptions", "unplayed", "player_exceptions")}))
    for e in summary["exceptions"][:20]:
        print("EXC", e.get("division"), e.get("home"), "vs", e.get("away"), e.get("reasons"))
    for u in summary["unplayed"][:15]:
        print("UNP", u.get("home"), "vs", u.get("away"), "round", u.get("round"))
    for p in summary["player_exceptions"][:15]:
        print("PLR", p.get("type"), p.get("last"), p.get("first"), p.get("team"))
finally:
    driver.quit()
