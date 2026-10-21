"""Comprehensive unit, property-based (Hypothesis), golden cross-check, and multi-backend tests."""

from __future__ import annotations

import math

import duckdb
import pandas as pd
import polars as pl
import pyarrow as pa
import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

import sabermetricspy as sp
from sabermetricspy import (
    BaseState,
    LinearWeightsEstimator,
    Log5Model,
    MarcelProjector,
    MarkovChainModel,
    Metric,
    MetricSuite,
    MonteCarloSimulator,
    RunExpectancyMatrix,
    SeasonContext,
    Stat,
    WARFramework,
    binomial_rate_interval,
    bootstrap_interval,
    ip_notation_to_outs_scalar,
    load_custom_metrics_yaml,
    outs_to_ip_notation_scalar,
    prepare_retrosheet_events,
    prepare_statcast_pitches,
)


# ==============================================================================
# 1. Three-Tier Naming & Registry Introspection Tests
# ==============================================================================
def test_three_tier_naming_and_registry_lookup() -> None:
    assert Metric.WRC_PLUS == "wrc_plus"
    assert Stat.HR == "hr"
    assert Stat.OUTS == "outs"

    # Lookup by StrEnum, snake_case string, and official display_name ('wRC+')
    spec_enum = sp.describe(Metric.WRC_PLUS)
    spec_str = sp.describe("wrc_plus")
    spec_disp = sp.describe("wRC+")

    assert spec_enum == spec_str == spec_disp
    assert spec_enum.name == "wrc_plus"
    assert spec_enum.display_name == "wRC+"
    assert "wRAA" in sp.formula(Metric.WRC_PLUS)

    pitching_metrics = sp.search_metrics(category=sp.Category.DEFENSE_INDEPENDENT_PITCHING)
    names = {m.name for m in pitching_metrics}
    assert {"fip", "xfip", "kwera", "siera", "dice"}.issubset(names)


# ==============================================================================
# 2. Innings Pitched ("6.2" <-> 20 Outs) & Zero-Denominator Safety Tests
# ==============================================================================
def test_innings_pitched_conversion() -> None:
    assert ip_notation_to_outs_scalar("5.1") == 16
    assert ip_notation_to_outs_scalar(5.2) == 17
    assert ip_notation_to_outs_scalar(6.0) == 18
    assert ip_notation_to_outs_scalar("6.2") == 20
    assert outs_to_ip_notation_scalar(20) == "6.2"
    assert outs_to_ip_notation_scalar(18) == "6.0"

    with pytest.raises(ValueError, match="Invalid baseball innings-pitched notation"):
        ip_notation_to_outs_scalar(6.4)

    # Vectorized DataFrame conversion from `ip` to `outs` and `ERA`
    df = pl.DataFrame(
        {"player_id": ["p1", "p2"], "ip": [6.2, 0.0], "er": [2, 0], "bb": [1, 0], "h": [4, 0]}
    )
    res = sp.calculate(df, [Metric.IP, Metric.ERA, Metric.WHIP])
    out = res.df
    # 6.2 IP = 20 outs = 6.6667 IP -> ERA = 9 * 2 / (20/3) = 2.70
    assert math.isclose(out["ip"][0], 20.0 / 3.0, rel_tol=1e-9)
    assert math.isclose(out["era"][0], 2.70, rel_tol=1e-9)
    assert math.isclose(out["whip"][0], 5.0 / (20.0 / 3.0), rel_tol=1e-9)
    # Zero outs -> null, never inf, NaN or ZeroDivisionError
    assert out["era"][1] is None
    assert out["whip"][1] is None


# ==============================================================================
# 3. Two-Stage Additive Grouping Rule (Never Average Ratios)
# ==============================================================================
def test_additive_counts_before_ratios() -> None:
    # Game 1: 3-for-4 (.750). Game 2: 1-for-5 (.200).
    # True combined AVG = 4 / 9 = 0.4444..., NOT (0.750 + 0.200) / 2 = 0.475!
    df = pl.DataFrame(
        {
            "player_id": ["b1", "b1"],
            "game_id": [1, 2],
            "ab": [4, 5],
            "h": [3, 1],
            "b2": [1, 0],
            "b3": [0, 0],
            "hr": [1, 0],
            "bb": [1, 0],
            "hbp": [0, 0],
            "sf": [0, 0],
        }
    )
    res = sp.calculate(df, [Metric.AVG, Metric.OPS], by="player_id")
    row = res.df.row(0, named=True)
    assert math.isclose(row["avg"], 4.0 / 9.0, rel_tol=1e-9)
    # TB = 2 singles (2) + 1 double (2) + 1 HR (4) = 8 TB in 9 AB -> SLG = 8/9
    # OBP = (4 + 1) / (9 + 1) = 5/10 = 0.500 -> OPS = 0.500 + 8/9 = 1.388888...
    assert math.isclose(row["ops"], 0.5 + (8.0 / 9.0), rel_tol=1e-9)


