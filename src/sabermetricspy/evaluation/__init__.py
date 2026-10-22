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

import math
from collections.abc import Sequence
from typing import Any, Literal

import narwhals as nw
import numpy as np
import polars as pl
from pydantic import BaseModel, ConfigDict
from scipy.stats import norm

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


def _bin_index(p: np.ndarray, n_bins: int, closed: Literal["left", "right"]) -> np.ndarray:
    """Bin number of each forecast for `n_bins` equal-width bins on [0, 1].

    Right-closed bins use `searchsorted` on the float edges, which never places a decimal edge k/n in the wrong bin
    (the float edge is never below the decimal edge); `floor(p * n)` and `ceil(p * n) - 1` do mis-bin some decimal
    edges for large n (for example 29/50), so they are not used for the right-closed case.
    """
    if closed == "right":
        edges = np.linspace(0.0, 1.0, n_bins + 1)[1:-1]
        return np.searchsorted(edges, p, side="left")
    return np.minimum((p * n_bins).astype(int), n_bins - 1)


@profiled(category="evaluation")
def calibration_table(
    df: Any,
    forecast_col: str,
    outcome_col: str,
    *,
    n_bins: int = 10,
    weight_col: str | None = None,
    closed: Literal["left", "right"] = "right",
) -> CalibrationResults:
    """Equal-width calibration bins with the Murphy (1973) Brier decomposition.

    `closed="right"` (the default, as in scikit-learn's `calibration_curve` and Guo et al. 2017) makes bin k the
    interval `(k/n, (k+1)/n]` with 0.0 in the first bin; `closed="left"` makes it `[k/n, (k+1)/n)` with 1.0 in the last
    bin (the behaviour before ADR-0072). Only a forecast exactly on an inner edge changes bin. `count` is the number
    of rows; the means use the weights.
    """
    if n_bins < 1:
        raise ValueError("n_bins must be at least 1.")
    if closed not in ("left", "right"):
        raise ValueError("closed must be 'left' or 'right'.")
    p, y, w = _probabilities(df, forecast_col, outcome_col, weight_col)
    idx = _bin_index(p, n_bins, closed)
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


def _calibration_gaps(
    p: np.ndarray, y: np.ndarray, w: np.ndarray, n_bins: int, closed: Literal["left", "right"]
) -> tuple[np.ndarray, np.ndarray]:
    """Per occupied equal-width bin: its weight share and the absolute gap |observed rate - mean forecast|."""
    if n_bins < 1:
        raise ValueError("n_bins must be at least 1.")
    if closed not in ("left", "right"):
        raise ValueError("closed must be 'left' or 'right'.")
    if p.size == 0 or float(np.sum(w)) <= 0.0:
        raise ValueError("No rows with positive weight to score.")
    idx = _bin_index(p, n_bins, closed)
    wk = np.bincount(idx, weights=w, minlength=n_bins)
    occupied = wk > 0
    mean_forecast = np.bincount(idx, weights=w * p, minlength=n_bins)[occupied] / wk[occupied]
    observed = np.bincount(idx, weights=w * y, minlength=n_bins)[occupied] / wk[occupied]
    return wk[occupied] / float(np.sum(wk)), np.abs(observed - mean_forecast)


@profiled(category="evaluation")
def expected_calibration_error(
    df: Any,
    forecast_col: str,
    outcome_col: str,
    *,
    n_bins: int = 10,
    closed: Literal["left", "right"] = "right",
    weight_col: str | None = None,
) -> float:
    """Expected Calibration Error: the share-weighted mean of |observed rate - mean forecast| over equal-width bins.

    This is the event form of Naeini, Cooper and Hauskrecht (2015), `sum_i P(i) |o_i - e_i|`, with equal-width
    right-closed bins by default (the bin convention of Guo et al. 2017). It is not Guo's predicted-class form,
    which scores the confidence of the top class. Empty bins are skipped. Raises `ValueError` for invalid input.
    """
    p, y, w = _probabilities(df, forecast_col, outcome_col, weight_col)
    share, gap = _calibration_gaps(p, y, w, n_bins, closed)
    return float(np.sum(share * gap))


@profiled(category="evaluation")
def maximum_calibration_error(
    df: Any,
    forecast_col: str,
    outcome_col: str,
    *,
    n_bins: int = 10,
    closed: Literal["left", "right"] = "right",
    weight_col: str | None = None,
) -> float:
    """Maximum Calibration Error: the largest |observed rate - mean forecast| over occupied equal-width bins.

    Same binning as `expected_calibration_error`. Guo et al. (2017) note that it is sensitive to the binning scheme
    and a poor fit for small samples.
    """
    p, y, w = _probabilities(df, forecast_col, outcome_col, weight_col)
    _, gap = _calibration_gaps(p, y, w, n_bins, closed)
    return float(np.max(gap))


