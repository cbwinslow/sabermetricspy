"""Expected and Maximum Calibration Error (tests/golden/ece_mce.yaml).

Neither Naeini et al. (2015) nor Guo et al. (2017) prints a numeric example, so the rows are hand arithmetic from the
quoted definitions or library-computed fixtures (also reproduced by an independent implementation in the research
notes); the fixture header says so. Equal-frequency and predicted-class (Guo confidence) rows are not implemented.
"""

from __future__ import annotations

from typing import Any

import polars as pl
import pytest
from golden_loader import load_entries
from hypothesis import given
from hypothesis import strategies as st

import sabermetricspy.evaluation as ev

ENTRIES = [
    e
    for e in load_entries("ece_mce.yaml")
    if e["inputs"].get("strategy") == "uniform" and e["inputs"].get("form") == "event"
]


@pytest.mark.parametrize("entry", ENTRIES, ids=lambda e: e["id"])
def test_ece_and_mce_match_the_fixture(entry: dict[str, Any]) -> None:
    i = entry["inputs"]
    df = pl.DataFrame({"p": i["p"], "y": i["y"]})
    kw: dict[str, Any] = {"n_bins": i["n_bins"], "closed": i["closed"]}
    assert ev.expected_calibration_error(df, "p", "y", **kw) == pytest.approx(
        entry["published"]["ece"], abs=entry["tolerance"]["ece"]
    )
    assert ev.maximum_calibration_error(df, "p", "y", **kw) == pytest.approx(
        entry["published"]["mce"], abs=entry["tolerance"]["mce"]
    )


def test_one_bin_gives_the_absolute_gap_between_base_rate_and_mean_forecast() -> None:
    df = pl.DataFrame({"p": [0.1, 0.4, 0.9], "y": [0, 1, 1]})
    expected = abs(2 / 3 - (0.1 + 0.4 + 0.9) / 3)
    assert ev.expected_calibration_error(df, "p", "y", n_bins=1) == pytest.approx(expected)
    assert ev.maximum_calibration_error(df, "p", "y", n_bins=1) == pytest.approx(expected)


def test_weights_act_as_repeated_rows() -> None:
    df = pl.DataFrame({"p": [0.2, 0.8], "y": [0, 1], "w": [3.0, 1.0]})
    rep = pl.DataFrame({"p": [0.2, 0.2, 0.2, 0.8], "y": [0, 0, 0, 1]})
    for fn in (ev.expected_calibration_error, ev.maximum_calibration_error):
        assert fn(df, "p", "y", n_bins=5, weight_col="w") == pytest.approx(
            fn(rep, "p", "y", n_bins=5)
        )


def test_invalid_input_raises() -> None:
    df = pl.DataFrame({"p": [0.2, 0.8], "y": [0, 1]})
    with pytest.raises(ValueError, match="n_bins"):
        ev.expected_calibration_error(df, "p", "y", n_bins=0)
    with pytest.raises(ValueError, match="closed"):
        ev.maximum_calibration_error(df, "p", "y", closed="middle")  # type: ignore[arg-type]
    with pytest.raises(ValueError):
        ev.expected_calibration_error(pl.DataFrame({"p": [1.2], "y": [1]}), "p", "y")


probs = st.floats(min_value=0.0, max_value=1.0, allow_nan=False)


@given(st.lists(st.tuples(probs, st.integers(0, 1)), min_size=1, max_size=60), st.integers(1, 20))
def test_ece_is_between_zero_and_mce_and_both_within_unit_interval(
    rows: list[tuple[float, int]], n_bins: int
) -> None:
    df = pl.DataFrame({"p": [r[0] for r in rows], "y": [r[1] for r in rows]})
    ece = ev.expected_calibration_error(df, "p", "y", n_bins=n_bins)
    mce = ev.maximum_calibration_error(df, "p", "y", n_bins=n_bins)
    assert 0.0 <= ece <= mce + 1e-12 <= 1.0 + 1e-12
