"""Seasonal constants (wOBA weights, FIP and park factors, WAR inputs) read from YAML files you supply.

The library ships no third-party constants and downloads none (ADR-0068): point it at a directory with
`use_constants` or `$SABERMETRICSPY_CONSTANTS`. `docs/CONSTANTS.md` lists the files, their fields and where
the values come from.
"""

from __future__ import annotations

import os
import warnings
from pathlib import Path
from typing import Any

import yaml

from sabermetricspy.types.context import (
    LeagueWARConstants,
    ParkFactor,
    PitcherWARConstants,
    SeasonContext,
    WOBAWeights,
)

DEFAULT_SEASON = 2024
"""Season used when neither the caller nor the data names one."""

CONSTANTS_ENV = "SABERMETRICSPY_CONSTANTS"
CONSTANTS_FILES: tuple[str, ...] = (
    "woba_fangraphs.yaml",
    "park_factors.yaml",
    "park_fip.yaml",
    "pitcher_war.yaml",
    "league_war.yaml",
)
GUTS_URL = "https://www.fangraphs.com/guts.aspx?type=cn"


class ConstantsNotFoundError(FileNotFoundError):
    """Raised when a constants file is needed but no constants directory (or file) is available."""


_constants_override: Path | None = None
_GUTS_OVERRIDE: dict[int, WOBAWeights] = {}
_TABLES: dict[tuple[str, str], Any] = {}


def use_constants(path: str | Path | None) -> None:
    """Read seasonal constants from this directory (None goes back to `$SABERMETRICSPY_CONSTANTS`).

    The directory holds the YAML files in `CONSTANTS_FILES`; only the ones a calculation needs have to exist.
    """
    global _constants_override
    _constants_override = Path(path) if path is not None else None
    _TABLES.clear()
    _GUTS_OVERRIDE.clear()


def constants_dir() -> Path:
    """The directory seasonal constants are read from: `use_constants`, else `$SABERMETRICSPY_CONSTANTS`."""
    if _constants_override is not None:
        return _constants_override
    env = os.environ.get(CONSTANTS_ENV)
    if env:
        return Path(env)
    raise ConstantsNotFoundError(
        "No seasonal constants directory is set. sabermetricspy ships no constants and downloads none: call "
        f"use_constants(path) or set {CONSTANTS_ENV}. wOBA weights and league constants can be taken from "
        f"FanGraphs' Guts! page ({GUTS_URL}) under its terms, or computed from your own data (see docs/CONSTANTS.md)."
    )


def constants_dir_or_none() -> Path | None:
    """`constants_dir()` or None when no directory is set."""
    try:
        return constants_dir()
    except ConstantsNotFoundError:
        return None


def _constants_yaml(name: str) -> dict[str, Any]:
    root = constants_dir()
    key = (str(root.resolve()), name)
    if key not in _TABLES:
        path = root / name
        if not path.is_file():
            raise ConstantsNotFoundError(
                f"Constants file {path} not found (see docs/CONSTANTS.md)."
            )
        _TABLES[key] = yaml.safe_load(path.read_text(encoding="utf-8"))
    return _TABLES[key]


def _cached_table(name: str, build: Any) -> Any:
    root = constants_dir()
    key = (str(root.resolve()), "table:" + name)
    if key not in _TABLES:
        _TABLES[key] = build()
    return _TABLES[key]


_GUTS_COLUMNS: dict[str, tuple[str, ...]] = {
    "season": ("season",),
    "lg_woba": ("woba", "lg_woba"),
    "woba_scale": ("wobascale", "woba_scale"),
    "w_bb": ("wbb",),
    "w_hbp": ("whbp",),
    "w_1b": ("w1b",),
    "w_2b": ("w2b",),
    "w_3b": ("w3b",),
    "w_hr": ("whr",),
    "r_sb": ("runsb",),
    "r_cs": ("runcs",),
    "lg_r_per_pa": ("r/pa", "lg_r_pa", "r_pa"),
    "lg_r_per_w": ("r/w", "lg_r_w", "r_w"),
    "c_fip": ("cfip",),
}


