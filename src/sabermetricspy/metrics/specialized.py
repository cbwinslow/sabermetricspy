"""Plate discipline, Batted-Ball quality, Baserunning, Fielding, and Team Pythagorean/Pythagenpat metrics."""

from __future__ import annotations

import narwhals as nw

from sabermetricspy.registry import EvalContext, MetricSpec, register_metric
from sabermetricspy.schema import safe_div
from sabermetricspy.types.enums import Category, Direction, ImplKind, Metric

# ==============================================================================
# Plate Discipline
# ==============================================================================


@register_metric(
    MetricSpec(
        metric=Metric.SWING_PCT,
        display_name="Swing%",
        category=Category.PLATE_DISCIPLINE,
        kind=ImplKind.DETERMINISTIC,
        required_columns=("swings", "pitches"),
        direction=Direction.NEUTRAL,
        formula_latex=r"Swing\% = \frac{Swings}{Pitches}",
        citation="FanGraphs Library (Plate Discipline)",
        description="Overall swing rate across all pitches.",
    )
)
def calc_swing_pct(ctx: EvalContext) -> nw.Expr:
    return safe_div(nw.col("swings"), nw.col("pitches"))


@register_metric(
    MetricSpec(
        metric=Metric.Z_SWING_PCT,
        display_name="Z-Swing%",
        category=Category.PLATE_DISCIPLINE,
        kind=ImplKind.DETERMINISTIC,
        required_columns=("zone_swings", "zone_pitches"),
        direction=Direction.HIGHER_IS_BETTER,
        formula_latex=r"Z\text{-}Swing\% = \frac{ZoneSwings}{ZonePitches}",
        citation="FanGraphs Library (Plate Discipline)",
        description="Swing rate on pitches inside the strike zone.",
    )
)
def calc_z_swing_pct(ctx: EvalContext) -> nw.Expr:
    return safe_div(nw.col("zone_swings"), nw.col("zone_pitches"))


@register_metric(
    MetricSpec(
        metric=Metric.O_SWING_PCT,
        display_name="O-Swing%",
        category=Category.PLATE_DISCIPLINE,
        kind=ImplKind.DETERMINISTIC,
        required_columns=("out_zone_swings", "out_zone_pitches"),
        direction=Direction.LOWER_IS_BETTER,
        formula_latex=r"O\text{-}Swing\% = \frac{OutZoneSwings}{OutZonePitches}",
        citation="FanGraphs Library (Plate Discipline)",
        description="Chase rate on pitches outside the strike zone.",
    )
)
def calc_o_swing_pct(ctx: EvalContext) -> nw.Expr:
    return safe_div(nw.col("out_zone_swings"), nw.col("out_zone_pitches"))


@register_metric(
    MetricSpec(
        metric=Metric.ZONE_PCT,
        display_name="Zone%",
        category=Category.PLATE_DISCIPLINE,
        kind=ImplKind.DETERMINISTIC,
        required_columns=("zone_pitches", "pitches"),
        direction=Direction.HIGHER_IS_BETTER,
        formula_latex=r"Zone\% = \frac{ZonePitches}{Pitches}",
        citation="FanGraphs Library (Plate Discipline)",
        description="Percentage of pitches seen or thrown inside the strike zone.",
    )
)
def calc_zone_pct(ctx: EvalContext) -> nw.Expr:
    return safe_div(nw.col("zone_pitches"), nw.col("pitches"))


@register_metric(
    MetricSpec(
        metric=Metric.CONTACT_PCT,
        display_name="Contact%",
        category=Category.PLATE_DISCIPLINE,
        kind=ImplKind.DETERMINISTIC,
        required_columns=("contacts", "swings"),
        direction=Direction.HIGHER_IS_BETTER,
        formula_latex=r"Contact\% = \frac{Contacts}{Swings}",
        citation="FanGraphs Library (Plate Discipline)",
        description="Percentage of swings resulting in contact (foul or in-play).",
    )
)
def calc_contact_pct(ctx: EvalContext) -> nw.Expr:
    return safe_div(nw.col("contacts"), nw.col("swings"))


@register_metric(
    MetricSpec(
        metric=Metric.Z_CONTACT_PCT,
        display_name="Z-Contact%",
        category=Category.PLATE_DISCIPLINE,
        kind=ImplKind.DETERMINISTIC,
        required_columns=("zone_contacts", "zone_swings"),
        direction=Direction.HIGHER_IS_BETTER,
        formula_latex=r"Z\text{-}Contact\% = \frac{ZoneContacts}{ZoneSwings}",
        citation="FanGraphs Library (Plate Discipline)",
        description="Contact rate on swings at pitches inside the strike zone.",
    )
)
def calc_z_contact_pct(ctx: EvalContext) -> nw.Expr:
    return safe_div(nw.col("zone_contacts"), nw.col("zone_swings"))


@register_metric(
    MetricSpec(
        metric=Metric.O_CONTACT_PCT,
        display_name="O-Contact%",
        category=Category.PLATE_DISCIPLINE,
        kind=ImplKind.DETERMINISTIC,
        required_columns=("out_zone_contacts", "out_zone_swings"),
        direction=Direction.HIGHER_IS_BETTER,
        formula_latex=r"O\text{-}Contact\% = \frac{OutZoneContacts}{OutZoneSwings}",
        citation="FanGraphs Library (Plate Discipline)",
        description="Contact rate on swings at pitches outside the strike zone.",
    )
)
def calc_o_contact_pct(ctx: EvalContext) -> nw.Expr:
    return safe_div(nw.col("out_zone_contacts"), nw.col("out_zone_swings"))


@register_metric(
    MetricSpec(
        metric=Metric.WHIFF_PCT,
        display_name="Whiff%",
        category=Category.PLATE_DISCIPLINE,
        kind=ImplKind.DETERMINISTIC,
        required_columns=("whiffs", "swings"),
        direction=Direction.LOWER_IS_BETTER,
        formula_latex=r"Whiff\% = \frac{Whiffs}{Swings}",
        citation="Baseball Savant / Statcast Glossary",
        description="Swinging strikes divided by total swings.",
    )
)
def calc_whiff_pct(ctx: EvalContext) -> nw.Expr:
    return safe_div(nw.col("whiffs"), nw.col("swings"))


@register_metric(
    MetricSpec(
        metric=Metric.SWSTR_PCT,
        display_name="SwStr%",
        category=Category.PLATE_DISCIPLINE,
        kind=ImplKind.DETERMINISTIC,
        required_columns=("whiffs", "pitches"),
        direction=Direction.LOWER_IS_BETTER,
        formula_latex=r"SwStr\% = \frac{Whiffs}{Pitches}",
        citation="FanGraphs Library (Plate Discipline)",
        description="Swinging strikes divided by total pitches.",
    )
)
def calc_swstr_pct(ctx: EvalContext) -> nw.Expr:
    return safe_div(nw.col("whiffs"), nw.col("pitches"))


