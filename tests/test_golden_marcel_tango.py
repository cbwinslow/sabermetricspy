"""MarcelProjector against Tom Tango's published 2004 Marcel files (tangotiger.net/marcel/marcel2004.zip).

Inputs are Lahman 2001-2003 batting and pitching lines (tests/fixtures/marcel_*_2001_2003.csv), with pitchers' own hitting
left out of the league rates as Tango's step 2 does. Tango publishes whole numbers and his final "rebaseline" step is
undefined, so counting stats are compared by mean and share within tolerance; the reliability column is exact to its
two printed decimals.
"""

from __future__ import annotations

from pathlib import Path
from typing import cast

import polars as pl
import pytest

import sabermetricspy as sp

HERE = Path(__file__).parent
HIT = pl.read_csv(HERE / "fixtures" / "marcel_hitters_2001_2003.csv")
PIT = pl.read_csv(HERE / "fixtures" / "marcel_pitchers_2001_2003.csv")
PUB_BAT = pl.read_csv(HERE / "golden" / "marcel_tango_2004_batting.csv")
PUB_PIT = pl.read_csv(HERE / "golden" / "marcel_tango_2004_pitching.csv")


def _max(series: pl.Series) -> float:
    return cast(float, series.max())


def _mean(series: pl.Series) -> float:
    return cast(float, series.mean())


@pytest.fixture(scope="module")
def hitters() -> pl.DataFrame:
    proj = sp.MarcelProjector(target_season=2004).fit(HIT).predict()
    return proj.join(PUB_BAT, left_on="player_id", right_on="playerID")


@pytest.fixture(scope="module")
def pitchers() -> pl.DataFrame:
    last = PIT.filter(pl.col("season") == 2003).select(
        "player_id", (25.0 + 35.0 * pl.col("gs") / pl.col("g")).alias("base")
    )
    data = PIT.join(last, on="player_id", how="left").with_columns(pl.col("base").fill_null(25.0))
    proj = sp.MarcelProjector.for_pitchers(target_season=2004, playing_time_base="base")
    joined = proj.fit(data).predict().join(PUB_PIT, left_on="player_id", right_on="playerID")
    roles = PIT.filter(pl.col("season") == 2003).select("player_id", "g", "gs")
    return joined.join(roles, on="player_id", how="left")


def test_the_published_file_is_covered(hitters: pl.DataFrame, pitchers: pl.DataFrame) -> None:
    assert hitters.height >= 830 and pitchers.height >= 860


def test_hitter_projected_plate_appearances_equal_the_published_file(hitters: pl.DataFrame) -> None:
    # 0.5 * last + 0.1 * prior + 200, published as whole numbers
    assert _max((hitters["proj_pa"] - hitters["mPA"]).abs()) <= 0.5 + 1e-9


def test_hitter_reliability_equals_the_published_column(hitters: pl.DataFrame) -> None:
    # W / (W + 1200) with W = 5 PA1 + 4 PA2 + 3 PA3, published to two decimals
    assert _max((hitters["proj_reliability"] - hitters["reliability"]).abs()) <= 0.005 + 1e-9


def test_hitter_home_runs_are_close_to_the_published_file(hitters: pl.DataFrame) -> None:
    diff = (hitters["proj_hr"] - hitters["mHR"]).abs()
    assert _mean(diff) < 0.35
    assert _max(diff) < 0.9
    steady = hitters.filter(pl.col("reliability") >= 0.8)
    assert _mean(((steady["proj_hr"] - steady["mHR"]).abs() <= 0.5).cast(pl.Float64)) > 0.85


def test_hitter_walks_and_hits_are_close_to_the_published_file(hitters: pl.DataFrame) -> None:
    assert _mean((hitters["proj_bb"] - hitters["mBB"]).abs()) < 0.5
    assert _mean((hitters["proj_h"] - hitters["mH"]).abs()) < 0.6
    assert _mean((hitters["proj_so"] - hitters["mSO"]).abs()) < 1.7


def test_pitcher_reliability_equals_the_published_column(pitchers: pl.DataFrame) -> None:
    """The 266.67 IP of regression is inferred from this column, which every row then reproduces to its rounding."""
    within = (pitchers["proj_reliability"] - pitchers["reliability"]).abs() <= 0.005 + 1e-9
    assert _mean(within.cast(pl.Float64)) > 0.995


def test_pitcher_innings_for_pure_starters_and_relievers(pitchers: pl.DataFrame) -> None:
    """0.5 * last + 0.1 * prior + 60 (starters) or 25 (relievers); part-timers' base is not published."""
    pure = pitchers.filter(
        ((pl.col("gs") == pl.col("g")) | (pl.col("gs") == 0)) & (pl.col("g") >= 10)
    )
    assert pure.height > 100
    assert _mean(((pure["proj_ip"] - pure["mIP"]).abs() <= 1.0).cast(pl.Float64)) > 0.8


def test_beltran_and_abreu_match_the_two_rows_in_tangos_post(hitters: pl.DataFrame) -> None:
    for player, pa, hr in (("beltrca01", 573, 22), ("abreubo01", 616, 20)):
        row = hitters.filter(pl.col("player_id") == player).row(0, named=True)
        assert row["mPA"] == pa and row["mHR"] == hr
        assert row["proj_pa"] == pytest.approx(pa, abs=0.5)
        assert row["proj_hr"] == pytest.approx(hr, abs=0.5)
        assert row["proj_reliability"] == pytest.approx(0.87, abs=0.005)
