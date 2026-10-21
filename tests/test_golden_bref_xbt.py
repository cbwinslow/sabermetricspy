"""Extra bases taken % from Baseball-Reference's published situation counts equals its printed team percentages."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import polars as pl
import pytest
import yaml

import sabermetricspy as sp
from sabermetricspy import Metric

ROWS: list[dict[str, Any]] = yaml.safe_load(
    (Path(__file__).parent / "golden" / "bref_xbt_2025.yaml").read_text("utf-8")
)["rows"]


def _xbt_pct(row: dict[str, Any]) -> float:
    frame = pl.DataFrame(
        {
            "xbt": [
                row["on_first_single_13"] + row["on_first_double_1H"] + row["on_second_single_2H"]
            ],
            "xbt_opp": [row["on_first_single"] + row["on_first_double"] + row["on_second_single"]],
        }
    )
    return sp.calculate(frame, [Metric.XBT_PCT]).df["xbt_pct"][0]


def test_every_team_row_is_present() -> None:
    assert len(ROWS) == 30


@pytest.mark.parametrize("row", ROWS, ids=lambda r: r["team"])
def test_xbt_pct_rounds_to_the_printed_team_percent(row: dict[str, Any]) -> None:
    assert round(100 * _xbt_pct(row)) == row["xbt_pct"]
