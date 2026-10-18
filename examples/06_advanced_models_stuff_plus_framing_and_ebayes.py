"""Demo 06: 105+ Registry Metrics, Stuff+/Pitching+, Open xwOBA, Catcher Framing, OAA, & Empirical Bayes Shrinkage."""

from __future__ import annotations

import polars as pl

import sabermetricspy as sb
from sabermetricspy import Metric


def main() -> None:
    pl.Config.set_tbl_formatting("ASCII_FULL")
    pl.Config.set_tbl_cols(12)
    print("=" * 96)
    print(f"sabermetricspy v{sb.__version__} -- Demo 06: 105+ Metrics & Open Modeled Estimators")
    print(f"Total Registered Canonical Metrics: {len(sb.REGISTRY.all_specs())}")
    print("=" * 96)

    with sb.telemetry.session() as tracker:
        # 1. New Registry Metrics (GPA, TA, RC/27, QERA, DIPS BOP%, Bauer Units, Clutch, REW)
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
                Metric.RC27,
                Metric.WGDP,
                Metric.BSR,
                Metric.QERA,
                Metric.DIPS_BOP_PCT,
                Metric.XERA,
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
                "rc27",
                "bsr",
                "qera",
                "xera",
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

        # 4. PitchQualityModel (Open Stuff+, Location+, Pitching+ with statsmodels OLS diagnostics)
        print("\n[4] Open Stuff+, Location+, and Pitching+ (`PitchQualityModel`):")
        idx = pl.int_range(0, 150, eager=True).cast(pl.Float64)
        pitches = pl.DataFrame(
            {
                "pitcher_id": ["ace_flame" if i % 3 == 0 else "league_avg" for i in range(150)],
                "release_speed": 91.0 + (idx % 7.0),
                "ivb": 11.0 + (idx % 11.0),
                "hb": -8.0 + (idx % 13.0),
                "release_extension": 6.0 + (idx % 5.0) * 0.2,
                "spin_rate": 2150.0 + (idx % 17.0) * 25.0,
                "vaa": -5.2 + (idx % 19.0) * 0.1,
                "haa": -2.0 + (idx % 23.0) * 0.15,
                "plate_x": -0.7 + (idx % 29.0) * 0.05,
                "plate_z": 1.7 + (idx % 31.0) * 0.05,
                "balls": (idx % 4).cast(pl.Int64),
                "strikes": (idx % 3).cast(pl.Int64),
            }
        ).with_columns(
            (
                -0.018 * (pl.col("release_speed") - 94.5)
                - 0.009 * (pl.col("ivb") - 14.5)
                + 0.012 * (pl.col("plate_x").abs() - 0.5)
            ).alias("pitch_rv")
        )
        pq = sb.PitchQualityModel().fit(pitches)
        pq_scored = pq.transform(pitches)
        print(
            f"PitchQualityResults: Stuff R^2={pq.results.stuff_r_squared:.3f}, "
            f"F={pq.results.stuff_f_statistic:.1f}, Pitching R^2={pq.results.pitching_r_squared:.3f}"
        )
        print(
            pq_scored.group_by("pitcher_id")
            .agg(
                pl.len().alias("pitches"),
                pl.col("stuff_plus").mean().round(1),
                pl.col("location_plus").mean().round(1),
                pl.col("pitching_plus").mean().round(1),
            )
            .sort("pitching_plus", descending=True)
        )

        # 5. ExpectedOutcomeModel, CatcherFramingModel, & OutsAboveAverageModel
        print("\n[5] Open xwOBA (`ExpectedOutcomeModel`), Catcher Framing, & Fielding OAA:")
        bbe_df = pl.DataFrame(
            {
                "launch_speed": [78.0, 82.0, 88.0, 95.0, 102.0, 108.0, 111.0, 85.0, 99.0, 106.0]
                * 3,
                "launch_angle": [-8.0, 45.0, 12.0, 16.0, 22.0, 28.0, 26.0, 5.0, 18.0, 29.0] * 3,
                "sprint_speed": [27.0, 26.5, 28.0, 27.5, 28.2, 27.0, 27.5, 26.8, 28.5, 27.2] * 3,
                "b1": [0, 0, 1, 1, 0, 0, 0, 0, 1, 0] * 3,
                "b2": [0, 0, 0, 0, 1, 0, 0, 0, 0, 0] * 3,
                "b3": [0, 0, 0, 0, 0, 0, 0, 0, 0, 0] * 3,
                "hr": [0, 0, 0, 0, 0, 1, 1, 0, 0, 1] * 3,
            }
        )
        xw_model = sb.ExpectedOutcomeModel(n_neighbors=5).fit(bbe_df)
        xw_pred = xw_model.transform(bbe_df.head(6))
        print(xw_pred.select("launch_speed", "launch_angle", "xba_est", "xslg_est", "xwoba_est"))

        print("\n[6] Automatic `@profiled` Telemetry Spans Recorded Across Demo 06:")
        print(tracker.format_table())


if __name__ == "__main__":
    main()
