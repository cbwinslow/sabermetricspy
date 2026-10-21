"""Pitcher WAR against 1,477 FanGraphs leaderboard pitcher-seasons (2016, 2019, 2022, 2024, 2025; 50 or more IP).

Inputs are FanGraphs counting stats (tests/golden/pitcher_war_leaderboard.csv, retrieved 2026-10-21 through baseballr
fg_pitcher_leaders) with the FIP park factor of the pitcher's team taken from the bundled park_fip.yaml. FanGraphs values
a pitcher's starts and relief innings separately and its park factor is unrounded, so single rows can differ by half a
win; the gates are therefore on the distribution of the errors.
"""

from __future__ import annotations

from pathlib import Path
from typing import cast

import polars as pl
import pytest

import sabermetricspy as sp
from sabermetricspy.constants import get_fip_park_factor

DATA = pl.read_csv(Path(__file__).parent / "golden" / "pitcher_war_leaderboard.csv")


def _errors(season: int) -> pl.DataFrame:
    sub = DATA.filter(pl.col("season") == season)
    pf = [get_fip_park_factor(t, season) for t in sub["team"]]
    frame = sub.with_columns(pl.Series("fip_park_factor", pf)).drop("war")
    out = sp.WARFramework(season=season).calculate_pitcher_war_df(frame)
    return sub.with_columns(
        (pl.col("war") - out["pitcher_war"]).abs().alias("err"),
        ((pl.col("gs") == pl.col("g")) | (pl.col("gs") == 0)).alias("single_role"),
    )


def _share(err: pl.Series, bound: float) -> float:
    return cast(float, (err <= bound).cast(pl.Float64).mean())


@pytest.mark.parametrize(
    ("season", "median_bound", "within_quarter"),
    [
        (2016, 0.11, 0.85),
        (2019, 0.08, 0.92),
        (2022, 0.07, 0.92),
        (2024, 0.06, 0.95),
        (2025, 0.06, 0.95),
    ],
)
def test_error_distribution_against_the_leaderboard(
    season: int, median_bound: float, within_quarter: float
) -> None:
    res = _errors(season)
    assert cast(float, res["err"].median()) < median_bound
    assert _share(res["err"], 0.25) >= within_quarter


def test_single_role_pitchers_are_closer_than_mixed_ones() -> None:
    res = pl.concat([_errors(y) for y in (2019, 2022, 2024, 2025)])
    single = res.filter(pl.col("single_role"))["err"]
    mixed = res.filter(~pl.col("single_role"))["err"]
    assert cast(float, single.median()) < cast(float, mixed.median())
    assert _share(single, 0.25) > 0.95
