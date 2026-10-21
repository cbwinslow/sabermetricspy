"""MarkovWinExpectancy: hand-solvable chains, structure and input checks.

The comparison with Tom Tango's published table on real Retrosheet data is opt-in in
tests/test_retrosheet_2016_markov_win_expectancy.py.
"""

from __future__ import annotations

from typing import Any

import polars as pl
import pytest

import sabermetricspy as sp

BASES = ["---", "1--", "-2-", "--3", "12-", "1-3", "-23", "123"]
P_HR = 0.25  # a solo home run with probability 1/4 from every state, otherwise an out


def _home_run_or_out_plays(hr: int = 100, out: int = 300) -> pl.DataFrame:
    rows: list[dict[str, Any]] = []
    for o in (0, 1, 2):
        for b in BASES:
            rows += [
                {
                    "outs_before": o,
                    "base_state_before": b,
                    "outs_after": o,
                    "base_state_after": b,
                    "runs_on_play": 1,
                }
            ] * hr
            rows += [
                {
                    "outs_before": o,
                    "base_state_before": b,
                    "outs_after": o + 1,
                    "base_state_after": b,
                    "runs_on_play": 0,
                }
            ] * out
    return pl.DataFrame(rows)


@pytest.fixture(scope="module")
def model() -> sp.MarkovWinExpectancy:
    return sp.MarkovWinExpectancy().fit(_home_run_or_out_plays())


def test_equal_teams_start_at_exactly_one_half(model: sp.MarkovWinExpectancy) -> None:
    # Identical teams and a tie: 0.5 by symmetry, up to the run-difference cap (a lead of 12 is treated as decisive)
    assert model.win_expectancy(1, "top", 0, "---", 0) == pytest.approx(0.5, abs=1e-4)


def test_bottom_of_the_ninth_tied_matches_the_closed_form(model: sp.MarkovWinExpectancy) -> None:
    """Home wins at once if it hits a home run before its third out; otherwise extra innings, worth 0.5 by symmetry."""
    for outs in (0, 1, 2):
        reaches = 1.0 - (1.0 - P_HR) ** (3 - outs)
        expected = reaches + (1.0 - reaches) * 0.5
        assert model.win_expectancy(9, "bottom", outs, "---", 0) == pytest.approx(
            expected, abs=1e-9
        )


def test_bottom_of_the_ninth_trailing_by_one_needs_two_home_runs(
    model: sp.MarkovWinExpectancy,
) -> None:
    """Down 1 with 2 outs: a home run ties (the inning goes on), a second wins; an out ends the inning at -1, a loss."""
    # With 2 outs, a first home run (P) ties the game and the inning continues with 2 outs; the same
    # value as down 0 with 2 outs, which is P + (1 - P) * 0.5.
    tied_two_outs = P_HR + (1.0 - P_HR) * 0.5
    assert model.win_expectancy(9, "bottom", 2, "---", -1) == pytest.approx(
        P_HR * tied_two_outs, abs=1e-9
    )


def test_a_lead_after_the_top_of_the_ninth_is_a_win_before_the_bottom_is_played(
    model: sp.MarkovWinExpectancy,
) -> None:
    assert (
        model.win_expectancy(9, "top", 2, "123", 1) < 1.0
    )  # the home team may still lose the lead in the top
    assert model.win_expectancy(9, "bottom", 0, "---", 1) == pytest.approx(1.0)
    assert model.win_expectancy(9, "bottom", 0, "---", -12) == 0.0


def test_values_are_probabilities_and_rise_with_the_home_lead(
    model: sp.MarkovWinExpectancy,
) -> None:
    for inning in (1, 5, 9, 12):
        values = [model.win_expectancy(inning, "top", 0, "---", d) for d in range(-6, 7)]
        assert all(0.0 <= v <= 1.0 for v in values)
        assert values == sorted(values)


def test_unobserved_states_and_bad_input_raise() -> None:
    plays = _home_run_or_out_plays().filter(pl.col("base_state_before") != "123")
    with pytest.raises(ValueError, match="No plays observed"):
        sp.MarkovWinExpectancy().fit(plays)
    with pytest.raises(ValueError, match="missing columns"):
        sp.MarkovWinExpectancy().fit(plays.drop("runs_on_play"))
    with pytest.raises(RuntimeError, match="not fitted"):
        sp.MarkovWinExpectancy().win_expectancy(1, "top", 0, "---", 0)
    with pytest.raises(ValueError, match="at least 9"):
        sp.MarkovWinExpectancy(max_inning=8)


def test_results_report_the_fit(model: sp.MarkovWinExpectancy) -> None:
    assert model.results.n_plays == 24 * 400
    assert model.results.max_inning == 30
