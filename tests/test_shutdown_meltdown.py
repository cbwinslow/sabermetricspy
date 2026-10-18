"""Shutdown and Meltdown thresholds from the FanGraphs Library page (inclusive, relievers only)."""

from __future__ import annotations

import polars as pl

import sabermetricspy as sp
from sabermetricspy import Metric

# game_wpa, is_reliever, expected shutdown, expected meltdown
CASES = [
    (0.06, True, 1, 0),
    (0.0599, True, 0, 0),
    (0.10, True, 1, 0),  # the page's 84% -> 94% example
    (-0.06, True, 0, 1),
    (-0.0599, True, 0, 0),
    (0.30, False, 0, 0),  # starters never earn either
    (-0.30, False, 0, 0),
]


def test_thresholds_are_inclusive_and_reliever_only() -> None:
    df = pl.DataFrame(
        {
            "player_id": [str(i) for i in range(len(CASES))],
            "game_wpa": [c[0] for c in CASES],
            "is_reliever": [c[1] for c in CASES],
        }
    )
    out = sp.calculate(df, [Metric.SHUTDOWN, Metric.MELTDOWN]).df
    assert out["shutdown"].to_list() == [c[2] for c in CASES]
    assert out["meltdown"].to_list() == [c[3] for c in CASES]
