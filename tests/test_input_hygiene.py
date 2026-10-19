"""Bad inputs produce null or a loud error, never a plausible wrong number (ADR-0046)."""

from __future__ import annotations

import narwhals as nw
import polars as pl
import pytest

import sabermetricspy as sp
from sabermetricspy.presets import prepare_statcast_pitches
from sabermetricspy.schema import ip_expr_to_outs
from sabermetricspy.types import Metric


def _outs(ip: float) -> int | None:
    frame = nw.from_native(pl.DataFrame({"ip": [ip]})).select(ip_expr_to_outs("ip").alias("outs"))
    return frame.to_native()["outs"][0]


@pytest.mark.parametrize(
    ("ip", "outs"),
    [(6.0, 18), (6.1, 19), (6.2, 20), (6.333, 19), (6.667, 20), (0.1, 1), (0.2, 2)],
)
def test_valid_innings_notation_converts_to_outs(ip: float, outs: int) -> None:
    assert _outs(ip) == outs


@pytest.mark.parametrize("ip", [6.5, 6.15, 6.3, 6.9])
def test_invalid_innings_notation_is_null_not_a_wrong_number(ip: float) -> None:
    assert _outs(ip) is None


def test_zero_denominator_is_null_not_nan() -> None:
    df = pl.DataFrame({"outs": [0, 27], "er": [0, 3], "bb": [0, 1], "h": [0, 4]})
    res = sp.calculate(df, [Metric.ERA, Metric.WHIP])
    assert res.df["era"].to_list() == [None, 3.0]
    assert res.df["whip"][0] is None


def test_sacrifice_double_plays_count_as_plate_appearances_without_at_bats() -> None:
    raw = pl.DataFrame(
        {
            "player_name": ["x", "x", "x"],
            "description": ["hit_into_play"] * 3,
            "events": ["sac_fly_double_play", "sac_bunt_double_play", "single"],
            "zone": [5, 5, 5],
            "bb_type": ["fly_ball", "ground_ball", "line_drive"],
            "launch_speed": [80.0, 40.0, 95.0],
            "launch_angle": [30.0, -20.0, 12.0],
        }
    )
    row = prepare_statcast_pitches(raw).select("pa", "ab", "sf", "sh").sum().row(0, named=True)
    assert row == {"pa": 3, "ab": 1, "sf": 1, "sh": 1}
