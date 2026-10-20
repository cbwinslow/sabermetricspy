"""MarkovChainModel.fit_transitions(): hand-computed chain, then the Albert-Baumer-Marchi printed 2016 values (opt-in)."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import polars as pl
import pytest
import yaml

from sabermetricspy.models import MarkovChainModel

REF = yaml.safe_load(
    (Path(__file__).parent / "golden" / "markov_abdwr_2016.yaml").read_text("utf-8")
)
BASES = ("---", "1--", "-2-", "--3", "12-", "1-3", "-23", "123")
PATH = os.environ.get("SABERMETRICSPY_RETRO2016")


def _half_unit(printed: float, floor: int) -> float:
    """Half a unit in the last printed decimal; YAML drops trailing zeros, so `floor` is the book's minimum digits."""
    text = repr(float(printed))
    decimals = max(floor, len(text.split(".")[1]) if "e" not in text else floor)
    return 0.5 * 10**-decimals


def _home_run_or_out(hr_per_100: int) -> pl.DataFrame:
    """Every state observed: `hr_per_100` of 100 plays are home runs, the rest outs."""
    rows = []
    for outs in range(3):
        for bases in BASES:
            runners = sum(c != "-" for c in bases)
            rows += [(outs, bases, outs, "---", runners + 1)] * hr_per_100
            rows += [(outs, bases, outs + 1, bases, 0)] * (100 - hr_per_100)
    return pl.DataFrame(
        rows,
        schema=[
            "outs_before",
            "base_state_before",
            "outs_after",
            "base_state_after",
            "runs_on_play",
        ],
        orient="row",
    )


def test_home_run_or_out_chain_matches_the_negative_binomial_closed_form() -> None:
    """Runs before the third out are the home runs in a run of Bernoulli(p) trials: E = 3 p / (1 - p)."""
    res = MarkovChainModel().fit_transitions(_home_run_or_out(10)).results
    assert res.expected_runs_per_half_inning == pytest.approx(3 * 0.1 / 0.9)
    assert res.expected_pa_per_half_inning == pytest.approx(3 / 0.9)
    assert res.plate_appearances == 24 * 100


def test_state_distribution_after_one_batter_is_the_first_row() -> None:
    model = MarkovChainModel().fit_transitions(_home_run_or_out(10))
    assert model.state_distribution(1) == pytest.approx({"0|---": 0.1, "1|---": 0.9})
    assert model.state_distribution(0) == {"0|---": 1.0}


def test_unobserved_state_and_missing_columns_raise() -> None:
    with pytest.raises(ValueError, match="No plays observed"):
        MarkovChainModel().fit_transitions(_home_run_or_out(10).filter(pl.col("outs_before") < 2))
    with pytest.raises(ValueError, match="missing columns"):
        MarkovChainModel().fit_transitions(_home_run_or_out(10).drop("runs_on_play"))


