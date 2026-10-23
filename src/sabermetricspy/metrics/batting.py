"""Traditional offensive counting derivations and rate statistics."""

from __future__ import annotations

import narwhals as nw

from sabermetricspy.registry import EvalContext, MetricSpec, register_metric
from sabermetricspy.schema import safe_div
from sabermetricspy.types.enums import Category, Direction, ImplKind, Metric


@register_metric(
    MetricSpec(
        metric=Metric.B1,
        display_name="1B",
        category=Category.BATTING,
        kind=ImplKind.DETERMINISTIC,
        required_columns=("h", "b2", "b3", "hr"),
        direction=Direction.HIGHER_IS_BETTER,
        formula_latex=r"1B = H - 2B - 3B - HR",
        citation="Chadwick, H. (1867); Official MLB Baseball Rules",
        description="Singles derived from total hits minus extra-base hits.",
    )
)
def calc_b1(ctx: EvalContext) -> nw.Expr:
    return nw.col("h") - nw.col("b2") - nw.col("b3") - nw.col("hr")


@register_metric(
    MetricSpec(
        metric=Metric.XBH,
        display_name="XBH",
        category=Category.BATTING,
        kind=ImplKind.DETERMINISTIC,
        required_columns=("b2", "b3", "hr"),
        direction=Direction.HIGHER_IS_BETTER,
        formula_latex=r"XBH = 2B + 3B + HR",
        citation="Official MLB Baseball Rules",
        description="Total extra-base hits.",
    )
)
def calc_xbh(ctx: EvalContext) -> nw.Expr:
    return nw.col("b2") + nw.col("b3") + nw.col("hr")


@register_metric(
    MetricSpec(
        metric=Metric.TB,
        display_name="TB",
        category=Category.BATTING,
        kind=ImplKind.DETERMINISTIC,
        required_columns=("h", "b2", "b3", "hr"),
        requires=(Metric.B1,),
        direction=Direction.HIGHER_IS_BETTER,
        formula_latex=r"TB = 1B + 2(2B) + 3(3B) + 4(HR)",
        citation="Chadwick, H.; Thorn, J. & Palmer, P. (1984) The Hidden Game of Baseball",
        description="Total bases gained on hits.",
    )
)
def calc_tb(ctx: EvalContext) -> nw.Expr:
    return nw.col("b1") + 2 * nw.col("b2") + 3 * nw.col("b3") + 4 * nw.col("hr")


@register_metric(
    MetricSpec(
        metric=Metric.UBB,
        display_name="uBB",
        category=Category.BATTING,
        kind=ImplKind.DETERMINISTIC,
        required_columns=("bb",),
        optional_columns=("ibb",),
        direction=Direction.HIGHER_IS_BETTER,
        formula_latex=r"uBB = BB - IBB",
        citation="Tango, T., Lichtman, M., & Dolphin, A. (2007) The Book",
        description="Unintentional walks.",
    )
)
def calc_ubb(ctx: EvalContext) -> nw.Expr:
    if "ibb" in ctx.available_columns:
        return nw.col("bb") - nw.col("ibb")
    return nw.col("bb")


@register_metric(
    MetricSpec(
        metric=Metric.AVG,
        display_name="AVG",
        category=Category.BATTING,
        kind=ImplKind.DETERMINISTIC,
        required_columns=("h", "ab"),
        direction=Direction.HIGHER_IS_BETTER,
        formula_latex=r"AVG = \frac{H}{AB}",
        citation="Chadwick, H. (1872)",
        description="Batting average (hits per at-bat).",
    )
)
def calc_avg(ctx: EvalContext) -> nw.Expr:
    return safe_div(nw.col("h"), nw.col("ab"))


