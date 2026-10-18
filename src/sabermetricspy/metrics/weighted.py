"""Weighted linear-weights offensive metrics (wOBA, wRAA, wRC, wRC+, OPS+) and Run Estimators (Runs Created, BaseRuns)."""

from __future__ import annotations

import narwhals as nw

from sabermetricspy.registry import EvalContext, MetricSpec, register_metric
from sabermetricspy.schema import safe_div
from sabermetricspy.types.enums import Category, Direction, ImplKind, Metric


@register_metric(
    MetricSpec(
        metric=Metric.WOBA,
        display_name="wOBA",
        category=Category.WEIGHTED_OFFENSE,
        kind=ImplKind.CONTEXTUAL,
        required_columns=("h", "b2", "b3", "hr", "bb", "ab"),
        optional_columns=("ibb", "hbp", "sf"),
        requires=(Metric.B1, Metric.UBB),
        direction=Direction.HIGHER_IS_BETTER,
        formula_latex=r"wOBA = \frac{w_{BB}uBB + w_{HBP}HBP + w_{1B}1B + w_{2B}2B + w_{3B}3B + w_{HR}HR}{AB + uBB + SF + HBP}",
        citation="Tango, T., Lichtman, M., & Dolphin, A. (2007) The Book: Playing the Percentages in Baseball",
        description="Weighted On-Base Average scaled to league OBP using seasonal linear weights.",
    )
)
def calc_woba(ctx: EvalContext) -> nw.Expr:
    w = ctx.weights
    hbp = nw.col("hbp") if "hbp" in ctx.available_columns else nw.lit(0)
    sf = nw.col("sf") if "sf" in ctx.available_columns else nw.lit(0)
    num = (
        w.w_bb * nw.col("ubb")
        + w.w_hbp * hbp
        + w.w_1b * nw.col("b1")
        + w.w_2b * nw.col("b2")
        + w.w_3b * nw.col("b3")
        + w.w_hr * nw.col("hr")
    )
    den = nw.col("ab") + nw.col("ubb") + sf + hbp
    return safe_div(num, den)


@register_metric(
    MetricSpec(
        metric=Metric.WRAA,
        display_name="wRAA",
        category=Category.WEIGHTED_OFFENSE,
        kind=ImplKind.CONTEXTUAL,
        required_columns=("h", "b2", "b3", "hr", "bb", "ab", "pa"),
        optional_columns=("ibb", "hbp", "sf"),
        requires=(Metric.WOBA,),
        direction=Direction.HIGHER_IS_BETTER,
        formula_latex=r"wRAA = \left(\frac{wOBA - lgwOBA}{wOBAScale}\right) \times PA",
        citation="Tango, T. (2007); FanGraphs Library (wRAA)",
        description="Weighted Runs Above Average.",
    )
)
def calc_wraa(ctx: EvalContext) -> nw.Expr:
    w = ctx.weights
    return ((nw.col("woba") - w.lg_woba) / w.woba_scale) * nw.col("pa")


@register_metric(
    MetricSpec(
        metric=Metric.WRC,
        display_name="wRC",
        category=Category.WEIGHTED_OFFENSE,
        kind=ImplKind.CONTEXTUAL,
        required_columns=("h", "b2", "b3", "hr", "bb", "ab", "pa"),
        optional_columns=("ibb", "hbp", "sf"),
        requires=(Metric.WRAA,),
        direction=Direction.HIGHER_IS_BETTER,
        formula_latex=r"wRC = wRAA + \left(\frac{lgR}{lgPA}\right) \times PA",
        citation="Tango, T. (2007); FanGraphs Library (wRC)",
        description="Weighted Runs Created.",
    )
)
def calc_wrc(ctx: EvalContext) -> nw.Expr:
    w = ctx.weights
    return nw.col("wraa") + (w.lg_r_per_pa * nw.col("pa"))


@register_metric(
    MetricSpec(
        metric=Metric.WRC_PLUS,
        display_name="wRC+",
        category=Category.WEIGHTED_OFFENSE,
        kind=ImplKind.CONTEXTUAL,
        required_columns=("h", "b2", "b3", "hr", "bb", "ab", "pa"),
        optional_columns=("ibb", "hbp", "sf"),
        requires=(Metric.WRAA,),
        direction=Direction.HIGHER_IS_BETTER,
        formula_latex=r"wRC^+ = \left(\frac{(wRAA / PA + lgR/PA) + (lgR/PA - PF \times lgR/PA)}{lgwRC/PA_{\text{non-pitchers}}}\right) \times 100",
        citation="FanGraphs Library (wRC+)",
        description="Park- and league-adjusted Weighted Runs Created (100 = league average).",
        caveats=(
            "Divides by the AL/NL non-pitcher wRC/PA (SeasonContext.league) when the season has that constant; otherwise falls back to league R/PA.",
            "Park factor defaults to 100 (no park adjustment); pass SeasonContext(park_factor=...) with the published factor, e.g. the FanGraphs Guts! 5-year value.",
        ),
    )
)
def calc_wrc_plus(ctx: EvalContext) -> nw.Expr:
    w = ctx.weights
    pf = ctx.season_context.park_factor / 100.0
    r_per_pa = safe_div(nw.col("wraa"), nw.col("pa")) + w.lg_r_per_pa
    park_adj = w.lg_r_per_pa - (pf * w.lg_r_per_pa)
    denominator = w.wrc_per_pa_for(ctx.season_context.league)
    if denominator is None:
        denominator = w.lg_r_per_pa
    return ((r_per_pa + park_adj) / denominator) * 100.0


