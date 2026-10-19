"""Hand-derived value assertions for every registered metric, plus a guard that none is missing.

Each expected value is written as the arithmetic derivation of the metric's documented formula
(small integer inputs, so the arithmetic can be checked by eye) and does not call library code.
Whether a documented formula equals the *published* method is tracked separately by each metric's
reference status (docs/METHODOLOGY.md); published-value checks live in tests/test_golden_values.py.
"""

from __future__ import annotations

import math
from typing import Any

import polars as pl
import pytest
from test_golden_values import BATTING_METRICS, PITCHING_METRICS

import sabermetricspy as sp
from sabermetricspy import Metric
from sabermetricspy.constants import get_woba_weights
from sabermetricspy.registry import REGISTRY
from sabermetricspy.types.context import SeasonContext

W = get_woba_weights(2024)
assert W.lg_era is not None and W.lg_fip is not None and W.lg_xfip is not None
assert W.lg_hr_per_fb is not None

# --- shared hand-countable batting line -------------------------------------------------------
# h=30, 2B=6, 3B=1, HR=4 -> 1B=19; TB = 19 + 12 + 3 + 16 = 50; BB=12 (IBB=2 -> uBB=10); AB=100
BAT = dict(h=30, b2=6, b3=1, hr=4, bb=12, ab=100)
TB = 19 + 2 * 6 + 3 * 1 + 4 * 4
OBP = (30 + 12 + 1) / (100 + 12 + 1 + 1)  # hbp=1, sf=1
SLG = TB / 100

# --- pitching lines -----------------------------------------------------------------------------
# 60 IP = 180 outs; hr=5, bb=15, so=60, hbp=2
FIP_60 = (13 * 5 + 3 * (15 + 2) - 2 * 60) / 60 + W.c_fip
XFIP_NUM = 13 * 60 * W.lg_hr_per_fb + 3 * (15 + 2) - 2 * 50  # fb=60, so=50, outs=54 (18 IP)
XFIP_18 = XFIP_NUM / 18 + W.c_fip

# SIERA: so=90, bb=30, gb=150, fb=100, pu=20, bf=400 -> netGB = 30/400 > 0 so the squared term is negative
_so, _bb, _ngb = 90 / 400, 30 / 400, (150 - 100 - 20) / 400
SIERA = (
    6.145
    - 16.986 * _so
    + 11.434 * _bb
    - 1.858 * _ngb
    + 7.653 * _so**2
    - 6.664 * _ngb**2
    + 10.130 * _so * _ngb
    - 5.195 * _bb * _ngb
)

# Pythagorean: 800 RS, 700 RA, 90-72
_PY = 800**1.83 / (800**1.83 + 700**1.83)
_GAMMA = (1500 / 162) ** 0.287
_PYPAT = 800**_GAMMA / (800**_GAMMA + 700**_GAMMA)

_W_BB, _W_HBP = W.w_bb, W.w_hbp
WOBA_LINE = (_W_BB * 8 + _W_HBP * 1 + W.w_1b * 19 + W.w_2b * 6 + W.w_3b * 1 + W.w_hr * 4) / (
    100 + 8 + 1 + 1
)  # ibb=2 -> uBB=8 with bb=10 below

RC_TECH = (
    (30 + 12 + 1 - 1 - 2) * (TB + 0.26 * (10 + 1) + 0.52 * (1 + 1 + 3)) / (100 + 12 + 1 + 1 + 1)
)
_BR_B = 1.1 * (1.4 * TB - 0.6 * 30 - 3 * 4 + 0.1 * (12 + 1 - 2) + 0.9 * (3 - 1 - 2))
BASE_RUNS = (30 + 12 + 1 - 4 - 0.5 * 2) * _BR_B / (_BR_B + (100 - 30 + 1 + 2)) + 4

WSB_1B = 100 - 20 - 2 - 15  # singles in the speed/wSB line: h=100,b2=20,b3=2,hr=15
SPEED = (
    (  # Bill James four-factor Speed Score; 1B=100, BB=60, HBP=4, SO=100, each factor within 0-10
        ((10 + 3) / (10 + 2 + 7) - 0.4) * 20  # f1: stolen-base percentage
        + math.sqrt((10 + 2) / (100 + 60 + 4)) / 0.07  # f2: attempt rate
        + (5 / (500 - 20 - 100)) / 0.0016  # f3: triples rate
        + 25 * ((90 - 20) / (150 + 60 + 4 - 20) - 0.1)  # f4: runs scored
    )
    / 4.0
)

