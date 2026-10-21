"""Bundled league WAR inputs reproduce FanGraphs' runs per win and published position-player WAR rows."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import polars as pl
import pytest
import yaml

import sabermetricspy as sp
from sabermetricspy.constants import bundled_constants, get_league_war_constants
from sabermetricspy.value import WARFramework

ROWS = yaml.safe_load(
    (Path(__file__).parent / "golden" / "position_war_leaderboard.yaml").read_text("utf-8")
)["rows"]


# 1998 is the one season where the MLB Stats API totals give a runs per win 0.009 above Guts (10.241 vs 10.232);
# FanGraphs' own 1998 league totals give the same 10.241, so the published Guts figure is the outlier; it is excluded here and recorded in docs/VERIFICATION.md.
KNOWN_GUTS_GAP = {1998}


def test_runs_per_win_from_league_totals_equals_guts_for_every_season() -> None:
    """Guts prints R/W to three decimals; the formula from MLB runs and outs must agree within that rounding."""
    guts = bundled_constants()
    seasons = sorted(set(guts) - KNOWN_GUTS_GAP)
    assert len(seasons) >= 36
    for season in seasons:
        league = get_league_war_constants(season)
        assert league.runs_per_win == pytest.approx(guts[season].lg_r_per_w, abs=0.0006), season


def test_known_gap_season_is_still_the_measured_size() -> None:
    gap = get_league_war_constants(1998).runs_per_win - bundled_constants()[1998].lg_r_per_w
    assert gap == pytest.approx(0.009, abs=0.0005)


@pytest.mark.parametrize(
    ("season", "games", "pa"), [(2002, 2426, 186615), (2013, 2431, 184873), (2020, 898, 66506)]
)
def test_games_and_plate_appearances_for_unusual_seasons(season: int, games: int, pa: int) -> None:
    league = get_league_war_constants(season)
    assert (league.games, league.pa) == (games, pa)


def test_replacement_runs_per_600_pa_is_below_a_flat_twenty() -> None:
    """The FanGraphs formula gives 16.95 to 19.54 runs per 600 PA (2000-2026), never the flat 20."""
    rates = [get_league_war_constants(y).replacement_runs_per_600_pa for y in range(2000, 2027)]
    assert 16.9 < min(rates) < 17.0
    assert 19.5 < max(rates) < 19.6


@pytest.mark.parametrize("row", ROWS, ids=lambda r: f"{r['player']} {r['season']}")
def test_framework_reproduces_published_replacement_and_war(row: dict[str, Any]) -> None:
    fw = WARFramework(season=row["season"])
    assert fw.context.weights is not None
    rpw = fw.context.weights.lg_r_per_w
    frame = pl.DataFrame(
        {
            "pa": [row["pa"]],
            "batting_runs": [row["batting"]],
            "bsr": [row["baserunning"]],
            "fielding_runs": [row["fielding"] or 0.0],
            "league_runs": [row["wleague"]],
        }
    )
    out = fw.calculate_position_player_df(frame).row(0, named=True)
    assert out["replacement_runs"] == pytest.approx(row["replacement"], abs=0.002)
    war = (
        row["batting"]
        + row["baserunning"]
        + (row["fielding"] or 0.0)
        + row["positional"]
        + row["wleague"]
        + out["replacement_runs"]
    ) / rpw
    assert war == pytest.approx(row["war"], abs=0.0005)


def test_flat_replacement_rate_is_still_available_when_asked_for() -> None:
    fw = WARFramework(season=2024, replacement_runs_per_600_pa=20.5)
    frame = pl.DataFrame({"pa": [600], "batting_runs": [0.0]})
    assert fw.calculate_position_player_df(frame)["replacement_runs"][0] == pytest.approx(20.5)


def test_default_replacement_is_the_season_formula_not_a_flat_rate() -> None:
    frame = pl.DataFrame({"pa": [600], "batting_runs": [0.0]})
    got = sp.WARFramework(season=2024).calculate_position_player_df(frame)["replacement_runs"][0]
    # the framework divides by the bundled Guts R/W (three decimals), so allow that rounding
    assert got == pytest.approx(
        get_league_war_constants(2024).replacement_runs_per_600_pa, rel=1e-3
    )
    assert got != pytest.approx(20.0, abs=0.5)
