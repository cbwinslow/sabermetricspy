"""Demo 01: Batting & Pitching Leaderboards, Multi-Backend Execution, Suites, and Provenance.

Run with:
    uv run python examples/01_batting_and_pitching_leaderboards.py
"""

from __future__ import annotations

import sys

import duckdb
import pandas as pd
import polars as pl
import pyarrow as pa

import sabermetricspy as sb
from sabermetricspy import Category, Metric, MetricSuite


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    print("=" * 88)
    print("SABERMETRICSPY DEMO 01: BATTING & PITCHING LEADERBOARDS ACROSS 4 DATAFRAME BACKENDS")
    print("=" * 88)

    # 1. 2024 MLB MVP Contenders (Polars DataFrame)
    batters_pl = pl.DataFrame(
        {
            "player_id": ["Aaron Judge", "Shohei Ohtani", "Juan Soto", "Bobby Witt Jr."],
            "team": ["NYY", "LAD", "NYY", "KCR"],
            "g": [158, 159, 157, 161],
            "pa": [704, 731, 713, 709],
            "ab": [559, 636, 576, 636],
            "r": [122, 134, 128, 125],
            "h": [180, 197, 166, 211],
            "b2": [36, 38, 31, 45],
            "b3": [1, 7, 4, 11],
            "hr": [58, 54, 41, 32],
            "rbi": [144, 130, 109, 109],
            "bb": [133, 81, 129, 57],
            "ibb": [20, 10, 2, 9],
            "hbp": [9, 6, 4, 8],
            "sf": [2, 5, 4, 8],
            "sh": [0, 0, 0, 0],
            "so": [171, 162, 119, 106],
            "sb": [10, 59, 7, 31],
            "cs": [0, 4, 4, 12],
            "gidp": [22, 7, 10, 4],
        }
    )

    # Evaluate TRADITIONAL_BATTING + WEIGHTED_OFFENSE suites with 2024 FanGraphs context
    batting_res = sb.calculate_suite(
        batters_pl,
        [MetricSuite.TRADITIONAL_BATTING, MetricSuite.WEIGHTED_OFFENSE],
        by="player_id",
        season=2024,
    )
    print("\n[1] 2024 MLB Batting Leaderboard (Polars Native Execution):")
    print(
        batting_res.df.select(
            "player_id",
            "avg",
            "obp",
            "slg",
            "ops",
            "iso",
            "babip",
            "bb_pct",
            "k_pct",
            "woba",
            "wrc",
            "wraa",
            "wrc_plus",
        ).sort("wrc_plus", descending=True)
    )

    # 2. Verify Identical Output Across Polars, DuckDB, PyArrow, and pandas
    batters_pd = batters_pl.to_pandas()
    batters_pa = batters_pl.to_arrow()
    conn = duckdb.connect()
    conn.register("batters_v", batters_pa)
    batters_duck = conn.sql("SELECT * FROM batters_v")

    res_pd = sb.calculate(batters_pd, [Metric.WRC_PLUS, Metric.OPS], by="player_id", season=2024)
    res_pa = sb.calculate(batters_pa, [Metric.WRC_PLUS, Metric.OPS], by="player_id", season=2024)
    res_duck = sb.calculate(
        batters_duck, [Metric.WRC_PLUS, Metric.OPS], by="player_id", season=2024
    )

    assert isinstance(res_pd.df, pd.DataFrame)
    assert isinstance(res_pa.df, pa.Table)
    print("\n[2] Multi-Backend Native Return Types Verified:")
    print(f"  - Polars  -> {type(batting_res.df).__name__}")
    print(f"  - pandas  -> {type(res_pd.df).__name__}")
    print(f"  - PyArrow -> {type(res_pa.df).__name__}")
    print(f"  - DuckDB  -> {type(res_duck.df).__name__}")

    # 3. 2024 Cy Young Pitching Leaderboard (with baseball IP notation '209.1')
    pitchers_pl = pl.DataFrame(
        {
            "player_id": ["Tarik Skubal", "Chris Sale", "Zack Wheeler", "Emmanuel Clase"],
            "ip": ["192.0", "177.2", "200.0", "74.1"],
            "bf": [756, 702, 787, 275],
            "h": [142, 141, 139, 42],
            "r": [54, 48, 62, 10],
            "er": [51, 47, 57, 5],
            "hr": [15, 9, 20, 2],
            "bb": [35, 39, 52, 10],
            "ibb": [0, 0, 0, 2],
            "hbp": [5, 8, 7, 2],
            "so": [228, 225, 224, 66],
            "gb": [225, 195, 220, 122],
            "fb": [155, 140, 175, 45],
            "ld": [92, 85, 98, 28],
            "pu": [28, 22, 32, 8],
        }
    )

    pitching_res = sb.calculate_suite(
        pitchers_pl,
        [MetricSuite.TRADITIONAL_PITCHING, MetricSuite.DEFENSE_INDEPENDENT_PITCHING],
        by="player_id",
        season=2024,
    )
    print("\n[3] 2024 MLB Pitching Leaderboard (ERA, WHIP, FIP, xFIP, SIERA, K-BB%):")
    print(
        pitching_res.df.select(
            "player_id",
            "outs",
            "era",
            "whip",
            "fip",
            "xfip",
            "siera",
            "k_per_9",
            "bb_per_9",
            "pit_k_minus_bb_pct",
            "era_minus",
            "fip_minus",
        ).sort("fip")
    )

    # 4. Auto-Discovery & Provenance Inspection
    avail_res = sb.calculate_available(pitchers_pl, by="player_id", season=2024)
    print(f"\n[4] Auto-Discovered {len(avail_res.specs)} Computable Metrics on Pitching Table!")
    print("\n[5] Metric Provenance & Citations (.summary()):")
    print(pitching_res.summary())

    batting_metrics = sb.search_metrics(category=Category.BATTING)
    print(f"\n[6] Registry Search: Found {len(batting_metrics)} registered BATTING metrics.")
    print(f"    wRC+ Formula: {sb.formula(Metric.WRC_PLUS)}")


if __name__ == "__main__":
    main()