def load_guts(source: Any) -> dict[int, WOBAWeights]:
    """Read a FanGraphs Guts! constants table you downloaded: a CSV path or a pandas/polars/Arrow frame.

    Column names are matched ignoring case, so both the web page's headers (`Season, wOBA, wOBAScale, wBB, wHBP, w1B,
    w2B, w3B, wHR, runSB, runCS, R/PA, R/W, cFIP`) and `baseballr::fg_guts()` names work. The library does not fetch
    the table; `docs/CONSTANTS.md` shows how to get it. Rows are keyed by season.
    """
    import polars as pl

    from sabermetricspy.schema import to_polars_df

    frame = (
        pl.read_csv(source, infer_schema_length=0)
        if isinstance(source, (str, Path))
        else to_polars_df(source)
    )
    by_lower = {c.strip().lower(): c for c in frame.columns}
    chosen: dict[str, str] = {}
    for field, names in _GUTS_COLUMNS.items():
        hit = next((by_lower[n] for n in names if n in by_lower), None)
        if hit is None:
            raise ValueError(f"Guts table is missing a column for {field!r} (looked for {names}).")
        chosen[field] = hit
    table: dict[int, WOBAWeights] = {}
    for row in frame.iter_rows(named=True):
        values = {field: float(row[col]) for field, col in chosen.items()}
        season = int(values.pop("season"))
        table[season] = WOBAWeights.model_validate({"season": season, **values})
    return table


def use_guts(source: Any) -> None:
    """Use a Guts! table (see `load_guts`) for wOBA weights and league constants, instead of a YAML file.

    The table lives in memory until `use_constants` is called again. Other constants (park factors, WAR inputs)
    still come from the constants directory when a calculation needs them.
    """
    table = load_guts(source)
    root = constants_dir_or_none()
    key = (str(root.resolve()) if root else "<none>", "table:woba")
    _GUTS_OVERRIDE.clear()
    _GUTS_OVERRIDE.update(table)
    _TABLES.pop(key, None)


def _load_default_woba_table() -> dict[int, WOBAWeights]:
    """Load the woba_fangraphs.yaml constants table from the constants directory."""

    if _GUTS_OVERRIDE:
        return dict(_GUTS_OVERRIDE)

    def build() -> dict[int, WOBAWeights]:
        raw = _constants_yaml("woba_fangraphs.yaml")
        return {
            int(yr): WOBAWeights.model_validate(vals) for yr, vals in raw.get("seasons", {}).items()
        }

    return _cached_table("woba", build)


def _load_default_parks_table() -> dict[str, ParkFactor]:
    """Load the park_factors.yaml table from the constants directory."""

    def build() -> dict[str, ParkFactor]:
        raw = _constants_yaml("park_factors.yaml")
        return {k.upper(): ParkFactor.model_validate(v) for k, v in raw.get("parks", {}).items()}

    return _cached_table("parks", build)


def constants_table() -> dict[int, WOBAWeights]:
    """Return a copy of the seasonal wOBA/FIP constants table in use, keyed by season."""
    return dict(_load_default_woba_table())


def _missing_season(what: str, season: int, table: dict[int, Any]) -> ConstantsNotFoundError:
    covered = f"{min(table)}-{max(table)}" if table else "no seasons"
    return ConstantsNotFoundError(
        f"No {what} for season {season}; the table you supplied covers {covered}. Add the season to it "
        "(see docs/CONSTANTS.md)."
    )


def get_woba_weights(season: int = DEFAULT_SEASON) -> WOBAWeights:
    """Retrieve seasonal wOBA/FIP linear weights for a season from the table you supplied.

    Raises `ConstantsNotFoundError` when the season is not in the table; there is no fallback to another season.
    """
    table = _load_default_woba_table()
    if season in table:
        return table[season]
    raise _missing_season("wOBA constants", season, table)


def get_park_factor(team_or_park: str) -> ParkFactor:
    """Retrieve the 2024 ParkFactor for a team abbreviation (e.g. 'COL', 'BOS').

    An unknown park returns a neutral factor and emits a `UserWarning`.
    """
    table = _load_default_parks_table()
    key = team_or_park.upper()
    if key in table:
        return table[key]
    for pf in table.values():
        if pf.park_id.upper() == key:
            return pf
    warnings.warn(
        f"Park {team_or_park!r} is not in the park table; returning a neutral park factor of 100.",
        UserWarning,
        stacklevel=2,
    )
    return ParkFactor(park_id=key, team_id=key, season=2024, basic_5yr=100.0, basic_1yr=100.0)


