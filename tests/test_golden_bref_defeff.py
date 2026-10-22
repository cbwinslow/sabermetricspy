"""Defensive efficiency against Baseball-Reference's team DefEff, all 30 teams of 2016 (retrieved 2026-10-21).

Counts are by fielding team from Retrosheet 2016 play-by-play, with reached-on-error counted from event code 18
(tests/golden/bref_defeff_2016.csv); the published column is Baseball-Reference's team fielding table
(https://www.baseball-reference.com/leagues/majors/2016.shtml). Baseball-Reference estimates reached-on-error as 0.71
times errors and averages two estimates, so the library, which counts it, sits a little above the published value.
"""

from __future__ import annotations

from pathlib import Path
from typing import cast

import polars as pl

import sabermetricspy as sp
from sabermetricspy import Metric

TEAMS = pl.read_csv(Path(__file__).parent / "golden" / "bref_defeff_2016.csv")


def _gap() -> pl.Series:
    got = sp.calculate(TEAMS, [Metric.DER]).df["der"]
    return got - TEAMS["pub_defeff"]


def test_every_team_is_within_half_a_percentage_point() -> None:
    gap = _gap()
    assert TEAMS.height == 30
    assert cast(float, gap.abs().max()) < 0.005


def test_the_library_sits_above_the_published_value_by_about_a_quarter_point() -> None:
    gap = _gap()
    assert 0.002 < cast(float, gap.mean()) < 0.003
    assert (gap > -0.001).all()
