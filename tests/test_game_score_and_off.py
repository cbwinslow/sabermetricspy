"""Game Score (James, Tango) on published games, and Off recomputed from the FanGraphs formula."""

from __future__ import annotations

from typing import Any

import polars as pl
import pytest

import sabermetricspy as sp
from sabermetricspy import Metric
from sabermetricspy.constants import get_woba_weights
from sabermetricspy.types.context import SeasonContext


def _value(row: dict[str, Any], metric: Metric) -> float:
    return sp.calculate(
        pl.DataFrame({"player_id": ["x"], **{k: [v] for k, v in row.items()}}), [metric]
    ).df.row(0, named=True)[metric.value]


def test_game_score_kerry_wood_1998() -> None:
    """27 outs, 20 K, 1 H: 50 + 27 + 10 + 20 - 2 = 105 (Wikipedia, Game score)."""
    row = dict(outs=27, so=20, h=1, er=0, r=0, bb=0)
    assert _value(row, Metric.GAME_SCORE) == 105


def test_game_score_scherzer_2015_no_hitter() -> None:
    assert _value(dict(outs=27, so=17, h=0, er=0, r=0, bb=0), Metric.GAME_SCORE) == 104


def test_game_score_counts_unearned_runs_and_partial_innings() -> None:
    """20 outs (6 complete innings, 2 after the fourth), 5 K, 6 H, 3 R of which 2 earned, 2 BB."""
    row = dict(outs=20, so=5, h=6, er=2, r=3, bb=2)
    assert _value(row, Metric.GAME_SCORE) == 50 + 20 + 2 * 2 + 5 - 12 - 8 - 2 - 2


def test_game_score_short_start_has_no_inning_bonus() -> None:
    assert (
        _value(dict(outs=9, so=2, h=4, er=3, r=3, bb=1), Metric.GAME_SCORE)
        == 50 + 9 + 2 - 8 - 12 - 1
    )


def test_game_score_v2_hand_computed_from_the_fangraphs_formula() -> None:
    """7 IP, 8 K, 2 BB, 5 H including 1 HR, 2 R: 40 + 42 + 8 - 4 - 8 - 8 - 6 = 64."""
    row = dict(outs=21, so=8, bb=2, h=5, hr=1, r=2)
    assert _value(row, Metric.GAME_SCORE_V2) == 64


def test_off_is_the_fangraphs_composition() -> None:
    line = dict(pa=600, ab=520, h=160, b2=30, b3=3, hr=25, bb=70, hbp=5, sf=4, sb=15, cs=4)
    ctx = SeasonContext(season=2024, league="AL", park_factor=105.0)
    frame = pl.DataFrame({"player_id": ["x"], **{k: [v] for k, v in line.items()}})
    row = sp.calculate(frame, [Metric.WRAA, Metric.BSR, Metric.OFF], context=ctx).df.row(
        0, named=True
    )
    w = get_woba_weights(2024)
    denominator = w.wrc_per_pa_for("AL") or w.lg_r_per_pa
    expected = (
        row["wraa"]
        + (w.lg_r_per_pa - 1.05 * w.lg_r_per_pa) * 600
        + (w.lg_r_per_pa - denominator) * 600
        + row["bsr"]
    )
    assert row["off"] == pytest.approx(expected, abs=1e-9)


def test_off_equals_wraa_plus_bsr_in_a_neutral_park_when_league_constants_agree() -> None:
    """With park factor 100 only the league term and BsR separate Off from wRAA."""
    line = dict(pa=500, ab=450, h=120, b2=20, b3=2, hr=15, bb=40, hbp=3, sf=3, sb=5, cs=2)
    frame = pl.DataFrame({"player_id": ["x"], **{k: [v] for k, v in line.items()}})
    row = sp.calculate(frame, [Metric.WRAA, Metric.BSR, Metric.OFF]).df.row(0, named=True)
    w = get_woba_weights(2024)
    league_term = (w.lg_r_per_pa - (w.wrc_per_pa_for("MLB") or w.lg_r_per_pa)) * 500
    assert row["off"] == pytest.approx(row["wraa"] + league_term + row["bsr"], abs=1e-9)


def _era_minus(er: int, outs: int, park_factor: float, lg_era: float) -> float:
    weights = get_woba_weights(2014).model_copy(update={"lg_era_nl": lg_era})
    frame = pl.DataFrame({"player_id": ["x"], "er": [er], "outs": [outs]})
    ctx = SeasonContext(season=2014, league="NL", park_factor=park_factor, weights=weights)
    return sp.calculate(frame, [Metric.ERA_MINUS], context=ctx).df["era_minus"][0]


@pytest.mark.parametrize(("park_factor", "published"), [(95.0, 86), (98.0, 84), (102.0, 80)])
def test_era_minus_reproduces_the_fangraphs_library_table(
    park_factor: float, published: int
) -> None:
    """FanGraphs Library (ERA-, FIP-, xFIP-): a 3.00 ERA in the NL (3.66 in 2014) with park factors 95, 98, 102."""
    assert round(_era_minus(10, 90, park_factor, 3.66)) == published


def test_era_minus_reproduces_the_kershaw_2014_example() -> None:
    """ERA 1.77, park factor 96 and NL ERA 3.66 give 50 (100 x 1.77 x 1.04 / 3.66 = 50.3)."""
    assert round(_era_minus(59, 900, 96.0, 3.66)) == 50  # ERA = 27 * 59 / 900 = 1.77
