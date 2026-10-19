"""Total Break is the mean per-pitch magnitude, not the magnitude of the mean break (ADR-0040)."""

from __future__ import annotations

import math

import polars as pl

import sabermetricspy as sp
from sabermetricspy.types import MetricSuite


def _statcast(pfx_x: list[float], pfx_z: list[float]) -> pl.DataFrame:
    n = len(pfx_x)
    return pl.DataFrame({"pitcher": [101] * n, "batter": [202] * n, "pfx_x": pfx_x, "pfx_z": pfx_z})


def test_opposite_horizontal_breaks_do_not_cancel() -> None:
    # +10 in and -10 in horizontal break, no vertical break: every pitch breaks 10 inches.
    df = _statcast([10 / 12, -10 / 12], [0.0, 0.0])
    row = sp.calculate_suite(
        df, [MetricSuite.PITCH_PHYSICS], by="pitcher_id", preset="statcast"
    ).df.row(0, named=True)
    assert math.isclose(row["hb"], 0.0, abs_tol=1e-9)
    assert math.isclose(row["total_break"], 10.0, rel_tol=1e-9)


def test_total_break_averages_each_pitch_magnitude() -> None:
    # 3-4-5 triangles scaled to inches: magnitudes 15 and 5 average to 10.
    df = _statcast([9 / 12, 3 / 12], [12 / 12, 4 / 12])
    row = sp.calculate_suite(
        df, [MetricSuite.PITCH_PHYSICS], by="pitcher_id", preset="statcast"
    ).df.row(0, named=True)
    assert math.isclose(row["total_break"], 10.0, rel_tol=1e-9)
