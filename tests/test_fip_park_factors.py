"""Bundled FIP park factors (FanGraphs park page, FIP column) equal the values the FIP- fixtures were taken with."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
import yaml

from sabermetricspy.constants import ConstantsNotFoundError, get_fip_park_factor

ROWS: list[dict[str, Any]] = yaml.safe_load(
    (Path(__file__).parent / "golden" / "fip_minus_fangraphs.yaml").read_text("utf-8")
)["rows"]


@pytest.mark.full_constants
@pytest.mark.parametrize("row", ROWS, ids=lambda r: f"{r['player']} {r['season']}")
def test_bundled_factor_equals_the_fixture_factor(row: dict[str, Any]) -> None:
    assert get_fip_park_factor(row["team"], row["season"]) == row["pf_fip"]


@pytest.mark.full_constants
@pytest.mark.parametrize(
    ("season", "teams"), [(1990, 26), (1993, 28), (1998, 30), (2024, 30), (2026, 30)]
)
def test_every_franchise_has_a_factor(season: int, teams: int) -> None:
    from sabermetricspy.constants import _load_fip_park_table  # pyright: ignore[reportPrivateUsage]

    assert len(_load_fip_park_table()[season]) == teams


def test_unknown_team_or_season_raises_instead_of_defaulting() -> None:
    with pytest.raises(ValueError, match="No FIP park factor"):
        get_fip_park_factor("XXX", 2024)
    with pytest.raises(ConstantsNotFoundError, match="FIP park factors"):
        get_fip_park_factor("DET", 1980)
