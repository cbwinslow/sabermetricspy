"""League run-environment data for pitcher WAR must be internally consistent and equal its snapshot."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).parent.parent
SNAPSHOT = Path(__file__).parent / "golden" / "league_war_totals_snapshot.yaml"
BUNDLED = ROOT / "src" / "sabermetricspy" / "data" / "constants" / "pitcher_war.yaml"
LEAGUE_TOTALS = Path(__file__).parent / "golden" / "league_totals_snapshot.yaml"

FIELDS = ("outs", "r", "er", "hr", "bb", "hbp", "so", "iffb")


def _seasons(path: Path) -> dict[int, dict[str, Any]]:
    return yaml.safe_load(path.read_text(encoding="utf-8"))["seasons"]


def _outs(notation: str) -> int:
    whole, thirds = notation.split(".")
    return int(whole) * 3 + int(thirds)


def snapshot_problems(
    bundled: dict[int, dict[str, Any]], snap: dict[int, dict[str, Any]]
) -> list[str]:
    problems = []
    for year, entry in snap.items():
        if year not in bundled:
            problems.append(f"{year}: missing from bundled data")
            continue
        for lg in ("al", "nl"):
            for field in FIELDS:
                if bundled[year][lg][field] != entry[lg][field]:
                    problems.append(
                        f"{year}.{lg}.{field}: {bundled[year][lg][field]} != {entry[lg][field]}"
                    )
        if bundled[year].get("war_ip_correction") != entry.get("war_ip_correction"):
            problems.append(f"{year}: war_ip_correction differs")
    return problems


def test_bundled_pitcher_war_data_equals_the_snapshot() -> None:
    assert snapshot_problems(_seasons(BUNDLED), _seasons(SNAPSHOT)) == []


def test_comparison_detects_an_altered_value() -> None:
    bundled = _seasons(BUNDLED)
    altered = {year: {**entry, "al": {**entry["al"]}} for year, entry in bundled.items()}
    altered[2016]["al"]["hr"] += 1
    assert snapshot_problems(altered, _seasons(SNAPSHOT))


def test_covers_every_season_with_provenance() -> None:
    seasons = _seasons(BUNDLED)
    assert sorted(seasons) == list(range(1990, 2026))
    for year, entry in seasons.items():
        assert entry["source"] and entry["retrieved"], year


def test_al_plus_nl_equals_the_mlb_league_totals() -> None:
    mlb = yaml.safe_load(LEAGUE_TOTALS.read_text(encoding="utf-8"))["pitching"]
    for year, entry in _seasons(BUNDLED).items():
        total = {
            f: entry["al"][f] + entry["nl"][f] for f in ("outs", "r", "er", "hr", "bb", "hbp", "so")
        }
        expected = {
            "outs": _outs(mlb[year]["ip_notation"]),
            "r": mlb[year]["r"],
            "er": mlb[year]["er"],
            "hr": mlb[year]["hr"],
            "bb": mlb[year]["bb"],
            "hbp": mlb[year]["hbp"],
            "so": mlb[year]["so"],
        }
        assert total == expected, year


def test_infield_flies_are_published_only_from_2002() -> None:
    for year, entry in _seasons(BUNDLED).items():
        for lg in ("al", "nl"):
            assert (entry[lg]["iffb"] is None) == (year < 2002), (year, lg)


def test_2016_matches_the_fangraphs_worked_example() -> None:
    entry = _seasons(BUNDLED)[2016]
    # FanGraphs "Calculating Pitcher WAR, A Complete Example" (Stroman 2016) quotes AL totals and the MLB sums.
    assert entry["al"]["hr"] == 2934
    assert entry["al"]["bb"] == 7280
    assert entry["al"]["hbp"] == 771
    assert entry["al"]["so"] == 19244
    assert entry["al"]["iffb"] == 2320
    assert entry["al"]["outs"] == 21611 * 3
    assert entry["al"]["hr"] + entry["nl"]["hr"] == 5610
    assert entry["al"]["bb"] + entry["nl"]["bb"] == 15088
    assert entry["al"]["hbp"] + entry["nl"]["hbp"] == 1651
    assert entry["al"]["so"] + entry["nl"]["so"] == 38982
    assert entry["al"]["iffb"] + entry["nl"]["iffb"] == 4234
    assert entry["war_ip_correction"] == -0.000682902
