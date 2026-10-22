"""Bundled seasonal constants must equal the published FanGraphs Guts! table and carry provenance."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
import yaml

from sabermetricspy.constants import constants_table, get_woba_weights

GOLDEN_DIR = Path(__file__).parent / "golden"

GUTS_FIELDS = (
    "lg_woba",
    "woba_scale",
    "w_bb",
    "w_hbp",
    "w_1b",
    "w_2b",
    "w_3b",
    "w_hr",
    "r_sb",
    "r_cs",
    "lg_r_per_pa",
    "lg_r_per_w",
    "c_fip",
)


def _load_snapshot() -> dict[str, Any]:
    return yaml.safe_load((GOLDEN_DIR / "guts_snapshot.yaml").read_text(encoding="utf-8"))


def test_guts_snapshot_structure_and_provenance() -> None:
    snap = _load_snapshot()
    assert snap["source"].startswith("FanGraphs Guts!")
    assert snap["retrieved"]
    seasons = snap["seasons"]
    assert sorted(seasons) == list(range(1990, 2027))
    for year, row in seasons.items():
        assert set(row) == set(GUTS_FIELDS), year
        assert row["w_bb"] < row["w_1b"] < row["w_2b"] < row["w_3b"] < row["w_hr"], year


def test_constants_table_match_guts_snapshot() -> None:
    snap = _load_snapshot()["seasons"]
    table = constants_table()
    diffs: list[str] = []
    for year, ref in snap.items():
        if year not in table:
            diffs.append(f"{year}: season missing from bundled table")
            continue
        for field in GUTS_FIELDS:
            ours = getattr(table[year], field)
            if abs(ours - ref[field]) > 1e-9:
                diffs.append(f"{year}.{field}: bundled {ours} vs Guts! {ref[field]}")
    assert not diffs, f"{len(diffs)} differences from Guts!:\n" + "\n".join(diffs)


def test_league_era_fip_xfip_are_not_copies_of_each_other() -> None:
    table = constants_table()
    copied = [
        year
        for year, w in table.items()
        if w.lg_era is not None and w.lg_era == w.lg_fip == w.lg_xfip
    ]
    assert not copied, f"lg_era == lg_fip == lg_xfip (placeholder) in seasons {copied}"


@pytest.mark.parametrize("year", sorted(constants_table()))
def test_every_bundled_entry_has_a_source(year: int) -> None:
    entry = get_woba_weights(year)
    assert entry.source and entry.source.strip(), f"{year} has no source"


def test_optional_league_constants_validate_with_and_without_values() -> None:
    from sabermetricspy.types.context import WOBAWeights

    base = {
        "season": 2001,
        "lg_woba": 0.327,
        "woba_scale": 1.182,
        "w_bb": 0.704,
        "w_hbp": 0.733,
        "w_1b": 0.887,
        "w_2b": 1.242,
        "w_3b": 1.561,
        "w_hr": 1.982,
        "lg_r_per_pa": 0.124,
        "lg_r_per_w": 10.235,
        "c_fip": 3.049,
    }
    bare = WOBAWeights.model_validate(base)
    assert bare.lg_era is None
    assert bare.lg_fip is None
    assert bare.lg_xfip is None
    assert bare.lg_hr_per_fb is None
    assert bare.lg_wrc_per_pa is None
    full = WOBAWeights.model_validate({**base, "lg_era": 4.3, "lg_wrc_per_pa": 0.13})
    assert full.lg_era == 4.3
    assert full.lg_wrc_per_pa == 0.13


def _load_league_totals() -> dict[str, Any]:
    return yaml.safe_load((GOLDEN_DIR / "league_totals_snapshot.yaml").read_text(encoding="utf-8"))


def _outs_to_ip(notation: str) -> float:
    whole, thirds = notation.split(".")
    return int(whole) + int(thirds) / 3.0


def test_bundled_league_constants_match_league_totals_snapshot() -> None:
    totals = _load_league_totals()
    table = constants_table()
    diffs: list[str] = []
    for year, pit in totals["pitching"].items():
        w = table[year]
        bat = totals["batting"][year]
        expected = {
            "lg_era": pit["era"],
            "lg_fip": pit["fip"],
            "lg_xfip": pit["xfip"],
            "lg_hr_per_fb": pit["hr_per_fb"],
            "lg_obp": bat["obp"],
            "lg_slg": bat["slg"],
            "lg_k_pct": bat["so"] / bat["pa"],
            "lg_bb_pct": bat["bb"] / bat["pa"],
        }
        for field, ref in expected.items():
            ours = getattr(w, field)
            if ref is None:
                if ours is not None:
                    diffs.append(f"{year}.{field}: bundled {ours} but no published value")
            elif ours is None or abs(ours - ref) > 1e-9:
                diffs.append(f"{year}.{field}: bundled {ours} vs published {ref}")
    assert not diffs, "\n".join(diffs)


def test_xfip_inputs_absent_before_2002_and_present_after() -> None:
    table = constants_table()
    for year, w in table.items():
        if year < 2002:
            assert w.lg_xfip is None and w.lg_hr_per_fb is None, year
        else:
            assert w.lg_xfip is not None and w.lg_hr_per_fb is not None, year


def test_cfip_reproduces_league_era_from_league_totals() -> None:
    """lgERA = (13 HR + 3 (BB incl. IBB + HBP) - 2 K) / IP + cFIP.

    Tolerance is cFIP's 3-decimal rounding (0.0005) plus FanGraphs' own league FIP-vs-ERA gap
    (up to about 0.0004 in early seasons).
    """
    totals = _load_league_totals()["pitching"]
    table = constants_table()
    for year, p in totals.items():
        ip = _outs_to_ip(p["ip_notation"])
        raw = (13 * p["hr"] + 3 * (p["bb"] + p["hbp"]) - 2 * p["so"]) / ip
        assert abs(raw + table[year].c_fip - 9 * p["er"] / ip) < 1e-3, year


def test_missing_season_raises_and_names_the_covered_range() -> None:
    from sabermetricspy import constants

    with pytest.raises(constants.ConstantsNotFoundError, match=r"1975.*covers"):
        constants.get_woba_weights(1975)


def test_bundled_season_does_not_warn() -> None:
    import warnings

    from sabermetricspy import constants

    with warnings.catch_warnings():
        warnings.simplefilter("error")
        for year in (1990, 2001, 2025):
            assert constants.get_woba_weights(year).season == year


def test_non_pitcher_wrc_per_pa_matches_snapshot() -> None:
    snap = yaml.safe_load((GOLDEN_DIR / "np_wrc_snapshot.yaml").read_text(encoding="utf-8"))
    table = constants_table()
    for year, row in snap["seasons"].items():
        w = table[year]
        nl = row["nl_wrc"] / row["nl_pa"]
        al = row["al_wrc"] / row["al_pa"]
        mlb = (row["nl_wrc"] + row["al_wrc"]) / (row["nl_pa"] + row["al_pa"])
        assert w.lg_wrc_per_pa_nl == pytest.approx(nl, abs=1e-12), year
        assert w.lg_wrc_per_pa_al == pytest.approx(al, abs=1e-12), year
        assert w.lg_wrc_per_pa == pytest.approx(mlb, abs=1e-12), year
        # Non-pitcher run environment is close to (within ~8% of) the all-player league R/PA.
        assert 0.97 < mlb / w.lg_r_per_pa < 1.10, year


def test_wrc_per_pa_for_selects_league_and_falls_back_to_mlb() -> None:
    w = get_woba_weights(2001)
    assert w.wrc_per_pa_for("NL") == w.lg_wrc_per_pa_nl
    assert w.wrc_per_pa_for("al") == w.lg_wrc_per_pa_al
    assert w.wrc_per_pa_for("MLB") == w.lg_wrc_per_pa
    assert w.lg_wrc_per_pa_nl is not None and w.lg_wrc_per_pa_nl > 0.13
