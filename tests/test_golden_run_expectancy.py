"""The built-in RE24 table must be the published FanGraphs matrix, not an unsourced approximation."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from sabermetricspy.expectancy import DEFAULT_RE24_TABLE

REF = yaml.safe_load(
    (Path(__file__).parent / "golden" / "run_expectancy_table.yaml").read_text("utf-8")
)
TABLE: dict[str, list[float]] = REF["table"]


def test_published_matrix_is_internally_consistent() -> None:
    """Recomputation gate: expectancy falls with outs and a runner never lowers it."""
    for values in TABLE.values():
        assert values[0] > values[1] > values[2] > 0
    for outs in range(3):
        assert TABLE["---"][outs] < TABLE["1--"][outs] < TABLE["12-"][outs] < TABLE["123"][outs]


@pytest.mark.parametrize("state", list(TABLE))
@pytest.mark.parametrize("outs", [0, 1, 2])
def test_default_table_is_the_published_matrix(state: str, outs: int) -> None:
    assert DEFAULT_RE24_TABLE[(outs, state)] == pytest.approx(TABLE[state][outs], abs=1e-9)
