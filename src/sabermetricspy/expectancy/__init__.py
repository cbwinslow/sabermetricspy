"""Empirical Run Expectancy (RE24), Count Expectancy (RE288), Linear Weights, Steal Breakeven, and Win Probability (WPA, LI) estimators."""

from __future__ import annotations

import math
from collections.abc import Mapping
from typing import Any, Self

import polars as pl
from narwhals.typing import IntoFrame
from pydantic import BaseModel, ConfigDict, Field

from sabermetricspy.schema import require_no_nulls, require_values, to_polars_df
from sabermetricspy.telemetry import profiled
from sabermetricspy.types.enums import BaseState

# Published 24-state run-expectancy matrix from the FanGraphs Library RE24 page, which describes it as
# roughly neutral for 2014 (4.15 runs per game): https://library.fangraphs.com/misc/re24/
# Indexed by (outs_before: int, base_state: BaseState) -> expected runs to end of inning.
# Pass a fitted RunExpectancyMatrix for a specific season; tests/golden/run_expectancy_table.yaml pins this table.
DEFAULT_RE24_TABLE: dict[tuple[int, str], float] = {
    (0, "---"): 0.461,
    (1, "---"): 0.243,
    (2, "---"): 0.095,
    (0, "1--"): 0.831,
    (1, "1--"): 0.489,
    (2, "1--"): 0.214,
    (0, "-2-"): 1.068,
    (1, "-2-"): 0.644,
    (2, "-2-"): 0.305,
    (0, "12-"): 1.373,
    (1, "12-"): 0.908,
    (2, "12-"): 0.343,
    (0, "--3"): 1.426,
    (1, "--3"): 0.865,
    (2, "--3"): 0.413,
    (0, "1-3"): 1.798,
    (1, "1-3"): 1.140,
    (2, "1-3"): 0.471,
    (0, "-23"): 1.920,
    (1, "-23"): 1.352,
    (2, "-23"): 0.570,
    (0, "123"): 2.282,
    (1, "123"): 1.520,
    (2, "123"): 0.736,
}

# Expected runs for the bases-empty, no-out state; the anchor used to rescale the table to another run environment.
_RE24_ANCHOR = DEFAULT_RE24_TABLE[(0, "---")]

# Run value of reaching each ball-strike count, in batting runs relative to the 0-0 count, from John Walsh,
# "Searching for the game's best pitch", The Hardball Times, 2008-02-26, Table 1:
# https://tht.fangraphs.com/searching-for-the-games-best-pitch
# Context-free: the values are not split by base-out state. tests/golden/count_run_values.yaml pins every cell.
WALSH_COUNT_RUN_VALUES: dict[tuple[int, int], float] = {
    (0, 0): 0.000,
    (1, 0): 0.038,
    (2, 0): 0.104,
    (3, 0): 0.220,
    (0, 1): -0.044,
    (1, 1): -0.015,
    (2, 1): 0.037,
    (3, 1): 0.142,
    (0, 2): -0.106,
    (1, 2): -0.082,
    (2, 2): -0.039,
    (3, 2): 0.059,
}


@profiled(category="expectancy")
def count_run_value(balls: int, strikes: int) -> float:
    """Return Walsh's run value of a plate appearance reaching `balls`-`strikes`, relative to 0-0."""
    try:
        return WALSH_COUNT_RUN_VALUES[(balls, strikes)]
    except KeyError:
        raise ValueError(
            f"count {balls}-{strikes} is not a live count (balls 0-3, strikes 0-2)"
        ) from None


def _walk_transition(base_state: str) -> tuple[str, int]:
    """Return the base state after a walk and the runs forced in, from a `'123'`-style base state."""
    first, second, third = (c != "-" for c in base_state)
    runs = int(first and second and third)
    new_second = first or second
    new_third = third or (first and second)
    return f"1{'2' if new_second else '-'}{'3' if new_third else '-'}", runs


class RE24Results(BaseModel):
    """Frozen statsmodels-style diagnostics and learned state table for RunExpectancyMatrix."""

    model_config = ConfigDict(frozen=True)

    state_expectancy: dict[str, float] = Field(
        ..., description="Mapping of 'outs|base_state' (e.g. '0|---', '1|123') to expected runs"
    )
    state_counts: dict[str, int] = Field(
        default_factory=dict, description="Sample count per base-out state"
    )
    state_std_err: dict[str, float] = Field(
        default_factory=dict, description="Standard error of mean runs per state"
    )
    total_plays: int = 0
    prior_strength: float = 0.0

    def lookup(self, outs: int, base_state: BaseState | str) -> float:
        """Return expected runs for `(outs, base_state)`, returning 0.0 when `outs >= 3`."""
        if outs >= 3:
            return 0.0
        key = f"{outs}|{base_state!s}"
        return self.state_expectancy.get(key, 0.0)

    def steal_breakeven_rate(
        self,
        outs: int,
        start_state: BaseState | str = BaseState.FIRST,
        success_state: BaseState | str = BaseState.SECOND,
        caught_state: BaseState | str = BaseState.EMPTY,
    ) -> float:
        """Compute stolen-base breakeven success probability: (RE_0 - RE_C) / (RE_S - RE_C)."""
        re_0 = self.lookup(outs, start_state)
        re_s = self.lookup(outs, success_state)
        re_c = self.lookup(outs + 1, caught_state)
        denom = re_s - re_c
        if denom <= 0:
            return 1.0
        return (re_0 - re_c) / denom


