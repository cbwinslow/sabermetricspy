"""Core enumeration types and closed vocabularies for sabermetricspy.

Follows the 3-Tier Naming Standard defined in docs/NAMING_CONVENTIONS.md:
- Tier 1 (StrEnum member name): UPPER_SNAKE_CASE official baseball abbreviations
- Tier 2 (StrEnum string value): lower_snake_case canonical column/function identifiers
- Tier 3 (MetricSpec.display_name): Authentic sabermetric typography
"""

from __future__ import annotations

from enum import StrEnum


class Category(StrEnum):
    """High-level domain category of a baseball metric."""

    BATTING = "batting"
    WEIGHTED_OFFENSE = "weighted_offense"
    PITCHING = "pitching"
    DEFENSE_INDEPENDENT_PITCHING = "defense_independent_pitching"
    PLATE_DISCIPLINE = "plate_discipline"
    BATTED_BALL = "batted_ball"
    STATCAST_EXPECTED = "statcast_expected"
    PITCH_PHYSICS = "pitch_physics"
    BASERUNNING = "baserunning"
    FIELDING = "fielding"
    EXPECTANCY = "expectancy"
    VALUE = "value"
    TEAM = "team"


class ImplKind(StrEnum):
    """Implementation classification of a metric."""

    DETERMINISTIC = "deterministic"
    CONTEXTUAL = "contextual"
    EMPIRICAL = "empirical"
    MODELED = "modeled"


class ReferenceStatus(StrEnum):
    """How closely a metric follows the published method of its reference source."""

    MATCHES = "matches"
    APPROXIMATE = "approximate"
    DIVERGENT = "divergent"
    UNVERIFIED = "unverified"


class EvidenceTier(StrEnum):
    """How strongly an audit result is supported by its sources."""

    GOLDEN = "golden"
    PRIMARY = "primary"
    SECONDARY = "secondary"


class Direction(StrEnum):
    """Competitive direction of a metric."""

    HIGHER_IS_BETTER = "higher_is_better"
    LOWER_IS_BETTER = "lower_is_better"
    NEUTRAL = "neutral"


class Handedness(StrEnum):
    """Player batting or pitching handedness."""

    LEFT = "L"
    RIGHT = "R"
    SWITCH = "S"


class PitchOutcome(StrEnum):
    """Canonical pitch-level outcome taxonomy."""

    BALL = "ball"
    INTENTIONAL_BALL = "intentional_ball"
    AUTOMATIC_BALL = "automatic_ball"
    PITCHOUT = "pitchout"
    HIT_BY_PITCH = "hit_by_pitch"
    CALLED_STRIKE = "called_strike"
    AUTOMATIC_STRIKE = "automatic_strike"
    SWINGING_STRIKE = "swinging_strike"
    SWINGING_STRIKE_BLOCKED = "swinging_strike_blocked"
    MISSED_BUNT = "missed_bunt"
    FOUL = "foul"
    FOUL_BUNT = "foul_bunt"
    FOUL_TIP = "foul_tip"
    IN_PLAY = "in_play"


class PlayOutcome(StrEnum):
    """Canonical plate-appearance / play-by-play event taxonomy."""

    SINGLE = "single"
    DOUBLE = "double"
    TRIPLE = "triple"
    HOME_RUN = "home_run"
    WALK = "walk"
    INTENTIONAL_WALK = "intentional_walk"
    HIT_BY_PITCH = "hit_by_pitch"
    STRIKEOUT = "strikeout"
    SAC_FLY = "sac_fly"
    SAC_BUNT = "sac_bunt"
    FIELD_OUT = "field_out"
    FORCE_OUT = "force_out"
    GROUNDED_INTO_DP = "grounded_into_dp"
    DOUBLE_PLAY = "double_play"
    TRIPLE_PLAY = "triple_play"
    FIELDERS_CHOICE = "fielders_choice"
    REACHED_ON_ERROR = "reached_on_error"
    CATCHER_INTERFERENCE = "catcher_interference"
    STOLEN_BASE = "stolen_base"
    CAUGHT_STEALING = "caught_stealing"
    PICKOFF = "pickoff"
    WILD_PITCH = "wild_pitch"
    PASSED_BALL = "passed_ball"
    BALK = "balk"
    OTHER_ADVANCE = "other_advance"


