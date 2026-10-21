"""xFIP, Game Score 2.0, Shutdowns and Meltdowns against FanGraphs leaderboards and game logs (retrieved 2026-10-21).

Sources: baseballr fg_pitcher_leaders (xFIP; 138 pitcher-seasons with 100 or more IP, six per season 2002-2025) and
fg_pitcher_game_logs (55 starts by Chris Sale and Tarik Skubal in 2023 and 2024 with GSv2; 235 relief appearances by four
2024 relievers with WPA, SD and MD).
"""

from __future__ import annotations

from pathlib import Path
from typing import cast

import polars as pl
import pytest

import sabermetricspy as sp
from sabermetricspy import Metric
from sabermetricspy.types.context import SeasonContext

GOLDEN = Path(__file__).parent / "golden"
XFIP = pl.read_csv(GOLDEN / "fg_pitching_xfip.csv")
STARTS = pl.read_csv(GOLDEN / "fg_game_score_v2.csv")
RELIEF = pl.read_csv(GOLDEN / "fg_shutdown_meltdown.csv")


def test_xfip_matches_the_fangraphs_leaderboard() -> None:
    errors: list[float] = []
    for (season,), sub in XFIP.group_by("season"):
        got = sp.calculate(
            sub.drop("pub_xfip", "player"),
            [Metric.XFIP],
            context=SeasonContext(season=cast(int, season)),
        ).df["xfip"]
        errors += (got - sub["pub_xfip"]).abs().to_list()
    assert len(errors) == 138
    assert max(errors) < 0.001
    assert sum(errors) / len(errors) < 0.0005


def _game_scores() -> pl.Series:
    frame = STARTS.select("outs", "so", "bb", "h", "hr", "r")
    return sp.calculate(frame, [Metric.GAME_SCORE_V2]).df["game_score_v2"]


def test_game_score_v2_is_within_one_point_of_fangraphs() -> None:
    """Tango's formula; FanGraphs' GSv2 equals it on 21 of 55 starts and is one point lower on the other 34 (cause unknown)."""
    diff = _game_scores() - STARTS["gsv2"]
    assert set(diff.to_list()) <= {0, 1}
    assert (diff == 0).sum() == 21


def test_shutdowns_and_meltdowns_match_every_appearance() -> None:
    frame = RELIEF.select(pl.col("wpa").alias("game_wpa"), pl.lit(1).alias("is_reliever"))
    out = sp.calculate(frame, [Metric.SHUTDOWN, Metric.MELTDOWN]).df
    assert out["shutdown"].to_list() == RELIEF["sd"].to_list()
    assert out["meltdown"].to_list() == RELIEF["md"].to_list()


@pytest.mark.parametrize(
    ("player", "sd", "md"),
    [
        ("Pedro Avila", 7, 5),
        ("Ryan Yarbrough", 11, 9),
        ("Derek Law", 23, 14),
        ("Luke Weaver", 25, 6),
    ],
)
def test_season_counts_equal_the_leaderboard(player: str, sd: int, md: int) -> None:
    rows = RELIEF.filter(pl.col("player") == player)
    frame = rows.select(pl.col("wpa").alias("game_wpa"), pl.lit(1).alias("is_reliever"))
    out = sp.calculate(frame, [Metric.SHUTDOWN, Metric.MELTDOWN]).df
    assert (out["shutdown"].sum(), out["meltdown"].sum()) == (sd, md)