class RunExpectancyMatrix:
    """Empirical 24-State Run Expectancy (RE24) estimator and play-valuation transformer.

    Follows the scikit-learn `.fit()` / `.transform()` API and attaches a frozen `.results`
    diagnostics object (`RE24Results`).
    """

    def __init__(self, *, prior_strength: float = 0.0) -> None:
        """Initialize RunExpectancyMatrix.

        Args:
            prior_strength: Optional Empirical Bayes shrinkage weight (in pseudo-observations)
                toward the canonical MLB 24-state prior. Set to 0.0 for pure sample means.
        """
        self.prior_strength = prior_strength
        self._results: RE24Results | None = None

    @classmethod
    def from_default(cls) -> RunExpectancyMatrix:
        """Return a pre-fitted RunExpectancyMatrix initialized with the canonical MLB 24-state table."""
        inst = cls(prior_strength=0.0)
        state_exp = {f"{o}|{s}": val for (o, s), val in DEFAULT_RE24_TABLE.items()}
        inst._results = RE24Results(
            state_expectancy=state_exp,
            state_counts=dict.fromkeys(state_exp, 0),
            state_std_err=dict.fromkeys(state_exp, 0.0),
            total_plays=0,
            prior_strength=0.0,
        )
        return inst

    @property
    def results(self) -> RE24Results:
        """Return the frozen RE24Results object."""
        if self._results is None:
            raise RuntimeError(
                "RunExpectancyMatrix is not fitted yet. Call .fit(df) or .from_default() first."
            )
        return self._results

    @profiled(category="expectancy")
    def fit(self, df: IntoFrame) -> Self:
        """Fit the 24-state run expectancy table from play-by-play records.

        Accepts columns:
        - `outs_before` (0, 1, 2)
        - `base_state_before` ('---', '1--', etc.) OR boolean (`on_1b`, `on_2b`, `on_3b`)
        - `runs_rest_of_inning` (or automatically computes it if `game_id`, `inning`, `half_inning`, `runs_on_play` exist).
        """
        pl_df = to_polars_df(df)

        if "base_state_before" not in pl_df.columns:
            if {"on_1b", "on_2b", "on_3b"}.issubset(pl_df.columns):
                pl_df = pl_df.with_columns(
                    (
                        pl.when(pl.col("on_1b")).then(pl.lit("1")).otherwise(pl.lit("-"))
                        + pl.when(pl.col("on_2b")).then(pl.lit("2")).otherwise(pl.lit("-"))
                        + pl.when(pl.col("on_3b")).then(pl.lit("3")).otherwise(pl.lit("-"))
                    ).alias("base_state_before")
                )
            else:
                raise ValueError(
                    "Input dataframe must contain 'base_state_before' or ('on_1b', 'on_2b', 'on_3b')."
                )

        if "runs_rest_of_inning" not in pl_df.columns:
            if {"game_id", "inning", "half_inning", "runs_on_play"}.issubset(pl_df.columns):
                # Compute total runs in half-inning minus cumulative runs scored prior to this play
                pl_df = pl_df.with_columns(
                    (
                        pl.col("runs_on_play").sum().over(["game_id", "inning", "half_inning"])
                        - pl.col("runs_on_play")
                        .cum_sum()
                        .over(["game_id", "inning", "half_inning"])
                        + pl.col("runs_on_play")
                    ).alias("runs_rest_of_inning")
                )
            else:
                raise ValueError(
                    "Input dataframe must contain 'runs_rest_of_inning' or ('game_id', 'inning', 'half_inning', 'runs_on_play')."
                )

        valid = pl_df.filter((pl.col("outs_before") >= 0) & (pl.col("outs_before") <= 2))
        grouped = valid.group_by(["outs_before", "base_state_before"]).agg(
            pl.col("runs_rest_of_inning").mean().alias("mean_roi"),
            pl.col("runs_rest_of_inning").count().alias("n"),
            pl.col("runs_rest_of_inning").std().fill_null(0.0).alias("std_roi"),
        )

        state_exp: dict[str, float] = {
            f"{o}|{s}": val for (o, s), val in DEFAULT_RE24_TABLE.items()
        }
        state_counts: dict[str, int] = dict.fromkeys(state_exp, 0)
        state_se: dict[str, float] = dict.fromkeys(state_exp, 0.0)

        for row in grouped.iter_rows(named=True):
            o = int(row["outs_before"])
            s = str(row["base_state_before"])
            key = f"{o}|{s}"
            n = int(row["n"])
            mean_val = float(row["mean_roi"])
            prior_val = DEFAULT_RE24_TABLE.get((o, s), mean_val)
            if self.prior_strength > 0:
                shrunk = (n * mean_val + self.prior_strength * prior_val) / (
                    n + self.prior_strength
                )
            else:
                shrunk = mean_val
            state_exp[key] = shrunk
            state_counts[key] = n
            state_se[key] = float(row["std_roi"]) / (n**0.5) if n > 0 else 0.0

        self._results = RE24Results(
            state_expectancy=state_exp,
            state_counts=state_counts,
            state_std_err=state_se,
            total_plays=len(valid),
            prior_strength=self.prior_strength,
        )
        return self

    @profiled(category="expectancy")
    def transform(self, df: IntoFrame) -> Any:
        """Annotate play-by-play records with `re_before`, `re_after`, and `run_value` (RE24).

        Formula: `run_value = runs_on_play + re_after - re_before`
        """
        res = self.results
        pl_df = to_polars_df(df)

        if "base_state_before" not in pl_df.columns and {"on_1b", "on_2b", "on_3b"}.issubset(
            pl_df.columns
        ):
            pl_df = pl_df.with_columns(
                (
                    pl.when(pl.col("on_1b")).then(pl.lit("1")).otherwise(pl.lit("-"))
                    + pl.when(pl.col("on_2b")).then(pl.lit("2")).otherwise(pl.lit("-"))
                    + pl.when(pl.col("on_3b")).then(pl.lit("3")).otherwise(pl.lit("-"))
                ).alias("base_state_before")
            )

        if "base_state_after" not in pl_df.columns and {
            "on_1b_after",
            "on_2b_after",
            "on_3b_after",
        }.issubset(pl_df.columns):
            pl_df = pl_df.with_columns(
                (
                    pl.when(pl.col("on_1b_after")).then(pl.lit("1")).otherwise(pl.lit("-"))
                    + pl.when(pl.col("on_2b_after")).then(pl.lit("2")).otherwise(pl.lit("-"))
                    + pl.when(pl.col("on_3b_after")).then(pl.lit("3")).otherwise(pl.lit("-"))
                ).alias("base_state_after")
            )

        key_before = pl.col("outs_before").cast(pl.Utf8) + pl.lit("|") + pl.col("base_state_before")
        key_after = pl.col("outs_after").cast(pl.Utf8) + pl.lit("|") + pl.col("base_state_after")

        re_before_expr = key_before.replace_strict(res.state_expectancy, default=0.0).alias(
            "re_before"
        )
        re_after_expr = (
            pl.when(pl.col("outs_after") >= 3)
            .then(0.0)
            .otherwise(key_after.replace_strict(res.state_expectancy, default=0.0))
            .alias("re_after")
        )

        pl_df = pl_df.with_columns(re_before_expr, re_after_expr)
        pl_df = pl_df.with_columns(
            (pl.col("runs_on_play") + pl.col("re_after") - pl.col("re_before")).alias("run_value")
        )

        if isinstance(df, pl.DataFrame):
            return pl_df
        arrow_tbl = pl_df.to_arrow()
        if type(df).__module__.startswith("pandas"):
            return arrow_tbl.to_pandas()
        return arrow_tbl


