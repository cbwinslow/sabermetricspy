"""Vertical approach angle from Savant kinematics equals published four-seam VAA values."""

from __future__ import annotations

import math
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
    (HERE / "golden" / "vaa_published.yaml").read_text("utf-8")
)["rows"]
Y0, YF = 50.0, 17.0 / 12.0


def _vaa_exact(vy0: float, vz0: float, ay: float, az: float) -> float:
    """The FanGraphs primer's equations, evaluated pitch by pitch with math.atan."""
    vy_f = -math.sqrt(vy0**2 - 2.0 * ay * (Y0 - YF))
    t = (vy_f - vy0) / ay
    vz_f = vz0 + az * t
    return -math.atan(vz_f / vy_f) * 180.0 / math.pi


@pytest.mark.parametrize("ref", ROWS, ids=lambda r: r["player"])
def test_vaa_matches_the_published_value(ref: dict[str, Any]) -> None:
    raw = pl.read_csv(HERE / "fixtures" / "statcast" / ref["fixture"], infer_schema_length=0)
    assert raw.height == ref["pitches"]
    got = sp.calculate(prepare_statcast_pitches(raw), [Metric.VAA], by="pitcher_id").df["vaa"][0]
    # Published to one decimal; Joe Ryan's -3.847 recomputes against -3.9, so allow 0.06.
    assert got == pytest.approx(ref["vaa"], abs=0.06)


@pytest.mark.parametrize("ref", ROWS, ids=lambda r: r["player"])
def test_library_vaa_equals_the_exact_equations(ref: dict[str, Any]) -> None:
    raw = pl.read_csv(HERE / "fixtures" / "statcast" / ref["fixture"], infer_schema_length=0)
    got = sp.calculate(prepare_statcast_pitches(raw), [Metric.VAA], by="pitcher_id").df["vaa"][0]
    angles = [
        _vaa_exact(*(float(r[c]) for c in ("vy0", "vz0", "ay", "az")))
        for r in raw.iter_rows(named=True)
    ]
    assert got == pytest.approx(sum(angles) / len(angles), abs=1e-3)
