"""Every metric declares how closely it follows the published method of its reference source."""

from __future__ import annotations

from sabermetricspy import ReferenceStatus
from sabermetricspy.registry import REGISTRY, MetricSpec
from sabermetricspy.types.enums import Category


def test_reference_status_enum_follows_naming_convention() -> None:
    assert [s.name for s in ReferenceStatus] == [
        "MATCHES",
        "APPROXIMATE",
        "DIVERGENT",
        "UNVERIFIED",
        "EXPERIMENTAL",
    ]
    assert [s.value for s in ReferenceStatus] == [
        "matches",
        "approximate",
        "divergent",
        "unverified",
        "experimental",
    ]


def test_metric_spec_defaults_to_unverified() -> None:
    spec = MetricSpec(
        metric="custom_metric",
        display_name="Custom",
        category=Category.BATTING,
        formula_latex="x",
        citation="n/a",
    )
    assert spec.reference_status is ReferenceStatus.UNVERIFIED
    assert spec.reference_url == ""


def test_registered_metrics_carry_a_status() -> None:
    for spec in REGISTRY.all_specs():
        assert isinstance(spec.reference_status, ReferenceStatus), spec.name
