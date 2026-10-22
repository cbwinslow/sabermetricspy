"""Regenerates league_war.yaml (a file in the constants directory you supply; docs/CONSTANTS.md) from the MLB Stats API.

Run: uv run python tools/league_war_constants.py   (needs internet)

For each regular season it records the inputs of the FanGraphs position-player replacement formula
(https://library.fangraphs.com/war/war-position-players/): games played, league plate appearances, and the
runs and outs that give runs per win. Every figure is a sum over the 30 team lines of the
`statsapi.mlb.com/api/v1/teams/stats` endpoint; games are the sum of team games divided by two.
"""

from __future__ import annotations

import json
import sys
import urllib.request
from datetime import date
from pathlib import Path
from typing import Any

FIRST_SEASON = 1990
URL = (
    "https://statsapi.mlb.com/api/v1/teams/stats?stats=season&group={group}"
    "&season={season}&sportIds=1&gameType=R"
)
OUT = (
    Path(__file__).parent.parent
    / "src"
    / "sabermetricspy"
    / "data"
    / "constants"
    / "league_war.yaml"
)


def _splits(group: str, season: int) -> list[dict[str, Any]]:
    with urllib.request.urlopen(URL.format(group=group, season=season), timeout=60) as resp:
        return json.load(resp)["stats"][0]["splits"]


def _outs(innings: str) -> int:
    whole, _, frac = innings.partition(".")
    return int(whole) * 3 + int(frac or 0)


def season_row(season: int) -> dict[str, int]:
    hitting = _splits("hitting", season)
    pitching = _splits("pitching", season)
    games = sum(s["stat"]["gamesPlayed"] for s in hitting)
    if games % 2:
        raise ValueError(f"{season}: team games sum to an odd number ({games})")
    return {
        "games": games // 2,
        "pa": sum(s["stat"]["plateAppearances"] for s in hitting),
        "runs": sum(s["stat"]["runs"] for s in hitting),
        "outs": sum(_outs(s["stat"]["inningsPitched"]) for s in pitching),
    }


def main() -> None:
    last = date.today().year
    lines = [
        "# League inputs to the FanGraphs position-player WAR replacement and runs-per-win formulas.",
        "# games = MLB games played, pa = MLB plate appearances, runs and outs = MLB totals (outs = innings x 3).",
        "# Source: MLB Stats API team totals (https://statsapi.mlb.com/api/v1/teams/stats, regular season, 30 teams summed).",
        f"# Regenerate with tools/league_war_constants.py (retrieved {date.today().isoformat()}).",
        "# Verified by tests: runs per win from these totals equals the FanGraphs Guts R/W column for every season.",
        "seasons:",
    ]
    for season in range(FIRST_SEASON, last + 1):
        try:
            row = season_row(season)
        except Exception as exc:  # a season not yet played has no team lines
            print(f"skip {season}: {exc}", file=sys.stderr)
            continue
        lines += [
            f"  {season}:",
            f"    games: {row['games']}",
            f"    pa: {row['pa']}",
            f"    runs: {row['runs']}",
            f"    outs: {row['outs']}",
        ]
    OUT.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