# ==============================================================================
# 4. Golden Cross-Check Tests Against Historical MLB Benchmarks
# ==============================================================================
def test_golden_barry_bonds_2001_and_pedro_martinez_2000() -> None:
    # Barry Bonds 2001 historical stats:
    # PA=664, AB=476, H=156, 2B=32, 3B=2, HR=73, BB=177, IBB=35, HBP=9, SF=2, SO=93, SB=13, CS=3, R=129, RBI=137
    bonds_df = pl.DataFrame(
        {
            "player_id": ["bondsba01"],
            "season": [2001],
            "pa": [664],
            "ab": [476],
            "h": [156],
            "b2": [32],
            "b3": [2],
            "hr": [73],
            "bb": [177],
            "ibb": [35],
            "hbp": [9],
            "sf": [2],
            "so": [93],
            "sb": [13],
            "cs": [3],
            "r": [129],
            "rbi": [137],
        }
    )
    res = sp.calculate(
        bonds_df,
        [
            Metric.AVG,
            Metric.OBP,
            Metric.SLG,
            Metric.OPS,
            Metric.ISO,
            Metric.BABIP,
            Metric.WOBA,
            Metric.WRAA,
            Metric.WRC_PLUS,
        ],
        season=2001,
    )
    row = res.df.row(0, named=True)
    assert math.isclose(row["avg"], 156 / 476, abs_tol=1e-4)  # .3277
    assert math.isclose(row["obp"], (156 + 177 + 9) / (476 + 177 + 9 + 2), abs_tol=1e-4)  # .5151
    assert math.isclose(row["slg"], 411 / 476, abs_tol=1e-4)  # .8634
    assert math.isclose(row["ops"], row["obp"] + row["slg"], abs_tol=1e-6)  # 1.3785
    assert math.isclose(row["iso"], row["slg"] - row["avg"], abs_tol=1e-6)  # .5357
    # Exact published-value checks (wOBA, wRAA, wRC, wRC+) live in tests/test_golden_values.py.

    # Pedro Martinez 2000 historical stats:
    # IP=217.0 (651 outs), ER=42, RA=44, H=128, BB=32, IBB=0, HBP=14, HR=17, SO=284, BF=817
    pedro_df = pl.DataFrame(
        {
            "player_id": ["martipe02"],
            "season": [2000],
            "ip": [217.0],
            "er": [42],
            "ra": [44],
            "h": [128],
            "bb": [32],
            "ibb": [0],
            "hbp": [14],
            "hr": [17],
            "so": [284],
            "bf": [817],
        }
    )
    pres = sp.calculate(
        pedro_df,
        [
            Metric.ERA,
            Metric.WHIP,
            Metric.K_PER_9,
            Metric.BB_PER_9,
            Metric.FIP,
            Metric.ERA_PLUS,
            Metric.FIP_MINUS,
        ],
        context=SeasonContext(season=2000, park_factor=104.0),
    )
    prow = pres.df.row(0, named=True)
    assert math.isclose(prow["era"], 1.7419, abs_tol=1e-3)
    assert math.isclose(prow["whip"], 0.7373, abs_tol=1e-3)
    assert math.isclose(prow["k_per_9"], 11.7788, abs_tol=1e-3)
    assert math.isclose(prow["fip"], 2.1710342213854816, abs_tol=5e-4)  # FanGraphs FIP, 2000
    # ERA+ / FIP- are approximate (see METHODOLOGY); published-value checks are in tests/test_golden_values.py.


# ==============================================================================
# 5. Multi-Backend Interoperability (Polars, pandas, PyArrow, DuckDB)
# ==============================================================================
def test_multi_backend_interoperability() -> None:
    data = {
        "player_id": ["p1", "p2"],
        "pa": [600, 500],
        "ab": [520, 450],
        "h": [160, 120],
        "b2": [35, 22],
        "b3": [4, 2],
        "hr": [30, 15],
        "bb": [65, 40],
        "ibb": [5, 1],
        "hbp": [8, 5],
        "sf": [7, 5],
        "so": [110, 95],
    }
    metrics = [
        Metric.AVG,
        Metric.OBP,
        Metric.SLG,
        Metric.OPS,
        Metric.ISO,
        Metric.BABIP,
        Metric.WOBA,
        Metric.WRC_PLUS,
    ]

    pl_df = pl.DataFrame(data)
    pd_df = pd.DataFrame(data)
    pa_tbl = pa.Table.from_pydict(data)
    con = duckdb.connect()
    duck_rel = con.from_arrow(pa_tbl)

    res_pl = sp.calculate(pl_df, metrics)
    res_pd = sp.calculate(pd_df, metrics)
    res_pa = sp.calculate(pa_tbl, metrics)
    res_duck = sp.calculate(duck_rel, metrics)

    assert isinstance(res_pl.df, pl.DataFrame)
    assert isinstance(res_pd.df, pd.DataFrame)
    assert isinstance(res_pa.df, pa.Table)

    pl_wrc = res_pl.df["wrc_plus"].to_list()
    pd_wrc = res_pd.df["wrc_plus"].tolist()
    pa_wrc = res_pa.df["wrc_plus"].to_pylist()
    duck_wrc = res_duck.to_polars()["wrc_plus"].to_list()

    for i in range(2):
        assert math.isclose(pl_wrc[i], pd_wrc[i], rel_tol=1e-9)
        assert math.isclose(pl_wrc[i], pa_wrc[i], rel_tol=1e-9)
        assert math.isclose(pl_wrc[i], duck_wrc[i], rel_tol=1e-9)