class BattedBallType(StrEnum):
    """Canonical batted-ball trajectory classifications."""

    GROUND_BALL = "ground_ball"
    FLY_BALL = "fly_ball"
    LINE_DRIVE = "line_drive"
    POPUP = "popup"


class BaseState(StrEnum):
    """The 8 base-runner occupancy states (`_`, `1`, `2`, `3`)."""

    EMPTY = "---"
    FIRST = "1--"
    SECOND = "-2-"
    THIRD = "--3"
    FIRST_SECOND = "12-"
    FIRST_THIRD = "1-3"
    SECOND_THIRD = "-23"
    LOADED = "123"

    @classmethod
    def from_runners(cls, on_1b: bool, on_2b: bool, on_3b: bool) -> BaseState:
        """Construct a BaseState from boolean occupancy flags."""
        code = f"{'1' if on_1b else '-'}{'2' if on_2b else '-'}{'3' if on_3b else '-'}"
        return cls(code)


class Stat(StrEnum):
    """Canonical additive counting & measurement columns (Tier 1 -> Tier 2)."""

    # Games & Plate Appearances
    G = "g"
    GS = "gs"
    PA = "pa"
    AB = "ab"
    R = "r"
    H = "h"
    B1 = "b1"
    B2 = "b2"
    B3 = "b3"
    HR = "hr"
    RBI = "rbi"
    BB = "bb"
    IBB = "ibb"
    UBB = "ubb"
    HBP = "hbp"
    SO = "so"
    SF = "sf"
    SH = "sh"
    CI = "ci"
    ROE = "roe"
    GIDP = "gidp"
    LOB = "lob"

    # Baserunning
    SB = "sb"
    CS = "cs"
    PK = "pk"
    OOB = "oob"
    XBT = "xbt"
    XBT_OPP = "xbt_opp"
    GIDP_OPP = "gidp_opp"
    UBR = "ubr"

    # Pitching
    OUTS = "outs"
    BF = "bf"
    ER = "er"
    RA = "ra"
    W = "w"
    L = "l"
    CG = "cg"
    SHO = "sho"
    QS = "qs"
    SV = "sv"
    BS = "bs"
    HLD = "hld"
    WP = "wp"
    BK = "bk"

    # Plate Discipline & Pitches
    PITCHES = "pitches"
    SWINGS = "swings"
    WHIFFS = "whiffs"
    CALLED_STRIKES = "called_strikes"
    FOULS = "fouls"
    CONTACTS = "contacts"
    ZONE_PITCHES = "zone_pitches"
    OUT_ZONE_PITCHES = "out_zone_pitches"
    ZONE_SWINGS = "zone_swings"
    OUT_ZONE_SWINGS = "out_zone_swings"
    ZONE_CONTACTS = "zone_contacts"
    OUT_ZONE_CONTACTS = "out_zone_contacts"
    FIRST_PITCH_SWINGS = "first_pitch_swings"
    FIRST_PITCH_STRIKES = "first_pitch_strikes"
    TWO_STRIKE_SO = "two_strike_so"
    TWO_STRIKE_PITCHES = "two_strike_pitches"
    TWO_STRIKE_OUT_ZONE_SWINGS = "two_strike_out_zone_swings"
    TWO_STRIKE_OUT_ZONE_PITCHES = "two_strike_out_zone_pitches"
    MEATBALL_SWINGS = "meatball_swings"
    MEATBALL_PITCHES = "meatball_pitches"

    # Batted-Ball & Statcast
    BBE = "bbe"
    GB = "gb"
    FB = "fb"
    LD = "ld"
    PU = "pu"
    PULL_BBE = "pull_bbe"
    CENT_BBE = "cent_bbe"
    OPPO_BBE = "oppo_bbe"
    HARD_HIT_BBE = "hard_hit_bbe"
    SWEET_SPOT_BBE = "sweet_spot_bbe"
    BARRELS = "barrels"
    EV_SUM = "ev_sum"
    EV_COUNT = "ev_count"
    EV_MAX = "ev_max"

    # Statcast Expected Sums & Pitch Physics Sums
    XBA_SUM = "xba_sum"
    XSLG_SUM = "xslg_sum"
    XWOBA_SUM = "xwoba_sum"
    XWOBA_COUNT = "xwoba_count"
    VELO_SUM = "velo_sum"
    VELO_COUNT = "velo_count"
    SPIN_SUM = "spin_sum"
    SPIN_COUNT = "spin_count"
    EXT_SUM = "ext_sum"
    EXT_COUNT = "ext_count"
    IVB_SUM = "ivb_sum"
    HB_SUM = "hb_sum"
    BREAK_COUNT = "break_count"
    TOTAL_BREAK_SUM = "total_break_sum"
    EFF_VELO_SUM = "eff_velo_sum"
    EFF_VELO_COUNT = "eff_velo_count"
    VAA_SUM = "vaa_sum"
    VAA_COUNT = "vaa_count"
    HAA_SUM = "haa_sum"
    HAA_COUNT = "haa_count"
    PITCH_RV_SUM = "pitch_rv_sum"

    # Fielding
    PO = "po"
    A = "a"
    E = "e"
    DP = "dp"
    TP = "tp"
    PB = "pb"
    INN_OUTS_FLD = "inn_outs_fld"

    # Expectancy & Win Probability
    RE24 = "re24"
    WPA = "wpa"
    LI_SUM = "li_sum"
    WPA_LI_SUM = "wpa_li_sum"

    # Team / Game-Level
    RS = "rs"


