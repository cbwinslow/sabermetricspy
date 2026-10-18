"""WinProbabilityModel against rows of Tom Tango's published win-expectancy table."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from sabermetricspy.expectancy import WinProbabilityModel

REF = yaml.safe_load(
    (Path(__file__).parent / "golden" / "win_expectancy_tango.yaml").read_text("utf-8")
)
MODEL = WinProbabilityModel.from_default()
ORDER = ("---", "1--", "-2-", "12-", "--3", "1-3", "-23", "123")


def _cells() -> list[tuple[str, int, str, int, int, str, float]]:
    cells = []
    for key, inning, half, diff in (
        ("bottom9_tied", 9, "bottom", 0),
        ("bottom9_trailing_1", 9, "bottom", -1),
    ):
        for state, values in REF[key].items():
            cells += [(key, inning, half, diff, outs, state, v) for outs, v in enumerate(values)]
    cells += [
        ("top9_tied_empty", 9, "top", 0, o, "---", v) for o, v in enumerate(REF["top9_tied_empty"])
    ]
    cells += [
        ("bottom7_tied_empty", 7, "bottom", 0, o, "---", v)
        for o, v in enumerate(REF["bottom7_tied_empty"])
    ]
    return cells


def test_published_rows_are_internally_consistent() -> None:
    """Recomputation gate: more outs lower the home win expectancy in the bottom of the 9th; more runners raise it."""
    for key in ("bottom9_tied", "bottom9_trailing_1"):
        table = REF[key]
        for values in table.values():
            assert values[0] > values[1] > values[2]
        for outs in range(3):
            assert table["---"][outs] < table["1--"][outs] < table["12-"][outs]


def test_model_stays_within_the_stated_gap_of_the_published_table() -> None:
    errors = [
        abs(MODEL.home_win_probability(inning, half, outs, state, diff) - value)
        for _, inning, half, diff, outs, state, value in _cells()
    ]
    assert len(errors) == 54
    assert max(errors) < 0.20
    assert sum(errors) / len(errors) < 0.05


@pytest.mark.parametrize("state", ["---", "1--", "12-", "123"])
def test_model_orders_outs_and_runners_like_the_table(state: str) -> None:
    wp = [MODEL.home_win_probability(9, "bottom", o, state, 0) for o in range(3)]
    assert wp[0] > wp[1] > wp[2]