# ==============================================================================
# 6. Property-Based Mathematical Identity Tests (Hypothesis)
# ==============================================================================
@given(
    b1=st.integers(min_value=0, max_value=150),
    b2=st.integers(min_value=0, max_value=50),
    b3=st.integers(min_value=0, max_value=15),
    hr=st.integers(min_value=0, max_value=60),
    outs_in_play=st.integers(min_value=1, max_value=400),
    so=st.integers(min_value=0, max_value=200),
    bb=st.integers(min_value=0, max_value=150),
    hbp=st.integers(min_value=0, max_value=20),
    sf=st.integers(min_value=0, max_value=15),
)
@settings(max_examples=40, deadline=None)
def test_property_based_offensive_identities(
    b1: int,
    b2: int,
    b3: int,
    hr: int,
    outs_in_play: int,
    so: int,
    bb: int,
    hbp: int,
    sf: int,
) -> None:
    h = b1 + b2 + b3 + hr
    ab = h + outs_in_play + so
    pa = ab + bb + hbp + sf

    df = pl.DataFrame(
        {
            "pa": [pa],
            "ab": [ab],
            "h": [h],
            "b2": [b2],
            "b3": [b3],
            "hr": [hr],
            "bb": [bb],
            "hbp": [hbp],
            "sf": [sf],
            "so": [so],
        }
    )
    res = sp.calculate(
        df,
        [
            Metric.AVG,
            Metric.OBP,
            Metric.SLG,
            Metric.OPS,
            Metric.ISO,
            Metric.BB_PCT,
            Metric.K_PCT,
            Metric.K_MINUS_BB_PCT,
            Metric.BABIP,
            Metric.DER,
        ],
    )
    r = res.df.row(0, named=True)

    # Identity 1: OPS == OBP + SLG
    assert math.isclose(r["ops"], r["obp"] + r["slg"], abs_tol=1e-9)
    # Identity 2: ISO == SLG - AVG
    assert math.isclose(r["iso"], r["slg"] - r["avg"], abs_tol=1e-9)
    # Identity 3: K-BB% == K% - BB%
    assert math.isclose(r["k_minus_bb_pct"], r["k_pct"] - r["bb_pct"], abs_tol=1e-9)
    # Identity 4: DER == 1.0 - BABIP
    assert math.isclose(r["der"], 1.0 - r["babip"], abs_tol=1e-9)
    # Identity 5: Bounds 0 <= AVG <= SLG <= 4.0
    assert 0.0 <= r["avg"] <= r["slg"] + 1e-9 <= 4.0 + 1e-9


# ==============================================================================
# 7. Presets (`retrosheetpy` & `statcast`), Suites, & Custom YAML Formulas
# ==============================================================================
def test_retrosheetpy_and_statcast_presets_and_custom_yaml() -> None:
    retro_raw = pl.DataFrame(
        {
            "GAME_ID": ["BOS202404010", "BOS202404010"],
            "BAT_ID": ["dever001", "dever001"],
            "PIT_ID": ["burnc001", "burnc001"],
            "OUTS_CT": [0, 0],
            "BASE1_RUN_ID": ["", ""],
            "BASE2_RUN_ID": ["", ""],
            "BASE3_RUN_ID": ["", ""],
            "EVENT_CD": [23, 3],  # HR then SO
            "H_CD": [4, 0],
            "AB_FL": [True, True],
            "SH_FL": [False, False],
            "SF_FL": [False, False],
            "BAT_EVENT_FL": [True, True],
            "EVENT_OUTS_CT": [0, 1],
            "RBI_CT": [1, 0],
            "BAT_DEST_ID": [4, 0],
            "BATTEDBALL_CD": ["F", ""],
        }
    )
    prepped = prepare_retrosheet_events(retro_raw)
    res = sp.calculate_suite(prepped, suite=MetricSuite.TRADITIONAL_BATTING, by="player_id")
    row = res.df.row(0, named=True)
    assert math.isclose(row["avg"], 0.500, rel_tol=1e-9)
    assert math.isclose(row["slg"], 2.000, rel_tol=1e-9)

    # Statcast pitch-level preset
    sc_raw = pl.DataFrame(
        {
            "player_name": ["Ohtani", "Ohtani"],
            "description": ["called_strike", "hit_into_play"],
            "events": [None, "home_run"],
            "zone": [5, 4],
            "bb_type": [None, "fly_ball"],
            "launch_speed": [None, 108.5],
            "launch_angle": [None, 28.0],
            "launch_speed_angle": [None, 6],
        }
    )
    sc_prepped = prepare_statcast_pitches(sc_raw)
    sc_res = sp.calculate_available(sc_prepped, by="player_name")
    sc_row = sc_res.df.row(0, named=True)
    assert math.isclose(sc_row["csw_pct"], 0.500, rel_tol=1e-9)
    assert math.isclose(sc_row["hard_hit_pct"], 1.000, rel_tol=1e-9)
    assert math.isclose(sc_row["barrel_pct"], 1.000, rel_tol=1e-9)

    # Custom YAML metric compilation
    yaml_def = """
metrics:
  - name: power_speed_num
    display_name: "PSN"
    category: batting
    required_columns: [hr, sb]
    formula: "(2 * hr * sb) / (hr + sb)"
    citation: "Bill James Power-Speed Number"
"""
    specs = load_custom_metrics_yaml(yaml_def)
    assert len(specs) == 1
    psn_df = pl.DataFrame({"hr": [30], "sb": [30]})
    psn_res = sp.calculate(psn_df, ["power_speed_num"])
    assert math.isclose(psn_res.df["power_speed_num"][0], 30.0, rel_tol=1e-9)