class LinearWeightsResults(BaseModel):
    """Frozen results from empirical LinearWeightsEstimator."""

    model_config = ConfigDict(frozen=True)

    raw_event_run_values: dict[str, float]
    run_values_above_out: dict[str, float]
    woba_weights: dict[str, float]
    woba_scale: float
    out_run_value: float


class LinearWeightsEstimator:
    """Empirical Linear Weights and wOBA weight estimator from RE24 play-by-play run values.

    Implements Tom Tango's derivation of wOBA weights:
    1. Compute mean `run_value` per event (`walk`, `hit_by_pitch`, `single`, `double`, `triple`, `home_run`, `out`).
    2. Shift all positive events relative to `out` (`RV_above_out = RV_event - RV_out`).
    3. Multiply by `woba_scale` so league wOBA equals league OBP.
    """

    def __init__(self, *, target_lg_obp: float | None = None) -> None:
        self.target_lg_obp = target_lg_obp
        self._results: LinearWeightsResults | None = None

    @property
    def results(self) -> LinearWeightsResults:
        if self._results is None:
            raise RuntimeError("LinearWeightsEstimator is not fitted yet. Call .fit(df) first.")
        return self._results

    @profiled(category="expectancy")
    def fit(
        self, df: IntoFrame, *, event_col: str = "play_outcome", rv_col: str = "run_value"
    ) -> Self:
        pl_df = to_polars_df(df)

        grouped = pl_df.group_by(event_col).agg(
            pl.col(rv_col).mean().alias("mean_rv"),
            pl.col(rv_col).count().alias("count"),
        )
        raw_rv: dict[str, float] = {}
        counts: dict[str, int] = {}
        for row in grouped.iter_rows(named=True):
            ev_name = str(row[event_col]).lower()
            raw_rv[ev_name] = float(row["mean_rv"])
            counts[ev_name] = int(row["count"])

        out_rv = raw_rv.get("out", raw_rv.get("field_out", -0.26))
        above_out = {k: v - out_rv for k, v in raw_rv.items()}

        # Compute unscaled wOBA and empirical OBP on sample to derive woba_scale
        pos_events = ("walk", "hit_by_pitch", "single", "double", "triple", "home_run")
        total_weighted = sum(above_out.get(e, 0.0) * counts.get(e, 0) for e in pos_events)
        total_on_base = sum(counts.get(e, 0) for e in pos_events)
        total_pa = sum(counts.values())
        unscaled_woba = total_weighted / total_pa if total_pa > 0 else 0.250
        sample_obp = (total_on_base / total_pa) if total_pa > 0 else 0.315
        target_obp = self.target_lg_obp if self.target_lg_obp is not None else sample_obp
        woba_scale = target_obp / unscaled_woba if unscaled_woba > 0 else 1.24

        woba_w = {e: above_out.get(e, 0.0) * woba_scale for e in pos_events}
        self._results = LinearWeightsResults(
            raw_event_run_values=raw_rv,
            run_values_above_out=above_out,
            woba_weights=woba_w,
            woba_scale=woba_scale,
            out_run_value=out_rv,
        )
        return self


