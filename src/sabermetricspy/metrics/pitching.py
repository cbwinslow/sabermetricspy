"""Traditional pitching metrics and Defense-Independent Pitching Statistics (DIPS: FIP, xFIP, kwERA, DICE, SIERA, ERA+, ERA-, FIP-, xFIP-)."""

from __future__ import annotations

import narwhals as nw

from sabermetricspy.registry import EvalContext, MetricSpec, register_metric
from sabermetricspy.schema import missing_constant, safe_div
from sabermetricspy.types.enums import Category, Direction, ImplKind, Metric


@register_metric(
    MetricSpec(
        metric=Metric.IP,
        display_name="IP",
        category=Category.PITCHING,
        kind=ImplKind.DETERMINISTIC,
        required_columns=("outs",),
        direction=Direction.HIGHER_IS_BETTER,
        formula_latex=r"IP = \frac{Outs}{3}",
        citation="Official MLB Baseball Rules",
        description="True decimal innings pitched (outs / 3.0) for mathematical calculations.",
    )
)
def calc_ip(ctx: EvalContext) -> nw.Expr:
    return nw.col("outs").cast(nw.Float64) / 3.0


@register_metric(
    MetricSpec(
        metric=Metric.ERA,
        display_name="ERA",
        category=Category.PITCHING,
        kind=ImplKind.DETERMINISTIC,
        required_columns=("er", "outs"),
        direction=Direction.LOWER_IS_BETTER,
        formula_latex=r"ERA = \frac{27 \times ER}{Outs} = \frac{9 \times ER}{IP}",
        citation="Chadwick, H. & Heydler, J. (1912)",
        description="Earned run average per 9 innings (27 outs).",
    )
)
def calc_era(ctx: EvalContext) -> nw.Expr:
    return safe_div(27.0 * nw.col("er"), nw.col("outs"))


@register_metric(
    MetricSpec(
        metric=Metric.RA9,
        display_name="RA9",
        category=Category.PITCHING,
        kind=ImplKind.DETERMINISTIC,
        required_columns=("ra", "outs"),
        direction=Direction.LOWER_IS_BETTER,
        formula_latex=r"RA9 = \frac{27 \times RA}{Outs}",
        citation="Baseball-Reference Glossary",
        description="Total runs allowed (earned and unearned) per 9 innings (27 outs).",
    )
)
def calc_ra9(ctx: EvalContext) -> nw.Expr:
    return safe_div(27.0 * nw.col("ra"), nw.col("outs"))


@register_metric(
    MetricSpec(
        metric=Metric.WHIP,
        display_name="WHIP",
        category=Category.PITCHING,
        kind=ImplKind.DETERMINISTIC,
        required_columns=("bb", "h", "outs"),
        direction=Direction.LOWER_IS_BETTER,
        formula_latex=r"WHIP = \frac{3 \times (BB + H)}{Outs} = \frac{BB + H}{IP}",
        citation="Okrent, D. (1979)",
        description="Walks plus hits allowed per inning pitched.",
    )
)
def calc_whip(ctx: EvalContext) -> nw.Expr:
    return safe_div(3.0 * (nw.col("bb") + nw.col("h")), nw.col("outs"))


@register_metric(
    MetricSpec(
        metric=Metric.H_PER_9,
        display_name="H/9",
        category=Category.PITCHING,
        kind=ImplKind.DETERMINISTIC,
        required_columns=("h", "outs"),
        direction=Direction.LOWER_IS_BETTER,
        formula_latex=r"H/9 = \frac{27 \times H}{Outs}",
        citation="Official MLB Rules",
        description="Hits allowed per 9 innings pitched.",
    )
)
def calc_h_per_9(ctx: EvalContext) -> nw.Expr:
    return safe_div(27.0 * nw.col("h"), nw.col("outs"))