# ==============================================================================
# 8. Expectancy (RE24, Linear Weights), WAR, & Forecasting Models
# ==============================================================================
def test_re24_linear_weights_war_and_forecasting_models() -> None:
    # 1. RE24 default matrix & steal breakeven
    re24 = RunExpectancyMatrix.from_default()
    be_rate = re24.results.steal_breakeven_rate(
        0, BaseState.FIRST, BaseState.SECOND, BaseState.EMPTY
    )
    # At 0 outs, runner on 1B (0.859) stealing 2B (1.100) vs caught (1 out, empty = 0.254):
    # (0.859 - 0.254) / (1.100 - 0.254) = 0.605 / 0.846 = 0.7151
    assert 0.68 <= be_rate <= 0.75

    plays = pl.DataFrame(
        {
            "outs_before": [0, 0, 1, 1, 2],
            "base_state_before": ["---", "1--", "---", "---", "---"],
            "outs_after": [0, 0, 2, 2, 3],
            "base_state_after": ["---", "12-", "---", "---", "---"],
            "runs_on_play": [1, 0, 0, 0, 0],
            "play_outcome": ["home_run", "single", "out", "out", "out"],
        }
    )
    valued = re24.transform(plays)
    # Solo HR with 0 outs, bases empty: 1 + RE(0 outs, empty) - RE(0 outs, empty) = 1.000 run value
    assert math.isclose(valued["run_value"][0], 1.000, rel_tol=1e-9)

    lw = LinearWeightsEstimator(target_lg_obp=0.320).fit(valued)
    assert lw.results.run_values_above_out["home_run"] > 1.10
    assert lw.results.woba_weights["home_run"] > lw.results.woba_weights["single"] > 0.0

    # 2. WARFramework
    war_calc = WARFramework(season=2024)
    pos_war = war_calc.calculate_position_player_scalar(
        pa=650, batting_runs=35.0, baserunning_runs=4.0, fielding_runs=8.0, position="SS"
    )
    assert pos_war.war > 6.5

    # 3. MarcelProjector
    hist_df = pl.DataFrame(
        {
            "player_id": ["p1", "p1", "p1", "p2", "p2", "p2"],
            "season": [2022, 2023, 2024, 2022, 2023, 2024],
            "age": [25, 26, 27, 29, 30, 31],
            "pa": [600, 620, 640, 550, 540, 530],
            "hr": [35, 38, 42, 12, 10, 9],
            "bb": [70, 75, 80, 40, 38, 35],
            "so": [130, 125, 120, 90, 95, 100],
            "h": [160, 165, 175, 140, 135, 130],
            "b2": [30, 32, 35, 25, 22, 20],
            "b3": [2, 3, 2, 1, 1, 0],
        }
    )
    marcel = MarcelProjector(target_season=2025).fit(hist_df)
    proj = marcel.predict()
    assert marcel.results.n_players_projected == 2
    assert (
        proj.filter(pl.col("player_id") == "p1")["proj_hr"][0]
        > proj.filter(pl.col("player_id") == "p2")["proj_hr"][0]
    )

    # 4. Log5Model
    assert math.isclose(Log5Model.team_matchup_prob(0.500, 0.500), 0.500, rel_tol=1e-9)
    assert Log5Model.batter_pitcher_matchup_rate(0.300, 0.280, 0.250) > 0.300

    # 5. MarkovChainModel & MonteCarloSimulator
    mc_chain = MarkovChainModel().fit(p_1b=0.15, p_2b=0.05, p_3b=0.005, p_hr=0.035, p_bb=0.09)
    assert 3.5 <= mc_chain.results.expected_runs_per_9_innings <= 6.5

    sim = MonteCarloSimulator(n_simulations=300, seed=42)
    sim_res = sim.simulate(p_1b=0.15, p_2b=0.05, p_3b=0.005, p_hr=0.035, p_bb=0.09)
    assert abs(sim_res.mean_runs_per_game - mc_chain.results.expected_runs_per_9_innings) < 0.6

    # 6. Uncertainty intervals
    ci_bin = binomial_rate_interval(180, 600)
    assert ci_bin.ci_lower < 0.300 < ci_bin.ci_upper
    ci_boot = bootstrap_interval([0.280, 0.300, 0.310, 0.295, 0.315], n_resamples=200, seed=42)
    assert ci_boot.ci_lower <= ci_boot.estimate <= ci_boot.ci_upper


