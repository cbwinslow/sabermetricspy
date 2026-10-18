"""Batted-ball rates must reproduce the FanGraphs leaderboard rates from the published counts.

Two layers: a recomputation gate that uses only arithmetic (so a mis-transcribed fixture cannot hide a
library bug), then the library compared with the published values. FanGraphs conventions, established by
recomputing every row: GB/FB/LD% divide by GB+FB+LD; IFFB% divides by FB; Pull/Cent/Oppo% divide by
Pull+Cent+Oppo (which equals GB+FB+LD+BU).
"""

from __future__ import annotations

import copy
from typing import Any

import polars as pl
import pytest
from golden_loader import load_entries

import sabermetricspy as sp
from sabermetricspy import Metric

ENTRIES = load_entries("batted_ball.yaml")

# published key -> (Metric, output column)
METRICS: dict[str, tuple[Metric, str]] = {
    "gb_pct": (Metric.GB_PCT, "gb_pct"),
    "fb_pct": (Metric.FB_PCT, "fb_pct"),
    "ld_pct": (Metric.LD_PCT, "ld_pct"),
    "hr_to_fb": (Metric.HR_TO_FB, "hr_to_fb"),
    "gb_to_fb": (Metric.GB_TO_FB, "gb_to_fb"),
    "pull_pct": (Metric.PULL_PCT, "pull_pct"),
    "cent_pct": (Metric.CENT_PCT, "cent_pct"),
    "oppo_pct": (Metric.OPPO_PCT, "oppo_pct"),
}


def recompute(entry: dict[str, Any]) -> dict[str, float]:
    i = entry["inputs"]
    bbe = i["gb"] + i["fb"] + i["ld"]
    directed = i["pull"] + i["cent"] + i["oppo"]
    return {
        "gb_pct": i["gb"] / bbe,
        "fb_pct": i["fb"] / bbe,
        "ld_pct": i["ld"] / bbe,
        "iffb_pct": i["iffb"] / i["fb"],
        "hr_to_fb": i["hr"] / i["fb"],
        "gb_to_fb": i["gb"] / i["fb"],
        "pull_pct": i["pull"] / directed,
        "cent_pct": i["cent"] / directed,
        "oppo_pct": i["oppo"] / directed,
    }


def gate_problems(entry: dict[str, Any]) -> list[str]:
    problems = []
    for key in ("source_url", "retrieved", "inputs", "published", "tolerance"):
        if not entry.get(key):
            problems.append(f"{entry['id']}: missing {key}")
    i = entry["inputs"]
    if i["pull"] + i["cent"] + i["oppo"] != i["gb"] + i["fb"] + i["ld"] + i["bu"]:
        problems.append(f"{entry['id']}: directed balls != GB+FB+LD+BU")
    for metric, value in recompute(entry).items():
        if abs(value - entry["published"][metric]) > entry["tolerance"][metric]:
            problems.append(
                f"{entry['id']}: {metric} recomputed {value} != {entry['published'][metric]}"
            )
    return problems


def test_fixture_covers_six_or_more_seasons_across_eras() -> None:
    assert len(ENTRIES) >= 15
    assert len({e["season"] for e in ENTRIES}) >= 5


@pytest.mark.parametrize("entry", ENTRIES, ids=[e["id"] for e in ENTRIES])
def test_recomputation_gate(entry: dict[str, Any]) -> None:
    assert gate_problems(entry) == []


def test_gate_fails_on_an_altered_value() -> None:
    entry = copy.deepcopy(ENTRIES[0])
    entry["published"]["gb_pct"] += 0.01
    assert any("gb_pct" in p for p in gate_problems(entry))
    entry = copy.deepcopy(ENTRIES[0])
    entry["inputs"]["bu"] += 1
    assert any("GB+FB+LD+BU" in p for p in gate_problems(entry))


@pytest.mark.parametrize("entry", ENTRIES, ids=[e["id"] for e in ENTRIES])
def test_library_reproduces_published_rates(entry: dict[str, Any]) -> None:
    i = entry["inputs"]
    frame = pl.DataFrame(
        {
            "player_id": [entry["id"]],
            "gb": [i["gb"]],
            "fb": [i["fb"]],
            "ld": [i["ld"]],
            "hr": [i["hr"]],
            "pull_bbe": [i["pull"]],
            "cent_bbe": [i["cent"]],
            "oppo_bbe": [i["oppo"]],
        }
    )
    result = sp.calculate(frame, [m for m, _ in METRICS.values()])
    row = result.df.row(0, named=True)
    for key, (_, column) in METRICS.items():
        assert row[column] == pytest.approx(entry["published"][key], abs=entry["tolerance"][key]), (
            f"{entry['id']} {key}"
        )