@register_metric(
    MetricSpec(
        metric=Metric.BB_PER_9,
        display_name="BB/9",
        category=Category.PITCHING,
        kind=ImplKind.DETERMINISTIC,
        required_columns=("bb", "outs"),
        direction=Direction.LOWER_IS_BETTER,
        formula_latex=r"BB/9 = \frac{27 \times BB}{Outs}",
        citation="Official MLB Rules",
        description="Walks allowed per 9 innings pitched.",
    )
)
def calc_bb_per_9(ctx: EvalContext) -> nw.Expr:
    return safe_div(27.0 * nw.col("bb"), nw.col("outs"))


@register_metric(
    MetricSpec(
        metric=Metric.K_PER_9,
        display_name="K/9",
        category=Category.PITCHING,
        kind=ImplKind.DETERMINISTIC,
        required_columns=("so", "outs"),
        direction=Direction.HIGHER_IS_BETTER,
        formula_latex=r"K/9 = \frac{27 \times SO}{Outs}",
        citation="Official MLB Rules",
        description="Strikeouts per 9 innings pitched.",
    )
)
def calc_k_per_9(ctx: EvalContext) -> nw.Expr:
    return safe_div(27.0 * nw.col("so"), nw.col("outs"))


@register_metric(
    MetricSpec(
        metric=Metric.HR_PER_9,
        display_name="HR/9",
        category=Category.PITCHING,
        kind=ImplKind.DETERMINISTIC,
        required_columns=("hr", "outs"),
        direction=Direction.LOWER_IS_BETTER,
        formula_latex=r"HR/9 = \frac{27 \times HR}{Outs}",
        citation="Official MLB Rules",
        description="Home runs allowed per 9 innings pitched.",
    )
)
def calc_hr_per_9(ctx: EvalContext) -> nw.Expr:
    return safe_div(27.0 * nw.col("hr"), nw.col("outs"))


@register_metric(
    MetricSpec(
        metric=Metric.PIT_K_PCT,
        display_name="K% (Pit)",
        category=Category.PITCHING,
        kind=ImplKind.DETERMINISTIC,
        required_columns=("so", "bf"),
        direction=Direction.HIGHER_IS_BETTER,
        formula_latex=r"K\% = \frac{SO}{TBF}",
        citation="FanGraphs Library",
        description="Pitcher strikeout rate per batter faced.",
    )
)
def calc_pit_k_pct(ctx: EvalContext) -> nw.Expr:
    return safe_div(nw.col("so"), nw.col("bf"))


@register_metric(
    MetricSpec(
        metric=Metric.PIT_BB_PCT,
        display_name="BB% (Pit)",
        category=Category.PITCHING,
        kind=ImplKind.DETERMINISTIC,
        required_columns=("bb", "bf"),
        direction=Direction.LOWER_IS_BETTER,
        formula_latex=r"BB\% = \frac{BB}{TBF}",
        citation="FanGraphs Library",
        description="Pitcher walk rate per batter faced.",
    )
)
def calc_pit_bb_pct(ctx: EvalContext) -> nw.Expr:
    return safe_div(nw.col("bb"), nw.col("bf"))


@register_metric(
    MetricSpec(
        metric=Metric.PIT_K_MINUS_BB_PCT,
        display_name="K-BB% (Pit)",
        category=Category.PITCHING,
        kind=ImplKind.DETERMINISTIC,
        required_columns=("so", "bb", "bf"),
        requires=(Metric.PIT_K_PCT, Metric.PIT_BB_PCT),
        direction=Direction.HIGHER_IS_BETTER,
        formula_latex=r"K\!-\!BB\% = \frac{SO - BB}{TBF}",
        citation="FanGraphs Library",
        description="Pitcher strikeout rate minus walk rate per batter faced.",
    )
)
def calc_pit_k_minus_bb_pct(ctx: EvalContext) -> nw.Expr:
    return nw.col("pit_k_pct") - nw.col("pit_bb_pct")


