"""Tie-outs against real baseballr output (fixture made by tools/baseballr_golden.R; provenance is inside the JSON)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import polars as pl
import pytest

import sabermetricspy as sp
from sabermetricspy.constants import bundled_constants
from sabermetricspy.types import Metric

FIXTURE = Path(__file__).parent / "golden" / "baseballr" / "baseballr_tieout.json"
DATA: dict[str, Any] = json.loads(FIXTURE.read_text(encoding="utf-8"))

GUTS_FIELDS = {
    "lg_woba": "lg_woba",
    "woba_scale": "woba_scale",
    "wBB": "w_bb",
    "wHBP": "w_hbp",
    "w1B": "w_1b",
    "w2B": "w_2b",
    "w3B": "w_3b",
    "wHR": "w_hr",
    "runSB": "r_sb",
    "runCS": "r_cs",
    "lg_r_pa": "lg_r_per_pa",
    "lg_r_w": "lg_r_per_w",
    "cFIP": "c_fip",
}


def test_fixture_records_where_it_came_from() -> None:
    prov = DATA["provenance"]
    assert prov["package"] == "baseballr" and prov["version"] and prov["run_date"]
    assert "fg_guts()" in prov["calls"]


def test_bundled_constants_equal_baseballr_fg_guts() -> None:
    ours = bundled_constants()
    by_season = {row["season"]: row for row in DATA["guts"]}
    assert set(ours) <= set(by_season), "bundled seasons missing from baseballr fg_guts()"
    diffs: list[str] = []
    for season, weights in ours.items():
        for r_name, our_name in GUTS_FIELDS.items():
            if getattr(weights, our_name) != pytest.approx(by_season[season][r_name], abs=1e-9):
                diffs.append(
                    f"{season}.{our_name}: ours {getattr(weights, our_name)} vs baseballr {by_season[season][r_name]}"
                )
    assert not diffs, "\n".join(diffs)


def test_woba_matches_baseballr_woba_plus() -> None:
    for row in DATA["batters"]:
        hits = row["X1B"] + row["X2B"] + row["X3B"] + row["HR"]
        df = pl.DataFrame(
            {
                "ab": [row["AB"]],
                "h": [hits],
                "b1": [row["X1B"]],
                "b2": [row["X2B"]],
                "b3": [row["X3B"]],
                "hr": [row["HR"]],
                "bb": [row["uBB"] + row["IBB"]],
                "ibb": [row["IBB"]],
                "hbp": [row["HBP"]],
                "sf": [row["SF"]],
                "pa": [row["AB"] + row["uBB"] + row["IBB"] + row["HBP"] + row["SF"]],
            }
        )
        got = sp.calculate(df, [Metric.WOBA], season=row["season"]).df["woba"][0]
        # baseballr rounds wOBA to 3 decimals
        assert got == pytest.approx(row["wOBA"], abs=0.0005 + 1e-9), row["id"]


def test_fip_matches_baseballr_fip_plus() -> None:
    for row in DATA["pitchers"]:
        df = pl.DataFrame(
            {
                "outs": [row["outs"]],
                "hr": [row["HR"]],
                "bb": [row["BB"]],
                "ibb": [row["IBB"]],
                "hbp": [row["HBP"]],
                "so": [row["SO"]],
            }
        )
        got = sp.calculate(df, [Metric.FIP], season=row["season"]).df["fip"][0]
        # baseballr rounds FIP to 2 decimals
        assert got == pytest.approx(row["FIP"], abs=0.005 + 1e-9), row["id"]
