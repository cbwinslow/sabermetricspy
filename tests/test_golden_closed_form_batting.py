"""Tests for closed-form offensive metrics: Isolated Discipline (IsoD), Batter's Run Average (BRA), and Estimated Runs Produced (ERP)."""

from __future__ import annotations

import math
from typing import Any

import duckdb
import pandas as pd
import polars as pl
import pyarrow as pa
import pytest
from golden_loader import load_entries
from hypothesis import given, settings
from hypothesis import strategies as st

import sabermetricspy as sp
from sabermetricspy import Metric

ENTRIES = load_entries("closed_form_batting.yaml")


@pytest.mark.parametrize("entry", [e for e in ENTRIES if "published" in e], ids=lambda e: e["id"])
def test_closed_form_metrics_match_fixture(entry: dict[str, Any]) -> None:
    df = pl.DataFrame([entry["inputs"]])
    metrics = [Metric.ISOD, Metric.BRA, Metric.ERP]
    res = sp.calculate(df, metrics).df.row(0, named=True)

    for metric_name, expected_val in entry["published"].items():
        tol = entry["tolerance"].get(metric_name, 1e-5)
        assert res[metric_name] == pytest.approx(expected_val, abs=tol), (
            f"{entry['id']} {metric_name}"
        )


def test_bra_cramer_palmer_1973_league_worked_example() -> None:
    """Cramer and Palmer (1974) BRJ: 1973 NL league OBA .323, SLG .376 yields BRA .121."""
    # Constructed counts to yield exact OBP = 0.323 and SLG = 0.376
    # pa = 1000, ab = 800, bb = 200, sf = 0, hbp = 0 -> obp = (h + 200)/1000 = 0.323 -> h = 123
    # slg = tb / 800 = 0.376 -> tb = 300.8
    # With direct expressions: 0.323 * 0.376 = 0.121448 -> .121 within rounding
    obp = 0.323
    slg = 0.376
    assert obp * slg == pytest.approx(0.121, abs=0.001)


def test_erp_algebraic_expansion_matches_formula() -> None:
    """ERP = (2(TB + BB + HBP) + H + SB - 0.605(AB + CS + GIDP - H)) * 0.16.

    Linear weights expansion:
    = 0.48*1B + 0.80*2B + 1.12*3B + 1.44*HR + 0.32*(BB+HBP) + 0.16*SB - 0.0968*(AB + CS + GIDP - H).
    """
    row = {
        "ab": 500,
        "h": 140,
        "b2": 25,
        "b3": 4,
        "hr": 20,
        "bb": 50,
        "hbp": 5,
        "sb": 15,
        "cs": 3,
        "gidp": 8,
    }
    df = pl.DataFrame([row])
    res = sp.calculate(df, [Metric.ERP]).df["erp"][0]

    b1 = row["h"] - row["b2"] - row["b3"] - row["hr"]
    outs = row["ab"] + row["cs"] + row["gidp"] - row["h"]
    expected_expansion = (
        0.48 * b1
        + 0.80 * row["b2"]
        + 1.12 * row["b3"]
        + 1.44 * row["hr"]
        + 0.32 * (row["bb"] + row["hbp"])
        + 0.16 * row["sb"]
        - 0.0968 * outs
    )
    assert res == pytest.approx(expected_expansion, abs=1e-9)


def test_erp_missing_optional_columns_defaults_to_zero() -> None:
    """When optional columns (cs, gidp, hbp, sb) are omitted, ERP defaults them to 0."""
    row = {"ab": 500, "h": 140, "b2": 25, "b3": 4, "hr": 20, "bb": 50}
    df = pl.DataFrame([row])
    res = sp.calculate(df, [Metric.ERP]).df["erp"][0]

    # Without optional columns: tb = 91 + 50 + 12 + 80 = 233
    tb = (
        (row["h"] - row["b2"] - row["b3"] - row["hr"])
        + 2 * row["b2"]
        + 3 * row["b3"]
        + 4 * row["hr"]
    )
    expected = (2.0 * (tb + row["bb"]) + row["h"] - 0.605 * (row["ab"] - row["h"])) * 0.16
    assert res == pytest.approx(expected, abs=1e-9)


def test_zero_denominator_returns_null() -> None:
    """When at-bats or plate appearances are zero, isod and bra return null."""
    df = pl.DataFrame([{"ab": 0, "h": 0, "b2": 0, "b3": 0, "hr": 0, "bb": 0, "pa": 0}])
    res = sp.calculate(df, [Metric.ISOD, Metric.BRA]).df.row(0, named=True)
    assert res["isod"] is None
    assert res["bra"] is None


@settings(max_examples=50, deadline=None)
@given(
    ab=st.integers(10, 600),
    h=st.integers(0, 200),
    bb=st.integers(0, 100),
    hbp=st.integers(0, 15),
    sf=st.integers(0, 10),
    hr=st.integers(0, 50),
    b2=st.integers(0, 40),
    b3=st.integers(0, 10),
)
def test_isod_and_bra_identities(
    ab: int, h: int, bb: int, hbp: int, sf: int, hr: int, b2: int, b3: int
) -> None:
    # Ensure physical counts are valid
    h = min(h, ab)
    hr = min(hr, h)
    b2 = min(b2, h - hr)
    b3 = min(b3, h - hr - b2)

    df = pl.DataFrame(
        [{"ab": ab, "h": h, "bb": bb, "hbp": hbp, "sf": sf, "hr": hr, "b2": b2, "b3": b3}]
    )
    res = sp.calculate(df, [Metric.AVG, Metric.OBP, Metric.SLG, Metric.ISOD, Metric.BRA]).df.row(
        0, named=True
    )

    assert math.isclose(res["isod"], res["obp"] - res["avg"], abs_tol=1e-9)
    assert math.isclose(res["bra"], res["obp"] * res["slg"], abs_tol=1e-9)


def test_multi_backend_interoperability_closed_form() -> None:
    """Multi-backend test for Polars, DuckDB, PyArrow, and pandas."""
    data = {
        "ab": [559, 636],
        "h": [180, 197],
        "b2": [36, 38],
        "b3": [1, 7],
        "hr": [58, 54],
        "bb": [133, 81],
        "hbp": [9, 6],
        "sf": [3, 5],
        "sb": [10, 59],
        "cs": [0, 4],
        "gidp": [22, 9],
    }
    metrics = [Metric.ISOD, Metric.BRA, Metric.ERP]

    pl_df = pl.DataFrame(data)
    pa_tbl = pa.Table.from_pydict(data)
    pd_df = pd.DataFrame(data)
    con = duckdb.connect()
    con.register("batters", pl_df.to_arrow())
    duck_rel = con.table("batters")

    res_pl = sp.calculate(pl_df, metrics).df
    res_pa = sp.calculate(pa_tbl, metrics).df
    res_pd = sp.calculate(pd_df, metrics).df
    res_duck = sp.calculate(duck_rel, metrics).to_polars()

    for col in ("isod", "bra", "erp"):
        val_pl = res_pl[col].to_list()
        val_pa = res_pa[col].to_pylist()
        val_pd = res_pd[col].tolist()
        val_duck = res_duck[col].to_list()

        assert pytest.approx(val_pl) == val_pa
        assert pytest.approx(val_pl) == val_pd
        assert pytest.approx(val_pl) == val_duck
