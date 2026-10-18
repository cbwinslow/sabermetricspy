"""docs/LITERATURE.md must keep its accepted entries complete, scored, ordered and sourced."""

from __future__ import annotations

import re
from pathlib import Path

DOC = (Path(__file__).parent.parent / "docs" / "LITERATURE.md").read_text(encoding="utf-8")

REQUIRED = (
    "Citation",
    "Formula source",
    "Inputs",
    "Inputs in canonical schema",
    "Validation target",
    "Scores",
    "Priority score",
    "Difficulty",
)
CRITERIA = ("formula", "inputs", "validation", "fit", "value", "difficulty")


def _entries() -> list[tuple[str, dict[str, str]]]:
    section = DOC.split("## Candidate methods", 1)[1].split("## Rejected or deferred", 1)[0]
    entries = []
    for block in re.split(r"^### ", section, flags=re.MULTILINE)[1:]:
        title, _, body = block.partition("\n")
        fields = dict(re.findall(r"^- \*\*([^*]+)\*\*: (.*)$", body, flags=re.MULTILINE))
        entries.append((title.strip(), fields))
    return entries


def test_catalogue_has_entries() -> None:
    assert len(_entries()) >= 5


def test_every_entry_has_all_fields_and_a_primary_source_url() -> None:
    for title, fields in _entries():
        for name in REQUIRED:
            assert fields.get(name), f"{title}: missing {name}"
        assert re.search(r"\]\(https?://[^)]+\)", fields["Citation"]), title


def test_recorded_score_is_the_sum_of_the_criteria() -> None:
    for title, fields in _entries():
        scores = {k: int(v) for k, v in re.findall(r"(\w+)=(\d+)", fields["Scores"])}
        assert tuple(scores) == CRITERIA, title
        total = sum(v for k, v in scores.items() if k != "difficulty") - scores["difficulty"]
        assert int(fields["Priority score"]) == total, title
        assert int(fields["Difficulty"][0]) == scores["difficulty"], title
        assert 0 <= scores["formula"] <= 1 and 0 <= scores["inputs"] <= 2, title
        assert 0 <= scores["validation"] <= 2 and 0 <= scores["fit"] <= 2, title
        assert 1 <= scores["value"] <= 3 and 1 <= scores["difficulty"] <= 3, title


def test_entries_are_in_descending_priority_order() -> None:
    priorities = [int(f["Priority score"]) for _, f in _entries()]
    assert priorities == sorted(priorities, reverse=True)


def test_rejected_table_names_a_reason_for_each_row() -> None:
    table = DOC.split("## Rejected or deferred with reason", 1)[1].split(
        "## baseballr coverage", 1
    )[0]
    rows = [
        r
        for r in table.splitlines()
        if r.startswith("| ") and not r.startswith("| Candidate") and "---" not in r
    ]
    assert len(rows) >= 5
    for row in rows:
        cells = [c.strip() for c in row.strip("|").split("|")]
        assert len(cells) == 3 and all(cells), row


def test_digest_referenced_by_the_catalogue_exists() -> None:
    match = re.search(r"\]\((literature/digest-[\d-]+\.json)\)", DOC)
    assert match is not None
    assert (Path(__file__).parent.parent / "docs" / match.group(1)).is_file()
