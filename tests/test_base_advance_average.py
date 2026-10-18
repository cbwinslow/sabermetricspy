"""Base-Advance Average (Hardegree 2005) reproduced on the paper's sample half-inning."""

from __future__ import annotations

from pathlib import Path

import polars as pl
import pytest
import yaml

import sabermetricspy as sp
from sabermetricspy import Metric
from sabermetricspy.expectancy import add_base_advance_columns

REF = yaml.safe_load(
    (Path(__file__).parent / "golden" / "base_advance_sample_inning.yaml").read_text("utf-8")
)
PLAYS = pl.DataFrame(
    {
        "base_state_before": [p["before"] for p in REF["plays"]],
        "base_state_after": [p["after"] for p in REF["plays"]],
        "runs_on_play": [p["runs"] for p in REF["plays"]],
    }
)


def test_published_rows_sum_to_the_published_totals() -> None:
    """Recomputation gate on the fixture itself."""
    assert sum(p["bases_advanced"] for p in REF["plays"]) == REF["total_bases"]
    assert sum(p["opportunities"] for p in REF["plays"]) == REF["total_opportunities"]
    ratio = REF["total_bases"] / REF["total_opportunities"]
    assert int(ratio * 1000) / 1000 == REF["printed_average"]


def test_helper_reproduces_every_row_of_the_sample_inning() -> None:
    out = add_base_advance_columns(PLAYS)
    assert out["bases_advanced"].to_list() == [p["bases_advanced"] for p in REF["plays"]]
    assert out["base_advance_opps"].to_list() == [p["opportunities"] for p in REF["plays"]]


def test_metric_gives_the_inning_average() -> None:
    out = add_base_advance_columns(PLAYS).select("bases_advanced", "base_advance_opps").sum()
    result = sp.calculate(
        out.with_columns(pl.lit("x").alias("player_id")), [Metric.BASE_ADVANCE_AVERAGE]
    )
    assert result.df["base_advance_average"][0] == pytest.approx(14 / 57, abs=1e-12)


def test_batter_out_with_bases_empty_is_zero_for_four() -> None:
    frame = pl.DataFrame(
        {"base_state_before": ["---"], "base_state_after": ["---"], "runs_on_play": [0]}
    )
    out = add_base_advance_columns(frame)
    assert (out["bases_advanced"][0], out["base_advance_opps"][0]) == (0, 4)


def test_grand_slam_is_ten_for_ten() -> None:
    frame = pl.DataFrame(
        {"base_state_before": ["123"], "base_state_after": ["---"], "runs_on_play": [4]}
    )
    out = add_base_advance_columns(frame)
    assert (out["bases_advanced"][0], out["base_advance_opps"][0]) == (10, 10)


def test_walk_with_bases_loaded_is_four_for_ten() -> None:
    frame = pl.DataFrame(
        {"base_state_before": ["123"], "base_state_after": ["123"], "runs_on_play": [1]}
    )
    out = add_base_advance_columns(frame)
    assert (out["bases_advanced"][0], out["base_advance_opps"][0]) == (4, 10)