@register_metric(
    MetricSpec(
        metric=Metric.OBP,
        display_name="OBP",
        category=Category.BATTING,
        kind=ImplKind.DETERMINISTIC,
        required_columns=("h", "bb", "ab"),
        optional_columns=("hbp", "sf"),
        direction=Direction.HIGHER_IS_BETTER,
        formula_latex=r"OBP = \frac{H + BB + HBP}{AB + BB + HBP + SF}",
        citation="Roth, A. & Rickey, B. (1954)",
        description="On-base percentage.",
    )
)
def calc_obp(ctx: EvalContext) -> nw.Expr:
    hbp = nw.col("hbp") if "hbp" in ctx.available_columns else nw.lit(0)
    sf = nw.col("sf") if "sf" in ctx.available_columns else nw.lit(0)
    num = nw.col("h") + nw.col("bb") + hbp
    den = nw.col("ab") + nw.col("bb") + hbp + sf
    return safe_div(num, den)


@register_metric(
    MetricSpec(
        metric=Metric.SLG,
        display_name="SLG",
        category=Category.BATTING,
        kind=ImplKind.DETERMINISTIC,
        required_columns=("h", "b2", "b3", "hr", "ab"),
        requires=(Metric.TB,),
        direction=Direction.HIGHER_IS_BETTER,
        formula_latex=r"SLG = \frac{TB}{AB}",
        citation="Lane, F. C. (1925) Batting",
        description="Slugging percentage (total bases per at-bat).",
    )
)
def calc_slg(ctx: EvalContext) -> nw.Expr:
    return safe_div(nw.col("tb"), nw.col("ab"))


@register_metric(
    MetricSpec(
        metric=Metric.OPS,
        display_name="OPS",
        category=Category.BATTING,
        kind=ImplKind.DETERMINISTIC,
        required_columns=("h", "b2", "b3", "hr", "bb", "ab"),
        optional_columns=("hbp", "sf"),
        requires=(Metric.OBP, Metric.SLG),
        direction=Direction.HIGHER_IS_BETTER,
        formula_latex=r"OPS = OBP + SLG",
        citation="Thorn, J. & Palmer, P. (1984) The Hidden Game of Baseball",
        description="On-base plus slugging percentage.",
    )
)
def calc_ops(ctx: EvalContext) -> nw.Expr:
    return nw.col("obp") + nw.col("slg")


@register_metric(
    MetricSpec(
        metric=Metric.ISO,
        display_name="ISO",
        category=Category.BATTING,
        kind=ImplKind.DETERMINISTIC,
        required_columns=("h", "b2", "b3", "hr", "ab"),
        requires=(Metric.SLG, Metric.AVG),
        direction=Direction.HIGHER_IS_BETTER,
        formula_latex=r"ISO = SLG - AVG = \frac{2B + 2(3B) + 3(HR)}{AB}",
        citation="Roth, A. & Rickey, B. (1954); James, B. (1977)",
        description="Isolated power (extra bases per at-bat).",
    )
)
def calc_iso(ctx: EvalContext) -> nw.Expr:
    return nw.col("slg") - nw.col("avg")


@register_metric(
    MetricSpec(
        metric=Metric.ISOD,
        display_name="IsoD",
        category=Category.BATTING,
        kind=ImplKind.DETERMINISTIC,
        required_columns=("h", "ab", "bb"),
        optional_columns=("hbp", "sf"),
        requires=(Metric.AVG, Metric.OBP),
        direction=Direction.HIGHER_IS_BETTER,
        formula_latex=r"IsoD = OBP - AVG",
        citation="James, B.; Tango, T. (2006)",
        description="Isolated discipline (non-hit on-base rate).",
    )
)
def calc_isod(ctx: EvalContext) -> nw.Expr:
    return nw.col("obp") - nw.col("avg")


@register_metric(
    MetricSpec(
        metric=Metric.BABIP,
        display_name="BABIP",
        category=Category.BATTING,
        kind=ImplKind.DETERMINISTIC,
        required_columns=("h", "hr", "ab", "so"),
        optional_columns=("sf",),
        direction=Direction.HIGHER_IS_BETTER,
        formula_latex=r"BABIP = \frac{H - HR}{AB - SO - HR + SF}",
        citation="McCracken, V. (2001) Pitching and Defense: How Much Control Do Hurlers Have?",
        description="Batting average on balls in play.",
    )
)
def calc_babip(ctx: EvalContext) -> nw.Expr:
    sf = nw.col("sf") if "sf" in ctx.available_columns else nw.lit(0)
    num = nw.col("h") - nw.col("hr")
    den = nw.col("ab") - nw.col("so") - nw.col("hr") + sf
    return safe_div(num, den)


