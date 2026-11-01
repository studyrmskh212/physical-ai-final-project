#!/usr/bin/env python3

import csv
import time
import os
from pathlib import Path

FOLDER = Path.home() / "physical_ai_final"

def latest_record():
    files = list(FOLDER.glob("run_*.csv"))

    if not files:
        return None, None

    latest = max(
        files, key=lambda p: p.stat().st_mtime
    )

    with latest.open(newline="") as f:
        rows = list(csv.DictReader(f))

    if not rows:
        return latest.name, None

    return latest.name, rows[-1]


def main():
    try:
        while True:
            name, row = latest_record()

            os.system("clear")

            print("=" * 40)
            print("     PHYSICAL AI PATROL")
            print("        LIVE MONITOR")
            print("=" * 40)

            if row:
                action = row["executed_action"]
                decision = row["ai_decision"]

                print()
                print(f" TIME       : {row['time_sec']} s")
                print()
                print(f" FRONT      : {row['front_m']} m")
                print(f" LEFT       : {row['left_m']} m")
                print(f" RIGHT      : {row['right_m']} m")
                print()
                print("-" * 40)
                print(f" AI DECISION: {decision}")
                print(f" EXECUTION  : {action}")
                print(
                    " SAFETY     : " +
                    ("OVERRIDE" if
                     row["safety_override"] == "1"
                     else "NORMAL")
                )
                print("-" * 40)
            else:
                print()
                print(" Waiting for CSV data...")
                print()

            print(f"\n FILE: {name or 'not found'}")
            print(" Press Ctrl+C to close")

            time.sleep(0.5)

    except KeyboardInterrupt:
        print("\nDashboard stopped.")


if __name__ == "__main__":
    main()
