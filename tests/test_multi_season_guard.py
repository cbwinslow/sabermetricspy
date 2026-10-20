"""One call applies one season's constants, so a frame with several seasons must be rejected."""

from __future__ import annotations

import warnings

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


def test_single_season_frame_uses_its_own_season() -> None:
    df = _two_seasons().filter(pl.col("season") == 2001)
    res = sp.calculate(df, [Metric.WRC_PLUS])
    assert res.context.season == 2001


def test_frame_season_that_contradicts_the_context_raises() -> None:
    df = _two_seasons().filter(pl.col("season") == 2001)
    with pytest.raises(ValueError, match="holds season 2001"):
        sp.calculate(df, [Metric.WRC_PLUS], context=SeasonContext(season=2024))
    with pytest.raises(ValueError, match="holds season 2001"):
        sp.calculate(df, [Metric.WRC_PLUS], season=2024)


def test_no_season_anywhere_warns_for_constant_metrics_only() -> None:
    df = pl.DataFrame([dict(player_id=1, **_LINE)])
    with pytest.warns(UserWarning, match="use 2024 constants"):
        sp.calculate(df, [Metric.WRC_PLUS])
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        sp.calculate(df, [Metric.AVG])
        sp.calculate(df, [Metric.WRC_PLUS], season=2024)


def _as_backend(df: pl.DataFrame, backend: str) -> object:
    import duckdb

    return {
        "polars": df,
        "lazy": df.lazy(),
        "pandas": df.to_pandas(),
        "pyarrow": df.to_arrow(),
        "duckdb": duckdb.from_arrow(df.to_arrow()),
    }[backend]


BACKENDS = ["polars", "lazy", "pandas", "pyarrow", "duckdb"]


@pytest.mark.parametrize("backend", BACKENDS)
def test_season_inference_and_guard_on_every_backend(backend: str) -> None:
    one = _two_seasons().filter(pl.col("season") == 2001)
    res = sp.calculate(_as_backend(one, backend), [Metric.WRC_PLUS])  # type: ignore[arg-type]
    assert res.context.season == 2001
    sp.calculate(_as_backend(one, backend), [Metric.AVG])  # type: ignore[arg-type]
    sp.calculate(_as_backend(one, backend), [Metric.WRC_PLUS], season=2001)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="holds season 2001"):
        sp.calculate(_as_backend(one, backend), [Metric.WRC_PLUS], season=2024)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="more than one season"):
        sp.calculate(
            _as_backend(_two_seasons(), backend),  # type: ignore[arg-type]
            [Metric.WRC_PLUS],
            by=["player_id", "season"],
            season=2024,
        )


@pytest.mark.parametrize("backend", BACKENDS)
def test_season_column_that_is_not_a_year_is_ignored(backend: str) -> None:
    text = pl.DataFrame([dict(player_id=1, **_LINE)]).with_columns(
        pl.lit("2016-reg").alias("season")
    )
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        sp.calculate(_as_backend(text, backend), [Metric.AVG], by="player_id")  # type: ignore[arg-type]
    with pytest.warns(UserWarning, match="no usable season value"):
        sp.calculate(_as_backend(text, backend), [Metric.WRC_PLUS])  # type: ignore[arg-type]


def test_all_null_and_date_season_columns_warn_accurately() -> None:
    import datetime

    base = pl.DataFrame([dict(player_id=1, **_LINE)])
    nulls = base.with_columns(pl.lit(None, dtype=pl.Int64).alias("season"))
    dates = base.with_columns(pl.lit(datetime.date(2016, 4, 1)).alias("season"))
    for frame in (nulls, dates):
        with pytest.warns(UserWarning, match="no usable season value"):
            sp.calculate(frame, [Metric.WRC_PLUS])


def test_digit_text_and_integral_float_seasons_are_years() -> None:
    one = _two_seasons().filter(pl.col("season") == 2001)
    for frame in (
        one.with_columns(pl.col("season").cast(pl.Utf8)),
        one.with_columns(pl.col("season").cast(pl.Float64)),
    ):
        assert sp.calculate(frame, [Metric.WRC_PLUS]).context.season == 2001


def test_warning_points_at_the_caller_not_the_library() -> None:
    df = pl.DataFrame([dict(player_id=1, **_LINE)])
    for call in (
        lambda: sp.calculate(df, [Metric.WRC_PLUS]),
        lambda: sp.calculate_suite(df, "weighted_offense"),
        lambda: sp.calculate_available(df),
    ):
        with pytest.warns(UserWarning, match="no usable season value") as caught:
            call()
        assert caught[0].filename == __file__


def test_war_framework_warns_without_a_season_or_context() -> None:
    from sabermetricspy.value import WARFramework

    with pytest.warns(UserWarning, match="neither a context nor a season") as caught:
        WARFramework()
    assert caught[0].filename == __file__
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        WARFramework(season=2016)
        WARFramework(SeasonContext(season=2016))
