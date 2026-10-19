"""Forecast evaluation: point-error scores, probability scores and calibration.

Definitions: mean squared / absolute error and bias are the textbook forms (forecast minus actual). The binary Brier
score is the mean of (forecast - outcome)^2 (Brier, G. W. (1950), Monthly Weather Review 78(1), 1-3, reduced to one
event). The skill score is 1 - BS / BS_reference. The calibration table uses the Murphy (1973) decomposition
(J. Applied Meteorology 12(4), 595-600): BS = reliability - resolution + uncertainty, exact when forecasts are constant
within each bin; the within-bin remainder is reported rather than hidden.

Every function takes a dataframe (any narwhals-supported backend) and column names, with an optional weight column such
as plate appearances or innings.
"""

from __future__ import annotations

from typing import Any

import narwhals as nw
import numpy as np
import polars as pl
from pydantic import BaseModel, ConfigDict

from sabermetricspy.telemetry import profiled

# Probabilities are clipped to [eps, 1 - eps] inside log loss so a certain wrong forecast is finite.
LOG_LOSS_EPSILON = 1e-15


class CalibrationBin(BaseModel):
    """One occupied forecast bin of a calibration table."""

    model_config = ConfigDict(frozen=True)

    bin_lower: float
    bin_upper: float
    count: int
    mean_forecast: float
    observed_rate: float


class CalibrationResults(BaseModel):
    """Calibration bins and the Murphy (1973) decomposition of the Brier score."""

    model_config = ConfigDict(frozen=True)

    bins: tuple[CalibrationBin, ...]
    brier_score: float
    reliability: float
    resolution: float
    uncertainty: float
    within_bin_remainder: float

    def to_polars(self) -> pl.DataFrame:
        """Return the occupied bins as a Polars frame."""
        return pl.DataFrame(
            {
                "bin_lower": [b.bin_lower for b in self.bins],
                "bin_upper": [b.bin_upper for b in self.bins],
                "count": [b.count for b in self.bins],
                "mean_forecast": [b.mean_forecast for b in self.bins],
                "observed_rate": [b.observed_rate for b in self.bins],
            },
            schema={
                "bin_lower": pl.Float64,
                "bin_upper": pl.Float64,
                "count": pl.Int64,
                "mean_forecast": pl.Float64,
                "observed_rate": pl.Float64,
            },
        )


def _column(df: Any, name: str) -> np.ndarray:
    values = nw.from_native(df, eager_only=True)[name].cast(nw.Float64).to_numpy()
    arr = np.asarray(values, dtype=float)
    if not np.all(np.isfinite(arr)):
        raise ValueError(f"Column '{name}' contains null or non-finite values.")
    return arr


def _weights(df: Any, weight_col: str | None, n: int) -> np.ndarray:
    if weight_col is None:
        return np.ones(n)
    w = _column(df, weight_col)
    if np.any(w < 0) or w.sum() <= 0:
        raise ValueError("Weights must be non-negative with a positive sum.")
    return w


