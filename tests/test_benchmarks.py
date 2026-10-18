"""Automated performance regression benchmarks using pytest-benchmark."""

from __future__ import annotations

from typing import Any

import polars as pl

import sabermetricspy as sb
from sabermetricspy import MetricSuite


def test_benchmark_offensive_suites_polars(benchmark: Any) -> None:
    """Benchmark TRADITIONAL_BATTING + WEIGHTED_OFFENSE over 25,000 player-game rows."""
    n = 25_000
    idx = pl.int_range(0, n, eager=True)
    df = pl.DataFrame(
        {
            "player_id": (idx % 200).cast(pl.Utf8),
            "pa": pl.repeat(4, n, eager=True),
            "ab": pl.repeat(3, n, eager=True),
            "r": (idx % 4 == 0).cast(pl.Int64),
            "h": (idx % 3 == 0).cast(pl.Int64),
            "b2": (idx % 11 == 0).cast(pl.Int64),
            "b3": (idx % 67 == 0).cast(pl.Int64),
            "hr": (idx % 19 == 0).cast(pl.Int64),
            "rbi": (idx % 4 == 0).cast(pl.Int64),
            "bb": (idx % 5 == 0).cast(pl.Int64),
            "ibb": (idx % 47 == 0).cast(pl.Int64),
            "hbp": (idx % 37 == 0).cast(pl.Int64),
            "sf": (idx % 41 == 0).cast(pl.Int64),
            "sh": pl.repeat(0, n, eager=True),
            "so": (idx % 4 == 0).cast(pl.Int64),
        }
    )

    res = benchmark(
        sb.calculate_suite,
        df,
        [MetricSuite.TRADITIONAL_BATTING, MetricSuite.WEIGHTED_OFFENSE],
        by="player_id",
        season=2024,
    )
    assert len(res.df) == 200
    assert res.profile.rows_per_sec > 10_000


def test_benchmark_vectorized_wpa_and_re288(benchmark: Any) -> None:
    """Benchmark vectorized WinProbabilityModel.transform() over 20,000 plays."""
    n = 20_000
    idx = pl.int_range(0, n, eager=True)
    plays = pl.DataFrame({"idx": idx}).select(
        ((pl.col("idx") % 9) + 1).cast(pl.Int64).alias("inning"),
        pl.when(pl.col("idx") % 2 == 0).then(pl.lit("top")).otherwise(pl.lit("bottom")).alias("half_inning"),
        (pl.col("idx") % 3).cast(pl.Int64).alias("outs_before"),
        pl.when(pl.col("idx") % 4 == 0).then(pl.lit("12-")).otherwise(pl.lit("---")).alias("base_state_before"),
        ((pl.col("idx") % 7) - 3).cast(pl.Int64).alias("home_score_diff_before"),
        ((pl.col("idx") + 1) % 4).cast(pl.Int64).alias("outs_after"),
        pl.lit("---").alias("base_state_after"),
        (pl.col("idx") % 5 == 0).cast(pl.Int64).alias("runs_on_play"),
    )
    wp_model = sb.WinProbabilityModel.from_default()
    out = benchmark(wp_model.transform, plays)
    assert len(out) == n
    assert "wpa" in out.columns

