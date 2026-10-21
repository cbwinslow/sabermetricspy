"""Demo 05: Execution Telemetry (.profile), Multi-Backend Benchmarking, Rolling Windows, Pitch Physics (VAA/IVB/HB) & CLI.

Run with:
    uv run python examples/05_benchmarking_rolling_physics_and_cli.py
"""

from __future__ import annotations

import sys

import polars as pl

import sabermetricspy as sb
from sabermetricspy import Metric, MetricSuite
from sabermetricspy.cli import main as cli_main


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    print("=" * 96)
    print(
        "SABERMETRICSPY DEMO 05: TELEMETRY, MULTI-BACKEND BENCHMARKS, ROLLING WINDOWS, PITCH PHYSICS & CLI"
    )
    print("=" * 96)

    # 1. Built-In ExecutionProfile Telemetry (.profile) & Multi-Backend Benchmark
    bench_report = sb.benchmark(rows=100_000, groups=500, warmup=1, repeats=3)
    print(
        "\n[1] Live Multi-Backend Benchmark (100,000 game logs -> 500 players, 12 offensive metrics):"
    )
    print(bench_report.format_table())

    # 2. Additive Rolling-Window Engine (calculate_rolling)
    game_logs = pl.DataFrame(
        {
            "player_id": ["judga001"] * 5,
            "game_seq": [1, 2, 3, 4, 5],
            "pa": [4, 5, 4, 4, 5],
            "ab": [3, 4, 3, 2, 4],
            "h": [1, 2, 0, 2, 3],
            "b2": [0, 1, 0, 0, 1],
            "b3": [0, 0, 0, 0, 0],
            "hr": [1, 0, 0, 1, 2],
            "bb": [1, 1, 1, 2, 1],
            "ibb": [0, 0, 0, 1, 0],
            "hbp": [0, 0, 0, 0, 0],
            "sf": [0, 0, 0, 0, 0],
            "so": [1, 1, 2, 0, 1],
        }
    )
    rolling_res = sb.calculate_rolling(
        game_logs,
        [Metric.AVG, Metric.OBP, Metric.SLG, Metric.OPS, Metric.WOBA, Metric.WRC_PLUS],
        window=3,
        by="player_id",
        order_by="game_seq",
    )
    print("\n[2] 3-Game Additive Rolling Window (Sums Counts Over 3-Game Window Before Dividing):")
    print(
        rolling_res.df.select(
            "player_id",
            "game_seq",
            "pa",
            "ab",
            "h",
            "hr",
            "bb",
            "avg",
            "obp",
            "slg",
            "woba",
            "wrc_plus",
        )
    )
    print(f"    Rolling Execution Profile: {rolling_res.profile.model_dump()}")

    # 3. Pitch-Tracking Kinematics (VAA, IVB, HB, Spin, Extension) & Statcast Expected Metrics (xBA, xSLG, xwOBA)
    statcast_pitches = pl.DataFrame(
        {
            "pitcher": [669373, 669373, 669373, 543037, 543037],
            "batter": [592450, 592450, 665742, 592450, 665742],
            "release_speed": [97.8, 98.4, 97.2, 99.1, 98.7],
            "effective_speed": [98.6, 99.1, 98.0, 100.2, 99.8],
            "release_spin_rate": [2420, 2460, 2390, 2550, 2510],
            "release_extension": [6.6, 6.7, 6.5, 7.1, 7.0],
            "pfx_x": [-0.75, -0.82, -0.70, 0.95, 0.88],  # Feet -> converted to inches (* 12)
            "pfx_z": [1.55, 1.62, 1.48, 1.40, 1.35],  # Feet -> converted to inches (* 12)
            "vy0": [-142.1, -143.0, -141.2, -144.0, -143.4],
            "vz0": [-4.2, -3.8, -5.1, -6.5, -6.1],
            "ay": [31.5, 32.0, 31.0, 32.8, 32.4],
            "az": [-13.2, -12.4, -14.0, -15.1, -15.6],
            "description": [
                "swinging_strike",
                "called_strike",
                "hit_into_play",
                "swinging_strike",
                "hit_into_play",
            ],
            "zone": [2, 5, 4, 8, 6],
            "events": ["", "strikeout", "home_run", "strikeout", "single"],
            "bb_type": ["", "", "fly_ball", "", "line_drive"],
            "launch_speed": [None, None, 110.5, None, 99.2],
            "launch_angle": [None, None, 27.0, None, 14.0],
            "estimated_ba_using_speedangle": [0.0, 0.0, 0.940, 0.0, 0.720],
            "estimated_slg_using_speedangle": [0.0, 0.0, 3.650, 0.0, 0.980],
            "estimated_woba_using_speedangle": [0.0, 0.0, 1.880, 0.0, 0.710],
        }
    )

    physics_res = sb.calculate_suite(
        statcast_pitches,
        [MetricSuite.PITCH_PHYSICS, MetricSuite.STATCAST_EXPECTED],
        by="pitcher_id",
        preset="statcast",
    )
    print("\n[3] Pitch-Tracking Physics (VAA, IVB, HB, Total Break) & Statcast Expected Metrics:")
    print(
        physics_res.df.select(
            "pitcher_id",
            "avg_velo",
            "effective_velo",
            "avg_spin",
            "avg_extension",
            "ivb",
            "hb",
            "total_break",
            "vaa",
            "xba",
            "xslg",
            "xwoba",
        )
    )

    # 4. Decorator-Based Telemetry (@sb.profiled & sb.telemetry) + Registered Subsystem Benchmarks (@sb.register_benchmark)
    @sb.profiled(category="user_pipeline")
    def build_custom_pitcher_report(df_pitches: pl.DataFrame) -> pl.DataFrame:
        translated = sb.prepare_statcast_pitches(df_pitches)
        res = sb.calculate_suite(
            translated,
            [MetricSuite.PITCH_PHYSICS, MetricSuite.STATCAST_EXPECTED],
            by="pitcher_id",
        )
        return res.df

    with sb.telemetry.session():
        _ = build_custom_pitcher_report(statcast_pitches)
        print(
            "\n[4] Decorator-Captured Telemetry Session (@sb.profiled across library & user functions):"
        )
        print(sb.telemetry.format_table())

    print("\n[5] Decorator-Registered Subsystem Benchmark Suite (@sb.register_benchmark):")
    reg_bench = sb.run_registered_benchmarks(repeats=2)
    print(reg_bench.format_table())

    # 6. CLI Inspection (`sabermetrics info vaa` & `sabermetrics suites`)
    print("\n[6] CLI Output (`sabermetrics info vaa` & `sabermetrics suites`):")
    cli_main(["info", "vaa"])
    print()
    cli_main(["suites"])


if __name__ == "__main__":
    main()