class RE288Results(BaseModel):
    """Frozen diagnostics and learned 288-state table for CountExpectancyMatrix (RE288)."""

    model_config = ConfigDict(frozen=True)

    state_expectancy: dict[str, float] = Field(
        ...,
        description="Mapping of 'outs|base_state|balls|strikes' (e.g. '0|---|3|2') to expected runs; states with no data are absent",
    )
    state_counts: dict[str, int] = Field(
        default_factory=dict,
        description="Plate appearances that reached each fitted state (one per plate appearance per count)",
    )
    total_plate_appearances: int = 0
    prior_strength: float = 0.0

    def lookup(
        self,
        outs: int,
        base_state: BaseState | str,
        balls: int = 0,
        strikes: int = 0,
    ) -> float | None:
        """Return expected runs for `(outs, base_state, balls, strikes)`: 0.0 when `outs >= 3`, None when unfitted."""
        if outs >= 3:
            return 0.0
        b = min(max(balls, 0), 3)
        s = min(max(strikes, 0), 2)
        key = f"{outs}|{base_state!s}|{b}|{s}"
        return self.state_expectancy.get(key)

    def count_leverage(
        self, outs: int, base_state: BaseState | str, balls: int, strikes: int
    ) -> float | None:
        """Return the run-value swing between a ball and a strike, or None when a needed state is unfitted.

        A fourth ball is a walk: the forced-advance base state at 0-0, plus any run forced in. A third
        strike is an out at 0-0 with the bases unchanged.
        """
        if outs >= 3:
            return 0.0
        if balls < 3:
            re_ball = self.lookup(outs, base_state, balls + 1, strikes)
        else:
            walk_state, walk_runs = _walk_transition(str(base_state))
            walk_re = self.lookup(outs, walk_state, 0, 0)
            re_ball = None if walk_re is None else walk_re + walk_runs
        if strikes < 2:
            re_strike = self.lookup(outs, base_state, balls, strikes + 1)
        else:
            re_strike = self.lookup(outs + 1, base_state, 0, 0)
        if re_ball is None or re_strike is None:
            return None
        return max(0.0, re_ball - re_strike)


