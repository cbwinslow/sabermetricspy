"""Glicko-2 reproduces every printed value of Glickman's worked example (tests/golden/glicko2.yaml).

Source: Glickman, "Example of the Glicko-2 system" (2022), https://www.glicko.net/glicko/glicko2.pdf, pp. 5-6: a player
rated 1500 (RD 200, volatility 0.06, tau 0.5) beats a 1400/RD 30 opponent and loses to 1550/RD 100 and 1700/RD 300.
The printed r' = 1464.06 and RD' = 151.52 come from rounded intermediates; the full-precision values are
1464.0507 and 151.5165, so tolerances follow the printed rounding.
"""

from __future__ import annotations

import math
from typing import Any

import pytest
from golden_loader import load_entries

import sabermetricspy as sp
from sabermetricspy.models import glicko2 as g2

# The tests reach the private step functions to check the printed intermediate values of the worked example.
_g = g2._g  # pyright: ignore[reportPrivateUsage]
_expected = g2._expected  # pyright: ignore[reportPrivateUsage]
_new_volatility = g2._new_volatility  # pyright: ignore[reportPrivateUsage]

ENTRIES = {e["id"]: e for e in load_entries("glicko2.yaml")}
EX = ENTRIES["glicko2_pdf_example_inputs_to_scale"]["inputs"]
GAMES = [tuple(o) for o in EX["opponents"]]
SCALE = sp.GLICKO2_SCALE


def _terms() -> dict[str, Any]:
    mu = (EX["r"] - 1500.0) / SCALE
    phi = EX["rd"] / SCALE
    mu_j = [(r - 1500.0) / SCALE for r, _, _ in GAMES]
    phi_j = [d / SCALE for _, d, _ in GAMES]
    g = [_g(p) for p in phi_j]
    e = [_expected(mu, m, p) for m, p in zip(mu_j, phi_j, strict=True)]
    v = 1.0 / sum(gi * gi * ei * (1 - ei) for gi, ei in zip(g, e, strict=True))
    delta = v * sum(gi * (s - ei) for gi, (_, _, s), ei in zip(g, GAMES, e, strict=True))
    return {
        "mu": mu,
        "phi": phi,
        "mu_j": mu_j,
        "phi_j": phi_j,
        "g": g,
        "e": e,
        "v": v,
        "delta": delta,
    }


def test_inputs_converted_to_the_glicko2_scale() -> None:
    entry = ENTRIES["glicko2_pdf_example_inputs_to_scale"]
    pub, tol, t = entry["published"], entry["tolerance"], _terms()
    assert t["mu"] == pytest.approx(pub["mu"], abs=tol["mu"])
    assert t["phi"] == pytest.approx(pub["phi"], abs=tol["phi"])
    assert t["mu_j"] == pytest.approx(pub["mu_j"], abs=tol["mu_j"])
    assert t["phi_j"] == pytest.approx(pub["phi_j"], abs=tol["phi_j"])
    assert t["g"] == pytest.approx(pub["g"], abs=tol["g"])
    assert t["e"] == pytest.approx(pub["E"], abs=tol["E"])


def test_estimated_variance_and_improvement() -> None:
    entry = ENTRIES["glicko2_pdf_example_v_delta"]
    t = _terms()
    assert t["v"] == pytest.approx(entry["published"]["v"], abs=entry["tolerance"]["v"])
    assert t["delta"] == pytest.approx(entry["published"]["delta"], abs=entry["tolerance"]["delta"])


def test_volatility_bracket_and_converged_value() -> None:
    entry = ENTRIES["glicko2_pdf_example_volatility_bracket"]
    pub, tol, t = entry["published"], entry["tolerance"], _terms()
    sigma, tau = EX["sigma"], EX["tau"]
    a = math.log(sigma**2)

    def f(x: float) -> float:
        ex = math.exp(x)
        return (
            ex
            * (t["delta"] ** 2 - t["phi"] ** 2 - t["v"] - ex)
            / (2 * (t["phi"] ** 2 + t["v"] + ex) ** 2)
            - (x - a) / tau**2
        )

    assert a == pytest.approx(pub["A0"], abs=tol["A0"])
    assert a - tau == pytest.approx(pub["B0"], abs=tol["B0"])
    assert f(a) == pytest.approx(pub["fA0"], abs=tol["fA0"])
    assert f(a - tau) == pytest.approx(pub["fB0"], abs=tol["fB0"])
    new_sigma = _new_volatility(t["delta"], t["phi"], t["v"], sigma, tau, 1e-6)
    assert 2 * math.log(new_sigma) == pytest.approx(pub["A_final"], abs=tol["A_final"])


