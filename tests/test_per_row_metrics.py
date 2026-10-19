"""Per-game metrics are only valid on one row per game; grouping would sum their inputs first."""

from __future__ import annotations

import polars as pl
import pytest

import sabermetricspy as sp
from sabermetricspy.types import Metric

_START = dict(outs=21, so=8, h=4, er=2, r=2, bb=1, hr=1, game_wpa=0.1, is_reliever=True)


def _two_starts() -> pl.DataFrame:
    return pl.DataFrame([dict(player_id=1, **_START), dict(player_id=1, **_START)])


@pytest.mark.parametrize(
    "metric", [Metric.GAME_SCORE, Metric.GAME_SCORE_V2, Metric.SHUTDOWN, Metric.MELTDOWN]
)
def test_grouping_a_per_game_metric_raises(metric: Metric) -> None:
    with pytest.raises(ValueError, match="one row per game"):
        sp.calculate(_two_starts(), [metric], by="player_id")


def test_per_game_metric_on_one_row_per_game_still_works() -> None:
    res = sp.calculate(_two_starts(), [Metric.GAME_SCORE])
    # 50 + 21 outs + 2 * (7 - 4) innings + 8 SO - 2 * 4 H - 4 * 2 ER - 2 * 0 unearned - 1 BB = 68
    assert res.df["game_score"].to_list() == [68, 68]


def test_calculate_available_skips_per_game_metrics_when_grouping() -> None:
    res = sp.calculate_available(_two_starts(), by="player_id")
    assert "game_score" not in res.df.columns
    assert "whip" in res.df.columns
