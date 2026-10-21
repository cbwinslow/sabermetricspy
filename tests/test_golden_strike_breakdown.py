"""Strike-breakdown, first-pitch, meatball, HAA and per-PA rates reproduce published values (ADR-0050)."""

from __future__ import annotations

from pathlib import Path

import polars as pl
import pytest
import yaml

import sabermetricspy as sp
from sabermetricspy import Metric
from sabermetricspy.presets import prepare_statcast_pitches

HERE = Path(__file__).parent
REF = yaml.safe_load((HERE / "golden" / "strike_breakdown_rates.yaml").read_text("utf-8"))
ROOT = HERE.parent


def _prepared(sample: str) -> pl.DataFrame:
    raw = pl.read_csv(ROOT / sample, infer_schema_length=0)
    return prepare_statcast_pitches(raw)


@pytest.fixture(scope="module")
def skubal() -> pl.DataFrame:
    return _prepared(REF["baseball_reference_skubal_2024"]["sample"])


def test_strike_count_matches_baseball_reference(skubal: pl.DataFrame) -> None:
    assert skubal["strike_pitches"].sum() == REF["baseball_reference_skubal_2024"]["strikes"]


def test_i_to_str_reproduces_baseball_reference(skubal: pl.DataFrame) -> None:
    got = sp.calculate(skubal.select("bbe", "strike_pitches").sum(), [Metric.I_TO_STR]).df
    assert (
        round(100 * got["i_to_str"][0], 1) == REF["baseball_reference_skubal_2024"]["i_to_str_pct"]
    )


def test_f_to_str_reproduces_baseball_reference(skubal: pl.DataFrame) -> None:
    got = sp.calculate(skubal.select("fouls", "strike_pitches").sum(), [Metric.F_TO_STR]).df
    assert (
        round(100 * got["f_to_str"][0], 1) == REF["baseball_reference_skubal_2024"]["f_to_str_pct"]
    )


def test_foul_bunts_are_fouls(skubal: pl.DataFrame) -> None:
    """Counting only `foul` gives 525 of 1,985 (26.4 percent), which misses Baseball-Reference's 26.6."""
    assert skubal["fouls"].sum() == 529


def test_first_pitch_swing_split_matches_baseball_reference(skubal: pl.DataFrame) -> None:
    ref = REF["baseball_reference_skubal_2024"]
    swung, took = ref["first_pitch_swung"], ref["first_pitch_took"]
    assert skubal["first_pitch_swings"].sum() == swung
    frame = pl.DataFrame({"first_pitch_swings": [swung], "pa": [swung + took]})
    got = sp.calculate(frame, [Metric.FP_SWING_PCT]).df["fp_swing_pct"][0]
    assert got == pytest.approx(swung / (swung + took), abs=1e-12)


@pytest.mark.parametrize("pitcher", ["skubal_2024", "cabrera_2024"])
def test_meatball_rates_reproduce_savant(pitcher: str) -> None:
    ref = REF["savant_meatball"][pitcher]
    frame = _prepared(ref["sample"])
    located = int(frame["located_pitches"].sum())
    assert located == ref["located_pitches"]
    assert round(100 * int(frame["meatball_pitches"].sum()) / located, 1) == ref["meatball_pct"]
    got = sp.calculate(
        frame.select("meatball_swings", "meatball_pitches").sum(), [Metric.MEATBALL_SWING_PCT]
    ).df
    assert round(100 * got["meatball_swing_pct"][0], 1) == ref["meatball_swing_pct"]


def test_haa_reproduces_chamberlain_four_seamer_table() -> None:
    ref = REF["chamberlain_haa_2023"]
    raw = pl.read_csv(ROOT / ref["sample"], infer_schema_length=10000)
    got = sp.calculate(prepare_statcast_pitches(raw), [Metric.HAA], by="pitcher").df
    by_pitcher = dict(zip(got["pitcher"], got["haa"], strict=True))
    assert set(by_pitcher) == set(ref["pitchers"])
    for pitcher, value in by_pitcher.items():
        assert value == pytest.approx(ref["published_degrees"], abs=ref["tolerance"]), pitcher


def test_hr_pct_reproduces_baseball_reference() -> None:
    ref = REF["baseball_reference_hr_pct"]
    got = sp.calculate(pl.DataFrame({"hr": [ref["hr"]], "pa": [ref["pa"]]}), [Metric.HR_PCT]).df
    assert round(100 * got["hr_pct"][0], 1) == ref["hr_pct"]


def test_r_per_pa_equals_fangraphs_guts_in_every_season() -> None:
    """League R / TBF rounds to the Guts! R/PA in all 37 seasons (1990 to 2026)."""
    guts = yaml.safe_load((HERE / "golden" / "guts_snapshot.yaml").read_text("utf-8"))["seasons"]
    totals = yaml.safe_load((HERE / "golden" / "league_totals_snapshot.yaml").read_text("utf-8"))[
        "pitching"
    ]
    assert len(totals) == 37
    for season, row in totals.items():
        frame = pl.DataFrame({"r": [row["r"]], "pa": [row["tbf"]]})
        got = sp.calculate(frame, [Metric.R_PER_PA]).df["r_per_pa"][0]
        assert round(got, 3) == guts[season]["lg_r_per_pa"], season