@register_metric(
    MetricSpec(
        metric=Metric.CSTR_PCT,
        display_name="CStr%",
        category=Category.PLATE_DISCIPLINE,
        kind=ImplKind.DETERMINISTIC,
        required_columns=("called_strikes", "pitches"),
        direction=Direction.NEUTRAL,
        formula_latex=r"CStr\% = \frac{CalledStrikes}{Pitches}",
        citation="FanGraphs Library (Plate Discipline)",
        description="Called strikes divided by total pitches.",
    )
)
def calc_cstr_pct(ctx: EvalContext) -> nw.Expr:
    return safe_div(nw.col("called_strikes"), nw.col("pitches"))


@register_metric(
    MetricSpec(
        metric=Metric.CSW_PCT,
        display_name="CSW%",
        category=Category.PLATE_DISCIPLINE,
        kind=ImplKind.DETERMINISTIC,
        required_columns=("called_strikes", "whiffs", "pitches"),
        direction=Direction.HIGHER_IS_BETTER,
        formula_latex=r"CSW\% = \frac{CalledStrikes + Whiffs}{Pitches}",
        citation="Fast, A. & Pollack, N. (2019) Pitcher List",
        description="Called Strikes plus Whiffs divided by total pitches.",
    )
)
def calc_csw_pct(ctx: EvalContext) -> nw.Expr:
    return safe_div(nw.col("called_strikes") + nw.col("whiffs"), nw.col("pitches"))


@register_metric(
    MetricSpec(
        metric=Metric.FOUL_PCT,
        display_name="Foul%",
        category=Category.PLATE_DISCIPLINE,
        kind=ImplKind.DETERMINISTIC,
        required_columns=("fouls", "swings"),
        direction=Direction.NEUTRAL,
        formula_latex=r"Foul\% = \frac{Fouls}{Swings}",
        citation="Baseball Savant Glossary",
        description="Foul balls divided by total swings.",
    )
)
def calc_foul_pct(ctx: EvalContext) -> nw.Expr:
    return safe_div(nw.col("fouls"), nw.col("swings"))


@register_metric(
    MetricSpec(
        metric=Metric.FP_SWING_PCT,
        display_name="F-Swing%",
        category=Category.PLATE_DISCIPLINE,
        kind=ImplKind.DETERMINISTIC,
        required_columns=("first_pitch_swings", "pa"),
        direction=Direction.NEUTRAL,
        formula_latex=r"F\text{-}Swing\% = \frac{FirstPitchSwings}{PA}",
        citation="FanGraphs Library",
        description="First-pitch swing percentage.",
    )
)
def calc_fp_swing_pct(ctx: EvalContext) -> nw.Expr:
    return safe_div(nw.col("first_pitch_swings"), nw.col("pa"))


@register_metric(
    MetricSpec(
        metric=Metric.FP_STRIKE_PCT,
        display_name="F-Strike%",
        category=Category.PLATE_DISCIPLINE,
        kind=ImplKind.DETERMINISTIC,
        required_columns=("first_pitch_strikes", "pa"),
        direction=Direction.HIGHER_IS_BETTER,
        formula_latex=r"F\text{-}Strike\% = \frac{FirstPitchStrikes}{PA}",
        citation="FanGraphs Library",
        description="First-pitch strike percentage.",
    )
)
def calc_fp_strike_pct(ctx: EvalContext) -> nw.Expr:
    return safe_div(nw.col("first_pitch_strikes"), nw.col("pa"))


# ==============================================================================
# Batted-Ball & Contact Quality
# ==============================================================================


@register_metric(
    MetricSpec(
        metric=Metric.GB_PCT,
        display_name="GB%",
        category=Category.BATTED_BALL,
        kind=ImplKind.DETERMINISTIC,
        required_columns=("gb", "bbe"),
        direction=Direction.NEUTRAL,
        formula_latex=r"GB\% = \frac{GB}{BBE}",
        citation="FanGraphs Library (Batted Ball)",
        description="Ground-ball rate per batted-ball event.",
    )
)
def calc_gb_pct(ctx: EvalContext) -> nw.Expr:
    return safe_div(nw.col("gb"), nw.col("bbe"))


@register_metric(
    MetricSpec(
        metric=Metric.FB_PCT,
        display_name="FB%",
        category=Category.BATTED_BALL,
        kind=ImplKind.DETERMINISTIC,
        required_columns=("fb", "bbe"),
        direction=Direction.NEUTRAL,
        formula_latex=r"FB\% = \frac{FB}{BBE}",
        citation="FanGraphs Library (Batted Ball)",
        description="Fly-ball rate per batted-ball event.",
    )
)
def calc_fb_pct(ctx: EvalContext) -> nw.Expr:
    return safe_div(nw.col("fb"), nw.col("bbe"))


@register_metric(
    MetricSpec(
        metric=Metric.LD_PCT,
        display_name="LD%",
        category=Category.BATTED_BALL,
        kind=ImplKind.DETERMINISTIC,
        required_columns=("ld", "bbe"),
        direction=Direction.HIGHER_IS_BETTER,
        formula_latex=r"LD\% = \frac{LD}{BBE}",
        citation="FanGraphs Library (Batted Ball)",
        description="Line-drive rate per batted-ball event.",
    )
)
def calc_ld_pct(ctx: EvalContext) -> nw.Expr:
    return safe_div(nw.col("ld"), nw.col("bbe"))


@register_metric(
    MetricSpec(
        metric=Metric.PU_PCT,
        display_name="PU%",
        category=Category.BATTED_BALL,
        kind=ImplKind.DETERMINISTIC,
        required_columns=("pu", "bbe"),
        direction=Direction.LOWER_IS_BETTER,
        formula_latex=r"PU\% = \frac{PU}{BBE}",
        citation="FanGraphs Library (Batted Ball)",
        description="Popup / infield fly-ball rate per batted-ball event.",
    )
)
def calc_pu_pct(ctx: EvalContext) -> nw.Expr:
    return safe_div(nw.col("pu"), nw.col("bbe"))


@register_metric(
    MetricSpec(
        metric=Metric.GB_TO_FB,
        display_name="GB/FB",
        category=Category.BATTED_BALL,
        kind=ImplKind.DETERMINISTIC,
        required_columns=("gb", "fb"),
        direction=Direction.NEUTRAL,
        formula_latex=r"GB/FB = \frac{GB}{FB}",
        citation="FanGraphs Library (Batted Ball)",
        description="Ground-ball to fly-ball ratio.",
    )
)
def calc_gb_to_fb(ctx: EvalContext) -> nw.Expr:
    return safe_div(nw.col("gb"), nw.col("fb"))


