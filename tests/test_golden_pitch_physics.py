"""Pitch-physics, run-value and Statcast-expected metrics computed from the recorded Savant sample.

Published values (Baseball Savant leaderboards and FanGraphs) are in tests/golden/pitch_arsenal.yaml. Savant
rounds velocity to one decimal, spin to whole rpm and expected rates to three decimals, so each comparison
allows exactly that rounding.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import polars as pl
import pytest
import yaml
from golden_loader import GOLDEN_DIR

import sabermetricspy as sp
from sabermetricspy import Metric
from sabermetricspy.presets import prepare_statcast_pitches
from sabermetricspy.types.context import SeasonContext

REF: dict[str, Any] = yaml.safe_load(
    (GOLDEN_DIR / "pitch_arsenal.yaml").read_text(encoding="utf-8")
)
SAMPLE = Path(__file__).parent / "fixtures" / "statcast" / "skubal_2024_pitches.csv"


@pytest.fixture(scope="module")
def raw() -> pl.DataFrame:
    return pl.read_csv(SAMPLE, infer_schema_length=0)


def _calc(
    sub: pl.DataFrame, metrics: list[Metric], *, with_run_value: bool = False
) -> dict[str, Any]:
    prepared = prepare_statcast_pitches(sub)
    if with_run_value:
        # Savant's delta_run_exp is the batting side's change; the pitcher's run value is its negative.
        rv = -pl.col("delta_run_exp").cast(pl.Float64, strict=False).fill_null(0.0)
        prepared = prepared.with_columns(rv.alias("pitch_rv_sum"))
    return sp.calculate(prepared, metrics, by="pitcher_id").df.row(0, named=True)


@pytest.mark.parametrize("pitch_type", ["FF", "SI", "SL", "CH", "CU", "FS"])
def test_velocity_and_spin_match_savant(raw: pl.DataFrame, pitch_type: str) -> None:
    ref = REF["pitch_types"][pitch_type]
    row = _calc(raw.filter(pl.col("pitch_type") == pitch_type), [Metric.AVG_VELO, Metric.AVG_SPIN])
    assert row["avg_velo"] == pytest.approx(ref["avg_speed"], abs=0.05)
    assert row["avg_spin"] == pytest.approx(ref["avg_spin"], abs=0.5)


def test_four_seam_induced_and_horizontal_break_match_savant(raw: pl.DataFrame) -> None:
    row = _calc(raw.filter(pl.col("pitch_type") == "FF"), [Metric.IVB, Metric.HB])
    # Savant rounds the leaderboard to one decimal (16.2 for a 16.26 mean), so allow 0.1 inch.
    assert row["ivb"] == pytest.approx(REF["movement_ff"]["pitcher_break_z_induced"], abs=0.1)
    assert row["hb"] == pytest.approx(REF["movement_ff"]["pitcher_break_x"], abs=0.1)


@pytest.mark.parametrize("pitch_type", ["FF", "SI", "CH"])
def test_run_value_per_100_matches_savant(raw: pl.DataFrame, pitch_type: str) -> None:
    ref = REF["pitch_types"][pitch_type]
    row = _calc(
        raw.filter(pl.col("pitch_type") == pitch_type), [Metric.RV_PER_100], with_run_value=True
    )
    assert row["rv_per_100"] == pytest.approx(ref["rv_per_100"], abs=0.05)


@pytest.mark.parametrize("pitch_type", ["FF", "SI", "CH"])
def test_pitch_type_expected_rates_match_savant(raw: pl.DataFrame, pitch_type: str) -> None:
    ref = REF["pitch_types"][pitch_type]
    row = _calc(
        raw.filter(pl.col("pitch_type") == pitch_type), [Metric.XBA, Metric.XSLG, Metric.XWOBA]
    )
    assert row["xba"] == pytest.approx(ref["est_ba"], abs=0.0005)
    assert row["xslg"] == pytest.approx(ref["est_slg"], abs=0.0005)
    assert row["xwoba"] == pytest.approx(ref["est_woba"], abs=0.0005)


def test_season_xwoba_matches_the_savant_leaderboard(raw: pl.DataFrame) -> None:
    assert _calc(raw, [Metric.XWOBA])["xwoba"] == pytest.approx(
        REF["season"]["est_woba"], abs=0.0005
    )


def test_season_xba_and_xslg_run_below_the_leaderboard_by_the_sprint_speed_term(
    raw: pl.DataFrame,
) -> None:
    """Pitch-level estimates ignore sprint speed, which the leaderboard xBA/xSLG include: a bounded gap."""
    row = _calc(raw, [Metric.XBA, Metric.XSLG])
    assert 0.0 < REF["season"]["est_ba"] - row["xba"] < 0.003
    assert 0.0 < REF["season"]["est_slg"] - row["xslg"] < 0.004


def test_average_exit_velocity_uses_tracked_batted_balls_only(raw: pl.DataFrame) -> None:
    """Fouls are excluded; the mean sits 0.53 mph under FanGraphs' EV, which also appears to drop the slowest rollers."""
    row = _calc(raw, [Metric.AVG_EV])
    assert row["ev_count"] == 478  # the 481 balls in play minus 3 without a tracked exit velocity
    assert row["avg_ev"] == pytest.approx(REF["fangraphs_statcast"]["ev"], abs=0.6)
    assert row["avg_ev"] < REF["fangraphs_statcast"]["ev"]