# ==============================================================================
# 9. Declarative YAML SourceTranslator & Custom Nomenclature Registry Tests
# ==============================================================================
def test_declarative_yaml_source_translator_and_nomenclature() -> None:
    # 1. Register custom column nomenclature via YAML
    custom_nomenclature_yaml = """
canonical_aliases:
  hr: ["dingers_hit"]
  bb: ["free_passes"]
  so: ["whiff_outs"]
  outs: ["total_outs_recorded"]
"""
    sp.register_column_aliases_yaml(custom_nomenclature_yaml)
    custom_pit_df = pl.DataFrame(
        {
            "player_id": ["p_custom"],
            "dingers_hit": [15],
            "free_passes": [40],
            "whiff_outs": [200],
            "total_outs_recorded": [540],  # 180.0 IP
        }
    )
    res_fip = sp.calculate(custom_pit_df, [Metric.FIP, Metric.K_PER_9, Metric.BB_PER_9])
    assert math.isclose(res_fip.df["k_per_9"][0], 10.0, rel_tol=1e-9)
    assert math.isclose(res_fip.df["bb_per_9"][0], 2.0, rel_tol=1e-9)

    # 2. Define a completely custom provider schema translator in YAML (e.g., KBO / College TrackMan feed)
    custom_provider_yaml = """
presets:
  college_trackman:
    description: "Custom college pitch & play feed translator"
    column_map:
      BatterId: "player_id"
    constant_rules:
      pitches: 1
    value_rules:
      - source_col: "PitchCall"
        values: ["StrikeSwinging", "FoulBall", "InPlay"]
        target_col: "swings"
      - source_col: "PitchCall"
        values: ["StrikeSwinging"]
        target_col: "whiffs"
      - source_col: "PitchCall"
        values: ["StrikeCalled"]
        target_col: "called_strikes"
      - source_col: "PlayResult"
        values: ["Single", "Double", "Triple", "HomeRun", "Out", "Strikeout", "Walk"]
        target_col: "pa"
      - source_col: "PlayResult"
        values: ["Single", "Double", "Triple", "HomeRun", "Out", "Strikeout"]
        target_col: "ab"
      - source_col: "PlayResult"
        values: ["Single", "Double", "Triple", "HomeRun"]
        target_col: "h"
      - source_col: "PlayResult"
        values: ["HomeRun"]
        target_col: "hr"
"""
    translators = sp.load_source_translator_yaml(custom_provider_yaml)
    assert len(translators) == 1

    college_df = pl.DataFrame(
        {
            "BatterId": ["col_1", "col_1", "col_1", "col_1"],
            "PitchCall": ["StrikeCalled", "StrikeSwinging", "InPlay", "InPlay"],
            "PlayResult": ["None", "None", "HomeRun", "Out"],
        }
    )
    res_col = sp.calculate(
        college_df,
        [Metric.AVG, Metric.CSW_PCT, Metric.WHIFF_PCT],
        preset="college_trackman",
        by="player_id",
    )
    row = res_col.df.row(0, named=True)
    # 1 hit in 2 AB -> AVG = 0.500
    assert math.isclose(row["avg"], 0.500, rel_tol=1e-9)
    # 1 called strike + 1 swinging strike out of 4 pitches -> CSW% = 0.500
    assert math.isclose(row["csw_pct"], 0.500, rel_tol=1e-9)
    # 1 whiff out of 3 swings -> Whiff% = 1/3
    assert math.isclose(row["whiff_pct"], 1.0 / 3.0, rel_tol=1e-9)