@register_metric(
    MetricSpec(
        metric=Metric.HR_TO_FB,
        display_name="HR/FB",
        category=Category.BATTED_BALL,
        kind=ImplKind.DETERMINISTIC,
        required_columns=("hr", "fb"),
        direction=Direction.HIGHER_IS_BETTER,
        formula_latex=r"HR/FB = \frac{HR}{FB}",
        citation="Studeman, D. (2005); FanGraphs Library",
        description="Home runs per fly ball.",
    )
)
def calc_hr_to_fb(ctx: EvalContext) -> nw.Expr:
    return safe_div(nw.col("hr"), nw.col("fb"))


@register_metric(
    MetricSpec(
        metric=Metric.PULL_PCT,
        display_name="Pull%",
        category=Category.BATTED_BALL,
        kind=ImplKind.DETERMINISTIC,
        required_columns=("pull_bbe", "bbe"),
        direction=Direction.NEUTRAL,
        formula_latex=r"Pull\% = \frac{PullBBE}{BBE}",
        citation="FanGraphs Library (Batted Ball)",
        description="Pulled batted-ball rate.",
    )
)
def calc_pull_pct(ctx: EvalContext) -> nw.Expr:
    return safe_div(nw.col("pull_bbe"), nw.col("bbe"))


@register_metric(
    MetricSpec(
        metric=Metric.CENT_PCT,
        display_name="Cent%",
        category=Category.BATTED_BALL,
        kind=ImplKind.DETERMINISTIC,
        required_columns=("cent_bbe", "bbe"),
        direction=Direction.NEUTRAL,
        formula_latex=r"Cent\% = \frac{CentBBE}{BBE}",
        citation="FanGraphs Library (Batted Ball)",
        description="Center-field batted-ball rate.",
    )
)
def calc_cent_pct(ctx: EvalContext) -> nw.Expr:
    return safe_div(nw.col("cent_bbe"), nw.col("bbe"))


@register_metric(
    MetricSpec(
        metric=Metric.OPPO_PCT,
        display_name="Oppo%",
        category=Category.BATTED_BALL,
        kind=ImplKind.DETERMINISTIC,
        required_columns=("oppo_bbe", "bbe"),
        direction=Direction.NEUTRAL,
        formula_latex=r"Oppo\% = \frac{OppoBBE}{BBE}",
        citation="FanGraphs Library (Batted Ball)",
        description="Opposite-field batted-ball rate.",
    )
)
def calc_oppo_pct(ctx: EvalContext) -> nw.Expr:
    return safe_div(nw.col("oppo_bbe"), nw.col("bbe"))


@register_metric(
    MetricSpec(
        metric=Metric.HARD_HIT_PCT,
        display_name="HardHit%",
        category=Category.BATTED_BALL,
        kind=ImplKind.DETERMINISTIC,
        required_columns=("hard_hit_bbe", "bbe"),
        direction=Direction.HIGHER_IS_BETTER,
        formula_latex=r"HardHit\% = \frac{BBE_{EV \ge 95}}{BBE}",
        citation="MLB Statcast Glossary (Hard-Hit Rate)",
        description="Percentage of batted-ball events with exit velocity >= 95.0 mph.",
    )
)
def calc_hard_hit_pct(ctx: EvalContext) -> nw.Expr:
    return safe_div(nw.col("hard_hit_bbe"), nw.col("bbe"))


@register_metric(
    MetricSpec(
        metric=Metric.SWEET_SPOT_PCT,
        display_name="SweetSpot%",
        category=Category.BATTED_BALL,
        kind=ImplKind.DETERMINISTIC,
        required_columns=("sweet_spot_bbe", "bbe"),
        direction=Direction.HIGHER_IS_BETTER,
        formula_latex=r"SweetSpot\% = \frac{BBE_{8^\circ \le LA \le 32^\circ}}{BBE}",
        citation="MLB Statcast Glossary (Sweet-Spot %)",
        description="Percentage of batted-ball events with launch angle between 8 and 32 degrees.",
    )
)
def calc_sweet_spot_pct(ctx: EvalContext) -> nw.Expr:
    return safe_div(nw.col("sweet_spot_bbe"), nw.col("bbe"))


@register_metric(
    MetricSpec(
        metric=Metric.BARREL_PCT,
        display_name="Barrel%",
        category=Category.BATTED_BALL,
        kind=ImplKind.DETERMINISTIC,
        required_columns=("barrels", "bbe"),
        direction=Direction.HIGHER_IS_BETTER,
        formula_latex=r"Barrel\% = \frac{Barrels}{BBE}",
        citation="Petriello, M. (2016) MLB Statcast Barrel Definition",
        description="Percentage of batted-ball events classified as Statcast Barrels.",
    )
)
def calc_barrel_pct(ctx: EvalContext) -> nw.Expr:
    return safe_div(nw.col("barrels"), nw.col("bbe"))


@register_metric(
    MetricSpec(
        metric=Metric.AVG_EV,
        display_name="Avg EV",
        category=Category.BATTED_BALL,
        kind=ImplKind.DETERMINISTIC,
        required_columns=("ev_sum", "ev_count"),
        direction=Direction.HIGHER_IS_BETTER,
        formula_latex=r"\overline{EV} = \frac{\sum EV}{N_{EV}}",
        citation="MLB Statcast Glossary",
        description="Average exit velocity computed from summed exit velocity over tracked batted balls.",
    )
)
def calc_avg_ev(ctx: EvalContext) -> nw.Expr:
    return safe_div(nw.col("ev_sum"), nw.col("ev_count"))


# ==============================================================================
# Baserunning, Fielding, and Team Metrics
# ==============================================================================


@register_metric(
    MetricSpec(
        metric=Metric.SB_PCT,
        display_name="SB%",
        category=Category.BASERUNNING,
        kind=ImplKind.DETERMINISTIC,
        required_columns=("sb", "cs"),
        direction=Direction.HIGHER_IS_BETTER,
        formula_latex=r"SB\% = \frac{SB}{SB + CS}",
        citation="Official MLB Baseball Rules",
        description="Stolen base success rate.",
    )
)
def calc_sb_pct(ctx: EvalContext) -> nw.Expr:
    return safe_div(nw.col("sb"), nw.col("sb") + nw.col("cs"))


@register_metric(
    MetricSpec(
        metric=Metric.WSB,
        display_name="wSB",
        category=Category.BASERUNNING,
        kind=ImplKind.CONTEXTUAL,
        required_columns=("sb", "cs", "h", "b2", "b3", "hr", "bb"),
        optional_columns=("ibb", "hbp"),
        requires=(Metric.B1, Metric.UBB),
        direction=Direction.HIGHER_IS_BETTER,
        formula_latex=r"wSB = (SB \times runSB) + (CS \times runCS) - lgwSB \times (1B + uBB + HBP)",
        citation="FanGraphs Library (wSB)",
        description="Weighted Stolen Base Runs above average.",
    )
)
def calc_wsb(ctx: EvalContext) -> nw.Expr:
    w = ctx.weights
    hbp = nw.col("hbp") if "hbp" in ctx.available_columns else nw.lit(0)
    opp = nw.col("b1") + nw.col("ubb") + hbp
    return nw.col("sb") * w.r_sb + nw.col("cs") * w.r_cs - w.lg_wsb * opp


