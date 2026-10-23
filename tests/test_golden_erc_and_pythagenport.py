"""Tests for Component ERA (ERC) and Pythagenport Winning Percentage."""

from __future__ import annotations

import math
from pathlib import Path
from typing import Any

import duckdb
import pandas as pd
import polars as pl
import pyarrow as pa
import pytest
import yaml
from hypothesis import given, settings
from hypothesis import strategies as st

import sabermetricspy as sp
from sabermetricspy import Metric

FIXTURE_PATH = Path(__file__).parent / "golden" / "erc_and_pythagenport.yaml"


def _load_fixtures() -> dict[str, Any]:
    with open(FIXTURE_PATH, encoding="utf-8") as f:
        return yaml.safe_load(f)


FIXTURES = _load_fixtures()


@pytest.mark.parametrize("case", FIXTURES["component_era"], ids=lambda c: c["label"])
def test_erc_matches_fixture(case: dict[str, Any]) -> None:
    inputs = {k: [case[k]] for k in ("h", "hr", "bb", "outs", "bf") if k in case}
    if "hbp" in case:
        inputs["hbp"] = [case["hbp"]]
    if "ibb" in case:
        inputs["ibb"] = [case["ibb"]]
    df = pl.DataFrame(inputs)
    res = sp.calculate(df, [Metric.ERC]).df.row(0, named=True)
    expected = case["expected_erc"]
    tol = case.get("tolerance", 1e-6)
    assert res["erc"] == pytest.approx(expected, abs=tol)


@pytest.mark.parametrize("case", FIXTURES["pythagenport"], ids=lambda c: c["label"])
def test_pythagenport_matches_fixture(case: dict[str, Any]) -> None:
    inputs = {k: [case[k]] for k in ("rs", "ra", "w", "l")}
    df = pl.DataFrame(inputs)
    res = sp.calculate(df, [Metric.PYTHAGENPORT_WIN_PCT]).df.row(0, named=True)
    expected = case["expected_pythagenport_win_pct"]
    tol = case.get("tolerance", 1e-5)
    assert res["pythagenport_win_pct"] == pytest.approx(expected, abs=tol)


def test_erc_continuity_at_2_24_threshold() -> None:
    """The piecewise branches of Component ERA meet at raw = 2.24: 2.24 * 0.75 == 2.24 - 0.56 == 1.68."""
    assert pytest.approx(1.68) == 2.24 * 0.75
    assert pytest.approx(1.68) == 2.24 - 0.56


def test_pythagenport_gibson_1968_rpg_tieout() -> None:
    """Bob Gibson 1968 run environment (RPG = 5.03) gives exponent approximately 1.50."""
    rpg = 5.03
    gamma = 1.50 * math.log10(rpg) + 0.45
    assert gamma == pytest.approx(1.50, abs=0.005)


def test_zero_denominator_null_safety() -> None:
    """Zero outs or BF for ERC, and zero games for Pythagenport return null without exception."""
    df_pitching = pl.DataFrame(
        {
            "h": [10.0, 0.0],
            "hr": [2.0, 0.0],
            "bb": [5.0, 0.0],
            "outs": [0, 0],
            "bf": [0, 0],
        }
    )
    res_pit = sp.calculate(df_pitching, [Metric.ERC]).df
    assert res_pit["erc"][0] is None
    assert res_pit["erc"][1] is None

    df_team = pl.DataFrame(
        {
            "rs": [0.0, 10.0],
            "ra": [0.0, 10.0],
            "w": [0, 0],
            "l": [0, 0],
        }
    )
    res_team = sp.calculate(df_team, [Metric.PYTHAGENPORT_WIN_PCT]).df
    assert res_team["pythagenport_win_pct"][0] is None
    assert res_team["pythagenport_win_pct"][1] is None


def test_multi_backend_execution() -> None:
    """Verify execution across Polars, DuckDB, PyArrow, and pandas backends."""
    data_pitching = {
        "h": [150.0],
        "hr": [20.0],
        "bb": [50.0],
        "hbp": [5.0],
        "ibb": [2.0],
        "outs": [600],
        "bf": [800],
    }
    data_team = {
        "rs": [965.0],
        "ra": [656.0],
        "w": [114],
        "l": [48],
    }

    # Polars
    res_polars_pit = sp.calculate(pl.DataFrame(data_pitching), [Metric.ERC]).df["erc"][0]
    res_polars_team = sp.calculate(pl.DataFrame(data_team), [Metric.PYTHAGENPORT_WIN_PCT]).df[
        "pythagenport_win_pct"
    ][0]
    assert res_polars_pit == pytest.approx(2.27765045, abs=1e-5)
    assert res_polars_team == pytest.approx(0.6797866, abs=1e-5)

    # pandas
    res_pandas_pit = sp.calculate(pd.DataFrame(data_pitching), [Metric.ERC]).df["erc"].iloc[0]
    res_pandas_team = (
        sp.calculate(pd.DataFrame(data_team), [Metric.PYTHAGENPORT_WIN_PCT])
        .df["pythagenport_win_pct"]
        .iloc[0]
    )
    assert res_pandas_pit == pytest.approx(2.27765045, abs=1e-5)
    assert res_pandas_team == pytest.approx(0.6797866, abs=1e-5)

    # PyArrow
    res_arrow_pit = (
        sp.calculate(pa.Table.from_pydict(data_pitching), [Metric.ERC]).df["erc"][0].as_py()
    )
    res_arrow_team = (
        sp.calculate(pa.Table.from_pydict(data_team), [Metric.PYTHAGENPORT_WIN_PCT])
        .df["pythagenport_win_pct"][0]
        .as_py()
    )
    assert res_arrow_pit == pytest.approx(2.27765045, abs=1e-5)
    assert res_arrow_team == pytest.approx(0.6797866, abs=1e-5)

    # DuckDB
    con = duckdb.connect()
    rel_pit = con.from_df(pd.DataFrame(data_pitching))
    res_duck_pit = sp.calculate(rel_pit, [Metric.ERC]).to_polars()["erc"][0]
    rel_team = con.from_df(pd.DataFrame(data_team))
    res_duck_team = sp.calculate(rel_team, [Metric.PYTHAGENPORT_WIN_PCT]).to_polars()[
        "pythagenport_win_pct"
    ][0]
    assert res_duck_pit == pytest.approx(2.27765045, abs=1e-5)
    assert res_duck_team == pytest.approx(0.6797866, abs=1e-5)


@given(
    rs=st.integers(min_value=1, max_value=1500),
    ra=st.integers(min_value=1, max_value=1500),
    w=st.integers(min_value=1, max_value=162),
    losses=st.integers(min_value=1, max_value=162),
)
@settings(max_examples=40)
def test_hypothesis_pythagenport_properties(rs: int, ra: int, w: int, losses: int) -> None:
    """Property: Pythagenport W% is always between 0 and 1, and equals 0.5 when RS == RA."""
    df = pl.DataFrame({"rs": [rs], "ra": [ra], "w": [w], "l": [losses]})
    got = sp.calculate(df, [Metric.PYTHAGENPORT_WIN_PCT]).df["pythagenport_win_pct"][0]
    assert got is not None
    assert 0.0 <= got <= 1.0
    if rs == ra:
        assert got == pytest.approx(0.5, abs=1e-6)
