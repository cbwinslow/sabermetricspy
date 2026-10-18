"""Demo 04: Wins Above Replacement (fWAR/bWAR), Marcel Projections, Log5, Markov Chains, Monte Carlo & Uncertainty.

Run with:
    uv run python examples/04_war_and_forecasting_models.py
"""

from __future__ import annotations

import sys

import polars as pl

from sabermetricspy import (
    Log5Model,
    MarcelProjector,
    MarkovChainModel,
    MonteCarloSimulator,
    WARFramework,
    binomial_rate_interval,
    bootstrap_interval,
)


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    print("=" * 88)
    print("SABERMETRICSPY DEMO 04: WAR VALUATION, FORECASTING MODELS & UNCERTAINTY INTERVALS")
    print("=" * 88)

    # 1. Wins Above Replacement (WARFramework)
    war_engine = WARFramework(season=2024, replacement_runs_per_600_pa=20.0)
    bobby_witt_war = war_engine.calculate_position_player_scalar(
        pa=709,
        batting_runs=54.2,
        baserunning_runs=6.8,
        fielding_runs=14.5,
        position="SS",
        league_runs=1.2,
    )
    print("\n[1] Bobby Witt Jr. 2024 Position-Player WAR Breakdown (SS):")
    print(f"  - Batting Runs (wRAA):     {bobby_witt_war.batting_runs:+.1f}")
    print(f"  - Baserunning Runs (BsR):  {bobby_witt_war.baserunning_runs:+.1f}")
    print(f"  - Fielding Runs:           {bobby_witt_war.fielding_runs:+.1f}")
    print(f"  - Positional Adj (SS):     {bobby_witt_war.positional_runs:+.1f}")
    print(f"  - Replacement Level Runs:  {bobby_witt_war.replacement_runs:+.1f}")
    print(
        f"  - Runs Above Replacement:  {bobby_witt_war.runs_above_replacement:+.1f} RAR -> {bobby_witt_war.war:.2f} WAR"
    )

    # Vectorized DataFrame Pitcher WAR Calculation
    pitcher_df = pl.DataFrame(
        {
            "player_id": ["Tarik Skubal", "Chris Sale", "Zack Wheeler"],
            "outs": [576, 533, 600],
            "fip": [2.49, 2.38, 2.95],
        }
    )
    pitcher_war = war_engine.calculate_pitcher_war_df(pitcher_df)
    print("\n[2] Vectorized Pitcher fWAR Table:")
    print(pitcher_war.select("player_id", "outs", "fip", "pitcher_rar", "pitcher_war"))

    # 2. Tom Tango's Marcel the Monkey Forecasting System
    history_df = pl.DataFrame(
        {
            "player_id": ["sotoj001", "sotoj001", "sotoj001", "wittb002", "wittb002", "wittb002"],
            "season": [2022, 2023, 2024, 2022, 2023, 2024],
            "age": [23, 24, 25, 22, 23, 24],
            "pa": [664, 708, 713, 632, 694, 709],
            "hr": [27, 35, 41, 20, 30, 32],
            "bb": [135, 132, 129, 30, 40, 57],
            "so": [96, 129, 119, 135, 121, 106],
            "h": [127, 156, 166, 150, 184, 211],
            "b2": [25, 32, 31, 31, 28, 45],
            "b3": [2, 1, 4, 6, 11, 11],
        }
    )
    marcel = MarcelProjector(target_season=2025).fit(history_df)
    projections_2025 = marcel.predict()
    print(
        "\n[3] 2025 Marcel the Monkey Projections (5/4/3 Weighting + Empirical Bayes + Age Curve):"
    )
    print(projections_2025)

    # 3. Bill James's Log5 Matchup Model
    log5_prob = Log5Model.batter_pitcher_matchup_rate(0.310, 0.215, 0.245)
    print(
        f"\n[4] Bill James Log5 Matchup (.310 Batter vs .215 Pitcher in .245 League): {log5_prob:.3f}"
    )

    # 4. Exact Absorbing Markov Chain Half-Inning Run Distribution (Bukiet, Harold & Palacios 1997)
    markov = MarkovChainModel().fit(
        p_1b=0.145,
        p_2b=0.046,
        p_3b=0.004,
        p_hr=0.042,
        p_bb=0.088,
    )
    print("\n[5] Exact Absorbing Markov Chain Half-Inning Run Distribution:")
    print(f"  - Expected Runs / Half-Inning: {markov.results.expected_runs_per_half_inning:.3f}")
    print(f"  - Expected Runs / 9 Innings:   {markov.results.expected_runs_per_9_innings:.2f}")

    # 5. Vectorized Monte Carlo Inning Simulator (Cross-Checking Analytical Markov Chain)
    mc = MonteCarloSimulator(n_simulations=2_000, seed=42).simulate(
        p_1b=0.145,
        p_2b=0.046,
        p_3b=0.004,
        p_hr=0.042,
        p_bb=0.088,
    )
    print(
        f"\n[6] Monte Carlo Simulation (2,000 Games): Mean={mc.mean_runs_per_game:.2f} ± {mc.std_runs_per_game:.2f} runs/9"
    )

    # 6. Credible & Confidence Uncertainty Intervals for Small Samples
    ci_wilson = binomial_rate_interval(successes=18, trials=50)
    ci_boot = bootstrap_interval(
        [102.4, 105.1, 98.7, 108.9, 111.2, 95.4, 104.0, 106.8], n_resamples=1000, seed=42
    )
    print("\n[7] Small-Sample Uncertainty Quantification (18-for-50 = .360 AVG):")
    print(
        f"  - Binomial 95% Interval:      [{ci_wilson.ci_lower:.3f}, {ci_wilson.ci_upper:.3f}] (est={ci_wilson.estimate:.3f})"
    )
    print(
        f"  - Bootstrap Exit Velo 95% CI: [{ci_boot.ci_lower:.1f}, {ci_boot.ci_upper:.1f}] mph (mean={ci_boot.estimate:.1f})"
    )


if __name__ == "__main__":
    main()
