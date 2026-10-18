"""Modular Wins Above Replacement (WAR) calculation framework for position players and pitchers."""

from __future__ import annotations

from typing import Any

import narwhals as nw
from narwhals.typing import IntoFrame
from pydantic import BaseModel, ConfigDict

from sabermetricspy.constants import resolve_context
from sabermetricspy.schema import normalize_columns, safe_div
from sabermetricspy.telemetry import profiled
from sabermetricspy.types.context import SeasonContext

# Standard FanGraphs Positional Adjustments per 162 games (1,350 defensive innings / 600 PA)
POSITIONAL_ADJUSTMENTS_PER_162: dict[str, float] = {
    "C": 12.5,
    "SS": 7.5,
    "2B": 2.5,
    "CF": 2.5,
    "3B": 2.5,
    "RF": -7.5,
    "LF": -7.5,
    "1B": -12.5,
    "DH": -17.5,
    "P": 0.0,
}


class WARComponents(BaseModel):
    """Frozen component breakdown of a single player's WAR."""

    model_config = ConfigDict(frozen=True)

    batting_runs: float
    baserunning_runs: float
    fielding_runs: float
    positional_runs: float
    league_runs: float
    replacement_runs: float
    runs_above_replacement: float
    runs_per_win: float
    war: float


class WARFramework:
    """Transparent, configurable WAR calculator for position players and pitchers.

    Follows the canonical FanGraphs / MLB WAR equation:
        WAR = (BattingRuns + BaserunningRuns + FieldingRuns + PositionalRuns + LeagueRuns + ReplacementRuns) / RPW
    """

    def __init__(
        self,
        context: SeasonContext | None = None,
        *,
        season: int = 2024,
        replacement_runs_per_600_pa: float = 20.0,
    ) -> None:
        self.context = resolve_context(context, season=season)
        self.replacement_runs_per_600_pa = replacement_runs_per_600_pa

    @profiled(category="valuation")
    def calculate_position_player_scalar(
        self,
        *,
        pa: int,
        batting_runs: float,
        baserunning_runs: float = 0.0,
        fielding_runs: float = 0.0,
        position: str = "CF",
        league_runs: float = 0.0,
    ) -> WARComponents:
        """Compute position-player WAR and return a frozen WARComponents breakdown."""
        assert self.context.weights is not None
        rpw = self.context.weights.lg_r_per_w
        pos_adj_162 = POSITIONAL_ADJUSTMENTS_PER_162.get(position.upper(), 0.0)
        positional_runs = (pa / 600.0) * pos_adj_162
        replacement_runs = (pa / 600.0) * self.replacement_runs_per_600_pa
        rar = (
            batting_runs
            + baserunning_runs
            + fielding_runs
            + positional_runs
            + league_runs
            + replacement_runs
        )
        return WARComponents(
            batting_runs=batting_runs,
            baserunning_runs=baserunning_runs,
            fielding_runs=fielding_runs,
            positional_runs=positional_runs,
            league_runs=league_runs,
            replacement_runs=replacement_runs,
            runs_above_replacement=rar,
            runs_per_win=rpw,
            war=rar / rpw,
        )

    @profiled(category="valuation")
    def calculate_pitcher_war_df(
        self,
        df: IntoFrame,
        *,
        run_estimator_col: str = "fip",
        replacement_level_win_pct: float = 0.380,
    ) -> Any:
        """Compute Pitcher WAR over a DataFrame using either FIP (fWAR-style) or RA9 (rWAR-style).

        Adds `pitcher_rar` and `pitcher_war` columns to the native DataFrame.
        """
        assert self.context.weights is not None
        w = self.context.weights
        pf = self.context.park_factor / 100.0
        nw_df = normalize_columns(nw.from_native(df))

        ip_expr = nw.col("outs").cast(nw.Float64) / 3.0
        park_adj_est = safe_div(nw.col(run_estimator_col), pf)
        if w.lg_fip is None:
            raise ValueError(
                f"Pitcher WAR requires a sourced league FIP/RA9 for season {w.season}; none is bundled."
            )
        lg_ra9 = w.lg_fip
        rpw = w.lg_r_per_w

        # Runs above average per 9 IP = lg_ra9 - park_adj_est
        # Replacement level offset in runs per 9 IP = (0.500 - replacement_level_win_pct) * rpw
        rep_offset_per_9 = (0.500 - replacement_level_win_pct) * rpw
        runs_above_rep_per_9 = (lg_ra9 - park_adj_est) + rep_offset_per_9
        rar_expr = (runs_above_rep_per_9 * (ip_expr / 9.0)).alias("pitcher_rar")
        war_expr = (rar_expr / rpw).alias("pitcher_war")

        out_nw = nw_df.with_columns(rar_expr).with_columns(war_expr)
        return nw.to_native(out_nw)

    @profiled(category="valuation")
    def calculate_position_player_df(
        self,
        df: IntoFrame,
        *,
        batting_runs_col: str = "wraa",
        baserunning_runs_col: str = "bsr",
        fielding_runs_col: str = "fielding_runs",
        position_col: str = "position",
        league_runs_col: str = "league_runs",
    ) -> Any:
        """Compute Position-Player WAR vectorized over any Polars, DuckDB, PyArrow, or pandas DataFrame.

        Adds `positional_runs`, `replacement_runs`, `runs_above_replacement`, and `war` columns
        to the native DataFrame, matching `calculate_position_player_scalar` row-for-row.
        """
        assert self.context.weights is not None
        rpw = self.context.weights.lg_r_per_w
        nw_df = normalize_columns(nw.from_native(df))
        cols = set(nw_df.columns)

        if "pa" not in cols:
            raise ValueError("Position-player WAR requires column 'pa'.")
        if batting_runs_col not in cols and "batting_runs" in cols:
            batting_runs_col = "batting_runs"
        if batting_runs_col not in cols:
            raise ValueError(
                f"Position-player WAR requires '{batting_runs_col}' or 'batting_runs' column."
            )

        pa_expr = nw.col("pa").cast(nw.Float64)
        bat_expr = nw.col(batting_runs_col).cast(nw.Float64)
        bsr_expr = (
            nw.col(baserunning_runs_col).cast(nw.Float64)
            if baserunning_runs_col in cols
            else (nw.col("wsb").cast(nw.Float64) if "wsb" in cols else nw.lit(0.0))
        )
        fld_expr = (
            nw.col(fielding_runs_col).cast(nw.Float64) if fielding_runs_col in cols else nw.lit(0.0)
        )
        lg_expr = (
            nw.col(league_runs_col).cast(nw.Float64) if league_runs_col in cols else nw.lit(0.0)
        )

        if position_col in cols:
            pos_upper = nw.col(position_col).str.to_uppercase()
            pos_adj_expr: nw.Expr = nw.lit(0.0)
            for pos_code, adj_val in POSITIONAL_ADJUSTMENTS_PER_162.items():
                pos_adj_expr = nw.when(pos_upper == pos_code).then(adj_val).otherwise(pos_adj_expr)
        else:
            pos_adj_expr = nw.lit(0.0)

        pos_runs_expr = ((pa_expr / 600.0) * pos_adj_expr).alias("positional_runs")
        rep_runs_expr = ((pa_expr / 600.0) * self.replacement_runs_per_600_pa).alias(
            "replacement_runs"
        )

        out_nw = nw_df.with_columns(pos_runs_expr, rep_runs_expr)
        rar_expr = (
            bat_expr
            + bsr_expr
            + fld_expr
            + nw.col("positional_runs")
            + lg_expr
            + nw.col("replacement_runs")
        ).alias("runs_above_replacement")
        out_nw = out_nw.with_columns(rar_expr)
        war_expr = (nw.col("runs_above_replacement") / rpw).alias("war")
        out_nw = out_nw.with_columns(war_expr)
        return nw.to_native(out_nw)
