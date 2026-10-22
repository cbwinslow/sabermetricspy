"""Opt-in check of the id crosswalk against the real Chadwick Register and published player pages.

Runs only when the register is present, either at `$SABERMETRICSPY_REGISTER` or the default cache directory (fetch it with
your own download of the Chadwick Register (https://github.com/chadwickbureau/register); ODC-BY 1.0, credit the Chadwick Bureau). The Retrosheet cross-check also needs
`SABERMETRICSPY_RETRO2016` (see tests/test_retrosheet_2016_count_fit.py).

Published ids, each read on 2026-10-20:
- Mike Trout: baseballsavant.mlb.com/savant-player/545361, baseball-reference.com/players/t/troutmi01.shtml and
  fangraphs.com/players/mike-trout/10155/stats all open his page.
- Tarik Skubal: Savant 669373, Baseball-Reference skubata01, FanGraphs 22267.
- Retrosheet id troum001: Mike Trout has 681 plate appearances in 2016 on his Baseball-Reference line (159 G), and the
  Retrosheet 2016 event file gives 681 batting events for the id the register maps to MLBAM 545361.
"""

from __future__ import annotations

import os
from typing import Any

import polars as pl
import pytest

from sabermetricspy.ids import (
    PlayerRegister,
    default_register_path,
    find_players,
    load_register,
    player_id,
    translate_ids,
)

_PATH = default_register_path()
pytestmark = pytest.mark.skipif(
    not (_PATH / "people-0.csv").is_file(),
    reason="Chadwick Register not found; set SABERMETRICSPY_REGISTER to a downloaded copy",
)

PUBLISHED = {
    "trout": {"mlbam": 545361, "bbref": "troutmi01", "fangraphs": 10155, "retro": "troum001"},
    "skubal": {"mlbam": 669373, "bbref": "skubata01", "fangraphs": 22267, "retro": "skubt001"},
}


@pytest.fixture(scope="module")
def register() -> PlayerRegister:
    return load_register()


@pytest.mark.parametrize(
    ("key", "first", "last", "born"),
    [("trout", "Mike", "Trout", 1991), ("skubal", "Tarik", "Skubal", 1996)],
)
def test_published_ids(
    register: PlayerRegister, key: str, first: str, last: str, born: int
) -> None:
    for system, expected in PUBLISHED[key].items():
        assert player_id(system, first, last, birth_year=born, register=register) == expected


def test_griffey_father_and_son_are_two_people(register: PlayerRegister) -> None:
    both = find_players("Ken", "Griffey", register=register)
    assert both.height >= 2
    assert player_id("bbref", "Ken", "Griffey", birth_year=1969, register=register) == "griffke02"
    assert player_id("bbref", "Ken", "Griffey", birth_year=1950, register=register) == "griffke01"
    with pytest.raises(ValueError, match="narrow with birth_year"):
        player_id("bbref", "Ken", "Griffey", register=register)


def test_round_trip_through_every_integer_and_string_system(register: PlayerRegister) -> None:
    frame = pl.DataFrame({"key_mlbam": [545361, 669373, 408234, 514888]})
    to_retro = translate_ids(frame, "mlbam", "retro", register=register).df
    back = translate_ids(to_retro, "retro", "mlbam", output="mlbam_again", register=register).df
    assert back["key_mlbam"].to_list() == back["mlbam_again"].to_list()
    assert to_retro["key_retro"].to_list() == ["troum001", "skubt001", "cabrm001", "altuj001"]


def test_retrosheet_2016_batters_all_map_and_trout_has_681_plate_appearances(
    register: PlayerRegister,
) -> None:
    path = os.environ.get("SABERMETRICSPY_RETRO2016")
    if not path:
        pytest.skip("set SABERMETRICSPY_RETRO2016 to retro2016.rda")
    import pyreadr  # pyright: ignore[reportMissingImports]

    frame: Any = pyreadr.read_r(path)["retro2016"]
    events = pl.from_pandas(frame).filter(pl.col("bat_event_fl"))
    res = translate_ids(
        events.select(pl.col("bat_id").alias("key_retro")), "retro", "mlbam", register=register
    )
    assert res.unmatched / res.df.height < 0.001
    assert res.df.filter(pl.col("key_mlbam") == 545361).height == 681
