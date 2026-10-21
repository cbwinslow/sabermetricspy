"""SIERA, FIP- and xFIP- reproduce FanGraphs leaderboard values (fixtures retrieved 2026-10-21)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import polars as pl
import pytest
import yaml

import sabermetricspy as sp
from sabermetricspy.constants import get_woba_weights
from sabermetricspy.types import Metric
from sabermetricspy.types.context import SeasonContext

GOLDEN = Path(__file__).parent / "golden"
SIERA_ROWS: list[dict[str, Any]] = yaml.safe_load(
    (GOLDEN / "siera_fangraphs.yaml").read_text("utf-8")
)["rows"]
FIP_ROWS: list[dict[str, Any]] = yaml.safe_load(
    (GOLDEN / "fip_minus_fangraphs.yaml").read_text("utf-8")
)["rows"]


def _siera(row: dict[str, Any]) -> float:
    frame = pl.DataFrame(
        {k: [row[k]] for k in ("outs", "start_outs", "so", "bb", "gb", "fb")} | {"bf": [row["tbf"]]}
    )
    ctx = SeasonContext(season=row["season"])
    return sp.calculate(frame, [Metric.SIERA], context=ctx).df["siera"][0]


@pytest.mark.parametrize("row", SIERA_ROWS, ids=lambda r: f"{r['player']} {r['season']}")
def test_siera_reproduces_the_fangraphs_leaderboard(row: dict[str, Any]) -> None:
    assert _siera(row) == pytest.approx(row["siera"], abs=0.01)


def test_siera_error_over_the_fixture_is_small() -> None:
    errors = [abs(_siera(r) - r["siera"]) for r in SIERA_ROWS]
    assert max(errors) < 0.002
    assert sum(errors) / len(errors) < 0.004


def test_siera_starter_term_is_a_share_of_innings() -> None:
    base = {"outs": [600], "so": [150], "bb": [40], "gb": [200], "fb": [180], "bf": [800]}
    ctx = SeasonContext(season=2024)
    starter = sp.calculate(pl.DataFrame(base | {"start_outs": [600]}), [Metric.SIERA], context=ctx)
    reliever = sp.calculate(pl.DataFrame(base | {"start_outs": [0]}), [Metric.SIERA], context=ctx)
    assert starter.df["siera"][0] - reliever.df["siera"][0] == pytest.approx(0.367, abs=1e-9)


def test_siera_accepts_fangraphs_start_ip_notation() -> None:
    frame = pl.DataFrame(
        {
            "ip": [100.2],
            "start_ip": [100.1],
            "so": [90],
            "bb": [30],
            "gb": [120],
            "fb": [100],
            "bf": [420],
        }
    )
    out = sp.calculate(frame, [Metric.SIERA], context=SeasonContext(season=2024)).df
    assert out["siera"][0] is not None


def test_siera_is_null_without_a_bundled_constant() -> None:
    """FanGraphs publishes SIERA from 2002; before that there is no constant to use."""
    frame = pl.DataFrame(
        {
            "outs": [600],
            "start_outs": [600],
            "so": [150],
            "bb": [40],
            "gb": [200],
            "fb": [180],
            "bf": [800],
        }
    )
    out = sp.calculate(frame, [Metric.SIERA], context=SeasonContext(season=1995)).df
    assert out["siera"][0] is None


def _fip_family(row: dict[str, Any]) -> tuple[float, float]:
    weights = get_woba_weights(row["season"])
    ctx = SeasonContext(
        season=row["season"],
        league=row["league"],
        park_factor=float(row["pf_fip"]),
        weights=weights,
    )
    frame = pl.DataFrame(
        {
            "outs": [row["outs"]],
            "hr": [row["hr"]],
            "bb": [row["bb"]],
            "hbp": [row["hbp"]],
            "so": [row["so"]],
            "fb": [row["fb"]],
        }
    )
    res = sp.calculate(frame, [Metric.FIP_MINUS, Metric.XFIP_MINUS], context=ctx).df
    return res["fip_minus"][0], res["xfip_minus"][0]


@pytest.mark.parametrize("row", FIP_ROWS, ids=lambda r: f"{r['player']} {r['season']}")
def test_fip_minus_and_xfip_minus_match_fangraphs(row: dict[str, Any]) -> None:
    fip_minus, xfip_minus = _fip_family(row)
    # The FanGraphs park factor is a whole number, which moves FIP- by up to about 0.6 points.
    assert fip_minus == pytest.approx(row["fip_minus"], abs=1.2)
    assert xfip_minus == pytest.approx(row["xfip_minus"], abs=0.001)


def test_fip_minus_error_over_the_fixture() -> None:
    errors = [abs(_fip_family(r)[0] - r["fip_minus"]) for r in FIP_ROWS]
    assert sum(errors) / len(errors) < 0.5


def test_xfip_minus_ignores_the_park_factor() -> None:
    row = FIP_ROWS[0]
    base = _fip_family(row)[1]
    shifted = _fip_family({**row, "pf_fip": 120})[1]
    assert shifted == pytest.approx(base)
