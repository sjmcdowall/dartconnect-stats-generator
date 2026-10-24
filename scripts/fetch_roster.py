#!/usr/bin/env python3
"""League-portal Players roster (with M/F) - cached, read-only refresh.

The roster is cached at <data_dir>/players_roster.csv (one per season data dir)
and is only re-downloaded from the league portal Players tab when:
  (a) no roster file exists for this season, or
  (b) the by-leg export in <data_dir> has a player (by email, else team+name)
      who is not in the cached roster, or
  --force is given (weekly.sh --refresh-roster).
Otherwise it logs "roster cache hit, no refresh" and touches nothing.

If a refresh fails the cached roster is left untouched (exit 3 = refresh failed
but a cached roster exists; exit 1 = refresh failed and no roster at all).
The sanity check still hard-fails on any player left with no gender.

Usage:
  venv/bin/python scripts/fetch_roster.py --headless -o data/season76
  venv/bin/python scripts/fetch_roster.py -o data/season76 --dry-run   # decision only
  venv/bin/python scripts/fetch_roster.py --headless -o data/season76 --force
"""
import argparse
import logging
import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.data_processor import ROSTER_FILENAME, export_players_missing_from_roster  # noqa: E402

log = logging.getLogger("fetch_roster")


def find_export(data_dir: Path):
    c = sorted(data_dir.glob("*By_Leg_export*.csv"), key=lambda p: p.stat().st_mtime, reverse=True)
    return c[0] if c else None


def missing_players(data_dir: Path, roster: Path):
    export = find_export(data_dir)
    if export is None:
        log.warning(f"No *By_Leg_export*.csv in {data_dir}; cannot check roster coverage")
        return []
    return export_players_missing_from_roster(export, roster)


def fmt(players, limit=10):
    s = ", ".join(f"{n} ({t}{', ' + e if e else ''})" for n, t, e in players[:limit])
    return s + (f", ... +{len(players) - limit} more" if len(players) > limit else "")


def decide(data_dir: Path, force: bool):
    """Return (refresh: bool, reason: str)."""
    roster = data_dir / ROSTER_FILENAME
    if force:
        return True, "forced refresh (--refresh-roster)"
    if not roster.exists():
        return True, f"trigger (a): no roster file for this season ({roster})"
    miss = missing_players(data_dir, roster)
    if miss:
        return True, f"trigger (b): {len(miss)} export player(s) not in cached roster: {fmt(miss)}"
    return False, f"roster cache hit, no refresh ({roster})"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("-o", "--output-dir", default="data/season76", help="season data dir (holds export + roster)")
    ap.add_argument("--headless", action="store_true")
    ap.add_argument("--force", action="store_true", help="refresh even on a cache hit")
    ap.add_argument("--dry-run", action="store_true", help="log the refresh decision only; no network")
    ap.add_argument("-v", "--verbose", action="store_true")
    a = ap.parse_args()
    logging.basicConfig(
        level=logging.DEBUG if a.verbose else logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    data_dir = Path(a.output_dir)
    roster = data_dir / ROSTER_FILENAME
    refresh, reason = decide(data_dir, a.force)
    log.info(f"👥 Roster: {reason}")
    if not refresh:
        return 0
    if a.dry_run:
        log.info("👥 Roster: --dry-run, would refresh now (skipped)")
        return 0

    from src.export_downloader import DartConnectExporter

    try:
        path = DartConnectExporter(headless=a.headless).download_players_roster(str(data_dir))
    except Exception as e:  # keep the cache on any failure
        log.error(f"Roster refresh raised: {e}")
        path = None
    if not path:
        if roster.exists():
            log.warning(f"⚠️  Roster refresh FAILED - keeping cached {roster}")
            return 3
        log.error("❌ Roster refresh FAILED and no cached roster exists")
        return 1
    print(f"✅ Roster saved: {path}")
    still = missing_players(data_dir, roster)
    if still:
        log.warning(f"⚠️  Still not in refreshed roster ({len(still)}): {fmt(still)} "
                    "- they need export M/F or config/gender_overrides.yaml")
    return 0


if __name__ == "__main__":
    sys.exit(main())
