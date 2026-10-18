"""Speed Score follows Bill James's four-factor definition (SB%, attempt rate, triples, runs scored), each limited to 0-10."""

from __future__ import annotations

import math

import polars as pl
import pytest

import sabermetricspy as sp
from sabermetricspy import Metric
from sabermetricspy.registry import REGISTRY

# 1B = 150 - 25 - 5 - 20 = 100
LINE = dict(sb=10, cs=2, h=150, b2=25, b3=5, hr=20, bb=60, ab=500, r=90, hbp=4, so=100)

F1 = ((10 + 3) / (10 + 2 + 7) - 0.4) * 20  # stolen-base percentage
F2 = math.sqrt((10 + 2) / (100 + 60 + 4)) / 0.07  # attempt rate: SB+CS over 1B + BB + HBP
F3 = (5 / (500 - 20 - 100)) / 0.0016  # triples over AB - HR - SO
F4 = 25 * ((90 - 20) / (150 + 60 + 4 - 20) - 0.1)  # runs scored
EXPECTED = (F1 + F2 + F3 + F4) / 4


def _spd(**overrides: float) -> float | None:
    data = {**LINE, **overrides}
    frame = pl.DataFrame({"player_id": ["p"], **{k: [v] for k, v in data.items()}})
    return sp.calculate(frame, [Metric.SPEED_SCORE]).df["speed_score"][0]


def test_hand_computed_four_factor_example() -> None:
    assert all(0 < f < 10 for f in (F1, F2, F3, F4))
    assert round(EXPECTED, 4) == 6.0732
    got = _spd()
    assert got is not None and math.isclose(got, EXPECTED, rel_tol=1e-9)


def test_each_factor_is_limited_to_zero_to_ten_before_averaging() -> None:
    # No steals and ten caught: F1 would be negative -> 0; no triples and no runs scored above HR -> low factors.
    got = _spd(sb=0, cs=10)
    f1_raw = ((0 + 3) / (0 + 10 + 7) - 0.4) * 20
    assert f1_raw < 0
    f2 = min(10.0, math.sqrt(10 / (100 + 60 + 4)) / 0.07)
    assert got is not None and math.isclose(got, (0.0 + f2 + F3 + F4) / 4, rel_tol=1e-9)
    # Very high triples rate: F3 would exceed 10 -> 10.
    got_high = _spd(b3=40)
    f3_raw = (40 / (500 - 20 - 100)) / 0.0016
    assert f3_raw > 10
    f2_high = (
        math.sqrt((10 + 2) / ((150 - 25 - 40 - 20) + 60 + 4)) / 0.07
    )  # more triples -> fewer singles
    assert got_high is not None and math.isclose(
        got_high, (F1 + f2_high + 10.0 + F4) / 4, rel_tol=1e-9
    )


def test_missing_strikeout_column_is_reported() -> None:
    frame = pl.DataFrame({"player_id": ["p"], **{k: [v] for k, v in LINE.items() if k != "so"}})
    with pytest.raises(ValueError, match="so"):
        sp.calculate(frame, [Metric.SPEED_SCORE])


def test_zero_denominators_give_null() -> None:
    zero = {k: 0 for k in LINE}
    frame = pl.DataFrame({"player_id": ["p"], **{k: [v] for k, v in zero.items()}})
    got = sp.calculate(frame, [Metric.SPEED_SCORE]).df["speed_score"][0]
    assert got is None or math.isnan(got)


def test_registry_formula_describes_four_factors() -> None:
    spec = REGISTRY.spec(Metric.SPEED_SCORE)
    assert "f_4" in spec.formula_latex and "f_5" not in spec.formula_latex
    assert "so" in spec.required_columns