@register_metric(
    MetricSpec(
        metric=Metric.SPEED_SCORE,
        display_name="Spd",
        category=Category.BASERUNNING,
        kind=ImplKind.DETERMINISTIC,
        required_columns=("sb", "cs", "h", "b2", "b3", "hr", "bb", "ab", "r"),
        optional_columns=("ibb", "hbp", "gidp"),
        requires=(Metric.B1, Metric.UBB),
        direction=Direction.HIGHER_IS_BETTER,
        formula_latex=r"Spd = \frac{f_1 + f_2 + f_3 + f_4 + f_5}{5}",
        citation="James, B. (1987) Baseball Abstract; FanGraphs Library (Spd)",
        description="Bill James's composite Speed Score (0 to 10 scale).",
    )
)
def calc_speed_score(ctx: EvalContext) -> nw.Expr:
    hbp = nw.col("hbp") if "hbp" in ctx.available_columns else nw.lit(0)
    on_base_1b = nw.col("b1") + nw.col("ubb") + hbp
    # f1: Stolen base percentage component: ((SB + 3)/(SB + CS + 7) - 0.4) * 20
    f1 = (safe_div(nw.col("sb") + 3.0, nw.col("sb") + nw.col("cs") + 7.0) - 0.4) * 20.0
    # f2: Stolen base attempt rate: ((SB + CS) / (1B + uBB + HBP)) / 0.07
    f2 = safe_div(nw.col("sb") + nw.col("cs"), on_base_1b) / 0.07
    # f3: Triples rate: (3B / (AB - HR - SO)) / 0.0016
    f3 = safe_div(nw.col("b3"), nw.col("ab") - nw.col("hr")) / 0.002
    # f4: Runs scored percentage: ((R - HR) / (H + BB + HBP - HR) - 0.1) / 0.04
    f4 = (safe_div(nw.col("r") - nw.col("hr"), nw.col("h") + nw.col("bb") + hbp - nw.col("hr")) - 0.1) / 0.04
    return (f1 + f2 + f3 + f4) / 4.0


@register_metric(
    MetricSpec(
        metric=Metric.TC,
        display_name="TC",
        category=Category.FIELDING,
        kind=ImplKind.DETERMINISTIC,
        required_columns=("po", "a", "e"),
        direction=Direction.HIGHER_IS_BETTER,
        formula_latex=r"TC = PO + A + E",
        citation="Chadwick, H.; Official MLB Rules",
        description="Total defensive chances.",
    )
)
def calc_tc(ctx: EvalContext) -> nw.Expr:
    return nw.col("po") + nw.col("a") + nw.col("e")


@register_metric(
    MetricSpec(
        metric=Metric.FPCT,
        display_name="FPCT",
        category=Category.FIELDING,
        kind=ImplKind.DETERMINISTIC,
        required_columns=("po", "a", "e"),
        requires=(Metric.TC,),
        direction=Direction.HIGHER_IS_BETTER,
        formula_latex=r"FPCT = \frac{PO + A}{PO + A + E}",
        citation="Chadwick, H.; Official MLB Rules",
        description="Fielding percentage.",
    )
)
def calc_fpct(ctx: EvalContext) -> nw.Expr:
    return safe_div(nw.col("po") + nw.col("a"), nw.col("tc"))


@register_metric(
    MetricSpec(
        metric=Metric.RF_PER_G,
        display_name="RF/G",
        category=Category.FIELDING,
        kind=ImplKind.DETERMINISTIC,
        required_columns=("po", "a", "g"),
        direction=Direction.HIGHER_IS_BETTER,
        formula_latex=r"RF/G = \frac{PO + A}{G}",
        citation="James, B. (1977) Baseball Abstract",
        description="Range factor per game played.",
    )
)
def calc_rf_per_g(ctx: EvalContext) -> nw.Expr:
    return safe_div(nw.col("po") + nw.col("a"), nw.col("g"))


@register_metric(
    MetricSpec(
        metric=Metric.RF_PER_9,
        display_name="RF/9",
        category=Category.FIELDING,
        kind=ImplKind.DETERMINISTIC,
        required_columns=("po", "a", "inn_outs_fld"),
        direction=Direction.HIGHER_IS_BETTER,
        formula_latex=r"RF/9 = \frac{27 \times (PO + A)}{DefOuts}",
        citation="James, B. (1982) Baseball Abstract",
        description="Range factor per 9 defensive innings (27 defensive outs).",
    )
)
def calc_rf_per_9(ctx: EvalContext) -> nw.Expr:
    return safe_div(27.0 * (nw.col("po") + nw.col("a")), nw.col("inn_outs_fld"))


@register_metric(
    MetricSpec(
        metric=Metric.DER,
        display_name="DER",
        category=Category.FIELDING,
        kind=ImplKind.DETERMINISTIC,
        required_columns=("h", "hr", "ab", "so"),
        optional_columns=("sf",),
        requires=(Metric.BABIP,),
        direction=Direction.HIGHER_IS_BETTER,
        formula_latex=r"DER = 1 - BABIP = 1 - \frac{H - HR}{AB - SO - HR + SF}",
        citation="James, B. (1979); Baseball Prospectus",
        description="Defensive Efficiency Ratio (rate of balls in play converted into outs).",
    )
)
def calc_der(ctx: EvalContext) -> nw.Expr:
    return 1.0 - nw.col("babip")


@register_metric(
    MetricSpec(
        metric=Metric.CATCHER_CS_PCT,
        display_name="CS%",
        category=Category.FIELDING,
        kind=ImplKind.DETERMINISTIC,
        required_columns=("cs", "sb"),
        direction=Direction.HIGHER_IS_BETTER,
        formula_latex=r"CS\% = \frac{CS}{SB + CS}",
        citation="Official MLB Rules",
        description="Catcher caught-stealing percentage.",
    )
)
def calc_catcher_cs_pct(ctx: EvalContext) -> nw.Expr:
    return safe_div(nw.col("cs"), nw.col("sb") + nw.col("cs"))


# ==============================================================================
# Team Performance & Pythagorean Estimators
# ==============================================================================


@register_metric(
    MetricSpec(
        metric=Metric.RUN_DIFF,
        display_name="RunDiff",
        category=Category.TEAM,
        kind=ImplKind.DETERMINISTIC,
        required_columns=("rs", "ra"),
        direction=Direction.HIGHER_IS_BETTER,
        formula_latex=r"RunDiff = RS - RA",
        citation="Official MLB Rules",
        description="Team run differential (runs scored minus runs allowed).",
    )
)
def calc_run_diff(ctx: EvalContext) -> nw.Expr:
    return nw.col("rs") - nw.col("ra")


