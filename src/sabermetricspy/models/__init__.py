"""Statistical forecasting, matchup, and simulation models (Marcel, Log5, Absorbing Markov Chain, Monte Carlo)."""

from __future__ import annotations

from typing import Any, Self

import narwhals as nw
import numpy as np
import polars as pl
from narwhals.typing import IntoFrame
from pydantic import BaseModel, ConfigDict, Field

from sabermetricspy.models.modeled import (
    CatcherFramingModel,
    CatcherFramingResults,
    ExpectedOutcomeModel,
    ExpectedOutcomeResults,
    OutsAboveAverageModel,
    OutsAboveAverageResults,
    PitchQualityModel,
    PitchQualityResults,
)
from sabermetricspy.schema import to_polars_df
from sabermetricspy.telemetry import profiled


class MarcelResults(BaseModel):
    """Frozen results and diagnostics for Marcel the Monkey forecasting system."""

    model_config = ConfigDict(frozen=True)

    target_season: int
    season_weights: tuple[float, float, float]
    regression_pa: float
    league_rates: dict[str, float]
    n_players_projected: int


class MarcelProjector:
    """Tom Tango's Marcel the Monkey Forecasting System (scikit-learn style estimator).

    Implements Tango's Marcel method for hitters:
    1. Weight the previous 3 seasons by `(5, 4, 3)` for rate stats; playing time is
       `0.5 * last-year + 0.1 * prior-year + 200`.
    2. Regress weighted player rates toward the league mean by adding `regression_pa` (default `1200`)
       plate appearances of league-average production.
    3. Apply the age adjustment (`+0.006 * (29 - age)` if `age < 29`, `-0.003 * (age - 29)` if `age > 29`).

    Pitchers (Tango's March 2004 post): weights `3/2/1`, innings in place of plate appearances, and the `200`
    in the playing-time formula replaced by 25 for relievers or 60 for starters (part-timers in between by GS/G).
    Configure with `season_weights=(3, 2, 1)`, `exposure_col="ip"` and `playing_time_base` (a number, or the name of
    a column holding each player's base). Tango gives no innings equivalent for the regression step, so
    `regression_pa` must be chosen by the caller for pitchers; no source supports a 134 IP constant.

    Differences from the published method (see docs/METHODOLOGY.md): the final re-baselining step is not
    implemented.
    """

    def __init__(
        self,
        *,
        target_season: int = 2025,
        season_weights: tuple[float, float, float] = (5.0, 4.0, 3.0),
        regression_pa: float = 1200.0,
        peak_age: int = 29,
        rate_cols: tuple[str, ...] = ("hr", "bb", "so", "h", "b2", "b3"),
        exposure_col: str = "pa",
        playing_time_base: float | str = 200.0,
    ) -> None:
        self.target_season = target_season
        self.season_weights = season_weights
        self.regression_pa = regression_pa
        self.peak_age = peak_age
        self.rate_cols = rate_cols
        self.exposure_col = exposure_col
        self.playing_time_base = playing_time_base
        self._results: MarcelResults | None = None
        self._projections_df: pl.DataFrame | None = None

    @property
    def results(self) -> MarcelResults:
        if self._results is None:
            raise RuntimeError("MarcelProjector is not fitted yet. Call .fit(df) first.")
        return self._results

    @profiled(category="forecasting")
    def fit(self, df: IntoFrame) -> Self:
        """Learn league baseline rates and compute Marcel projections from historical player-season data."""
        pl_df = to_polars_df(df)

        w1, w2, w3 = self.season_weights
        y1 = self.target_season - 1
        y2 = self.target_season - 2
        y3 = self.target_season - 3

        recent = pl_df.filter(pl.col("season").is_in([y1, y2, y3]))
        if recent.is_empty():
            raise ValueError(
                f"No player-season records found in {y3}..{y1} for target_season={self.target_season}."
            )

        # Assign season recency weights
        recent = recent.with_columns(
            pl.when(pl.col("season") == y1)
            .then(w1)
            .when(pl.col("season") == y2)
            .then(w2)
            .otherwise(w3)
            .alias("_recency_w"),
            pl.when(pl.col("season") == y1)
            .then(0.5)
            .when(pl.col("season") == y2)
            .then(0.1)
            .otherwise(0.0)
            .alias("_pt_w"),
        )

        # Compute weighted league average rates per exposure
        total_weighted_exp = float((recent[self.exposure_col] * recent["_recency_w"]).sum())
        league_rates: dict[str, float] = {}
        for col in self.rate_cols:
            if col in recent.columns and total_weighted_exp > 0:
                league_rates[col] = (
                    float((recent[col] * recent["_recency_w"]).sum()) / total_weighted_exp
                )

        # Aggregate per player. The playing-time constant is 200 PA for hitters; Tango uses 25 or 60 innings for pitchers.
        base_expr: pl.Expr = (
            pl.col(self.playing_time_base).sort_by("season").last()
            if isinstance(self.playing_time_base, str)
            else pl.lit(float(self.playing_time_base))
        )
        agg_exprs: list[pl.Expr] = [
            (pl.col(self.exposure_col) * pl.col("_recency_w")).sum().alias("_weighted_exp"),
            ((pl.col(self.exposure_col) * pl.col("_pt_w")).sum() + base_expr).alias(
                f"proj_{self.exposure_col}"
            ),
        ]
        if "age" in recent.columns:
            # Project age in target_season from most recent season
            agg_exprs.append(
                (pl.col("age") + (self.target_season - pl.col("season"))).max().alias("proj_age")
            )
        for col in self.rate_cols:
            if col in recent.columns:
                agg_exprs.append((pl.col(col) * pl.col("_recency_w")).sum().alias(f"_w_{col}"))

        player_df = recent.group_by("player_id").agg(*agg_exprs)

        # Age adjustment multiplier
        if "proj_age" in player_df.columns:
            age_mult = (
                pl.when(pl.col("proj_age") < self.peak_age)
                .then(1.0 + 0.006 * (self.peak_age - pl.col("proj_age")))
                .when(pl.col("proj_age") > self.peak_age)
                .then(1.0 - 0.003 * (pl.col("proj_age") - self.peak_age))
                .otherwise(1.0)
            )
        else:
            age_mult = pl.lit(1.0)

        player_df = player_df.with_columns(age_mult.alias("age_factor"))

        proj_cols: list[pl.Expr] = [pl.lit(self.target_season).alias("target_season")]
        w_sum = w1 + w2 + w3
        reg_weighted = self.regression_pa * (
            w_sum / 3.0
        )  # 1200 PA across 3 seasons weighted by (5+4+3)/3 = 4800

        for col, lg_rate in league_rates.items():
            regressed_rate = (
                (pl.col(f"_w_{col}") + reg_weighted * lg_rate)
                / (pl.col("_weighted_exp") + reg_weighted)
            ) * pl.col("age_factor")
            proj_cols.append(regressed_rate.alias(f"proj_{col}_rate"))
            proj_cols.append(
                (regressed_rate * pl.col(f"proj_{self.exposure_col}")).alias(f"proj_{col}")
            )

        drop_temp = [c for c in player_df.columns if c.startswith("_")]
        self._projections_df = player_df.with_columns(*proj_cols).drop(drop_temp).sort("player_id")
        self._results = MarcelResults(
            target_season=self.target_season,
            season_weights=self.season_weights,
            regression_pa=self.regression_pa,
            league_rates=league_rates,
            n_players_projected=len(self._projections_df),
        )
        return self

    @profiled(category="forecasting")
    def predict(self, df: IntoFrame | None = None) -> Any:
        """Return projected player statistics for `target_season`."""
        if self._projections_df is None:
            raise RuntimeError("MarcelProjector is not fitted yet. Call .fit(df) first.")
        if df is None or isinstance(df, pl.DataFrame):
            return self._projections_df.clone()
        arrow_tbl = self._projections_df.to_arrow()
        if type(df).__module__.startswith("pandas"):
            return arrow_tbl.to_pandas()
        return arrow_tbl