@register_metric(
    MetricSpec(
        metric=Metric.OPS_PLUS,
        display_name="OPS+",
        category=Category.WEIGHTED_OFFENSE,
        kind=ImplKind.CONTEXTUAL,
        required_columns=("h", "b2", "b3", "hr", "bb", "ab"),
        optional_columns=("hbp", "sf"),
        requires=(Metric.OBP, Metric.SLG),
        direction=Direction.HIGHER_IS_BETTER,
        formula_latex=r"OPS^+ = \frac{100}{PF} \left(\frac{OBP}{lgOBP} + \frac{SLG}{lgSLG} - 1\right)",
        citation="Thorn, J. & Palmer, P. (1984); Baseball-Reference Glossary",
        description="Park- and league-adjusted OPS (100 = league average).",
    )
)
def calc_ops_plus(ctx: EvalContext) -> nw.Expr:
    w = ctx.weights
    pf = ctx.season_context.park_factor / 100.0
    raw = (nw.col("obp") / w.lg_obp) + (nw.col("slg") / w.lg_slg) - 1.0
    return (100.0 / pf) * raw


@register_metric(
    MetricSpec(
        metric=Metric.RC_BASIC,
        display_name="RC",
        category=Category.WEIGHTED_OFFENSE,
        kind=ImplKind.DETERMINISTIC,
        required_columns=("h", "b2", "b3", "hr", "bb", "ab"),
        requires=(Metric.TB,),
        direction=Direction.HIGHER_IS_BETTER,
        formula_latex=r"RC = \frac{(H + BB) \times TB}{AB + BB}",
        citation="James, B. (1979) Baseball Abstract",
        description="Bill James's basic Runs Created formula.",
    )
)
def calc_rc_basic(ctx: EvalContext) -> nw.Expr:
    num = (nw.col("h") + nw.col("bb")) * nw.col("tb")
    den = nw.col("ab") + nw.col("bb")
    return safe_div(num, den)


@register_metric(
    MetricSpec(
        metric=Metric.RC_TECH,
        display_name="RC (Tech)",
        category=Category.WEIGHTED_OFFENSE,
        kind=ImplKind.DETERMINISTIC,
        required_columns=("h", "b2", "b3", "hr", "bb", "ab"),
        optional_columns=("ibb", "hbp", "sb", "cs", "gidp", "sh", "sf"),
        requires=(Metric.TB, Metric.UBB),
        direction=Direction.HIGHER_IS_BETTER,
        formula_latex=r"RC_{tech} = \frac{A \times B}{C}",
        citation="James, B. (1985) Baseball Abstract",
        description="Bill James's technical Runs Created including steals, caught stealing, HBP, and GIDP.",
    )
)
def calc_rc_tech(ctx: EvalContext) -> nw.Expr:
    hbp = nw.col("hbp") if "hbp" in ctx.available_columns else nw.lit(0)
    cs = nw.col("cs") if "cs" in ctx.available_columns else nw.lit(0)
    sb = nw.col("sb") if "sb" in ctx.available_columns else nw.lit(0)
    gidp = nw.col("gidp") if "gidp" in ctx.available_columns else nw.lit(0)
    sh = nw.col("sh") if "sh" in ctx.available_columns else nw.lit(0)
    sf = nw.col("sf") if "sf" in ctx.available_columns else nw.lit(0)

    a = nw.col("h") + nw.col("bb") + hbp - cs - gidp
    b = (
        nw.col("tb")
        + 0.26 * (nw.col("ubb") + hbp)
        + 0.52 * (sh + sf + sb)
    )
    c = nw.col("ab") + nw.col("bb") + hbp + sh + sf
    return safe_div(a * b, c)


