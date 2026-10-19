"""One call applies one season's constants, so a frame with several seasons must be rejected."""

from __future__ import annotations

import polars as pl
import pytest

import sabermetricspy as sp
from sabermetricspy.types import Metric
from sabermetricspy.types.context import SeasonContext

_LINE = dict(pa=600, ab=520, h=160, b2=30, b3=2, hr=30, bb=60, ibb=3, hbp=5, sf=4, sh=0, so=100)


def _two_seasons() -> pl.DataFrame:
    return pl.DataFrame(
        [dict(player_id=1, season=2001, **_LINE), dict(player_id=1, season=2024, **_LINE)]
    )


def test_context_metric_on_several_seasons_raises() -> None:
    with pytest.raises(ValueError, match="more than one season"):
        sp.calculate(
            _two_seasons(),
            [Metric.WRC_PLUS],
            by=["player_id", "season"],
            context=SeasonContext(season=2024),
        )


def test_context_free_metric_on_several_seasons_is_allowed() -> None:
    res = sp.calculate(_two_seasons(), [Metric.AVG], by=["player_id", "season"])
    assert res.df.height == 2


def test_context_metric_one_season_at_a_time_still_works() -> None:
    df = _two_seasons().filter(pl.col("season") == 2001)
    res = sp.calculate(df, [Metric.WRC_PLUS], context=SeasonContext(season=2001))
    assert res.df.height == 1
