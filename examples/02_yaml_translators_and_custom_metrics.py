"""Demo 02: Provider-Agnostic YAML Translators (retrosheetpy, Statcast, Custom) & Custom YAML Metrics.

Run with:
    uv run python examples/02_yaml_translators_and_custom_metrics.py
"""

from __future__ import annotations

import sys

import polars as pl

import sabermetricspy as sb
from sabermetricspy import Metric, MetricSuite


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    print("=" * 88)
    print("SABERMETRICSPY DEMO 02: YAML SOURCE TRANSLATORS & DECLARATIVE CUSTOM METRICS")
    print("=" * 88)

    # 1. Raw Retrosheet / retrosheetpy Event Schema -> Translated via YAML Preset
    raw_retrosheet = pl.DataFrame(
        {
            "BAT_ID": ["judga001", "judga001", "judga001", "judga001", "sotoj001", "sotoj001"],
            "EVENT_CD": [23, 14, 20, 3, 21, 23],  # HR, Walk, Single, Strikeout, Double, HR
            "H_CD": [4, 0, 1, 0, 2, 4],  # 4=HR, 0=No Hit, 1=1B, 0=No Hit, 2=2B, 4=HR
            "AB_FL": [True, False, True, True, True, True],
            "SH_FL": [False, False, False, False, False, False],
            "SF_FL": [False, False, False, False, False, False],
            "RBI_CT": [2, 0, 1, 0, 1, 3],
            "BATTEDBALL_CD": ["F", "", "L", "", "L", "F"],
        }
    )

    retro_res = sb.calculate_suite(
        raw_retrosheet,
        MetricSuite.TRADITIONAL_BATTING,
        by="player_id",
        preset="retrosheetpy_events",
    )
    print("\n[1] Raw Retrosheet Event Records Evaluated Directly via `preset='retrosheetpy_events'`:")
    print(
        retro_res.df.select(
            "player_id", "pa", "ab", "h", "b2", "hr", "rbi", "bb", "so", "avg", "obp", "slg", "ops"
        )
    )

    # 2. Raw Statcast Pitch-by-Pitch Schema -> Translated via YAML Preset
    raw_statcast = pl.DataFrame(
        {
            "pitcher": [669373, 669373, 669373, 669373, 669373],
            "batter": [592450, 592450, 592450, 665742, 665742],
            "description": [
                "called_strike",
                "swinging_strike",
                "ball",
                "hit_into_play",
                "swinging_strike_blocked",
            ],
            "zone": [5, 14, 12, 4, 13],
            "events": ["", "", "", "home_run", "strikeout"],
            "bb_type": ["", "", "", "fly_ball", ""],
            "launch_speed": [None, None, None, 112.4, None],
            "launch_angle": [None, None, None, 28.0, None],
            "launch_speed_angle": [None, None, None, 6, None],
        }
    )

    statcast_res = sb.calculate_suite(
        raw_statcast,
        [MetricSuite.PLATE_DISCIPLINE, MetricSuite.BATTED_BALL],
        by="pitcher_id",
        preset="statcast",
    )
    print("\n[2] Raw Statcast Pitch-by-Pitch Records Evaluated Directly via `preset='statcast'`:")
    print(
        statcast_res.df.select(
            "pitcher_id",
            "zone_pct",
            "o_swing_pct",
            "z_swing_pct",
            "whiff_pct",
            "csw_pct",
            "hard_hit_pct",
            "barrel_pct",
            "avg_ev",
        )
    )

    # 3. User-Defined Custom Provider Nomenclature via YAML String
    custom_source_yaml = """
presets:
  japan_npb_feed:
    description: "Custom NPB Japanese Baseball Feed Translator"
    column_map:
      senshu_mei: player_id
      daseki: pa
      dasu: ab
      anda: h
      niruida: b2
      sanruida: b3
      honruida: hr
      shikyu: bb
      shikyu_hbp: hbp
      gihi: sf
      sanshin: so
"""
    sb.load_source_translator_yaml(custom_source_yaml)

    npb_df = pl.DataFrame(
        {
            "senshu_mei": ["Munetaka Murakami", "Kensuke Kondoh"],
            "daseki": [612, 580],
            "dasu": [487, 465],
            "anda": [155, 146],
            "niruida": [21, 33],
            "sanruida": [1, 2],
            "honruida": [56, 26],
            "shikyu": [118, 105],
            "shikyu_hbp": [5, 6],
            "gihi": [2, 4],
            "sanshin": [128, 88],
        }
    )

    npb_res = sb.calculate(
        npb_df,
        [Metric.AVG, Metric.OBP, Metric.SLG, Metric.OPS, Metric.WOBA, Metric.WRC_PLUS],
        by="player_id",
        preset="japan_npb_feed",
        season=2024,
    )
    print("\n[3] Custom NPB Japanese Provider Schema Translated via Declarative YAML:")
    print(npb_res.df.select("player_id", "avg", "obp", "slg", "ops", "woba", "wrc_plus"))

    # 4. User-Defined Custom Research Equations Compiled from YAML into Narwhals AST
    custom_metrics_yaml = """
metrics:
  - name: power_patience_index
    display_name: "PPI"
    category: batting
    description: "Harmonic combination of Isolated Power and Walk Rate."
    formula_latex: "(2 * ISO * BB%) / (ISO + BB%)"
    formula: "(2.0 * (slg - avg) * bb_pct) / ((slg - avg) + bb_pct)"
    requires: ["avg", "slg", "bb_pct"]
    citation: "Custom Sabermetric Research Lab (2026)"
"""
    registered = sb.load_custom_metrics_yaml(custom_metrics_yaml)
    print(f"\n[4] Compiled & Registered Custom YAML Metric: {[m.metric for m in registered]}")
    ppi_res = sb.calculate(
        npb_df,
        ["avg", "slg", "bb_pct", "power_patience_index"],
        by="player_id",
        preset="japan_npb_feed",
    )
    print(ppi_res.df.select("player_id", "avg", "slg", "bb_pct", "power_patience_index"))


if __name__ == "__main__":
    main()
