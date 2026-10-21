"""Popup rate and barrels from per-pitch Statcast rows equal the Baseball Savant 2025 leaderboards."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import polars as pl
import pytest
import yaml

import sabermetricspy as sp
from sabermetricspy import Metric
from sabermetricspy.presets import prepare_statcast_pitches

HERE = Path(__file__).parent
ROWS: list[dict[str, Any]] = yaml.safe_load(
    (HERE / "golden" / "savant_batted_balls_2025.yaml").read_text("utf-8")
)["rows"]
RAW = pl.read_csv(HERE / "fixtures" / "statcast" / "batted_balls_2025.csv", infer_schema_length=0)


def _row(batter: int) -> dict[str, Any]:
    sub = RAW.filter(pl.col("batter") == str(batter))
    prepared = prepare_statcast_pitches(sub)
    return sp.calculate(prepared, [Metric.PU_PCT, Metric.BARREL_PCT], by="player_id").df.row(
        0, named=True
    )


@pytest.mark.parametrize("ref", ROWS, ids=lambda r: r["player"])
def test_popup_rate_equals_savant_pu_rate(ref: dict[str, Any]) -> None:
    got = _row(ref["batter"])
    assert got["bbe"] == ref["bbe"]
    assert got["pu_pct"] == pytest.approx(ref["pu_rate"], abs=1e-9)


@pytest.mark.parametrize("ref", ROWS, ids=lambda r: r["player"])
def test_barrels_equal_savant_barrel_count(ref: dict[str, Any]) -> None:
    got = _row(ref["batter"])
    assert got["barrels"] == ref["barrels"]
    assert got["barrel_pct"] == pytest.approx(ref["barrels"] / ref["bbe"], abs=1e-9)
