"""OPS+ against Baseball-Reference values (tests/golden/ops_plus.yaml)."""

from __future__ import annotations

from typing import Any

import polars as pl
import pytest
import yaml
from golden_loader import GOLDEN_DIR

import sabermetricspy as sp
from sabermetricspy import Metric

DATA: dict[str, Any] = yaml.safe_load((GOLDEN_DIR / "ops_plus.yaml").read_text(encoding="utf-8"))


@pytest.mark.parametrize("entry", DATA["entries"], ids=lambda e: e["id"])
def test_ops_plus_is_within_the_documented_gap_of_baseball_reference(entry: dict[str, Any]) -> None:
    df = pl.DataFrame([entry["inputs"]])
    got = sp.calculate(df, [Metric.OPS_PLUS], season=entry["season"]).df["ops_plus"][0]
    published = entry["published_ops_plus"]
    assert got == pytest.approx(published, rel=DATA["relative_tolerance"]), (
        f"{entry['id']}: {got:.1f} vs Baseball-Reference {published}"
    )