@register_metric(
    MetricSpec(
        metric=Metric.LOB_PCT,
        display_name="LOB%",
        category=Category.PITCHING,
        kind=ImplKind.DETERMINISTIC,
        required_columns=("h", "bb", "hr", "ra"),
        optional_columns=("hbp",),
        direction=Direction.HIGHER_IS_BETTER,
        formula_latex=r"LOB\% = \frac{H + BB + HBP - R}{H + BB + HBP - 1.4 \times HR}",
        citation="Tango, T. & FanGraphs Library (Left On Base %)",
        description="Estimated strand rate of baserunners allowed.",
    )
)
def calc_lob_pct(ctx: EvalContext) -> nw.Expr:
    hbp = nw.col("hbp") if "hbp" in ctx.available_columns else nw.lit(0)
    baserunners = nw.col("h") + nw.col("bb") + hbp
    num = baserunners - nw.col("ra")
    den = baserunners - 1.4 * nw.col("hr")
    return safe_div(num, den)


@register_metric(
    MetricSpec(
        metric=Metric.QS_PCT,
        display_name="QS%",
        category=Category.PITCHING,
        kind=ImplKind.DETERMINISTIC,
        required_columns=("qs", "gs"),
        direction=Direction.HIGHER_IS_BETTER,
        formula_latex=r"QS\% = \frac{QS}{GS}",
        citation="Lowe, J. (1985)",
        description="Quality start percentage per game started.",
    )
)
def calc_qs_pct(ctx: EvalContext) -> nw.Expr:
    return safe_div(nw.col("qs"), nw.col("gs"))


@register_metric(
    MetricSpec(
        metric=Metric.CG_PCT,
        display_name="CG%",
        category=Category.PITCHING,
        kind=ImplKind.DETERMINISTIC,
        required_columns=("cg", "gs"),
        direction=Direction.HIGHER_IS_BETTER,
        formula_latex=r"CG\% = \frac{CG}{GS}",
        citation="Official MLB Rules",
        description="Complete game percentage per game started.",
    )
)
def calc_cg_pct(ctx: EvalContext) -> nw.Expr:
    return safe_div(nw.col("cg"), nw.col("gs"))


@register_metric(
    MetricSpec(
        metric=Metric.SV_PCT,
        display_name="SV%",
        category=Category.PITCHING,
        kind=ImplKind.DETERMINISTIC,
        required_columns=("sv", "bs"),
        direction=Direction.HIGHER_IS_BETTER,
        formula_latex=r"SV\% = \frac{SV}{SV + BS}",
        citation="Holtzman, J. (1960)",
        description="Save conversion rate.",
    )
)
def calc_sv_pct(ctx: EvalContext) -> nw.Expr:
    return safe_div(nw.col("sv"), nw.col("sv") + nw.col("bs"))


# ==============================================================================
# Defense-Independent Pitching Statistics (DIPS) & Indexed Pitching
# ==============================================================================


@register_metric(
    MetricSpec(
        metric=Metric.FIP,
        display_name="FIP",
        category=Category.DEFENSE_INDEPENDENT_PITCHING,
        kind=ImplKind.CONTEXTUAL,
        required_columns=("hr", "bb", "so", "outs"),
        optional_columns=("ibb", "hbp"),
        requires=(Metric.UBB,),
        direction=Direction.LOWER_IS_BETTER,
        formula_latex=r"FIP = \frac{13(HR) + 3(uBB + HBP) - 2(SO)}{IP} + C_{FIP}",
        citation="McCracken, V. (2001); Tango, T. (2007); Basco, D. & Davies, M. (2010) SABR BRJ",
        description="Fielding Independent Pitching scaled to league ERA.",
        caveats=(
            "Assumes pitchers have no control over BABIP; see Tippett (2003) and Lichtman (2004).",
        ),
    )
)
def calc_fip(ctx: EvalContext) -> nw.Expr:
    hbp = nw.col("hbp") if "hbp" in ctx.available_columns else nw.lit(0)
    num = 13.0 * nw.col("hr") + 3.0 * (nw.col("ubb") + hbp) - 2.0 * nw.col("so")
    ip = nw.col("outs").cast(nw.Float64) / 3.0
    return safe_div(num, ip) + ctx.weights.c_fip


