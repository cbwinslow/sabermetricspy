"""Demo 06: 100+ Registry Metrics, Position-Player WAR, & Empirical Bayes Shrinkage.

Needs seasonal constants, which the library does not ship: set SABERMETRICSPY_CONSTANTS to a directory of them or call
sp.use_guts("guts.csv") first (see docs/CONSTANTS.md).
"""

from __future__ import annotations

import polars as pl

import sabermetricspy as sb
from sabermetricspy import Metric


def main() -> None:
    pl.Config.set_tbl_formatting("ASCII_FULL")
    pl.Config.set_tbl_cols(12)
    print("=" * 96)
    print(f"sabermetricspy v{sb.__version__} -- Demo 06: 100+ Metrics, WAR & Empirical Bayes")
    print(f"Total Registered Canonical Metrics: {len(sb.REGISTRY.all_specs())}")
    print("=" * 96)

    with sb.telemetry.session() as tracker:
        # 1. New Registry Metrics (GPA, TA, DIPS BOP%, Bauer Units, Clutch, REW)
        print("\n[1] Newly Added Batting, Pitching/DIPS, Physics, & Expectancy Metrics:")
        season_df = pl.DataFrame(
            {
                "player_id": ["judge_2024", "skenes_2024"],
                "pa": [704, 514],
                "ab": [559, 460],
                "h": [180, 94],
                "b2": [36, 14],
                "b3": [1, 1],
                "hr": [58, 11],
                "bb": [133, 32],
                "ibb": [20, 0],
                "hbp": [9, 4],
                "sf": [2, 2],
                "so": [171, 170],
                "sb": [10, 0],
                "cs": [0, 0],
                "gidp": [16, 8],
                "gidp_opp": [140, 110],
                "ubr": [1.8, 0.0],
                "outs": [399, 399],  # 133.0 IP for Skenes
                "bf": [514, 514],
                "gb": [160, 155],
                "bbe": [389, 310],
                "xwoba_sum": [335.0, 130.0],
                "xwoba_count": [704, 514],
                "velo_sum": [94000.0, 99100.0],
                "velo_count": [1000, 1000],
                "spin_sum": [2300000.0, 2550000.0],
                "spin_count": [1000, 1000],
                "re24": [92.4, 34.0],
                "wpa": [6.8, 3.9],
                "li_sum": [739.2, 540.0],
                "wpa_li_sum": [6.1, 3.5],
            }
        )
        res = sb.calculate(
            season_df,
            [
                Metric.GPA,
                Metric.TA,
                Metric.BSR,
                Metric.DIPS_BOP_PCT,
                Metric.BAUER_UNITS,
                Metric.PLI,
                Metric.CLUTCH,
                Metric.REW,
            ],
            season=2024,
        )
        print(
            res.df.select(
                "player_id",
                "gpa",
                "ta",
                "bsr",
                "bauer_units",
                "clutch",
                "rew",
            )
        )

        # 2. Vectorized Position-Player WAR DataFrame
        print("\n[2] Vectorized Position-Player WAR (`WARFramework.calculate_position_player_df`):")
        pos_war_input = pl.DataFrame(
            {
                "player_id": ["judge_2024", "witt_2024", "henderson_2024"],
                "position": ["CF", "SS", "SS"],
                "pa": [704, 709, 719],
                "wraa": [86.5, 58.2, 46.8],
                "bsr": [2.1, 8.4, 6.2],
                "fielding_runs": [-1.5, 13.5, 7.8],
            }
        )
        war_df = sb.WARFramework(season=2024).calculate_position_player_df(pos_war_input)
        print(
            war_df.select(
                "player_id",
                "position",
                "pa",
                "positional_runs",
                "replacement_runs",
                "runs_above_replacement",
                "war",
            )
        )

        # 3. EmpiricalBayesShrinker (Beta-Binomial stabilization)
        print("\n[3] Empirical Bayes Shrinkage (`EmpiricalBayesShrinker` for Small-Sample AVG):")
        eb_input = pl.DataFrame(
            {
                "player_id": [
                    "april_callout_4_for_10",
                    "veteran_200_for_500",
                    "regular_130_for_500",
                ],
                "h": [4, 200, 130],
                "ab": [10, 500, 500],
            }
        )
        eb = sb.EmpiricalBayesShrinker(
            success_col="h", trials_col="ab", stabilization_trials=300.0
        ).fit(eb_input)
        eb_out = eb.transform(eb_input)
        print("EmpiricalBayesResults:", eb.results)
        print(
            eb_out.select(
                "player_id",
                "ab",
                "eb_raw_rate",
                "eb_rate",
                "eb_shrinkage",
                "eb_ci_lower",
                "eb_ci_upper",
            )
        )

        print("\n[4] Automatic `@profiled` Telemetry Spans Recorded Across Demo 06:")
        print(tracker.format_table())


if __name__ == "__main__":
    main()
