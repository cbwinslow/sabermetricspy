"""FIP- follows the FanGraphs Library formula, the ERA- form with FIP and the pitcher's own league (ADR-0045)."""

from __future__ import annotations

import polars as pl
import pytest

import sabermetricspy as sp
from sabermetricspy.constants import bundled_constants, get_woba_weights
from sabermetricspy.types import Metric
from sabermetricspy.types.context import SeasonContext


def test_fip_minus_uses_the_printed_formula_with_the_own_league_fip() -> None:
    # 100 IP, 60 SO, no HR/BB/HBP, cFIP 3.0: FIP = -2 * 60 / 100 + 3.0 = 1.8.
    weights = get_woba_weights(2014).model_copy(
        update={"c_fip": 3.0, "lg_fip_nl": 3.6, "lg_era_nl": 3.66}
    )
    ctx = SeasonContext(season=2014, league="NL", park_factor=96.0, weights=weights)
    df = pl.DataFrame({"outs": [300], "so": [60], "bb": [0], "hr": [0], "hbp": [0], "ibb": [0]})
    res = sp.calculate(df, [Metric.FIP_MINUS], context=ctx)
    # The NL constant is cFIP + (lgERA - lgFIP) = 3.0 + 0.06, so the NL-constant FIP is 1.86 and
    # FIP- = 100 * 1.86 * (2 - 0.96) / 3.66, the page's 100*(1.77+(1.77-1.77*.96))/3.66 form.
    assert res.df["fip_minus"][0] == pytest.approx(100 * 1.86 * 1.04 / 3.66, abs=1e-9)


@pytest.mark.parametrize("season", sorted(bundled_constants()))
def test_league_fips_average_to_the_published_mlb_league_fip(season: int) -> None:
    from sabermetricspy.constants import _load_pitcher_war_table  # pyright: ignore[reportPrivateUsage]

    w = get_woba_weights(season)
    war = _load_pitcher_war_table()[season]
    assert w.lg_fip is not None and w.lg_fip_al is not None and w.lg_fip_nl is not None
    outs_al, outs_nl = war.al.outs, war.nl.outs
    mean = (w.lg_fip_al * outs_al + w.lg_fip_nl * outs_nl) / (outs_al + outs_nl)
    assert mean == pytest.approx(w.lg_fip, abs=0.01)
