"""Demo 07: from a Baseball Savant CSV and a season of counting stats to metrics, in a few lines.

Savant: Statcast Search > Download CSV gives the pitch-level file read below (a recorded sample of Tarik Skubal's 2024
pitches is in tests/fixtures/statcast). Season counting stats can come from any source with the usual columns.

Needs seasonal constants, which the library does not ship: set SABERMETRICSPY_CONSTANTS to a directory of them or call
sp.use_guts("guts.csv") first (see docs/CONSTANTS.md).
"""

from pathlib import Path

import polars as pl

import sabermetricspy as sp
from sabermetricspy import Metric, MetricSuite

SAMPLE = (
    Path(__file__).resolve().parent.parent
    / "tests"
    / "fixtures"
    / "statcast"
    / "skubal_2024_pitches.csv"
)


def main() -> None:
    # 1. Pitch-level Statcast CSV -> pitch-tracking metrics per pitcher
    pitches = sp.prepare_statcast_pitches(pl.read_csv(SAMPLE, infer_schema_length=0))
    physics = sp.calculate_suite(
        pitches, [MetricSuite.PITCH_PHYSICS], by="pitcher_id", preset="statcast"
    )
    print(physics.df.select("pitcher_id", "avg_velo", "avg_spin", "ivb", "hb", "vaa"))

    # 2. Season totals -> rates. Counts are summed first, then divided; wRC+ uses the 2024 constants you supply (sp.use_constants or sp.use_guts).
    batters = pl.DataFrame(
        {
            "player_id": ["a", "b"],
            "ab": [550, 480],
            "h": [170, 130],
            "b2": [35, 22],
            "b3": [2, 1],
            "hr": [30, 12],
            "bb": [70, 45],
            "hbp": [4, 2],
            "sf": [5, 3],
            "ibb": [3, 1],
            "so": [120, 90],
            "pa": [630, 530],
        }
    )
    result = sp.calculate(
        batters,
        [Metric.OBP, Metric.SLG, Metric.WOBA, Metric.WRC_PLUS],
        by="player_id",
        context=sp.SeasonContext(season=2024),
    )
    print(result.df.select("player_id", "obp", "slg", "woba", "wrc_plus"))

    # 3. Where each number comes from
    print(result.summary())


if __name__ == "__main__":
    main()
