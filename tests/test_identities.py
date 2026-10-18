"""Property tests: rates computed with `by=` must equal rates computed from summed counts (never averaged)."""

from __future__ import annotations

import math

import polars as pl
from hypothesis import given, settings
from hypothesis import strategies as st

import sabermetricspy as sp
from sabermetricspy import Metric
from sabermetricspy.constants import get_woba_weights

_game = st.fixed_dictionaries(
    {
        "b1": st.integers(0, 4),
        "b2": st.integers(0, 2),
        "b3": st.integers(0, 1),
        "hr": st.integers(0, 2),
        "outs_in_play": st.integers(0, 6),
        "so": st.integers(0, 4),
        "bb": st.integers(0, 3),
        "hbp": st.integers(0, 1),
        "sf": st.integers(0, 1),
    }
)


def _batting_frame(games: list[dict[str, int]]) -> pl.DataFrame:
    rows = []
    for g in games:
        h = g["b1"] + g["b2"] + g["b3"] + g["hr"]
        ab = h + g["outs_in_play"] + g["so"]
        rows.append(
            dict(
                player_id="p",
                pa=ab + g["bb"] + g["hbp"] + g["sf"],
                ab=ab,
                h=h,
                b2=g["b2"],
                b3=g["b3"],
                hr=g["hr"],
                bb=g["bb"],
                hbp=g["hbp"],
                sf=g["sf"],
                so=g["so"],
            )
        )
    return pl.DataFrame(rows)


@given(
    games=st.lists(_game, min_size=1, max_size=8).filter(
        lambda gs: (
            sum(g["b1"] + g["b2"] + g["b3"] + g["hr"] + g["outs_in_play"] + g["so"] for g in gs) > 0
        )
    )
)
@settings(max_examples=60, deadline=None)
def test_grouped_batting_rates_equal_rates_of_summed_counts(games: list[dict[str, int]]) -> None:
    df = _batting_frame(games)
    res = sp.calculate(
        df, [Metric.AVG, Metric.OBP, Metric.SLG, Metric.OPS, Metric.ISO], by="player_id"
    ).df.row(0, named=True)

    t = {c: int(df[c].sum()) for c in ("pa", "ab", "h", "b2", "b3", "hr", "bb", "hbp", "sf", "so")}
    tb = (t["h"] - t["b2"] - t["b3"] - t["hr"]) + 2 * t["b2"] + 3 * t["b3"] + 4 * t["hr"]
    obp_den = t["ab"] + t["bb"] + t["hbp"] + t["sf"]
    expected_avg = t["h"] / t["ab"]
    expected_obp = (t["h"] + t["bb"] + t["hbp"]) / obp_den
    expected_slg = tb / t["ab"]
    assert math.isclose(res["avg"], expected_avg, abs_tol=1e-9)
    assert math.isclose(res["obp"], expected_obp, abs_tol=1e-9)
    assert math.isclose(res["slg"], expected_slg, abs_tol=1e-9)
    assert math.isclose(res["ops"], res["obp"] + res["slg"], abs_tol=1e-9)
    assert math.isclose(res["iso"], res["slg"] - res["avg"], abs_tol=1e-9)


_pitch_game = st.fixed_dictionaries(
    {
        "outs": st.integers(3, 27),
        "hr": st.integers(0, 3),
        "bb": st.integers(0, 5),
        "ibb": st.integers(0, 1),
        "hbp": st.integers(0, 2),
        "so": st.integers(0, 12),
        "er": st.integers(0, 8),
        "h": st.integers(0, 10),
    }
)


@given(games=st.lists(_pitch_game, min_size=1, max_size=8))
@settings(max_examples=60, deadline=None)
def test_grouped_pitching_rates_equal_rates_of_summed_counts(games: list[dict[str, int]]) -> None:
    rows = [dict(player_id="p", **{**g, "ibb": min(g["ibb"], g["bb"])}) for g in games]
    df = pl.DataFrame(rows)
    res = sp.calculate(
        df, [Metric.ERA, Metric.WHIP, Metric.FIP], season=2024, by="player_id"
    ).df.row(0, named=True)
    t = {c: int(df[c].sum()) for c in ("outs", "hr", "bb", "hbp", "so", "er", "h")}
    ip = t["outs"] / 3.0
    c_fip = get_woba_weights(2024).c_fip
    assert math.isclose(res["era"], 9 * t["er"] / ip, abs_tol=1e-9)
    assert math.isclose(res["whip"], (t["bb"] + t["h"]) / ip, abs_tol=1e-9)
    assert math.isclose(
        res["fip"],
        (13 * t["hr"] + 3 * (t["bb"] + t["hbp"]) - 2 * t["so"]) / ip + c_fip,
        abs_tol=1e-9,
    )