class Metric(StrEnum):
    """Canonical Sabermetric Metric Identifiers (Tier 1 -> Tier 2)."""

    # Derived Batting Counts & Traditional Rates
    B1 = "b1"
    TB = "tb"
    XBH = "xbh"
    UBB = "ubb"
    AVG = "avg"
    OBP = "obp"
    SLG = "slg"
    OPS = "ops"
    ISO = "iso"
    BABIP = "babip"
    SECA = "seca"
    XBH_PCT = "xbh_pct"
    HR_PCT = "hr_pct"
    BB_PCT = "bb_pct"
    K_PCT = "k_pct"
    K_MINUS_BB_PCT = "k_minus_bb_pct"
    BB_TO_K = "bb_to_k"
    K_TO_BB = "k_to_bb"
    R_PER_PA = "r_per_pa"
    RBI_PER_PA = "rbi_per_pa"
    BAT_K_PCT_PLUS = "bat_k_pct_plus"
    BAT_BB_PCT_PLUS = "bat_bb_pct_plus"

    # Weighted Offense & Run Estimators
    WOBA = "woba"
    WRAA = "wraa"
    WRC = "wrc"
    WRC_PLUS = "wrc_plus"
    OFF = "off"
    OPS_PLUS = "ops_plus"
    RC_BASIC = "rc_basic"
    RC_TECH = "rc_tech"
    RC27 = "rc27"
    BASE_RUNS = "base_runs"
    GPA = "gpa"
    TA = "ta"

    # Baserunning
    SB_PCT = "sb_pct"
    WSB = "wsb"
    SPEED_SCORE = "speed_score"
    XBT_PCT = "xbt_pct"
    WGDP = "wgdp"
    BSR = "bsr"

    # Traditional Pitching
    IP = "ip"
    ERA = "era"
    RA9 = "ra9"
    WHIP = "whip"
    BASE_ADVANCE_AVERAGE = "base_advance_average"
    SHUTDOWN = "shutdown"
    MELTDOWN = "meltdown"
    GAME_SCORE = "game_score"
    GAME_SCORE_V2 = "game_score_v2"
    H_PER_9 = "h_per_9"
    BB_PER_9 = "bb_per_9"
    K_PER_9 = "k_per_9"
    HR_PER_9 = "hr_per_9"
    PIT_K_PCT = "pit_k_pct"
    PIT_BB_PCT = "pit_bb_pct"
    PIT_K_MINUS_BB_PCT = "pit_k_minus_bb_pct"
    PIT_BB_TO_K = "pit_bb_to_k"
    PIT_K_TO_BB = "pit_k_to_bb"
    BF_PER_IP = "bf_per_ip"
    LOB_PCT = "lob_pct"
    QS_PCT = "qs_pct"
    CG_PCT = "cg_pct"
    SV_PCT = "sv_pct"

    # Defense-Independent & Indexed Pitching
    FIP = "fip"
    XFIP = "xfip"
    KWERA = "kwera"
    DICE = "dice"
    QERA = "qera"
    DIPS_BOP_PCT = "dips_bop_pct"
    XERA = "xera"
    SIERA = "siera"
    ERA_PLUS = "era_plus"
    ERA_MINUS = "era_minus"
    FIP_MINUS = "fip_minus"
    XFIP_MINUS = "xfip_minus"
    K_PCT_PLUS = "k_pct_plus"
    BB_PCT_PLUS = "bb_pct_plus"

    # Plate Discipline
    SWING_PCT = "swing_pct"
    Z_SWING_PCT = "z_swing_pct"
    O_SWING_PCT = "o_swing_pct"
    ZONE_PCT = "zone_pct"
    CONTACT_PCT = "contact_pct"
    Z_CONTACT_PCT = "z_contact_pct"
    O_CONTACT_PCT = "o_contact_pct"
    WHIFF_PCT = "whiff_pct"
    SWSTR_PCT = "swstr_pct"
    CSTR_PCT = "cstr_pct"
    CSW_PCT = "csw_pct"
    FOUL_PCT = "foul_pct"
    BIP_PCT = "bip_pct"
    FP_SWING_PCT = "fp_swing_pct"
    FP_STRIKE_PCT = "fp_strike_pct"
    PUTAWAY_PCT = "putaway_pct"
    TWO_STRIKE_CHASE_PCT = "two_strike_chase_pct"
    MEATBALL_SWING_PCT = "meatball_swing_pct"

    # Batted-Ball & Contact Quality
    GB_PCT = "gb_pct"
    FB_PCT = "fb_pct"
    LD_PCT = "ld_pct"
    PU_PCT = "pu_pct"
    GB_TO_FB = "gb_to_fb"
    HR_TO_FB = "hr_to_fb"
    PULL_PCT = "pull_pct"
    CENT_PCT = "cent_pct"
    OPPO_PCT = "oppo_pct"
    HARD_HIT_PCT = "hard_hit_pct"
    SWEET_SPOT_PCT = "sweet_spot_pct"
    BARREL_PCT = "barrel_pct"
    AVG_EV = "avg_ev"

    # Statcast Expected Offense
    XBA = "xba"
    XSLG = "xslg"
    XWOBA = "xwoba"
    BA_MINUS_XBA = "ba_minus_xba"
    WOBA_MINUS_XWOBA = "woba_minus_xwoba"

    # Pitch Kinematics & Physics
    AVG_VELO = "avg_velo"
    AVG_SPIN = "avg_spin"
    AVG_EXTENSION = "avg_extension"
    IVB = "ivb"
    HB = "hb"
    TOTAL_BREAK = "total_break"
    EFFECTIVE_VELO = "effective_velo"
    VAA = "vaa"
    HAA = "haa"
    BAUER_UNITS = "bauer_units"
    RV_PER_100 = "rv_per_100"
    WHIFF_PER_100 = "whiff_per_100"

    # Fielding
    TC = "tc"
    FPCT = "fpct"
    ERR_PCT = "err_pct"
    RF_PER_G = "rf_per_g"
    RF_PER_9 = "rf_per_9"
    DER = "der"
    CATCHER_CS_PCT = "catcher_cs_pct"

    # Expectancy & Win Probability Aggregates
    PLI = "pli"
    WPA_LI = "wpa_li"
    CLUTCH = "clutch"
    REW = "rew"

    # Team Performance
    RUN_DIFF = "run_diff"
    WIN_PCT = "win_pct"
    PYTHAG_WIN_PCT = "pythag_win_pct"
    PYTHAGENPAT_WIN_PCT = "pythagenpat_win_pct"
    PYTHAG_WINS = "pythag_wins"
    PYTHAG_LUCK = "pythag_luck"


class MetricSuite(StrEnum):
    """Curated metric bundles for single-call calculation."""

    TRADITIONAL_BATTING = "traditional_batting"
    WEIGHTED_OFFENSE = "weighted_offense"
    BASERUNNING = "baserunning"
    TRADITIONAL_PITCHING = "traditional_pitching"
    DEFENSE_INDEPENDENT_PITCHING = "defense_independent_pitching"
    PLATE_DISCIPLINE = "plate_discipline"
    BATTED_BALL = "batted_ball"
    STATCAST_EXPECTED = "statcast_expected"
    PITCH_PHYSICS = "pitch_physics"
    FIELDING = "fielding"
    EXPECTANCY = "expectancy"
    TEAM_ESTIMATORS = "team_estimators"
    OFFENSE_ALL = "offense_all"
    PITCHING_ALL = "pitching_all"
    ALL = "all"