@profiled(category="evaluation")
def ranked_probability_score(
    df: Any,
    forecast_cols: Sequence[str],
    outcome_col: str,
    *,
    normalise: bool = True,
    weight_col: str | None = None,
) -> float:
    """Ranked probability score of forecasts over K ordered categories (Epstein 1969; Murphy 1971). Lower is better.

    `forecast_cols` are the K >= 2 category probabilities in category order (the order is the ranking); each row must
    sum to 1. `outcome_col` holds the 0-based position of the observed category within `forecast_cols`. The per-row
    score is the sum of squared differences between the forecast and observed cumulative distributions, divided by
    `K - 1` when `normalise` is true (so it lies in [0, 1] and equals the Brier score of the first category when
    K = 2); Epstein's positively oriented score is `1 - rps`. Raises `ValueError` for invalid input.
    """
    cols = list(forecast_cols)
    if len(cols) < 2:
        raise ValueError("A ranked probability score needs at least two forecast columns.")
    prob = np.column_stack([_column(df, c) for c in cols])
    pos_raw = _column(df, outcome_col)
    k = prob.shape[1]
    if np.any((prob < 0.0) | (prob > 1.0)):
        raise ValueError("Probability forecasts must lie in [0, 1].")
    if not np.allclose(prob.sum(axis=1), 1.0, rtol=0.0, atol=1e-8):
        raise ValueError("Each row of forecast probabilities must sum to 1.")
    if np.any(pos_raw != np.round(pos_raw)) or np.any((pos_raw < 0) | (pos_raw > k - 1)):
        raise ValueError(f"Outcomes must be integer positions between 0 and {k - 1}.")
    pos = pos_raw.astype(int)
    w = _weights(df, weight_col, len(pos))
    cum_forecast = np.cumsum(prob, axis=1)[:, :-1]
    cum_observed = (np.arange(k - 1)[None, :] >= pos[:, None]).astype(np.float64)
    per_row = np.sum((cum_forecast - cum_observed) ** 2, axis=1)
    if normalise:
        per_row = per_row / (k - 1)
    return _wmean(per_row, w)


class DieboldMarianoResult(BaseModel):
    """Diebold-Mariano test of equal expected loss for two forecasts."""

    model_config = ConfigDict(frozen=True)

    statistic: float
    pvalue: float
    mean_loss_differential: float
    n_obs: int
    horizon: int
    lags: int
    window: str


@profiled(category="evaluation")
def diebold_mariano_test(
    df: Any,
    actual_col: str,
    forecast_a_col: str,
    forecast_b_col: str,
    *,
    horizon: int = 1,
    power: float = 2.0,
    lags: int | None = None,
) -> DieboldMarianoResult:
    """Diebold-Mariano (1995) test that two forecasts have equal expected loss.

    The loss differential is `d_t = |e_a,t|**power - |e_b,t|**power` (squared error by default) with forecast errors
    `e = forecast - actual`. A positive statistic means forecast A has the larger loss. The statistic is
    `mean(d) / sqrt(lrv / T)` with a long-run variance built from `lags` autocovariances (default `horizon - 1`, as
    the paper's truncation for h-step forecasts) with Bartlett weights, which keeps the estimate non-negative; for
    `horizon = 1` this is the plain variance. The p-value is two-sided from the standard normal. Rows must be in time
    order. The Harvey-Leybourne-Newbold small-sample correction is not applied (ADR-0076). Raises `ValueError` for
    invalid input or a zero long-run variance.
    """
    if horizon < 1:
        raise ValueError("horizon must be at least 1.")
    if power <= 0:
        raise ValueError("power must be positive.")
    actual = _column(df, actual_col)
    err_a = _column(df, forecast_a_col) - actual
    err_b = _column(df, forecast_b_col) - actual
    t = int(actual.size)
    n_lags = horizon - 1 if lags is None else lags
    if n_lags < 0:
        raise ValueError("lags must not be negative.")
    if t < 2 or n_lags >= t:
        raise ValueError("Need more observations than lags (and at least 2).")
    d = np.abs(err_a) ** power - np.abs(err_b) ** power
    dbar = float(np.mean(d))
    centered = d - dbar
    lrv = float(np.dot(centered, centered) / t)
    for k in range(1, n_lags + 1):
        lrv += 2.0 * (1.0 - k / (n_lags + 1)) * float(np.dot(centered[k:], centered[: t - k]) / t)
    if lrv <= 0.0:
        raise ValueError(
            "The long-run variance of the loss differential is not positive; the statistic is undefined."
        )
    statistic = dbar / math.sqrt(lrv / t)
    return DieboldMarianoResult(
        statistic=statistic,
        pvalue=float(2.0 * norm.sf(abs(statistic))),
        mean_loss_differential=dbar,
        n_obs=t,
        horizon=horizon,
        lags=n_lags,
        window="bartlett",
    )


__all__ = [
    "LOG_LOSS_EPSILON",
    "CalibrationBin",
    "CalibrationResults",
    "DieboldMarianoResult",
    "bias",
    "brier_score",
    "brier_skill_score",
    "calibration_table",
    "diebold_mariano_test",
    "expected_calibration_error",
    "log_loss",
    "mae",
    "maximum_calibration_error",
    "mse",
    "ranked_probability_score",
    "rmse",
]
