"""JamesSteinShrinker reproduces Efron and Morris (1975), Tables 1-2 (tests/golden/efron_morris_james_stein.yaml).

18 players, first 45 at bats of 1970; the printed retransformed Stein estimates, the shrinkage constants and the total
squared errors (17.56 for the MLE and 5.01 for the Stein rule on the transformed scale) are reproduced. The paper's
printed Xbar of -3.275 contradicts its own Table 1 (column mean -3.317) and is not tested (see the fixture's `excluded`).
"""

from __future__ import annotations

from typing import Any

import numpy as np
import polars as pl
import pytest
from golden_loader import load_entries

from sabermetricspy import EmpiricalBayesShrinker, JamesSteinShrinker

ALL = load_entries("efron_morris_james_stein.yaml")
PLAYERS = [e for e in ALL if e["id"].startswith("em1975_") and "player" in e]
GROUP = next(e for e in ALL if e["id"] == "em1975_group_scalars")


def _frame() -> pl.DataFrame:
    return pl.DataFrame(
        {
            "player": [e["player"] for e in PLAYERS],
            "h": [e["inputs"]["h"] for e in PLAYERS],
            "ab": [e["inputs"]["ab"] for e in PLAYERS],
            "rest": [e["inputs"]["rest_of_season_average"] for e in PLAYERS],
        }
    )


def _fitted() -> tuple[JamesSteinShrinker, pl.DataFrame]:
    df = _frame()
    js = JamesSteinShrinker().fit(df)
    return js, js.transform(df)


def test_there_are_eighteen_players() -> None:
    assert len(PLAYERS) == 18


@pytest.mark.parametrize("entry", PLAYERS, ids=lambda e: e["id"])
def test_retransformed_estimates_match_table_2(entry: dict[str, Any]) -> None:
    _, out = _fitted()
    got = out.filter(pl.col("player") == entry["player"])["js_rate"][0]
    assert got == pytest.approx(
        entry["published"]["stein_retransformed"], abs=entry["tolerance"]["stein_retransformed"]
    )


def test_shrinkage_constants_match_the_printed_values() -> None:
    js, _ = _fitted()
    pub, tol = GROUP["published"], GROUP["tolerance"]
    r = js.results
    assert r.shrinkage == pytest.approx(
        pub["shrink_k_minus_3_over_V"], abs=tol["shrink_k_minus_3_over_V"]
    )
    assert r.factor == pytest.approx(pub["c"], abs=tol["c"])
    assert r.tau_hat == pytest.approx(pub["tau_hat"], abs=tol["tau_hat"])
    assert r.grand_mean == pytest.approx(pub["xbar_table1_column_mean"], abs=0.001)
    assert (r.n_groups, r.trials) == (18, 45)


def test_total_squared_errors_and_efficiency_match_the_paper() -> None:
    _, out = _fitted()
    n = 45.0
    pub, tol = GROUP["published"], GROUP["tolerance"]
    x = np.sqrt(n) * np.arcsin(2 * (out["h"].to_numpy() / n) - 1)
    theta = np.sqrt(n) * np.arcsin(2 * out["rest"].to_numpy() - 1)
    delta = np.sqrt(n) * np.arcsin(2 * out["js_rate"].to_numpy() - 1)
    tse_mle = float(np.sum((x - theta) ** 2))
    tse_stein = float(np.sum((delta - theta) ** 2))
    assert tse_mle == pytest.approx(pub["tse_mle_transformed"], abs=tol["tse_mle_transformed"])
    assert tse_stein == pytest.approx(
        pub["tse_stein_transformed"], abs=tol["tse_stein_transformed"]
    )
    assert tse_mle / tse_stein == pytest.approx(pub["efficiency"], abs=tol["efficiency"])
    closer = int(np.sum(np.abs(delta - theta) < np.abs(x - theta)))
    assert closer == pub["stein_closer_count"]


def test_empirical_bayes_shrinker_is_a_different_estimator() -> None:
    df = _frame()
    eb = EmpiricalBayesShrinker().fit(df).transform(df)["eb_rate"].to_numpy()
    js = JamesSteinShrinker().fit(df).transform(df)["js_rate"].to_numpy()
    assert float(np.max(np.abs(eb - js))) > 0.01


def test_invalid_input_raises() -> None:
    ok = pl.DataFrame({"h": [18, 17, 16, 15, 14], "ab": [45] * 5})
    with pytest.raises(ValueError, match="same positive number"):
        JamesSteinShrinker().fit(pl.DataFrame({"h": [18, 17, 16, 15], "ab": [45, 45, 45, 44]}))
    with pytest.raises(ValueError, match="at least 4"):
        JamesSteinShrinker().fit(pl.DataFrame({"h": [18, 17, 16], "ab": [45] * 3}))
    with pytest.raises(ValueError, match="nothing to shrink"):
        JamesSteinShrinker().fit(pl.DataFrame({"h": [10] * 5, "ab": [45] * 5}))
    with pytest.raises(ValueError, match="between 0"):
        JamesSteinShrinker().fit(pl.DataFrame({"h": [18, 17, 16, 15, 60], "ab": [45] * 5}))
    with pytest.raises(RuntimeError):
        JamesSteinShrinker().transform(ok)
    with pytest.raises(ValueError, match="positive-part"):
        JamesSteinShrinker().fit(pl.DataFrame({"h": [22, 23, 22, 23, 22, 23], "ab": [45] * 6}))
