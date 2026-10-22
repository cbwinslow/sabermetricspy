"""Power-Speed Number reproduces Baseball-Reference, SABR and Wikipedia values (tests/golden/power_speed_number.yaml)."""

from __future__ import annotations

from typing import Any

import polars as pl
import pytest
from golden_loader import load_entries
from hypothesis import given
from hypothesis import strategies as st

import sabermetricspy as sp
from sabermetricspy import Metric

ENTRIES = load_entries("power_speed_number.yaml")


def _psn(hr: int, sb: int) -> float | None:
    out = sp.calculate(pl.DataFrame({"hr": [hr], "sb": [sb]}), [Metric.POWER_SPEED_NUMBER]).df
    return out["power_speed_number"][0]


def _num(hr: int, sb: int) -> float:
    value = _psn(hr, sb)
    assert value is not None
    return value


@pytest.mark.parametrize("entry", ENTRIES, ids=lambda e: e["id"])
def test_power_speed_number_matches_the_fixture(entry: dict[str, Any]) -> None:
    got = _psn(entry["inputs"]["hr"], entry["inputs"]["sb"])
    published = entry["published"]["psn"]
    if published is None:
        assert got is None
    else:
        assert got == pytest.approx(published, abs=entry["tolerance"]["psn"]), entry["id"]


def test_zero_home_runs_and_steals_is_null_not_zero() -> None:
    assert _psn(0, 0) is None


def test_career_value_uses_career_totals_not_the_mean_of_season_values() -> None:
    seasons = pl.DataFrame({"player_id": ["a", "a"], "hr": [10, 40], "sb": [30, 5]})
    got = sp.calculate(seasons, [Metric.POWER_SPEED_NUMBER], by=["player_id"]).df[
        "power_speed_number"
    ][0]
    assert got == pytest.approx(2 * 50 * 35 / 85)
    assert got != pytest.approx((2 * 10 * 30 / 40 + 2 * 40 * 5 / 45) / 2)


def test_registry_resolves_all_three_names() -> None:
    from sabermetricspy.registry import REGISTRY

    spec = REGISTRY.get(Metric.POWER_SPEED_NUMBER).spec
    assert spec.display_name == "PSN"
    assert spec.required_columns == ("hr", "sb")
    assert REGISTRY.resolve_name("PSN") == "power_speed_number"
    assert REGISTRY.resolve_name("power_speed_number") == "power_speed_number"
    assert REGISTRY.resolve_name(Metric.POWER_SPEED_NUMBER) == "power_speed_number"


counts = st.integers(min_value=1, max_value=2000)


@given(counts, counts)
def test_symmetric_and_bounded_by_the_arithmetic_mean(h: int, s: int) -> None:
    v = _num(h, s)
    assert v == pytest.approx(_num(s, h))
    assert min(h, s) - 1e-9 <= v <= (h + s) / 2 + 1e-9


@given(counts, counts, st.integers(min_value=1, max_value=20))
def test_homogeneous_of_degree_one(h: int, s: int, k: int) -> None:
    assert _num(k * h, k * s) == pytest.approx(k * _num(h, s))
