"""Model audit: each check compares a model with a published formula or an exact analytical result."""

from __future__ import annotations

import math

import polars as pl
import pytest

from sabermetricspy.expectancy import LinearWeightsEstimator
from sabermetricspy.models import Log5Model, MarkovChainModel, MonteCarloSimulator
from sabermetricspy.uncertainty import EmpiricalBayesShrinker


def test_log5_matches_the_published_arithmetic() -> None:
    """Wikipedia Log5 article: pA=0.6 vs pB=0.4 -> 0.36 / 0.52."""
    assert Log5Model.team_matchup_prob(0.6, 0.4) == pytest.approx(0.36 / 0.52, abs=1e-12)


def test_log5_equal_teams_are_even_and_swapping_complements() -> None:
    assert Log5Model.team_matchup_prob(0.55, 0.55) == pytest.approx(0.5)
    a, b = 0.62, 0.47
    assert Log5Model.team_matchup_prob(a, b) + Log5Model.team_matchup_prob(b, a) == pytest.approx(
        1.0
    )


def test_log5_batter_pitcher_matches_the_published_form() -> None:
    """pB,P = (pB*pP/pL) / (pB*pP/pL + (1-pB)(1-pP)/(1-pL))."""
    pb, pp, pl_ = 0.300, 0.230, 0.250
    published = (pb * pp / pl_) / (pb * pp / pl_ + (1 - pb) * (1 - pp) / (1 - pl_))
    assert Log5Model.batter_pitcher_matchup_rate(pb, pp, pl_) == pytest.approx(published, abs=1e-12)
    frame = pl.DataFrame({"batter_rate": [pb], "pitcher_rate": [pp]})
    got = Log5Model().predict_df(frame, league_rate=pl_)["matchup_prob"][0]
    assert got == pytest.approx(published, abs=1e-12)


def test_league_average_opponent_returns_the_batter_rate() -> None:
    assert Log5Model.batter_pitcher_matchup_rate(0.31, 0.25, 0.25) == pytest.approx(0.31)


def test_markov_chain_matches_the_negative_binomial_closed_form() -> None:
    """Only home runs and outs: runs per inning is the number of home runs before the third out, 3p/(1-p)."""
    p = 0.08
    res = MarkovChainModel().fit(p_1b=0, p_2b=0, p_3b=0, p_hr=p, p_bb=0, p_out=1 - p).results
    assert res.expected_runs_per_half_inning == pytest.approx(3 * p / (1 - p), abs=1e-12)
    assert res.expected_pa_per_half_inning == pytest.approx(3 / (1 - p), abs=1e-12)


def test_markov_chain_state_values_are_ordered() -> None:
    """More outs lower the expectancy and more runners raise it."""
    res = MarkovChainModel().fit(p_1b=0.15, p_2b=0.05, p_3b=0.005, p_hr=0.03, p_bb=0.08).results
    s = res.state_expected_runs
    assert s["0|---"] > s["1|---"] > s["2|---"] > 0
    assert s["0|123"] > s["0|1--"] > s["0|---"]


def test_monte_carlo_converges_to_the_markov_chain() -> None:
    probs = {"p_1b": 0.15, "p_2b": 0.045, "p_3b": 0.004, "p_hr": 0.03, "p_bb": 0.085}
    exact = MarkovChainModel().fit(**probs).results.expected_runs_per_9_innings
    sim = MonteCarloSimulator(n_simulations=4000, seed=7).simulate(**probs)
    standard_error = sim.std_runs_per_game / math.sqrt(sim.n_simulations)
    assert abs(sim.mean_runs_per_game - exact) < 4 * standard_error


def test_linear_weights_scale_makes_woba_equal_the_target_obp() -> None:
    """Tango's construction: weights are (RV_event - RV_out) times a scale that sets league wOBA to OBP."""
    events = ["out"] * 70 + ["walk"] * 8 + ["single"] * 15 + ["double"] * 5 + ["home_run"] * 2
    run_values = {"out": -0.27, "walk": 0.31, "single": 0.46, "double": 0.76, "home_run": 1.39}
    frame = pl.DataFrame({"play_outcome": events, "run_value": [run_values[e] for e in events]})
    res = LinearWeightsEstimator(target_lg_obp=0.320).fit(frame).results
    assert res.woba_weights["single"] == pytest.approx(
        (run_values["single"] - run_values["out"]) * res.woba_scale
    )
    woba = sum(res.woba_weights.get(e, 0.0) for e in events) / len(events)
    assert woba == pytest.approx(0.320, abs=1e-9)


def test_empirical_bayes_posterior_mean_is_the_beta_binomial_formula() -> None:
    frame = pl.DataFrame({"h": [30, 60, 90, 120], "ab": [100, 200, 300, 400]})
    shrinker = EmpiricalBayesShrinker(stabilization_trials=200.0).fit(frame)
    r = shrinker.results
    out = shrinker.transform(frame)
    for k, n, rate in zip(frame["h"], frame["ab"], out["eb_rate"], strict=True):
        assert rate == pytest.approx((k + r.alpha_0) / (n + r.alpha_0 + r.beta_0), abs=1e-12)
        weight = r.stabilization_trials / (n + r.stabilization_trials)
        assert rate == pytest.approx((1 - weight) * k / n + weight * r.prior_mean, abs=1e-12)


def test_extended_pythagorean_equals_the_league_free_form() -> None:
    """Cleary et al. equations 1.4 and 1.5: the league average cancels."""
    rs_h, ra_h, rs_a, ra_a, lg, g = 5.1, 4.3, 4.4, 4.9, 4.5, 1.87
    got = Log5Model.extended_pythagorean_home_win_prob(
        runs_scored_home=rs_h,
        runs_allowed_home=ra_h,
        runs_scored_away=rs_a,
        runs_allowed_away=ra_a,
        league_runs=lg,
        exponent=g,
    )
    a, b = (rs_h * ra_a) ** g, (ra_h * rs_a) ** g
    assert got == pytest.approx(a / (a + b), abs=1e-12)


def test_extended_pythagorean_reduces_to_pythagorean_against_a_league_average_opponent() -> None:
    lg, g = 4.5, 1.83
    got = Log5Model.extended_pythagorean_home_win_prob(
        runs_scored_home=5.0,
        runs_allowed_home=4.0,
        runs_scored_away=lg,
        runs_allowed_away=lg,
        league_runs=lg,
        exponent=g,
    )
    assert got == pytest.approx(5.0**g / (5.0**g + 4.0**g), abs=1e-12)


def test_extended_pythagorean_swapped_equal_teams_are_even() -> None:
    got = Log5Model.extended_pythagorean_home_win_prob(
        runs_scored_home=4.6,
        runs_allowed_home=4.6,
        runs_scored_away=4.6,
        runs_allowed_away=4.6,
        league_runs=4.5,
        exponent=1.83,
    )
    assert got == pytest.approx(0.5)