@register_metric(
    MetricSpec(
        metric=Metric.XFIP,
        display_name="xFIP",
        category=Category.DEFENSE_INDEPENDENT_PITCHING,
        kind=ImplKind.CONTEXTUAL,
        required_columns=("fb", "bb", "so", "outs"),
        optional_columns=("ibb", "hbp"),
        requires=(Metric.UBB,),
        direction=Direction.LOWER_IS_BETTER,
        formula_latex=r"xFIP = \frac{13(FB \times lgHR/FB) + 3(uBB + HBP) - 2(SO)}{IP} + C_{FIP}",
        citation="Studeman, D. (2005) The Hardball Times",
        description="Expected Fielding Independent Pitching normalizing HR/FB rate to league average.",
    )
)
def calc_xfip(ctx: EvalContext) -> nw.Expr:
    w = ctx.weights
    hbp = nw.col("hbp") if "hbp" in ctx.available_columns else nw.lit(0)
    if w.lg_hr_per_fb is None:
        return missing_constant()
    x_hr = nw.col("fb") * w.lg_hr_per_fb
    num = 13.0 * x_hr + 3.0 * (nw.col("ubb") + hbp) - 2.0 * nw.col("so")
    ip = nw.col("outs").cast(nw.Float64) / 3.0
    return safe_div(num, ip) + w.c_fip


@register_metric(
    MetricSpec(
        metric=Metric.DICE,
        display_name="DICE",
        category=Category.DEFENSE_INDEPENDENT_PITCHING,
        kind=ImplKind.DETERMINISTIC,
        required_columns=("hr", "bb", "so", "outs"),
        optional_columns=("hbp",),
        direction=Direction.LOWER_IS_BETTER,
        formula_latex=r"DICE = 3.00 + \frac{13(HR) + 3(BB + HBP) - 2(SO)}{IP}",
        citation="Dreslough, C. (2000); Basco, D. & Davies, M. (2010) SABR BRJ",
        description="Defense-Independent Component ERA with fixed 3.00 baseline constant.",
    )
)
def calc_dice(ctx: EvalContext) -> nw.Expr:
    hbp = nw.col("hbp") if "hbp" in ctx.available_columns else nw.lit(0)
    num = 13.0 * nw.col("hr") + 3.0 * (nw.col("bb") + hbp) - 2.0 * nw.col("so")
    ip = nw.col("outs").cast(nw.Float64) / 3.0
    return safe_div(num, ip) + 3.0


@register_metric(
    MetricSpec(
        metric=Metric.KWERA,
        display_name="kwERA",
        category=Category.DEFENSE_INDEPENDENT_PITCHING,
        kind=ImplKind.DETERMINISTIC,
        required_columns=("so", "bb", "bf"),
        direction=Direction.LOWER_IS_BETTER,
        formula_latex=r"kwERA = 5.40 - 12 \times \left(\frac{SO - BB}{TBF}\right)",
        citation="Tango, T. & The Hardball Times",
        description="Strikeout-and-walk-based ERA estimator.",
    )
)
def calc_kwera(ctx: EvalContext) -> nw.Expr:
    return 5.40 - 12.0 * safe_div(nw.col("so") - nw.col("bb"), nw.col("bf"))


