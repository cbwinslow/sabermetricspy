"""WinExpectancyMatrix.fit() is the observed home win rate per state, pinned by hand-computed values."""

from __future__ import annotations

import math

import polars as pl
import pytest

import sabermetricspy as sp


def _frame() -> pl.DataFrame:
    # State A (bottom 9, 1 out, bases empty, tied): games g1 (home won, two PAs), g2 (home lost), g3 (home won).
    # State B (top 1, 0 out, bases empty, tied): every game once; home won g1 and g3 only.
    rows = []
    for gid, win in (("g1", 1), ("g2", 0), ("g3", 1)):
        rows.append((gid, 9, True, 1, "---", 0, win))
        rows.append((gid, 1, False, 0, "---", 0, win))
    rows.append(("g1", 9, True, 1, "---", 0, 1))
    return pl.DataFrame(
        rows,
        schema=[
            "game_id",
            "inning",
            "is_bottom",
            "outs_before",
            "base_state_before",
            "home_score_diff",
            "home_win",
        ],
        orient="row",
    )


def test_fit_is_the_home_win_rate_in_each_state() -> None:
    res = sp.WinExpectancyMatrix().fit(_frame()).results
    assert res.lookup(9, "bottom", 1, "---", 0) == pytest.approx(3 / 4)  # 4 PAs, 3 in home wins
    assert res.state_counts["9|bottom|1|---|0"] == 4
    assert res.state_games["9|bottom|1|---|0"] == 3
    assert res.lookup(1, "top", 0, "---", 0) == pytest.approx(2 / 3)


def test_standard_error_counts_games_not_plate_appearances() -> None:
    res = sp.WinExpectancyMatrix().fit(_frame()).results
    se = res.standard_error(9, "bottom", 1, "---", 0)
    assert se == pytest.approx(math.sqrt(0.75 * 0.25 / 3))


def test_unobserved_state_is_none_and_half_aliases_agree() -> None:
    res = sp.WinExpectancyMatrix().fit(_frame()).results
    assert res.lookup(9, "bottom", 0, "123", 4) is None
    assert res.standard_error(9, "bottom", 0, "123", 4) is None
    assert res.lookup(1, "away", 0, "---", 0) == res.lookup(1, "top", 0, "---", 0)


def test_missing_columns_and_unfitted_model_raise() -> None:
    with pytest.raises(ValueError, match="missing columns"):
        sp.WinExpectancyMatrix().fit(_frame().drop("home_win"))
    with pytest.raises(RuntimeError, match="not fitted"):
        _ = sp.WinExpectancyMatrix().results
