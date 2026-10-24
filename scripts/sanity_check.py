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
  (g) a player's published Men/Women list (processed_results.json lookup and
      the newest Individual-*.pdf) differs from a non-blank DartConnect M/F
      (players keyed by email, else team+name)
  WARNINGS (do not fail): every player whose gender came from first-name
  inference (all DartConnect M/F rows blank), and conflicting DartConnect M/F

Exit code 0 = pass, 1 = PROBABLE ERROR (do not upload), 2 = could not run.

Usage:
  venv/bin/python scripts/sanity_check.py data/season76 \
      --results output/season76/processed_results.json --log /tmp/run.log
"""

import argparse
import json
import logging
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.config import Config  # noqa: E402
from src.data_processor import DataProcessor, PLACEHOLDER_NAMES  # noqa: E402
from src.pdf_generator import build_gender_lookup  # noqa: E402


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


def results_raw_df(results):
    raw = results.get("raw_data")
    if isinstance(raw, dict):
        return pd.DataFrame.from_dict(raw, orient="index")
    if isinstance(raw, list):
        return pd.DataFrame(raw)
    return raw if isinstance(raw, pd.DataFrame) else pd.DataFrame()


def pdf_gender_lists(pdf_path, names_by_division):
    """Parse an Individual PDF: {(division, name): 'F'|'M'} for the
    Singles/All Events/Quality Points blocks (Women block, then Men block)."""
    exe = shutil.which("pdftotext") or (
        "/opt/homebrew/bin/pdftotext" if Path("/opt/homebrew/bin/pdftotext").exists() else None
    )
    if not exe:
        return None
    # -layout keeps table rows on one line; plain mode interleaves columns.
    text = subprocess.run([exe, "-layout", str(pdf_path), "-"], capture_output=True, text=True).stdout
    out, div, mode = {}, None, None
    for line in text.splitlines():
        m = re.match(r"^\s*(\w[\w ]*?) Division\s*$", line)
        if m and m.group(1) in names_by_division:
            div, mode = m.group(1), None
            continue
        if "Singles - Women" in line:
            mode = "F"
            continue
        if "Singles - Men" in line:
            mode = "M"
            continue
        if "Ratings - " in line:
            mode = None
        if not (div and mode):
            continue
        for name in names_by_division[div]:
            if re.search(r"(?<!\w)" + re.escape(name) + r"(?!\w)", line):
                prev = out.get((div, name))
                out[(div, name)] = mode if prev in (None, mode) else "BOTH"
    return out


def gender_checks(csv_path, pub_df, pdf_path):
    """Return (errors, warnings, notes) for gender list integrity."""
    errors, warnings, notes = [], [], []
    raw = pd.read_csv(csv_path, low_memory=False)
    raw = raw[~raw["First Name"].astype(str).str.strip().str.lower().isin(PLACEHOLDER_NAMES)]
    raw = raw[raw["First Name"].notna() & raw["Date"].notna()].copy()
    first = raw["First Name"].astype(str).str.strip()
    lastfi = raw["Last Name, FI"].astype(str)
    raw["player_name"] = first + " " + lastfi.str.split(",").str[0].str.strip()
    raw["mf"] = raw["M/F"].where(raw["M/F"].notna(), "").astype(str).str.strip().str.upper()
    raw["key"] = DataProcessor._player_key_series(raw)
    dc = {}
    for key, grp in raw.groupby("key"):
        vals = set(v for v in grp["mf"] if v)
        dc[key] = {
            "vals": vals,
            "name": grp["player_name"].iloc[0],
            "teams": set(grp["Team"].dropna()),
            "division": grp["Division"].dropna().iloc[0] if grp["Division"].notna().any() else "",
        }
        if len(vals) > 1:
            warnings.append(f"    conflicting DartConnect M/F for {grp['player_name'].iloc[0]} <{key}>: {grp['mf'].value_counts().to_dict()}")

    # (team, name) shared by >1 unique player with different DartConnect genders
    tn = {}
    for key, info in dc.items():
        for t in info["teams"]:
            tn.setdefault((t, info["name"]), []).append(key)
    for (t, n), keys in tn.items():
        gset = set().union(*(dc[k]["vals"] for k in keys))
        if len(keys) > 1 and len(gset) > 1:
            errors.append(f"(g) identity collision: {n} ({t}) is {len(keys)} players with M/F {sorted(gset)}: {keys}")

    lookup = build_gender_lookup(pub_df)
    names_by_div = {}
    for info in dc.values():
        names_by_div.setdefault(info["division"], set()).add(info["name"])
    pdf = pdf_gender_lists(pdf_path, names_by_div) if pdf_path else None
    if pdf_path and pdf is None:
        warnings.append("    pdftotext not found - PDF gender lists not checked")

    checked = 0
    for key, info in dc.items():
        if len(info["vals"]) != 1:
            continue
        want = next(iter(info["vals"]))
        for t in info["teams"]:
            got = lookup.get((t, info["name"]))
            checked += 1
            if got != want:
                errors.append(f"(g) {info['name']} ({t}) <{key}>: DartConnect M/F={want} but published gender={got}")
        if pdf is not None:
            got_pdf = pdf.get((info["division"], info["name"]))
            if got_pdf is not None and got_pdf != want:
                where = "both lists" if got_pdf == "BOTH" else ("Women lists" if got_pdf == "F" else "Men lists")
                errors.append(f"(g) {info['name']} <{key}>: DartConnect M/F={want} but on {where} in {Path(pdf_path).name}")

    inferred = []
    if "gender_source" in pub_df.columns:
        src = pub_df.drop_duplicates(["Team", "player_name"])
        for _, r in src[src["gender_source"] == "inferred"].iterrows():
            inferred.append(f"    {r['player_name']} ({r['Team']}) <{r.get('player_key', '')}> -> {r['player_gender']} (no DartConnect M/F)")
    else:
        for key, info in dc.items():
            if not info["vals"]:
                for t in info["teams"]:
                    g = lookup.get((t, info["name"]))
                    if g:
                        inferred.append(f"    {info['name']} ({t}) <{key}> -> {g} (no DartConnect M/F)")
    if inferred:
        warnings.append(f"  {len(inferred)} player(s) with INFERRED gender (all DartConnect M/F blank):")
        warnings.extend(sorted(inferred))
    unknown = [info["name"] for info in dc.values() if not info["vals"]
               and not any(lookup.get((t, info["name"])) for t in info["teams"])]
    if unknown:
        warnings.append(f"  {len(unknown)} player(s) with NO gender (left off Men/Women lists): {', '.join(sorted(unknown))}")
    notes.append(
        f"Gender: {sum(1 for i in dc.values() if i['vals'])} players with DartConnect M/F checked "
        f"({checked} team entries), {len(inferred)} inferred, "
        f"PDF lists {'checked: ' + Path(pdf_path).name if pdf else 'not checked'}"
    )
    return errors, warnings, notes


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("input", help="by-leg export CSV or data directory")
    ap.add_argument("--config", default=str(ROOT / "config.yaml"))
    ap.add_argument("--results", help="processed_results.json to cross-check")
    ap.add_argument("--log", help="run log from main_consolidated.py to scan")
    ap.add_argument("--pdf", help="Individual PDF to check (default: newest Individual-*.pdf next to --results)")
    ap.add_argument("--min-ratio", type=float, default=0.25)
    args = ap.parse_args()

    logging.basicConfig(level=logging.ERROR, format="%(levelname)s %(name)s: %(message)s")
    errors, notes, warnings = [], [], []

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

    # (g) gender lists
    pub_df = cur["raw_data"]
    pdf_path = Path(args.pdf) if args.pdf else None
    if args.results and Path(args.results).exists():
        pub_df = results_raw_df(json.load(open(args.results)))
        if pdf_path is None:
            pdfs = sorted(Path(args.results).parent.glob("Individual-*.pdf"), key=lambda f: f.stat().st_mtime)
            pdf_path = pdfs[-1] if pdfs else None
    g_err, g_warn, g_notes = gender_checks(csv_path, pub_df, pdf_path)
    errors.extend(g_err)
    warnings.extend(g_warn)
    notes.extend(g_notes)

    print("=" * 72)
    for n in notes:
        print(n)
    print("-" * 72)
    if warnings:
        print("⚠️  WARNINGS (not blocking):")
        for w in warnings:
            print(w)
        print("-" * 72)
    if errors:
        print("❌ PROBABLE ERROR — DO NOT PUBLISH. Sanity check found:")
        for e in errors:
            print(e)
        print("=" * 72)
        return 1
    print("✅ SANITY CHECK PASSED (a-g clean)")
    print("=" * 72)
    return 0


if __name__ == "__main__":
    sys.exit(main())
