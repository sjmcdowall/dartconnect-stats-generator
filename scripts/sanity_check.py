#!/usr/bin/env python3
"""Pre-publish sanity check for weekly WSSNDL stats.

Re-processes the by-leg export (recap pages come from cache, so this is fast),
plus the same export minus the latest match date ("prior week"), and fails with
a PROBABLE ERROR report when:

  (a) any match report failed to fetch/parse, a leg had no QP source, or the
      run log shows failed reports / "No game data found"
  (b) any match date's total QPs are 0 or < 25% of the season per-date average
  (c) a player played legs on the latest date with qualifying CSV turns/outs
      (501 Hi Turn >= 95, DO >= 61, Cricket Hi Turn >= 5) but their season QP
      total did not move vs the prior week
  (d) a special QP (180 / 9-mark cricket turn) is in the latest CSV data but
      the player's QPs went up by less than 5
  (e) 501 QPs rose by less than the CSV lower bound (Hi Turn + DO QPs) on the
      latest date
  (f) the QPs in processed_results.json (what gets published) differ from a
      fresh in-process run

Exit code 0 = pass, 1 = PROBABLE ERROR (do not upload), 2 = could not run.

Usage:
  venv/bin/python scripts/sanity_check.py data/season76 \
      --results output/season76/processed_results.json --log /tmp/run.log
"""

import argparse
import json
import logging
import re
import sys
import tempfile
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.config import Config  # noqa: E402
from src.data_processor import DataProcessor  # noqa: E402


def qp_501_turn(v):
    if pd.isna(v):
        return 0
    for lo, q in ((164, 5), (148, 4), (132, 3), (116, 2), (95, 1)):
        if v >= lo:
            return q
    return 0


def qp_501_out(v):
    if pd.isna(v):
        return 0
    for lo, q in ((151, 5), (129, 4), (107, 3), (85, 2), (61, 1)):
        if v >= lo:
            return q
    return 0


def find_csv(path: Path) -> Path:
    if path.is_file():
        return path
    cands = sorted(path.glob("*By_Leg_export*.csv")) or sorted(path.glob("*by_leg*.csv"))
    if not cands:
        raise FileNotFoundError(f"No by-leg export CSV in {path}")
    return max(cands, key=lambda p: p.stat().st_mtime)