@register_metric(
    MetricSpec(
        metric=Metric.SIERA,
        display_name="SIERA",
        category=Category.DEFENSE_INDEPENDENT_PITCHING,
        kind=ImplKind.CONTEXTUAL,
        required_columns=("so", "bb", "gb", "fb", "bf"),
        optional_columns=("pu",),
        direction=Direction.LOWER_IS_BETTER,
        formula_latex=r"SIERA = \beta_0 + \beta_1(SO/PA) + \beta_2(BB/PA) + \beta_3(netGB/PA) + \dots",
        citation="Swartz, M. & Seidman, E. (2010) Baseball Prospectus; FanGraphs Library",
        description="Skill-Interactive Earned Run Average accounting for non-linear strikeout, walk, and ground-ball interactions.",
    )
)
def calc_siera(ctx: EvalContext) -> nw.Expr:
    c = ctx.season_context.siera_coeffs
    pu = nw.col("pu") if "pu" in ctx.available_columns else nw.lit(0)
    so_pa = safe_div(nw.col("so"), nw.col("bf"))
    bb_pa = safe_div(nw.col("bb"), nw.col("bf"))
    net_gb_raw = nw.col("gb") - nw.col("fb") - pu
    net_gb_pa = safe_div(net_gb_raw, nw.col("bf"))
    # Sign-adjusted squared net_gb term: negative when net_gb > 0, positive when net_gb <= 0
    net_gb_sq_signed = (
        nw.when(net_gb_pa > 0.0).then(net_gb_pa * net_gb_pa).otherwise(-(net_gb_pa * net_gb_pa))
    )
    return (
        c.intercept
        + c.so_per_pa * so_pa
        + c.bb_per_pa * bb_pa
        + c.net_gb_per_pa * net_gb_pa
        + c.so_per_pa_sq * (so_pa * so_pa)
        + c.net_gb_per_pa_sq * net_gb_sq_signed
        + c.so_x_net_gb * (so_pa * net_gb_pa)
        + c.bb_x_net_gb * (bb_pa * net_gb_pa)
        + c.so_x_bb * (so_pa * bb_pa)
    )


@register_metric(
    MetricSpec(
        metric=Metric.ERA_PLUS,
        display_name="ERA+",
        category=Category.DEFENSE_INDEPENDENT_PITCHING,
        kind=ImplKind.CONTEXTUAL,
        required_columns=("er", "outs"),
        requires=(Metric.ERA,),
        direction=Direction.HIGHER_IS_BETTER,
        formula_latex=r"ERA^+ = 100 \times \frac{lgERA \times PF}{ERA}",
        citation="Baseball-Reference Glossary (ERA+)",
        description="Park- and league-adjusted ERA where 100 is league average and higher is better.",
    )
)
def calc_era_plus(ctx: EvalContext) -> nw.Expr:
    if ctx.weights.lg_era is None:
        return missing_constant()
    pf = ctx.season_context.park_factor / 100.0
    return safe_div(100.0 * ctx.weights.lg_era * pf, nw.col("era"))


@register_metric(
    MetricSpec(
        metric=Metric.ERA_MINUS,
        display_name="ERA-",
        category=Category.DEFENSE_INDEPENDENT_PITCHING,
        kind=ImplKind.CONTEXTUAL,
        required_columns=("er", "outs"),
        requires=(Metric.ERA,),
        direction=Direction.LOWER_IS_BETTER,
        formula_latex=r"ERA^- = 100 \times \frac{ERA}{lgERA \times PF}",
        citation="FanGraphs Library (ERA-)",
        description="Park- and league-adjusted ERA where 100 is league average and lower is better.",
    )
)
def calc_era_minus(ctx: EvalContext) -> nw.Expr:
    if ctx.weights.lg_era is None:
        return missing_constant()
    pf = ctx.season_context.park_factor / 100.0
    return safe_div(100.0 * nw.col("era"), ctx.weights.lg_era * pf)


@register_metric(
    MetricSpec(
        metric=Metric.FIP_MINUS,
        display_name="FIP-",
        category=Category.DEFENSE_INDEPENDENT_PITCHING,
        kind=ImplKind.CONTEXTUAL,
        required_columns=("hr", "bb", "so", "outs"),
        optional_columns=("ibb", "hbp"),
        requires=(Metric.FIP,),
        direction=Direction.LOWER_IS_BETTER,
        formula_latex=r"FIP^- = 100 \times \frac{FIP}{lgFIP \times PF}",
        citation="FanGraphs Library (FIP-)",
        description="Park- and league-adjusted FIP where 100 is league average and lower is better.",
    )
)
def calc_fip_minus(ctx: EvalContext) -> nw.Expr:
    if ctx.weights.lg_fip is None:
        return missing_constant()
    pf = ctx.season_context.park_factor / 100.0
    return safe_div(100.0 * nw.col("fip"), ctx.weights.lg_fip * pf)


