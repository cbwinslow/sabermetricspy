"""Repeatable literature sweep over OpenAlex and arXiv; stores bibliographic metadata only.

Usage: uv run python tools/literature_sweep.py [--per-query 8] [--out docs/literature/digest-YYYY-MM-DD.json]

The tool uses only the standard library, sends no email address or API key, waits at least three seconds between
arXiv requests (the interval arXiv publishes), and records identifiers, title, authors, year, venue, license and a
landing link. It never stores abstracts or paper text. Terms: https://info.arxiv.org/help/api/index.html and
https://developers.openalex.org/.
"""

from __future__ import annotations

import argparse
import dataclasses
import json
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from collections.abc import Callable
from datetime import date
from pathlib import Path
from typing import Any

ARXIV_MIN_INTERVAL_SECONDS = 3.0
USER_AGENT = "sabermetricspy-literature-sweep (metadata-only research tool)"
OPENALEX_API = "https://api.openalex.org/works"
ARXIV_API = "https://export.arxiv.org/api/query"
_ATOM = "{http://www.w3.org/2005/Atom}"
_OPENSEARCH = "{http://a9.com/-/spec/opensearch/1.1/}"

# Topic queries, each combined with the word "baseball". Keep in sync with docs/LITERATURE_SWEEP.md.
QUERIES: tuple[str, ...] = (
    "run expectancy",
    "win probability",
    "pitch quality stuff model",
    "expected batting average exit velocity launch angle",
    "catcher framing",
    "fielding metrics defensive runs",
    "player projection forecasting",
    "park factors",
    "aging curve",
    "pitch tracking release",
    "batter pitcher matchup",
    "baserunning stolen base value",
)


@dataclasses.dataclass(frozen=True)
class Record:
    """Bibliographic metadata for one result; no abstract or paper text is stored."""

    source: str
    identifier: str
    title: str
    authors: list[str]
    year: int | None
    venue: str | None
    license: str | None
    url: str
    query: str


class Throttle:
    """Block until at least `interval` seconds have passed since the previous call."""

    def __init__(
        self,
        interval: float,
        *,
        clock: Callable[[], float] = time.monotonic,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        self.interval = interval
        self._clock = clock
        self._sleep = sleep
        self._last: float | None = None

    def wait(self) -> None:
        if self._last is not None:
            remaining = self.interval - (self._clock() - self._last)
            if remaining > 0:
                self._sleep(remaining)
        self._last = self._clock()


def openalex_url(query: str, per_page: int) -> str:
    params = {
        "search": f"baseball {query}",
        "per-page": str(per_page),
        "select": "id,doi,title,publication_year,authorships,primary_location,type",
    }
    return f"{OPENALEX_API}?{urllib.parse.urlencode(params)}"


def arxiv_url(query: str, max_results: int) -> str:
    terms = f'all:baseball AND all:"{query}"'
    params = {"search_query": terms, "max_results": str(max_results)}
    return f"{ARXIV_API}?{urllib.parse.urlencode(params)}"


def parse_openalex(text: str, query: str) -> tuple[list[Record], int]:
    data = json.loads(text)
    records = []
    for work in data.get("results", []):
        location = work.get("primary_location") or {}
        source = location.get("source") or {}
        authors = [
            (a.get("author") or {}).get("display_name") or "" for a in work.get("authorships", [])
        ]
        records.append(
            Record(
                source="openalex",
                identifier=str(work.get("id", "")),
                title=str(work.get("title") or ""),
                authors=[a for a in authors if a],
                year=work.get("publication_year"),
                venue=source.get("display_name"),
                license=location.get("license"),
                url=str(location.get("landing_page_url") or work.get("doi") or work.get("id", "")),
                query=query,
            )
        )
    return records, int((data.get("meta") or {}).get("count", len(records)))


def parse_arxiv(text: str, query: str) -> tuple[list[Record], int]:
    root = ET.fromstring(text)
    total = int(root.findtext(f"{_OPENSEARCH}totalResults", default="0"))
    records = []
    for entry in root.findall(f"{_ATOM}entry"):
        abs_url = (entry.findtext(f"{_ATOM}id") or "").strip()
        arxiv_id = abs_url.rsplit("/abs/", 1)[-1]
        published = entry.findtext(f"{_ATOM}published") or ""
        records.append(
            Record(
                source="arxiv",
                identifier=f"arxiv:{arxiv_id}",
                title=" ".join((entry.findtext(f"{_ATOM}title") or "").split()),
                authors=[
                    (a.findtext(f"{_ATOM}name") or "").strip()
                    for a in entry.findall(f"{_ATOM}author")
                ],
                year=int(published[:4]) if published[:4].isdigit() else None,
                venue="arXiv",
                license=None,
                url=abs_url.replace("http://", "https://"),
                query=query,
            )
        )
    return records, total


def build_digest(runs: list[tuple[str, str, int, list[Record]]], run_date: str) -> dict[str, Any]:
    """Collect the query, date, result counts and metadata records of every run."""
    return {
        "date": run_date,
        "note": "Bibliographic metadata only; paper licenses are recorded as returned (null when the API gives none).",
        "queries": [
            {
                "source": source,
                "query": query,
                "total_results": total,
                "returned": len(records),
                "records": [dataclasses.asdict(r) for r in records],
            }
            for source, query, total, records in runs
        ],
    }


def _get(url: str) -> str:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=60) as response:
        return response.read().decode("utf-8")


def run_sweep(per_query: int, run_date: str) -> dict[str, Any]:
    throttle = Throttle(ARXIV_MIN_INTERVAL_SECONDS)
    runs: list[tuple[str, str, int, list[Record]]] = []
    for query in QUERIES:
        records, total = parse_openalex(_get(openalex_url(query, per_query)), query)
        runs.append(("openalex", query, total, records))
        throttle.wait()
        records, total = parse_arxiv(_get(arxiv_url(query, per_query)), query)
        runs.append(("arxiv", query, total, records))
    return build_digest(runs, run_date)


def main() -> None:
    today = date.today().isoformat()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--per-query", type=int, default=8)
    parser.add_argument("--out", default=f"docs/literature/digest-{today}.json")
    args = parser.parse_args()
    digest = run_sweep(args.per_query, today)
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(digest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"wrote {out} ({len(digest['queries'])} query runs)")


if __name__ == "__main__":
    main()
