"""League wSB constant: recomputed from sourced league totals and checked against FanGraphs player rows."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from sabermetricspy.constants import get_woba_weights

GOLDEN = Path(__file__).parent / "golden"
SBCS = yaml.safe_load((GOLDEN / "league_sbcs_snapshot.yaml").read_text("utf-8"))["seasons"]
TOTALS = yaml.safe_load((GOLDEN / "league_totals_snapshot.yaml").read_text("utf-8"))["batting"]

# FanGraphs 2024 leaderboard rows (stats=bat, qual=400, type=8, fetched 2026-10-18). The API field named wBsR equals
# wSB: the definition below reproduces it to three decimals for every player, which would not happen by chance.
# name, 1B, BB, IBB, HBP, SB, CS, published wSB
PLAYERS = [
    ("Judge", 85, 133, 20, 9, 10, 0, 0.36626859754323959),
    ("Witt", 123, 57, 9, 8, 31, 12, -0.072820417582988739),
    ("Ohtani", 98, 81, 10, 6, 59, 4, 8.7988006249070168),
    ("Soto", 90, 129, 2, 4, 7, 4, -1.9642509594559669),
    ("Henderson", 102, 78, 1, 7, 21, 4, 1.1119838654994965),
    ("Lindor", 96, 56, 0, 12, 29, 4, 2.8856171816587448),
    ("Duran", 108, 54, 1, 6, 34, 7, 2.6469207033514977),
    ("De La Cruz", 89, 69, 2, 6, 67, 16, 5.6413252353668213),
]


def test_snapshot_agrees_with_the_league_totals_snapshot() -> None:
    assert sorted(SBCS) == list(range(1990, 2026))
    for season, row in SBCS.items():
        t = TOTALS[season]
        assert (row["bb"], row["ibb"], row["hbp"]) == (t["bb"], t["ibb"], t["hbp"]), season
        assert row["b1"] == t["h"] - t["b2"] - t["b3"] - t["hr"], season


def test_bundled_lg_wsb_is_the_fangraphs_definition_for_every_season() -> None:
    """lgwSB = (lgSB*runSB + lgCS*runCS) / (lg1B + lgBB + lgHBP - lgIBB)."""
    for season, row in SBCS.items():
        w = get_woba_weights(season)
        expected = (row["sb"] * w.r_sb + row["cs"] * w.r_cs) / (
            row["b1"] + row["bb"] + row["hbp"] - row["ibb"]
        )
        assert w.lg_wsb == pytest.approx(expected, abs=1e-9), season


@pytest.mark.parametrize("player", PLAYERS, ids=[p[0] for p in PLAYERS])
def test_wsb_reproduces_fangraphs(player: tuple[str, int, int, int, int, int, int, float]) -> None:
    _, b1, bb, ibb, hbp, sb, cs, published = player
    w = get_woba_weights(2024)
    got = sb * w.r_sb + cs * w.r_cs - w.lg_wsb * (b1 + bb + hbp - ibb)
    assert got == pytest.approx(published, abs=0.002)
