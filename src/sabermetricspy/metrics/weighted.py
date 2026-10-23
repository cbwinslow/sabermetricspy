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
        metric=Metric.OFF,
        display_name="Off",
        category=Category.WEIGHTED_OFFENSE,
        kind=ImplKind.CONTEXTUAL,
        required_columns=("pa",),
        requires=(Metric.WRAA, Metric.BSR),
        direction=Direction.HIGHER_IS_BETTER,
        formula_latex=r"Off = wRAA + (lgR/PA - PF \times lgR/PA) PA + (lgR/PA - lgwRC/PA_{\text{non-pitchers}}) PA + BsR",
        citation="FanGraphs Library (Off)",
        description="Batting runs above average (park and league adjusted) plus base running runs.",
        caveats=(
            "Park factor defaults to 100 (no park adjustment); pass SeasonContext(park_factor=...).",
            "Uses the AL/NL non-pitcher wRC/PA when the season has it, otherwise league R/PA, as wRC+ does.",
        ),
    )
)
def calc_off(ctx: EvalContext) -> nw.Expr:
    w = ctx.weights
    pf = ctx.season_context.park_factor / 100.0
    league_wrc_per_pa = w.wrc_per_pa_for(ctx.season_context.league)
    if league_wrc_per_pa is None:
        league_wrc_per_pa = w.lg_r_per_pa
    park_term = (w.lg_r_per_pa - pf * w.lg_r_per_pa) * nw.col("pa")
    league_term = (w.lg_r_per_pa - league_wrc_per_pa) * nw.col("pa")
    return nw.col("wraa") + park_term + league_term + nw.col("bsr")


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
    raw = (nw.col("obp") / w.require("lg_obp")) + (nw.col("slg") / w.require("lg_slg")) - 1.0
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
    b = nw.col("tb") + 0.26 * (nw.col("ubb") + hbp) + 0.52 * (sh + sf + sb)
    c = nw.col("ab") + nw.col("bb") + hbp + sh + sf
    return safe_div(a * b, c)


# Furtado's published Extrapolated Runs weights (The 1999 Big Bad Baseball Annual; Baseball Think Factory "Introducing XR").
# Fixed constants of the method, not seasonal values. Fitted to 1955-1997 seasons.
XR_WEIGHTS: dict[str, float] = {
    "b1": 0.50,
    "b2": 0.72,
    "b3": 1.04,
    "hr": 1.44,
    "unintentional_walk_hbp": 0.34,
    "ibb": 0.25,
    "sb": 0.18,
    "cs": -0.32,
    "non_strikeout_out": -0.090,
    "so": -0.098,
    "gidp": -0.37,
    "sf": 0.37,
    "sh": 0.04,
}
XRR_WEIGHTS: dict[str, float] = {
    "b1": 0.50,
    "b2": 0.72,
    "b3": 1.04,
    "hr": 1.44,
    "walk_hbp": 0.33,
    "sb": 0.18,
    "cs": -0.32,
    "out": -0.098,
}


def _count_or_zero(ctx: EvalContext, name: str) -> nw.Expr:
    return nw.col(name) if name in ctx.available_columns else nw.lit(0)


@register_metric(
    MetricSpec(
        metric=Metric.XR,
        display_name="XR",
        category=Category.WEIGHTED_OFFENSE,
        kind=ImplKind.DETERMINISTIC,
        required_columns=("h", "b2", "b3", "hr", "bb", "ab", "so"),
        optional_columns=("ibb", "hbp", "sb", "cs", "gidp", "sf", "sh"),
        requires=(Metric.B1,),
        direction=Direction.HIGHER_IS_BETTER,
        formula_latex=(
            r"XR = .50\,1B + .72\,2B + 1.04\,3B + 1.44\,HR + .34\,(HBP + BB - IBB) + .25\,IBB"
            r" + .18\,SB - .32\,CS - .090\,(AB - H - SO) - .098\,SO - .37\,GIDP + .37\,SF + .04\,SH"
        ),
        citation="Furtado, J. (1999) Extrapolated Runs, The 1999 Big Bad Baseball Annual",
        description="Furtado's linear-weights run estimator fitted to 1955-1997 seasons.",
        caveats=(
            "bb is total walks including intentional walks; the formula subtracts ibb from the .34 group and credits it at .25.",
            "Absent optional columns count as 0 (as for rc_tech); so is required because strikeouts and other outs have different weights.",
            "The published weights were fitted to 1955-1997; earlier seasons are outside the documented scope.",
        ),
    )
)
def calc_xr(ctx: EvalContext) -> nw.Expr:
    w = XR_WEIGHTS
    hbp, ibb, sb, cs = (_count_or_zero(ctx, c) for c in ("hbp", "ibb", "sb", "cs"))
    gidp, sf, sh = (_count_or_zero(ctx, c) for c in ("gidp", "sf", "sh"))
    so = nw.col("so")
    return (
        w["b1"] * nw.col("b1")
        + w["b2"] * nw.col("b2")
        + w["b3"] * nw.col("b3")
        + w["hr"] * nw.col("hr")
        + w["unintentional_walk_hbp"] * (hbp + nw.col("bb") - ibb)
        + w["ibb"] * ibb
        + w["sb"] * sb
        + w["cs"] * cs
        + w["non_strikeout_out"] * (nw.col("ab") - nw.col("h") - so)
        + w["so"] * so
        + w["gidp"] * gidp
        + w["sf"] * sf
        + w["sh"] * sh
    )


