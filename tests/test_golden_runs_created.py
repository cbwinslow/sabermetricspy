"""Runs Created equals Baseball-Reference's published values (tests/golden/runs_created_bref.yaml)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import polars as pl
import pytest
import yaml

import sabermetricspy as sp
from sabermetricspy import Metric

REF: dict[str, list[dict[str, Any]]] = yaml.safe_load(
    (Path(__file__).parent / "golden" / "runs_created_bref.yaml").read_text("utf-8")
)


def _value(row: dict[str, Any], metric: Metric) -> float:
    cols = {k: [v] for k, v in row.items() if k not in ("player", "season", "rc")}
    return sp.calculate(pl.DataFrame(cols), [metric]).df[metric.value][0]


@pytest.mark.parametrize("row", REF["technical"], ids=lambda r: r["player"])
def test_technical_runs_created_rounds_to_baseball_reference(row: dict[str, Any]) -> None:
    assert round(_value(row, Metric.RC_TECH)) == row["rc"]


@pytest.mark.parametrize("row", REF["basic"], ids=lambda r: r["player"])
def test_basic_runs_created_rounds_to_baseball_reference(row: dict[str, Any]) -> None:
    assert round(_value(row, Metric.RC_BASIC)) == row["rc"]
