"""Statistical forecasting, matchup, and simulation models (Marcel, Log5, Absorbing Markov Chain, Monte Carlo)."""

from __future__ import annotations

from typing import Any, Self

import narwhals as nw
import numpy as np
import polars as pl
from narwhals.typing import IntoFrame
from pydantic import BaseModel, ConfigDict, Field

from sabermetricspy.schema import require_no_nulls, require_values, to_polars_df
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
       plate appearances of league-average production to the weighted total (Tango's Beltran example:
       7,938 weighted PA + 1,200 = 9,138), the league rate mixed from the player's own seasons and PA.
    3. Apply the age adjustment (`+0.006 * (29 - age)` if `age < 29`, `-0.003 * (age - 29)` if `age > 29`).

    Pitchers (Tango's March 2004 post): weights `3/2/1`, innings in place of plate appearances, and the `200`
    in the playing-time formula replaced by 25 for relievers or 60 for starters (part-timers in between by GS/G).
    Configure with `season_weights=(3, 2, 1)`, `exposure_col="ip"` and `playing_time_base` (a number, or the name of
    a column holding each player's base), or call `MarcelProjector.for_pitchers`. Tango states no innings
    equivalent for the regression step; `for_pitchers` uses 266.67 IP, the amount that reproduces the reliability
    column of his published 2004 and 2012 pitcher files (869 of 870 and 941 of 943 rows), an inference from those
    files, not a number he wrote. No source supports a 134 IP constant.

    Each projection carries `proj_reliability`, Tango's reliability: the weighted exposure over itself plus the
    regression amount (his "how much of the forecast is based on his performance").

    Differences from the published method (see docs/METHODOLOGY.md): the final re-baselining step is not
    implemented; pitchers' own hitting must be left out of the league rates by the caller; players with no history
    are not projected.
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

    @classmethod
    def for_pitchers(
        cls, *, target_season: int = 2025, playing_time_base: float | str = 60.0
    ) -> MarcelProjector:
        """Tango's pitcher configuration: weights 3/2/1, innings, and 266.67 IP of regression (see the class docs).

        `playing_time_base` is his 60 innings for starters or 25 for relievers, or the name of a column holding
        each pitcher's base (in between for part-time starters, by GS/G).
        """
        return cls(
            target_season=target_season,
            season_weights=(3.0, 2.0, 1.0),
            regression_pa=800.0 / 3.0,
            rate_cols=("hr", "bb", "so", "h", "er"),
            exposure_col="ip",
            playing_time_base=playing_time_base,
        )

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

        # Each season's league rate, so a player's league-average component can follow his own seasons (Tango's Beltran example).
        present_cols = [c for c in league_rates if c in recent.columns]
        season_rates = recent.group_by("season").agg(
            [
                (pl.col(c).sum() / pl.col(self.exposure_col).sum()).alias(f"_lg_{c}")
                for c in present_cols
            ]
        )
        recent = recent.join(season_rates, on="season")

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
        for col in present_cols:
            agg_exprs.append(
                (pl.col(self.exposure_col) * pl.col("_recency_w") * pl.col(f"_lg_{col}"))
                .sum()
                .alias(f"_wl_{col}")
            )

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

        player_df = player_df.with_columns(
            age_mult.alias("age_factor"),
            (pl.col("_weighted_exp") / (pl.col("_weighted_exp") + self.regression_pa)).alias(
                "proj_reliability"
            ),
        )

        proj_cols: list[pl.Expr] = [pl.lit(self.target_season).alias("target_season")]

        for col in present_cols:
            # Tango adds `regression_pa` of league average, mixed from the player's own seasons, to the weighted total.
            league_component = self.regression_pa * pl.col(f"_wl_{col}") / pl.col("_weighted_exp")
            regressed_rate = (
                (pl.col(f"_w_{col}") + league_component)
                / (pl.col("_weighted_exp") + self.regression_pa)
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
        home_advantage: float = 0.5,
    ) -> float:
        """Calculate probability that Team A defeats Team B using Bill James's Log5 equation.

        Formula:
            P(A beats B) = (p_A - p_A * p_B) / (p_A + p_B - 2 * p_A * p_B)

        `home_advantage` is the home team's win probability in an even matchup (0.54 for MLB), as in Tango's
        Log5 page, and team A is then the home team:
            P = p_A (1 - p_B) HA / (p_A (1 - p_B) HA + (1 - p_A) p_B (1 - HA))
        The default 0.5 means no home effect, which reduces to plain Log5. Two equal teams return exactly HA.
        """
        pa = min(max(win_pct_a, 1e-6), 1.0 - 1e-6)
        pb = min(max(win_pct_b, 1e-6), 1.0 - 1e-6)
        num = pa * (1.0 - pb) * home_advantage
        den = num + (1.0 - pa) * pb * (1.0 - home_advantage)
        return num / den

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
    state_expected_plate_appearances: dict[str, float] = Field(
        default_factory=dict,
        description="Expected plate appearances until the third out from each state ('outs|bases')",
    )
    transition_probabilities: dict[str, dict[str, float]] = Field(
        default_factory=dict,
        description="Row-stochastic transition matrix keyed 'outs|bases' to 'outs|bases' or '3' (three outs); filled by fit_transitions",
    )
    plate_appearances: int = Field(
        default=0, description="Observed plays behind the transition matrix (fit_transitions)"
    )


class MarkovChainModel:
    """Exact 24-state absorbing Markov chain of a baseball half-inning, estimated from play-by-play.

    `fit_transitions` is the construction in Albert, Baumer & Marchi, *Analyzing Baseball Data with R* (3rd ed.),
    chapter 9.2: the observed frequency of each next base-out state gives the transition matrix `P`, three outs is
    the absorbing state, `N = (I - Q)^-1` counts visits to each state, and expected runs from a state are `N @ r`.
    Event-probability chains with hand-chosen advancement rules were removed in 1.4.0 (no published method).
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
            raise RuntimeError(
                "MarkovChainModel is not fitted yet. Call .fit_transitions(df) first."
            )
        return self._results

    @profiled(category="forecasting")
    def fit_transitions(self, df: IntoFrame) -> Self:
        """Estimate the 24 x 25 transition matrix from play-by-play and solve the absorbing chain exactly.

        This is the construction in Albert, Baumer and Marchi, *Analyzing Baseball Data with R* (3rd ed.), chapter 9:
        each row of `P` is the observed frequency of the next base-out state, three outs is the absorbing state,
        `N = (I - Q)^-1` counts visits to each state, and expected runs from a state are `N @ r` where `r` is the
        mean runs scored on a play from that state. Pass batting plays from complete half-innings (three outs)
        only; the book's own filter also drops plays that change neither the state nor the score.

        Requires `outs_before`, `base_state_before`, `outs_after`, `base_state_after` (bases as '---' to '123'; ignored
        once `outs_after` is 3) and `runs_on_play`. Raises when any of the 24 states was never observed.
        """
        pl_df = to_polars_df(df)
        required = {
            "outs_before",
            "base_state_before",
            "outs_after",
            "base_state_after",
            "runs_on_play",
        }
        missing = required - set(pl_df.columns)
        if missing:
            raise ValueError(
                f"Input dataframe for MarkovChainModel.fit_transitions is missing columns: {sorted(missing)}"
            )
        what = "MarkovChainModel.fit_transitions"
        require_no_nulls(
            pl_df.select("outs_before", "base_state_before", "outs_after", "runs_on_play"),
            ("outs_before", "base_state_before", "outs_after", "runs_on_play"),
            what,
        )
        require_values(pl_df, "outs_before", (0, 1, 2), what)
        require_values(pl_df, "outs_after", (0, 1, 2, 3), what)
        bases = ["---", "1--", "-2-", "--3", "12-", "1-3", "-23", "123"]
        require_values(pl_df, "base_state_before", bases, what)
        still_batting = pl_df.filter(pl.col("outs_after") < 3)
        require_no_nulls(still_batting, ("base_state_after",), what)
        require_values(still_batting, "base_state_after", bases, what)
        if pl_df.filter(pl.col("outs_after") < pl.col("outs_before")).height:
            raise ValueError(f"{what}: outs_after is below outs_before on some plays.")
        if pl_df.filter(pl.col("runs_on_play") < 0).height:
            raise ValueError(f"{what}: runs_on_play is negative on some plays.")
        idx = {s: i for i, s in enumerate(self.STATES)}
        counts = np.zeros((24, 25), dtype=np.float64)
        runs_sum = np.zeros(24, dtype=np.float64)
        for row in (
            pl_df.filter(pl.col("outs_before").is_between(0, 2))
            .group_by(["outs_before", "base_state_before", "outs_after", "base_state_after"])
            .agg(pl.len().alias("n"), pl.col("runs_on_play").sum().alias("runs"))
            .iter_rows(named=True)
        ):
            start = idx[(int(row["outs_before"]), str(row["base_state_before"]))]
            outs_after = int(row["outs_after"])
            end = 24 if outs_after >= 3 else idx[(outs_after, str(row["base_state_after"]))]
            counts[start, end] += row["n"]
            runs_sum[start] += row["runs"]
        totals = counts.sum(axis=1)
        unseen = [f"{o}|{b}" for (o, b), t in zip(self.STATES, totals, strict=True) if t == 0]
        if unseen:
            raise ValueError(f"No plays observed from base-out states: {unseen}")
        p_mat = counts / totals[:, None]
        q_mat = p_mat[:, :24]
        reaches_end = p_mat[:, 24] > 0
        for _ in range(24):
            reaches_end = reaches_end | (q_mat[:, reaches_end].sum(axis=1) > 0)
        if not reaches_end.all():
            stuck = [
                f"{o}|{b}" for (o, b), ok in zip(self.STATES, reaches_end, strict=True) if not ok
            ]
            raise ValueError(
                f"{what}: from these states the observed plays never reach three outs: {stuck}. "
                "Pass complete half-innings only."
            )
        n_mat = np.linalg.inv(np.eye(24) - q_mat)
        reward = runs_sum / totals
        expected_runs = n_mat @ reward
        expected_pa = n_mat.sum(axis=1)
        names = [f"{o}|{b}" for o, b in self.STATES]
        self._results = MarkovInningResults(
            expected_runs_per_half_inning=float(expected_runs[0]),
            expected_runs_per_9_innings=float(expected_runs[0]) * 9.0,
            expected_pa_per_half_inning=float(expected_pa[0]),
            state_expected_runs=dict(zip(names, map(float, expected_runs), strict=True)),
            state_expected_plate_appearances=dict(zip(names, map(float, expected_pa), strict=True)),
            transition_probabilities={
                names[i]: {
                    **{names[j]: float(p_mat[i, j]) for j in range(24) if p_mat[i, j] > 0},
                    **({"3": float(p_mat[i, 24])} if p_mat[i, 24] > 0 else {}),
                }
                for i in range(24)
            },
            plate_appearances=int(totals.sum()),
        )
        return self

    def state_distribution(
        self, plate_appearances: int, start: tuple[int, str] = (0, "---")
    ) -> dict[str, float]:
        """State probabilities after `plate_appearances` batters from `start`; requires fit_transitions.

        Keys are 'outs|bases' plus '3' for three outs. Zero-probability states are omitted.
        """
        table = self.results.transition_probabilities
        if not table:
            raise RuntimeError("state_distribution needs a model fitted with fit_transitions().")
        if plate_appearances < 0:
            raise ValueError(f"plate_appearances must be 0 or more, got {plate_appearances}.")
        if f"{start[0]}|{start[1]}" not in table:
            raise ValueError(
                f"start {start!r} is not a base-out state; use (outs 0 to 2, bases such as '---' or '1-3')."
            )
        dist = {f"{start[0]}|{start[1]}": 1.0}
        for _ in range(plate_appearances):
            nxt: dict[str, float] = {}
            for state, prob in dist.items():
                if state == "3":
                    nxt["3"] = nxt.get("3", 0.0) + prob
                    continue
                for new_state, t in table[state].items():
                    nxt[new_state] = nxt.get(new_state, 0.0) + prob * t
            dist = nxt
        return dist


__all__ = [
    "Log5Model",
    "MarcelProjector",
    "MarcelResults",
    "MarkovChainModel",
    "MarkovInningResults",
]
