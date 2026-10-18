"""Pitcher WAR compared with FanGraphs leaderboard values (tests/golden/pitcher_war.yaml).

The implementation follows the documented FanGraphs method exactly (see test_pitcher_war.py for the published
worked example). Live leaderboard values differ from the documented method by an amount FanGraphs does not
explain; this file records that difference with an explicit tolerance and lists the exceptions.
"""

from __future__ import annotations

import statistics
from typing import Any

import polars as pl
import pytest
from golden_loader import load_entries

import sabermetricspy as sp

ENTRIES = load_entries("pitcher_war.yaml")


def _library_war(entry: dict[str, Any]) -> float:
    inputs = {k: v for k, v in entry["inputs"].items() if k != "ip"}
    frame = pl.DataFrame(
        [
            {
                "player_id": entry["id"],
                "league": entry["league"],
                "fip_park_factor": entry["fip_park_factor"],
                **inputs,
            }
        ]
    )
    out = sp.WARFramework(season=entry["season"]).calculate_pitcher_war_df(frame)
    return float(out["pitcher_war"][0])


def test_fixture_entries_have_provenance_and_tolerance() -> None:
    assert len(ENTRIES) >= 25
    for e in ENTRIES:
        assert e["source_url"].startswith("https://www.fangraphs.com/"), e["id"]
        assert str(e["retrieved"]) == "2026-10-18", e["id"]
        assert e["tolerance"]["war"] > 0, e["id"]
        assert e["fip_park_factor_source"].startswith("https://www.fangraphs.com/guts.aspx"), e[
            "id"
        ]


@pytest.mark.parametrize("entry", ENTRIES, ids=lambda e: e["id"])
def test_library_war_is_within_the_stated_tolerance_of_the_leaderboard(
    entry: dict[str, Any],
) -> None:
    got = _library_war(entry)
    want = entry["published"]["war"]
    diff = got - want
    message = f"{entry['id']}: library {got:.3f} vs FanGraphs {want:.3f} (diff {diff:+.3f}); {entry['source_url']}"
    if "war" in entry.get("divergence", {}):
        assert abs(diff) > entry["tolerance"]["war"], (
            f"{message} no longer diverges; remove the divergence"
        )
        assert len(entry["divergence"]["war"]) > 40
    else:
        assert abs(diff) <= entry["tolerance"]["war"], message


def test_typical_difference_is_small_and_unbiased() -> None:
    diffs = [
        _library_war(e) - e["published"]["war"]
        for e in ENTRIES
        if "war" not in e.get("divergence", {})
    ]
    assert statistics.median(abs(d) for d in diffs) < 0.10
    assert abs(statistics.mean(diffs)) < 0.05


def test_the_two_recorded_exceptions_are_the_only_divergences() -> None:
    assert {e["id"] for e in ENTRIES if "war" in e.get("divergence", {})} == {
        "perdomo_2016",
        "skubal_2024",
    }
