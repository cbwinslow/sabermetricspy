"""Analytical confidence intervals and seeded bootstrap uncertainty estimation."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any, Self

import narwhals as nw
import numpy as np
import polars as pl
from narwhals.typing import IntoFrame
from pydantic import BaseModel, ConfigDict

from sabermetricspy.schema import normalize_columns, to_polars_df
from sabermetricspy.telemetry import profiled


class UncertaintyInterval(BaseModel):
    """Frozen statistical confidence/credible interval."""

    model_config = ConfigDict(frozen=True)

    estimate: float
    std_err: float
    ci_lower: float
    ci_upper: float
    confidence_level: float = 0.95
    method: str = "analytical"


class EmpiricalBayesResults(BaseModel):
    """Frozen prior parameters and diagnostics from Beta-Binomial Empirical Bayes shrinkage."""

    model_config = ConfigDict(frozen=True)

    success_col: str
    trials_col: str
    alpha_0: float
    beta_0: float
    prior_mean: float
    stabilization_trials: float
    n_players_fitted: int


class EmpiricalBayesShrinker:
    """Beta-Binomial Empirical Bayes shrinkage estimator for baseball rate statistics (Efron & Morris 1975; Tango 2007).

    Learns the population Beta prior `(alpha_0, beta_0)` from observed player successes `k_i` and
    trials `n_i` via method-of-moments (with optional explicit `stabilization_trials` override),
    then shrinks each player's noisy observed rate `k_i / n_i` toward the prior mean:
        `eb_rate = (k_i + alpha_0) / (n_i + alpha_0 + beta_0)`
    Also outputs posterior standard deviation (`eb_std`) and exact Beta credible intervals
    (`eb_ci_lower`, `eb_ci_upper`).
    """

    def __init__(
        self,
        *,
        success_col: str = "h",
        trials_col: str = "ab",
        stabilization_trials: float | None = None,
        min_trials_for_fit: int = 20,
        confidence_level: float = 0.95,
        output_prefix: str = "eb",
    ) -> None:
        self.success_col = success_col
        self.trials_col = trials_col
        self.stabilization_trials = stabilization_trials
        self.min_trials_for_fit = min_trials_for_fit
        self.confidence_level = confidence_level
        self.output_prefix = output_prefix
        self._results: EmpiricalBayesResults | None = None

    @property
    def results(self) -> EmpiricalBayesResults:
        if self._results is None:
            raise RuntimeError("EmpiricalBayesShrinker is not fitted yet. Call .fit(df) first.")
        return self._results

    @profiled(category="uncertainty")
    def fit(self, df: IntoFrame) -> Self:
        """Estimate Beta prior parameters `(alpha_0, beta_0)` from observed player counts."""
        nw_df = normalize_columns(nw.from_native(df))
        pl_df = to_polars_df(nw.to_native(nw_df))

        valid = pl_df.filter(pl.col(self.trials_col) >= self.min_trials_for_fit)
        if valid.is_empty():
            valid = pl_df.filter(pl.col(self.trials_col) > 0)
        if valid.is_empty():
            raise ValueError(f"No positive trials found in column {self.trials_col!r}.")

        k_arr = valid[self.success_col].to_numpy().astype(np.float64)
        n_arr = valid[self.trials_col].to_numpy().astype(np.float64)
        rates = k_arr / n_arr

        # Exposure-weighted population mean
        mu = float(np.sum(k_arr) / np.sum(n_arr))
        mu = min(max(mu, 1e-4), 1.0 - 1e-4)

        if self.stabilization_trials is not None and self.stabilization_trials > 0:
            m_val = float(self.stabilization_trials)
        else:
            # Method-of-moments Beta-Binomial overdispersion estimate
            raw_var = float(np.var(rates, ddof=1)) if len(rates) > 1 else 0.001
            avg_inv_n = float(np.mean(1.0 / n_arr))
            within_var = mu * (1.0 - mu) * avg_inv_n
            true_var = max(raw_var - within_var, 1e-5)
            m_val = max((mu * (1.0 - mu) / true_var) - 1.0, 25.0)
            m_val = min(m_val, 2000.0)

        alpha_0 = mu * m_val
        beta_0 = (1.0 - mu) * m_val
        self._results = EmpiricalBayesResults(
            success_col=self.success_col,
            trials_col=self.trials_col,
            alpha_0=alpha_0,
            beta_0=beta_0,
            prior_mean=mu,
            stabilization_trials=m_val,
            n_players_fitted=len(valid),
        )
        return self

    @profiled(category="uncertainty")
    def transform(self, df: IntoFrame) -> Any:
        """Attach Empirical Bayes posterior mean, shrinkage factor, SD, and credible intervals."""
        from scipy.stats import beta as beta_dist

        res = self.results
        nw_df = normalize_columns(nw.from_native(df))
        pl_df = to_polars_df(nw.to_native(nw_df))

        k = pl_df[self.success_col].to_numpy().astype(np.float64)
        n = pl_df[self.trials_col].to_numpy().astype(np.float64)

        a_post = res.alpha_0 + k
        b_post = res.beta_0 + np.maximum(0.0, n - k)
        tot_post = a_post + b_post

        raw_rate = np.where(n > 0, k / np.where(n > 0, n, 1.0), np.nan)
        eb_rate = a_post / tot_post
        shrinkage_w = res.stabilization_trials / (n + res.stabilization_trials)
        eb_std = np.sqrt((a_post * b_post) / ((tot_post * tot_post) * (tot_post + 1.0)))

        tail = (1.0 - self.confidence_level) / 2.0
        ci_low = beta_dist.ppf(tail, a_post, b_post)
        ci_high = beta_dist.ppf(1.0 - tail, a_post, b_post)

        pfx = self.output_prefix
        out_pl = pl_df.with_columns(
            pl.Series(f"{pfx}_raw_rate", raw_rate),
            pl.Series(f"{pfx}_rate", eb_rate),
            pl.Series(f"{pfx}_shrinkage", shrinkage_w),
            pl.Series(f"{pfx}_std", eb_std),
            pl.Series(f"{pfx}_ci_lower", ci_low),
            pl.Series(f"{pfx}_ci_upper", ci_high),
        )
        if isinstance(df, pl.DataFrame):
            return out_pl
        arrow_tbl = out_pl.to_arrow()
        if type(df).__module__.startswith("pandas"):
            return arrow_tbl.to_pandas()
        return arrow_tbl


@profiled(category="uncertainty")
def binomial_rate_interval(
    successes: int | float,
    trials: int | float,
    *,
    confidence_level: float = 0.95,
) -> UncertaintyInterval:
    """Compute Wilson score analytical confidence interval for a baseball rate stat (AVG, OBP, K%, BB%)."""
    from scipy.stats import norm

    if trials <= 0:
        return UncertaintyInterval(
            estimate=float("nan"),
            std_err=float("nan"),
            ci_lower=float("nan"),
            ci_upper=float("nan"),
            confidence_level=confidence_level,
            method="wilson_binomial",
        )
    p = float(successes) / float(trials)
    n = float(trials)
    z = float(norm.ppf(1.0 - (1.0 - confidence_level) / 2.0))
    se = float(np.sqrt(p * (1.0 - p) / n))

    denom = 1.0 + (z * z) / n
    center = (p + (z * z) / (2.0 * n)) / denom
    half_width = (z * np.sqrt((p * (1.0 - p) / n) + ((z * z) / (4.0 * n * n)))) / denom

    return UncertaintyInterval(
        estimate=p,
        std_err=se,
        ci_lower=max(0.0, float(center - half_width)),
        ci_upper=min(1.0, float(center + half_width)),
        confidence_level=confidence_level,
        method="wilson_binomial",
    )


@profiled(category="uncertainty")
def bootstrap_interval(
    values: Any,
    statistic_fn: Callable[[np.ndarray[Any, Any]], float] = np.mean,
    *,
    n_resamples: int = 1000,
    confidence_level: float = 0.95,
    seed: int = 42,
) -> UncertaintyInterval:
    """Compute a reproducible seeded bootstrap confidence interval for any metric or estimator."""
    arr = np.asarray(values, dtype=np.float64)
    if arr.size == 0:
        return UncertaintyInterval(
            estimate=float("nan"),
            std_err=float("nan"),
            ci_lower=float("nan"),
            ci_upper=float("nan"),
            confidence_level=confidence_level,
            method="seeded_bootstrap",
        )
    rng = np.random.default_rng(seed)
    n = arr.shape[0]
    point_est = float(statistic_fn(arr))
    boot_stats = np.empty(n_resamples, dtype=np.float64)
    for i in range(n_resamples):
        idx = rng.integers(0, n, size=n)
        boot_stats[i] = statistic_fn(arr[idx])

    alpha = 1.0 - confidence_level
    lower = float(np.percentile(boot_stats, 100.0 * (alpha / 2.0)))
    upper = float(np.percentile(boot_stats, 100.0 * (1.0 - alpha / 2.0)))
    se = float(np.std(boot_stats, ddof=1))
    return UncertaintyInterval(
        estimate=point_est,
        std_err=se,
        ci_lower=lower,
        ci_upper=upper,
        confidence_level=confidence_level,
        method="seeded_bootstrap",
    )
