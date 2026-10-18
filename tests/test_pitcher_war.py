"""Pitcher WAR follows the documented FanGraphs method (library page and the Stroman 2016 worked example)."""

from __future__ import annotations

import math
from typing import Any

import polars as pl
import pytest

import sabermetricspy as sp
from sabermetricspy.constants import get_pitcher_war_constants
from sabermetricspy.types.context import SeasonContext


def reference_war(
    season: int,
    league: str,
    fip_park_factor: float,
    *,
    ip: float,
    g: int,
    gs: int,
    hr: int,
    bb: int,
    hbp: int,
    so: int,
    iffb: int = 0,
    gmli: float = 1.0,
    correction_per_ip: float = 0.0,
) -> dict[str, float]:
    """Scalar transcription of the FanGraphs 'WAR for Pitchers' steps (independent of the library code)."""
    c = get_pitcher_war_constants(season)
    mlb = c.mlb
    lg_era = 9 * mlb.er / (mlb.outs / 3)
    lg_ra9 = 9 * mlb.r / (mlb.outs / 3)
    const = lg_era - (13 * mlb.hr + 3 * (mlb.bb + mlb.hbp) - 2 * (mlb.so + (mlb.iffb or 0))) / (
        mlb.outs / 3
    )
    if_fip = (13 * hr + 3 * (bb + hbp) - 2 * (so + iffb)) / ip + const
    fipr9 = if_fip + (lg_ra9 - lg_era)
    pfipr9 = fipr9 / (fip_park_factor / 100)
    env = c.al if league == "AL" else c.nl if league == "NL" else mlb
    lg_fipr9 = (
        (13 * env.hr + 3 * (env.bb + env.hbp) - 2 * (env.so + (env.iffb or 0))) / (env.outs / 3)
        + const
        + (lg_ra9 - lg_era)
    )
    raap9 = lg_fipr9 - pfipr9
    ip_per_g = ip / g
    drpw = (((18 - ip_per_g) * lg_fipr9 + ip_per_g * pfipr9) / 18 + 2) * 1.5
    replacement = 0.03 * (1 - gs / g) + 0.12 * (gs / g)
    war = (raap9 / drpw + replacement) * ip / 9
    if gs == 0:
        war *= (1 + gmli) / 2
    return {
        "if_fip": if_fip,
        "fipr9": fipr9,
        "pfipr9": pfipr9,
        "lg_fipr9": lg_fipr9,
        "raap9": raap9,
        "drpw": drpw,
        "war": war + correction_per_ip * ip,
        "rar": (raap9 + replacement * drpw) * ip / 9,
    }


def _frame(rows: list[dict[str, Any]]) -> pl.DataFrame:
    return pl.DataFrame(rows)


STROMAN = dict(outs=612, g=32, gs=32, hr=21, bb=54, hbp=4, so=166, iffb=7, gmli=0.9)


def test_stroman_2016_worked_example() -> None:
    ctx = SeasonContext(season=2016, league="AL", park_factor=101.0)
    out = sp.WARFramework(ctx).calculate_pitcher_war_df(
        _frame([{"player_id": "stroman", **STROMAN}])
    )
    row = out.row(0, named=True)
    # Values quoted on FanGraphs' "Calculating Pitcher WAR, A Complete Example" (rounded by the page).
    assert math.isclose(row["pitcher_if_fip"], 3.84, abs_tol=0.01)
    assert math.isclose(row["pitcher_fipr9"], 4.17, abs_tol=0.01)
    assert math.isclose(row["pitcher_pfipr9"], 4.12, abs_tol=0.01)
    assert math.isclose(row["pitcher_raap9"], 0.44, abs_tol=0.01)
    assert math.isclose(row["pitcher_drpw"], 9.61, abs_tol=0.01)
    # WAR before correction is 3.76 from the page's rounded steps; after the 2016 correction the page's
    # unrounded result is about 3.62.
    pre = row["pitcher_war"] - (-0.000682902 * 204)
    assert math.isclose(pre, 3.76, abs_tol=0.03)
    assert math.isclose(row["pitcher_war"], 3.62, abs_tol=0.03)


def test_matches_independent_reference_for_starters_relievers_and_mixed_roles() -> None:
    rows: list[dict[str, Any]] = [
        dict(
            player_id="starter_nl",
            league="NL",
            fip_park_factor=97.0,
            outs=548,
            g=33,
            gs=33,
            hr=22,
            bb=83,
            hbp=5,
            so=147,
            iffb=18,
            gmli=0.87,
        ),
        dict(
            player_id="reliever_al",
            league="AL",
            fip_park_factor=103.0,
            outs=201,
            g=69,
            gs=0,
            hr=1,
            bb=18,
            hbp=0,
            so=74,
            iffb=0,
            gmli=1.66,
        ),
        dict(
            player_id="mixed_nl",
            league="NL",
            fip_park_factor=99.0,
            outs=440,
            g=35,
            gs=20,
            hr=23,
            bb=46,
            hbp=7,
            so=105,
            iffb=4,
            gmli=0.71,
        ),
    ]
    out = sp.WARFramework(season=2016).calculate_pitcher_war_df(_frame(rows))
    for i, r in enumerate(rows):
        ref = reference_war(
            2016,
            r["league"],
            r["fip_park_factor"],
            ip=r["outs"] / 3,
            g=r["g"],
            gs=r["gs"],
            hr=r["hr"],
            bb=r["bb"],
            hbp=r["hbp"],
            so=r["so"],
            iffb=r["iffb"],
            gmli=r["gmli"],
            correction_per_ip=-0.000682902,
        )
        row = out.row(i, named=True)
        assert math.isclose(row["pitcher_war"], ref["war"], abs_tol=1e-9), r["player_id"]
        assert math.isclose(row["pitcher_rar"], ref["rar"], abs_tol=1e-9), r["player_id"]
        assert math.isclose(row["pitcher_drpw"], ref["drpw"], abs_tol=1e-9), r["player_id"]
        assert math.isclose(row["pitcher_if_fip"], ref["if_fip"], abs_tol=1e-9), r["player_id"]


