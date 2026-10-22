"""Model audit: each check compares a model with a published formula or an exact analytical result."""

from __future__ import annotations

import polars as pl
import pytest

from sabermetricspy.expectancy import LinearWeightsEstimator
from sabermetricspy.models import Log5Model
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


def _history(exposure: str, rows: list[tuple[int, float]]) -> pl.DataFrame:
    return pl.DataFrame(
        {
            "player_id": ["p"] * len(rows),
            "season": [s for s, _ in rows],
            exposure: [e for _, e in rows],
            "so": [e * 0.2 for _, e in rows],
        }
    )


def test_marcel_hitter_playing_time_reproduces_tangos_beltran_example() -> None:
    """Tango's post #25: 602 PA last year and 722 the year before project to 602*.5 + 722*.1 + 200 = 573.2."""
    from sabermetricspy.models import MarcelProjector

    hist = _history("pa", [(2003, 602.0), (2002, 722.0), (2001, 650.0)])
    out = MarcelProjector(target_season=2004, rate_cols=("so",)).fit(hist).predict()
    assert out["proj_pa"][0] == pytest.approx(602 * 0.5 + 722 * 0.1 + 200, abs=1e-9)


def test_marcel_hitter_rate_reproduces_tangos_beltran_example() -> None:
    """Tango's post #25: weighted HR 318 over 7,938 PA, plus 1,200 PA of league average, gives .0386 HR/PA."""
    from sabermetricspy.models import MarcelProjector

    beltran = [(2001, 680, 24, 0.0300), (2002, 722, 29, 0.0279), (2003, 602, 26, 0.0285)]
    filler_pa = 1_000_000.0
    rows = []
    for season, pa, hr, lg_rate in beltran:
        rows.append(("beltran", season, float(pa), float(hr)))
        # A large filler player sets each season's league rate (Beltran included) to Tango's figure.
        rows.append(("league", season, filler_pa, lg_rate * (filler_pa + pa) - hr))
    hist = pl.DataFrame(rows, schema=["player_id", "season", "pa", "hr"], orient="row")

    out = MarcelProjector(target_season=2004, rate_cols=("hr",)).fit(hist).predict()
    row = out.filter(pl.col("player_id") == "beltran").row(0, named=True)

    league_hr = sum(w * pa * lg for w, (_, pa, _, lg) in zip((3, 4, 5), beltran, strict=True))
    weighted_pa = 3 * 680 + 4 * 722 + 5 * 602
    expected_rate = (318 + league_hr * 1200 / weighted_pa) / (weighted_pa + 1200)
    assert weighted_pa == 7938
    assert row["proj_hr_rate"] == pytest.approx(expected_rate, rel=1e-4)
    assert row["proj_hr_rate"] == pytest.approx(0.0386, abs=5e-5)
    assert row["proj_hr"] == pytest.approx(22.1, abs=0.1)


def test_marcel_pitcher_configuration_uses_tangos_weights_and_innings_base() -> None:
    """Tango's pitcher post: weights 3/2/1 and the 200 replaced by 25 (relievers) or 60 (starters)."""
    from sabermetricspy.models import MarcelProjector

    hist = _history("ip", [(2003, 180.0), (2002, 200.0), (2001, 150.0)])
    out = (
        MarcelProjector(
            target_season=2004,
            season_weights=(3.0, 2.0, 1.0),
            exposure_col="ip",
            rate_cols=("so",),
            playing_time_base=60.0,
        )
        .fit(hist)
        .predict()
    )
    assert out["proj_ip"][0] == pytest.approx(180 * 0.5 + 200 * 0.1 + 60, abs=1e-9)


def test_marcel_playing_time_base_can_come_from_a_column() -> None:
    from sabermetricspy.models import MarcelProjector

    hist = _history("ip", [(2003, 80.0), (2002, 70.0), (2001, 60.0)]).with_columns(
        base=pl.lit(25.0)
    )
    out = (
        MarcelProjector(
            target_season=2004, exposure_col="ip", rate_cols=("so",), playing_time_base="base"
        )
        .fit(hist)
        .predict()
    )
    assert out["proj_ip"][0] == pytest.approx(80 * 0.5 + 70 * 0.1 + 25, abs=1e-9)