def test_new_rating_rd_and_volatility_match_the_worked_example() -> None:
    entry = ENTRIES["glicko2_pdf_example_new_rating"]
    pub, tol = entry["published"], entry["tolerance"]
    new = sp.glicko2_update(EX["r"], EX["rd"], EX["sigma"], GAMES, tau=EX["tau"])
    assert new.volatility == pytest.approx(pub["sigma_new"], abs=tol["sigma_new"])
    assert new.rating == pytest.approx(pub["r_new"], abs=tol["r_new"])
    assert new.rd == pytest.approx(pub["rd_new"], abs=tol["rd_new"])
    phi_new = new.rd / SCALE
    assert phi_new == pytest.approx(pub["phi_new"], abs=tol["phi_new"])
    assert (new.rating - 1500.0) / SCALE == pytest.approx(pub["mu_new"], abs=tol["mu_new"])


def test_full_precision_values_recorded_by_the_research_notes() -> None:
    new = sp.glicko2_update(1500.0, 200.0, 0.06, GAMES, tau=0.5)
    assert new.rating == pytest.approx(1464.0507, abs=1e-3)
    assert new.rd == pytest.approx(151.5165, abs=1e-3)
    assert new.volatility == pytest.approx(0.059996, abs=1e-6)


def test_no_games_only_grows_the_rating_deviation() -> None:
    new = sp.glicko2_update(1600.0, 100.0, 0.06, (), tau=0.5)
    assert new.rating == 1600.0 and new.volatility == 0.06
    assert new.rd == pytest.approx(SCALE * math.sqrt((100.0 / SCALE) ** 2 + 0.06**2))
    assert new.rd > 100.0


def test_expected_score_is_symmetric_around_equal_ratings_and_in_unit_interval() -> None:
    assert sp.glicko2_expected_score(1500.0, 1500.0, 50.0) == pytest.approx(0.5)
    hi = sp.glicko2_expected_score(1700.0, 1500.0, 50.0)
    assert 0.5 < hi < 1.0
    assert sp.glicko2_expected_score(1500.0, 1700.0, 50.0) == pytest.approx(1.0 - hi, abs=1e-12)


def test_winning_raises_and_losing_lowers_the_rating() -> None:
    win = sp.glicko2_update(1500.0, 200.0, 0.06, [(1500.0, 200.0, 1.0)], tau=0.5)
    loss = sp.glicko2_update(1500.0, 200.0, 0.06, [(1500.0, 200.0, 0.0)], tau=0.5)
    assert win.rating > 1500.0 > loss.rating
    assert win.rd < 200.0 and loss.rd < 200.0


def test_invalid_input_raises() -> None:
    games = [(1500.0, 200.0, 1.0)]
    with pytest.raises(ValueError, match="Scores"):
        sp.glicko2_update(1500.0, 200.0, 0.06, [(1500.0, 200.0, 0.7)], tau=0.5)
    with pytest.raises(ValueError, match="positive"):
        sp.glicko2_update(1500.0, 0.0, 0.06, games, tau=0.5)
    with pytest.raises(ValueError, match="positive"):
        sp.glicko2_update(1500.0, 200.0, 0.06, games, tau=0.0)
    with pytest.raises(ValueError, match="finite"):
        sp.glicko2_update(float("nan"), 200.0, 0.06, games, tau=0.5)
    with pytest.raises(ValueError, match="opponent"):
        sp.glicko2_update(1500.0, 200.0, 0.06, [(1500.0, 0.0, 1.0)], tau=0.5)
    with pytest.raises(TypeError):
        sp.glicko2_update(1500.0, 200.0, 0.06, games)  # type: ignore[call-arg]
