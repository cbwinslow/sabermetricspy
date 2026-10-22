"""League constants computed from Lahman-format files you supply.

The unit tests use small hand-made files whose totals can be checked by hand. The comparison with the published
FanGraphs values runs only when `SABERMETRICSPY_LAHMAN` names a directory holding the official database
(https://sabr.org/lahman-database/, CC BY-SA 3.0) and the full local constants table is present.
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from sabermetricspy.constants import get_woba_weights
from sabermetricspy.lahman import LeagueConstants, league_constants

BATTING_HEADER = "playerID,yearID,stint,teamID,lgID,AB,R,H,2B,3B,HR,SB,CS,BB,SO,IBB,HBP,SH,SF"
PITCHING_HEADER = "playerID,yearID,stint,teamID,lgID,IPouts,ER,R,HR,BB,HBP,SO,BFP"
BATTING_ROWS = [
    # AL: AB 100, H 30 (2B 5, 3B 1, HR 4), BB 10, HBP 2, SF 3, SH 1, R 20
    "a1,2024,1,AAA,AL,100,20,30,5,1,4,3,1,10,25,1,2,1,3",
    # NL: AB 200, H 50 (2B 10, 3B 2, HR 6), BB 20, HBP 4, SF 6, SH 2, R 40
    "n1,2024,1,NNN,NL,200,40,50,10,2,6,5,2,20,50,2,4,2,6",
    "x1,2023,1,AAA,AL,999,999,999,0,0,0,0,0,0,0,0,0,0,0",
]
PITCHING_ROWS = [
    # AL: 90 outs (30 IP), ER 12, R 20, HR 4, BB 10, HBP 2, SO 25, BFP 130
    "ap,2024,1,AAA,AL,90,12,20,4,10,2,25,130",
    # NL: 180 outs (60 IP), ER 24, R 40, HR 6, BB 20, HBP 4, SO 50, BFP 260
    "np,2024,1,NNN,NL,180,24,40,6,20,4,50,260",
]


@pytest.fixture
def lahman_dir(tmp_path: Path) -> Path:
    (tmp_path / "Batting.csv").write_text("\n".join([BATTING_HEADER, *BATTING_ROWS]) + "\n")
    (tmp_path / "Pitching.csv").write_text("\n".join([PITCHING_HEADER, *PITCHING_ROWS]) + "\n")
    return tmp_path


def _mlb(lahman_dir: Path, league: str = "MLB") -> LeagueConstants:
    return league_constants(2024, league=league, lahman_dir=lahman_dir)


def test_league_sums_and_rates_match_a_hand_calculation(lahman_dir: Path) -> None:
    got = _mlb(lahman_dir)
    # PA = AB + BB + HBP + SF + SH = 300 + 30 + 6 + 9 + 3
    assert got.pa == 348
    assert got.runs == 60
    assert got.outs == 270
    assert got.lg_r_per_pa == pytest.approx(60 / 348, abs=1e-12)
    assert got.lg_obp == pytest.approx((80 + 30 + 6) / (300 + 30 + 6 + 9), abs=1e-12)
    # TB = 1B + 2*2B + 3*3B + 4*HR with 1B = 80 - 15 - 3 - 10 = 52
    assert got.lg_slg == pytest.approx((52 + 30 + 9 + 40) / 300, abs=1e-12)


def test_era_fip_constant_and_kwera_follow_their_definitions(lahman_dir: Path) -> None:
    got = _mlb(lahman_dir)
    ip, er = 90.0, 36.0
    assert got.lg_era == pytest.approx(9 * er / ip, abs=1e-12)
    numerator = 13 * 10 + 3 * (30 + 6) - 2 * 75
    assert got.c_fip == pytest.approx(9 * er / ip - numerator / ip, abs=1e-12)
    assert got.kwera_constant == pytest.approx(9 * er / ip + 12 * (75 - 30) / 390, abs=1e-12)


def test_caught_stealing_value_is_two_runs_per_out_plus_a_constant(lahman_dir: Path) -> None:
    got = _mlb(lahman_dir)
    assert got.runs_per_out == pytest.approx(60 / 270, abs=1e-12)
    assert got.r_cs == pytest.approx(-(2 * 60 / 270 + 0.075), abs=1e-12)


def test_leagues_split_and_sum(lahman_dir: Path) -> None:
    al, nl, both = _mlb(lahman_dir, "AL"), _mlb(lahman_dir, "NL"), _mlb(lahman_dir)
    assert (al.runs, nl.runs) == (20, 40)
    assert al.runs + nl.runs == both.runs
    assert al.outs + nl.outs == both.outs
    assert al.lg_era == pytest.approx(9 * 12 / 30, abs=1e-12)


def test_other_seasons_are_not_mixed_in(lahman_dir: Path) -> None:
    assert _mlb(lahman_dir).runs == 60  # the 2023 row with 999 runs is ignored


def test_bad_inputs_raise(tmp_path: Path, lahman_dir: Path) -> None:
    empty = tmp_path / "empty"
    empty.mkdir()
    with pytest.raises(FileNotFoundError, match=r"sabr\.org"):
        league_constants(2024, lahman_dir=empty)
    with pytest.raises(ValueError, match="league must be"):
        league_constants(2024, league="XX", lahman_dir=lahman_dir)
    with pytest.raises(ValueError, match="No Lahman rows"):
        league_constants(1950, lahman_dir=lahman_dir)


def test_no_directory_says_where_to_get_the_database(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("SABERMETRICSPY_LAHMAN", raising=False)
    with pytest.raises(FileNotFoundError, match=r"sabr\.org"):
        league_constants(2024)


REAL = os.environ.get("SABERMETRICSPY_LAHMAN")


@pytest.mark.skipif(not REAL, reason="set SABERMETRICSPY_LAHMAN to the official Lahman download")
@pytest.mark.parametrize("season", [2002, 2016, 2019, 2020, 2024])
def test_real_database_matches_the_published_fangraphs_values(season: int) -> None:
    got, ref = league_constants(season, lahman_dir=REAL), get_woba_weights(season)
    assert ref.season == season
    assert got.c_fip == pytest.approx(ref.c_fip, abs=0.0011)
    assert got.lg_r_per_pa == pytest.approx(ref.lg_r_per_pa, abs=0.0011)
    assert got.r_cs == pytest.approx(ref.r_cs, abs=0.0011)
    assert got.lg_obp == pytest.approx(ref.lg_obp, abs=1e-5)
    assert got.lg_slg == pytest.approx(ref.lg_slg, abs=1e-5)
