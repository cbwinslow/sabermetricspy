"""Batter K%+ and BB%+ must reproduce FanGraphs: the rate divided by the player's own league (AL or NL).

FanGraphs divides by the non-pitcher BB%/K% of the player's league, not by the MLB-wide rate; the league
rates are recorded in tests/golden/league_bb_k_snapshot.yaml and pass a recomputation gate (BB/PA and SO/PA
equal the published rates) before they are trusted.
"""

from __future__ import annotations

from typing import Any

import polars as pl
import pytest
import yaml
from golden_loader import GOLDEN_DIR, load_entries

import sabermetricspy as sp
from sabermetricspy import Metric
from sabermetricspy.constants import get_woba_weights
from sabermetricspy.types.context import SeasonContext

ENTRIES = load_entries("batting_indices.yaml")
SNAPSHOT = yaml.safe_load((GOLDEN_DIR / "league_bb_k_snapshot.yaml").read_text(encoding="utf-8"))[
    "seasons"
]


def test_league_snapshot_recomputation_gate() -> None:
    assert sorted(SNAPSHOT) == list(range(1990, 2026))
    for season, leagues in SNAPSHOT.items():
        assert set(leagues) == {"AL", "NL"}
        for lg, row in leagues.items():
            assert row["bb"] / row["pa"] == pytest.approx(row["bb_pct"], abs=1e-8), (season, lg)
            assert row["so"] / row["pa"] == pytest.approx(row["k_pct"], abs=1e-8), (season, lg)


@pytest.mark.parametrize("entry", ENTRIES, ids=[e["id"] for e in ENTRIES])
def test_fixture_matches_the_league_snapshot(entry: dict[str, Any]) -> None:
    i, lg = entry["inputs"], SNAPSHOT[entry["season"]][entry["league"]]
    assert i["bb"] / i["pa"] == pytest.approx(entry["published"]["bb_pct"], abs=1e-8)
    assert i["so"] / i["pa"] == pytest.approx(entry["published"]["k_pct"], abs=1e-8)
    assert 100 * (i["bb"] / i["pa"]) / lg["bb_pct"] == pytest.approx(
        entry["published"]["bat_bb_pct_plus"], abs=entry["tolerance"]["bat_bb_pct_plus"]
    )
    assert 100 * (i["so"] / i["pa"]) / lg["k_pct"] == pytest.approx(
        entry["published"]["bat_k_pct_plus"], abs=entry["tolerance"]["bat_k_pct_plus"]
    )


@pytest.mark.parametrize("entry", ENTRIES, ids=[e["id"] for e in ENTRIES])
def test_library_reproduces_published_indices(entry: dict[str, Any]) -> None:
    i = entry["inputs"]
    frame = pl.DataFrame(
        {"player_id": [entry["id"]], "pa": [i["pa"]], "bb": [i["bb"]], "so": [i["so"]]}
    )
    ctx = SeasonContext(season=entry["season"], league=entry["league"])
    row = sp.calculate(frame, [Metric.BAT_BB_PCT_PLUS, Metric.BAT_K_PCT_PLUS], context=ctx).df.row(
        0, named=True
    )
    for key in ("bat_bb_pct_plus", "bat_k_pct_plus"):
        assert row[key] == pytest.approx(entry["published"][key], abs=entry["tolerance"][key]), key


def test_bundled_league_rates_equal_the_snapshot() -> None:
    for season, leagues in SNAPSHOT.items():
        w = get_woba_weights(season)
        assert w.bb_pct_for("AL") == pytest.approx(leagues["AL"]["bb_pct"], abs=1e-8)
        assert w.bb_pct_for("NL") == pytest.approx(leagues["NL"]["bb_pct"], abs=1e-8)
        assert w.k_pct_for("AL") == pytest.approx(leagues["AL"]["k_pct"], abs=1e-8)
        assert w.k_pct_for("NL") == pytest.approx(leagues["NL"]["k_pct"], abs=1e-8)


def test_mlb_wide_context_falls_back_to_the_mlb_rate() -> None:
    w = get_woba_weights(2024)
    assert w.bb_pct_for("MLB") == w.lg_bb_pct
    assert w.k_pct_for("MLB") == w.lg_k_pct


COUNTING = load_entries("batting_counting.yaml")


@pytest.mark.parametrize("entry", COUNTING, ids=[e["id"] for e in COUNTING])
def test_library_reproduces_singles_total_bases_and_bb_per_k(entry: dict[str, Any]) -> None:
    i = entry["inputs"]
    frame = pl.DataFrame({"player_id": [entry["id"]], **{k: [v] for k, v in i.items()}})
    row = sp.calculate(frame, [Metric.B1, Metric.TB, Metric.BB_TO_K]).df.row(0, named=True)
    for key in ("b1", "tb", "bb_to_k"):
        assert row[key] == pytest.approx(
            entry["published"][key], abs=max(entry["tolerance"][key], 1e-12)
        ), key
