"""Plate-discipline rates computed from a recorded Statcast sample must agree with the FanGraphs published rates.

Sample: every regular-season pitch thrown by Tarik Skubal in 2024 (Baseball Savant CSV export). The pitch
counts (2,868 pitches, 1,985 strikes, 883 balls) and Called-Strike% reproduce FanGraphs exactly; the zone
rates agree within the stated tolerance because FanGraphs applies its own pitch classification (it excludes
bunts and uses only pitches with a tracked location).
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import polars as pl
import pytest
from golden_loader import load_entries

import sabermetricspy as sp
from sabermetricspy import Metric
from sabermetricspy.presets import prepare_statcast_pitches

ENTRY = load_entries("plate_discipline.yaml")[0]
SAMPLE = Path(__file__).parent / "fixtures" / "statcast" / "skubal_2024_pitches.csv"


@pytest.fixture(scope="module")
def raw() -> pl.DataFrame:
    return pl.read_csv(SAMPLE, infer_schema_length=0)


def _rates(raw: pl.DataFrame) -> dict[str, float]:
    prepared = prepare_statcast_pitches(raw)
    metrics = [
        Metric.SWING_PCT,
        Metric.Z_SWING_PCT,
        Metric.O_SWING_PCT,
        Metric.ZONE_PCT,
        Metric.CONTACT_PCT,
        Metric.Z_CONTACT_PCT,
        Metric.O_CONTACT_PCT,
        Metric.SWSTR_PCT,
        Metric.CSTR_PCT,
        Metric.CSW_PCT,
    ]
    return sp.calculate(prepared, metrics, by="pitcher_id").df.row(0, named=True)


def test_sample_gate_counts_match_the_published_counts(raw: pl.DataFrame) -> None:
    c = ENTRY["counts"]
    assert raw.height == c["pitches"]
    assert raw.filter(pl.col("type").is_in(["S", "X"])).height == c["strikes"]
    assert raw.filter(pl.col("type") == "B").height == c["balls"]
    assert raw.filter(pl.col("zone").is_not_null()).height == c["located_pitches"]
    first = raw.filter((pl.col("balls") == "0") & (pl.col("strikes") == "0"))
    assert first.height == c["sample_first_pitches"]
    assert first.filter(pl.col("type").is_in(["S", "X"])).height == c["first_pitch_strikes"]


def test_published_rates_are_integer_counts_of_the_sample() -> None:
    """Recomputation gate on the published values: each is a whole number of pitches over its denominator."""
    c, p = ENTRY["counts"], ENTRY["published"]
    for rate, denom in (
        (p["cstr_pct"], c["pitches"]),
        (p["swing_pct_pi"], c["located_pitches"]),
        (p["f_strike_pct"], c["plate_appearances"]),
    ):
        assert rate * denom == pytest.approx(round(rate * denom), abs=1e-3)


def test_called_strike_rate_is_exact(raw: pl.DataFrame) -> None:
    got = _rates(raw)["cstr_pct"]
    assert got == pytest.approx(ENTRY["published"]["cstr_pct"], abs=ENTRY["tolerance"]["cstr_pct"])


def test_first_pitch_strike_rate_is_exact(raw: pl.DataFrame) -> None:
    first = raw.filter((pl.col("balls") == "0") & (pl.col("strikes") == "0"))
    strikes = first.filter(pl.col("type").is_in(["S", "X"])).height
    assert strikes == ENTRY["counts"]["first_pitch_strikes"]
    frame = pl.DataFrame(
        {
            "player_id": ["p"],
            "first_pitch_strikes": [strikes],
            "pa": [ENTRY["counts"]["plate_appearances"]],
        }
    )
    got = sp.calculate(frame, [Metric.FP_STRIKE_PCT]).df.row(0, named=True)["fp_strike_pct"]
    assert got == pytest.approx(
        ENTRY["published"]["f_strike_pct"], abs=ENTRY["tolerance"]["f_strike_pct"]
    )


@pytest.mark.parametrize(
    ("column", "published"),
    [
        ("swing_pct", "swing_pct_pi"),
        ("zone_pct", "zone_pct_sc"),
        ("o_swing_pct", "o_swing_pct_sc"),
        ("z_swing_pct", "z_swing_pct_sc"),
        ("o_contact_pct", "o_contact_pct_sc"),
        ("z_contact_pct", "z_contact_pct_sc"),
        ("contact_pct", "contact_pct"),
        ("swstr_pct", "swstr_pct"),
        ("csw_pct", "csw_pct"),
    ],
)
def test_zone_rates_agree_within_the_stated_tolerance(
    raw: pl.DataFrame, column: str, published: str
) -> None:
    row: dict[str, Any] = _rates(raw)
    assert row[column] == pytest.approx(
        ENTRY["published"][published], abs=ENTRY["tolerance"][published]
    ), column