def _batting_plays() -> pl.DataFrame:
    """The book's retro2016_complete: batting plays in complete half-innings that change the state or the score."""
    import pyreadr  # pyright: ignore[reportMissingImports]

    frame: Any = pyreadr.read_r(PATH)["retro2016"]
    dests = ["bat_dest_id", "run1_dest_id", "run2_dest_id", "run3_dest_id"]

    def occupied(col: str) -> pl.Expr:
        return pl.col(col).is_not_null() & (pl.col(col) != "")

    def bases(b1: pl.Expr, b2: pl.Expr, b3: pl.Expr) -> pl.Expr:
        return (
            pl.when(b1).then(pl.lit("1")).otherwise(pl.lit("-"))
            + pl.when(b2).then(pl.lit("2")).otherwise(pl.lit("-"))
            + pl.when(b3).then(pl.lit("3")).otherwise(pl.lit("-"))
        )

    ev = (
        pl.from_pandas(frame)
        .with_columns(
            pl.sum_horizontal((pl.col(c) > 3).cast(pl.Int64) for c in dests).alias("runs_on_play"),
            bases(
                occupied("base1_run_id"), occupied("base2_run_id"), occupied("base3_run_id")
            ).alias("base_state_before"),
            bases(
                (pl.col("run1_dest_id") == 1) | (pl.col("bat_dest_id") == 1),
                (pl.col("run1_dest_id") == 2)
                | (pl.col("run2_dest_id") == 2)
                | (pl.col("bat_dest_id") == 2),
                (pl.col("run1_dest_id") == 3)
                | (pl.col("run2_dest_id") == 3)
                | (pl.col("run3_dest_id") == 3)
                | (pl.col("bat_dest_id") == 3),
            ).alias("base_state_after"),
            (pl.col("outs_ct") + pl.col("event_outs_ct")).alias("outs_after"),
            pl.col("outs_ct").alias("outs_before"),
            (
                pl.col("game_id")
                + pl.col("inn_ct").cast(pl.Utf8)
                + pl.col("bat_home_id").cast(pl.Utf8)
            ).alias("half_inning"),
        )
        .with_columns(pl.col("event_outs_ct").sum().over("half_inning").alias("outs_inning"))
    )
    return ev.filter(
        (
            (pl.col("outs_before") != pl.col("outs_after"))
            | (pl.col("base_state_before") != pl.col("base_state_after"))
            | (pl.col("runs_on_play") > 0)
        )
        & (pl.col("outs_inning") == 3)
        & pl.col("bat_event_fl")
    ).select("outs_before", "base_state_before", "outs_after", "base_state_after", "runs_on_play")


@pytest.fixture(scope="module")
def retro_model() -> MarkovChainModel:
    if not PATH:
        pytest.skip("set SABERMETRICSPY_RETRO2016 to retro2016.rda")
    return MarkovChainModel().fit_transitions(_batting_plays())


@pytest.mark.parametrize("start", list(REF["transitions"]))
def test_transition_rows_equal_the_printed_probabilities(
    retro_model: MarkovChainModel, start: str
) -> None:
    got = retro_model.results.transition_probabilities[start]
    assert set(got) == set(REF["transitions"][start])
    for state, printed in REF["transitions"][start].items():
        assert abs(got[state] - printed) <= _half_unit(printed, 3), (start, state)


def test_expected_plate_appearances_equal_the_printed_values(
    retro_model: MarkovChainModel,
) -> None:
    res = retro_model.results
    assert abs(res.expected_pa_per_half_inning - REF["expected_pa_from_start"]) <= 0.005
    for state, printed in REF["expected_plays_to_end"].items():
        assert abs(res.state_expected_plate_appearances[state] - printed) <= 0.005, state


def test_three_batter_distribution_equals_the_printed_values(
    retro_model: MarkovChainModel,
) -> None:
    dist = retro_model.state_distribution(3)
    for state, printed in REF["after_three_batters_from_start"].items():
        assert abs(dist[state] - printed) <= _half_unit(printed, 3), state


def test_exact_run_expectancy_is_within_simulation_noise_of_the_printed_matrix(
    retro_model: MarkovChainModel,
) -> None:
    """The book's matrix is a 10,000-inning simulation per state (standard error up to about 0.02)."""
    res = retro_model.results
    worst = 0.0
    for bases, by_outs in REF["simulated_run_expectancy"].items():
        for outs, printed in enumerate(by_outs):
            worst = max(worst, abs(res.state_expected_runs[f"{outs}|{bases}"] - printed))
    assert worst < 0.06


def _replace(frame: pl.DataFrame, column: str, value: object) -> pl.DataFrame:
    return frame.with_columns(
        pl.when(pl.int_range(pl.len()) == 0)
        .then(pl.lit(value, dtype=frame.schema[column]))
        .otherwise(pl.col(column))
        .alias(column)
    )


@pytest.mark.parametrize(
    ("column", "value", "message"),
    [
        ("base_state_before", "___", "base_state_before has"),
        ("base_state_after", "zzz", "base_state_after has"),
        ("outs_before", 3, "outs_before has"),
        ("outs_after", 4, "outs_after has"),
    ],
)
def test_fit_transitions_rejects_invalid_values(column: str, value: object, message: str) -> None:
    frame = _home_run_or_out(10)
    with pytest.raises(ValueError, match=message):
        MarkovChainModel().fit_transitions(_replace(frame, column, value))


