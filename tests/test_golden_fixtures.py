"""Golden fixtures must carry provenance and be self-consistent before the library is compared to them.

The recomputation gate uses only raw arithmetic and the Guts! snapshot (never the library), so a
mis-transcribed fixture value cannot hide a library bug or create a false one.
"""

from __future__ import annotations

import copy
from typing import Any

import pytest
import yaml
from golden_loader import GOLDEN_DIR, load_entries


def _guts() -> dict[int, dict[str, float]]:
    return yaml.safe_load((GOLDEN_DIR / "guts_snapshot.yaml").read_text(encoding="utf-8"))[
        "seasons"
    ]


def _all_entries() -> list[tuple[str, dict[str, Any]]]:
    return [("batting.yaml", e) for e in load_entries("batting.yaml")] + [
        ("pitching.yaml", e) for e in load_entries("pitching.yaml")
    ]


def provenance_problems(entry: dict[str, Any]) -> list[str]:
    problems = []
    for key in ("source_url", "retrieved", "inputs", "published", "tolerance"):
        if not entry.get(key):
            problems.append(f"{entry.get('id')}: missing {key}")
    for metric in entry.get("published", {}):
        if metric not in entry.get("tolerance", {}):
            problems.append(f"{entry.get('id')}: no tolerance for {metric}")
    return problems


def recompute_batting(entry: dict[str, Any]) -> dict[str, float]:
    i = entry["inputs"]
    g = _guts()[entry["season"]]
    ubb = i["bb"] - i["ibb"]
    b1 = i["h"] - i["b2"] - i["b3"] - i["hr"]
    tb = b1 + 2 * i["b2"] + 3 * i["b3"] + 4 * i["hr"]
    den = i["ab"] + ubb + i["sf"] + i["hbp"]
    num = (
        g["w_bb"] * ubb
        + g["w_hbp"] * i["hbp"]
        + g["w_1b"] * b1
        + g["w_2b"] * i["b2"]
        + g["w_3b"] * i["b3"]
        + g["w_hr"] * i["hr"]
    )
    woba = num / den
    wraa = (woba - g["lg_woba"]) / g["woba_scale"] * i["pa"]
    return {
        "avg": i["h"] / i["ab"],
        "obp": (i["h"] + i["bb"] + i["hbp"]) / (i["ab"] + i["bb"] + i["hbp"] + i["sf"]),
        "slg": tb / i["ab"],
        "ops": (i["h"] + i["bb"] + i["hbp"]) / (i["ab"] + i["bb"] + i["hbp"] + i["sf"])
        + tb / i["ab"],
        "iso": tb / i["ab"] - i["h"] / i["ab"],
        "babip": (i["h"] - i["hr"]) / (i["ab"] - i["so"] - i["hr"] + i["sf"]),
        "k_pct": i["so"] / i["pa"],
        "bb_pct": i["bb"] / i["pa"],
        "woba": woba,
        "wraa": wraa,
        "wrc": wraa + g["lg_r_per_pa"] * i["pa"],
    }


def recompute_pitching(entry: dict[str, Any]) -> dict[str, float]:
    i = entry["inputs"]
    g = _guts()[entry["season"]]
    ip = i["outs"] / 3.0
    out = {
        "era": 9.0 * i["er"] / ip,
        "fip": (13 * i["hr"] + 3 * (i["bb"] + i["hbp"]) - 2 * i["so"]) / ip + g["c_fip"],
    }
    if "h" in i:
        out["whip"] = (i["bb"] + i["h"]) / ip
        out["lob_pct"] = (i["h"] + i["bb"] + i["hbp"] - i["r"]) / (
            i["h"] + i["bb"] + i["hbp"] - 1.4 * i["hr"]
        )
    out["k_per_9"] = 9.0 * i["so"] / ip
    out["bb_per_9"] = 9.0 * i["bb"] / ip
    out["hr_per_9"] = 9.0 * i["hr"] / ip
    if "bf" in i:
        out["k_pct"] = i["so"] / i["bf"]
        out["bb_pct"] = i["bb"] / i["bf"]
    return out


# Published metrics the raw-arithmetic gate can reproduce (the rest are checked against the library only).
GATE_METRICS = {
    "batting.yaml": (
        "avg",
        "obp",
        "slg",
        "ops",
        "iso",
        "babip",
        "k_pct",
        "bb_pct",
        "woba",
        "wraa",
        "wrc",
    ),
    "pitching.yaml": (
        "era",
        "fip",
        "whip",
        "lob_pct",
        "k_per_9",
        "bb_per_9",
        "hr_per_9",
        "k_pct",
        "bb_pct",
    ),
}


def gate_failures(fixture: str, entry: dict[str, Any]) -> list[str]:
    recomputed = (recompute_batting if fixture == "batting.yaml" else recompute_pitching)(entry)
    failures = []
    for metric in GATE_METRICS[fixture]:
        if metric not in entry["published"]:
            continue
        pub = entry["published"][metric]
        tol = entry["tolerance"][metric]
        if abs(recomputed[metric] - pub) > tol:
            failures.append(
                f"{entry['id']}.{metric}: recomputed {recomputed[metric]} vs published {pub} (tol {tol})"
            )
    return failures


@pytest.mark.parametrize(
    ("fixture", "entry"), _all_entries(), ids=lambda v: v if isinstance(v, str) else v["id"]
)
def test_every_fixture_entry_has_provenance_and_tolerance(
    fixture: str, entry: dict[str, Any]
) -> None:
    assert provenance_problems(entry) == []
    assert entry["source_url"].startswith("https://www.fangraphs.com/")
    assert str(entry["retrieved"]) == "2026-10-18"


def test_entry_without_url_or_date_is_rejected() -> None:
    entry = copy.deepcopy(load_entries("batting.yaml")[0])
    del entry["source_url"]
    entry["retrieved"] = ""
    problems = provenance_problems(entry)
    assert any("source_url" in p for p in problems)
    assert any("retrieved" in p for p in problems)


@pytest.mark.parametrize(
    ("fixture", "entry"), _all_entries(), ids=lambda v: v if isinstance(v, str) else v["id"]
)
def test_published_values_recompute_from_raw_inputs(fixture: str, entry: dict[str, Any]) -> None:
    assert gate_failures(fixture, entry) == []


def test_gate_fails_for_a_deliberately_altered_value() -> None:
    entry = copy.deepcopy(load_entries("pitching.yaml")[0])
    entry["published"]["fip"] += 0.5
    assert gate_failures("pitching.yaml", entry)
    batter = copy.deepcopy(load_entries("batting.yaml")[0])
    batter["published"]["woba"] += 0.01
    assert gate_failures("batting.yaml", batter)


def test_fixture_seasons_are_inside_the_constants_table_range() -> None:
    from sabermetricspy.constants import constants_table

    bundled = constants_table()
    for _, entry in _all_entries():
        assert entry["season"] in bundled, entry["id"]
