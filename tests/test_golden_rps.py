"""Ranked probability score against Epstein (1969) Tables 1-2 and hand arithmetic (tests/golden/rps_epstein_1969.yaml).

Epstein prints the positively oriented score S_j (1 is perfect); the library returns the loss `1 - S_j` with the
1/(K - 1) normalisation. Two printed Table 2 cells (0.92 for the forecast (0, 1/6, 1/3, 1/3, 1/6, 0) when category 3 or
4 occurs) disagree with the formula (0.9389); a second reading of the page image confirms the paper prints 0.92, so the
cells are excluded (the fixture's `excluded` list), not adjusted.
"""

from __future__ import annotations

from fractions import Fraction
from typing import Any

import polars as pl
import pytest
from golden_loader import load_entries
from hypothesis import given
from hypothesis import strategies as st

import sabermetricspy.evaluation as ev

ENTRIES = load_entries("rps_epstein_1969.yaml")
TABLE = [e for e in ENTRIES if "s_by_observed" in e["published"]]
HAND = [e for e in ENTRIES if "rps_normalised" in e["published"]]


def _probs(raw: list[Any]) -> list[float]:
    return [float(Fraction(str(x))) for x in raw]


def _rps(forecast: list[float], observed_zero_based: int, *, normalise: bool = True) -> float:
    k = len(forecast)
    data: dict[str, list[float]] = {f"p{i}": [forecast[i]] for i in range(k)}
    data["obs"] = [float(observed_zero_based)]
    return ev.ranked_probability_score(
        pl.DataFrame(data), [f"p{i}" for i in range(k)], "obs", normalise=normalise
    )


@pytest.mark.parametrize("entry", TABLE, ids=lambda e: e["id"])
def test_epstein_tables_are_reproduced_as_one_minus_the_loss(entry: dict[str, Any]) -> None:
    forecast = _probs(entry["inputs"]["forecast"])
    for j, printed in enumerate(entry["published"]["s_by_observed"]):
        if printed is None:  # the two excluded cells
            continue
        got = 1.0 - _rps(forecast, j)
        assert got == pytest.approx(printed, abs=entry["tolerance"]["s_by_observed"]), (
            entry["id"],
            j + 1,
        )


@pytest.mark.parametrize("entry", HAND, ids=lambda e: e["id"])
def test_hand_arithmetic_rows(entry: dict[str, Any]) -> None:
    forecast = _probs(entry["inputs"]["forecast"])
    pos = int(entry["inputs"]["observed"]) - 1  # the fixture counts categories from 1
    pub, tol = entry["published"], entry["tolerance"]
    assert _rps(forecast, pos, normalise=False) == pytest.approx(
        pub["rps_unnormalised"], abs=tol["rps_unnormalised"]
    )
    assert _rps(forecast, pos) == pytest.approx(pub["rps_normalised"], abs=tol["rps_normalised"])


def test_two_categories_equal_the_brier_score_of_the_first_category() -> None:
    df = pl.DataFrame({"a": [0.7, 0.2, 0.9], "b": [0.3, 0.8, 0.1], "obs": [0, 1, 0]})
    rps = ev.ranked_probability_score(df, ["a", "b"], "obs")
    brier = ev.brier_score(df.with_columns(y=(pl.col("obs") == 0).cast(pl.Int64)), "a", "y")
    assert rps == pytest.approx(brier)


def test_category_order_matters() -> None:
    assert _rps([0.7, 0.2, 0.1], 2) != pytest.approx(_rps([0.2, 0.7, 0.1], 2))


def test_weights_act_as_repeated_rows() -> None:
    df = pl.DataFrame(
        {"a": [0.6, 0.1], "b": [0.3, 0.2], "c": [0.1, 0.7], "obs": [0, 2], "w": [3.0, 1.0]}
    )
    rep = pl.DataFrame(
        {
            "a": [0.6] * 3 + [0.1],
            "b": [0.3] * 3 + [0.2],
            "c": [0.1] * 3 + [0.7],
            "obs": [0, 0, 0, 2],
        }
    )
    cols = ["a", "b", "c"]
    assert ev.ranked_probability_score(df, cols, "obs", weight_col="w") == pytest.approx(
        ev.ranked_probability_score(rep, cols, "obs")
    )


def test_invalid_input_raises() -> None:
    ok = pl.DataFrame({"a": [0.5], "b": [0.5], "obs": [1]})
    with pytest.raises(ValueError, match="at least two"):
        ev.ranked_probability_score(ok, ["a"], "obs")
    with pytest.raises(ValueError, match="sum to 1"):
        ev.ranked_probability_score(ok.with_columns(b=pl.lit(0.4)), ["a", "b"], "obs")
    with pytest.raises(ValueError, match="positions"):
        ev.ranked_probability_score(ok.with_columns(obs=pl.lit(2)), ["a", "b"], "obs")
    with pytest.raises(ValueError, match="positions"):
        ev.ranked_probability_score(ok.with_columns(obs=pl.lit(0.5)), ["a", "b"], "obs")
    with pytest.raises(ValueError, match=r"\[0, 1\]"):
        ev.ranked_probability_score(
            ok.with_columns(a=pl.lit(1.5), b=pl.lit(-0.5)), ["a", "b"], "obs"
        )


@given(st.lists(st.integers(0, 20), min_size=2, max_size=6).filter(lambda v: sum(v) > 0), st.data())
def test_score_lies_between_zero_and_one(weights: list[int], data: st.DataObject) -> None:
    total = sum(weights)
    forecast = [w / total for w in weights]
    pos = data.draw(st.integers(0, len(forecast) - 1))
    assert -1e-12 <= _rps(forecast, pos) <= 1.0 + 1e-12


def test_probabilities_rounded_to_four_decimals_are_accepted() -> None:
    df = pl.DataFrame({"a": [0.3333], "b": [0.3333], "c": [0.3333], "obs": [1]})
    assert ev.ranked_probability_score(df, ["a", "b", "c"], "obs") >= 0.0
    bad = pl.DataFrame({"a": [0.3], "b": [0.3], "c": [0.3], "obs": [1]})
    with pytest.raises(ValueError, match="sum to 1"):
        ev.ranked_probability_score(bad, ["a", "b", "c"], "obs")
