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
        assert got[state] == pytest.approx(printed, abs=6e-4), (start, state)


def test_expected_plate_appearances_equal_the_printed_values(
    retro_model: MarkovChainModel,
) -> None:
    res = retro_model.results
    assert res.expected_pa_per_half_inning == pytest.approx(
        REF["expected_pa_from_start"], abs=0.005
    )
    for state, printed in REF["expected_plays_to_end"].items():
        assert res.state_expected_plate_appearances[state] == pytest.approx(printed, abs=0.005)


def test_three_batter_distribution_equals_the_printed_values(
    retro_model: MarkovChainModel,
) -> None:
    dist = retro_model.state_distribution(3)
    for state, printed in REF["after_three_batters_from_start"].items():
        assert dist[state] == pytest.approx(printed, abs=6e-4), state


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