def _pair(
    df: Any, forecast_col: str, actual_col: str, weight_col: str | None
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    f, a = _column(df, forecast_col), _column(df, actual_col)
    return f, a, _weights(df, weight_col, len(f))


def _probabilities(
    df: Any, forecast_col: str, outcome_col: str, weight_col: str | None
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    p, y, w = _pair(df, forecast_col, outcome_col, weight_col)
    if np.any((p < 0) | (p > 1)):
        raise ValueError("Probability forecasts must lie in [0, 1].")
    if not np.all((y == 0) | (y == 1)):
        raise ValueError("Outcomes must be 0 or 1.")
    return p, y, w


def _wmean(x: np.ndarray, w: np.ndarray) -> float:
    return float(np.sum(w * x) / np.sum(w))


@profiled(category="evaluation")
def mse(df: Any, forecast_col: str, actual_col: str, *, weight_col: str | None = None) -> float:
    """Mean squared error of forecast against actual."""
    f, a, w = _pair(df, forecast_col, actual_col, weight_col)
    return _wmean((f - a) ** 2, w)


@profiled(category="evaluation")
def rmse(df: Any, forecast_col: str, actual_col: str, *, weight_col: str | None = None) -> float:
    """Root mean squared error."""
    return float(np.sqrt(mse(df, forecast_col, actual_col, weight_col=weight_col)))


@profiled(category="evaluation")
def mae(df: Any, forecast_col: str, actual_col: str, *, weight_col: str | None = None) -> float:
    """Mean absolute error."""
    f, a, w = _pair(df, forecast_col, actual_col, weight_col)
    return _wmean(np.abs(f - a), w)


@profiled(category="evaluation")
def bias(df: Any, forecast_col: str, actual_col: str, *, weight_col: str | None = None) -> float:
    """Mean of forecast minus actual (positive means the forecast runs high)."""
    f, a, w = _pair(df, forecast_col, actual_col, weight_col)
    return _wmean(f - a, w)


@profiled(category="evaluation")
def brier_score(
    df: Any, forecast_col: str, outcome_col: str, *, weight_col: str | None = None
) -> float:
    """Binary Brier score: mean of (forecast probability - outcome)^2."""
    p, y, w = _probabilities(df, forecast_col, outcome_col, weight_col)
    return _wmean((p - y) ** 2, w)


@profiled(category="evaluation")
def brier_skill_score(
    df: Any,
    forecast_col: str,
    outcome_col: str,
    *,
    reference_col: str | None = None,
    weight_col: str | None = None,
) -> float:
    """1 - BS / BS_reference; the reference defaults to always forecasting the observed base rate."""
    p, y, w = _probabilities(df, forecast_col, outcome_col, weight_col)
    bs = _wmean((p - y) ** 2, w)
    if reference_col is None:
        ref = np.full_like(p, _wmean(y, w))
    else:
        ref = _column(df, reference_col)
        if np.any((ref < 0) | (ref > 1)):
            raise ValueError("Reference probabilities must lie in [0, 1].")
    ref_bs = _wmean((ref - y) ** 2, w)
    if ref_bs == 0.0:
        raise ValueError("The reference forecast has zero Brier score; skill is undefined.")
    return 1.0 - bs / ref_bs


@profiled(category="evaluation")
def log_loss(
    df: Any, forecast_col: str, outcome_col: str, *, weight_col: str | None = None
) -> float:
    """Binary log loss with probabilities clipped to [LOG_LOSS_EPSILON, 1 - LOG_LOSS_EPSILON]."""
    p, y, w = _probabilities(df, forecast_col, outcome_col, weight_col)
    q = np.clip(p, LOG_LOSS_EPSILON, 1.0 - LOG_LOSS_EPSILON)
    return _wmean(-(y * np.log(q) + (1.0 - y) * np.log(1.0 - q)), w)


@profiled(category="evaluation")
def calibration_table(
    df: Any,
    forecast_col: str,
    outcome_col: str,
    *,
    n_bins: int = 10,
    weight_col: str | None = None,
) -> CalibrationResults:
    """Equal-width calibration bins with the Murphy (1973) Brier decomposition.

    A forecast of exactly 1.0 falls in the last bin. `count` is the number of rows; the means use the weights.
    """
    if n_bins < 1:
        raise ValueError("n_bins must be at least 1.")
    p, y, w = _probabilities(df, forecast_col, outcome_col, weight_col)
    idx = np.minimum((p * n_bins).astype(int), n_bins - 1)
    total = float(np.sum(w))
    base_rate = _wmean(y, w)
    reliability = resolution = 0.0
    bins: list[CalibrationBin] = []
    for k in range(n_bins):
        mask = idx == k
        if not mask.any():
            continue
        wk = w[mask]
        share = float(np.sum(wk)) / total
        mean_f = _wmean(p[mask], wk)
        obs = _wmean(y[mask], wk)
        reliability += share * (mean_f - obs) ** 2
        resolution += share * (obs - base_rate) ** 2
        bins.append(
            CalibrationBin(
                bin_lower=k / n_bins,
                bin_upper=(k + 1) / n_bins,
                count=int(mask.sum()),
                mean_forecast=mean_f,
                observed_rate=obs,
            )
        )
    uncertainty = base_rate * (1.0 - base_rate)
    bs = _wmean((p - y) ** 2, w)
    return CalibrationResults(
        bins=tuple(bins),
        brier_score=bs,
        reliability=reliability,
        resolution=resolution,
        uncertainty=uncertainty,
        within_bin_remainder=bs - (reliability - resolution + uncertainty),
    )


__all__ = [
    "LOG_LOSS_EPSILON",
    "CalibrationBin",
    "CalibrationResults",
    "bias",
    "brier_score",
    "brier_skill_score",
    "calibration_table",
    "log_loss",
    "mae",
    "mse",
    "rmse",
]
