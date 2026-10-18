"""Offline tests for tools/literature_sweep.py using recorded OpenAlex and arXiv responses."""

from __future__ import annotations

import dataclasses
import importlib.util
import sys
from pathlib import Path
from typing import Any

import pytest

ROOT = Path(__file__).parent.parent
FIXTURES = Path(__file__).parent / "fixtures" / "literature"


def _load() -> Any:
    spec = importlib.util.spec_from_file_location(
        "literature_sweep", ROOT / "tools" / "literature_sweep.py"
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules["literature_sweep"] = module
    spec.loader.exec_module(module)
    return module


ls: Any = _load()


def test_openalex_response_is_normalized() -> None:
    records, total = ls.parse_openalex(
        (FIXTURES / "openalex_run_expectancy.json").read_text("utf-8"), "q"
    )
    assert total >= len(records) == 3
    first = records[0]
    assert first.source == "openalex"
    assert first.identifier.startswith("https://openalex.org/W")
    assert first.title and first.year
    assert first.authors and all(isinstance(a, str) for a in first.authors)
    assert first.url.startswith("http")
    assert first.query == "q"


def test_arxiv_response_is_normalized() -> None:
    records, total = ls.parse_arxiv((FIXTURES / "arxiv_run_expectancy.xml").read_text("utf-8"), "q")
    assert total == len(records) == 2
    first = records[0]
    assert first.source == "arxiv"
    assert first.identifier.startswith("arxiv:")
    assert first.url.startswith("https://arxiv.org/abs/")
    assert first.authors == ["Sebastian E. Ferrando", "Eli Kohn"]
    assert first.year == 2026


def test_records_store_metadata_only() -> None:
    """No abstract or paper text is kept: only identifiers, bibliographic fields, license and the landing link."""
    fields = {f.name for f in dataclasses.fields(ls.Record)}
    assert fields == {
        "source",
        "identifier",
        "title",
        "authors",
        "year",
        "venue",
        "license",
        "url",
        "query",
    }
    for name in ("abstract", "summary", "text", "full_text"):
        assert name not in fields


def test_license_is_recorded_as_returned_or_marked_absent() -> None:
    records, _ = ls.parse_openalex(
        (FIXTURES / "openalex_run_expectancy.json").read_text("utf-8"), "q"
    )
    assert all(r.license is None or isinstance(r.license, str) for r in records)
    arxiv, _ = ls.parse_arxiv((FIXTURES / "arxiv_run_expectancy.xml").read_text("utf-8"), "q")
    assert all(r.license is None for r in arxiv)


def test_arxiv_requests_are_spaced_by_the_published_interval() -> None:
    slept: list[float] = []
    now = [100.0]

    def clock() -> float:
        return now[0]

    def sleep(seconds: float) -> None:
        slept.append(seconds)
        now[0] += seconds

    throttle = ls.Throttle(3.0, clock=clock, sleep=sleep)
    throttle.wait()
    assert slept == []
    now[0] += 1.0
    throttle.wait()
    assert slept == [pytest.approx(2.0)]
    now[0] += 5.0
    throttle.wait()
    assert slept == [pytest.approx(2.0)]


def test_default_arxiv_interval_is_at_least_three_seconds() -> None:
    assert ls.ARXIV_MIN_INTERVAL_SECONDS >= 3.0


def test_requests_carry_no_personal_data() -> None:
    urls = [ls.openalex_url(q, 5) for q in ls.QUERIES]
    urls += [ls.arxiv_url(q, 5) for q in ls.QUERIES]
    for url in urls:
        assert "mailto" not in url and "api_key" not in url and "@" not in url
    assert "@" not in ls.USER_AGENT


def test_digest_records_query_date_and_counts() -> None:
    records, total = ls.parse_arxiv(
        (FIXTURES / "arxiv_run_expectancy.xml").read_text("utf-8"), "run expectancy"
    )
    digest = ls.build_digest([("arxiv", "run expectancy", total, records)], "2026-10-18")
    entry = digest["queries"][0]
    assert digest["date"] == "2026-10-18"
    assert entry["query"] == "run expectancy" and entry["source"] == "arxiv"
    assert entry["total_results"] == total and entry["returned"] == len(records)
    assert entry["records"][0]["title"]