def player_table(results):
    out = {}
    for div, teams in (results.get("team_statistics") or {}).items():
        for team in teams:
            for p in team.get("players", []):
                out[(team["name"], p["name"])] = {
                    "legs": int(p.get("legs", 0)),
                    "qps": int(p.get("qps", 0)),
                    "qp_pct": p.get("qp_pct", ""),
                    "division": div,
                }
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("input", help="by-leg export CSV or data directory")
    ap.add_argument("--config", default=str(ROOT / "config.yaml"))
    ap.add_argument("--results", help="processed_results.json to cross-check")
    ap.add_argument("--log", help="run log from main_consolidated.py to scan")
    ap.add_argument("--min-ratio", type=float, default=0.25)
    args = ap.parse_args()

    logging.basicConfig(level=logging.ERROR, format="%(levelname)s %(name)s: %(message)s")
    errors, notes = [], []

    try:
        csv_path = find_csv(Path(args.input))
        config = Config(args.config) if Path(args.config).exists() else Config()
        cur = DataProcessor(config).process_file(str(csv_path))
    except Exception as e:  # pragma: no cover
        print(f"SANITY CHECK COULD NOT RUN: {e}")
        return 2

    df = cur["raw_data"].copy()
    df["d"] = pd.to_datetime(df["game_date"], errors="coerce").dt.date
    df["Hi Turn"] = pd.to_numeric(df["Hi Turn"], errors="coerce")
    df["DO"] = pd.to_numeric(df["DO"], errors="coerce")
    dates = sorted(x for x in df["d"].dropna().unique())
    latest = dates[-1]
    enh = cur["enhanced_data"]
    notes.append(f"Export: {csv_path.name} | {len(dates)} match dates, {dates[0]} .. {latest}")
    notes.append(f"Match reports: {enh.get('urls_processed', 0)} parsed, {enh.get('urls_failed', 0)} failed")

    # (a) fetch/parse failures
    failed = enh.get("failed_urls") or []
    if enh.get("urls_failed", 0) or failed:
        errors.append(f"(a) {enh.get('urls_failed', len(failed))} match report(s) failed to fetch/parse:")
        errors.extend(f"      {u}" for u in failed)
    missing = enh.get("qp_missing_legs") or []
    if missing:
        errors.append(f"(a) {len(missing)} leg(s) had no recap data AND no CSV Hi Turn (QPs missing):")
        errors.extend(f"      {m['player']} {m['game']} {m['url']}" for m in missing[:20])
    if args.log and Path(args.log).exists():
        text = Path(args.log).read_text(errors="replace")
        nodata = len(re.findall(r"No game data found|Failed to parse JSON", text))
        m = re.findall(r"(\d+) successful, (\d+) failed", text)
        if nodata:
            errors.append(f"(a) run log {args.log}: {nodata} 'No game data found'/'Failed to parse JSON' line(s)")
        if m and int(m[-1][1]) > 0:
            errors.append(f"(a) run log {args.log}: '{m[-1][0]} successful, {m[-1][1]} failed'")

    # (b) per-date QP totals (recap turn QPs + CSV checkout QPs; fallback excluded)
    url_qp = enh.get("url_qp_totals") or {}
    url_date = df.dropna(subset=["d"]).groupby("report_url")["d"].first()
    per_date = {d: 0 for d in dates}
    for url, d in url_date.items():
        per_date[d] += int(url_qp.get(url, 0))
    s01 = df[df["game_name"] == "501 SIDO"]
    for d, v in s01.groupby("d")["DO"].apply(lambda s: sum(qp_501_out(x) for x in s)).items():
        per_date[d] += int(v)
    avg = sum(per_date.values()) / max(1, len(per_date))
    notes.append("QPs per match date: " + ", ".join(f"{d:%m/%d}={v}" for d, v in per_date.items()) + f" (avg {avg:.0f})")
    for d, v in per_date.items():
        if v == 0 or v < args.min_ratio * avg:
            errors.append(f"(b) {d}: total QPs {v} is {'zero' if v == 0 else f'< {args.min_ratio:.0%} of season avg {avg:.0f}'}")

    # Prior week = same export without the latest match date
    raw = pd.read_csv(csv_path, low_memory=False)
    raw_d = pd.to_datetime(raw["Date"], errors="coerce").dt.date
    prior_tbl = {}
    if len(dates) > 1:
        with tempfile.TemporaryDirectory() as td:
            pth = Path(td) / csv_path.name
            raw[raw_d < latest].to_csv(pth, index=False)
            prior_tbl = player_table(DataProcessor(config).process_file(str(pth)))
    cur_tbl = player_table(cur)

    # (c)/(d)/(e) per-player checks on the latest date
    wk = df[df["d"] == latest]
    flat, special, lowb = [], [], []
    for (team, name), rows in wk.groupby(["Team", "player_name"]):
        c = cur_tbl.get((team, name))
        if not c:
            continue
        p = prior_tbl.get((team, name), {"qps": 0, "legs": 0})
        delta = c["qps"] - p["qps"]
        r501 = rows[rows["game_name"] == "501 SIDO"]
        rcr = rows[rows["game_name"] == "Cricket"]
        qualifying = (r501["Hi Turn"] >= 95).any() or (r501["DO"] >= 61).any() or (rcr["Hi Turn"] >= 5).any()
        if qualifying and delta == 0:
            flat.append(f"      {name} ({team}): QPs {p['qps']} -> {c['qps']} with qualifying turns/outs on {latest}")
        n180 = int((r501["Hi Turn"] >= 180).sum()) + int((rcr["Hi Turn"] >= 9).sum())
        if n180 and delta < 5 * n180:
            special.append(f"      {name} ({team}): {n180} special (180 / 9-mark) on {latest} but QPs only {p['qps']} -> {c['qps']}")
        lb = sum(qp_501_turn(x) for x in r501["Hi Turn"]) + sum(qp_501_out(x) for x in r501["DO"])
        if delta < lb:
            lowb.append(f"      {name} ({team}): QPs +{delta} but CSV 501 lower bound is +{lb} on {latest}")
    if flat:
        errors.append(f"(c) {len(flat)} player(s) with flat QPs despite qualifying turns/outs:")
        errors.extend(flat)
    if special:
        errors.append(f"(d) {len(special)} special QP(s) not reflected in QP totals:")
        errors.extend(special)
    if lowb:
        errors.append(f"(e) {len(lowb)} player(s) below the CSV 501 QP lower bound:")
        errors.extend(lowb)

    cur_total = sum(v["qps"] for v in cur_tbl.values())
    prior_total = sum(v["qps"] for v in prior_tbl.values())
    notes.append(f"Season QPs: prior week {prior_total} -> now {cur_total} (+{cur_total - prior_total} on {latest})")

    # (f) published results must match a fresh run
    if args.results and Path(args.results).exists():
        pub = player_table(json.load(open(args.results)))
        diff = [k for k in set(pub) | set(cur_tbl) if pub.get(k, {}).get("qps") != cur_tbl.get(k, {}).get("qps")]
        if diff:
            errors.append(f"(f) {len(diff)} player(s) differ between {args.results} and a fresh run, e.g.:")
            for k in sorted(diff)[:10]:
                errors.append(f"      {k[1]} ({k[0]}): published {pub.get(k, {}).get('qps')} vs fresh {cur_tbl.get(k, {}).get('qps')}")

    print("=" * 72)
    for n in notes:
        print(n)
    print("-" * 72)
    if errors:
        print("❌ PROBABLE ERROR — DO NOT PUBLISH. Sanity check found:")
        for e in errors:
            print(e)
        print("=" * 72)
        return 1
    print("✅ SANITY CHECK PASSED (a-f clean)")
    print("=" * 72)
    return 0


if __name__ == "__main__":
    sys.exit(main())
