"""Metric definitions must follow the published method (FanGraphs FIP/xFIP walk term, xFIP league HR/FB)."""

from __future__ import annotations

import math

import polars as pl
import pytest

import sabermetricspy as sp
from sabermetricspy import Metric
from sabermetricspy.constants import get_woba_weights
from sabermetricspy.registry import REGISTRY
from sabermetricspy.types.context import SeasonContext

# FanGraphs leaderboard rows (retrieved 2026-10-18 from the FanGraphs leaders API).
# (name, season, outs, hr, bb, ibb, hbp, so, published FIP)
FIP_ROWS = [
    ("Johnson", 2001, 749, 19, 71, 2, 18, 372, 2.1279085437378074),
    ("Schilling", 2001, 770, 37, 39, 0, 1, 293, 3.1075783901340066),
    ("Mussina", 2001, 686, 20, 42, 2, 4, 214, 2.917941497017448),
    ("Maddux", 2001, 699, 20, 27, 10, 7, 173, 3.1178063527761619),
    ("Morris", 2001, 649, 13, 54, 3, 13, 185, 3.0491368293762213),
    ("Bradley", 2016, 425, 16, 67, 8, 4, 143, 4.0995015251001288),
    ("Koehler", 2016, 530, 22, 83, 7, 5, 147, 4.59561694489802),
    ("Conley", 2016, 400, 13, 62, 7, 11, 124, 4.1965603027343814),
    ("Perdomo", 2016, 440, 23, 46, 7, 7, 105, 4.8374693491439285),
    ("Fernandez", 2016, 547, 13, 55, 6, 6, 253, 2.3019534829807822),
]

# cFIP is published to three decimals, so FIP reproduces to within about 0.0005.
FIP_TOL = 5e-4


def _line(outs: int, hr: int, bb: int, ibb: int, hbp: int, so: int, **extra: int) -> pl.DataFrame:
    return pl.DataFrame(
        {
            "player_id": ["p"],
            "outs": [outs],
            "hr": [hr],
            "bb": [bb],
            "ibb": [ibb],
            "hbp": [hbp],
            "so": [so],
            **{k: [v] for k, v in extra.items()},
        }
    )


@pytest.mark.parametrize(
    ("name", "season", "outs", "hr", "bb", "ibb", "hbp", "so", "published"), FIP_ROWS
)
def test_fip_matches_fangraphs_including_intentional_walks(
    name: str,
    season: int,
    outs: int,
    hr: int,
    bb: int,
    ibb: int,
    hbp: int,
    so: int,
    published: float,
) -> None:
    res = sp.calculate(_line(outs, hr, bb, ibb, hbp, so), [Metric.FIP], season=season)
    fip = res.df["fip"][0]
    assert math.isclose(fip, published, abs_tol=FIP_TOL), (
        f"{name} {season}: {fip} vs FanGraphs {published}"
    )


def test_maddux_2001_documents_the_intentional_walk_effect() -> None:
    """Excluding his 10 IBB would give 2.989; FanGraphs (and now the library) report 3.118."""
    res = sp.calculate(_line(699, 20, 27, 10, 7, 173), [Metric.FIP], season=2001)
    assert res.df["fip"][0] > 3.1


def test_fip_identical_with_and_without_ibb_column_when_no_intentional_walks() -> None:
    with_ibb = sp.calculate(_line(770, 37, 39, 0, 1, 293), [Metric.FIP], season=2001).df["fip"][0]
    without = sp.calculate(_line(770, 37, 39, 0, 1, 293).drop("ibb"), [Metric.FIP], season=2001).df[
        "fip"
    ][0]
    assert with_ibb == without


def test_xfip_is_null_for_seasons_without_a_published_league_hr_fb() -> None:
    res = sp.calculate(_line(749, 19, 71, 2, 18, 372, fb=300), [Metric.XFIP], season=2001)
    assert res.df["xfip"][0] is None


