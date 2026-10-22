"""Test setup: no network, and seasonal constants come from the full local table when it exists, else a small sample.

The library ships no third-party constants (ADR-0068). The full FanGraphs constants table and the large FanGraphs
leaderboard fixtures are kept on the maintainer's machine only (`tests/_local_full_constants` and the files in
`LOCAL_ONLY`; all git-ignored). Without them:

- tests use the small sample in `tests/constants_sample`;
- a test that asks for a season outside the sample raises `ConstantsNotFoundError` and is reported as skipped (the
  library has no fallback to another season, so this cannot hide a wrong number);
- a test module that reads a missing local-only fixture is not collected, and the run header and summary list how many
  such modules there are, so a growing count is visible.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import pytest

import sabermetricspy as sp
from sabermetricspy.constants import ConstantsNotFoundError

HERE = Path(__file__).parent
FULL_CONSTANTS = HERE / "_local_full_constants"
SAMPLE_CONSTANTS = HERE / "constants_sample"
HAVE_FULL = FULL_CONSTANTS.is_dir()

# (file name under tests/, regex that marks a test module as reading it). Every file here is git-ignored.
LOCAL_ONLY: tuple[tuple[str, str], ...] = (
    ("baseballr_tieout.json", r"baseballr_tieout\.json"),
    ("guts_snapshot.yaml", r"guts_snapshot\.yaml"),
    ("league_totals_snapshot.yaml", r"league_totals_snapshot\.yaml"),
    ("league_war_totals_snapshot.yaml", r"league_war_totals_snapshot\.yaml"),
    ("league_bb_k_snapshot.yaml", r"league_bb_k_snapshot\.yaml"),
    ("league_pitching_rates_snapshot.yaml", r"league_pitching_rates_snapshot\.yaml"),
    ("league_sbcs_snapshot.yaml", r"league_sbcs_snapshot\.yaml"),
    ("np_wrc_snapshot.yaml", r"np_wrc_snapshot\.yaml"),
    ("pitcher_war.yaml", r'load_entries\("pitcher_war\.yaml"\)'),
    ("pitcher_war_leaderboard.csv", r"pitcher_war_leaderboard\.csv"),
    ("fg_batting_rates.csv", r"fg_batting_rates\.csv"),
    ("fg_pitching_rates.csv", r"fg_pitching_rates\.csv"),
    ("fg_batting_bb_k.csv", r"fg_batting_bb_k\.csv"),
    ("fg_pitching_xfip.csv", r"fg_pitching_xfip\.csv"),
    ("fg_game_score_v2.csv", r"fg_game_score_v2\.csv"),
    ("fg_shutdown_meltdown.csv", r"fg_shutdown_meltdown\.csv"),
)

sp.use_constants(FULL_CONSTANTS if HAVE_FULL else SAMPLE_CONSTANTS)

_NOT_COLLECTED: list[str] = []


def _missing_local_fixture(path: Path) -> str | None:
    try:
        source = path.read_text(encoding="utf-8")
    except OSError:
        return None
    for name, pattern in LOCAL_ONLY:
        if re.search(pattern, source) and not any((HERE / "golden").rglob(name)):
            return name
    return None


def pytest_ignore_collect(collection_path: Path, config: pytest.Config) -> bool | None:
    if collection_path.suffix == ".py" and collection_path.name.startswith("test_"):
        missing = _missing_local_fixture(collection_path)
        if missing is not None:
            _NOT_COLLECTED.append(f"{collection_path.name} (needs {missing})")
            return True
    return None


def pytest_report_header(config: pytest.Config) -> list[str]:
    mode = "full local constants" if HAVE_FULL else "small sample constants"
    return [f"sabermetricspy tests: {mode}"]


def pytest_terminal_summary(terminalreporter: Any, exitstatus: int, config: pytest.Config) -> None:
    if _NOT_COLLECTED:
        terminalreporter.section("test modules not collected (local-only fixtures missing)")
        for line in sorted(set(_NOT_COLLECTED)):
            terminalreporter.line(line)
        terminalreporter.line(f"{len(set(_NOT_COLLECTED))} modules not collected")


def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    if HAVE_FULL:
        return
    skip = pytest.mark.skip(reason="needs the full local constants table")
    for item in items:
        if "full_constants" in item.keywords:
            item.add_marker(skip)


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item: pytest.Item, call: pytest.CallInfo[Any]) -> Any:
    """In sample mode, turn 'season not in the table' (setup or call) into a reported skip."""
    outcome = yield
    report = outcome.get_result()
    if HAVE_FULL or not report.failed or call.excinfo is None:
        return
    error = call.excinfo.value
    if isinstance(error, ConstantsNotFoundError) and "for season" in str(error):
        report.outcome = "skipped"
        report.longrepr = (
            str(item.path),
            item.location[1] or 0,
            "needs the full local constants table",
        )
