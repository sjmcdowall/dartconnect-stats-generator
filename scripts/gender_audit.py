#!/usr/bin/env python3
"""
Gender audit for DartConnect by_leg export data.

Finds:
- Players with missing gender (M/F empty)
- Players with inconsistent gender across rows (both M and F)
- Players where recorded gender is likely mismatched with first name (best-effort heuristic)

Usage:
  python scripts/gender_audit.py [--csv data/seasonXX/by_leg_export.csv] [--output output/gender_audit.csv]

Notes:
- Heuristic is intentionally conservative and only flags obvious cases.
- Review results manually; names can be unisex or culturally diverse.
"""

import argparse
from pathlib import Path
from typing import Dict, List, Tuple

import pandas as pd


COMMON_MALE = {
    # Common US male names (partial list)
    "john","michael","david","james","robert","william","richard","thomas","charles","joseph",
    "christopher","daniel","matthew","anthony","mark","donald","steven","paul","andrew","joshua",
    "kenneth","kevin","brian","george","timothy","ronald","edward","jason","ryan","gary",
    "nicholas","eric","stephen","larry","justin","scott","brandon","benjamin","adam","samuel",
    "gregory","alexander","patrick","tyler","frank","peter","marc","marcus","matt","mike","jeff",
    "jeffrey","steve","steven","bryan","bruce","jason","shaun","sean","ian","craig","donald",
}

COMMON_FEMALE = {
    # Common US female names (partial list)
    "mary","patricia","jennifer","linda","elizabeth","barbara","susan","jessica","sarah","karen",
    "nancy","lisa","betty","margaret","sandra","ashley","kimberly","emily","donna","michelle",
    "carol","amanda","melissa","deborah","stephanie","rebecca","laura","sharon","cynthia","kathleen",
    "amy","angela","rachel","heather","nicole","christine","julie","anna","maria","victoria",
    "bonnie","bonny","samantha","megan","katherine","catherine","jenny","lindsay","lindsey","amber",
}

# Some explicitly unisex names to avoid over-flagging
UNISEX = {
    "alex","sam","jordan","casey","taylor","jamie","morgan","bailey","skyler","skye","cameron",
    "devon","drew","parker","reese","riley","sydney","syd","avery","quinn","kyle","chris",
}


def norm(s: str) -> str:
    return (s or "").strip()


def extract_first_name(row: pd.Series) -> str:
    # Prefer explicit First Name column if present
    if "First Name" in row:
        return norm(row["First Name"]).title()
    # Fallback: try to approximate from player_name or Last Name, FI (not reliable for first name)
    if "player_name" in row:
        val = norm(row["player_name"]).title()
        # If it's two tokens, assume first is first name
        parts = [p for p in val.split() if p]
        if len(parts) >= 1:
            return parts[0]
    # If we only have "Last Name, FI", we can't reliably recover first name; return empty
    return ""


def likely_gender_from_first_name(first_name: str) -> str:
    if not first_name:
        return "unknown"
    n = first_name.lower()
    if n in UNISEX:
        return "unknown"  # deliberately avoid flagging
    if n in COMMON_MALE:
        return "M"
    if n in COMMON_FEMALE:
        return "F"
    # Simple heuristic: names ending with 'a' more likely female; with caution
    if len(n) >= 3 and n.endswith("a"):
        return "F"
    return "unknown"


def audit_gender(csv_path: Path) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    df = pd.read_csv(csv_path, dtype=str)

    # Normalize relevant columns
    for col in ["M/F", "First Name", "Last Name, FI", "Team", "Division"]:
        if col not in df.columns:
            df[col] = ""
    df["M/F"] = df["M/F"].fillna("").str.strip().str.upper()

    # Build a player key (first name + last name token for stability)
    df["first_name"] = df.apply(extract_first_name, axis=1)
    df["last_name_fi"] = df["Last Name, FI"].fillna("").astype(str)
    df["player_key"] = df["first_name"].str.lower() + "|" + df["last_name_fi"].str.lower()

    # Aggregate genders per player
    agg = (
        df.groupby("player_key").agg(
            first_name=("first_name", "first"),
            last_name_fi=("last_name_fi", "first"),
            teams=("Team", lambda x: ", ".join(sorted(set([norm(v) for v in x if norm(v)])))),
            division=("Division", lambda x: ", ".join(sorted(set([norm(v) for v in x if norm(v)])))),
            genders=("M/F", lambda x: sorted(set([g for g in x if g in {"M","F"}])))
        )
        .reset_index(drop=True)
    )

    # Compute flags
    flags: List[Dict] = []
    for _, row in agg.iterrows():
        genders = row["genders"]
        first = row["first_name"]
        likely = likely_gender_from_first_name(first)

        reason = None
        flag = None
        if not genders:
            flag = "missing_gender"
            reason = "No M/F recorded in any row"
        elif len(genders) > 1:
            flag = "inconsistent_gender"
            reason = f"Multiple genders recorded: {genders}"
        else:
            g = genders[0]
            if likely != "unknown" and likely != g:
                # Only flag if likely is confident and different
                flag = "suspect_name_mismatch"
                reason = f"First name suggests {likely}, but recorded {g}"

        if flag:
            flags.append({
                "first_name": first,
                "last_name_fi": row["last_name_fi"],
                "teams": row["teams"],
                "division": row["division"],
                "genders": ",".join(genders) if genders else "",
                "flag": flag,
                "reason": reason,
            })

    flagged_df = pd.DataFrame(flags)

    # Separate views for convenience
    missing_df = flagged_df[flagged_df["flag"] == "missing_gender"].copy()
    mismatch_df = flagged_df[flagged_df["flag"] == "suspect_name_mismatch"].copy()
    inconsistent_df = flagged_df[flagged_df["flag"] == "inconsistent_gender"].copy()

    return missing_df, mismatch_df, inconsistent_df


def main():
    parser = argparse.ArgumentParser(description="Audit gender anomalies in DartConnect by_leg CSV")
    parser.add_argument("--csv", default="data/season74/by_leg_export.csv", help="Path to by_leg export CSV")
    parser.add_argument("--output", default="output/gender_audit.csv", help="Path to write combined flagged CSV")
    args = parser.parse_args()

    csv_path = Path(args.csv)
    if not csv_path.exists():
        raise SystemExit(f"CSV not found: {csv_path}")

    missing_df, mismatch_df, inconsistent_df = audit_gender(csv_path)

    # Write a single CSV with a type column
    out = pd.concat([
        missing_df.assign(type="missing_gender"),
        mismatch_df.assign(type="suspect_name_mismatch"),
        inconsistent_df.assign(type="inconsistent_gender"),
    ], ignore_index=True)

    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(args.output, index=False)

    # Console summary
    print("\n===== Gender Audit Summary =====")
    print(f"CSV: {csv_path}")
    print(f"Total flagged: {len(out)}")
    print(f"  Missing gender: {len(missing_df)}")
    print(f"  Suspect name mismatch: {len(mismatch_df)}")
    print(f"  Inconsistent gender: {len(inconsistent_df)}")

    def preview(df: pd.DataFrame, title: str):
        if df.empty:
            print(f"\n{title}: none")
            return
        cols = ["first_name","last_name_fi","teams","division","genders","reason"]
        print(f"\n{title} (up to 10):")
        print(df[cols].head(10).to_string(index=False))

    preview(missing_df, "Missing gender")
    preview(mismatch_df, "Suspect name mismatch")
    preview(inconsistent_df, "Inconsistent gender")
    print(f"\nReport written to: {args.output}")


if __name__ == "__main__":
    main()