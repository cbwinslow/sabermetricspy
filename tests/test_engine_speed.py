"""Polars evaluation builds one query plan: wide frames with many metrics stay fast and give the same values.

Before the engine deferred the plan, 30 metrics on 120,000 rows and 98 columns took 8.7 s eager against 0.12 s lazy
(measured 2026-10-20); the eager path ran a full pass over every column for each metric.
"""

from __future__ import annotations

import time

import polars as pl
import pytest

import sabermetricspy as sp
from sabermetricspy.registry import REGISTRY
from sabermetricspy.types import Metric


def _wide_frame(repeat: int) -> pl.DataFrame:
    columns: set[str] = set()
    for metric in Metric:
        columns |= set(REGISTRY.required_base_columns([metric.value]))
    n = 60
    idx = pl.int_range(0, n, eager=True)
    base = pl.DataFrame(
        {
            "player_id": idx.cast(pl.Utf8),
            "season": pl.repeat(2024, n, eager=True),
            **{c: (idx % (7 + (sum(map(ord, c)) % 5))) + 3 for c in sorted(columns)},
        }
    )
    return pl.concat([base] * repeat)


def test_many_metrics_on_a_wide_eager_frame_are_fast() -> None:
    frame = _wide_frame(2000)  # 120,000 rows x 98 columns
    names = [m.value for m in Metric][:30]
    start = time.perf_counter()
    res = sp.calculate(frame, names, season=2024)
    elapsed = time.perf_counter() - start
    assert isinstance(res.df, pl.DataFrame)
    assert res.df.height == 120_000
    assert elapsed < 3.0, (
        f"30 metrics on 120,000 x 98 took {elapsed:.1f} s (was 8.7 s before deferral)"
    )


def test_lazy_input_stays_lazy() -> None:
    res = sp.calculate(_wide_frame(2).lazy(), ["iso", "ops"], season=2024)
    assert isinstance(res.df, pl.LazyFrame)


@pytest.mark.parametrize("by", [None, "player_id"])
def test_all_at_once_equals_one_metric_at_a_time(by: str | None) -> None:
    frame = _wide_frame(3)
    names = [m.value for m in Metric][:30]
    together = sp.calculate(frame, names, by=by, season=2024).df
    key = ["player_id"] if by else None
    for name in names:
        alone = sp.calculate(frame, [name], by=by, season=2024).df
        assert alone.height == together.height
        if key:
            a, b = alone.sort(key)[name], together.sort(key)[name]
        else:
            a, b = alone[name], together[name]
        assert a.dtype == b.dtype
        if a.dtype.is_float():
            for u, v in zip(a.to_list(), b.to_list(), strict=True):
                if u is None or v is None or u != u or v != v:
                    assert (u is None or u != u) and (v is None or v != v), name
                else:
                    assert abs(u - v) <= 1e-12 * max(1.0, abs(u)), name
        else:
            assert a.to_list() == b.to_list(), name