def load_custom_constants_yaml(path: str | Path) -> dict[int, WOBAWeights]:
    """Load user-supplied seasonal constants from an external YAML file."""
    raw: dict[str, Any] = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    seasons_raw: dict[Any, Any] = raw.get("seasons", raw)
    return {int(yr): WOBAWeights.model_validate(vals) for yr, vals in seasons_raw.items()}


def resolve_context(
    context: SeasonContext | None = None, season: int = DEFAULT_SEASON
) -> SeasonContext:
    """Ensure a SeasonContext has populated WOBAWeights."""
    if context is None:
        return SeasonContext(season=season, weights=get_woba_weights(season))
    if context.weights is None:
        return context.model_copy(update={"weights": get_woba_weights(context.season)})
    return context


def _load_pitcher_war_table() -> dict[int, PitcherWARConstants]:
    """Load pitcher_war.yaml (AL/NL pitching totals per season) from the constants directory."""

    def build() -> dict[int, PitcherWARConstants]:
        raw = _constants_yaml("pitcher_war.yaml")
        table: dict[int, PitcherWARConstants] = {}
        for year, entry in raw["seasons"].items():
            table[int(year)] = PitcherWARConstants.model_validate(
                {
                    "season": int(year),
                    "al": entry["al"],
                    "nl": entry["nl"],
                    "war_ip_correction": entry.get("war_ip_correction"),
                    "source": entry.get("source", ""),
                    "retrieved": entry.get("retrieved"),
                }
            )
        return table

    return _cached_table("pitcher_war", build)


def get_pitcher_war_constants(season: int = DEFAULT_SEASON) -> PitcherWARConstants:
    """Retrieve the league run environment for FanGraphs-method pitcher WAR.

    Raises `ConstantsNotFoundError` when the season is not in the table; there is no fallback to another season.
    """
    table = _load_pitcher_war_table()
    if season in table:
        return table[season]
    raise _missing_season("pitcher-WAR constants", season, table)


def _load_league_war_table() -> dict[int, LeagueWARConstants]:
    """Load league_war.yaml (MLB games, plate appearances, runs and outs per season)."""

    def build() -> dict[int, LeagueWARConstants]:
        raw = _constants_yaml("league_war.yaml")
        return {
            int(year): LeagueWARConstants.model_validate({"season": int(year), **entry})
            for year, entry in raw["seasons"].items()
        }

    return _cached_table("league_war", build)


def get_league_war_constants(season: int = DEFAULT_SEASON) -> LeagueWARConstants:
    """Retrieve the MLB games, plate appearances, runs and outs behind the FanGraphs replacement level.

    Raises `ConstantsNotFoundError` when the season is not in the table; there is no fallback to another season.
    """
    table = _load_league_war_table()
    if season in table:
        return table[season]
    raise _missing_season("league WAR constants", season, table)


# One abbreviation per franchise in park_fip.yaml; common alternates map onto it.
_TEAM_ALIASES: dict[str, str] = {
    "ATH": "OAK",
    "FLA": "MIA",
    "MON": "WSN",
    "TBD": "TBR",
    "ANA": "LAA",
    "CAL": "LAA",
    "SD": "SDP",
    "SF": "SFG",
    "TB": "TBR",
    "KC": "KCR",
    "WAS": "WSN",
    "CWS": "CHW",
}


def _load_fip_park_table() -> dict[int, dict[str, int]]:
    """Load park_fip.yaml (FIP park factor by season and team) from the constants directory."""

    def build() -> dict[int, dict[str, int]]:
        raw = _constants_yaml("park_fip.yaml")
        return {
            int(season): {str(tm): int(v) for tm, v in teams.items()}
            for season, teams in raw["seasons"].items()
        }

    return _cached_table("fip_park", build)


def get_fip_park_factor(team: str, season: int) -> float:
    """FanGraphs' FIP park factor (100 = neutral) for a team's home park in a season, 1990 on.

    This is the park input of FIP- (pass it as `SeasonContext.park_factor`) and of FanGraphs pitcher WAR. It is the
    FIP column of the FanGraphs park factors page, a whole number. Raises `ValueError` for an unknown team or season
    instead of returning a neutral value.
    """
    table = _load_fip_park_table()
    if season not in table:
        raise _missing_season("FIP park factors", season, table)
    key = _TEAM_ALIASES.get(team.upper(), team.upper())
    if key not in table[season]:
        raise ValueError(
            f"No FIP park factor for team {team!r} in {season}; teams: {sorted(table[season])}."
        )
    return float(table[season][key])
