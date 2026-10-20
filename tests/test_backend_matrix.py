"""Every metric and the fitted estimators give the same answer on Polars, LazyFrame, pandas, PyArrow and DuckDB.

Added after a review found that the season check broke every DuckDB call while all tests ran on Polars only. The input
values are arbitrary integers: the test compares backends with each other, not with a published value.
"""

from __future__ import annotations

import math
import time
import warnings
from typing import Any

import duckdb
import polars as pl
import pytest

import sabermetricspy as sp
from sabermetricspy.registry import REGISTRY
from sabermetricspy.types import Metric

BACKENDS = ["lazy", "pandas", "pyarrow", "duckdb"]


def _backend(df: pl.DataFrame, name: str) -> Any:
    return {
        "lazy": df.lazy(),
        "pandas": df.to_pandas(),
        "pyarrow": df.to_arrow(),
        "duckdb": duckdb.from_arrow(df.to_arrow()),
    }[name]


def _to_polars(x: Any) -> pl.DataFrame:
    module = type(x).__module__
    if isinstance(x, pl.DataFrame):
        return x
    if isinstance(x, pl.LazyFrame):
        return x.collect()
    if module.startswith("pandas"):
        return pl.from_pandas(x)
    if module.startswith("pyarrow"):
        return pl.from_arrow(x)  # type: ignore[return-value]
    return pl.from_arrow(x.to_arrow_table())  # type: ignore[return-value]


def _assert_same(a: pl.DataFrame, b: pl.DataFrame, key: str) -> None:
    a, b = a.sort(key), b.sort(key)
    assert a.columns == b.columns
    for col in a.columns:
        if a[col].dtype.is_float() or b[col].dtype.is_float():
            for u, v in zip(
                a[col].cast(pl.Float64).to_list(), b[col].cast(pl.Float64).to_list(), strict=True
            ):
                if u is None or v is None or math.isnan(u) or math.isnan(v):
                    assert (u is None or math.isnan(u)) and (v is None or math.isnan(v)), col
                else:
                    assert u == pytest.approx(v, rel=1e-9), col
        else:
            assert a[col].to_list() == b[col].to_list(), col


def _all_metrics_frame() -> pl.DataFrame:
    columns: set[str] = set()
    for metric in Metric:
        columns |= set(REGISTRY.required_base_columns([metric.value]))
    n = 60
    idx = pl.int_range(0, n, eager=True)
    data = {c: (idx % (7 + (sum(map(ord, c)) % 5))) + 3 for c in sorted(columns)}
    return pl.DataFrame(
        {"player_id": idx.cast(pl.Utf8), "season": pl.repeat(2024, n, eager=True), **data}
    )


@pytest.mark.parametrize("backend", BACKENDS)
def test_every_available_metric_agrees_across_backends(backend: str) -> None:
    frame = _all_metrics_frame()
    ref = sp.calculate_available(frame, season=2024)
    assert (
        len(ref.requested_metrics) >= 130
    )  # the frame carries the inputs of (nearly) every registered metric
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        start = time.perf_counter()
        got = sp.calculate_available(_backend(frame, backend), season=2024)
        out = _to_polars(got.df)
        elapsed = time.perf_counter() - start
    assert got.requested_metrics == ref.requested_metrics
    _assert_same(_to_polars(ref.df), out, "player_id")
    if backend == "duckdb":
        assert "duckdb" in type(got.df).__module__
        assert elapsed < 10.0, (
            f"141 metrics on DuckDB took {elapsed:.1f} s (minutes before ADR-0056)"
        )


@pytest.mark.parametrize("backend", BACKENDS)
def test_grouped_suites_agree_across_backends(backend: str) -> None:
    frame = _all_metrics_frame().with_columns(
        (pl.col("player_id").cast(pl.Int64) % 6).cast(pl.Utf8).alias("team")
    )
    ref = sp.calculate_suite(frame, sp.MetricSuite.WEIGHTED_OFFENSE, by="team", season=2024)
    got = sp.calculate_suite(
        _backend(frame, backend), sp.MetricSuite.WEIGHTED_OFFENSE, by="team", season=2024
    )
    _assert_same(_to_polars(ref.df), _to_polars(got.df), "team")


