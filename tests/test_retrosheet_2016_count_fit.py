"""Opt-in check: CountExpectancyMatrix.fit() reproduces the ABDWR 3e chapter 6 count values on Retrosheet 2016.

Runs only when SABERMETRICSPY_RETRO2016 names a local copy of `retro2016.rda` and `pyreadr` is installed, so the
default suite needs neither the data nor the network. The file is CC0 in the abdwr3edata package
(https://github.com/beanumber/abdwr3edata/raw/main/data/retro2016.rda, 2.8 MB, 190,713 event rows) and is built from
Retrosheet event files; Retrosheet's notice applies to the underlying data (https://www.retrosheet.org/notice.txt).

    SABERMETRICSPY_RETRO2016=path/to/retro2016.rda uv run --with pyreadr --with pandas pytest tests/test_retrosheet_2016_count_fit.py

Two things are checked against the chapter's printed values (tests/golden/count_run_values.yaml, `abdwr_2016`):
1. The number of event rows that pass through a count, counting each row once, equals the printed n exactly
   (76,165 for 1-0; 94,106 for 0-1; 44,254 for 2-2; 75,226 for 1-1). This pins the one-count-per-plate-appearance rule.
2. The mean of RE288(state, count) - RE288(state, 0-0) over those rows is within a few standard errors of the printed
   mean run value. The chapter averages RE24 change plus runs, which has less noise than the realised runs fit() uses.
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
    (Path(__file__).parent / "golden" / "count_run_values.yaml").read_text("utf-8")
)["abdwr_2016"]

_BALL_CODES = "BIPV"
_STRIKE_CODES = "CSKMOQRT"  # always a strike
_FOUL_CODES = "FL"  # a strike only below two strikes


def _counts_through(pitch_seq: str) -> list[tuple[int, int]]:
    """Counts a plate appearance passes through, in order, from a Retrosheet pitch sequence."""
    balls = strikes = 0
    counts = [(0, 0)]
    for code in pitch_seq:
        if code in _BALL_CODES:
            balls += 1
        elif code in _STRIKE_CODES:
            strikes += 1
        elif code in _FOUL_CODES:
            strikes += strikes < 2
        else:
            continue  # in-play, hit-by-pitch and the sequence's non-pitch markers
        if balls > 3 or strikes > 2:
            break
        counts.append((balls, strikes))
    return counts


def _occupied(col: str) -> pl.Expr:
    return pl.col(col).is_not_null() & (pl.col(col) != "")


def _pitches() -> pl.DataFrame:
    import pyreadr  # pyright: ignore[reportMissingImports]

    frame: Any = pyreadr.read_r(PATH)["retro2016"]
    events = pl.from_pandas(frame).with_row_index("event")
    dests = ["bat_dest_id", "run1_dest_id", "run2_dest_id", "run3_dest_id"]
    events = events.with_columns(
        pl.sum_horizontal((pl.col(c) >= 4).cast(pl.Int64) for c in dests).alias("runs_on_play"),
        (
            pl.when(_occupied("base1_run_id")).then(pl.lit("1")).otherwise(pl.lit("-"))
            + pl.when(_occupied("base2_run_id")).then(pl.lit("2")).otherwise(pl.lit("-"))
            + pl.when(_occupied("base3_run_id")).then(pl.lit("3")).otherwise(pl.lit("-"))
        ).alias("base_state_before"),
    ).with_columns(
        pl.col("runs_on_play")
        .reverse()
        .cum_sum()
        .reverse()
        .over("game_id", "inn_ct", "bat_home_id")
        .alias("runs_rest_of_inning")
    )
    rows: list[tuple[int, int, str, int, int, float]] = []
    for r in events.select(
        "event", "outs_ct", "base_state_before", "runs_rest_of_inning", "pitch_seq_tx"
    ).iter_rows(named=True):
        for balls, strikes in dict.fromkeys(_counts_through(r["pitch_seq_tx"] or "")):
            rows.append(
                (
                    r["event"],
                    r["outs_ct"],
                    r["base_state_before"],
                    balls,
                    strikes,
                    float(r["runs_rest_of_inning"]),
                )
            )
    return pl.DataFrame(
        rows,
        schema=[
            "pa_id",
            "outs_before",
            "base_state_before",
            "balls",
            "strikes",
            "runs_rest_of_inning",
        ],
        orient="row",
    )


@pytest.fixture(scope="module")
def fitted() -> sp.RE288Results:
    return sp.CountExpectancyMatrix().fit(_pitches()).results


def _mean_run_value(res: sp.RE288Results, balls: int, strikes: int) -> tuple[float, int]:
    total, n = 0.0, 0
    for key, count in res.state_counts.items():
        outs, bases, b, s = key.split("|")
        if (int(b), int(s)) == (balls, strikes):
            total += count * (
                res.state_expectancy[key] - res.state_expectancy[f"{outs}|{bases}|0|0"]
            )
            n += count
    return total / n, n


@pytest.mark.parametrize("label", ["1-0", "0-1", "2-2", "1-1"])
def test_event_rows_through_each_count_equal_the_printed_n(
    fitted: sp.RE288Results, label: str
) -> None:
    balls, strikes = (int(x) for x in label.split("-"))
    assert _mean_run_value(fitted, balls, strikes)[1] == REF[label]["n"]


@pytest.mark.parametrize("label", ["1-0", "0-1", "2-2", "1-1"])
def test_mean_run_value_by_count_is_close_to_the_printed_value(
    fitted: sp.RE288Results, label: str
) -> None:
    balls, strikes = (int(x) for x in label.split("-"))
    value, _ = _mean_run_value(fitted, balls, strikes)
    assert value == pytest.approx(REF[label]["value"], abs=REF["tolerance"])
