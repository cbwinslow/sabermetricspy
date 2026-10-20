"""Count run values follow Walsh's published table; the RE288 estimator has no invented defaults."""

from __future__ import annotations

from pathlib import Path

import polars as pl
import pytest
import yaml

import sabermetricspy as sp
from sabermetricspy.expectancy import (
    WALSH_COUNT_RUN_VALUES,
    RE288Results,
    _walk_transition,  # pyright: ignore[reportPrivateUsage]
    count_run_value,
)

REF = yaml.safe_load(
    (Path(__file__).parent / "golden" / "count_run_values.yaml").read_text("utf-8")
)


def _count(label: str) -> tuple[int, int]:
    balls, strikes = label.split("-")
    return int(balls), int(strikes)


@pytest.mark.parametrize("label", list(REF["counts"]))
def test_count_run_value_is_the_published_cell(label: str) -> None:
    balls, strikes = _count(label)
    assert count_run_value(balls, strikes) == pytest.approx(REF["counts"][label], abs=1e-9)


def test_table_covers_the_twelve_live_counts() -> None:
    assert len(WALSH_COUNT_RUN_VALUES) == 12 == len(REF["counts"])


@pytest.mark.parametrize("label", ["1-0", "0-1", "2-2", "1-1"])
def test_walsh_agrees_with_abdwr_2016(label: str) -> None:
    abdwr = REF["abdwr_2016"]
    assert count_run_value(*_count(label)) == pytest.approx(
        abdwr[label]["value"], abs=abdwr["tolerance"]
    )


def test_dead_count_is_rejected() -> None:
    with pytest.raises(ValueError, match="not a live count"):
        count_run_value(4, 0)


@pytest.mark.parametrize(
    ("before", "after", "runs"),
    [
        ("---", "1--", 0),
        ("1--", "12-", 0),
        ("-2-", "12-", 0),
        ("--3", "1-3", 0),
        ("12-", "123", 0),
        ("1-3", "123", 0),
        ("-23", "123", 0),
        ("123", "123", 1),
    ],
)
def test_walk_forces_runners_only(before: str, after: str, runs: int) -> None:
    assert _walk_transition(before) == (after, runs)


def _pitches() -> pl.DataFrame:
    # PA a reaches 0-2 and fouls one off (roi 3.0 on the repeat); PA b stops at 0-1.
    return pl.DataFrame(
        {
            "pa_id": ["a", "a", "a", "a", "b", "b"],
            "outs_before": [0] * 6,
            "base_state_before": ["---"] * 6,
            "balls": [0, 0, 0, 0, 0, 0],
            "strikes": [0, 1, 2, 2, 0, 1],
            "runs_rest_of_inning": [1.0, 1.0, 1.0, 3.0, 0.0, 0.0],
        }
    )


def test_fit_counts_each_plate_appearance_once_per_count() -> None:
    res = sp.CountExpectancyMatrix().fit(_pitches()).results
    assert res.state_expectancy["0|---|0|0"] == pytest.approx(0.5)
    assert res.state_expectancy["0|---|0|1"] == pytest.approx(0.5)
    # The foul-off repeat of 0-2 (roi 3.0) is ignored, so the mean is 1.0 and n is 1, not 2.0 and 2.
    assert res.state_expectancy["0|---|0|2"] == pytest.approx(1.0)
    assert res.state_counts["0|---|0|2"] == 1
    assert res.total_plate_appearances == 2


def test_fit_leaves_unobserved_states_unfitted() -> None:
    res = sp.CountExpectancyMatrix().fit(_pitches()).results
    assert len(res.state_expectancy) == 3
    assert res.lookup(2, "123", 3, 2) is None
    assert res.lookup(3, "123", 0, 0) == 0.0


def test_fit_requires_a_plate_appearance_id() -> None:
    with pytest.raises(ValueError, match="pa_id"):
        sp.CountExpectancyMatrix().fit(_pitches().drop("pa_id"))


def test_prior_strength_needs_a_caller_supplied_prior() -> None:
    with pytest.raises(ValueError, match="prior"):
        sp.CountExpectancyMatrix(prior_strength=10.0)


def test_shrinkage_moves_toward_the_supplied_prior() -> None:
    matrix = sp.CountExpectancyMatrix(prior={"0|---|0|0": 1.5}, prior_strength=2.0)
    res = matrix.fit(_pitches()).results
    # (2 * 0.5 + 2 * 1.5) / (2 + 2)
    assert res.state_expectancy["0|---|0|0"] == pytest.approx(1.0)
    # No prior for this state: left at the sample mean.
    assert res.state_expectancy["0|---|0|1"] == pytest.approx(0.5)


def test_leverage_uses_the_forced_advance_state_and_run_for_a_walk() -> None:
    res = RE288Results(
        state_expectancy={
            "0|123|0|0": 2.0,
            "0|123|3|1": 2.5,
            "0|1--|0|0": 0.8,
            "0|1--|3|2": 0.5,
        }
    )
    # Walk with the bases loaded forces in a run: 2.0 + 1 against a strike worth 2.5.
    assert res.count_leverage(0, "123", 3, 0) == pytest.approx(0.5)
    # 3-2 with a runner on first: a walk puts runners on 1st and 2nd (no 0-0 state fitted) -> unknown.
    assert res.count_leverage(0, "1--", 3, 2) is None


def test_transform_gives_null_for_unfitted_states() -> None:
    fitted = sp.CountExpectancyMatrix().fit(_pitches())
    out = fitted.transform(
        pl.DataFrame(
            {
                "outs_before": [0, 1],
                "base_state_before": ["---", "---"],
                "balls": [0, 0],
                "strikes": [0, 0],
                "outs_after": [0, 1],
                "base_state_after": ["---", "---"],
                "balls_after": [0, 1],
                "strikes_after": [1, 0],
                "runs_on_play": [0, 0],
            }
        )
    )
    assert out["re288_before"][0] == pytest.approx(0.5)
    assert out["pitch_run_value"][0] == pytest.approx(0.0)
    assert out["re288_before"][1] is None
    assert out["pitch_run_value"][1] is None
