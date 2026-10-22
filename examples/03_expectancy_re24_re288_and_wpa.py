"""Demo 03: Empirical Run Expectancy (RE24), 288-State Count Expectancy (RE288), Linear Weights, and Win Expectancy.

Run with:
    uv run python examples/03_expectancy_re24_re288_and_wpa.py

Needs seasonal constants, which the library does not ship: set SABERMETRICSPY_CONSTANTS to a directory of them or call
sp.use_guts("guts.csv") first (see docs/CONSTANTS.md).
"""

from __future__ import annotations

import sys

import polars as pl

from sabermetricspy import (
    BaseState,
    CountExpectancyMatrix,
    LinearWeightsEstimator,
    RunExpectancyMatrix,
)


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    print("=" * 88)
    print(
        "SABERMETRICSPY DEMO 03: RE24, 288-STATE COUNT EXPECTANCY (RE288), LINEAR WEIGHTS & WIN EXPECTANCY"
    )
    print("=" * 88)

    # 1. 24-State Run Expectancy Matrix (RE24) & Steal Breakeven Rates
    re24 = RunExpectancyMatrix.from_default()
    print("\n[1] Canonical 24-State Run Expectancy (RE24) & Stolen Base Breakeven Rates:")
    for outs in (0, 1, 2):
        re_empty = re24.results.lookup(outs, BaseState.EMPTY)
        re_1b = re24.results.lookup(outs, BaseState.FIRST)
        re_loaded = re24.results.lookup(outs, BaseState.LOADED)
        sb_breakeven = re24.results.steal_breakeven_rate(
            outs, BaseState.FIRST, BaseState.SECOND, BaseState.EMPTY
        )
        print(
            f"  Outs={outs} | RE(---)={re_empty:.3f} | RE(1--)={re_1b:.3f} | "
            f"RE(123)={re_loaded:.3f} | Steal 2B Breakeven={sb_breakeven:.1%}"
        )

    # Annotate a sequence of plays with RE24 run values
    plays_df = pl.DataFrame(
        {
            "play_id": [1, 2, 3, 4],
            "inning": [9, 9, 9, 9],
            "half_inning": ["bottom", "bottom", "bottom", "bottom"],
            "outs_before": [0, 0, 1, 1],
            "base_state_before": ["---", "1--", "1--", "12-"],
            "outs_after": [0, 1, 1, 1],
            "base_state_after": ["1--", "1--", "12-", "---"],
            "runs_on_play": [0, 0, 0, 3],
            "home_score_diff_before": [-2, -2, -2, -2],
            "play_outcome": ["walk", "out", "single", "home_run"],
        }
    )
    plays_re24 = re24.transform(plays_df)
    print("\n[2] Bottom of the 9th Comeback Rally — Play-by-Play RE24 Valuation:")
    print(
        plays_re24.select(
            "play_id",
            "play_outcome",
            "outs_before",
            "base_state_before",
            "runs_on_play",
            "re_before",
            "re_after",
            "run_value",
        )
    )

    # 2. Empirical Linear Weights & wOBA Scale Derivation
    lw = LinearWeightsEstimator(target_lg_obp=0.312).fit(plays_re24)
    print("\n[3] Empirical Linear Weights Fitted from Play-by-Play RE24 Run Values:")
    print(f"  - Out Run Value: {lw.results.out_run_value:+.3f} runs")
    print(f"  - wOBA Scale:    {lw.results.woba_scale:.3f}")
    print(
        f"  - Derived wOBA Weights: { {k: round(v, 3) for k, v in lw.results.woba_weights.items() if v > 0} }"
    )

    # 3. 288-State Count & Base-Out Expectancy Matrix (RE288)
    # RE288 has no built-in table: it is fitted from pitch-level data (here, a four-pitch toy plate appearance).
    pitches_df = pl.DataFrame(
        {
            "pa_id": [1, 1, 1, 1],
            "runs_rest_of_inning": [1.0, 1.0, 1.0, 1.0],
            "pitch_no": [1, 2, 3, 4],
            "outs_before": [1, 1, 1, 1],
            "base_state_before": ["12-", "12-", "12-", "12-"],
            "balls": [0, 1, 2, 3],
            "strikes": [0, 0, 1, 2],
            "outs_after": [1, 1, 1, 2],
            "base_state_after": ["12-", "12-", "12-", "12-"],
            "balls_after": [1, 2, 3, 0],
            "strikes_after": [0, 1, 2, 0],
            "runs_on_play": [0, 0, 0, 0],
            "pitch_result": ["ball", "called_strike", "foul", "swinging_strike_out"],
        }
    )
    re288 = CountExpectancyMatrix().fit(pitches_df)
    print(
        f"\n[4] 288-State Count Expectancy (RE288) — States Fitted: {len(re288.results.state_expectancy)} of 288"
    )
    pitches_re288 = re288.transform(pitches_df)
    print(
        pitches_re288.select(
            "pitch_no",
            "pitch_result",
            "balls",
            "strikes",
            "re288_before",
            "re288_after",
            "pitch_run_value",
            "count_leverage",
        )
    )


if __name__ == "__main__":
    main()