@register_metric(
    MetricSpec(
        metric=Metric.WIN_PCT,
        display_name="W%",
        category=Category.TEAM,
        kind=ImplKind.DETERMINISTIC,
        required_columns=("w", "l"),
        direction=Direction.HIGHER_IS_BETTER,
        formula_latex=r"W\% = \frac{W}{W + L}",
        citation="Official MLB Rules",
        description="Actual team winning percentage.",
    )
)
def calc_win_pct(ctx: EvalContext) -> nw.Expr:
    return safe_div(nw.col("w"), nw.col("w") + nw.col("l"))


@register_metric(
    MetricSpec(
        metric=Metric.PYTHAG_WIN_PCT,
        display_name="Pythag W%",
        category=Category.TEAM,
        kind=ImplKind.CONTEXTUAL,
        required_columns=("rs", "ra"),
        direction=Direction.HIGHER_IS_BETTER,
        formula_latex=r"WinPct_{Pythag} = \frac{RS^\gamma}{RS^\gamma + RA^\gamma}",
        citation="James, B. (1980); Miller, S. J. (2007) A Derivation of the Pythagorean Won-Loss Formula in Baseball",
        description="Pythagorean expected winning percentage (default exponent gamma = 1.83).",
    )
)
def calc_pythag_win_pct(ctx: EvalContext) -> nw.Expr:
    gamma = ctx.season_context.pythag_exponent
    rs_g = nw.col("rs").cast(nw.Float64) ** gamma
    ra_g = nw.col("ra").cast(nw.Float64) ** gamma
    return safe_div(rs_g, rs_g + ra_g)


@register_metric(
    MetricSpec(
        metric=Metric.PYTHAGENPAT_WIN_PCT,
        display_name="Pythagenpat W%",
        category=Category.TEAM,
        kind=ImplKind.DETERMINISTIC,
        required_columns=("rs", "ra", "w", "l"),
        direction=Direction.HIGHER_IS_BETTER,
        formula_latex=r"\gamma = \left(\frac{RS + RA}{G}\right)^{0.287}, \quad W\% = \frac{RS^\gamma}{RS^\gamma + RA^\gamma}",
        citation="Smyth, D. & Patriot (2001) Pythagenpat Dynamic Exponent",
        description="Pythagenpat expected winning percentage with dynamic run-environment exponent.",
    )
)
def calc_pythagenpat_win_pct(ctx: EvalContext) -> nw.Expr:
    g = (nw.col("w") + nw.col("l")).cast(nw.Float64)
    rpg = safe_div(nw.col("rs") + nw.col("ra"), g)
    gamma = rpg ** 0.287
    rs_g = nw.col("rs").cast(nw.Float64) ** gamma
    ra_g = nw.col("ra").cast(nw.Float64) ** gamma
    return safe_div(rs_g, rs_g + ra_g)


@register_metric(
    MetricSpec(
        metric=Metric.PYTHAG_WINS,
        display_name="Pythag W",
        category=Category.TEAM,
        kind=ImplKind.CONTEXTUAL,
        required_columns=("rs", "ra", "w", "l"),
        requires=(Metric.PYTHAG_WIN_PCT,),
        direction=Direction.HIGHER_IS_BETTER,
        formula_latex=r"W_{Pythag} = (W + L) \times WinPct_{Pythag}",
        citation="James, B. (1980)",
        description="Expected wins from Pythagorean winning percentage.",
    )
)
def calc_pythag_wins(ctx: EvalContext) -> nw.Expr:
    return (nw.col("w") + nw.col("l")).cast(nw.Float64) * nw.col("pythag_win_pct")


@register_metric(
    MetricSpec(
        metric=Metric.PYTHAG_LUCK,
        display_name="Pythag Luck",
        category=Category.TEAM,
        kind=ImplKind.CONTEXTUAL,
        required_columns=("rs", "ra", "w", "l"),
        requires=(Metric.PYTHAG_WINS,),
        direction=Direction.NEUTRAL,
        formula_latex=r"Luck_{Pythag} = W - W_{Pythag}",
        citation="James, B. (1980); Baseball-Reference Glossary",
        description="Actual wins minus Pythagorean expected wins (cluster/sequencing luck).",
    )
)
def calc_pythag_luck(ctx: EvalContext) -> nw.Expr:
    return nw.col("w").cast(nw.Float64) - nw.col("pythag_wins")


# ==============================================================================
# Statcast Expected Offense (xBA, xSLG, xwOBA)
# ==============================================================================


@register_metric(
    MetricSpec(
        metric=Metric.XBA,
        display_name="xBA",
        category=Category.STATCAST_EXPECTED,
        kind=ImplKind.DETERMINISTIC,
        required_columns=("xba_sum", "ab"),
        direction=Direction.HIGHER_IS_BETTER,
        formula_latex=r"xBA = \frac{\sum P(Hit \mid EV, LA)}{AB}",
        citation="MLB Statcast / Baseball Savant Glossary (Expected Batting Average)",
        description="Expected batting average based on exit velocity, launch angle, and sprint speed.",
    )
)
def calc_xba(ctx: EvalContext) -> nw.Expr:
    return safe_div(nw.col("xba_sum"), nw.col("ab"))


@register_metric(
    MetricSpec(
        metric=Metric.XSLG,
        display_name="xSLG",
        category=Category.STATCAST_EXPECTED,
        kind=ImplKind.DETERMINISTIC,
        required_columns=("xslg_sum", "ab"),
        direction=Direction.HIGHER_IS_BETTER,
        formula_latex=r"xSLG = \frac{\sum E[TB \mid EV, LA]}{AB}",
        citation="MLB Statcast / Baseball Savant Glossary (Expected Slugging)",
        description="Expected slugging percentage based on exit velocity and launch angle.",
    )
)
def calc_xslg(ctx: EvalContext) -> nw.Expr:
    return safe_div(nw.col("xslg_sum"), nw.col("ab"))


@register_metric(
    MetricSpec(
        metric=Metric.XWOBA,
        display_name="xwOBA",
        category=Category.STATCAST_EXPECTED,
        kind=ImplKind.DETERMINISTIC,
        required_columns=("xwoba_sum", "xwoba_count"),
        direction=Direction.HIGHER_IS_BETTER,
        formula_latex=r"xwOBA = \frac{\sum xwOBA_{PA}}{N_{xwOBA}}",
        citation="MLB Statcast / Baseball Savant Glossary (Expected Weighted On-Base Average)",
        description="Expected wOBA combining batted-ball EV/LA probabilities with actual K, uBB, and HBP outcomes.",
    )
)
def calc_xwoba(ctx: EvalContext) -> nw.Expr:
    return safe_div(nw.col("xwoba_sum"), nw.col("xwoba_count"))