class CountExpectancyMatrix:
    """Empirical 288-State Count & Base-Out Run Expectancy (RE288) estimator and pitch valuation transformer.

    Evaluates all 288 states `3 outs x 8 base states x 4 ball counts x 3 strikes`. There is no built-in
    table: the table is estimated from the caller's data, and states with no data stay unfitted (null).
    Tango's published RE288 (http://tangotiger.com/index.php/site/re288-run-expectancy-by-the-24-base-out-states-x-12-plate-count-states-recu)
    shows the count effect depends on the base state, so a count offset added to RE24 would be wrong.
    """

    def __init__(
        self,
        *,
        prior: Mapping[str, float] | None = None,
        prior_strength: float = 0.0,
    ) -> None:
        """Initialize CountExpectancyMatrix.

        Args:
            prior: Optional caller-supplied table keyed 'outs|base_state|balls|strikes' to shrink toward.
            prior_strength: Pseudo-observations of weight on `prior`; requires `prior` when above zero.
        """
        if prior_strength > 0 and prior is None:
            raise ValueError("prior_strength > 0 requires a caller-supplied prior table")
        self.prior = dict(prior) if prior is not None else {}
        self.prior_strength = prior_strength
        self._results: RE288Results | None = None

    @property
    def results(self) -> RE288Results:
        if self._results is None:
            raise RuntimeError("CountExpectancyMatrix is not fitted yet. Call .fit(df) first.")
        return self._results

    @profiled(category="expectancy")
    def fit(self, df: IntoFrame) -> Self:
        """Fit the 288-state table from pitch-level records, counting each plate appearance once per count.

        A plate appearance that fouls off pitches at two strikes repeats a count; only the first pitch at
        each count in a plate appearance contributes, which is how Albert et al. (ABDWR 3e, ch. 6) average
        run value by count. Requires `pa_id` (any value that is constant within a plate appearance),
        `outs_before`, `base_state_before`, `balls`, `strikes`, `runs_rest_of_inning`, with rows in pitch order.
        """
        pl_df = to_polars_df(df)
        required = {
            "pa_id",
            "outs_before",
            "base_state_before",
            "balls",
            "strikes",
            "runs_rest_of_inning",
        }
        missing = required - set(pl_df.columns)
        if missing:
            raise ValueError(
                f"Input dataframe for CountExpectancyMatrix.fit is missing columns: {sorted(missing)}"
            )

        valid = pl_df.filter(
            (pl.col("outs_before").is_between(0, 2))
            & (pl.col("balls").is_between(0, 3))
            & (pl.col("strikes").is_between(0, 2))
        ).unique(subset=["pa_id", "balls", "strikes"], keep="first", maintain_order=True)
        grouped = valid.group_by(["outs_before", "base_state_before", "balls", "strikes"]).agg(
            pl.col("runs_rest_of_inning").mean().alias("mean_roi"),
            pl.col("runs_rest_of_inning").count().alias("n"),
        )

        state_exp: dict[str, float] = {}
        state_counts: dict[str, int] = {}
        for row in grouped.iter_rows(named=True):
            key = f"{int(row['outs_before'])}|{row['base_state_before']!s}|{int(row['balls'])}|{int(row['strikes'])}"
            n = int(row["n"])
            mean_val = float(row["mean_roi"])
            prior_val = self.prior.get(key)
            if self.prior_strength > 0 and prior_val is not None:
                mean_val = (n * mean_val + self.prior_strength * prior_val) / (
                    n + self.prior_strength
                )
            state_exp[key] = mean_val
            state_counts[key] = n

        self._results = RE288Results(
            state_expectancy=state_exp,
            state_counts=state_counts,
            total_plate_appearances=valid["pa_id"].n_unique(),
            prior_strength=self.prior_strength,
        )
        return self

    @profiled(category="expectancy")
    def transform(self, df: IntoFrame) -> Any:
        """Annotate pitch-level records with `re288_before`, `re288_after`, `pitch_run_value`, and `count_leverage`.

        Requires `outs_before`, `base_state_before`, `balls`, `strikes`, `outs_after`, `base_state_after`,
        `balls_after`, `strikes_after`, and `runs_on_play`. Pitches whose state was never fitted get null.
        """
        res = self.results
        pl_df = to_polars_df(df)

        key_before = (
            pl.col("outs_before").cast(pl.Utf8)
            + pl.lit("|")
            + pl.col("base_state_before")
            + pl.lit("|")
            + pl.col("balls").clip(0, 3).cast(pl.Utf8)
            + pl.lit("|")
            + pl.col("strikes").clip(0, 2).cast(pl.Utf8)
        )
        key_after = (
            pl.col("outs_after").cast(pl.Utf8)
            + pl.lit("|")
            + pl.col("base_state_after")
            + pl.lit("|")
            + pl.col("balls_after").clip(0, 3).cast(pl.Utf8)
            + pl.lit("|")
            + pl.col("strikes_after").clip(0, 2).cast(pl.Utf8)
        )

        leverage_map: dict[str, float] = {}
        for k in res.state_expectancy:
            o, bs, b, st = k.split("|")
            lev = res.count_leverage(int(o), bs, int(b), int(st))
            if lev is not None:
                leverage_map[k] = lev

        re_before_expr = key_before.replace_strict(
            res.state_expectancy, default=None, return_dtype=pl.Float64
        ).alias("re288_before")
        re_after_expr = (
            pl.when(pl.col("outs_after") >= 3)
            .then(0.0)
            .otherwise(
                key_after.replace_strict(
                    res.state_expectancy, default=None, return_dtype=pl.Float64
                )
            )
            .alias("re288_after")
        )
        leverage_expr = key_before.replace_strict(
            leverage_map, default=None, return_dtype=pl.Float64
        ).alias("count_leverage")

        pl_df = pl_df.with_columns(re_before_expr, re_after_expr, leverage_expr)
        pl_df = pl_df.with_columns(
            (pl.col("runs_on_play") + pl.col("re288_after") - pl.col("re288_before")).alias(
                "pitch_run_value"
            )
        )

        if isinstance(df, pl.DataFrame):
            return pl_df
        arrow_tbl = pl_df.to_arrow()
        if type(df).__module__.startswith("pandas"):
            return arrow_tbl.to_pandas()
        return arrow_tbl


