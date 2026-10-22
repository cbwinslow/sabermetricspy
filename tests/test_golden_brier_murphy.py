"""Brier score and the Murphy decomposition against printed values and bin-convention rows (tests/golden/brier_murphy.yaml).

Brier (1950) and Murphy (1973) print two-class / two-state vector values, exactly twice the library's single-event
values (see the fixture's single_event fields). Rows marked `prototype-computed` are library-computed fixtures (the
ten-point forecast set below), not paper values: they pin the bin convention, not a published number.
"""

from __future__ import annotations

from typing import Any

import polars as pl
import pytest
from golden_loader import load_entries

import sabermetricspy.evaluation as ev

ENTRIES = load_entries("brier_murphy.yaml")
# The ten-point set behind the prototype-computed rows (documented in the research dossier, tieouts/brier_murphy_decomposition).
TEN_POINT = pl.DataFrame(
    {
        "p": [0.1, 0.2, 0.8, 0.65, 0.9, 0.4, 0.3, 0.5, 0.7, 0.95],
        "y": [0, 0, 1, 1, 1, 0, 1, 0, 1, 1],
    }
)
FIELDS = ("reliability", "resolution", "uncertainty", "brier_score", "within_bin_remainder")


def _frame(entry: dict[str, Any]) -> pl.DataFrame:
    inputs = entry["inputs"]
    if "forecast" in inputs:
        return pl.DataFrame({"p": inputs["forecast"], "y": inputs["observed"]})
    return TEN_POINT


@pytest.mark.parametrize("entry", ENTRIES, ids=lambda e: e["id"])
def test_calibration_table_matches_the_fixture(entry: dict[str, Any]) -> None:
    inputs, published, tol = entry["inputs"], entry["published"], entry["tolerance"]
    df = _frame(entry)
    if entry["id"] == "brier1950_table1_P":
        got = ev.brier_score(df, "p", "y")
        assert got == pytest.approx(published["brier_single_event"], abs=tol["brier_single_event"])
        assert 2 * got == pytest.approx(published["brier_two_class"], abs=tol["brier_two_class"])
        base = sum(inputs["observed"]) / len(inputs["observed"])
        assert 1 - (base**2 + (1 - base) ** 2) == pytest.approx(
            published["constant_0_3_two_class"], abs=0.005
        )
        return
    if (
        "single_event_equivalents" in entry
    ):  # Murphy 1973: one-decimal forecasts, each in its own bin
        eq = entry["single_event_equivalents"]
        res = ev.calibration_table(df, "p", "y", n_bins=10)
        tol_half = tol["unc_vector"] / 2
        assert res.uncertainty == pytest.approx(eq["uncertainty"], abs=tol_half)
        assert res.reliability == pytest.approx(eq["reliability"], abs=tol_half)
        assert res.resolution == pytest.approx(eq["resolution"], abs=tol_half)
        assert res.brier_score == pytest.approx(eq["brier_score"], abs=tol_half)
        return
    n_bins = inputs.get(
        "n_bins", 1000 if "grouping" in inputs else 10
    )  # 1000 bins: every distinct forecast alone
    closed = inputs.get("closed", "right")
    res = ev.calibration_table(df, "p", "y", n_bins=n_bins, closed=closed)
    for field in FIELDS:
        if field in published:
            assert getattr(res, field) == pytest.approx(published[field], abs=tol[field]), (
                entry["id"],
                field,
            )


def test_the_two_conventions_differ_only_for_forecasts_on_an_inner_edge() -> None:
    off_edge = pl.DataFrame({"p": [0.05, 0.25, 0.45, 0.65, 0.85], "y": [0, 0, 1, 1, 1]})
    right = ev.calibration_table(off_edge, "p", "y", n_bins=5, closed="right")
    left = ev.calibration_table(off_edge, "p", "y", n_bins=5, closed="left")
    assert right.model_dump() == left.model_dump()
    on_edge = pl.DataFrame({"p": [0.2, 0.2], "y": [0, 1]})
    assert (
        ev.calibration_table(on_edge, "p", "y", n_bins=5, closed="right").bins[0].bin_upper == 0.2
    )
    assert ev.calibration_table(on_edge, "p", "y", n_bins=5, closed="left").bins[0].bin_lower == 0.2


def test_decimal_edges_stay_in_the_right_closed_bin_for_many_bins() -> None:
    # floor(p * n) puts 29/50 in the wrong bin; the searchsorted construction does not.
    df = pl.DataFrame({"p": [29 / 50], "y": [1]})
    res = ev.calibration_table(df, "p", "y", n_bins=50, closed="right")
    assert res.bins[0].bin_upper == pytest.approx(29 / 50)


def test_closed_must_be_left_or_right() -> None:
    with pytest.raises(ValueError, match="closed"):
        ev.calibration_table(TEN_POINT, "p", "y", closed="middle")  # type: ignore[arg-type]