# --- Published Log5 and empirical Bayes values (release 1.1.0) ------------------------------------------------------


def test_log5_home_advantage_follows_tangos_multiplicative_form() -> None:
    """Tango wiki, Log5: with HA the even-matchup home win probability, equal teams return exactly HA."""
    assert Log5Model.team_matchup_prob(0.5, 0.5, home_advantage=0.54) == pytest.approx(0.54)
    assert Log5Model.team_matchup_prob(0.6, 0.4, home_advantage=0.5) == pytest.approx(0.692307692)
    a, b, ha = 0.6, 0.45, 0.54
    odds = (a / (1 - a)) / (b / (1 - b)) * (ha / (1 - ha))
    assert Log5Model.team_matchup_prob(a, b, home_advantage=ha) == pytest.approx(odds / (1 + odds))


def test_log5_reproduces_tangos_odds_ratio_values() -> None:
    """Tango, 'The Odds Ratio Method' (2006): .600 vs .400 gives .692; .400 hitter, .250 pitcher, .333 league gives .308."""
    assert round(Log5Model.team_matchup_prob(0.6, 0.4), 3) == 0.692
    assert round(Log5Model.batter_pitcher_matchup_rate(0.400, 0.250, 1 / 3), 3) == 0.308
    # Hitter .400 in a .300 league, pitcher .250 in a .350 league, shared environment .380: matchup odds .590, rate .371.
    odds = (0.4 / 0.6) / (0.30 / 0.70) * (0.25 / 0.75) / (0.35 / 0.65) * (0.38 / 0.62)
    assert odds == pytest.approx(0.590, abs=0.001)
    assert round(odds / (1 + odds), 3) == pytest.approx(0.371, abs=0.001)


ROBINSON_PRIOR = (78.661, 224.875)
ROBINSON_ROWS = [
    # name, hits, at bats, published empirical Bayes estimate (varianceexplained.org, empirical_bayes_baseball)
    ("Rogers Hornsby", 2930, 8173, 0.355),
    ("Shoeless Joe Jackson", 1772, 4981, 0.350),
    ("Ed Delahanty", 2596, 7505, 0.343),
    ("Billy Hamilton", 2158, 6268, 0.340),
    ("Harry Heilmann", 2660, 7787, 0.339),
    ("Bill Bergen", 516, 3028, 0.178),
    ("Ray Oyler", 221, 1265, 0.191),
    ("John Vukovich", 90, 559, 0.196),
    ("John Humphries", 52, 364, 0.196),
    ("George Baker", 74, 474, 0.196),
]


@pytest.mark.parametrize(("name", "hits", "at_bats", "published"), ROBINSON_ROWS)
def test_empirical_bayes_reproduces_robinsons_published_estimates(
    name: str, hits: int, at_bats: int, published: float
) -> None:
    """David Robinson's posterior (H + 78.661) / (AB + 303.536), printed to three decimals."""
    from sabermetricspy.uncertainty import EmpiricalBayesShrinker

    frame = pl.DataFrame({"player_id": [name], "h": [hits], "ab": [at_bats]})
    out = EmpiricalBayesShrinker(prior=ROBINSON_PRIOR).fit(frame).transform(frame)
    assert out["eb_rate"][0] == pytest.approx(published, abs=0.0005)


def test_empirical_bayes_four_for_ten_example_and_tangos_mets_ballast() -> None:
    from sabermetricspy.uncertainty import EmpiricalBayesShrinker

    frame = pl.DataFrame({"player_id": ["x"], "h": [4], "ab": [10]})
    out = EmpiricalBayesShrinker(prior=ROBINSON_PRIOR).fit(frame).transform(frame)
    assert out["eb_rate"][0] == pytest.approx(0.264, abs=0.0005)
    # Tango's method for win percentage: ballast 77 games, Mets 12-13 gives (12 + 39) / (25 + 78) = .495.
    mets = pl.DataFrame({"player_id": ["mets"], "h": [12], "ab": [25]})
    got = EmpiricalBayesShrinker(prior=(38.5, 38.5)).fit(mets).transform(mets)["eb_rate"][0]
    assert got == pytest.approx(51 / 103, abs=0.0006)
