"""Position-player WAR components against FanGraphs 2024 leaderboard rows (tests/golden/position_war_2024.yaml)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import polars as pl
import pytest
import yaml

from sabermetricspy.types.context import SeasonContext
from sabermetricspy.value import WARFramework, position_war

FIXTURE: dict[str, Any] = yaml.safe_load(
    (Path(__file__).parent / "golden" / "position_war_2024.yaml").read_text(encoding="utf-8")
)
ROWS: list[dict[str, Any]] = FIXTURE["rows"]
MLB_R, MLB_IP, MLB_PA = 21343.0, 129349 / 3, 182449.0
GAMES = float(FIXTURE["mlb_games"])
RPW = position_war.runs_per_win(MLB_R, MLB_IP)


def test_runs_per_win_formula() -> None:
    assert pytest.approx(9.6826, abs=1e-3) == RPW


@pytest.mark.parametrize("row", ROWS, ids=lambda r: r["player"])
def test_replacement_runs_match_fangraphs(row: dict[str, Any]) -> None:
    got = position_war.replacement_runs(
        row["pa"], runs_per_win_value=RPW, league_pa=MLB_PA, mlb_games=GAMES
    )
    assert got == pytest.approx(row["replacement"], abs=0.01)


@pytest.mark.parametrize("row", ROWS, ids=lambda r: r["player"])
def test_war_identity_with_published_components(row: dict[str, Any]) -> None:
    """WAR = (Offense + Defense + wLeague + Replacement) / RPW, with Defense = Fielding + Positional."""
    total = row["offense"] + row["defense"] + row["wleague"] + row["replacement"]
    assert total / RPW == pytest.approx(row["war"], abs=0.005)
    assert (row["fielding"] or 0.0) + row["positional"] == pytest.approx(row["defense"], abs=1e-6)


def test_dh_positional_prorated_by_games() -> None:
    ohtani = next(r for r in ROWS if r["player"] == "Shohei Ohtani")
    got = position_war.positional_runs(ohtani["dh_games"] * 9, -17.5)
    assert got == pytest.approx(ohtani["positional"], abs=1e-4)


def test_league_adjustment_is_proportional_to_pa() -> None:
    judge, witt = ROWS[0], ROWS[1]
    per_pa = [r["wleague"] / r["pa"] for r in (judge, witt)]
    assert per_pa[0] == pytest.approx(per_pa[1], rel=1e-4)
    assert position_war.league_adjustment(-1856.2, 704_000, 704) == pytest.approx(1.8562, abs=1e-3)


def test_framework_reproduces_ohtani_war() -> None:
    ohtani = next(r for r in ROWS if r["player"] == "Shohei Ohtani")
    ctx = SeasonContext.model_validate({"season": 2024})
    fw = WARFramework(ctx, season=2024, league_pa=MLB_PA, mlb_games=GAMES)
    assert fw.context.weights is not None
    rpw = fw.context.weights.lg_r_per_w
    df = pl.DataFrame(
        {
            "pa": [ohtani["pa"]],
            "batting_runs": [ohtani["offense"]],
            "position": ["DH"],
            "defensive_innings": [ohtani["dh_games"] * 9],
            "league_runs": [ohtani["wleague"]],
        }
    )
    out = fw.calculate_position_player_df(df).row(0, named=True)
    assert out["positional_runs"] == pytest.approx(ohtani["positional"], abs=1e-4)
    expected = (
        ohtani["offense"] + ohtani["positional"] + ohtani["wleague"] + out["replacement_runs"]
    ) / rpw
    assert out["war"] == pytest.approx(expected, abs=1e-5)
    assert out["war"] == pytest.approx(ohtani["war"], abs=0.01)