def _plays(n: int = 2000) -> pl.DataFrame:
    bases = ["---", "1--", "-2-", "--3", "12-", "1-3", "-23", "123"]
    idx = pl.int_range(0, n, eager=True)
    return pl.DataFrame({"idx": idx}).select(
        ((pl.col("idx") % 9) + 1).alias("inning"),
        pl.when(pl.col("idx") % 2 == 0)
        .then(pl.lit("top"))
        .otherwise(pl.lit("bottom"))
        .alias("half_inning"),
        (pl.col("idx") % 3).alias("outs_before"),
        pl.Series([bases[i % 8] for i in range(n)]).alias("base_state_before"),
        ((pl.col("idx") % 7) - 3).alias("home_score_diff_before"),
        ((pl.col("idx") + 1) % 4).alias("outs_after"),
        pl.lit("---").alias("base_state_after"),
        (pl.col("idx") % 5 == 0).cast(pl.Int64).alias("runs_on_play"),
        (pl.col("idx") % 4).alias("runs_rest_of_inning"),
    )


@pytest.mark.parametrize("backend", BACKENDS)
def test_expectancy_models_agree_across_backends(backend: str) -> None:
    plays = _plays()
    native = _backend(plays, backend)
    assert (
        sp.RunExpectancyMatrix().fit(native).results == sp.RunExpectancyMatrix().fit(plays).results
    )
    ref = sp.WinProbabilityModel.from_default().transform(plays)
    got = sp.WinProbabilityModel.from_default().transform(native)
    _assert_same(
        _to_polars(ref), _to_polars(got), "idx" if "idx" in ref.columns else ref.columns[0]
    )


@pytest.mark.parametrize("backend", BACKENDS)
def test_shrinkage_and_projection_agree_across_backends(backend: str) -> None:
    idx = pl.int_range(0, 800, eager=True)
    eb = pl.DataFrame(
        {"player_id": idx.cast(pl.Utf8), "ab": 50 + (idx % 500), "h": 12 + ((idx * 3) % 140)}
    )
    shrink = sp.EmpiricalBayesShrinker(success_col="h", trials_col="ab")
    ref = shrink.fit(eb).transform(eb)
    got = sp.EmpiricalBayesShrinker(success_col="h", trials_col="ab").fit(_backend(eb, backend))
    _assert_same(_to_polars(ref), _to_polars(got.transform(_backend(eb, backend))), "player_id")

    seasons = pl.DataFrame(
        {
            "player_id": [str(i % 30) for i in range(90)],
            "season": [2022 + i // 30 for i in range(90)],
            "pa": [550 + i % 40 for i in range(90)],
            "hr": [18 + i % 9 for i in range(90)],
            "bb": [50 + i % 11 for i in range(90)],
            "so": [100 + i % 17 for i in range(90)],
        }
    )

    def project(df: Any) -> pl.DataFrame:
        model = sp.MarcelProjector(
            target_season=2025, rate_cols=("hr", "bb", "so"), exposure_col="pa"
        )
        return _to_polars(model.fit(df).predict())

    _assert_same(project(seasons), project(_backend(seasons, backend)), "player_id")


@pytest.mark.parametrize("backend", BACKENDS)
def test_rolling_agrees_across_backends(backend: str) -> None:
    n = 120
    i = pl.int_range(0, n, eager=True)
    df = pl.DataFrame(
        {
            "player_id": (i % 4).cast(pl.Utf8),
            "game": i // 4,
            "season": pl.repeat(2024, n, eager=True),
            "pa": pl.repeat(4, n, eager=True),
            "ab": pl.repeat(3, n, eager=True),
            "h": i % 3,
            "b2": i % 7 // 6,
            "b3": i % 31 // 30,
            "hr": i % 19 // 18,
            "bb": i % 5 // 4,
            "ibb": i * 0,
            "hbp": i * 0,
            "sf": i * 0,
            "so": i % 4 // 3,
        }
    )
    metrics = [Metric.AVG, Metric.OBP, Metric.WOBA]
    ref = sp.calculate_rolling(df, metrics, window=10, by="player_id", order_by="game")
    got = sp.calculate_rolling(
        _backend(df, backend), metrics, window=10, by="player_id", order_by="game"
    )
    a, b = _to_polars(ref.df), _to_polars(got.df)
    key = ["player_id", "game"]
    assert a.sort(key).equals(b.sort(key).select(a.columns))