def test_xfip_uses_league_hr_fb_and_total_walks_when_published() -> None:
    w = get_woba_weights(2016)
    assert w.lg_hr_per_fb is not None
    outs, bb, ibb, hbp, so, fb = 425, 67, 8, 4, 143, 220
    res = sp.calculate(_line(outs, 16, bb, ibb, hbp, so, fb=fb), [Metric.XFIP], season=2016)
    expected = (13 * fb * w.lg_hr_per_fb + 3 * (bb + hbp) - 2 * so) / (outs / 3) + w.c_fip
    assert math.isclose(res.df["xfip"][0], expected, abs_tol=1e-9)


# --- wRC+ ---------------------------------------------------------------------------------------
# FanGraphs leaderboard row for Barry Bonds 2001 (retrieved 2026-10-18).
BONDS_2001 = {
    "player_id": ["bondsba01"],
    "pa": [664],
    "ab": [476],
    "h": [156],
    "b2": [32],
    "b3": [2],
    "hr": [73],
    "bb": [177],
    "ibb": [35],
    "hbp": [9],
    "sf": [2],
    "so": [93],
}
BONDS_PUBLISHED = {
    "woba": 0.536696215217936,
    "wraa": 117.67847717808644,
    "wrc": 200.07072038458745,
    "wrc_plus": 234.58991124906629,
}
# FanGraphs Guts! park factor page, 2001, San Francisco Giants, Basic (5yr) = 96.
GIANTS_2001_PARK_FACTOR = 96.0


def _bonds_context(*, with_np_constant: bool = True) -> SeasonContext:
    weights = get_woba_weights(2001)
    if not with_np_constant:
        weights = weights.model_copy(
            update={"lg_wrc_per_pa": None, "lg_wrc_per_pa_nl": None, "lg_wrc_per_pa_al": None}
        )
    return SeasonContext(
        season=2001, league="NL", park_factor=GIANTS_2001_PARK_FACTOR, weights=weights
    )


def test_bonds_2001_woba_wraa_wrc_match_fangraphs() -> None:
    res = sp.calculate(
        pl.DataFrame(BONDS_2001), [Metric.WOBA, Metric.WRAA, Metric.WRC], context=_bonds_context()
    )
    row = res.df.row(0, named=True)
    # Weights are published to three decimals: wOBA within 2e-5, run totals within 0.2.
    assert math.isclose(row["woba"], BONDS_PUBLISHED["woba"], abs_tol=2e-5)
    assert math.isclose(row["wraa"], BONDS_PUBLISHED["wraa"], abs_tol=0.2)
    assert math.isclose(row["wrc"], BONDS_PUBLISHED["wrc"], abs_tol=0.2)


def test_bonds_2001_wrc_plus_uses_non_pitcher_league_denominator() -> None:
    """Published 234.59. Documented residual: FanGraphs' own AL/NL non-pitcher aggregation and park
    factor are not exactly reproducible from the public leaderboard (about 0.1%), so tolerance is 0.5."""
    res = sp.calculate(pl.DataFrame(BONDS_2001), [Metric.WRC_PLUS], context=_bonds_context())
    got = res.df["wrc_plus"][0]
    assert math.isclose(got, BONDS_PUBLISHED["wrc_plus"], abs_tol=0.5), got


def test_wrc_plus_falls_back_to_league_runs_per_pa_without_the_constant() -> None:
    res = sp.calculate(
        pl.DataFrame(BONDS_2001), [Metric.WRC_PLUS], context=_bonds_context(with_np_constant=False)
    )
    w = get_woba_weights(2001)
    wrc = sp.calculate(pl.DataFrame(BONDS_2001), [Metric.WRC], context=_bonds_context()).df["wrc"][
        0
    ]
    expected = ((wrc / 664) + w.lg_r_per_pa * (1 - 0.96)) / w.lg_r_per_pa * 100
    assert math.isclose(res.df["wrc_plus"][0], expected, abs_tol=1e-9)
    spec = REGISTRY.spec(Metric.WRC_PLUS)
    assert any("R/PA" in c for c in spec.caveats)


def test_default_park_factor_means_no_park_adjustment() -> None:
    ctx = SeasonContext(season=2001, league="NL")
    assert ctx.park_factor == 100.0
    spec = REGISTRY.spec(Metric.WRC_PLUS)
    assert any("park" in c.lower() and "100" in c for c in spec.caveats)
