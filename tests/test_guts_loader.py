"""A FanGraphs Guts! table you downloaded can be used as the wOBA constants; the library never fetches it."""

from __future__ import annotations

from pathlib import Path

import polars as pl
import pytest

import sabermetricspy as sp
from sabermetricspy.constants import ConstantsNotFoundError, constants_dir, get_woba_weights

WEB = {
    "Season": [2030, 2029],
    "wOBA": [0.320, 0.315],
    "wOBAScale": [1.2, 1.25],
    "wBB": [0.7, 0.69],
    "wHBP": [0.73, 0.72],
    "w1B": [0.9, 0.88],
    "w2B": [1.27, 1.25],
    "w3B": [1.6, 1.58],
    "wHR": [2.05, 2.03],
    "runSB": [0.2, 0.2],
    "runCS": [-0.41, -0.4],
    "R/PA": [0.12, 0.11],
    "R/W": [9.8, 9.7],
    "cFIP": [3.1, 3.2],
}


@pytest.fixture(autouse=True)
def _restore_constants() -> object:
    before = constants_dir()
    yield
    sp.use_constants(before)


def test_web_headers_load_from_a_frame_and_a_csv(tmp_path: Path) -> None:
    frame = pl.DataFrame(WEB)
    table = sp.load_guts(frame)
    assert sorted(table) == [2029, 2030]
    assert table[2030].w_hr == 2.05 and table[2030].lg_r_per_w == 9.8 and table[2030].c_fip == 3.1
    csv = tmp_path / "guts.csv"
    frame.write_csv(csv)
    assert sp.load_guts(csv)[2029].woba_scale == 1.25


def test_baseballr_style_names_also_work() -> None:
    renamed = pl.DataFrame(WEB).rename(
        {"wOBA": "lg_woba", "wOBAScale": "woba_scale", "R/PA": "lg_r_pa", "R/W": "lg_r_w"}
    )
    assert sp.load_guts(renamed)[2030].lg_woba == 0.32


def test_use_guts_feeds_the_lookup_and_a_missing_season_raises() -> None:
    sp.use_guts(pl.DataFrame(WEB))
    assert get_woba_weights(2030).w_bb == 0.7
    with pytest.raises(ConstantsNotFoundError, match="2031"):
        get_woba_weights(2031)


def test_use_constants_clears_the_guts_table() -> None:
    sp.use_guts(pl.DataFrame(WEB))
    sp.use_constants(constants_dir())
    with pytest.raises(ConstantsNotFoundError):
        get_woba_weights(2030)


def test_a_table_missing_a_column_says_which() -> None:
    with pytest.raises(ValueError, match="c_fip"):
        sp.load_guts(pl.DataFrame(WEB).drop("cFIP"))
