#!/usr/bin/env python3
"""Download the WSSNDL league-portal Players roster (with M/F) - read-only.

Writes <output_dir>/players_roster.csv (player_name, email, team, division,
gender, ...). Used by DataProcessor as the authoritative gender source.

Usage:
  venv/bin/python scripts/fetch_roster.py --headless -o data/season76
"""
import argparse
import logging
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.export_downloader import DartConnectExporter  # noqa: E402


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("-o", "--output-dir", default="data/season76")
    ap.add_argument("--headless", action="store_true")
    ap.add_argument("-v", "--verbose", action="store_true")
    a = ap.parse_args()
    logging.basicConfig(
        level=logging.DEBUG if a.verbose else logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    path = DartConnectExporter(headless=a.headless).download_players_roster(a.output_dir)
    if not path:
        return 1
    print(f"✅ Roster saved: {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