# (metric, inputs, expected, SeasonContext kwargs)
CASES: list[tuple[Metric, dict[str, Any], float, dict[str, Any]]] = [
    # ---- batting ----
    (Metric.B1, dict(h=10, b2=2, b3=1, hr=3), 4, {}),
    (Metric.XBH, dict(b2=2, b3=1, hr=3), 6, {}),
    (Metric.TB, dict(h=10, b2=2, b3=1, hr=3), 4 + 2 * 2 + 3 * 1 + 4 * 3, {}),
    (Metric.UBB, dict(bb=10, ibb=3), 7, {}),
    (Metric.SECA, dict(**BAT, sb=5, cs=2), (12 + (TB - 30) + (5 - 2)) / 100, {}),
    (Metric.XBH_PCT, dict(b2=6, b3=1, hr=4, pa=110), 11 / 110, {}),
    (Metric.HR_PCT, dict(hr=4, pa=110), 4 / 110, {}),
    (Metric.K_MINUS_BB_PCT, dict(so=25, bb=12, pa=110), 25 / 110 - 12 / 110, {}),
    (Metric.BB_TO_K, dict(bb=12, so=25), 12 / 25, {}),
    (Metric.K_TO_BB, dict(so=25, bb=12), 25 / 12, {}),
    (Metric.R_PER_PA, dict(r=20, pa=110), 20 / 110, {}),
    (Metric.RBI_PER_PA, dict(rbi=22, pa=110), 22 / 110, {}),
    (Metric.BAT_K_PCT_PLUS, dict(so=25, pa=110), 100 * (25 / 110) / W.lg_k_pct, {}),
    (Metric.BAT_BB_PCT_PLUS, dict(bb=12, pa=110), 100 * (12 / 110) / W.lg_bb_pct, {}),
    # ---- pitching ----
    (Metric.IP, dict(outs=20), 20 / 3, {}),
    (Metric.RA9, dict(ra=5, outs=54), 27 * 5 / 54, {}),
    (Metric.H_PER_9, dict(h=8, outs=54), 27 * 8 / 54, {}),
    (Metric.PIT_K_MINUS_BB_PCT, dict(so=9, bb=3, bf=27), (9 - 3) / 27, {}),
    (Metric.QS_PCT, dict(qs=15, gs=20), 0.75, {}),
    (Metric.CG_PCT, dict(cg=2, gs=20), 0.1, {}),
    (Metric.SV_PCT, dict(sv=30, bs=5), 30 / 35, {}),
    (Metric.XFIP, dict(fb=60, bb=15, so=50, outs=54, hbp=2), XFIP_18, {}),
    (
        Metric.DICE,
        dict(hr=2, bb=3, so=9, outs=54, hbp=1),
        3.0 + (13 * 2 + 3 * (3 + 1) - 2 * 9) / 18,
        {},
    ),
    (Metric.KWERA, dict(so=9, bb=3, bf=27), (4.07894181840083 + 1.887) - 12 * (9 - 3) / 27, {}),
    (Metric.SIERA, dict(so=90, bb=30, gb=150, fb=100, bf=400, pu=20), SIERA, {}),
    (
        Metric.ERA_PLUS,
        dict(er=10, outs=180),
        100 * W.lg_era * 1.10 / (9 * 10 / 60),
        dict(park_factor=110.0),
    ),
    (
        Metric.ERA_MINUS,
        dict(er=10, outs=180),
        100 * (9 * 10 / 60) * (2 - 1.10) / W.lg_era,
        dict(park_factor=110.0),
    ),
    (
        Metric.FIP_MINUS,
        dict(hr=5, bb=15, so=60, outs=180, hbp=2),
        100 * FIP_60 / (W.lg_fip * 1.05),
        dict(park_factor=105.0),
    ),
    (
        Metric.XFIP_MINUS,
        dict(fb=60, bb=15, so=50, outs=54, hbp=2),
        100 * XFIP_18 / (W.lg_xfip * 1.05),
        dict(park_factor=105.0),
    ),
    (Metric.PIT_BB_TO_K, dict(bb=3, so=9), 3 / 9, {}),
    (Metric.BASE_ADVANCE_AVERAGE, dict(bases_advanced=14, base_advance_opps=57), 14 / 57, {}),
    (
        Metric.GAME_SCORE,
        dict(outs=21, so=8, h=5, er=2, r=2, bb=2),
        50 + 21 + 2 * 3 + 8 - 10 - 8 - 0 - 2,
        {},
    ),
    (
        Metric.GAME_SCORE_V2,
        dict(outs=21, so=8, bb=2, h=5, hr=1, r=2),
        40 + 42 + 8 - 4 - 10 - 6 - 6,
        {},
    ),
    (Metric.SHUTDOWN, dict(game_wpa=0.06, is_reliever=True), 1, {}),
    (Metric.MELTDOWN, dict(game_wpa=-0.06, is_reliever=True), 1, {}),
    (Metric.PIT_K_TO_BB, dict(so=9, bb=3), 9 / 3, {}),
    (Metric.BF_PER_IP, dict(bf=27, outs=18), 3 * 27 / 18, {}),
    (Metric.K_PCT_PLUS, dict(so=9, bf=27), 100 * (9 / 27) / W.lg_k_pct, {}),
    (Metric.BB_PCT_PLUS, dict(bb=3, bf=27), 100 * (3 / 27) / W.lg_bb_pct, {}),
    (
        Metric.QERA,
        dict(so=60, bb=15, gb=120, bbe=200, bf=300),
        (2.69 - 0.66 * 120 / 200 + 3.88 * 15 / 300 - 3.40 * 60 / 300) ** 2,
        {},
    ),
    (Metric.DIPS_BOP_PCT, dict(hr=5, bb=15, so=60, bf=300, hbp=2), (5 + 15 + 2 + 60) / 300, {}),
    (
        Metric.XERA,
        dict(xwoba_sum=32.0, xwoba_count=100, bf=300, outs=180),
        W.lg_era + (0.32 - W.lg_woba) / W.woba_scale * 9 * (3 * 300 / 180),
        {},
    ),
    # ---- plate discipline ----
    (Metric.SWING_PCT, dict(swings=50, pitches=100), 0.5, {}),
    (Metric.Z_SWING_PCT, dict(zone_swings=30, zone_pitches=40), 0.75, {}),
    (Metric.O_SWING_PCT, dict(out_zone_swings=20, out_zone_pitches=60), 20 / 60, {}),
    (Metric.ZONE_PCT, dict(zone_pitches=40, pitches=100), 0.4, {}),
    (Metric.CONTACT_PCT, dict(contacts=40, swings=50), 0.8, {}),
    (Metric.Z_CONTACT_PCT, dict(zone_contacts=27, zone_swings=30), 0.9, {}),
    (Metric.O_CONTACT_PCT, dict(out_zone_contacts=10, out_zone_swings=20), 0.5, {}),
    (Metric.WHIFF_PCT, dict(whiffs=10, swings=50), 0.2, {}),
    (Metric.SWSTR_PCT, dict(whiffs=10, pitches=100), 0.1, {}),
    (Metric.CSTR_PCT, dict(called_strikes=15, pitches=100), 0.15, {}),
    (Metric.CSW_PCT, dict(called_strikes=15, whiffs=10, pitches=100), 0.25, {}),
    (Metric.FOUL_PCT, dict(fouls=15, swings=50), 0.3, {}),
    (Metric.FP_SWING_PCT, dict(first_pitch_swings=12, pa=40), 0.3, {}),
    (Metric.FP_STRIKE_PCT, dict(first_pitch_strikes=24, pa=40), 0.6, {}),
    (Metric.BIP_PCT, dict(bbe=70, swings=200), 0.35, {}),
    (Metric.PUTAWAY_PCT, dict(two_strike_so=15, two_strike_pitches=100), 0.15, {}),
    (
        Metric.TWO_STRIKE_CHASE_PCT,
        dict(two_strike_out_zone_swings=10, two_strike_out_zone_pitches=50),
        0.2,
        {},
    ),
    (Metric.MEATBALL_SWING_PCT, dict(meatball_swings=30, meatball_pitches=40), 0.75, {}),
    # ---- batted ball ----
    (Metric.GB_PCT, dict(gb=40, bbe=100), 0.4, {}),
    (Metric.FB_PCT, dict(fb=30, bbe=100), 0.3, {}),
    (Metric.LD_PCT, dict(ld=22, bbe=100), 0.22, {}),
    (Metric.PU_PCT, dict(pu=8, bbe=100), 0.08, {}),
    (Metric.GB_TO_FB, dict(gb=40, fb=30), 4 / 3, {}),
    (Metric.HR_TO_FB, dict(hr=6, fb=30), 0.2, {}),
    (Metric.PULL_PCT, dict(pull_bbe=38, cent_bbe=35, oppo_bbe=27), 0.38, {}),
    (Metric.CENT_PCT, dict(pull_bbe=38, cent_bbe=35, oppo_bbe=27), 0.35, {}),
    (Metric.OPPO_PCT, dict(pull_bbe=38, cent_bbe=35, oppo_bbe=27), 0.27, {}),
    (Metric.HARD_HIT_PCT, dict(hard_hit_bbe=42, bbe=100), 0.42, {}),
    (Metric.SWEET_SPOT_PCT, dict(sweet_spot_bbe=34, bbe=100), 0.34, {}),
    (Metric.BARREL_PCT, dict(barrels=9, bbe=100), 0.09, {}),
    (Metric.AVG_EV, dict(ev_sum=900.0, ev_count=10), 90.0, {}),
    # ---- pitch physics ----
    (Metric.AVG_VELO, dict(velo_sum=1860.0, velo_count=20), 93.0, {}),
    (Metric.AVG_SPIN, dict(spin_sum=45000.0, spin_count=20), 2250.0, {}),
    (Metric.AVG_EXTENSION, dict(ext_sum=130.0, ext_count=20), 6.5, {}),
    (Metric.IVB, dict(ivb_sum=300.0, break_count=20), 15.0, {}),
    (Metric.HB, dict(hb_sum=-100.0, break_count=20), -5.0, {}),
    (
        Metric.TOTAL_BREAK,
        dict(total_break_sum=400.0, break_count=20),
        20.0,
        {},
    ),
    (Metric.EFFECTIVE_VELO, dict(eff_velo_sum=1900.0, eff_velo_count=20), 95.0, {}),
    (Metric.VAA, dict(vaa_sum=-100.0, vaa_count=20), -5.0, {}),
    (Metric.HAA, dict(haa_sum=20.0, haa_count=20), 1.0, {}),
    (
        Metric.BAUER_UNITS,
        dict(spin_sum=45000.0, spin_count=20, velo_sum=1860.0, velo_count=20),
        2250.0 / 93.0,
        {},
    ),
    (Metric.RV_PER_100, dict(pitch_rv_sum=-2.5, pitches=500), -0.5, {}),
    (Metric.WHIFF_PER_100, dict(whiffs=25, pitches=500), 5.0, {}),
    # ---- statcast expected ----
    (Metric.XBA, dict(xba_sum=30.0, ab=100), 0.30, {}),
    (Metric.XSLG, dict(xslg_sum=45.0, ab=100), 0.45, {}),
    (Metric.XWOBA, dict(xwoba_sum=32.0, xwoba_count=100), 0.32, {}),
    (Metric.BA_MINUS_XBA, dict(h=28, ab=100, xba_sum=30.0), 0.28 - 0.30, {}),
    (
        Metric.WOBA_MINUS_XWOBA,
        dict(
            ab=100,
            bb=10,
            ibb=2,
            hbp=1,
            sf=1,
            h=30,
            b2=6,
            b3=1,
            hr=4,
            xwoba_sum=32.0,
            xwoba_count=100,
        ),
        WOBA_LINE - 0.32,
        {},
    ),
    # ---- baserunning ----
    (Metric.SB_PCT, dict(sb=20, cs=5), 0.8, {}),
    (
        Metric.WSB,
        dict(sb=10, cs=2, h=100, b2=20, b3=2, hr=15, bb=40, ibb=5, hbp=3),
        10 * W.r_sb + 2 * W.r_cs - 0.02 * (WSB_1B + 35 + 3),
        dict(lg_wsb=0.02),
    ),
    (
        Metric.SPEED_SCORE,
        dict(sb=10, cs=2, h=150, b2=25, b3=5, hr=20, bb=60, ab=500, r=90, ibb=5, hbp=4, so=100),
        SPEED,
        {},
    ),
    (Metric.WGDP, dict(gidp=8, gidp_opp=100), (100 * W.lg_gidp_rate - 8) * W.r_gidp, {}),
    (
        Metric.BSR,
        dict(
            sb=10,
            cs=2,
            h=100,
            b2=20,
            b3=2,
            hr=15,
            bb=40,
            ibb=5,
            hbp=3,
            gidp=8,
            gidp_opp=100,
            ubr=1.5,
        ),
        (10 * W.r_sb + 2 * W.r_cs - 0.02 * (WSB_1B + 35 + 3))
        + (100 * W.lg_gidp_rate - 8) * W.r_gidp
        + 1.5,
        dict(lg_wsb=0.02),
    ),
    (Metric.XBT_PCT, dict(xbt=25, xbt_opp=60), 25 / 60, {}),
    # ---- fielding ----
    (Metric.TC, dict(po=300, a=100, e=5), 405, {}),
    (Metric.FPCT, dict(po=300, a=100, e=5), 400 / 405, {}),
    (Metric.ERR_PCT, dict(po=300, a=100, e=5), 5 / 405, {}),
    (Metric.RF_PER_G, dict(po=300, a=100, g=100), 4.0, {}),
    (Metric.RF_PER_9, dict(po=300, a=100, inn_outs_fld=2700), 27 * 400 / 2700, {}),
    (
        Metric.DER,
        dict(h=150, hr=20, ab=500, so=100, sf=5),
        1 - (150 - 20) / (500 - 100 - 20 + 5),
        {},
    ),
    (Metric.CATCHER_CS_PCT, dict(cs=8, sb=32), 0.2, {}),
    # ---- team ----
    (Metric.RUN_DIFF, dict(rs=800, ra=700), 100, {}),
    (Metric.WIN_PCT, dict(w=90, l=72), 90 / 162, {}),
    (Metric.PYTHAG_WIN_PCT, dict(rs=800, ra=700), _PY, {}),
    (Metric.PYTHAGENPAT_WIN_PCT, dict(rs=800, ra=700, w=90, l=72), _PYPAT, {}),
    (Metric.PYTHAG_WINS, dict(rs=800, ra=700, w=90, l=72), 162 * _PY, {}),
    (Metric.PYTHAG_LUCK, dict(rs=800, ra=700, w=90, l=72), 90 - 162 * _PY, {}),
    # ---- weighted offense / run estimators ----
    (
        Metric.OPS_PLUS,
        dict(**BAT, hbp=1, sf=1),
        (100 / 1.10) * (OBP / W.lg_obp + SLG / W.lg_slg - 1),
        dict(park_factor=110.0),
    ),
    (Metric.RC_BASIC, dict(**BAT), (30 + 12) * TB / (100 + 12), {}),
    (Metric.RC_TECH, dict(**BAT, ibb=2, hbp=1, sb=3, cs=1, gidp=2, sh=1, sf=1), RC_TECH, {}),
    (
        Metric.BASE_RUNS,
        dict(**BAT, ibb=2, hbp=1, sb=3, cs=1, gidp=2),
        BASE_RUNS,
        {},
    ),  # Smyth version 2 (1.1)
    (
        Metric.RC27,
        dict(**BAT, ibb=2, hbp=1, sb=3, cs=1, gidp=2, sh=1, sf=1),
        27 * RC_TECH / (100 - 30 + 1 + 1 + 1 + 2),
        {},
    ),
    (Metric.GPA, dict(**BAT, hbp=1, sf=1), (1.8 * OBP + SLG) / 4, {}),
    (
        Metric.TA,
        dict(**BAT, hbp=1, sb=3, cs=1, gidp=2),
        (TB + 12 + 1 + 3) / (100 - 30 + 1 + 2),
        {},
    ),
    # ---- expectancy ----
    (Metric.PLI, dict(li_sum=150.0, pa=100), 1.5, {}),
    (Metric.WPA_LI, dict(wpa_li_sum=2.5), 2.5, {}),
    (Metric.CLUTCH, dict(wpa=3.0, li_sum=150.0, pa=100, wpa_li_sum=2.5), 3.0 / 1.5 - 2.5, {}),
    (Metric.REW, dict(re24=20.0), 20.0 / W.lg_r_per_w, {}),
]