@register_metric(
    MetricSpec(
        metric=Metric.SECA,
        display_name="SecA",
        category=Category.BATTING,
        kind=ImplKind.DETERMINISTIC,
        required_columns=("h", "b2", "b3", "hr", "bb", "ab"),
        optional_columns=("sb", "cs"),
        requires=(Metric.TB,),
        direction=Direction.HIGHER_IS_BETTER,
        formula_latex=r"SecA = \frac{BB + (TB - H) + (SB - CS)}{AB}",
        citation="James, B. (1982) Baseball Abstract",
        description="Bill James's Secondary Average.",
    )
)
def calc_seca(ctx: EvalContext) -> nw.Expr:
    sb = nw.col("sb") if "sb" in ctx.available_columns else nw.lit(0)
    cs = nw.col("cs") if "cs" in ctx.available_columns else nw.lit(0)
    num = nw.col("bb") + (nw.col("tb") - nw.col("h")) + (sb - cs)
    return safe_div(num, nw.col("ab"))


@register_metric(
    MetricSpec(
        metric=Metric.HR_PCT,
        display_name="HR%",
        category=Category.BATTING,
        kind=ImplKind.DETERMINISTIC,
        required_columns=("hr", "pa"),
        direction=Direction.HIGHER_IS_BETTER,
        formula_latex=r"HR\% = \frac{HR}{PA}",
        citation="FanGraphs Library",
        description="Home run rate per plate appearance.",
    )
)
def calc_hr_pct(ctx: EvalContext) -> nw.Expr:
    return safe_div(nw.col("hr"), nw.col("pa"))


@register_metric(
    MetricSpec(
        metric=Metric.BB_PCT,
        display_name="BB%",
        category=Category.BATTING,
        kind=ImplKind.DETERMINISTIC,
        required_columns=("bb", "pa"),
        direction=Direction.HIGHER_IS_BETTER,
        formula_latex=r"BB\% = \frac{BB}{PA}",
        citation="FanGraphs Library",
        description="Walk rate per plate appearance.",
    )
)
def calc_bb_pct(ctx: EvalContext) -> nw.Expr:
    return safe_div(nw.col("bb"), nw.col("pa"))


@register_metric(
    MetricSpec(
        metric=Metric.K_PCT,
        display_name="K%",
        category=Category.BATTING,
        kind=ImplKind.DETERMINISTIC,
        required_columns=("so", "pa"),
        direction=Direction.LOWER_IS_BETTER,
        formula_latex=r"K\% = \frac{SO}{PA}",
        citation="FanGraphs Library",
        description="Strikeout rate per plate appearance.",
    )
)
def calc_k_pct(ctx: EvalContext) -> nw.Expr:
    return safe_div(nw.col("so"), nw.col("pa"))


@register_metric(
    MetricSpec(
        metric=Metric.K_MINUS_BB_PCT,
        display_name="K-BB%",
        category=Category.BATTING,
        kind=ImplKind.DETERMINISTIC,
        required_columns=("so", "bb", "pa"),
        requires=(Metric.K_PCT, Metric.BB_PCT),
        direction=Direction.LOWER_IS_BETTER,
        formula_latex=r"K\!-\!BB\% = K\% - BB\%",
        citation="FanGraphs Library",
        description="Strikeout rate minus walk rate.",
    )
)
def calc_k_minus_bb_pct(ctx: EvalContext) -> nw.Expr:
    return nw.col("k_pct") - nw.col("bb_pct")