class WinExpectancyResults(BaseModel):
    """Frozen table learned by WinExpectancyMatrix: the home team's win rate from each game state."""

    model_config = ConfigDict(frozen=True)

    state_expectancy: dict[str, float] = Field(
        ...,
        description="Mapping of 'inning|half|outs|base_state|score_diff' (e.g. '9|bottom|2|---|0') to the home win rate; states with no data are absent",
    )
    state_counts: dict[str, int] = Field(
        default_factory=dict, description="Plate appearances observed in each fitted state"
    )
    state_games: dict[str, int] = Field(
        default_factory=dict, description="Distinct games that reached each fitted state"
    )
    total_plate_appearances: int = 0

    def lookup(
        self,
        inning: int,
        half_inning: str,
        outs: int,
        base_state: BaseState | str,
        home_score_diff: int,
    ) -> float | None:
        """Return the fitted home win rate for a state, or None when no plate appearance reached it."""
        half = "top" if half_inning.lower().strip() in ("top", "t", "0", "away") else "bottom"
        return self.state_expectancy.get(f"{inning}|{half}|{outs}|{base_state!s}|{home_score_diff}")

    def standard_error(
        self,
        inning: int,
        half_inning: str,
        outs: int,
        base_state: BaseState | str,
        home_score_diff: int,
    ) -> float | None:
        """Binomial standard error sqrt(p (1 - p) / games) of a fitted state, or None when unfitted.

        Uses the number of distinct games, not plate appearances, because plate appearances in one game
        share one result.
        """
        half = "top" if half_inning.lower().strip() in ("top", "t", "0", "away") else "bottom"
        key = f"{inning}|{half}|{outs}|{base_state!s}|{home_score_diff}"
        p = self.state_expectancy.get(key)
        if p is None:
            return None
        return math.sqrt(p * (1.0 - p) / self.state_games[key])


class WinExpectancyMatrix:
    """Empirical win expectancy (WE): how often the home team won from each inning, half, outs, bases and score state.

    There is no built-in table; the table is the observed home win rate in the caller's play-by-play. Tom Tango's
    published tables (http://tangotiger.net/welist.html, a 2002 page that states no method; his current
    https://tangotiger.net/we.html is a model built from run expectancy) are references to compare with, not the
    construction used here. Cells with few games are noisy: check `results.state_games` or
    `results.standard_error()` before relying on one.
    """

    def __init__(self) -> None:
        self._results: WinExpectancyResults | None = None

    @property
    def results(self) -> WinExpectancyResults:
        if self._results is None:
            raise RuntimeError("WinExpectancyMatrix is not fitted yet. Call .fit(df) first.")
        return self._results

    @profiled(category="expectancy")
    def fit(self, df: IntoFrame) -> Self:
        """Fit from plate-appearance records, one row per plate appearance with the state before it.

        Requires `game_id`, `inning`, `is_bottom` (boolean, True when the home team bats), `outs_before` (0 to 2),
        `base_state_before` (one of the eight base states), `home_score_diff` (home minus away runs before the plate
        appearance) and `home_win` (1 when the home team won the game, else 0). Nulls and values outside these ranges
        raise `ValueError`. Pass plate appearances only: rows for substitutions or other non-batting events would be
        counted as plate appearances.

        A state's rate is the share of its plate appearances that occurred in games the home team won. The standard
        error reported by the results uses the number of games as the sample size, an approximation because the
        plate appearances of one game share a result.
        """
        pl_df = to_polars_df(df)
        required = {
            "game_id",
            "inning",
            "is_bottom",
            "outs_before",
            "base_state_before",
            "home_score_diff",
            "home_win",
        }
        missing = required - set(pl_df.columns)
        if missing:
            raise ValueError(
                f"Input dataframe for WinExpectancyMatrix.fit is missing columns: {sorted(missing)}"
            )
        what = "WinExpectancyMatrix.fit"
        require_no_nulls(pl_df, sorted(required), what)
        if pl_df.schema["is_bottom"] != pl.Boolean:
            raise ValueError(
                f"{what}: is_bottom must be boolean (True when the home team bats), got {pl_df.schema['is_bottom']}."
            )
        require_values(pl_df, "outs_before", (0, 1, 2), what)
        require_values(pl_df, "base_state_before", [b.value for b in BaseState], what)
        if pl_df.schema["home_win"] != pl.Boolean:
            require_values(pl_df, "home_win", (0, 1), what)
        for col in ("inning", "home_score_diff"):
            if not pl_df.schema[col].is_numeric() or (
                pl_df.schema[col].is_float() and (pl_df[col] != pl_df[col].round()).any()
            ):
                raise ValueError(f"{what}: {col} must hold whole numbers.")
        if (pl_df["inning"] < 1).any():
            raise ValueError(f"{what}: inning must be 1 or more.")
        valid = pl_df.with_columns(
            pl.col("inning").cast(pl.Int64),
            pl.col("home_score_diff").cast(pl.Int64),
            pl.col("home_win").cast(pl.Int64),
        )
        grouped = valid.group_by(
            ["inning", "is_bottom", "outs_before", "base_state_before", "home_score_diff"]
        ).agg(
            pl.col("home_win").mean().alias("rate"),
            pl.len().alias("n"),
            pl.col("game_id").n_unique().alias("games"),
        )
        state_exp: dict[str, float] = {}
        state_counts: dict[str, int] = {}
        state_games: dict[str, int] = {}
        for row in grouped.iter_rows(named=True):
            half = "bottom" if row["is_bottom"] else "top"
            key = (
                f"{int(row['inning'])}|{half}|{int(row['outs_before'])}|"
                f"{row['base_state_before']!s}|{int(row['home_score_diff'])}"
            )
            state_exp[key] = float(row["rate"])
            state_counts[key] = int(row["n"])
            state_games[key] = int(row["games"])
        self._results = WinExpectancyResults(
            state_expectancy=state_exp,
            state_counts=state_counts,
            state_games=state_games,
            total_plate_appearances=valid.height,
        )
        return self