# Metrics asserted against published FanGraphs values in tests/test_golden_values.py.
GOLDEN_COVERED = {m.value for m, _ in BATTING_METRICS.values()} | {
    m.value for m, _ in PITCHING_METRICS.values()
}
# `off` composes wRAA, BsR and league constants; its formula recomputation is in tests/test_game_score_and_off.py.
TABLE_COVERED = {m.value for m, *_ in CASES} | {"off"}


def _context(kwargs: dict[str, Any]) -> SeasonContext:
    weights = W
    if "lg_wsb" in kwargs:
        weights = W.model_copy(update={"lg_wsb": kwargs["lg_wsb"]})
    extra = {k: v for k, v in kwargs.items() if k != "lg_wsb"}
    return SeasonContext(season=2024, weights=weights, **extra)


@pytest.mark.parametrize(
    ("metric", "inputs", "expected", "ctx"), CASES, ids=[c[0].value for c in CASES]
)
def test_metric_value_matches_hand_derivation(
    metric: Metric, inputs: dict[str, Any], expected: float, ctx: dict[str, Any]
) -> None:
    frame = pl.DataFrame({"player_id": ["p"], **{k: [v] for k, v in inputs.items()}})
    res = sp.calculate(frame, [metric], context=_context(ctx))
    got = res.df[metric.value][0]
    assert got is not None, f"{metric.value} returned null"
    assert math.isclose(got, expected, rel_tol=1e-9, abs_tol=1e-9), (
        f"{metric.value}: {got} != {expected}"
    )