class Log5Model:
    """Bill James's Log5 / Odds-Ratio model for team head-to-head and batter-vs-pitcher matchups."""

    @staticmethod
    def team_matchup_prob(
        win_pct_a: float,
        win_pct_b: float,
        *,
        home_edge: float = 0.0,
    ) -> float:
        """Calculate probability that Team A defeats Team B using Bill James's Log5 equation.

        Formula:
            P(A beats B) = (p_A - p_A * p_B) / (p_A + p_B - 2 * p_A * p_B)
        """
        pa = min(max(win_pct_a + home_edge, 1e-6), 1.0 - 1e-6)
        pb = min(max(win_pct_b - home_edge, 1e-6), 1.0 - 1e-6)
        num = pa - pa * pb
        den = pa + pb - 2.0 * pa * pb
        return num / den

    @staticmethod
    def extended_pythagorean_home_win_prob(
        *,
        runs_scored_home: float,
        runs_allowed_home: float,
        runs_scored_away: float,
        runs_allowed_away: float,
        league_runs: float,
        exponent: float,
    ) -> float:
        """Probability the home team wins, extending James's Pythagorean formula to a head-to-head matchup.

        Cleary, Jeffries, Miller, Miller, Murray and Skiera (head-to-head Pythagorean): the home team's runs scored
        and allowed are rescaled by the opponent's, relative to the league average `league_runs`:
            RS_adj = RS_h * RA_a / R,   RA_adj = RA_h * RS_a / R
            P(home wins) = RS_adj^g / (RS_adj^g + RA_adj^g)
        Runs may be per game or totals as long as all four and `league_runs` use the same unit. The exponent is
        required because sources differ (the paper cites Baseball-Reference's 1.87 and notes 1.83 is also common).
        """
        rs_adj = runs_scored_home * runs_allowed_away / league_runs
        ra_adj = runs_allowed_home * runs_scored_away / league_runs
        num = rs_adj**exponent
        return num / (num + ra_adj**exponent)

    @staticmethod
    def batter_pitcher_matchup_rate(
        batter_rate: float,
        pitcher_rate: float,
        league_rate: float,
    ) -> float:
        """Calculate expected event rate for a batter vs. pitcher matchup using the Odds-Ratio / Log5 method.

        Formula:
            Odds_matchup = (Odds_batter * Odds_pitcher) / Odds_league
            P_matchup = Odds_matchup / (1 + Odds_matchup)
        """
        b = min(max(batter_rate, 1e-6), 1.0 - 1e-6)
        p = min(max(pitcher_rate, 1e-6), 1.0 - 1e-6)
        lg = min(max(league_rate, 1e-6), 1.0 - 1e-6)

        odds_b = b / (1.0 - b)
        odds_p = p / (1.0 - p)
        odds_lg = lg / (1.0 - lg)
        odds_m = (odds_b * odds_p) / odds_lg
        return odds_m / (1.0 + odds_m)

    @profiled(category="forecasting")
    def predict_df(
        self,
        df: IntoFrame,
        *,
        batter_col: str = "batter_rate",
        pitcher_col: str = "pitcher_rate",
        league_rate: float = 0.250,
        output_col: str = "matchup_prob",
    ) -> Any:
        """Vectorized Log5 batter-vs-pitcher matchup probability over any DataFrame."""
        nw_df = nw.from_native(df)
        b = nw.col(batter_col).cast(nw.Float64)
        p = nw.col(pitcher_col).cast(nw.Float64)
        odds_lg = league_rate / (1.0 - league_rate)

        odds_b = b / (1.0 - b)
        odds_p = p / (1.0 - p)
        odds_m = (odds_b * odds_p) / odds_lg
        prob_expr = (odds_m / (1.0 + odds_m)).alias(output_col)
        return nw.to_native(nw_df.with_columns(prob_expr))