# ==============================================================================
# 10. 100% Metric & MetricSuite Exhaustive Audit + RE288 & WinProbabilityModel
# ==============================================================================
def test_all_registered_metrics_and_suites_audit() -> None:
    """Verify every single Metric enum member and MetricSuite enum member computes cleanly."""
    omni_df = pl.DataFrame(
        {
            "player_id": ["omni_1", "omni_2"],
            "g": [162, 162],
            "gs": [32, 32],
            "pa": [680, 620],
            "ab": [580, 540],
            "r": [110, 85],
            "h": [175, 145],
            "b1": [105, 95],
            "b2": [35, 28],
            "b3": [3, 2],
            "hr": [32, 20],
            "rbi": [105, 78],
            "bb": [85, 65],
            "ibb": [8, 3],
            "ubb": [77, 62],
            "hbp": [7, 6],
            "sh": [1, 2],
            "sf": [7, 7],
            "ci": [0, 0],
            "so": [135, 125],
            "gidp": [12, 14],
            "roe": [4, 3],
            "sb": [24, 12],
            "cs": [5, 4],
            "outs": [576, 540],
            "bf": [760, 740],
            "ra": [58, 72],
            "er": [54, 68],
            "w": [16, 12],
            "l": [5, 8],
            "cg": [1, 0],
            "sho": [1, 0],
            "qs": [22, 18],
            "sv": [5, 3],
            "bs": [1, 1],
            "hld": [2, 1],
            "wp": [4, 6],
            "bk": [0, 1],
            "pitches": [2900, 2800],
            "swings": [1400, 1350],
            "whiffs": [380, 310],
            "called_strikes": [510, 480],
            "strike_pitches": [1930, 1840],
            "fouls": [520, 510],
            "contacts": [1020, 1040],
            "zone_pitches": [1420, 1380],
            "out_zone_pitches": [1480, 1420],
            "zone_swings": [960, 930],
            "out_zone_swings": [440, 420],
            "zone_contacts": [810, 800],
            "out_zone_contacts": [210, 240],
            "first_pitch_swings": [230, 220],
            "first_pitch_strikes": [470, 450],
            "two_strike_so": [135, 125],
            "two_strike_pitches": [620, 610],
            "two_strike_out_zone_swings": [110, 105],
            "two_strike_out_zone_pitches": [340, 330],
            "meatball_swings": [165, 155],
            "meatball_pitches": [210, 205],
            "bbe": [420, 430],
            "gb": [185, 195],
            "fb": [135, 140],
            "ld": [85, 80],
            "pu": [15, 15],
            "pull_bbe": [175, 170],
            "cent_bbe": [145, 150],
            "oppo_bbe": [100, 110],
            "hard_hit_bbe": [195, 165],
            "sweet_spot_bbe": [155, 145],
            "barrels": [48, 32],
            "ev_sum": [38640.0, 38270.0],
            "ev_count": [420, 430],
            "ev_max": [116.4, 112.1],
            "xba_sum": [168.0, 140.0],
            "xslg_sum": [310.0, 240.0],
            "xwoba_sum": [255.0, 210.0],
            "xwoba_count": [670, 610],
            "velo_sum": [278400.0, 263200.0],
            "velo_count": [2900, 2800],
            "spin_sum": [7105000.0, 6580000.0],
            "spin_count": [2900, 2800],
            "ext_sum": [19140.0, 18200.0],
            "ext_count": [2900, 2800],
            "ivb_sum": [49300.0, 42000.0],
            "hb_sum": [-26100.0, 22400.0],
            "break_count": [2900, 2800],
            "eff_velo_sum": [281300.0, 266000.0],
            "eff_velo_count": [2900, 2800],
            "vaa_sum": [-13630.0, -14560.0],
            "vaa_count": [2900, 2800],
            "haa_sum": [-5800.0, 4200.0],
            "haa_count": [2900, 2800],
            "pitch_rv_sum": [-28.5, -14.0],
            "xbt": [22, 14],
            "xbt_opp": [48, 42],
            "gidp_opp": [125, 118],
            "ubr": [3.2, -0.8],
            "po": [310, 290],
            "a": [15, 18],
            "e": [3, 4],
            "dp": [4, 5],
            "tp": [0, 0],
            "pb": [2, 3],
            "inn_outs_fld": [4200, 4100],
            "sb_att_against": [45, 50],
            "cs_by_catcher": [14, 15],
            "bip_against": [420, 430],
            "bip_outs_made": [298, 295],
            "re24": [48.5, 15.2],
            "game_wpa": [0.08, -0.07],
            "is_reliever": [True, True],
            "bases_advanced": [900, 700],
            "base_advance_opps": [2400, 2200],
            "wpa": [4.8, 1.6],
            "li_sum": [714.0, 620.0],
            "wpa_li_sum": [4.2, 1.7],
            "rs": [815, 745],
        }
    )

    # 1. Verify every Metric enum member is registered and evaluates to finite non-null values
    per_game = [Metric.GAME_SCORE, Metric.GAME_SCORE_V2, Metric.SHUTDOWN, Metric.MELTDOWN]
    all_metrics = [m for m in Metric if m not in per_game]
    assert len(all_metrics) + len(per_game) >= 105
    per_game_res = sp.calculate(omni_df, per_game, season=2024)  # one row per game, never grouped
    assert all(m.value in per_game_res.df.columns for m in per_game)
    res_all = sp.calculate(omni_df, all_metrics, by="player_id", season=2024)
    for m in all_metrics:
        assert m.value in res_all.df.columns, f"Missing computed column for {m}"
        vals = res_all.df[m.value].to_list()
        assert all(v is not None and not math.isnan(v) and not math.isinf(v) for v in vals), (
            f"Invalid output for {m}: {vals}"
        )

    # 2. Verify every MetricSuite enum member expands and evaluates cleanly
    for suite in MetricSuite:
        suite_res = sp.calculate_suite(omni_df, suite, by="player_id", season=2024, strict=True)
        assert len(suite_res.requested_metrics) > 0

    # 3. Verify CalculationResult methods, WAR pitcher dataframe, RE24 fit, and registry helpers
    assert "wRC+" in res_all.summary()
    assert len(res_all.to_pandas()) == 2
    assert res_all.to_arrow().num_rows == 2
    assert sp.describe(Metric.WRC_PLUS).display_name == "wRC+"
    assert "wRAA" in sp.formula(Metric.WRC_PLUS)
    assert len(sp.search_metrics(requires_column="hr")) > 5
    assert sp.get_park_factor("COL").basic_5yr > 105
    pit_line = pl.DataFrame(
        {
            "player_id": ["p"],
            "outs": [540],
            "g": [30],
            "gs": [30],
            "hr": [20],
            "bb": [40],
            "hbp": [5],
            "so": [180],
        }
    )
    pit_war_df = sp.WARFramework(season=2024).calculate_pitcher_war_df(pit_line)
    assert "pitcher_war" in pit_war_df.columns
    re24_fitted = sp.RunExpectancyMatrix(prior_strength=10.0).fit(
        pl.DataFrame(
            {
                "game_id": ["g1", "g1"],
                "inning": [1, 1],
                "half_inning": ["top", "top"],
                "outs_before": [0, 0],
                "on_1b": [False, True],
                "on_2b": [False, False],
                "on_3b": [False, False],
                "runs_on_play": [0, 2],
            }
        )
    )
    assert re24_fitted.results.total_plays == 2


def test_re288_count_expectancy_matrix() -> None:
    """Verify the 288-state CountExpectancyMatrix (RE288)."""
    pitches_df = pl.DataFrame(
        {
            "pa_id": [1, 1],
            "outs_before": [0, 0],
            "base_state_before": ["---", "---"],
            "balls": [0, 0],
            "strikes": [0, 1],
            "outs_after": [0, 0],
            "base_state_after": ["---", "---"],
            "balls_after": [0, 1],
            "strikes_after": [1, 1],
            "runs_on_play": [0, 0],
            "runs_rest_of_inning": [1.0, 1.0],
        }
    )
    fitted_re288 = sp.CountExpectancyMatrix().fit(pitches_df)
    assert fitted_re288.results.total_plate_appearances == 1
    assert len(fitted_re288.results.state_expectancy) == 2


