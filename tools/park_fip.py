"""Builds park_fip.yaml (a file in the constants directory you supply; docs/CONSTANTS.md) from the CSVs written by tools/park_fip.R.

Run: uv run python tools/park_fip.py <folder written by tools/park_fip.R>
"""

from __future__ import annotations

import csv
import glob
import sys
from datetime import date
from pathlib import Path

OUT = (
    Path(__file__).parent.parent / "src" / "sabermetricspy" / "data" / "constants" / "park_fip.yaml"
)

# FanGraphs lists parks by team nickname; abbreviations follow park_factors.yaml, one per franchise
# (Expos are WSN, Devil Rays are TBR, Indians and Guardians are CLE, Marlins are MIA).
ABBR = {
    "Angels": "LAA",
    "Astros": "HOU",
    "Athletics": "OAK",
    "Blue Jays": "TOR",
    "Braves": "ATL",
    "Brewers": "MIL",
    "Cardinals": "STL",
    "Cleveland": "CLE",
    "Cubs": "CHC",
    "Devil Rays": "TBR",
    "Diamondbacks": "ARI",
    "Dodgers": "LAD",
    "Expos": "WSN",
    "Giants": "SFG",
    "Guardians": "CLE",
    "Indians": "CLE",
    "Mariners": "SEA",
    "Marlins": "MIA",
    "Mets": "NYM",
    "Nationals": "WSN",
    "Orioles": "BAL",
    "Padres": "SDP",
    "Phillies": "PHI",
    "Pirates": "PIT",
    "Rangers": "TEX",
    "Rays": "TBR",
    "Red Sox": "BOS",
    "Reds": "CIN",
    "Rockies": "COL",
    "Royals": "KCR",
    "Tigers": "DET",
    "Twins": "MIN",
    "White Sox": "CHW",
    "Yankees": "NYY",
}


def main(folder: str) -> None:
    lines = [
        "# FanGraphs park factors, the FIP column (100 = neutral), by season and team: the park input of FIP- and of pitcher WAR.",
        "# Source: https://www.fangraphs.com/guts.aspx?type=pf (the 'FIP' column) through baseballr fg_park; whole numbers as published.",
        f"# Regenerate with tools/park_fip.R and tools/park_fip.py (retrieved {date.today().isoformat()}).",
        "seasons:",
    ]
    for path in sorted(glob.glob(f"{folder}/park*.csv")):
        with open(path, encoding="utf-8") as handle:
            rows = list(csv.DictReader(handle))
        season = int(rows[0]["season"])
        lines.append(f"  {season}:")
        for row in sorted(rows, key=lambda r: ABBR[r["home_team"]]):
            lines.append(f"    {ABBR[row['home_team']]}: {int(float(row['FIP']))}")
    OUT.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main(sys.argv[1])