class MarkovInningResults(BaseModel):
    """Frozen analytical results from the 24-state Absorbing Markov Chain half-inning model."""

    model_config = ConfigDict(frozen=True)

    expected_runs_per_half_inning: float
    expected_runs_per_9_innings: float
    expected_pa_per_half_inning: float
    state_expected_runs: dict[str, float] = Field(
        ..., description="Analytical expected runs from each of the 24 base-out states"
    )


class MarkovChainModel:
    """Exact 24-State Absorbing Markov Chain model of a baseball half-inning (Bukiet, Harold, & Palacios 1997).

    Given a batter or lineup's plate-appearance event probabilities (`p_1b`, `p_2b`, `p_3b`, `p_hr`,
    `p_bb`, `p_out`), constructs the `24 x 24` transient state transition matrix `Q` and expected
    immediate run reward vector `r`, then solves the exact fundamental matrix:
        `N = (I - Q)^(-1)`
        `E[Runs | state] = N @ r`
    """

    STATES: tuple[tuple[int, str], ...] = tuple(
        (outs, bases)
        for outs in (0, 1, 2)
        for bases in ("---", "1--", "-2-", "--3", "12-", "1-3", "-23", "123")
    )

    def __init__(self) -> None:
        self._results: MarkovInningResults | None = None

    @property
    def results(self) -> MarkovInningResults:
        if self._results is None:
            raise RuntimeError("MarkovChainModel is not fitted yet. Call .fit(...) first.")
        return self._results

    @profiled(category="forecasting")
    def fit(
        self,
        *,
        p_1b: float,
        p_2b: float,
        p_3b: float,
        p_hr: float,
        p_bb: float,
        p_out: float | None = None,
    ) -> Self:
        """Solve the 24-state absorbing Markov chain for the supplied event probabilities."""
        pos_sum = p_1b + p_2b + p_3b + p_hr + p_bb
        out_prob = (1.0 - pos_sum) if p_out is None else p_out
        total = pos_sum + out_prob
        if total <= 0:
            raise ValueError("Sum of event probabilities must be positive.")
        # Normalize to sum to 1.0
        p1, p2, p3, phr, pbb, po = (
            p_1b / total,
            p_2b / total,
            p_3b / total,
            p_hr / total,
            p_bb / total,
            out_prob / total,
        )

        state_to_idx = {s: idx for idx, s in enumerate(self.STATES)}
        q_mat = np.zeros((24, 24), dtype=np.float64)
        r_vec = np.zeros(24, dtype=np.float64)

        for idx, (outs, bases) in enumerate(self.STATES):
            r1 = 1 if bases[0] == "1" else 0
            r2 = 1 if bases[1] == "2" else 0
            r3 = 1 if bases[2] == "3" else 0
            num_runners = r1 + r2 + r3

            # 1. Out: outs + 1, runners stay, 0 runs
            if outs + 1 < 3:
                q_mat[idx, state_to_idx[(outs + 1, bases)]] += po

            # 2. Walk / HBP: forces runners
            if r1 == 0:
                new_b_bb = f"1{bases[1]}{bases[2]}"
                runs_bb = 0
            elif r2 == 0:
                new_b_bb = f"12{bases[2]}"
                runs_bb = 0
            elif r3 == 0:
                new_b_bb = "123"
                runs_bb = 0
            else:
                new_b_bb = "123"
                runs_bb = 1
            q_mat[idx, state_to_idx[(outs, new_b_bb)]] += pbb
            r_vec[idx] += pbb * runs_bb

            # 3. Single: runner on 2B and 3B score, runner on 1B advances to 2B
            runs_1b = r2 + r3
            new_b_1b = f"1{'2' if r1 else '-'}-"
            q_mat[idx, state_to_idx[(outs, new_b_1b)]] += p1
            r_vec[idx] += p1 * runs_1b

            # 4. Double: runner on 2B and 3B score, runner on 1B advances to 3B
            runs_2b = r2 + r3
            new_b_2b = f"-2{'3' if r1 else '-'}"
            q_mat[idx, state_to_idx[(outs, new_b_2b)]] += p2
            r_vec[idx] += p2 * runs_2b

            # 5. Triple: all baserunners score, batter on 3B
            runs_3b = num_runners
            q_mat[idx, state_to_idx[(outs, "--3")]] += p3
            r_vec[idx] += p3 * runs_3b

            # 6. Home Run: all baserunners + batter score, bases empty
            runs_hr = num_runners + 1
            q_mat[idx, state_to_idx[(outs, "---")]] += phr
            r_vec[idx] += phr * runs_hr

        # Fundamental matrix N = (I - Q)^(-1)
        ident = np.eye(24, dtype=np.float64)
        n_mat = np.linalg.inv(ident - q_mat)
        expected_runs_by_state = n_mat @ r_vec
        expected_pa_from_start = float(np.sum(n_mat[0, :]))
        er_half_inning = float(expected_runs_by_state[0])

        state_dict = {
            f"{outs}|{bases}": float(expected_runs_by_state[i])
            for i, (outs, bases) in enumerate(self.STATES)
        }
        self._results = MarkovInningResults(
            expected_runs_per_half_inning=er_half_inning,
            expected_runs_per_9_innings=er_half_inning * 9.0,
            expected_pa_per_half_inning=expected_pa_from_start,
            state_expected_runs=state_dict,
        )
        return self