@register_metric(
    MetricSpec(
        metric=Metric.BA_MINUS_XBA,
        display_name="BA-xBA",
        category=Category.STATCAST_EXPECTED,
        kind=ImplKind.DETERMINISTIC,
        required_columns=("h", "ab", "xba_sum"),
        requires=(Metric.AVG, Metric.XBA),
        direction=Direction.NEUTRAL,
        formula_latex=r"BA - xBA = AVG - xBA",
        citation="MLB Statcast / Baseball Savant Glossary",
        description="Difference between actual batting average and expected batting average.",
    )
)
def calc_ba_minus_xba(ctx: EvalContext) -> nw.Expr:
    return nw.col("avg") - nw.col("xba")


@register_metric(
    MetricSpec(
        metric=Metric.WOBA_MINUS_XWOBA,
        display_name="wOBA-xwOBA",
        category=Category.STATCAST_EXPECTED,
        kind=ImplKind.CONTEXTUAL,
        required_columns=("ab", "bb", "h", "b2", "b3", "hr", "xwoba_sum", "xwoba_count"),
        optional_columns=("ibb", "hbp", "sf"),
        requires=(Metric.WOBA, Metric.XWOBA),
        direction=Direction.NEUTRAL,
        formula_latex=r"wOBA - xwOBA",
        citation="MLB Statcast / FanGraphs Library",
        description="Difference between actual wOBA and Statcast expected wOBA.",
    )
)
def calc_woba_minus_xwoba(ctx: EvalContext) -> nw.Expr:
    return nw.col("woba") - nw.col("xwoba")


# ==============================================================================
# Pitch Kinematics & Physics (Velo, Spin, Extension, IVB, HB, VAA)
# ==============================================================================


@register_metric(
    MetricSpec(
        metric=Metric.AVG_VELO,
        display_name="Avg Velo",
        category=Category.PITCH_PHYSICS,
        kind=ImplKind.DETERMINISTIC,
        required_columns=("velo_sum", "velo_count"),
        direction=Direction.HIGHER_IS_BETTER,
        formula_latex=r"\overline{v_0} = \frac{\sum v_0}{N_{v_0}}",
        citation="MLB Statcast / TrackMan Pitch Tracking Glossary",
        description="Mean pitch release velocity in mph.",
    )
)
def calc_avg_velo(ctx: EvalContext) -> nw.Expr:
    return safe_div(nw.col("velo_sum"), nw.col("velo_count"))


@register_metric(
    MetricSpec(
        metric=Metric.AVG_SPIN,
        display_name="Avg Spin",
        category=Category.PITCH_PHYSICS,
        kind=ImplKind.DETERMINISTIC,
        required_columns=("spin_sum", "spin_count"),
        direction=Direction.HIGHER_IS_BETTER,
        formula_latex=r"\overline{\omega} = \frac{\sum \omega}{N_{\omega}}",
        citation="MLB Statcast / TrackMan Pitch Tracking Glossary",
        description="Mean pitch release spin rate in RPM.",
    )
)
def calc_avg_spin(ctx: EvalContext) -> nw.Expr:
    return safe_div(nw.col("spin_sum"), nw.col("spin_count"))


@register_metric(
    MetricSpec(
        metric=Metric.AVG_EXTENSION,
        display_name="Extension",
        category=Category.PITCH_PHYSICS,
        kind=ImplKind.DETERMINISTIC,
        required_columns=("ext_sum", "ext_count"),
        direction=Direction.HIGHER_IS_BETTER,
        formula_latex=r"\overline{Ext} = \frac{\sum Ext}{N_{Ext}}",
        citation="MLB Statcast Glossary (Release Extension)",
        description="Mean pitcher release extension toward home plate in feet.",
    )
)
def calc_avg_extension(ctx: EvalContext) -> nw.Expr:
    return safe_div(nw.col("ext_sum"), nw.col("ext_count"))


@register_metric(
    MetricSpec(
        metric=Metric.IVB,
        display_name="IVB",
        category=Category.PITCH_PHYSICS,
        kind=ImplKind.DETERMINISTIC,
        required_columns=("ivb_sum", "break_count"),
        direction=Direction.HIGHER_IS_BETTER,
        formula_latex=r"IVB = \frac{\sum (12 \times pfx_z)}{N_{break}}",
        citation="Nathan, A. M. (2008) The Effect of Spin on the Flight of a Baseball; Baseball Savant",
        description="Mean Induced Vertical Break (gravity-removed vertical movement) in inches.",
    )
)
def calc_ivb(ctx: EvalContext) -> nw.Expr:
    return safe_div(nw.col("ivb_sum"), nw.col("break_count"))


@register_metric(
    MetricSpec(
        metric=Metric.HB,
        display_name="HB",
        category=Category.PITCH_PHYSICS,
        kind=ImplKind.DETERMINISTIC,
        required_columns=("hb_sum", "break_count"),
        direction=Direction.NEUTRAL,
        formula_latex=r"HB = \frac{\sum (12 \times pfx_x)}{N_{break}}",
        citation="Nathan, A. M. (2008); Baseball Savant",
        description="Mean Horizontal Break in inches.",
    )
)
def calc_hb(ctx: EvalContext) -> nw.Expr:
    return safe_div(nw.col("hb_sum"), nw.col("break_count"))


@register_metric(
    MetricSpec(
        metric=Metric.TOTAL_BREAK,
        display_name="Total Break",
        category=Category.PITCH_PHYSICS,
        kind=ImplKind.DETERMINISTIC,
        required_columns=("ivb_sum", "hb_sum", "break_count"),
        requires=(Metric.IVB, Metric.HB),
        direction=Direction.HIGHER_IS_BETTER,
        formula_latex=r"Break_{total} = \sqrt{IVB^2 + HB^2}",
        citation="Nathan, A. M. (2008); PitchingBot / Stuff+ Literature",
        description="Euclidean magnitude of mean Induced Vertical Break and Horizontal Break in inches.",
    )
)
def calc_total_break(ctx: EvalContext) -> nw.Expr:
    return (nw.col("ivb") ** 2.0 + nw.col("hb") ** 2.0) ** 0.5


@register_metric(
    MetricSpec(
        metric=Metric.EFFECTIVE_VELO,
        display_name="Eff Velo",
        category=Category.PITCH_PHYSICS,
        kind=ImplKind.DETERMINISTIC,
        required_columns=("eff_velo_sum", "eff_velo_count"),
        direction=Direction.HIGHER_IS_BETTER,
        formula_latex=r"\overline{v_{eff}} = \frac{\sum v_{eff}}{N_{v_{eff}}}",
        citation="MLB Statcast Glossary (Perceived / Effective Velocity)",
        description="Mean perceived velocity adjusted for release extension and drag in mph.",
    )
)
def calc_effective_velo(ctx: EvalContext) -> nw.Expr:
    return safe_div(nw.col("eff_velo_sum"), nw.col("eff_velo_count"))


