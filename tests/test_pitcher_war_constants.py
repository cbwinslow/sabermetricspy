"""The pitcher-WAR constants loader reproduces the FanGraphs worked-example constants."""

from __future__ import annotations

import math
import warnings

import pytest

from sabermetricspy import constants
from sabermetricspy.constants import get_pitcher_war_constants


def test_2016_constants_reproduce_the_worked_example() -> None:
    c = get_pitcher_war_constants(2016)
    # FanGraphs page: lgERA 4.19, lgRA9 4.52, ifFIP constant 3.34, RA9 adjustment 0.33, AL ifFIP 4.23.
    assert round(c.lg_era, 2) == 4.19
    assert round(c.lg_ra9, 2) == 4.52
    assert round(c.iffip_constant, 2) == 3.34
    assert round(c.ra9_minus_era, 2) == 0.33
    al_iffip = c.al.iffip_numerator / c.al.ip + c.iffip_constant
    assert round(al_iffip, 2) == 4.23
    assert round(c.league_fipr9("AL"), 2) == 4.56
    assert math.isclose(c.mlb.ip, 43306.33, abs_tol=0.01)
    assert c.war_ip_correction == -0.000682902


def test_mlb_league_fip_equals_league_ra9_by_construction() -> None:
    for season in (2001, 2016, 2024):
        c = get_pitcher_war_constants(season)
        assert math.isclose(c.league_fipr9("MLB"), c.lg_ra9, abs_tol=1e-9), season


def test_infield_flies_are_zero_before_2002() -> None:
    c = get_pitcher_war_constants(2001)
    assert c.al.iffb is None and c.nl.iffb is None
    expected = c.lg_era - (13 * c.mlb.hr + 3 * (c.mlb.bb + c.mlb.hbp) - 2 * c.mlb.so) / c.mlb.ip
    assert math.isclose(c.iffip_constant, expected, abs_tol=1e-12)


def test_only_2016_has_a_published_correction() -> None:
    corrected = [
        s for s in range(1990, 2026) if get_pitcher_war_constants(s).war_ip_correction is not None
    ]
    assert corrected == [2016]


def test_missing_season_raises_instead_of_borrowing_another() -> None:
    with pytest.raises(constants.ConstantsNotFoundError, match=r"1975.*covers"):
        get_pitcher_war_constants(1975)


def test_bundled_season_does_not_warn() -> None:
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        assert get_pitcher_war_constants(2016).season == 2016