@register_metric(
    MetricSpec(
        metric=Metric.XFIP_MINUS,
        display_name="xFIP-",
        category=Category.DEFENSE_INDEPENDENT_PITCHING,
        kind=ImplKind.CONTEXTUAL,
        required_columns=("fb", "bb", "so", "outs"),
        optional_columns=("ibb", "hbp"),
        requires=(Metric.XFIP,),
        direction=Direction.LOWER_IS_BETTER,
        formula_latex=r"xFIP^- = 100 \times \frac{xFIP}{lgxFIP \times PF}",
        citation="FanGraphs Library (xFIP-)",
        description="Park- and league-adjusted xFIP where 100 is league average and lower is better.",
    )
)
def calc_xfip_minus(ctx: EvalContext) -> nw.Expr:
    if ctx.weights.lg_xfip is None:
        return missing_constant()
    pf = ctx.season_context.park_factor / 100.0
    return safe_div(100.0 * nw.col("xfip"), ctx.weights.lg_xfip * pf)


@register_metric(
    MetricSpec(
        metric=Metric.PIT_BB_TO_K,
        display_name="BB/K (Pit)",
        category=Category.PITCHING,
        kind=ImplKind.DETERMINISTIC,
        required_columns=("bb", "so"),
        direction=Direction.LOWER_IS_BETTER,
        formula_latex=r"BB/K = \frac{BB}{SO}",
        citation="Official MLB Rules; FanGraphs Library",
        description="Pitcher walk-to-strikeout ratio.",
    )
)
def calc_pit_bb_to_k(ctx: EvalContext) -> nw.Expr:
    return safe_div(nw.col("bb"), nw.col("so"))


@register_metric(
    MetricSpec(
        metric=Metric.PIT_K_TO_BB,
        display_name="K/BB (Pit)",
        category=Category.PITCHING,
        kind=ImplKind.DETERMINISTIC,
        required_columns=("so", "bb"),
        direction=Direction.HIGHER_IS_BETTER,
        formula_latex=r"K/BB = \frac{SO}{BB}",
        citation="Official MLB Rules; FanGraphs Library",
        description="Pitcher strikeout-to-walk ratio.",
    )
)
def calc_pit_k_to_bb(ctx: EvalContext) -> nw.Expr:
    return safe_div(nw.col("so"), nw.col("bb"))


@register_metric(
    MetricSpec(
        metric=Metric.BF_PER_IP,
        display_name="BF/IP",
        category=Category.PITCHING,
        kind=ImplKind.DETERMINISTIC,
        required_columns=("bf", "outs"),
        direction=Direction.LOWER_IS_BETTER,
        formula_latex=r"BF/IP = \frac{3 \times TBF}{Outs}",
        citation="Baseball-Reference Glossary",
        description="Batters faced per inning pitched.",
    )
)
def calc_bf_per_ip(ctx: EvalContext) -> nw.Expr:
    return safe_div(3.0 * nw.col("bf"), nw.col("outs"))


@register_metric(
    MetricSpec(
        metric=Metric.K_PCT_PLUS,
        display_name="K%+",
        category=Category.DEFENSE_INDEPENDENT_PITCHING,
        kind=ImplKind.CONTEXTUAL,
        required_columns=("so", "bf"),
        requires=(Metric.PIT_K_PCT,),
        direction=Direction.HIGHER_IS_BETTER,
        formula_latex=r"K\%^+ = 100 \times \frac{K\%}{lgK\%}",
        citation="FanGraphs Library (Plus Stats)",
        description="League-indexed pitcher strikeout rate (100 = league average, higher is better).",
    )
)
def calc_k_pct_plus(ctx: EvalContext) -> nw.Expr:
    return safe_div(100.0 * nw.col("pit_k_pct"), ctx.weights.lg_k_pct)


