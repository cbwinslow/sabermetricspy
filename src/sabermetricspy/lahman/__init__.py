"""League constants computed from the Lahman Baseball Database, so no third-party constants table has to be shipped.

The Lahman database (SABR, copyright 1996-2025 by SABR via the donation of Sean Lahman, CC BY-SA 3.0) is downloaded to
the user's cache (`download_lahman`) and summed by season and league (`league_constants`). Everything here is a sum
or a published definition: runs per PA, OBP and SLG, ERA, the FIP constant (Tango's definition, league ERA minus the
FIP numerator over league innings), the kwERA constant, and the caught-stealing run value (FanGraphs Library, "wSB").
Linear weights, park factors and batted-ball constants need play-by-play or splits that Lahman does not hold and are
not computed here.
"""

from __future__ import annotations

import os
import tempfile
import urllib.request
from collections.abc import Sequence
from pathlib import Path

import polars as pl
from pydantic import BaseModel, ConfigDict

from sabermetricspy.telemetry import profiled

LAHMAN_ENV = "SABERMETRICSPY_LAHMAN"
LAHMAN_REPO = "cbwinslow/lahman-database-csv"
LAHMAN_URL = f"https://raw.githubusercontent.com/{LAHMAN_REPO}/{{ref}}/data"
LAHMAN_FILES: tuple[str, ...] = ("Batting.csv", "Pitching.csv")
LAHMAN_CREDIT = (
    "The SABR Lahman Baseball Database, copyright 1996-2025 by SABR via the generous donation of Sean Lahman; "
    "licensed CC BY-SA 3.0."
)

_BATTING_SUMS = ("AB", "R", "H", "2B", "3B", "HR", "BB", "IBB", "HBP", "SF", "SH", "SB", "CS", "SO")
_PITCHING_SUMS = ("IPouts", "ER", "R", "HR", "BB", "HBP", "SO", "BFP")


class LeagueConstants(BaseModel):
    """League totals and constants for one season, computed from Lahman (`league` is "MLB", "AL" or "NL")."""

    model_config = ConfigDict(frozen=True)

    season: int
    league: str
    pa: int
    runs: int
    outs: int
    lg_r_per_pa: float
    lg_obp: float
    lg_slg: float
    lg_era: float
    c_fip: float
    runs_per_out: float
    r_cs: float
    kwera_constant: float


def default_lahman_path() -> Path:
    """The directory used when no path is given: `$SABERMETRICSPY_LAHMAN`, else the user cache."""
    env = os.environ.get(LAHMAN_ENV)
    return Path(env) if env else Path.home() / ".cache" / "sabermetricspy" / "lahman"


def download_lahman(
    dest: str | Path | None = None,
    *,
    ref: str = "main",
    base_url: str = LAHMAN_URL,
    files: Sequence[str] = LAHMAN_FILES,
) -> Path:
    """Download the Lahman CSV files to `dest` (default: the user cache).

    `base_url` may contain `{ref}`. The data is CC BY-SA 3.0; credit SABR and Sean Lahman when you publish results.
    Files are fetched to a scratch directory first so a failure never leaves a half-written copy.
    """
    root = Path(dest) if dest is not None else default_lahman_path()
    root.mkdir(parents=True, exist_ok=True)
    base = base_url.format(ref=ref)
    with tempfile.TemporaryDirectory(dir=root, prefix=".download-") as scratch_name:
        scratch = Path(scratch_name)
        for name in files:
            with urllib.request.urlopen(f"{base}/{name}", timeout=120) as resp:
                (scratch / name).write_bytes(resp.read())
        for name in files:
            os.replace(scratch / name, root / name)
    return root


def _read(path: Path, sums: Sequence[str], keep_from: int) -> pl.DataFrame:
    frame = pl.read_csv(path, infer_schema_length=0, null_values=["NA", ""])
    renames = {"X2B": "2B", "X3B": "3B"}
    frame = frame.rename({k: v for k, v in renames.items() if k in frame.columns})
    cols = ["yearID", "lgID", *[c for c in sums if c in frame.columns]]
    out = frame.select(cols).with_columns(
        pl.col(c).cast(pl.Float64, strict=False).fill_null(0.0) for c in cols if c != "lgID"
    )
    return out.filter(pl.col("yearID") >= keep_from)


@profiled(category="constants")
def league_constants(
    season: int,
    *,
    league: str = "MLB",
    lahman_dir: str | Path | None = None,
) -> LeagueConstants:
    """Compute one season's league constants from the Lahman CSV files in `lahman_dir` (default: the user cache).

    `league` is "MLB" (both leagues), "AL" or "NL". Raises FileNotFoundError when the files are missing (run
    `download_lahman()`) and ValueError when the season is not in the data.
    """
    root = Path(lahman_dir) if lahman_dir is not None else default_lahman_path()
    for name in LAHMAN_FILES:
        if not (root / name).exists():
            raise FileNotFoundError(
                f"{root / name} not found; run sabermetricspy.lahman.download_lahman()."
            )
    leagues = {"MLB": ("AL", "NL"), "AL": ("AL",), "NL": ("NL",)}
    if league not in leagues:
        raise ValueError(f"league must be one of {sorted(leagues)}, got {league!r}.")
    bat = _read(root / "Batting.csv", _BATTING_SUMS, season).filter(
        (pl.col("yearID") == season) & pl.col("lgID").is_in(leagues[league])
    )
    pit = _read(root / "Pitching.csv", _PITCHING_SUMS, season).filter(
        (pl.col("yearID") == season) & pl.col("lgID").is_in(leagues[league])
    )
    if bat.is_empty() or pit.is_empty():
        raise ValueError(f"No Lahman rows for season {season}, league {league}.")
    b = {c: float(bat[c].sum()) for c in _BATTING_SUMS}
    p = {c: float(pit[c].sum()) for c in _PITCHING_SUMS}
    pa = b["AB"] + b["BB"] + b["HBP"] + b["SF"] + b["SH"]
    singles = b["H"] - b["2B"] - b["3B"] - b["HR"]
    total_bases = singles + 2 * b["2B"] + 3 * b["3B"] + 4 * b["HR"]
    ip = p["IPouts"] / 3.0
    lg_era = 9.0 * p["ER"] / ip
    fip_numerator = 13.0 * p["HR"] + 3.0 * (p["BB"] + p["HBP"]) - 2.0 * p["SO"]
    runs_per_out = b["R"] / p["IPouts"]
    return LeagueConstants(
        season=season,
        league=league,
        pa=int(pa),
        runs=int(b["R"]),
        outs=int(p["IPouts"]),
        lg_r_per_pa=b["R"] / pa,
        lg_obp=(b["H"] + b["BB"] + b["HBP"]) / (b["AB"] + b["BB"] + b["HBP"] + b["SF"]),
        lg_slg=total_bases / b["AB"],
        lg_era=lg_era,
        c_fip=lg_era - fip_numerator / ip,
        runs_per_out=runs_per_out,
        r_cs=-(2.0 * runs_per_out + 0.075),
        kwera_constant=lg_era + 12.0 * (p["SO"] - p["BB"]) / p["BFP"],
    )


__all__ = [
    "LAHMAN_CREDIT",
    "LeagueConstants",
    "default_lahman_path",
    "download_lahman",
    "league_constants",
]
