"""Fits the per-season SIERA constant to the FanGraphs leaderboard and prints it for woba_fangraphs.yaml.

Run: uv run python tools/siera_constants.py <folder written by tools/siera_constants.R>

With the published 2011 coefficients (the (BB/PA)^2 term at the measured 25.264) and FanGraphs' netGB = GB - FB,
each season's constant is the median of FanGraphs SIERA minus everything else over pitchers with 50 or more innings.
"""

from __future__ import annotations

import glob
import sys

import polars as pl

from sabermetricspy.types.context import SIERACoefficients


def _outs(column: str) -> pl.Expr:
    """Baseball innings notation (177.2 is 177 and two thirds) as outs."""
    whole = pl.col(column).floor()
    return whole * 3 + ((pl.col(column) - whole) * 10).round()


def main(folder: str) -> None:
    c = SIERACoefficients()
    columns = ["Season", "IP", "Start_IP", "TBF", "SO", "BB", "GB", "FB", "SIERA"]
    frames = [
        pl.read_csv(
            f, columns=columns, null_values=["NA"], schema_overrides={"Start_IP": pl.Float64}
        )
        for f in sorted(glob.glob(f"{folder}/p*.csv"))
    ]
    d = pl.concat(frames).with_columns(pl.col("Start_IP").fill_null(0.0)).filter(pl.col("IP") >= 50)
    so = pl.col("SO") / pl.col("TBF")
    bb = pl.col("BB") / pl.col("TBF")
    n = (pl.col("GB") - pl.col("FB")) / pl.col("TBF")
    rest = (
        c.so_per_pa * so
        + c.so_per_pa_sq * so * so
        + c.bb_per_pa * bb
        + c.bb_per_pa_sq * bb * bb
        + c.net_gb_per_pa * n
        + c.net_gb_per_pa_sq * n.sign() * n * n
        + c.so_x_bb * so * bb
        + c.so_x_net_gb * so * n
        + c.bb_x_net_gb * bb * n
        + c.start_share * _outs("Start_IP") / _outs("IP")
    )
    d = d.with_columns((pl.col("SIERA") - rest).alias("resid"))
    constants = d.group_by("Season").agg(pl.col("resid").median().alias("constant")).sort("Season")
    err = d.join(constants, on="Season").select(
        (pl.col("resid") - pl.col("constant")).abs().alias("e")
    )["e"]
    print(f"# pitcher-seasons {d.height}, max error {err.max():.4f}, mean {err.mean():.5f}")
    for season, value in constants.iter_rows():
        print(f"{season}: {value:.4f}")


if __name__ == "__main__":
    main(sys.argv[1])