class MarkovWinExpectancyResults(BaseModel):
    """Frozen diagnostics of MarkovWinExpectancy: how many plays built the transitions and the solved game length."""

    model_config = ConfigDict(frozen=True)

    n_plays: int
    max_inning: int
    max_run_diff: int


class MarkovWinExpectancy:
    """Win expectancy by dynamic programming over base-out transitions (Tango's construction for `we.html`).

    Tom Tango's win expectancy page (https://tangotiger.net/we.html) says it takes the actual run expectancy data
    "and simply ran it for every game state, recursively". This class does that: `fit` estimates, from plays in
    completed half-innings, the probability of each next base-out state and the runs scored on the play, and the
    win expectancy of every (inning, half, outs, bases, run difference) state is solved backward from the end of
    the game. The bottom of the 9th and later ends when the home team takes the lead; a game tied after the bottom
    of the 9th goes to extra innings, and the value after `max_inning` is 0.5. The two teams are identical and there
    is no home-field edge, so the top of the 1st with a tie is 0.5 (up to the run-difference cap), as in Tango's table.

    Tango's table uses completed innings through the 8th only; pass plays from such half-innings. Plays that change
    neither the base-out state nor the score are dropped, as in Albert and Marchi's construction.
    """

    STATES: tuple[tuple[int, str], ...] = tuple(
        (outs, bases)
        for outs in (0, 1, 2)
        for bases in ("---", "1--", "-2-", "--3", "12-", "1-3", "-23", "123")
    )

    def __init__(self, *, max_inning: int = 30, max_run_diff: int = 12) -> None:
        if max_inning < 9:
            raise ValueError("max_inning must be at least 9.")
        self.max_inning = max_inning
        self.max_run_diff = max_run_diff
        self._results: MarkovWinExpectancyResults | None = None
        self._value: dict[tuple[int, bool], Any] = {}

    @property
    def results(self) -> MarkovWinExpectancyResults:
        if self._results is None:
            raise RuntimeError("MarkovWinExpectancy is not fitted yet. Call .fit(df) first.")
        return self._results

    @profiled(category="expectancy")
    def fit(self, df: IntoFrame) -> Self:
        """Estimate the transitions from plays and solve every state's win expectancy.

        Requires `outs_before`, `base_state_before`, `outs_after`, `base_state_after` (ignored once `outs_after` is
        3) and `runs_on_play`, one row per batting play, the same columns as `MarkovChainModel.fit_transitions`.
        Raises when any of the 24 base-out states was never observed.
        """
        import numpy as np

        what = "MarkovWinExpectancy.fit"
        pl_df = to_polars_df(df)
        required = (
            "outs_before",
            "base_state_before",
            "outs_after",
            "base_state_after",
            "runs_on_play",
        )
        missing = set(required) - set(pl_df.columns)
        if missing:
            raise ValueError(f"Input dataframe for {what} is missing columns: {sorted(missing)}")
        nonnull = ("outs_before", "base_state_before", "outs_after", "runs_on_play")
        require_no_nulls(pl_df.select(*nonnull), nonnull, what)
        bases = [b for _, b in self.STATES[:8]]
        require_values(pl_df, "outs_before", (0, 1, 2), what)
        require_values(pl_df, "outs_after", (0, 1, 2, 3), what)
        require_values(pl_df, "base_state_before", bases, what)
        batting = pl_df.filter(pl.col("outs_after") < 3)
        require_no_nulls(batting, ("base_state_after",), what)
        require_values(batting, "base_state_after", bases, what)
        if pl_df.filter(pl.col("outs_after") < pl.col("outs_before")).height:
            raise ValueError(f"{what}: outs_after is below outs_before on some plays.")
        if pl_df.filter(pl.col("runs_on_play") < 0).height:
            raise ValueError(f"{what}: runs_on_play is negative on some plays.")

        idx = {s: i for i, s in enumerate(self.STATES)}
        counts: dict[tuple[int, int, int], float] = {}
        grouped = pl_df.group_by(
            ["outs_before", "base_state_before", "outs_after", "base_state_after", "runs_on_play"]
        ).agg(pl.len().alias("n"))
        for row in grouped.iter_rows(named=True):
            start = idx[(int(row["outs_before"]), str(row["base_state_before"]))]
            outs_after = int(row["outs_after"])
            end = 24 if outs_after >= 3 else idx[(outs_after, str(row["base_state_after"]))]
            runs = int(row["runs_on_play"])
            if end == start and runs == 0:
                continue  # a play that changes neither the state nor the score
            counts[(start, end, runs)] = counts.get((start, end, runs), 0.0) + float(row["n"])
        totals = np.zeros(24)
        for (start, _end, _runs), n in counts.items():
            totals[start] += n
        unseen = [f"{o}|{b}" for (o, b), t in zip(self.STATES, totals, strict=True) if t == 0]
        if unseen:
            raise ValueError(f"No plays observed from base-out states: {unseen}")
        max_runs = max(r for (_s, _e, r) in counts)
        trans = np.zeros((max_runs + 1, 24, 25))
        for (start, end, runs), n in counts.items():
            trans[runs, start, end] = n / totals[start]
        self._solve(trans)
        self._results = MarkovWinExpectancyResults(
            n_plays=int(pl_df.height), max_inning=self.max_inning, max_run_diff=self.max_run_diff
        )
        return self

    def _solve(self, trans: Any) -> None:
        """Backward induction over half-innings; trans[r][s, t] is the chance of s to t with r runs (t = 24 ends it)."""
        import numpy as np

        k = self.max_run_diff
        max_runs = trans.shape[0] - 1
        n_d = (
            2 * (k + max_runs) + 1
        )  # run differences -(k+R)..(k+R); the outer rows are fixed at 0 and 1
        d_values = np.arange(-(k + max_runs), k + max_runs + 1)
        inner = np.abs(d_values) < k
        value: dict[tuple[int, bool], Any] = {}
        top_start_next = np.full(n_d, 0.5)  # value at the start of the top of inning max_inning + 1
        for inning in range(self.max_inning, 0, -1):
            for is_top in (False, True):
                if is_top:
                    ended = value[(inning, False)][
                        :, 0
                    ]  # the bottom half begins with the same margin
                elif inning >= 9:
                    ended = np.where(d_values > 0, 1.0, np.where(d_values < 0, 0.0, top_start_next))
                else:
                    ended = top_start_next
                walk_off = (not is_top) and inning >= 9
                sign = -1 if is_top else 1
                grid = np.zeros((n_d, 25))
                grid[:, 24] = ended
                grid[d_values >= k, :] = 1.0
                grid[d_values <= -k, :] = 0.0
                for _ in range(2000):
                    new = np.zeros((n_d, 24))
                    for runs in range(max_runs + 1):
                        shifted_idx = np.clip(np.arange(n_d) + sign * runs, 0, n_d - 1)
                        shifted = grid[shifted_idx]
                        if walk_off:
                            shifted = np.where((d_values + runs > 0)[:, None], 1.0, shifted)
                        new += shifted @ trans[runs].T
                    change = float(np.max(np.abs(new[inner] - grid[inner, :24])))
                    grid[inner, :24] = new[inner]
                    if change < 1e-13:
                        break
                value[(inning, is_top)] = grid[:, :24].copy()
                if is_top:
                    top_start_next = grid[:, 0].copy()
        self._value = value

    def win_expectancy(
        self,
        inning: int,
        half_inning: str,
        outs: int,
        base_state: BaseState | str,
        home_score_diff: int,
    ) -> float:
        """Home team's win probability from a state (`home_score_diff` is home minus away runs)."""
        if not self._value:
            raise RuntimeError("MarkovWinExpectancy is not fitted yet. Call .fit(df) first.")
        if not 1 <= inning <= self.max_inning:
            raise ValueError(f"inning must be between 1 and {self.max_inning}.")
        key = (outs, str(base_state))
        if key not in self.STATES:
            raise ValueError(f"Unknown base-out state: {key}.")
        if home_score_diff >= self.max_run_diff:
            return 1.0
        if home_score_diff <= -self.max_run_diff:
            return 0.0
        is_top = half_inning.lower().strip() in ("top", "t", "0", "away")
        grid = self._value[(inning, is_top)]
        row = home_score_diff + (grid.shape[0] // 2)
        return float(grid[row, self.STATES.index(key)])


def _occupied_base_sum(state: str) -> pl.Expr:
    """Sum of the base numbers occupied in a base-state string such as '1-3' (4 for a runner on first and third)."""
    return sum(
        (pl.col(state).str.contains(str(base)).cast(pl.Int64) * base for base in (1, 2, 3)),
        start=pl.lit(0, dtype=pl.Int64),
    )


@profiled(category="expectancy")
def add_base_advance_columns(df: IntoFrame) -> Any:
    """Add per-plate-appearance `bases_advanced` and `base_advance_opps` (Hardegree 2005, Base-Advance Average).

    Needs `base_state_before`, `base_state_after` (runners left on base when the inning ends must stay in the
    after-state) and `runs_on_play` (batter and runners reaching home). With Pb and Pa the sums of occupied base
    numbers before and after, R the runs and n the runners on base before:
    bases advanced = 4R + Pa - Pb and opportunities = 4 + 4n - Pb. Steals and other non-plate-appearance events
    are not counted.
    """
    pl_df = to_polars_df(df)
    runners_before = sum(
        (pl.col("base_state_before").str.contains(str(b)).cast(pl.Int64) for b in (1, 2, 3)),
        start=pl.lit(0, dtype=pl.Int64),
    )
    out = pl_df.with_columns(
        (
            4 * pl.col("runs_on_play").cast(pl.Int64)
            + _occupied_base_sum("base_state_after")
            - _occupied_base_sum("base_state_before")
        ).alias("bases_advanced"),
        (4 + 4 * runners_before - _occupied_base_sum("base_state_before")).alias(
            "base_advance_opps"
        ),
    )
    if isinstance(df, pl.DataFrame):
        return out
    arrow_tbl = out.to_arrow()
    if type(df).__module__.startswith("pandas"):
        return arrow_tbl.to_pandas()
    return arrow_tbl
