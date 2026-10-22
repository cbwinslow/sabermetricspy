"""Extrapolated Runs (XR) and Extrapolated Runs Reduced (XRR) reproduce Furtado's printed example (tests/golden/extrapolated_runs.yaml).

Rule-7 note: the printed example is Furtado's own computation, so these tests validate the arithmetic and the inputs
(the same 14 inputs equal the Lahman 2025 row for McGwire 1998), not the estimator's accuracy. XRB is deliberately not
implemented: the article's printed XRB example (169.03) only reproduces with a walk weight of .35, not the printed .34.
"""

from __future__ import annotations

from typing import Any

import polars as pl
import pytest
from golden_loader import load_entries
from hypothesis import given
from hypothesis import strategies as st

import sabermetricspy as sp
from sabermetricspy import Metric
from sabermetricspy.metrics.weighted import XR_WEIGHTS, XRR_WEIGHTS

ENTRIES = load_entries("extrapolated_runs.yaml")
REQUIRED = ("ab", "h", "b2", "b3", "hr", "bb", "so")


def _frame(inputs: dict[str, int]) -> pl.DataFrame:
    row = {c: 0 for c in REQUIRED} | inputs
    return pl.DataFrame([row])


def _both(inputs: dict[str, int]) -> tuple[float, float]:
    df = sp.calculate(_frame(inputs), [Metric.XR, Metric.XRR]).df
    return df["xr"][0], df["xrr"][0]


@pytest.mark.parametrize("entry", ENTRIES, ids=lambda e: e["id"])
def test_xr_and_xrr_match_the_fixture(entry: dict[str, Any]) -> None:
    xr, xrr = _both(entry["inputs"])
    assert xr == pytest.approx(entry["published"]["xr"], abs=entry["tolerance"]["xr"]), entry["id"]
    assert xrr == pytest.approx(entry["published"]["xrr"], abs=entry["tolerance"]["xrr"]), entry[
        "id"
    ]


def test_weights_equal_the_quoted_coefficients() -> None:
    assert XR_WEIGHTS == {
        "b1": 0.50, "b2": 0.72, "b3": 1.04, "hr": 1.44, "unintentional_walk_hbp": 0.34, "ibb": 0.25,
        "sb": 0.18, "cs": -0.32, "non_strikeout_out": -0.090, "so": -0.098, "gidp": -0.37, "sf": 0.37, "sh": 0.04,
    }  # fmt: skip
    assert XRR_WEIGHTS == {
        "b1": 0.50, "b2": 0.72, "b3": 1.04, "hr": 1.44, "walk_hbp": 0.33, "sb": 0.18, "cs": -0.32, "out": -0.098,
    }  # fmt: skip


def test_all_zero_row_is_zero() -> None:
    assert _both({}) == (0.0, 0.0)


def test_xr_needs_strikeouts_but_xrr_does_not() -> None:
    df = pl.DataFrame({"ab": [4], "h": [1], "b2": [0], "b3": [0], "hr": [0], "bb": [0]})
    result = sp.calculate_available(df, season=2024).df
    assert "xrr" in result.columns
    assert "xr" not in result.columns


def test_registry_names() -> None:
    from sabermetricspy.registry import REGISTRY

    assert REGISTRY.get(Metric.XR).spec.display_name == "XR"
    assert REGISTRY.get(Metric.XRR).spec.display_name == "XRR"
    assert REGISTRY.resolve_name("XRR") == "xrr"


counts = st.integers(min_value=0, max_value=700)


@st.composite
def lines(draw: st.DrawFn) -> dict[str, int]:
    h = draw(counts)
    b2, b3, hr = draw(counts), draw(counts), draw(counts)
    h = max(h, b2 + b3 + hr)
    ab = h + draw(counts)
    so = draw(st.integers(min_value=0, max_value=ab - h))
    return {
        "ab": ab, "h": h, "b2": b2, "b3": b3, "hr": hr, "bb": draw(counts), "so": so,
        "ibb": 0, "hbp": draw(counts), "sb": draw(counts), "cs": draw(counts), "gidp": draw(counts),
        "sf": draw(counts), "sh": draw(counts),
    }  # fmt: skip


@given(lines(), lines())
def test_xr_and_xrr_are_additive_across_players(a: dict[str, int], b: dict[str, int]) -> None:
    total = {k: a[k] + b[k] for k in a}
    xr_a, xrr_a = _both(a)
    xr_b, xrr_b = _both(b)
    xr_t, xrr_t = _both(total)
    assert xr_t == pytest.approx(xr_a + xr_b, abs=1e-6)
    assert xrr_t == pytest.approx(xrr_a + xrr_b, abs=1e-6)


@given(lines(), st.integers(min_value=1, max_value=9))
def test_xr_scales_linearly_with_every_count(a: dict[str, int], k: int) -> None:
    xr_a, xrr_a = _both(a)
    xr_k, xrr_k = _both({key: k * v for key, v in a.items()})
    assert xr_k == pytest.approx(k * xr_a, abs=1e-6)
    assert xrr_k == pytest.approx(k * xrr_a, abs=1e-6)
