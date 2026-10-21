"""Library results must equal the published FanGraphs values recorded in tests/golden/*.yaml."""

from __future__ import annotations

import math
from typing import Any

import polars as pl
import pytest
from golden_loader import load_entries

import sabermetricspy as sp
from sabermetricspy import Metric
from sabermetricspy.types.context import SeasonContext

# published key -> (Metric, output column)
BATTING_METRICS: dict[str, tuple[Metric, str]] = {
    "avg": (Metric.AVG, "avg"),
    "obp": (Metric.OBP, "obp"),
    "slg": (Metric.SLG, "slg"),
    "ops": (Metric.OPS, "ops"),
    "iso": (Metric.ISO, "iso"),
    "babip": (Metric.BABIP, "babip"),
    "k_pct": (Metric.K_PCT, "k_pct"),
    "bb_pct": (Metric.BB_PCT, "bb_pct"),
    "woba": (Metric.WOBA, "woba"),
    "wraa": (Metric.WRAA, "wraa"),
    "wrc": (Metric.WRC, "wrc"),
    "wrc_plus": (Metric.WRC_PLUS, "wrc_plus"),
}
PITCHING_METRICS: dict[str, tuple[Metric, str]] = {
    "era": (Metric.ERA, "era"),
    "fip": (Metric.FIP, "fip"),
    "whip": (Metric.WHIP, "whip"),
    "k_per_9": (Metric.K_PER_9, "k_per_9"),
    "bb_per_9": (Metric.BB_PER_9, "bb_per_9"),
    "hr_per_9": (Metric.HR_PER_9, "hr_per_9"),
    "k_pct": (Metric.PIT_K_PCT, "pit_k_pct"),
    "bb_pct": (Metric.PIT_BB_PCT, "pit_bb_pct"),
    "lob_pct": (Metric.LOB_PCT, "lob_pct"),
    "era_minus": (Metric.ERA_MINUS, "era_minus"),
    "fip_minus": (Metric.FIP_MINUS, "fip_minus"),
}


def _frame(entry: dict[str, Any]) -> pl.DataFrame:
    # Fixtures store runs allowed as `r` (FanGraphs); the library's canonical column is `ra`.
    cols = {("ra" if k == "r" else k): [v] for k, v in entry["inputs"].items() if k != "ip"}
    return pl.DataFrame({"player_id": [entry["id"]], **cols})


def _context(entry: dict[str, Any]) -> SeasonContext:
    return SeasonContext(
        season=entry["season"],
        league=entry.get("league", "MLB"),
        park_factor=entry.get("park_factor", 100.0),
    )


def _compare(
    entry: dict[str, Any], mapping: dict[str, tuple[Metric, str]]
) -> tuple[list[str], list[str]]:
    """Return (undocumented failures, documented divergences) for one fixture entry."""
    keys = [k for k in entry["published"] if k in mapping]
    metrics = [mapping[k][0] for k in keys]
    row = sp.calculate(_frame(entry), metrics, context=_context(entry)).df.row(0, named=True)
    divergences = entry.get("divergence", {})
    failures, documented = [], []
    for key in keys:
        got = row[mapping[key][1]]
        want = entry["published"][key]
        tol = entry["tolerance"][key]
        if got is not None and math.isclose(got, want, abs_tol=tol):
            continue
        message = f"{entry['id']}.{key}: expected {want} (+/-{tol}) got {got}; source {entry['source_url']}"
        (documented if key in divergences else failures).append(message)
    return failures, documented


@pytest.mark.parametrize("entry", load_entries("batting.yaml"), ids=lambda e: e["id"])
def test_batting_golden_values(entry: dict[str, Any]) -> None:
    failures, _ = _compare(entry, BATTING_METRICS)
    assert not failures, "\n".join(failures)


@pytest.mark.parametrize("entry", load_entries("pitching.yaml"), ids=lambda e: e["id"])
def test_pitching_golden_values(entry: dict[str, Any]) -> None:
    failures, _ = _compare(entry, PITCHING_METRICS)
    assert not failures, "\n".join(failures)


def test_documented_divergences_have_reasons_and_still_diverge() -> None:
    """A divergence entry needs a written reason, and must be removed once the library agrees."""
    for fixture, mapping in (
        ("batting.yaml", BATTING_METRICS),
        ("pitching.yaml", PITCHING_METRICS),
    ):
        for entry in load_entries(fixture):
            for key, reason in entry.get("divergence", {}).items():
                assert isinstance(reason, str) and len(reason) > 30, (
                    f"{entry['id']}.{key} needs a reason"
                )
                failures, documented = _compare(entry, mapping)
                assert any(f"{entry['id']}.{key}:" in d for d in documented), (
                    f"{entry['id']}.{key} no longer diverges; remove it from the fixture"
                )
                assert not failures


def test_a_wrong_value_is_reported_with_metric_expected_actual_and_source() -> None:
    entry = dict(load_entries("pitching.yaml")[0])
    entry["published"] = {**entry["published"], "fip": entry["published"]["fip"] + 1.0}
    failures, _ = _compare(entry, PITCHING_METRICS)
    assert len(failures) == 1
    assert "fip" in failures[0] and "expected" in failures[0] and "got" in failures[0]
    assert entry["source_url"] in failures[0]


@pytest.mark.parametrize(
    ("fixture", "entry_id", "mapping"),
    [
        ("batting.yaml", "bonds_2001", BATTING_METRICS),
        ("pitching.yaml", "maddux_2001", PITCHING_METRICS),
    ],
)
def test_golden_entries_agree_across_polars_pandas_and_pyarrow(
    fixture: str, entry_id: str, mapping: dict[str, tuple[Metric, str]]
) -> None:
    import pyarrow as pa

    entry = next(e for e in load_entries(fixture) if e["id"] == entry_id)
    keys = [k for k in entry["published"] if k in mapping and k not in entry.get("divergence", {})]
    metrics = [mapping[k][0] for k in keys]
    frame = _frame(entry)
    ctx = _context(entry)
    base = sp.calculate(frame, metrics, context=ctx).df
    pandas_out = sp.calculate(frame.to_pandas(), metrics, context=ctx).df
    arrow_out = sp.calculate(frame.to_arrow(), metrics, context=ctx).df
    assert isinstance(arrow_out, pa.Table)
    for key in keys:
        col = mapping[key][1]
        expected = base[col][0]
        assert math.isclose(pandas_out[col].iloc[0], expected, abs_tol=1e-9), key
        assert math.isclose(arrow_out[col][0].as_py(), expected, abs_tol=1e-9), key


DIVERGENCE_BOUND = (
    3.2  # largest documented gap is 3.13 (Pedro Martinez 2000 FIP-); a bigger gap is a regression
)


def test_documented_divergences_stay_within_their_measured_bound() -> None:
    """A documented divergence is not a free pass: it may not grow beyond the gap measured when it was documented."""
    for fixture, mapping in (
        ("batting.yaml", BATTING_METRICS),
        ("pitching.yaml", PITCHING_METRICS),
    ):
        for entry in load_entries(fixture):
            for key in entry.get("divergence", {}):
                metric, column = mapping[key]
                row = sp.calculate(_frame(entry), [metric], context=_context(entry)).df.row(
                    0, named=True
                )
                gap = abs(row[column] - entry["published"][key])
                assert gap <= DIVERGENCE_BOUND, (
                    f"{entry['id']}.{key} gap {gap:.2f} exceeds the bound"
                )
