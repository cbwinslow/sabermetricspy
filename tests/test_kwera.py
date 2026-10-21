"""kwERA constant measured from the FanGraphs pitcher API (retrieved 2026-10-18; recomputed here)."""

from __future__ import annotations

import polars as pl
import pytest

import sabermetricspy as sp
from sabermetricspy import Metric
from sabermetricspy.types.context import SeasonContext

# season, pitcher, TBF, SO, BB, FanGraphs kwERA
ROWS = [
    (2001, "Randy Johnson", 994, 372, 71, 1.8489746832511802),
    (2001, "Curt Schilling", 1021, 293, 39, 2.4974689790948021),
    (2016, "Jose Fernandez", 737, 253, 55, 2.519444541077116),
    (2016, "Max Scherzer", 902, 284, 56, 2.7100657145887155),
    (2017, "Chris Sale", 851, 308, 43, 2.1935179745128375),
    (2018, "Jacob deGrom", 835, 269, 46, 2.5989318670626886),
    (2019, "Gerrit Cole", 817, 326, 48, 2.154706497729336),
    (2020, "Shane Bieber", 297, 122, 21, 2.085502372606836),
    (2021, "Corbin Burnes", 657, 234, 34, 2.4999418622282548),
    (2022, "Aaron Nola", 807, 235, 29, 2.7921471741119728),
    (2023, "Zack Wheeler", 787, 212, 39, 3.5808662350932106),
    (2024, "Tarik Skubal", 753, 228, 35, 2.8902615271716483),
    (2025, "Tarik Skubal", 748, 241, 33, 2.7086101320338125),
    (2026, "Jacob Misiorowski", 665, 252, 44, 2.3113125195180566),
    (2026, "Chris Sale", 648, 200, 31, 2.9350663485350434),
]


@pytest.mark.parametrize(("season", "name", "tbf", "so", "bb", "published"), ROWS)
def test_kwera_matches_fangraphs(
    season: int, name: str, tbf: int, so: int, bb: int, published: float
) -> None:
    df = pl.DataFrame({"player_id": [name], "so": [so], "bb": [bb], "bf": [tbf]})
    out = sp.calculate(df, [Metric.KWERA], context=SeasonContext(season=season))
    assert out.df["kwera"][0] == pytest.approx(published, abs=1e-4)
