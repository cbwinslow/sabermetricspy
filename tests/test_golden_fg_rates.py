"""Rate statistics against FanGraphs leaderboards (retrieved 2026-10-21 with baseballr::fg_batter_leaders / fg_pitcher_leaders).

833 qualified batter-seasons and 2,005 pitcher-seasons with 50 or more IP, from 2005, 2012, 2016, 2019, 2022 and 2024
(tests/golden/fg_batting_rates.csv, fg_pitching_rates.csv; built by tools/fg_leaderboards.R and tools/fg_leaderboards.py).
FanGraphs prints these rates to four decimals, so a half unit in the fourth decimal (bounded here by 5.5e-5, as FanGraphs rounds a few values by a hair more) is the rounding bound.
"""

from __future__ import annotations

from pathlib import Path
from typing import cast

import polars as pl
import pytest

import sabermetricspy as sp
from sabermetricspy import Metric

GOLDEN = Path(__file__).parent / "golden"
BAT = pl.read_csv(GOLDEN / "fg_batting_rates.csv")
PIT = pl.read_csv(GOLDEN / "fg_pitching_rates.csv")
HALF_UNIT = 5.5e-5  # FanGraphs prints four decimals; ERA is off by 5.14e-5 at worst, so the bound is empirical


def _worst(got: pl.Series, published: pl.Series) -> float:
    return cast(float, (got - published).abs().max())


def test_the_fixtures_hold_every_row() -> None:
    assert (BAT.height, PIT.height) == (833, 2005)


@pytest.mark.parametrize(
    ("metric", "column"),
    [
        (Metric.OBP, "pub_obp"),
        (Metric.SLG, "pub_slg"),
        (Metric.ISO, "pub_iso"),
        (Metric.BB_PCT, "pub_bb_pct"),
        (Metric.K_PCT, "pub_k_pct"),
        (Metric.BB_TO_K, "pub_bb_k"),
    ],
)
def test_batter_rates_match_fangraphs(metric: Metric, column: str) -> None:
    got = sp.calculate(BAT, [metric]).df[metric.value]
    assert _worst(got, BAT[column]) < HALF_UNIT


def test_batter_k_minus_bb_is_the_difference_of_the_published_rates() -> None:
    got = sp.calculate(BAT, [Metric.K_MINUS_BB_PCT]).df["k_minus_bb_pct"]
    assert _worst(got, BAT["pub_k_pct"] - BAT["pub_bb_pct"]) < 2 * HALF_UNIT


@pytest.mark.parametrize(
    ("metric", "column"),
    [
        (Metric.PIT_K_PCT, "pub_k_pct"),
        (Metric.PIT_BB_PCT, "pub_bb_pct"),
        (Metric.PIT_K_MINUS_BB_PCT, "pub_k_minus_bb"),
        (Metric.PIT_K_TO_BB, "pub_k_bb"),
    ],
)
def test_pitcher_rates_match_fangraphs(metric: Metric, column: str) -> None:
    got = sp.calculate(PIT, [metric]).df[metric.value]
    assert _worst(got, PIT[column]) < HALF_UNIT


def test_innings_notation_round_trips_through_outs() -> None:
    """The fixture stores outs converted from FanGraphs' notation; this checks the conversion, not an independent total."""
    got = sp.calculate(PIT, [Metric.IP]).df["ip"]
    whole = PIT["pub_ip"].floor()
    thirds = ((PIT["pub_ip"] - whole) * 10).round()
    assert _worst(got, whole + thirds / 3) < 1e-9


def test_runs_per_nine_equals_the_published_era_where_every_run_is_earned() -> None:
    """RA9 and ERA share 9 * runs / IP; on the pitcher-seasons with no unearned runs FanGraphs' ERA is the RA9."""
    clean = PIT.filter(pl.col("r") == pl.col("er"))
    got = sp.calculate(clean.select("outs", pl.col("r").alias("ra")), [Metric.RA9]).df["ra9"]
    assert clean.height == 170
    assert _worst(got, clean["pub_era"]) < HALF_UNIT