@register_metric(
    MetricSpec(
        metric=Metric.VAA,
        display_name="VAA",
        category=Category.PITCH_PHYSICS,
        kind=ImplKind.DETERMINISTIC,
        required_columns=("vaa_sum", "vaa_count"),
        direction=Direction.HIGHER_IS_BETTER,
        formula_latex=r"VAA = -\arctan\left(\frac{v_{zf}}{-v_{yf}}\right) \times \frac{180}{\pi}",
        citation="Nathan, A. M. (2012) & Chamberlain, A. (2020) FanGraphs Vertical Approach Angle",
        description="Mean Vertical Approach Angle (degrees) of the pitch as it crosses the front of home plate (y = 1.417 ft).",
    )
)
def calc_vaa(ctx: EvalContext) -> nw.Expr:
    return safe_div(nw.col("vaa_sum"), nw.col("vaa_count"))


@register_metric(
    MetricSpec(
        metric=Metric.HAA,
        display_name="HAA",
        category=Category.PITCH_PHYSICS,
        kind=ImplKind.DETERMINISTIC,
        required_columns=("haa_sum", "haa_count"),
        direction=Direction.NEUTRAL,
        formula_latex=r"HAA = \arctan\left(\frac{v_{xf}}{-v_{yf}}\right) \times \frac{180}{\pi}",
        citation="Nathan, A. M. (2012); Chamberlain, A. (2022) Horizontal Approach Angle",
        description="Mean Horizontal Approach Angle (degrees) of the pitch as it crosses the front of home plate.",
    )
)
def calc_haa(ctx: EvalContext) -> nw.Expr:
    return safe_div(nw.col("haa_sum"), nw.col("haa_count"))


@register_metric(
    MetricSpec(
        metric=Metric.BAUER_UNITS,
        display_name="Bauer Units",
        category=Category.PITCH_PHYSICS,
        kind=ImplKind.DETERMINISTIC,
        required_columns=("spin_sum", "spin_count", "velo_sum", "velo_count"),
        requires=(Metric.AVG_SPIN, Metric.AVG_VELO),
        direction=Direction.HIGHER_IS_BETTER,
        formula_latex=r"\text{Bauer Units} = \frac{\overline{\omega}}{\overline{v_0}}",
        citation="Boddy, K. & Driveline Baseball (2015) Spin Rate per MPH",
        description="Spin rate in RPM divided by release velocity in mph (velocity-normalized spin).",
    )
)
def calc_bauer_units(ctx: EvalContext) -> nw.Expr:
    return safe_div(nw.col("avg_spin"), nw.col("avg_velo"))


@register_metric(
    MetricSpec(
        metric=Metric.RV_PER_100,
        display_name="RV/100",
        category=Category.PITCH_PHYSICS,
        kind=ImplKind.DETERMINISTIC,
        required_columns=("pitch_rv_sum", "pitches"),
        direction=Direction.HIGHER_IS_BETTER,
        formula_latex=r"RV/100 = 100 \times \frac{\sum \Delta RE_{pitch}}{Pitches}",
        citation="Baseball Savant / FanGraphs Pitch Value Glossary",
        description="Pitch run value per 100 pitches thrown.",
    )
)
def calc_rv_per_100(ctx: EvalContext) -> nw.Expr:
    return safe_div(100.0 * nw.col("pitch_rv_sum"), nw.col("pitches"))


@register_metric(
    MetricSpec(
        metric=Metric.WHIFF_PER_100,
        display_name="Whiffs/100",
        category=Category.PITCH_PHYSICS,
        kind=ImplKind.DETERMINISTIC,
        required_columns=("whiffs", "pitches"),
        direction=Direction.HIGHER_IS_BETTER,
        formula_latex=r"Whiffs/100 = 100 \times \frac{Whiffs}{Pitches}",
        citation="Baseball Savant Glossary",
        description="Swinging strikes generated per 100 pitches thrown.",
    )
)
def calc_whiff_per_100(ctx: EvalContext) -> nw.Expr:
    return safe_div(100.0 * nw.col("whiffs"), nw.col("pitches"))


@register_metric(
    MetricSpec(
        metric=Metric.BIP_PCT,
        display_name="BIP%",
        category=Category.PLATE_DISCIPLINE,
        kind=ImplKind.DETERMINISTIC,
        required_columns=("bbe", "swings"),
        direction=Direction.NEUTRAL,
        formula_latex=r"BIP\% = \frac{BBE}{Swings}",
        citation="Baseball Savant Glossary",
        description="Percentage of swings put into fair play.",
    )
)
def calc_bip_pct(ctx: EvalContext) -> nw.Expr:
    return safe_div(nw.col("bbe"), nw.col("swings"))


@register_metric(
    MetricSpec(
        metric=Metric.PUTAWAY_PCT,
        display_name="PutAway%",
        category=Category.PLATE_DISCIPLINE,
        kind=ImplKind.DETERMINISTIC,
        required_columns=("two_strike_so", "two_strike_pitches"),
        direction=Direction.HIGHER_IS_BETTER,
        formula_latex=r"PutAway\% = \frac{SO_{2K}}{Pitches_{2K}}",
        citation="MLB Statcast / Baseball Savant Glossary (PutAway%)",
        description="Rate of two-strike pitches that result in a strikeout.",
    )
)
def calc_putaway_pct(ctx: EvalContext) -> nw.Expr:
    return safe_div(nw.col("two_strike_so"), nw.col("two_strike_pitches"))


@register_metric(
    MetricSpec(
        metric=Metric.TWO_STRIKE_CHASE_PCT,
        display_name="2K Chase%",
        category=Category.PLATE_DISCIPLINE,
        kind=ImplKind.DETERMINISTIC,
        required_columns=("two_strike_out_zone_swings", "two_strike_out_zone_pitches"),
        direction=Direction.LOWER_IS_BETTER,
        formula_latex=r"2K\text{-}Chase\% = \frac{OutZoneSwings_{2K}}{OutZonePitches_{2K}}",
        citation="Baseball Savant Glossary",
        description="Chase rate on pitches outside the strike zone with two strikes.",
    )
)
def calc_two_strike_chase_pct(ctx: EvalContext) -> nw.Expr:
    return safe_div(nw.col("two_strike_out_zone_swings"), nw.col("two_strike_out_zone_pitches"))