@register_metric(
    MetricSpec(
        metric=Metric.BASE_RUNS,
        display_name="BsR (Est)",
        category=Category.WEIGHTED_OFFENSE,
        kind=ImplKind.DETERMINISTIC,
        required_columns=("h", "b2", "b3", "hr", "bb", "ab"),
        optional_columns=("ibb", "hbp", "sb", "cs", "gidp"),
        requires=(Metric.TB, Metric.UBB),
        direction=Direction.HIGHER_IS_BETTER,
        formula_latex=r"BaseRuns = \frac{A \times B}{B + C} + D",
        citation="myth, D. (1991) Base Runs: A New Run Estimator",
        description="David Smyth's BaseRuns non-linear run estimator separating baserunners, advancement, outs, and home runs.",
    )
)
def calc_base_runs(ctx: EvalContext) -> nw.Expr:
    hbp = nw.col("hbp") if "hbp" in ctx.available_columns else nw.lit(0)
    ibb = nw.col("ibb") if "ibb" in ctx.available_columns else nw.lit(0)
    sb = nw.col("sb") if "sb" in ctx.available_columns else nw.lit(0)
    cs = nw.col("cs") if "cs" in ctx.available_columns else nw.lit(0)
    gidp = nw.col("gidp") if "gidp" in ctx.available_columns else nw.lit(0)

    # Smyth's version 1 (basic events) uses multiplier 1.02; version 2 (adds HBP, IBB, SB, CS, GDP) uses 1.1.
    version_2 = any(c in ctx.available_columns for c in ("hbp", "ibb", "sb", "cs", "gidp"))
    multiplier = 1.1 if version_2 else 1.02
    a = nw.col("h") + nw.col("bb") + hbp - nw.col("hr") - 0.5 * ibb
    b = multiplier * (
        1.4 * nw.col("tb")
        - 0.6 * nw.col("h")
        - 3.0 * nw.col("hr")
        + 0.1 * (nw.col("bb") + hbp - ibb)
        + 0.9 * (sb - cs - gidp)
    )
    c = nw.col("ab") - nw.col("h") + cs + gidp
    d = nw.col("hr")
    return safe_div(a * b, b + c) + d


@register_metric(
    MetricSpec(
        metric=Metric.RC27,
        display_name="RC/27",
        category=Category.WEIGHTED_OFFENSE,
        kind=ImplKind.DETERMINISTIC,
        required_columns=("h", "b2", "b3", "hr", "bb", "ab"),
        optional_columns=("ibb", "hbp", "sb", "cs", "gidp", "sh", "sf"),
        requires=(Metric.RC_TECH,),
        direction=Direction.HIGHER_IS_BETTER,
        formula_latex=r"RC/27 = 27 \times \frac{RC_{tech}}{AB - H + SH + SF + CS + GIDP}",
        citation="James, B. (1985) Baseball Abstract",
        description="Runs Created per 27 offensive outs.",
    )
)
def calc_rc27(ctx: EvalContext) -> nw.Expr:
    cs = nw.col("cs") if "cs" in ctx.available_columns else nw.lit(0)
    gidp = nw.col("gidp") if "gidp" in ctx.available_columns else nw.lit(0)
    sh = nw.col("sh") if "sh" in ctx.available_columns else nw.lit(0)
    sf = nw.col("sf") if "sf" in ctx.available_columns else nw.lit(0)
    outs_made = nw.col("ab") - nw.col("h") + sh + sf + cs + gidp
    return safe_div(27.0 * nw.col("rc_tech"), outs_made)


@register_metric(
    MetricSpec(
        metric=Metric.GPA,
        display_name="GPA",
        category=Category.WEIGHTED_OFFENSE,
        kind=ImplKind.DETERMINISTIC,
        required_columns=("h", "b2", "b3", "hr", "bb", "ab"),
        optional_columns=("hbp", "sf"),
        requires=(Metric.OBP, Metric.SLG),
        direction=Direction.HIGHER_IS_BETTER,
        formula_latex=r"GPA = \frac{1.8 \times OBP + SLG}{4}",
        citation="Gleeman, A. (2003) The Hardball Times (Gross Production Average)",
        description="Gross Production Average weighting OBP 1.8x relative to SLG and scaling to batting average.",
    )
)
def calc_gpa(ctx: EvalContext) -> nw.Expr:
    return (1.8 * nw.col("obp") + nw.col("slg")) / 4.0


@register_metric(
    MetricSpec(
        metric=Metric.TA,
        display_name="TA",
        category=Category.WEIGHTED_OFFENSE,
        kind=ImplKind.DETERMINISTIC,
        required_columns=("h", "b2", "b3", "hr", "bb", "ab"),
        optional_columns=("hbp", "sb", "cs", "gidp"),
        requires=(Metric.TB,),
        direction=Direction.HIGHER_IS_BETTER,
        formula_latex=r"TA = \frac{TB + BB + HBP + SB - CS}{AB - H + CS + GIDP}",
        citation="Boswell, T. (1978) Inside Sports / The Washington Post (Total Average)",
        description="Total Average measuring total bases gained per offensive out made.",
    )
)
def calc_ta(ctx: EvalContext) -> nw.Expr:
    hbp = nw.col("hbp") if "hbp" in ctx.available_columns else nw.lit(0)
    sb = nw.col("sb") if "sb" in ctx.available_columns else nw.lit(0)
    cs = nw.col("cs") if "cs" in ctx.available_columns else nw.lit(0)
    gidp = nw.col("gidp") if "gidp" in ctx.available_columns else nw.lit(0)
    num = nw.col("tb") + nw.col("bb") + hbp + sb - cs
    den = nw.col("ab") - nw.col("h") + cs + gidp
    return safe_div(num, den)

