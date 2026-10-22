"""Diebold-Mariano statistic: hand arithmetic and recorded statsmodels 0.15.0 output (tests/golden/diebold_mariano.yaml).

The 1995 paper prints no numeric example, so the rows are closed-form hand arithmetic or the recorded output of an
independent implementation (statsmodels `diebold_mariano_test` with `lags = horizon - 1`), which agrees with the
Bartlett-weight construction used here to about 1e-15. Rows with `harvey_adj: true` are not tested: the
Harvey-Leybourne-Newbold correction is not implemented (ADR-0076). The uniform-window rows are prototype values only.
"""

from __future__ import annotations

import math
from typing import Any

import numpy as np
import polars as pl
import pytest
from golden_loader import load_entries
from hypothesis import given
from hypothesis import strategies as st

import sabermetricspy.evaluation as ev

ENTRIES = [
    e
    for e in load_entries("diebold_mariano.yaml")
    if "published" in e
    and "statistic" in e["published"]
    and not e["inputs"].get("harvey_adj", False)
    and e["id"] != "dm_earlier_note_values"
]


def _frame(inputs: dict[str, Any]) -> pl.DataFrame:
    if (
        "loss_differential" in inputs
    ):  # actual = 0 so the errors are the forecasts; d = e_a^2 - e_b^2
        d = np.asarray(inputs["loss_differential"], dtype=float)
        return pl.DataFrame(
            {
                "y": np.zeros_like(d),
                "a": np.sqrt(np.maximum(d, 0.0)),
                "b": np.sqrt(np.maximum(-d, 0.0)),
            }
        )
    return pl.DataFrame({"y": np.zeros(len(inputs["e1"])), "a": inputs["e1"], "b": inputs["e2"]})


@pytest.mark.parametrize("entry", ENTRIES, ids=lambda e: e["id"])
def test_statistic_and_pvalue_match_the_fixture(entry: dict[str, Any]) -> None:
    inputs = entry["inputs"]
    res = ev.diebold_mariano_test(_frame(inputs), "y", "a", "b", horizon=inputs["horizon"])
    assert res.statistic == pytest.approx(
        entry["published"]["statistic"], abs=entry["tolerance"]["statistic"]
    )
    if "pvalue" in entry["published"]:
        assert res.pvalue == pytest.approx(
            entry["published"]["pvalue"], abs=entry["tolerance"]["pvalue"]
        )


def test_positive_statistic_means_forecast_a_is_worse() -> None:
    df = pl.DataFrame(
        {"y": [0.0] * 6, "a": [2.0, 1.0, 3.0, 2.0, 1.0, 2.0], "b": [1.0, 1.0, 1.0, 2.0, 1.0, 0.5]}
    )
    assert ev.diebold_mariano_test(df, "y", "a", "b").statistic > 0
    assert ev.diebold_mariano_test(df, "y", "b", "a").statistic < 0


def test_swapping_forecasts_flips_the_sign_only() -> None:
    df = pl.DataFrame(
        {
            "y": [0.0] * 8,
            "a": [1.0, 2.0, 1.0, 3.0, 2.0, 1.0, 2.0, 3.0],
            "b": [2.0, 1.0, 2.0, 1.0, 1.0, 2.0, 1.0, 1.0],
        }
    )
    ab = ev.diebold_mariano_test(df, "y", "a", "b", horizon=2)
    ba = ev.diebold_mariano_test(df, "y", "b", "a", horizon=2)
    assert ab.statistic == pytest.approx(-ba.statistic)
    assert ab.pvalue == pytest.approx(ba.pvalue)


def test_pvalue_is_two_sided_normal() -> None:
    df = pl.DataFrame({"y": [0.0] * 4, "a": [1.0, math.sqrt(2), math.sqrt(3), 2.0], "b": [0.0] * 4})
    res = ev.diebold_mariano_test(df, "y", "a", "b")
    assert res.statistic == pytest.approx(math.sqrt(20))
    assert res.pvalue == pytest.approx(math.erfc(res.statistic / math.sqrt(2)))


def test_invalid_input_raises() -> None:
    df = pl.DataFrame({"y": [0.0] * 4, "a": [1.0, 2.0, 3.0, 4.0], "b": [0.0] * 4})
    with pytest.raises(ValueError, match="horizon"):
        ev.diebold_mariano_test(df, "y", "a", "b", horizon=0)
    with pytest.raises(ValueError, match="power"):
        ev.diebold_mariano_test(df, "y", "a", "b", power=0.0)
    with pytest.raises(ValueError, match="observations"):
        ev.diebold_mariano_test(df, "y", "a", "b", horizon=5)
    with pytest.raises(ValueError, match="not positive"):
        ev.diebold_mariano_test(df.with_columns(b=pl.col("a")), "y", "a", "b")


@given(st.lists(st.floats(-5, 5, allow_nan=False), min_size=6, max_size=40, unique=True))
def test_scaling_the_errors_does_not_change_the_statistic(errors: list[float]) -> None:
    a = np.asarray(errors)
    b = np.roll(a, 1) * 0.5
    base = pl.DataFrame({"y": np.zeros(a.size), "a": a, "b": b})
    scaled = pl.DataFrame({"y": np.zeros(a.size), "a": 3.0 * a, "b": 3.0 * b})
    try:
        s1 = ev.diebold_mariano_test(base, "y", "a", "b").statistic
    except ValueError:
        return
    assert ev.diebold_mariano_test(scaled, "y", "a", "b").statistic == pytest.approx(
        s1, rel=1e-6, abs=1e-9
    )