def test_telemetry_rolling_physics_and_cli() -> None:
    """Verify ExecutionProfile telemetry, multi-backend benchmark(), calculate_rolling(), VAA/IVB/HB physics, and CLI."""
    from sabermetricspy.cli import main as cli_main

    # 1. Rolling window additive calculation (window=2)
    game_logs = pl.DataFrame(
        {
            "player_id": ["p1", "p1", "p1"],
            "game_seq": [1, 2, 3],
            "ab": [2, 6, 4],
            "h": [
                2,
                0,
                2,
            ],  # Game 1: 2/2 (1.000), Game 2: 0/6 (0.000) -> 2-game sum = 2/8 = 0.250 (NOT (1.0+0.0)/2 = 0.500!)
            "b2": [0, 0, 1],
            "b3": [0, 0, 0],
            "hr": [1, 0, 0],
            "bb": [0, 0, 0],
        }
    )
    roll_res = sp.calculate_rolling(
        game_logs,
        [Metric.AVG, Metric.SLG],
        window=2,
        by="player_id",
        order_by="game_seq",
    )
    assert roll_res.profile.backend == "polars"
    assert roll_res.profile.rows_in == 3
    assert roll_res.profile.total_ms > 0.0
    # At game_seq == 2, 2-game cumulative hits = 2, 2-game cumulative AB = 8 -> AVG = 0.250
    assert math.isclose(roll_res.df["avg"][1], 0.250, rel_tol=1e-9)

    # 2. Multi-backend benchmark
    bench = sp.benchmark(rows=2_000, groups=50, warmup=0, repeats=1)
    assert len(bench.summary_df) == 4
    assert "polars" in bench.format_table()

    # 3. Pitch-tracking physics (VAA, IVB, HB, Total Break) & Statcast Expected via preset='statcast'
    statcast_df = pl.DataFrame(
        {
            "pitcher": [101, 101],
            "batter": [202, 202],
            "release_speed": [96.0, 98.0],
            "effective_speed": [96.5, 98.5],
            "release_spin_rate": [2400, 2500],
            "release_extension": [6.5, 6.7],
            "pfx_x": [-0.5, -0.5],  # -6.0 inches HB
            "pfx_z": [1.5, 1.5],  # +18.0 inches IVB
            "vy0": [-140.0, -142.0],
            "vz0": [-4.0, -4.2],
            "ay": [31.0, 32.0],
            "az": [-13.0, -13.5],
            "description": ["swinging_strike", "hit_into_play"],
            "zone": [5, 4],
            "events": ["strikeout", "home_run"],
            "bb_type": ["", "fly_ball"],
            "launch_speed": [None, 108.0],
            "launch_angle": [None, 26.0],
            "estimated_ba_using_speedangle": [0.0, 0.900],
            "estimated_slg_using_speedangle": [0.0, 3.500],
            "estimated_woba_using_speedangle": [0.0, 1.800],
        }
    )
    phys_res = sp.calculate_suite(
        statcast_df,
        [MetricSuite.PITCH_PHYSICS, MetricSuite.STATCAST_EXPECTED],
        by="pitcher_id",
        preset="statcast",
    )
    prow = phys_res.df.row(0, named=True)
    assert math.isclose(prow["avg_velo"], 97.0, rel_tol=1e-9)
    assert math.isclose(prow["ivb"], 18.0, rel_tol=1e-9)
    assert math.isclose(prow["hb"], -6.0, rel_tol=1e-9)
    assert -6.5 <= prow["vaa"] <= -3.5
    assert math.isclose(prow["xba"], 0.450, rel_tol=1e-9)
    assert math.isclose(prow["xwoba"], 0.900, rel_tol=1e-9)

    # 4. CLI subcommands
    assert cli_main(["info", "wrc_plus"]) == 0
    assert cli_main(["list", "--category", "pitch_physics"]) == 0
    assert cli_main(["suites"]) == 0
    assert cli_main(["benchmark", "--rows", "1000", "--groups", "25", "--repeats", "1"]) == 0
    assert cli_main(["benchmark", "--registered", "--repeats", "1", "--rows", "200"]) != 2


def test_decorator_telemetry_and_benchmark_registry() -> None:
    """Verify @profiled decorator, sb.telemetry PerformanceTracker, and @register_benchmark."""

    @sp.profiled(category="custom_user")
    def custom_pipeline(df: pl.DataFrame) -> pl.DataFrame:
        res = sp.calculate(df, [Metric.AVG, Metric.OBP, Metric.SLG])
        return res.df

    sample_df = pl.DataFrame(
        {"ab": [10, 20], "h": [3, 7], "b2": [1, 2], "b3": [0, 0], "hr": [1, 1], "bb": [2, 3]}
    )
    with sp.telemetry.session() as tracker:
        out_df = custom_pipeline(sample_df)
        assert len(out_df) == 2
        spans = tracker.spans
        # Should have recorded both `calculate` (category='engine') and `custom_pipeline` (category='custom_user')
        span_categories = {s.category for s in spans}
        assert "engine" in span_categories
        assert "custom_user" in span_categories
        summary_df = tracker.summary_df()
        assert len(summary_df) >= 2
        table_str = tracker.format_table()
        assert "custom_pipeline" in table_str
        assert "calculate" in table_str

    # Register a custom benchmark with @register_benchmark and run registered benchmarks
    @sp.register_benchmark(name="custom.quick_avg", category="custom_test", default_rows=500)
    def _bench_custom(rows: int = 500) -> pl.DataFrame:
        df = pl.DataFrame({"ab": [4] * rows, "h": [1] * rows})
        return sp.calculate(df, Metric.AVG).df

    entries = sp.get_registered_benchmarks()
    assert "custom.quick_avg" in entries
    assert "engine.calculate_suite" in entries
    assert "expectancy.win_expectancy_fit" in entries
    assert "uncertainty.empirical_bayes" in entries

    reg_res = sp.run_registered_benchmarks(repeats=1, category="custom_test")
    reg_df = reg_res.summary_df()
    assert len(reg_df) == 1
    assert reg_df["name"][0] == "custom.quick_avg"
    assert reg_df["rows"][0] == 500
    assert reg_df["median_ms"][0] > 0.0
    assert "custom.quick_avg" in reg_res.format_table()