@register_metric(
    MetricSpec(
        metric=Metric.BB_PCT_PLUS,
        display_name="BB%+",
        category=Category.DEFENSE_INDEPENDENT_PITCHING,
        kind=ImplKind.CONTEXTUAL,
        required_columns=("bb", "bf"),
        requires=(Metric.PIT_BB_PCT,),
        direction=Direction.LOWER_IS_BETTER,
        formula_latex=r"BB\%^+ = 100 \times \frac{BB\%}{lgBB\%}",
        citation="FanGraphs Library (Plus Stats)",
        description="League-indexed pitcher walk rate (100 = league average, lower is better).",
    )
)
def calc_bb_pct_plus(ctx: EvalContext) -> nw.Expr:
    return safe_div(100.0 * nw.col("pit_bb_pct"), ctx.weights.lg_bb_pct)


@register_metric(
    MetricSpec(
        metric=Metric.QERA,
        display_name="QERA",
        category=Category.DEFENSE_INDEPENDENT_PITCHING,
        kind=ImplKind.DETERMINISTIC,
        required_columns=("so", "bb", "gb", "bbe", "bf"),
        direction=Direction.LOWER_IS_BETTER,
        formula_latex=r"QERA = \left(2.69 - 0.66\frac{GB}{BBE} + 3.88\frac{BB}{TBF} - 3.40\frac{SO}{TBF}\right)^2",
        citation="Silver, N. (2006) Baseball Prospectus; Basco, D. & Davies, M. (2010) SABR BRJ",
        description="Nate Silver's Quick ERA estimator combining ground-ball rate, walk rate, and strikeout rate.",
    )
)
def calc_qera(ctx: EvalContext) -> nw.Expr:
    gb_rate = safe_div(nw.col("gb"), nw.col("bbe"))
    bb_rate = safe_div(nw.col("bb"), nw.col("bf"))
    so_rate = safe_div(nw.col("so"), nw.col("bf"))
    root = 2.69 - 0.66 * gb_rate + 3.88 * bb_rate - 3.40 * so_rate
    return root * root


@register_metric(
    MetricSpec(
        metric=Metric.DIPS_BOP_PCT,
        display_name="BOP% (DIPS)",
        category=Category.DEFENSE_INDEPENDENT_PITCHING,
        kind=ImplKind.DETERMINISTIC,
        required_columns=("hr", "bb", "so", "bf"),
        optional_columns=("hbp",),
        direction=Direction.NEUTRAL,
        formula_latex=r"BOP\% = \frac{HR + BB + HBP + SO}{TBF}",
        citation="McCracken, V. (2001) Pitching and Defense; Basco, D. & Davies, M. (2010) SABR BRJ",
        description="Voros McCracken's DIPS 1.0 rate of batters faced whose plate appearance ends without a ball in play (Three True Outcomes + HBP rate).",
    )
)
def calc_dips_bop_pct(ctx: EvalContext) -> nw.Expr:
    hbp = nw.col("hbp") if "hbp" in ctx.available_columns else nw.lit(0)
    return safe_div(nw.col("hr") + nw.col("bb") + hbp + nw.col("so"), nw.col("bf"))


@register_metric(
    MetricSpec(
        metric=Metric.XERA,
        display_name="xERA",
        category=Category.DEFENSE_INDEPENDENT_PITCHING,
        kind=ImplKind.CONTEXTUAL,
        required_columns=("xwoba_sum", "xwoba_count", "bf", "outs"),
        requires=(Metric.XWOBA, Metric.BF_PER_IP),
        direction=Direction.LOWER_IS_BETTER,
        formula_latex=r"xERA = lgERA + \left(\frac{xwOBA - lgwOBA}{wOBAScale}\right) \times 9 \times \frac{TBF}{IP}",
        citation="MLB Statcast / Baseball Savant Glossary (Expected ERA)",
        description="Statcast Expected ERA translating a pitcher's xwOBA allowed onto the 9-inning ERA scale.",
    )
)
def calc_xera(ctx: EvalContext) -> nw.Expr:
    w = ctx.weights
    if w.lg_era is None:
        return missing_constant()
    runs_above_avg_per_pa = (nw.col("xwoba") - w.lg_woba) / w.woba_scale
    return w.lg_era + runs_above_avg_per_pa * 9.0 * nw.col("bf_per_ip")