class MonteCarloSimulationResults(BaseModel):
    """Frozen summary statistics from a seeded Monte Carlo baseball simulation."""

    model_config = ConfigDict(frozen=True)

    n_simulations: int
    seed: int
    mean_runs_per_game: float
    std_runs_per_game: float
    median_runs_per_game: float
    ci_95_lower: float
    ci_95_upper: float
    shutout_prob: float


class MonteCarloSimulator:
    """Seeded Monte Carlo 9-inning game simulator parameterized by event probabilities."""

    def __init__(self, *, n_simulations: int = 2000, seed: int = 42, innings: int = 9) -> None:
        self.n_simulations = n_simulations
        self.seed = seed
        self.innings = innings
        self._results: MonteCarloSimulationResults | None = None

    @property
    def results(self) -> MonteCarloSimulationResults:
        if self._results is None:
            raise RuntimeError(
                "MonteCarloSimulator has not been run yet. Call .simulate(...) first."
            )
        return self._results

    @profiled(category="forecasting")
    def simulate(
        self,
        *,
        p_1b: float,
        p_2b: float,
        p_3b: float,
        p_hr: float,
        p_bb: float,
    ) -> MonteCarloSimulationResults:
        """Simulate `n_simulations` games of `innings` innings and return frozen distribution diagnostics."""
        pos_sum = p_1b + p_2b + p_3b + p_hr + p_bb
        p_out = max(0.0, 1.0 - pos_sum)
        probs = np.array([p_out, p_bb, p_1b, p_2b, p_3b, p_hr], dtype=np.float64)
        probs = probs / probs.sum()

        rng = np.random.default_rng(self.seed)
        game_runs = np.zeros(self.n_simulations, dtype=np.int64)

        for g_idx in range(self.n_simulations):
            total_r = 0
            for _ in range(self.innings):
                outs = 0
                r1, r2, r3 = 0, 0, 0
                while outs < 3:
                    ev = int(rng.choice(6, p=probs))
                    if ev == 0:  # out
                        outs += 1
                    elif ev == 1:  # walk/hbp
                        if r1 and r2 and r3:
                            total_r += 1
                        elif r1 and r2:
                            r3 = 1
                        elif r1:
                            r2 = 1
                        else:
                            r1 = 1
                    elif ev == 2:  # single
                        total_r += r2 + r3
                        r3 = 0
                        r2 = r1
                        r1 = 1
                    elif ev == 3:  # double
                        total_r += r2 + r3
                        r3 = r1
                        r2 = 1
                        r1 = 0
                    elif ev == 4:  # triple
                        total_r += r1 + r2 + r3
                        r3 = 1
                        r2 = 0
                        r1 = 0
                    else:  # home run
                        total_r += r1 + r2 + r3 + 1
                        r1, r2, r3 = 0, 0, 0
            game_runs[g_idx] = total_r

        self._results = MonteCarloSimulationResults(
            n_simulations=self.n_simulations,
            seed=self.seed,
            mean_runs_per_game=float(np.mean(game_runs)),
            std_runs_per_game=float(np.std(game_runs, ddof=1)),
            median_runs_per_game=float(np.median(game_runs)),
            ci_95_lower=float(np.percentile(game_runs, 2.5)),
            ci_95_upper=float(np.percentile(game_runs, 97.5)),
            shutout_prob=float(np.mean(game_runs == 0)),
        )
        return self._results


__all__ = [
    "CatcherFramingModel",
    "CatcherFramingResults",
    "ExpectedOutcomeModel",
    "ExpectedOutcomeResults",
    "Log5Model",
    "MarcelProjector",
    "MarcelResults",
    "MarkovChainModel",
    "MarkovInningResults",
    "MonteCarloSimulationResults",
    "MonteCarloSimulator",
    "OutsAboveAverageModel",
    "OutsAboveAverageResults",
    "PitchQualityModel",
    "PitchQualityResults",
]