def test_fit_transitions_rejects_nulls_negative_runs_and_decreasing_outs() -> None:
    frame = _home_run_or_out(10)
    nulls = frame.with_columns(pl.lit(None, dtype=pl.Int64).alias("runs_on_play"))
    with pytest.raises(ValueError, match="null values in runs_on_play"):
        MarkovChainModel().fit_transitions(nulls)
    with pytest.raises(ValueError, match="negative"):
        MarkovChainModel().fit_transitions(_replace(frame, "runs_on_play", -1))
    backwards = pl.DataFrame([(2, "---", 1, "---", 0)], schema=frame.schema, orient="row")
    with pytest.raises(ValueError, match="below outs_before"):
        MarkovChainModel().fit_transitions(frame.vstack(backwards))


def test_base_state_after_is_ignored_once_the_inning_is_over() -> None:
    frame = _home_run_or_out(10).with_columns(
        pl.when(pl.col("outs_after") == 3)
        .then(None)
        .otherwise(pl.col("base_state_after"))
        .alias("base_state_after")
    )
    res = MarkovChainModel().fit_transitions(frame).results
    assert res.expected_runs_per_half_inning == pytest.approx(3 * 0.1 / 0.9)


def test_states_that_never_reach_three_outs_are_named() -> None:
    frame = _home_run_or_out(10)
    keep = frame.filter(
        ~((pl.col("outs_before") == 2) & pl.col("base_state_before").is_in(["123", "12-"]))
    )
    loop = pl.DataFrame(
        [(2, "123", 2, "12-", 0)] * 100 + [(2, "12-", 2, "123", 0)] * 100,
        schema=frame.schema,
        orient="row",
    )
    with pytest.raises(
        ValueError,
        match=r"never reach three outs.*2\|123.*2\|12-|never reach three outs.*2\|12-.*2\|123",
    ):
        MarkovChainModel().fit_transitions(keep.vstack(loop))


def test_state_distribution_validates_its_arguments() -> None:
    model = MarkovChainModel().fit_transitions(_home_run_or_out(10))
    with pytest.raises(ValueError, match="not a base-out state"):
        model.state_distribution(1, start=(3, "---"))
    with pytest.raises(ValueError, match="not a base-out state"):
        model.state_distribution(1, start=(0, "___"))
    with pytest.raises(ValueError, match="0 or more"):
        model.state_distribution(-1)


def test_event_probability_fit_gap_to_the_fitted_chain_is_as_documented(
    retro_model: MarkovChainModel,
) -> None:
    """The figures quoted in docs/METHODOLOGY.md for MarkovChainModel.fit() on 2016 league-average event rates."""
    import pyreadr  # pyright: ignore[reportMissingImports]

    events = pl.from_pandas(pyreadr.read_r(PATH)["retro2016"]).filter(pl.col("bat_event_fl"))
    n = events.height
    count = {
        code: events.filter(pl.col("event_cd") == code).height
        for code in (14, 15, 16, 20, 21, 22, 23)
    }
    simplified = MarkovChainModel().fit(
        p_1b=count[20] / n,
        p_2b=count[21] / n,
        p_3b=count[22] / n,
        p_hr=count[23] / n,
        p_bb=(count[14] + count[15] + count[16]) / n,
    )
    approx, fitted = simplified.results, retro_model.results
    quoted = {  # state: (event-probability fit, fitted chain)
        "0|---": (0.479, 0.485),
        "0|1--": (0.846, 0.848),
        "0|123": (2.131, 2.212),
    }
    for state, (a, b) in quoted.items():
        assert approx.state_expected_runs[state] == pytest.approx(a, abs=5e-4), state
        assert fitted.state_expected_runs[state] == pytest.approx(b, abs=5e-4), state
    assert approx.expected_pa_per_half_inning == pytest.approx(4.41, abs=5e-3)
    assert fitted.expected_pa_per_half_inning == pytest.approx(4.27, abs=5e-3)