def test_advanced_metrics_and_modeled_estimators() -> None:
    """Verify 105+ metrics, vectorized Position-Player WAR, and EmpiricalBayesShrinker."""
    with sp.telemetry.session() as tracker:
        # 1. Mathematical identities on newly added metrics (GPA, ERR_PCT, BAUER_UNITS, CLUTCH, QERA, DIPS_BOP_PCT)
        df_ident = pl.DataFrame(
            {
                "ab": [500],
                "pa": [600],
                "h": [150],
                "b2": [30],
                "b3": [5],
                "hr": [25],
                "bb": [70],
                "hbp": [5],
                "sf": [5],
                "so": [110],
                "po": [280],
                "a": [20],
                "e": [6],
                "spin_sum": [240000.0],
                "spin_count": [100],
                "velo_sum": [9600.0],
                "velo_count": [100],
                "wpa": [3.0],
                "li_sum": [900.0],  # pLI = 900 / 600 = 1.5
                "wpa_li_sum": [1.8],  # Clutch = (3.0 / 1.5) - 1.8 = 0.2
                "bf": [700],
                "gb": [220],
                "bbe": [480],
            }
        )
        res_id = sp.calculate(
            df_ident,
            [
                Metric.OBP,
                Metric.SLG,
                Metric.GPA,
                Metric.FPCT,
                Metric.ERR_PCT,
                Metric.BAUER_UNITS,
                Metric.PLI,
                Metric.CLUTCH,
                Metric.QERA,
                Metric.DIPS_BOP_PCT,
            ],
        )
        r0 = res_id.df.row(0, named=True)
        assert math.isclose(r0["gpa"], (1.8 * r0["obp"] + r0["slg"]) / 4.0, rel_tol=1e-9)
        assert math.isclose(r0["fpct"] + r0["err_pct"], 1.0, rel_tol=1e-9)
        assert math.isclose(r0["bauer_units"], 2400.0 / 96.0, rel_tol=1e-9)
        assert math.isclose(r0["pli"], 1.5, rel_tol=1e-9)
        assert math.isclose(r0["clutch"], 0.2, rel_tol=1e-9)
        assert math.isclose(r0["dips_bop_pct"], (25 + 70 + 5 + 110) / 700.0, rel_tol=1e-9)

        # 2. Vectorized Position-Player WAR matches scalar WAR exactly
        war_fw = sp.WARFramework(season=2024)
        scalar_war = war_fw.calculate_position_player_scalar(
            pa=650,
            batting_runs=42.0,
            baserunning_runs=4.5,
            fielding_runs=8.0,
            position="SS",
            league_runs=0.0,
        )
        pos_df = pl.DataFrame(
            {
                "player_id": ["ss_star"],
                "pa": [650],
                "wraa": [42.0],
                "bsr": [4.5],
                "fielding_runs": [8.0],
                "position": ["SS"],
                "league_runs": [0.0],
            }
        )
        war_df_out = war_fw.calculate_position_player_df(pos_df)
        assert math.isclose(war_df_out["war"][0], scalar_war.war, rel_tol=1e-9)
        assert math.isclose(
            war_df_out["runs_above_replacement"][0], scalar_war.runs_above_replacement, rel_tol=1e-9
        )

        # 3. EmpiricalBayesShrinker: small sample (4/10 = .400) shrinks much harder toward ~.260 than large sample (200/500 = .400)
        eb_df = pl.DataFrame(
            {
                "player_id": ["small_sample", "large_sample", "avg_1", "avg_2", "avg_3", "avg_4"],
                "h": [4, 200, 130, 125, 135, 128],
                "ab": [10, 500, 500, 500, 500, 500],
            }
        )
        eb = sp.EmpiricalBayesShrinker(
            success_col="h", trials_col="ab", stabilization_trials=300.0
        ).fit(eb_df)
        eb_out = eb.transform(eb_df)
        assert eb.results.stabilization_trials == 300.0
        assert eb_out["eb_rate"][0] < eb_out["eb_rate"][1]
        assert eb_out["eb_shrinkage"][0] > 0.95  # 300 / 310
        assert eb_out["eb_ci_lower"][1] < eb_out["eb_rate"][1] < eb_out["eb_ci_upper"][1]

        # 4. Verify @profiled spans were automatically recorded for all new estimators
        cats = {s.category for s in tracker.spans}
        assert {"engine", "valuation", "uncertainty"}.issubset(cats)
