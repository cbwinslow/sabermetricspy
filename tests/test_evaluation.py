"""Forecast-evaluation scores against hand-computed values (openspec: forecast-evaluation)."""

from __future__ import annotations

import math

import polars as pl
import pytest

from sabermetricspy import evaluation as ev

POINT = pl.DataFrame({"f": [2.0, 4.0, 6.0], "a": [1.0, 4.0, 9.0], "w": [1.0, 2.0, 1.0]})
PROB = pl.DataFrame({"p": [0.9, 0.2, 0.6], "y": [1, 0, 0]})


def test_point_errors_unweighted() -> None:
    assert ev.mse(POINT, "f", "a") == pytest.approx(10 / 3)
    assert ev.rmse(POINT, "f", "a") == pytest.approx(math.sqrt(10 / 3))
    assert ev.mae(POINT, "f", "a") == pytest.approx(4 / 3)
    assert ev.bias(POINT, "f", "a") == pytest.approx(-2 / 3)


def test_point_errors_weighted() -> None:
    assert ev.mse(POINT, "f", "a", weight_col="w") == pytest.approx(2.5)
    assert ev.rmse(POINT, "f", "a", weight_col="w") == pytest.approx(math.sqrt(2.5))
    assert ev.mae(POINT, "f", "a", weight_col="w") == pytest.approx(1.0)
    assert ev.bias(POINT, "f", "a", weight_col="w") == pytest.approx(-0.5)


def test_brier_score_hand_computed() -> None:
    assert ev.brier_score(PROB, "p", "y") == pytest.approx((0.01 + 0.04 + 0.36) / 3)


def test_log_loss_hand_computed() -> None:
    expected = -(math.log(0.9) + math.log(0.8) + math.log(0.4)) / 3
    assert ev.log_loss(PROB, "p", "y") == pytest.approx(expected)


def test_log_loss_is_finite_for_a_certain_wrong_forecast() -> None:
    df = pl.DataFrame({"p": [1.0], "y": [0]})
    assert math.isfinite(ev.log_loss(df, "p", "y"))


def test_skill_of_the_base_rate_is_zero() -> None:
    base = 1 / 3
    df = pl.DataFrame({"p": [base] * 3, "y": [1, 0, 0]})
    assert ev.brier_skill_score(df, "p", "y") == pytest.approx(0.0)


def test_skill_against_an_explicit_reference_forecast() -> None:
    df = PROB.with_columns(pl.lit(0.5).alias("ref"))
    ref_bs = 0.25
    bs = (0.01 + 0.04 + 0.36) / 3
    assert ev.brier_skill_score(df, "p", "y", reference_col="ref") == pytest.approx(1 - bs / ref_bs)


@pytest.mark.parametrize(
    "df",
    [
        pl.DataFrame({"p": [1.2], "y": [1]}),
        pl.DataFrame({"p": [-0.1], "y": [0]}),
        pl.DataFrame({"p": [0.5], "y": [2]}),
    ],
)
def test_invalid_probability_inputs_raise(df: pl.DataFrame) -> None:
    with pytest.raises(ValueError):
        ev.brier_score(df, "p", "y")


def test_non_finite_values_raise() -> None:
    with pytest.raises(ValueError):
        ev.rmse(pl.DataFrame({"f": [1.0, float("nan")], "a": [1.0, 2.0]}), "f", "a")


def test_murphy_decomposition_is_exact_for_discrete_forecasts() -> None:
    # 0.3 forecast hits 2 of 10, 0.7 forecast hits 8 of 10: reliability .01, resolution .09, uncertainty .25.
    df = pl.DataFrame({"p": [0.3] * 10 + [0.7] * 10, "y": [1] * 2 + [0] * 8 + [1] * 8 + [0] * 2})
    result = ev.calibration_table(df, "p", "y")
    assert result.brier_score == pytest.approx(0.17)
    assert result.reliability == pytest.approx(0.01)
    assert result.resolution == pytest.approx(0.09)
    assert result.uncertainty == pytest.approx(0.25)
    assert result.reliability - result.resolution + result.uncertainty == pytest.approx(
        result.brier_score
    )
    assert result.within_bin_remainder == pytest.approx(0.0, abs=1e-12)
    assert [b.count for b in result.bins] == [10, 10]
    assert [b.observed_rate for b in result.bins] == pytest.approx([0.2, 0.8])
    assert [b.mean_forecast for b in result.bins] == pytest.approx([0.3, 0.7])


def test_calibration_reports_remainder_when_forecasts_vary_within_a_bin() -> None:
    df = pl.DataFrame({"p": [0.31, 0.39, 0.7, 0.7], "y": [0, 1, 1, 1]})
    result = ev.calibration_table(df, "p", "y")
    assert result.within_bin_remainder == pytest.approx(
        result.brier_score - (result.reliability - result.resolution + result.uncertainty)
    )
    # BS = .16205; REL .05625 - RES .0625 + UNC .1875 = .18125 (hand-computed), so the remainder is -.0192.
    assert result.within_bin_remainder == pytest.approx(-0.0192)


def test_probability_of_one_lands_in_the_last_bin() -> None:
    df = pl.DataFrame({"p": [1.0, 1.0], "y": [1, 0]})
    assert ev.calibration_table(df, "p", "y").bins[-1].count == 2


def test_calibration_to_polars() -> None:
    df = pl.DataFrame({"p": [0.3, 0.7], "y": [0, 1]})
    out = ev.calibration_table(df, "p", "y").to_polars()
    assert out.columns == ["bin_lower", "bin_upper", "count", "mean_forecast", "observed_rate"]
    assert out.height == 2