def test_hard_hit_rate_counts_batted_balls_only(raw: pl.DataFrame) -> None:
    ref = REF["fangraphs_statcast"]
    row = _calc(raw, [Metric.HARD_HIT_PCT])
    assert row["bbe"] == ref["events"]
    assert row["hard_hit_bbe"] == ref["hard_hit"]
    assert row["hard_hit_pct"] == pytest.approx(ref["hard_hit_pct"], abs=1e-8)


def test_barrels_come_from_statcasts_launch_speed_angle(raw: pl.DataFrame) -> None:
    """Statcast labels barrels itself (launch_speed_angle == 6); the count equals FanGraphs' Barrels."""
    ref = REF["fangraphs_statcast"]
    row = _calc(raw, [Metric.BARREL_PCT])
    assert row["barrels"] == ref["barrels"]
    assert row["barrel_pct"] == pytest.approx(ref["barrel_pct"], abs=1e-8)


def test_season_xera_is_close_to_savant_but_not_equal(raw: pl.DataFrame) -> None:
    """Savant publishes no xERA formula; the library's xwOBA-to-ERA translation lands a few hundredths low."""
    prepared = prepare_statcast_pitches(raw)
    season = prepared.select(
        pl.col("xwoba_sum").cast(pl.Float64).sum(),
        pl.col("xwoba_count").cast(pl.Float64).sum(),
        pl.col("pa")
        .cast(pl.Float64)
        .sum()
        .alias("bf"),  # the preset derives PA, which equals BF here
        pl.lit(576).alias("outs"),  # 192.0 IP, from the FanGraphs leaderboard
    ).with_columns(pl.lit("p").alias("player_id"))
    ctx = SeasonContext(season=2024)
    got = sp.calculate(season, [Metric.XERA], context=ctx).df.row(0, named=True)["xera"]
    assert got == pytest.approx(REF["season"]["xera"], abs=0.1)
    assert got != pytest.approx(REF["season"]["xera"], abs=0.01), "xERA now matches: promote it"


def test_putaway_rate_matches_savant(raw: pl.DataFrame) -> None:
    for pitch_type in ("FF", "SI", "CH"):
        sub = raw.filter(pl.col("pitch_type") == pitch_type)
        two = sub.filter(pl.col("strikes") == "2")
        strikeouts = two.filter(pl.col("events").is_in(["strikeout", "strikeout_double_play"]))
        frame = pl.DataFrame(
            {
                "player_id": ["p"],
                "two_strike_so": [strikeouts.height],
                "two_strike_pitches": [two.height],
            }
        )
        got = sp.calculate(frame, [Metric.PUTAWAY_PCT]).df.row(0, named=True)["putaway_pct"]
        assert 100 * got == pytest.approx(REF["pitch_types"][pitch_type]["put_away"], abs=0.05)