def test_every_registered_metric_has_a_value_assertion() -> None:
    # Built-in metrics only: custom/plugin metrics registered by other tests are declared with plain strings.
    names = {s.name for s in REGISTRY.all_specs() if isinstance(s.metric, Metric)}
    uncovered = sorted(names - GOLDEN_COVERED - TABLE_COVERED)
    assert not uncovered, f"registered metrics with no value assertion: {uncovered}"


def test_guard_detects_a_metric_missing_from_the_tables() -> None:
    names = {"avg", "totally_new_metric"}
    assert sorted(names - GOLDEN_COVERED - TABLE_COVERED) == ["totally_new_metric"]


def test_base_runs_uses_smyth_version_1_multiplier_for_basic_columns() -> None:
    """Basic columns only: A=H+BB-HR, B=(1.4TB-.6H-3HR+.1BB)*1.02, C=AB-H, D=HR (Smyth version 1)."""
    b = 1.02 * (1.4 * TB - 0.6 * 30 - 3 * 4 + 0.1 * 12)
    expected = (30 + 12 - 4) * b / (b + (100 - 30)) + 4
    frame = pl.DataFrame({"player_id": ["p"], **{k: [v] for k, v in BAT.items()}})
    got = sp.calculate(frame, [Metric.BASE_RUNS], context=_context({})).df["base_runs"][0]
    assert math.isclose(got, expected, rel_tol=1e-9)


def test_pythagenpat_exponent_is_configurable() -> None:
    gamma = (1500 / 162) ** 0.285
    expected = 800**gamma / (800**gamma + 700**gamma)
    frame = pl.DataFrame({"player_id": ["t"], "rs": [800], "ra": [700], "w": [90], "l": [72]})
    ctx = SeasonContext(season=2024, weights=W, pythagenpat_exponent=0.285)
    got = sp.calculate(frame, [Metric.PYTHAGENPAT_WIN_PCT], context=ctx).df["pythagenpat_win_pct"][
        0
    ]
    assert math.isclose(got, expected, rel_tol=1e-9)
    assert not math.isclose(got, _PYPAT, rel_tol=1e-12)
