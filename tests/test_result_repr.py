"""Printing a CalculationResult must never raise UnicodeEncodeError on a legacy (cp1252) console."""

from __future__ import annotations

import polars as pl
import pytest

import sabermetricspy as sp
from sabermetricspy import Metric

LINE = dict(
    player_id=["b"],
    pa=[664],
    ab=[476],
    h=[156],
    b2=[32],
    b3=[2],
    hr=[73],
    bb=[177],
    hbp=[9],
    sf=[2],
    so=[93],
)


@pytest.mark.parametrize("backend", ["polars", "pandas", "pyarrow"])
def test_repr_and_str_are_ascii_and_cp1252_safe(backend: str) -> None:
    frame = pl.DataFrame(LINE)
    native = {"polars": frame, "pandas": frame.to_pandas(), "pyarrow": frame.to_arrow()}[backend]
    res = sp.calculate(native, [Metric.WOBA, Metric.WRC_PLUS, Metric.K_MINUS_BB_PCT])
    for text in (repr(res), str(res), res.summary()):
        text.encode("cp1252")  # raises UnicodeEncodeError if any character is unsupported
        assert text.isascii()
    assert "woba" in repr(res)
