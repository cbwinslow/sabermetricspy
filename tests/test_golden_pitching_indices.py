"""Pitcher K%+, BB%+, K-BB%, K/BB and H/9 must reproduce the FanGraphs leaderboard.

FanGraphs divides a pitcher's K% and BB% by the strikeout and walk rates per batter faced of the pitcher's
own league (AL or NL, all pitchers). The league rates are recorded in
tests/golden/league_pitching_rates_snapshot.yaml; the snapshot is checked for internal consistency
(SO and BB against the league WAR totals, AL+NL TBF against the MLB totals) before it is trusted.
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

ENTRIES = load_entries("pitching_indices.yaml")


def _yaml(name: str) -> Any:
    return yaml.safe_load((GOLDEN_DIR / name).read_text(encoding="utf-8"))


SNAPSHOT = _yaml("league_pitching_rates_snapshot.yaml")["seasons"]

METRICS: dict[str, tuple[Metric, str]] = {
    "pit_k_pct": (Metric.PIT_K_PCT, "pit_k_pct"),
    "pit_bb_pct": (Metric.PIT_BB_PCT, "pit_bb_pct"),
    "pit_k_minus_bb_pct": (Metric.PIT_K_MINUS_BB_PCT, "pit_k_minus_bb_pct"),
    "pit_k_to_bb": (Metric.PIT_K_TO_BB, "pit_k_to_bb"),
    "h_per_9": (Metric.H_PER_9, "h_per_9"),
    "k_pct_plus": (Metric.K_PCT_PLUS, "k_pct_plus"),
    "bb_pct_plus": (Metric.BB_PCT_PLUS, "bb_pct_plus"),
}


def test_league_snapshot_is_consistent_with_the_other_snapshots() -> None:
    war = _yaml("league_war_totals_snapshot.yaml")["seasons"]
    mlb = _yaml("league_totals_snapshot.yaml")["pitching"]
    assert sorted(SNAPSHOT) == list(range(1990, 2026))
    for season, leagues in SNAPSHOT.items():
        for lg in ("AL", "NL"):
            assert leagues[lg]["so"] == war[season][lg.lower()]["so"], (season, lg)
            assert leagues[lg]["bb"] == war[season][lg.lower()]["bb"], (season, lg)
        assert leagues["AL"]["tbf"] + leagues["NL"]["tbf"] == mlb[season]["tbf"], season


@pytest.mark.parametrize("entry", ENTRIES, ids=[e["id"] for e in ENTRIES])
def test_fixture_matches_the_league_snapshot(entry: dict[str, Any]) -> None:
    i, lg = entry["inputs"], SNAPSHOT[entry["season"]][entry["league"]]
    pub, tol = entry["published"], entry["tolerance"]
    assert i["so"] / i["bf"] == pytest.approx(pub["pit_k_pct"], abs=tol["pit_k_pct"])
    assert i["bb"] / i["bf"] == pytest.approx(pub["pit_bb_pct"], abs=tol["pit_bb_pct"])
    assert 100 * (i["so"] / i["bf"]) / (lg["so"] / lg["tbf"]) == pytest.approx(
        pub["k_pct_plus"], abs=tol["k_pct_plus"]
    )
    assert 100 * (i["bb"] / i["bf"]) / (lg["bb"] / lg["tbf"]) == pytest.approx(
        pub["bb_pct_plus"], abs=tol["bb_pct_plus"]
    )


@pytest.mark.parametrize("entry", ENTRIES, ids=[e["id"] for e in ENTRIES])
def test_library_reproduces_published_pitcher_rates(entry: dict[str, Any]) -> None:
    i = entry["inputs"]
    frame = pl.DataFrame(
        {
            "player_id": [entry["id"]],
            **{k: [v] for k, v in i.items() if k in ("bf", "so", "bb", "outs", "h")},
        }
    )
    ctx = SeasonContext(season=entry["season"], league=entry["league"])
    row = sp.calculate(frame, [m for m, _ in METRICS.values()], context=ctx).df.row(0, named=True)
    for key, (_, column) in METRICS.items():
        assert row[column] == pytest.approx(entry["published"][key], abs=entry["tolerance"][key]), (
            key
        )


def test_bundled_pitcher_league_rates_equal_the_snapshot() -> None:
    for season, leagues in SNAPSHOT.items():
        w = get_woba_weights(season)
        for lg in ("AL", "NL"):
            assert w.pit_k_pct_for(lg) == pytest.approx(
                leagues[lg]["so"] / leagues[lg]["tbf"], abs=1e-9
            )
            assert w.pit_bb_pct_for(lg) == pytest.approx(
                leagues[lg]["bb"] / leagues[lg]["tbf"], abs=1e-9
            )


def test_mlb_wide_context_falls_back_to_the_mlb_rate() -> None:
    w = get_woba_weights(2016)
    assert w.pit_k_pct_for("MLB") == w.lg_k_pct
    assert w.pit_bb_pct_for("MLB") == w.lg_bb_pct


@pytest.mark.parametrize("entry", load_entries("era_plus.yaml"), ids=lambda e: e["id"])
def test_era_plus_stays_within_the_documented_divergence_from_baseball_reference(
    entry: dict[str, Any],
) -> None:
    """ERA+ is approximate: Baseball-Reference uses league (AL/NL) ERA and its own park factor."""
    base = next(e for e in load_entries("pitching.yaml") if e["id"] == entry["fixture_id"])
    i = base["inputs"]
    frame = pl.DataFrame({"player_id": [entry["id"]], "er": [i["er"]], "outs": [i["outs"]]})
    ctx = SeasonContext(season=entry["season"], park_factor=base.get("park_factor", 100.0))
    got = sp.calculate(frame, [Metric.ERA_PLUS], context=ctx).df.row(0, named=True)["era_plus"]
    want = entry["published"]["era_plus"]
    assert got == pytest.approx(want, rel=entry["tolerance_relative"])
    assert got != pytest.approx(want, rel=0.005), (
        "ERA+ now matches: promote it to matches and tighten"
    )