@register_metric(
    MetricSpec(
        metric=Metric.MEATBALL_SWING_PCT,
        display_name="Meatball Swing%",
        category=Category.PLATE_DISCIPLINE,
        kind=ImplKind.DETERMINISTIC,
        required_columns=("meatball_swings", "meatball_pitches"),
        direction=Direction.HIGHER_IS_BETTER,
        formula_latex=r"MeatballSwing\% = \frac{MeatballSwings}{MeatballPitches}",
        citation="MLB Statcast Attack Zone Glossary",
        description="Swing percentage on pitches in the heart/meatball attack zone.",
    )
)
def calc_meatball_swing_pct(ctx: EvalContext) -> nw.Expr:
    return safe_div(nw.col("meatball_swings"), nw.col("meatball_pitches"))


@register_metric(
    MetricSpec(
        metric=Metric.ERR_PCT,
        display_name="Err%",
        category=Category.FIELDING,
        kind=ImplKind.DETERMINISTIC,
        required_columns=("po", "a", "e"),
        requires=(Metric.TC,),
        direction=Direction.LOWER_IS_BETTER,
        formula_latex=r"Err\% = \frac{E}{PO + A + E} = 1 - FPCT",
        citation="Official MLB Rules",
        description="Defensive error rate per total chance.",
    )
)
def calc_err_pct(ctx: EvalContext) -> nw.Expr:
    return safe_div(nw.col("e"), nw.col("tc"))


@register_metric(
    MetricSpec(
        metric=Metric.XBT_PCT,
        display_name="XBT%",
        category=Category.BASERUNNING,
        kind=ImplKind.DETERMINISTIC,
        required_columns=("xbt", "xbt_opp"),
        direction=Direction.HIGHER_IS_BETTER,
        formula_latex=r"XBT\% = \frac{XBT}{XBTOpp}",
        citation="Baseball-Reference Baserunning Glossary (Extra Base Taken %)",
        description="Percentage of times a baserunner advances more than one base on a single or more than two bases on a double.",
    )
)
def calc_xbt_pct(ctx: EvalContext) -> nw.Expr:
    return safe_div(nw.col("xbt"), nw.col("xbt_opp"))


@register_metric(
    MetricSpec(
        metric=Metric.WGDP,
        display_name="wGDP",
        category=Category.BASERUNNING,
        kind=ImplKind.CONTEXTUAL,
        required_columns=("gidp", "gidp_opp"),
        direction=Direction.HIGHER_IS_BETTER,
        formula_latex=r"wGDP = (GIDPOpp \times lgGIDPRate - GIDP) \times r_{GIDP}",
        citation="FanGraphs Library (wGDP)",
        description="Weighted Double Play Runs above average.",
    )
)
def calc_wgdp(ctx: EvalContext) -> nw.Expr:
    w = ctx.weights
    return (nw.col("gidp_opp") * w.lg_gidp_rate - nw.col("gidp")) * w.r_gidp


@register_metric(
    MetricSpec(
        metric=Metric.BSR,
        display_name="BsR",
        category=Category.BASERUNNING,
        kind=ImplKind.CONTEXTUAL,
        required_columns=("sb", "cs", "h", "b2", "b3", "hr", "bb"),
        optional_columns=("ibb", "hbp", "gidp", "gidp_opp", "ubr"),
        requires=(Metric.WSB,),
        direction=Direction.HIGHER_IS_BETTER,
        formula_latex=r"BsR = wSB + wGDP + UBR",
        citation="FanGraphs Library (BsR - Base Running Runs)",
        description="Total Baserunning Runs above average combining wSB, wGDP, and UBR.",
    )
)
def calc_bsr(ctx: EvalContext) -> nw.Expr:
    w = ctx.weights
    ubr = nw.col("ubr") if "ubr" in ctx.available_columns else nw.lit(0.0)
    if "gidp" in ctx.available_columns and "gidp_opp" in ctx.available_columns:
        wgdp = (nw.col("gidp_opp") * w.lg_gidp_rate - nw.col("gidp")) * w.r_gidp
    else:
        wgdp = nw.lit(0.0)
    return nw.col("wsb") + wgdp + ubr


@register_metric(
    MetricSpec(
        metric=Metric.PLI,
        display_name="pLI",
        category=Category.EXPECTANCY,
        kind=ImplKind.DETERMINISTIC,
        required_columns=("li_sum", "pa"),
        direction=Direction.NEUTRAL,
        formula_latex=r"pLI = \frac{\sum LI_i}{PA}",
        citation="Tango, T. (2006) Crucial Situations & Leverage Index; FanGraphs Library",
        description="Average Leverage Index faced per plate appearance.",
    )
)
def calc_pli(ctx: EvalContext) -> nw.Expr:
    return safe_div(nw.col("li_sum"), nw.col("pa"))


@register_metric(
    MetricSpec(
        metric=Metric.WPA_LI,
        display_name="WPA/LI",
        category=Category.EXPECTANCY,
        kind=ImplKind.DETERMINISTIC,
        required_columns=("wpa_li_sum",),
        direction=Direction.HIGHER_IS_BETTER,
        formula_latex=r"WPA/LI = \sum \frac{WPA_i}{LI_i}",
        citation="Tango, T. (2006); FanGraphs Library (Context-Neutral Wins)",
        description="Context-neutral Win Probability Added summed across plate appearances.",
    )
)
def calc_wpa_li(ctx: EvalContext) -> nw.Expr:
    return nw.col("wpa_li_sum").cast(nw.Float64)


@register_metric(
    MetricSpec(
        metric=Metric.CLUTCH,
        display_name="Clutch",
        category=Category.EXPECTANCY,
        kind=ImplKind.DETERMINISTIC,
        required_columns=("wpa", "li_sum", "pa", "wpa_li_sum"),
        requires=(Metric.PLI, Metric.WPA_LI),
        direction=Direction.HIGHER_IS_BETTER,
        formula_latex=r"Clutch = \frac{WPA}{pLI} - WPA/LI",
        citation="Tango, T. (2006); Cramer, D. (1977) Do Clutch Hitters Exist?; FanGraphs Library",
        description="Tom Tango's Clutch score measuring performance in high-leverage situations relative to context-neutral performance.",
    )
)
def calc_clutch(ctx: EvalContext) -> nw.Expr:
    return safe_div(nw.col("wpa"), nw.col("pli")) - nw.col("wpa_li")


@register_metric(
    MetricSpec(
        metric=Metric.REW,
        display_name="REW",
        category=Category.EXPECTANCY,
        kind=ImplKind.CONTEXTUAL,
        required_columns=("re24",),
        direction=Direction.HIGHER_IS_BETTER,
        formula_latex=r"REW = \frac{RE24}{RPW}",
        citation="Tango, T. (2007); FanGraphs Library (Run Expectancy Wins)",
        description="Run Expectancy Wins above average (RE24 divided by seasonal Runs Per Win).",
    )
)
def calc_rew(ctx: EvalContext) -> nw.Expr:
    return safe_div(nw.col("re24"), ctx.weights.lg_r_per_w)


