"""Opt-in check: MarkovWinExpectancy fitted on Retrosheet 2016 agrees with Tom Tango's published win expectancy table.

Runs only when SABERMETRICSPY_RETRO2016 names a local copy of `retro2016.rda` (CC0 in the abdwr3edata package,
https://github.com/beanumber/abdwr3edata/raw/main/data/retro2016.rda) and `pyreadr` is installed:

    SABERMETRICSPY_RETRO2016=path/to/retro2016.rda uv run --with pyreadr --with pandas pytest tests/test_retrosheet_2016_markov_win_expectancy.py

Tango's table (https://tangotiger.net/we.html) is built from 2010-2015 run expectancy; one 2016 season has a slightly
different run environment, so the gate is a mean absolute error and a maximum, over the stratified cells in
tests/golden/win_expectancy_tango_2010_2015.yaml. Plays are those of completed half-innings through the 8th, as in
Tango's run expectancy note.
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

CELLS: list[dict[str, Any]] = yaml.safe_load(
    (Path(__file__).parent / "golden" / "win_expectancy_tango_2010_2015.yaml").read_text("utf-8")
)["cells"]


def _occupied(col: str) -> pl.Expr:
    return pl.col(col).is_not_null() & (pl.col(col) != "")


def _plays() -> pl.DataFrame:
    import pyreadr  # pyright: ignore[reportMissingImports]

    frame: Any = pyreadr.read_r(PATH)["retro2016"]
    ev = pl.from_pandas(frame).with_row_index("i").sort("i")
    dests = ["bat_dest_id", "run1_dest_id", "run2_dest_id", "run3_dest_id"]
    half = ["game_id", "inn_ct", "bat_home_id"]

    def bases(prefix: str) -> pl.Expr:
        return (
            pl.when(_occupied("base1_run_id")).then(pl.lit("1")).otherwise(pl.lit("-"))
            + pl.when(_occupied("base2_run_id")).then(pl.lit("2")).otherwise(pl.lit("-"))
            + pl.when(_occupied("base3_run_id")).then(pl.lit("3")).otherwise(pl.lit("-"))
        ).alias(prefix)

    ev = ev.with_columns(
        pl.sum_horizontal((pl.col(c) >= 4).cast(pl.Int64) for c in dests).alias("runs_on_play"),
        bases("base_state_before"),
    ).with_columns(
        (pl.col("outs_ct") + pl.col("event_outs_ct")).max().over(*half).alias("end_outs"),
        pl.col("outs_ct").shift(-1).over(*half).alias("outs_next"),
        pl.col("base_state_before").shift(-1).over(*half).alias("bases_next"),
    )
    ev = ev.filter((pl.col("end_outs") == 3) & (pl.col("inn_ct") <= 8))
    return ev.select(
        pl.col("outs_ct").alias("outs_before"),
        "base_state_before",
        pl.col("outs_next").fill_null(3).alias("outs_after"),
        pl.col("bases_next").fill_null("---").alias("base_state_after"),
        "runs_on_play",
    )


@pytest.fixture(scope="module")
def fitted() -> sp.MarkovWinExpectancy:
    return sp.MarkovWinExpectancy().fit(_plays())


def _errors(model: sp.MarkovWinExpectancy) -> list[float]:
    return [
        abs(
            model.win_expectancy(c["inning"], c["half"], c["outs"], c["bases"], c["diff"]) - c["we"]
        )
        for c in CELLS
    ]


def test_cells_agree_with_the_published_table(fitted: sp.MarkovWinExpectancy) -> None:
    errors = _errors(fitted)
    assert len(errors) == 198
    assert sum(errors) / len(errors) < 0.01
    assert max(errors) < 0.025


def test_start_of_the_game_is_a_half(fitted: sp.MarkovWinExpectancy) -> None:
    assert fitted.win_expectancy(1, "top", 0, "---", 0) == pytest.approx(0.5, abs=1e-3)