@register_metric(
    MetricSpec(
        metric=Metric.XRR,
        display_name="XRR",
        category=Category.WEIGHTED_OFFENSE,
        kind=ImplKind.DETERMINISTIC,
        required_columns=("h", "b2", "b3", "hr", "bb", "ab"),
        optional_columns=("hbp", "sb", "cs"),
        requires=(Metric.B1,),
        direction=Direction.HIGHER_IS_BETTER,
        formula_latex=(
            r"XRR = .50\,1B + .72\,2B + 1.04\,3B + 1.44\,HR + .33\,(HBP + BB)"
            r" + .18\,SB - .32\,CS - .098\,(AB - H)"
        ),
        citation="Furtado, J. (1999) Extrapolated Runs Reduced, The 1999 Big Bad Baseball Annual",
        description="Furtado's reduced Extrapolated Runs, using only the commonly available counting stats.",
        caveats=(
            "The printed formula has an unbalanced parenthesis; it is read as -.098 x (AB - H), which reproduces the printed example.",
            "Absent optional columns count as 0.",
        ),
    )
)
def calc_xrr(ctx: EvalContext) -> nw.Expr:
    w = XRR_WEIGHTS
    hbp, sb, cs = (_count_or_zero(ctx, c) for c in ("hbp", "sb", "cs"))
    return (
        w["b1"] * nw.col("b1")
        + w["b2"] * nw.col("b2")
        + w["b3"] * nw.col("b3")
        + w["hr"] * nw.col("hr")
        + w["walk_hbp"] * (hbp + nw.col("bb"))
        + w["sb"] * sb
        + w["cs"] * cs
        + w["out"] * (nw.col("ab") - nw.col("h"))
    )


@register_metric(
    MetricSpec(
        metric=Metric.BASE_RUNS,
        display_name="BaseRuns",
        category=Category.WEIGHTED_OFFENSE,
        kind=ImplKind.DETERMINISTIC,
        required_columns=("h", "b2", "b3", "hr", "bb", "ab"),
        optional_columns=("ibb", "hbp", "sb", "cs", "gidp"),
        requires=(Metric.TB, Metric.UBB),
        direction=Direction.HIGHER_IS_BETTER,
        formula_latex=r"BaseRuns = \frac{A \times B}{B + C} + D",
        citation="Smyth, D. (1991) Base Runs: A New Run Estimator",
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
        formula_latex=r"TA = \frac{TB + BB + HBP + SB}{AB - H + CS + GIDP}",
        citation="Boswell, T. (1978) Inside Sports / The Washington Post (Total Average)",
        description="Total Average measuring total bases gained per offensive out made.",
    )
)
def calc_ta(ctx: EvalContext) -> nw.Expr:
    hbp = nw.col("hbp") if "hbp" in ctx.available_columns else nw.lit(0)
    sb = nw.col("sb") if "sb" in ctx.available_columns else nw.lit(0)
    cs = nw.col("cs") if "cs" in ctx.available_columns else nw.lit(0)
    gidp = nw.col("gidp") if "gidp" in ctx.available_columns else nw.lit(0)
    num = nw.col("tb") + nw.col("bb") + hbp + sb
    den = nw.col("ab") - nw.col("h") + cs + gidp
    return safe_div(num, den)


@register_metric(
    MetricSpec(
        metric=Metric.BRA,
        display_name="BRA",
        category=Category.WEIGHTED_OFFENSE,
        kind=ImplKind.DETERMINISTIC,
        required_columns=("h", "b2", "b3", "hr", "bb", "ab"),
        optional_columns=("hbp", "sf"),
        requires=(Metric.OBP, Metric.SLG),
        direction=Direction.HIGHER_IS_BETTER,
        formula_latex=r"BRA = OBP \times SLG",
        citation="Cramer, D. & Palmer, P. (1974) The Batter's Run Average, Baseball Research Journal",
        description="Batter's Run Average measuring multiplicative on-base and slugging interaction.",
    )
)
def calc_bra(ctx: EvalContext) -> nw.Expr:
    return nw.col("obp") * nw.col("slg")


@register_metric(
    MetricSpec(
        metric=Metric.ERP,
        display_name="ERP",
        category=Category.WEIGHTED_OFFENSE,
        kind=ImplKind.DETERMINISTIC,
        required_columns=("h", "b2", "b3", "hr", "bb", "ab"),
        optional_columns=("hbp", "sb", "cs", "gidp"),
        requires=(Metric.TB,),
        direction=Direction.HIGHER_IS_BETTER,
        formula_latex=r"ERP = (2(TB + BB + HBP) + H + SB - 0.605(AB + CS + GIDP - H)) \times 0.16",
        citation="Johnson, P. (1985) Bill James Baseball Abstract; Furtado, J. (1999)",
        description="Paul Johnson's Estimated Runs Produced linear run estimator.",
    )
)
def calc_erp(ctx: EvalContext) -> nw.Expr:
    hbp = nw.col("hbp") if "hbp" in ctx.available_columns else nw.lit(0)
    sb = nw.col("sb") if "sb" in ctx.available_columns else nw.lit(0)
    cs = nw.col("cs") if "cs" in ctx.available_columns else nw.lit(0)
    gidp = nw.col("gidp") if "gidp" in ctx.available_columns else nw.lit(0)
    inner = (
        2.0 * (nw.col("tb") + nw.col("bb") + hbp)
        + nw.col("h")
        + sb
        - 0.605 * (nw.col("ab") + cs + gidp - nw.col("h"))
    )
    return inner * 0.16

