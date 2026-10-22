"""Opt-in check: LinearWeightsEstimator on Retrosheet 2016 against the FanGraphs Guts! 2016 weights.

Runs only when SABERMETRICSPY_RETRO2016 names a local copy of `retro2016.rda` and `pyreadr` is installed (see
tests/test_retrosheet_2016_count_fit.py for the file and how to run).

Run value per plate appearance = RE24(after) - RE24(before) + runs scored on the play, with RE24 taken as the mean runs to
the end of the inning in this same file. Intentional walks, interference and sacrifice bunts are left out (they are not in
wOBA's denominator). The estimator does not reproduce FanGraphs exactly (its RE24 and event definitions are not published in
enough detail): measured on 2026-10-21 the weights differ from Guts! by -0.001 (walk), -0.001 (HBP), -0.007 (single),
+0.003 (double), +0.015 (triple), +0.031 (home run), and the scale is 1.251 against 1.212.
"""

from __future__ import annotations

import os
from typing import Any

import polars as pl
import pytest

from sabermetricspy.constants import get_woba_weights
from sabermetricspy.expectancy import LinearWeightsEstimator

PATH = os.environ.get("SABERMETRICSPY_RETRO2016")
pytestmark = pytest.mark.skipif(not PATH, reason="set SABERMETRICSPY_RETRO2016 to retro2016.rda")

_EVENT_NAMES = {
    14: "walk",
    16: "hit_by_pitch",
    20: "single",
    21: "double",
    22: "triple",
    23: "home_run",
}
# Largest accepted difference from Guts! per weight (about twice what was measured).
_TOLERANCE = {
    "walk": 0.003,
    "hit_by_pitch": 0.003,
    "single": 0.015,
    "double": 0.01,
    "triple": 0.03,
    "home_run": 0.06,
}
_GUTS_FIELD = {
    "walk": "w_bb",
    "hit_by_pitch": "w_hbp",
    "single": "w_1b",
    "double": "w_2b",
    "triple": "w_3b",
    "home_run": "w_hr",
}


def _occupied(col: str) -> pl.Expr:
    return pl.col(col).is_not_null() & (pl.col(col) != "")


def _plate_appearances() -> pl.DataFrame:
    import pyreadr  # pyright: ignore[reportMissingImports]

    frame: Any = pyreadr.read_r(PATH)["retro2016"]
    events = pl.from_pandas(frame).with_row_index("i")
    dests = ["bat_dest_id", "run1_dest_id", "run2_dest_id", "run3_dest_id"]
    half = ["game_id", "inn_ct", "bat_home_id"]
    events = events.with_columns(
        pl.sum_horizontal((pl.col(c) >= 4).cast(pl.Int64) for c in dests).alias("runs_on_play"),
        (
            pl.when(_occupied("base1_run_id")).then(1).otherwise(0)
            + pl.when(_occupied("base2_run_id")).then(2).otherwise(0)
            + pl.when(_occupied("base3_run_id")).then(4).otherwise(0)
        ).alias("bases"),
    ).with_columns(
        pl.col("runs_on_play").reverse().cum_sum().reverse().over(*half).alias("rest"),
    )
    expectancy = events.group_by("outs_ct", "bases").agg(pl.col("rest").mean().alias("re"))
    events = (
        events.join(expectancy, on=["outs_ct", "bases"])
        .sort("i")
        .with_columns(pl.col("re").shift(-1).over(*half).fill_null(0.0).alias("re_after"))
        .with_columns(
            (pl.col("re_after") - pl.col("re") + pl.col("runs_on_play")).alias("run_value")
        )
    )
    batting = events.filter(
        pl.col("bat_event_fl") & ~pl.col("sh_fl") & ~pl.col("event_cd").is_in([15, 17])
    )
    return batting.select(
        pl.col("event_cd").replace_strict(_EVENT_NAMES, default="out").alias("play_outcome"),
        "run_value",
    )


@pytest.fixture(scope="module")
def fitted() -> Any:
    return LinearWeightsEstimator().fit(_plate_appearances()).results


@pytest.mark.parametrize("event", list(_TOLERANCE))
def test_weights_are_within_the_measured_gap_of_fangraphs_guts(fitted: Any, event: str) -> None:
    guts = get_woba_weights(2016)
    assert fitted.woba_weights[event] == pytest.approx(
        getattr(guts, _GUTS_FIELD[event]), abs=_TOLERANCE[event]
    )


def test_scale_is_within_five_percent_of_guts(fitted: Any) -> None:
    assert fitted.woba_scale == pytest.approx(get_woba_weights(2016).woba_scale, rel=0.05)