def test_reliever_replacement_and_leverage_multiplier() -> None:
    base = dict(player_id="rp", outs=201, g=69, gs=0, hr=1, bb=18, hbp=0, so=74, iffb=0)
    ctx = SeasonContext(season=2016, league="AL", park_factor=103.0)
    low = sp.WARFramework(ctx).calculate_pitcher_war_df(_frame([{**base, "gmli": 1.0}]))[
        "pitcher_war"
    ][0]
    high = sp.WARFramework(ctx).calculate_pitcher_war_df(_frame([{**base, "gmli": 2.0}]))[
        "pitcher_war"
    ][0]

    def uncorrected(w: float) -> float:
        return w + 0.000682902 * 67  # remove the 2016 correction

    assert math.isclose(
        uncorrected(high) / uncorrected(low), (1 + 2.0) / 2 / ((1 + 1.0) / 2), rel_tol=1e-9
    )


def test_league_and_park_factor_are_taken_per_row() -> None:
    base = dict(outs=540, g=30, gs=30, hr=18, bb=40, hbp=5, so=160, iffb=8, gmli=0.9)
    rows: list[dict[str, Any]] = [
        {"player_id": "a", "league": "AL", "fip_park_factor": 95.0, **base},
        {"player_id": "b", "league": "NL", "fip_park_factor": 105.0, **base},
    ]
    out = sp.WARFramework(season=2016).calculate_pitcher_war_df(_frame(rows))
    assert out["pitcher_war"][0] != out["pitcher_war"][1]
    for i, r in enumerate(rows):
        ref = reference_war(
            2016,
            r["league"],
            r["fip_park_factor"],
            ip=180.0,
            g=30,
            gs=30,
            hr=18,
            bb=40,
            hbp=5,
            so=160,
            iffb=8,
            correction_per_ip=-0.000682902,
        )
        assert math.isclose(out["pitcher_war"][i], ref["war"], abs_tol=1e-9)


def test_context_league_and_park_factor_are_the_defaults() -> None:
    ctx = SeasonContext(season=2016, league="NL", park_factor=99.0)
    from_ctx = sp.WARFramework(ctx).calculate_pitcher_war_df(
        _frame([{"player_id": "x", **STROMAN}])
    )["pitcher_war"][0]
    from_cols = sp.WARFramework(season=2016).calculate_pitcher_war_df(
        _frame([{"player_id": "x", "league": "NL", "fip_park_factor": 99.0, **STROMAN}])
    )["pitcher_war"][0]
    assert math.isclose(from_ctx, from_cols, abs_tol=1e-12)


def test_league_correction_is_applied_only_where_published_or_supplied() -> None:
    row = {"player_id": "x", **STROMAN}
    with_2016 = sp.WARFramework(season=2016).calculate_pitcher_war_df(_frame([row]))["pitcher_war"][
        0
    ]
    without = sp.WARFramework(season=2016).calculate_pitcher_war_df(
        _frame([row]), league_correction_per_ip=0.0
    )["pitcher_war"][0]
    assert math.isclose(with_2016 - without, -0.000682902 * 204, abs_tol=1e-9)
    custom = sp.WARFramework(season=2016).calculate_pitcher_war_df(
        _frame([row]), league_correction_per_ip=-0.001
    )["pitcher_war"][0]
    assert math.isclose(custom - without, -0.001 * 204, abs_tol=1e-9)
    # 2024 has no bundled correction: the default equals the explicit zero.
    d_default = sp.WARFramework(season=2024).calculate_pitcher_war_df(_frame([row]))["pitcher_war"][
        0
    ]
    d_zero = sp.WARFramework(season=2024).calculate_pitcher_war_df(
        _frame([row]), league_correction_per_ip=0.0
    )["pitcher_war"][0]
    assert d_default == d_zero


def test_missing_required_columns_are_reported() -> None:
    row = {k: v for k, v in {"player_id": "x", **STROMAN}.items() if k != "g"}
    with pytest.raises(ValueError, match="g"):
        sp.WARFramework(season=2016).calculate_pitcher_war_df(_frame([row]))


def test_optional_columns_default_sensibly() -> None:
    minimal = {k: v for k, v in {"player_id": "x", **STROMAN}.items() if k not in ("iffb", "gmli")}
    out = sp.WARFramework(season=2016).calculate_pitcher_war_df(_frame([minimal]))
    ref = reference_war(
        2016,
        "MLB",
        100.0,
        ip=204.0,
        g=32,
        gs=32,
        hr=21,
        bb=54,
        hbp=4,
        so=166,
        correction_per_ip=-0.000682902,
    )
    assert math.isclose(out["pitcher_war"][0], ref["war"], abs_tol=1e-9)


def test_docstring_names_the_published_method_and_its_limits() -> None:
    doc = sp.WARFramework.calculate_pitcher_war_df.__doc__ or ""
    assert "FanGraphs" in doc and "worked example" in doc
    assert "separately" in doc
