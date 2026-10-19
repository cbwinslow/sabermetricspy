"""The Beta prior is fit by beta-binomial maximum likelihood, so it recovers a known prior without clamps."""

from __future__ import annotations

import numpy as np
import polars as pl
import pytest

import sabermetricspy as sb


def _simulate(strength: float, mean: float = 0.25, players: int = 4000) -> pl.DataFrame:
    rng = np.random.default_rng(7)
    p = rng.beta(mean * strength, (1 - mean) * strength, players)
    n = rng.integers(50, 600, players)
    return pl.DataFrame({"h": rng.binomial(n, p), "ab": n})


@pytest.mark.parametrize("strength", [10.0, 100.0, 1000.0])
def test_fit_recovers_the_true_prior_strength(strength: float) -> None:
    fitted = sb.EmpiricalBayesShrinker().fit(_simulate(strength)).results
    assert fitted.stabilization_trials == pytest.approx(strength, rel=0.25)
    assert fitted.prior_mean == pytest.approx(0.25, abs=0.01)


def test_explicit_stabilization_override_is_kept() -> None:
    fitted = sb.EmpiricalBayesShrinker(stabilization_trials=300.0).fit(_simulate(100.0)).results
    assert fitted.stabilization_trials == 300.0
