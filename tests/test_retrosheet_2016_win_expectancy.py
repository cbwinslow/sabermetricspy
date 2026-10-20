"""Opt-in check: WinExpectancyMatrix.fit() on Retrosheet 2016 agrees with Tom Tango's published win expectancy table.

Runs only when SABERMETRICSPY_RETRO2016 names a local copy of `retro2016.rda` (CC0 in the abdwr3edata package,
https://github.com/beanumber/abdwr3edata/raw/main/data/retro2016.rda; Retrosheet's notice applies to the underlying
data, https://www.retrosheet.org/notice.txt) and `pyreadr` is installed:

    SABERMETRICSPY_RETRO2016=path/to/retro2016.rda uv run --with pyreadr --with pandas pytest tests/test_retrosheet_2016_win_expectancy.py

Tango's table (tests/golden/win_expectancy_tango.yaml) states no seasons, and one season has few games in the rarer
states. The gate is therefore statistical: every bottom-of-the-9th cell with at least 30 games must lie within three
binomial standard errors of the published value, and the mean z-score over those cells must be small.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import polars as pl
import pytest
import yaml

import sabermetricspy as sp

PATH = os.environ.get("SABERMETRICSPY_RETRO2016")
pytestmark = pytest.mark.skipif(not PATH, reason="set SABERMETRICSPY_RETRO2016 to retro2016.rda")

REF = yaml.safe_load(
    (Path(__file__).parent / "golden" / "win_expectancy_tango.yaml").read_text("utf-8")
)
MIN_GAMES = 30


def _occupied(col: str) -> pl.Expr:
    return pl.col(col).is_not_null() & (pl.col(col) != "")


def _plate_appearances() -> pl.DataFrame:
    import pyreadr  # pyright: ignore[reportMissingImports]

    frame: Any = pyreadr.read_r(PATH)["retro2016"]
    events = pl.from_pandas(frame)
    dests = ["bat_dest_id", "run1_dest_id", "run2_dest_id", "run3_dest_id"]
    events = events.with_columns(
        pl.sum_horizontal((pl.col(c) >= 4).cast(pl.Int64) for c in dests).alias("runs_on_play"),
        (
            pl.when(_occupied("base1_run_id")).then(pl.lit("1")).otherwise(pl.lit("-"))
            + pl.when(_occupied("base2_run_id")).then(pl.lit("2")).otherwise(pl.lit("-"))
            + pl.when(_occupied("base3_run_id")).then(pl.lit("3")).otherwise(pl.lit("-"))
        ).alias("base_state_before"),
    )
    final = (
        events.group_by("game_id", maintain_order=True)
        .last()
        .select(
            "game_id",
            (
                pl.col("home_score_ct")
                + pl.when(pl.col("bat_home_id") == 1).then(pl.col("runs_on_play")).otherwise(0)
            ).alias("home_final"),
            (
                pl.col("away_score_ct")
                + pl.when(pl.col("bat_home_id") == 0).then(pl.col("runs_on_play")).otherwise(0)
            ).alias("away_final"),
        )
        .filter(pl.col("home_final") != pl.col("away_final"))  # a suspended game has no winner
        .with_columns(
            (pl.col("home_final") > pl.col("away_final")).cast(pl.Int64).alias("home_win")
        )
    )
    return events.join(final.select("game_id", "home_win"), on="game_id").select(
        "game_id",
        pl.col("inn_ct").alias("inning"),
        (pl.col("bat_home_id") == 1).alias("is_bottom"),
        pl.col("outs_ct").alias("outs_before"),
        "base_state_before",
        (pl.col("home_score_ct") - pl.col("away_score_ct")).alias("home_score_diff"),
        "home_win",
    )


@pytest.fixture(scope="module")
def fitted() -> sp.WinExpectancyResults:
    return sp.WinExpectancyMatrix().fit(_plate_appearances()).results


def _zscores(res: sp.WinExpectancyResults) -> list[tuple[str, float]]:
    out: list[tuple[str, float]] = []
    for table, diff in (("bottom9_tied", 0), ("bottom9_trailing_1", -1)):
        for state, values in REF[table].items():
            for outs, published in enumerate(values):
                key = f"9|bottom|{outs}|{state}|{diff}"
                if res.state_games.get(key, 0) < MIN_GAMES:
                    continue
                se = res.standard_error(9, "bottom", outs, state, diff)
                assert se is not None
                out.append((key, (res.state_expectancy[key] - published) / se))
    return out


def test_well_sampled_cells_agree_with_the_published_table(
    fitted: sp.WinExpectancyResults,
) -> None:
    z = _zscores(fitted)
    assert len(z) >= 10
    assert all(abs(v) < 3.0 for _, v in z), [kv for kv in z if abs(kv[1]) >= 3.0]
    assert abs(sum(v for _, v in z) / len(z)) < 1.0


def test_outs_lower_the_home_win_rate_in_the_bottom_of_the_ninth(
    fitted: sp.WinExpectancyResults,
) -> None:
    rates = [fitted.lookup(9, "bottom", o, "---", 0) for o in range(3)]
    assert None not in rates
    assert rates[0] > rates[1] > rates[2]  # type: ignore[operator]
