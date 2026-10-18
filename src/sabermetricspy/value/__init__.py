"""Modular Wins Above Replacement (WAR) calculation framework for position players and pitchers."""

from __future__ import annotations

from typing import Any

import narwhals as nw
from narwhals.typing import IntoFrame
from pydantic import BaseModel, ConfigDict

from sabermetricspy.constants import get_pitcher_war_constants, resolve_context
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

    Follows the structure of the FanGraphs position-player equation:
        WAR = (BattingRuns + BaserunningRuns + FieldingRuns + PositionalRuns + LeagueRuns + ReplacementRuns) / RPW

    It is an approximation, not the FanGraphs or Baseball-Reference calculation (docs/METHODOLOGY.md):
    replacement level is a flat `replacement_runs_per_600_pa` (FanGraphs derives it from
    `570 * (G / 2430) * (RPW / lgPA) * PA`), and the positional adjustment is scaled by PA / 600 rather than
    defensive innings. Pitcher WAR (`calculate_pitcher_war_df`) is further from the published methods.
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
        league_correction_per_ip: float | None = None,
    ) -> Any:
        """Compute pitcher WAR with the method documented on the FanGraphs Library ("WAR for Pitchers").

        Steps (validated against FanGraphs' published Stroman 2016 worked example):

        1. ifFIP = (13 HR + 3 (BB + HBP) - 2 (K + IFFB)) / IP + the MLB ifFIP constant.
        2. FIPR9 = ifFIP + (lgRA9 - lgERA); pFIPR9 = FIPR9 / (FIP park factor / 100).
        3. RAAP9 = league FIPR9 (AL, NL, or MLB) - pFIPR9, where league FIPR9 uses that league's totals
           with the MLB constant.
        4. dRPW = (((18 - IP/G) * lgFIPR9 + (IP/G) * pFIPR9) / 18 + 2) * 1.5.
        5. WAR = (RAAP9 / dRPW + replacement) * IP / 9, with replacement = 0.03 (1 - GS/G) + 0.12 GS/G.
        6. Pure relievers (GS = 0) are multiplied by (1 + gmLI) / 2.
        7. League correction: `league_correction_per_ip` wins per inning, defaulting to the value FanGraphs
           publishes (2016 only) and to zero elsewhere, so other seasons are uncorrected (typically about
           -0.0007 to -0.0012 wins per inning, i.e. about -0.15 WAR over 200 IP).

        Required columns: `outs` (or `ip`), `g`, `gs`, `hr`, `bb`, `hbp`, `so`. Optional: `iffb` or `pu` (infield flies; zero when
        absent), `gmli` (1.0 when absent), `league` ("AL"/"NL"; defaults to the context league, with MLB-wide
        totals otherwise) and `fip_park_factor` (the FIP column of the FanGraphs Guts! park factors; defaults
        to the context park factor, where 100 means no adjustment).

        FanGraphs values starters and relievers separately for pitchers who do both; give each role its own
        row to reproduce that. A single mixed row uses the blended replacement level from the same page and
        is less accurate. Live FanGraphs leaderboard values for 2016 differ from this documented method by up
        to about 0.2 WAR for reasons FanGraphs does not publish (see docs/METHODOLOGY.md).

        Adds `pitcher_if_fip`, `pitcher_fipr9`, `pitcher_pfipr9`, `pitcher_raap9`, `pitcher_drpw`,
        `pitcher_rar` (runs above replacement including the reliever leverage multiplier, before the league correction) and `pitcher_war`.
        """
        consts = get_pitcher_war_constants(self.context.season)
        nw_df = normalize_columns(nw.from_native(df))
        cols = set(nw_df.columns)
        required = ("outs", "g", "gs", "hr", "bb", "hbp", "so")
        missing = [c for c in required if c not in cols]
        if missing:
            raise ValueError(f"Pitcher WAR requires columns {list(required)}; missing {missing}.")

        correction = league_correction_per_ip
        if correction is None:
            correction = consts.war_ip_correction or 0.0

        ip = nw.col("outs").cast(nw.Float64) / 3.0
        # `iffb` (infield flies) is normalized to the canonical `pu` column by the alias registry.
        iffb = nw.col("pu").fill_null(0).cast(nw.Float64) if "pu" in cols else nw.lit(0.0)
        gmli = nw.col("gmli").cast(nw.Float64) if "gmli" in cols else nw.lit(1.0)
        pf = (
            nw.col("fip_park_factor").cast(nw.Float64) / 100.0
            if "fip_park_factor" in cols
            else nw.lit(self.context.park_factor / 100.0)
        )

        if_fip = (
            safe_div(
                13.0 * nw.col("hr")
                + 3.0 * (nw.col("bb") + nw.col("hbp"))
                - 2.0 * (nw.col("so") + iffb),
                ip,
            )
            + consts.iffip_constant
        )
        fipr9 = if_fip + consts.ra9_minus_era
        pfipr9 = safe_div(fipr9, pf)

        if "league" in cols:
            league = nw.col("league").str.to_uppercase()
            lg_fipr9 = (
                nw.when(league == "AL")
                .then(consts.league_fipr9("AL"))
                .when(league == "NL")
                .then(consts.league_fipr9("NL"))
                .otherwise(consts.league_fipr9("MLB"))
            )
        else:
            lg_fipr9 = nw.lit(consts.league_fipr9(self.context.league))

        raap9 = lg_fipr9 - pfipr9
        ip_per_g = safe_div(ip, nw.col("g"))
        drpw = (((18.0 - ip_per_g) * lg_fipr9 + ip_per_g * pfipr9) / 18.0 + 2.0) * 1.5
        start_share = safe_div(nw.col("gs"), nw.col("g"))
        replacement = 0.03 * (1.0 - start_share) + 0.12 * start_share
        wins_per_game = safe_div(raap9, drpw) + replacement
        multiplier = nw.when(nw.col("gs") == 0).then((1.0 + gmli) / 2.0).otherwise(1.0)

        out = nw_df.with_columns(
            if_fip.alias("pitcher_if_fip"),
            fipr9.alias("pitcher_fipr9"),
            pfipr9.alias("pitcher_pfipr9"),
            raap9.alias("pitcher_raap9"),
            drpw.alias("pitcher_drpw"),
            ((raap9 + replacement * drpw) * ip / 9.0 * multiplier).alias("pitcher_rar"),
            (wins_per_game * ip / 9.0 * multiplier + correction * ip).alias("pitcher_war"),
        )
        return nw.to_native(out)

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
