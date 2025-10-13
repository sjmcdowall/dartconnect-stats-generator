#!/usr/bin/env python3
"""
Analyze DartConnect membership for players with missing gender (M/F blank)
from a by_leg export CSV. Outputs a breakdown to stdout and a detailed CSV.

Usage:
  python3 scripts/gender_membership_audit.py \
    --csv data/season74/by_leg_export.csv \
    --output output/gender_missing_membership.csv
"""

import argparse
from pathlib import Path
import pandas as pd


def bucket_membership(value: str) -> str:
    v = (value or "").strip().lower()
    if v == "":
        return "Unknown"
    if "guest" in v:
        return "Guest"
    if "no" in v:
        return "No"
    # Treat anything else as an active/paid member
    return "Member"


def main():
    parser = argparse.ArgumentParser(description="Audit membership for players with missing gender")
    parser.add_argument("--csv", required=True, help="Path to by_leg export CSV")
    parser.add_argument("--output", default="output/gender_missing_membership.csv", help="Output CSV path")
    args = parser.parse_args()

    csv_path = Path(args.csv)
    if not csv_path.exists():
        raise SystemExit(f"CSV not found: {csv_path}")

    df = pd.read_csv(csv_path, dtype=str)

    # Ensure required columns exist
    for col in ["M/F","Membership","First Name","Last Name, FI","Team","Division"]:
        if col not in df.columns:
            df[col] = ""

    # Normalize
    df["M/F"] = df["M/F"].fillna("").str.strip()
    df["Membership"] = df["Membership"].fillna("").astype(str).str.strip()
    df["First Name"] = df["First Name"].fillna("").astype(str).str.strip()
    df["Last Name, FI"] = df["Last Name, FI"].fillna("").astype(str).str.strip()

    # Player key
    df["player_key"] = df["First Name"].str.lower() + "|" + df["Last Name, FI"].str.lower()

    # Filter to missing gender
    missing = df[df["M/F"] == ""].copy()

    # Aggregate per player
    player_membership = (
        missing.groupby("player_key").agg(
            first_name=("First Name","first"),
            last_name_fi=("Last Name, FI","first"),
            membership_raw=("Membership", lambda x: ", ".join(sorted(set([s for s in x if str(s).strip()!=''])))),
            teams=("Team", lambda x: ", ".join(sorted(set([str(i).strip() for i in x if str(i).strip()!=''])))),
            divisions=("Division", lambda x: ", ".join(sorted(set([str(i).strip() for i in x if str(i).strip()!=''])))),
        )
    ).reset_index(drop=True)

    # Membership bucket
    player_membership["membership_bucket"] = player_membership["membership_raw"].apply(bucket_membership)

    # Breakdown
    print("===== Missing-gender DC Membership Breakdown (distinct players) =====")
    print(f"Total distinct players with missing gender: {len(player_membership)}")

    breakdown = player_membership["membership_bucket"].value_counts()
    for k, v in breakdown.items():
        print(f"  {k}: {v}")

    # Sample per bucket
    print("\nSample per bucket (up to 5 each):")
    for k in breakdown.index:
        sample = player_membership[player_membership["membership_bucket"] == k].head(5)
        if not sample.empty:
            print(f"\n-- {k} --")
            for _, r in sample.iterrows():
                print(f"  {r['first_name']} {r['last_name_fi']} | {r['teams']} | {r['divisions']} | {r['membership_raw']}")

    # Write CSV
    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    player_membership.rename(columns={
        "membership_raw": "MembershipRaw",
        "membership_bucket": "MembershipBucket",
        "teams": "Teams",
        "divisions": "Divisions",
    }, inplace=True)
    player_membership.to_csv(out_path, index=False)
    print(f"\nDetailed list written to: {out_path}")


if __name__ == "__main__":
    main()
