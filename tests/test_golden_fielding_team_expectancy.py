"""Fielding, baserunning, team and expectancy metrics against Baseball-Reference and FanGraphs published values."""

from __future__ import annotations

from typing import Any

import polars as pl
import pytest
import yaml
from golden_loader import GOLDEN_DIR

import sabermetricspy as sp
from sabermetricspy import Metric
from sabermetricspy.types.context import SeasonContext

REF: dict[str, Any] = yaml.safe_load(
    (GOLDEN_DIR / "fielding_team_expectancy.yaml").read_text(encoding="utf-8")
)


def _row(inputs: dict[str, Any], metrics: list[Metric], **kwargs: Any) -> dict[str, Any]:
    cols = {k: [v] for k, v in inputs.items() if k != "inn"}
    return sp.calculate(pl.DataFrame({"player_id": ["x"], **cols}), metrics, **kwargs).df.row(
        0, named=True
    )


@pytest.mark.parametrize("entry", REF["fielding"], ids=lambda e: e["id"])
def test_fielding_rates_match_baseball_reference(entry: dict[str, Any]) -> None:
    metrics = [Metric.TC, Metric.FPCT, Metric.RF_PER_G, Metric.RF_PER_9, Metric.SB_PCT]
    row = _row(entry["inputs"], metrics)
    pub, tol = entry["published"], entry["tolerance"]
    for key in ("tc", "fpct", "rf_per_g", "rf_per_9", "sb_pct"):
        if key in pub:
            assert row[key] == pytest.approx(pub[key], abs=tol[key]), key


def test_error_rate_is_the_complement_of_fielding_percentage() -> None:
    for entry in REF["fielding"]:
        row = _row(entry["inputs"], [Metric.FPCT, Metric.ERR_PCT])
        assert row["err_pct"] == pytest.approx(1.0 - row["fpct"], abs=1e-12)


def test_catcher_caught_stealing_rate_matches_baseball_reference() -> None:
    entry = next(e for e in REF["fielding"] if e["id"] == "contreras_2024_c")
    row = _row(entry["inputs"], [Metric.CATCHER_CS_PCT])
    assert row["catcher_cs_pct"] == pytest.approx(
        entry["published"]["catcher_cs_pct"], abs=entry["tolerance"]["catcher_cs_pct"]
    )


@pytest.mark.parametrize("entry", REF["team"], ids=lambda e: e["id"])
def test_team_rates_match_baseball_reference(entry: dict[str, Any]) -> None:
    row = _row(
        entry["inputs"],
        [
            Metric.WIN_PCT,
            Metric.RUN_DIFF,
            Metric.PYTHAG_WIN_PCT,
            Metric.PYTHAG_WINS,
            Metric.PYTHAG_LUCK,
        ],
        context=SeasonContext(season=2024),
    )
    assert row["win_pct"] == pytest.approx(entry["published"]["win_pct"], abs=0.0005)
    assert row["run_diff"] == entry["inputs"]["rs"] - entry["inputs"]["ra"]
    assert round(row["pythag_wins"]) == entry["published"]["pythag_wins"]
    assert row["pythag_luck"] == pytest.approx(entry["inputs"]["w"] - row["pythag_wins"], abs=1e-9)


def test_default_pythagorean_exponent_is_the_baseball_reference_one() -> None:
    """The exponent matters: exponent 2 moves at least one of the teams off Baseball-Reference's rounded wins."""
    differs = 0
    for entry in REF["team"]:
        row = _row(
            entry["inputs"],
            [Metric.PYTHAG_WINS],
            context=SeasonContext(season=2024, pythag_exponent=2.0),
        )
        differs += round(row["pythag_wins"]) != entry["published"]["pythag_wins"]
    assert differs >= 1


@pytest.mark.parametrize("batter", REF["expectancy"]["batters"], ids=lambda b: b["player"])
def test_clutch_matches_fangraphs(batter: dict[str, Any]) -> None:
    row = _row(
        {
            "wpa": batter["wpa"],
            "pa": batter["pa"],
            "li_sum": batter["pli"] * batter["pa"],
            "wpa_li_sum": batter["wpa_li"],
        },
        [Metric.PLI, Metric.WPA_LI, Metric.CLUTCH],
    )
    assert row["pli"] == pytest.approx(batter["pli"], abs=1e-9)
    assert row["wpa_li"] == pytest.approx(batter["wpa_li"], abs=1e-6)
    assert row["clutch"] == pytest.approx(batter["clutch"], abs=1e-5)


@pytest.mark.parametrize("batter", REF["expectancy"]["batters"], ids=lambda b: b["player"])
def test_rew_uses_a_league_constant_where_fangraphs_uses_a_player_runs_per_win(
    batter: dict[str, Any],
) -> None:
    """REW is approximate: FanGraphs' implied runs per win varies by player (9.57 to 10.09); the library uses one."""
    row = _row({"re24": batter["re24"]}, [Metric.REW], context=SeasonContext(season=2024))
    assert row["rew"] == pytest.approx(batter["rew"], rel=0.06)