@register_metric(
    MetricSpec(
        metric=Metric.BB_TO_K,
        display_name="BB/K",
        category=Category.BATTING,
        kind=ImplKind.DETERMINISTIC,
        required_columns=("bb", "so"),
        direction=Direction.HIGHER_IS_BETTER,
        formula_latex=r"BB/K = \frac{BB}{SO}",
        citation="FanGraphs Library",
        description="Walk-to-strikeout ratio.",
    )
)
def calc_bb_to_k(ctx: EvalContext) -> nw.Expr:
    return safe_div(nw.col("bb"), nw.col("so"))


@register_metric(
    MetricSpec(
        metric=Metric.K_TO_BB,
        display_name="K/BB",
        category=Category.BATTING,
        kind=ImplKind.DETERMINISTIC,
        required_columns=("so", "bb"),
        direction=Direction.HIGHER_IS_BETTER,
        formula_latex=r"K/BB = \frac{SO}{BB}",
        citation="FanGraphs Library",
        description="Strikeout-to-walk ratio.",
    )
)
def calc_k_to_bb(ctx: EvalContext) -> nw.Expr:
    return safe_div(nw.col("so"), nw.col("bb"))


@register_metric(
    MetricSpec(
        metric=Metric.R_PER_PA,
        display_name="R/PA",
        category=Category.BATTING,
        kind=ImplKind.DETERMINISTIC,
        required_columns=("r", "pa"),
        direction=Direction.HIGHER_IS_BETTER,
        formula_latex=r"R/PA = \frac{R}{PA}",
        citation="Official MLB Rules",
        description="Runs scored per plate appearance.",
    )
)
def calc_r_per_pa(ctx: EvalContext) -> nw.Expr:
    return safe_div(nw.col("r"), nw.col("pa"))


@register_metric(
    MetricSpec(
        metric=Metric.RBI_PER_PA,
        display_name="RBI/PA",
        category=Category.BATTING,
        kind=ImplKind.DETERMINISTIC,
        required_columns=("rbi", "pa"),
        direction=Direction.HIGHER_IS_BETTER,
        formula_latex=r"RBI/PA = \frac{RBI}{PA}",
        citation="Official MLB Rules",
        description="Runs batted in per plate appearance.",
    )
)
def calc_rbi_per_pa(ctx: EvalContext) -> nw.Expr:
    return safe_div(nw.col("rbi"), nw.col("pa"))


@register_metric(
    MetricSpec(
        metric=Metric.BAT_K_PCT_PLUS,
        display_name="K%+ (Bat)",
        category=Category.BATTING,
        kind=ImplKind.CONTEXTUAL,
        required_columns=("so", "pa"),
        requires=(Metric.K_PCT,),
        direction=Direction.LOWER_IS_BETTER,
        formula_latex=r"K\%^+ = 100 \times \frac{K\%}{lgK\%}",
        citation="FanGraphs Library (Plus Stats)",
        description="League-indexed batter strikeout rate (100 = league average, lower is better for batters).",
    )
)
def calc_bat_k_pct_plus(ctx: EvalContext) -> nw.Expr:
    return safe_div(100.0 * nw.col("k_pct"), ctx.weights.k_pct_for(ctx.season_context.league))


@register_metric(
    MetricSpec(
        metric=Metric.BAT_BB_PCT_PLUS,
        display_name="BB%+ (Bat)",
        category=Category.BATTING,
        kind=ImplKind.CONTEXTUAL,
        required_columns=("bb", "pa"),
        requires=(Metric.BB_PCT,),
        direction=Direction.HIGHER_IS_BETTER,
        formula_latex=r"BB\%^+ = 100 \times \frac{BB\%}{lgBB\%}",
        citation="FanGraphs Library (Plus Stats)",
        description="League-indexed batter walk rate (100 = league average, higher is better for batters).",
    )
)
def calc_bat_bb_pct_plus(ctx: EvalContext) -> nw.Expr:
    return safe_div(100.0 * nw.col("bb_pct"), ctx.weights.bb_pct_for(ctx.season_context.league))
