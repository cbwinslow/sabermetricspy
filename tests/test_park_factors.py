"""Park factor calculation (FanGraphs Library method) and the bundled Guts! 2024 table."""

from __future__ import annotations

import warnings
from pathlib import Path

import pytest
import yaml

import sabermetricspy as sp
from sabermetricspy.value.park import (
    composite_park_factor,
    raw_park_factor,
    regress_park_factor,
)

GUTS = yaml.safe_load(
    (Path(__file__).parent / "golden" / "park_factors_2024.yaml").read_text("utf-8")
)


def test_raw_factor_matches_the_article_formula_and_rounds_to_its_example() -> None:
    """Home 11 and road 10 runs per game with 30 teams: 330/301, which the article prints as 1.10."""
    raw = raw_park_factor(11.0, 10.0, teams=30)
    assert raw == pytest.approx(330 / 301, abs=1e-12)
    assert round(raw, 2) == 1.10
    assert round(composite_park_factor(raw), 2) == 1.05


def test_composite_factor_is_the_midpoint_with_neutral() -> None:
    assert composite_park_factor(1.10) == pytest.approx(1.05)
    assert composite_park_factor(1.0) == 1.0


@pytest.mark.parametrize(
    ("years", "expected"), [(1, 1.15), (2, 1.175), (3, 1.20), (4, 1.225), (5, 1.225)]
)
def test_regression_by_years_matches_the_article(years: int, expected: float) -> None:
    assert regress_park_factor(1.25, years=years) == pytest.approx(expected, abs=1e-12)


def test_neutral_park_stays_neutral() -> None:
    assert raw_park_factor(4.5, 4.5, teams=30) == pytest.approx(1.0)
    assert regress_park_factor(1.0, years=1) == 1.0


def test_invalid_inputs_are_rejected() -> None:
    with pytest.raises(ValueError):
        regress_park_factor(1.1, years=0)
    with pytest.raises(ValueError):
        raw_park_factor(4.0, 0.0, teams=30)


@pytest.mark.full_constants
def test_bundled_table_covers_thirty_teams_and_equals_guts() -> None:
    assert len(GUTS["teams"]) == 30
    for team, row in GUTS["teams"].items():
        pf = sp.get_park_factor(team)
        assert (pf.basic_5yr, pf.basic_1yr, pf.hr_factor) == (
            row["basic_5yr"],
            row["basic_1yr"],
            row["hr"],
        ), team
        assert pf.season == GUTS["season"]


def test_known_park_lookup_by_team() -> None:
    assert sp.get_park_factor("COL").basic_5yr == 112.0
    assert sp.get_park_factor("sea").hr_factor == 96.0


def test_unknown_park_is_neutral_and_warns() -> None:
    with pytest.warns(UserWarning, match="not in the park table"):
        pf = sp.get_park_factor("ZZZ")
    assert pf.basic_5yr == 100.0
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        sp.get_park_factor("BOS")
