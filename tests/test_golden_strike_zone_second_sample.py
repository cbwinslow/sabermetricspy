"""The geometric strike zone on a second pitcher and season (Gerrit Cole 2023), against FanGraphs' Statcast-based rates."""

from __future__ import annotations

from pathlib import Path

import polars as pl
import pytest
import yaml
from golden_loader import GOLDEN_DIR

import sabermetricspy as sp
from sabermetricspy import Metric
from sabermetricspy.presets import prepare_statcast_pitches

SAMPLE = Path(__file__).parent / "fixtures" / "statcast" / "cole_2023_zone.csv"
REF = yaml.safe_load((GOLDEN_DIR / "plate_discipline_cole_2023.yaml").read_text(encoding="utf-8"))
METRICS = {
    "zone_pct": Metric.ZONE_PCT,
    "o_swing_pct": Metric.O_SWING_PCT,
    "z_swing_pct": Metric.Z_SWING_PCT,
    "o_contact_pct": Metric.O_CONTACT_PCT,
    "z_contact_pct": Metric.Z_CONTACT_PCT,
}


def _rates(raw: pl.DataFrame) -> dict[str, float]:
    prepared = prepare_statcast_pitches(raw)
    return sp.calculate(prepared, list(METRICS.values()), by="pitcher").df.row(0, named=True)


@pytest.fixture(scope="module")
def raw() -> pl.DataFrame:
    return pl.read_csv(SAMPLE, infer_schema_length=0)


def test_sample_is_the_whole_2023_regular_season(raw: pl.DataFrame) -> None:
    assert raw.height == 3286
    assert raw["game_year"].unique().to_list() == ["2023"]
    assert raw["game_type"].unique().to_list() == ["R"]


@pytest.mark.parametrize("name", list(METRICS))
def test_geometric_zone_rates_match_fangraphs_statcast_rates(raw: pl.DataFrame, name: str) -> None:
    got = _rates(raw)[name]
    assert got == pytest.approx(REF["published"][name], abs=REF["tolerance"])


def _total_gap(rates: dict[str, float]) -> float:
    return sum(abs(rates[name] - value) for name, value in REF["published"].items())


def test_geometric_zone_is_closer_than_savants_zone_field_overall(raw: pl.DataFrame) -> None:
    geometric = _rates(raw)
    fallback = _rates(raw.drop(["plate_x", "plate_z", "sz_top", "sz_bot"]))
    assert _total_gap(geometric) < _total_gap(fallback)
