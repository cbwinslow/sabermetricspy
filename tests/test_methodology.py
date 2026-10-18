"""The methodology audit, the registry and docs/METHODOLOGY.md must agree."""

from __future__ import annotations

from pathlib import Path

import pytest

from sabermetricspy import ReferenceStatus
from sabermetricspy.methodology import metric_entries, model_entries, render_markdown
from sabermetricspy.registry import REGISTRY
from sabermetricspy.types.enums import Metric

DOC = Path(__file__).parent.parent / "docs" / "METHODOLOGY.md"


def _builtin() -> dict[str, object]:
    return {s.name: s for s in REGISTRY.all_specs() if isinstance(s.metric, Metric)}


def test_every_builtin_metric_has_an_audit_entry_and_vice_versa() -> None:
    names = set(_builtin())
    entries = set(metric_entries())
    assert names - entries == set(), (
        f"metrics missing from methodology.yaml: {sorted(names - entries)}"
    )
    assert entries - names == set(), (
        f"methodology.yaml entries with no metric: {sorted(entries - names)}"
    )


def test_registry_status_equals_audit_status() -> None:
    entries = metric_entries()
    for name, spec in _builtin().items():
        assert spec.reference_status is entries[name].status, name  # type: ignore[attr-defined]


def test_methodology_document_is_current() -> None:
    assert DOC.read_text(encoding="utf-8") == render_markdown(), (
        "docs/METHODOLOGY.md is stale: run `uv run python -m sabermetricspy.methodology > docs/METHODOLOGY.md`"
    )


def test_document_lists_every_registered_metric_once() -> None:
    text = DOC.read_text(encoding="utf-8")
    for name in _builtin():
        assert text.count(f"| `{name}` |") == 1, name


def test_document_consistency_check_names_a_missing_metric() -> None:
    stale = render_markdown().replace("| `wrc_plus` |", "| `removed` |")
    assert "| `wrc_plus` |" not in stale
    assert stale != DOC.read_text(encoding="utf-8")


def test_non_matching_metrics_state_how_they_differ() -> None:
    entries = metric_entries()
    for name, spec in _builtin().items():
        status = entries[name].status
        if status is ReferenceStatus.MATCHES:
            continue
        assert entries[name].note, name
        assert entries[name].note in spec.caveats, f"{name}: caveats do not carry the audit note"  # type: ignore[attr-defined]


def test_matching_metrics_record_a_verifying_source() -> None:
    for name, entry in metric_entries().items():
        if entry.status is ReferenceStatus.MATCHES:
            assert entry.source_url.startswith("http"), name


@pytest.mark.parametrize(
    "name",
    [
        "woba",
        "wraa",
        "wrc",
        "babip",
        "obp",
        "lob_pct",
        "rc_tech",
        "dice",
        "hard_hit_pct",
        "sweet_spot_pct",
    ],
)
def test_verified_metrics_are_recorded_as_matching(name: str) -> None:
    assert metric_entries()[name].status is ReferenceStatus.MATCHES


def test_woba_links_the_fangraphs_library() -> None:
    assert "library.fangraphs.com/offense/woba" in metric_entries()["woba"].source_url


@pytest.mark.parametrize(
    "name",
    [
        "ops_plus",
        "kwera",
        "siera",
        "wsb",
        "bsr",
        "era_minus",
        "fip_minus",
        "pythagenpat_win_pct",
        "barrel_pct",
        "der",
    ],
)
def test_known_approximations_are_labeled(name: str) -> None:
    assert metric_entries()[name].status in (ReferenceStatus.APPROXIMATE, ReferenceStatus.DIVERGENT)


def test_speed_score_records_the_four_factor_form() -> None:
    entry = metric_entries()["speed_score"]
    assert entry.status is ReferenceStatus.MATCHES
    assert "six-factor" in entry.note


def test_siera_identifies_the_2010_version_and_the_revised_one() -> None:
    note = metric_entries()["siera"].note
    assert "2010" in note and "2011" in note


def test_models_with_known_differences_are_labeled() -> None:
    models = model_entries()
    pitcher = models["WARFramework.calculate_pitcher_war_df"]
    assert pitcher.status is ReferenceStatus.APPROXIMATE
    assert "worked example" in pitcher.note and "0.2 WAR" in pitcher.note
    assert models["WARFramework.calculate_position_player_*"].status is ReferenceStatus.APPROXIMATE
    assert models["MarcelProjector (pitchers)"].status is ReferenceStatus.DIVERGENT
    assert "134" in models["MarcelProjector (pitchers)"].note


def test_pitcher_war_docstring_names_the_published_method_and_its_limits() -> None:
    from sabermetricspy.value import WARFramework

    doc = WARFramework.calculate_pitcher_war_df.__doc__ or ""
    assert "FanGraphs Library" in doc and "worked example" in doc
    assert "separately" in doc and "0.2 WAR" in doc


def test_siera_coefficients_are_labeled_with_their_source_version() -> None:
    from sabermetricspy.types.context import SIERACoefficients

    assert SIERACoefficients().version == "baseball_prospectus_2010"
