"""Builds tests/golden/fg_batting_rates.csv and fg_pitching_rates.csv from the per-season CSVs of tools/fg_leaderboards.R.

Usage: python tools/fg_leaderboards.py <directory with bat_YYYY.csv and pit_YYYY.csv>
Pitchers have 50 or more IP; FanGraphs' innings notation (231.2 = 231 and 2/3) is converted to outs.
"""

from __future__ import annotations

import sys
from pathlib import Path

import polars as pl

GOLDEN = Path(__file__).resolve().parent.parent / "tests" / "golden"


def _read(files: list[Path], text: tuple[str, ...]) -> pl.DataFrame:
    frames = [
        pl.read_csv(f, infer_schema_length=0).with_columns(pl.all().replace("NA", None))
        for f in files
    ]
    df = pl.concat(frames, how="diagonal")
    return df.with_columns(
        [pl.col(c).cast(pl.Float64, strict=False) for c in df.columns if c not in text]
    )


def _outs(ip: float) -> int:
    whole = int(ip)
    return whole * 3 + round((ip - whole) * 10)


def main(src: Path) -> None:
    bat = _read(sorted(src.glob("bat_*.csv")), ("PlayerName",))
    counts = ["ab", "h", "b2", "b3", "hr", "bb", "hbp", "sf", "sb", "cs", "pa", "so", "ibb"]
    b = bat.select(
        season=pl.col("Season"),
        ab="AB",
        h="H",
        b2="2B",
        b3="3B",
        hr="HR",
        bb="BB",
        hbp="HBP",
        sf="SF",
        sb="SB",
        cs="CS",
        pa="PA",
        so="SO",
        ibb="IBB",
        pub_obp="OBP",
        pub_slg="SLG",
        pub_iso="ISO",
        pub_bb_pct="BB_pct",
        pub_k_pct="K_pct",
        pub_bb_k="BB_K",
    ).drop_nulls()
    b = b.with_columns([pl.col(c).cast(pl.Int64) for c in ["season", *counts]])
    b.write_csv(GOLDEN / "fg_batting_rates.csv")

    pit = _read(sorted(src.glob("pit_*.csv")), ("PlayerName",)).filter(pl.col("IP") >= 50)
    p = (
        pit.with_columns(pl.col("IP").map_elements(_outs, return_dtype=pl.Int64).alias("outs"))
        .select(
            season=pl.col("Season"),
            outs="outs",
            g="G",
            gs="GS",
            qs="QS",
            cg="CG",
            sv="SV",
            bs="BS",
            so="SO",
            bb="BB",
            hbp="HBP",
            hr="HR",
            h="H",
            r="R",
            er="ER",
            bf="TBF",
            pub_ip="IP",
            pub_era="ERA",
            pub_k_pct="K_pct",
            pub_bb_pct="BB_pct",
            pub_k_minus_bb="K-BB_pct",
            pub_k_bb="K_BB",
        )
        .drop_nulls()
    )
    ints = [
        "season",
        "g",
        "gs",
        "qs",
        "cg",
        "sv",
        "bs",
        "so",
        "bb",
        "hbp",
        "hr",
        "h",
        "r",
        "er",
        "bf",
    ]
    p.with_columns([pl.col(c).cast(pl.Int64) for c in ints]).write_csv(
        GOLDEN / "fg_pitching_rates.csv"
    )


if __name__ == "__main__":
    main(Path(sys.argv[1]))
