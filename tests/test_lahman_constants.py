"""League constants computed from the Lahman database agree with the values bundled from FanGraphs Guts!.

The fixture is a sample of the SABR Lahman Baseball Database (tests/fixtures/lahman, CC BY-SA 3.0). FanGraphs prints
cFIP, runs per PA and the caught-stealing run value to three decimals, so those bounds are rounding; OBP and SLG are
printed in full. The computed values are the ones that can replace a bundled table without shipping anyone's data.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from sabermetricspy.constants import get_woba_weights
from sabermetricspy.lahman import LeagueConstants, league_constants

FIXTURE = Path(__file__).parent / "fixtures" / "lahman"
SEASONS = [2002, 2016, 2019, 2020, 2024]


def _lc(season: int, league: str = "MLB") -> LeagueConstants:
    return league_constants(season, league=league, lahman_dir=FIXTURE)


@pytest.mark.parametrize("season", SEASONS)
def test_constants_match_the_bundled_fangraphs_values(season: int) -> None:
    got, ref = _lc(season), get_woba_weights(season)
    assert got.c_fip == pytest.approx(ref.c_fip, abs=0.0011)
    assert got.lg_r_per_pa == pytest.approx(ref.lg_r_per_pa, abs=0.0011)
    assert got.r_cs == pytest.approx(ref.r_cs, abs=0.0011)
    assert ref.lg_era is not None
    assert got.lg_era == pytest.approx(ref.lg_era, abs=0.001)


@pytest.mark.parametrize("season", SEASONS)
def test_league_obp_and_slg_match_to_the_printed_digits(season: int) -> None:
    got = _lc(season)
    import yaml

    table = yaml.safe_load(
        (
            Path(__file__).parent.parent
            / "src"
            / "sabermetricspy"
            / "data"
            / "constants"
            / "woba_fangraphs.yaml"
        ).read_text("utf-8")
    )["seasons"][season]
    assert got.lg_obp == pytest.approx(table["lg_obp"], abs=1e-5)
    assert got.lg_slg == pytest.approx(table["lg_slg"], abs=1e-5)


def test_kwera_constant_equals_the_league_definition_through_2020() -> None:
    for season in (2002, 2016, 2019, 2020):
        ref = get_woba_weights(season).kwera_constant
        assert ref is not None
        assert _lc(season).kwera_constant == pytest.approx(ref, abs=0.002)


def test_hand_checkable_identities() -> None:
    got = _lc(2024)
    assert got.lg_r_per_pa == pytest.approx(got.runs / got.pa, abs=1e-12)
    assert got.r_cs == pytest.approx(-(2 * got.runs / got.outs + 0.075), abs=1e-12)
    assert got.runs == 21343


def test_leagues_split_and_sum() -> None:
    al, nl, mlb = _lc(2024, "AL"), _lc(2024, "NL"), _lc(2024)
    assert al.runs + nl.runs == mlb.runs
    assert al.outs + nl.outs == mlb.outs


def test_bad_inputs_raise(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError, match="download_lahman"):
        league_constants(2024, lahman_dir=tmp_path)
    with pytest.raises(ValueError, match="league must be"):
        league_constants(2024, league="XX", lahman_dir=FIXTURE)
    with pytest.raises(ValueError, match="No Lahman rows"):
        league_constants(1950, lahman_dir=FIXTURE)
