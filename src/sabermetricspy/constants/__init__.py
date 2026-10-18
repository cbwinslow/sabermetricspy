"""Loader and registry for seasonal wOBA, FIP, and Park Factor constants from bundled YAML."""

from __future__ import annotations

import warnings
from functools import lru_cache
from importlib import resources
from pathlib import Path
from typing import Any

import yaml

from sabermetricspy.types.context import ParkFactor, PitcherWARConstants, SeasonContext, WOBAWeights

_WARNED_FALLBACKS: set[tuple[int, int]] = set()
_WARNED_WAR_FALLBACKS: set[tuple[int, int]] = set()


@lru_cache(maxsize=1)
def _load_default_woba_table() -> dict[int, WOBAWeights]:
    """Load bundled woba_fangraphs.yaml constants table."""
    pkg_files = resources.files("sabermetricspy")
    yaml_path = pkg_files.joinpath("data/constants/woba_fangraphs.yaml")
    raw: dict[str, Any] = yaml.safe_load(yaml_path.read_text(encoding="utf-8"))
    seasons_raw: dict[Any, Any] = raw.get("seasons", {})
    table: dict[int, WOBAWeights] = {}
    for yr, vals in seasons_raw.items():
        year_int = int(yr)
        table[year_int] = WOBAWeights.model_validate(vals)
    return table


@lru_cache(maxsize=1)
def _load_default_parks_table() -> dict[str, ParkFactor]:
    """Load bundled park_factors.yaml table."""
    pkg_files = resources.files("sabermetricspy")
    yaml_path = pkg_files.joinpath("data/constants/park_factors.yaml")
    raw: dict[str, Any] = yaml.safe_load(yaml_path.read_text(encoding="utf-8"))
    parks_raw: dict[str, Any] = raw.get("parks", {})
    return {k.upper(): ParkFactor.model_validate(v) for k, v in parks_raw.items()}


def bundled_constants() -> dict[int, WOBAWeights]:
    """Return a copy of the bundled seasonal constants table keyed by season."""
    return dict(_load_default_woba_table())


def get_woba_weights(season: int = 2024) -> WOBAWeights:
    """Retrieve seasonal wOBA/FIP linear weights for a given season.

    If the exact year is not in the bundled table, returns the nearest available season's
    constants labeled with the requested season and emits a `UserWarning` (once per
    requested/substituted pair) naming both seasons.
    """
    table = _load_default_woba_table()
    if season in table:
        return table[season]
    nearest_year = min(table.keys(), key=lambda y: abs(y - season))
    if (season, nearest_year) not in _WARNED_FALLBACKS:
        _WARNED_FALLBACKS.add((season, nearest_year))
        warnings.warn(
            f"No bundled constants for season {season}; using season {nearest_year} constants instead. "
            "Pass a SeasonContext with explicit weights for exact results.",
            UserWarning,
            stacklevel=2,
        )
    base = table[nearest_year]
    return base.model_copy(update={"season": season})


def get_park_factor(team_or_park: str) -> ParkFactor:
    """Retrieve the bundled 2024 ParkFactor for a team abbreviation (e.g. 'COL', 'BOS').

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
        f"Park {team_or_park!r} is not bundled; returning a neutral park factor of 100.",
        UserWarning,
        stacklevel=2,
    )
    return ParkFactor(park_id=key, team_id=key, season=2024, basic_5yr=100.0, basic_1yr=100.0)


def load_custom_constants_yaml(path: str | Path) -> dict[int, WOBAWeights]:
    """Load user-supplied seasonal constants from an external YAML file."""
    raw: dict[str, Any] = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    seasons_raw: dict[Any, Any] = raw.get("seasons", raw)
    return {int(yr): WOBAWeights.model_validate(vals) for yr, vals in seasons_raw.items()}


def resolve_context(context: SeasonContext | None = None, season: int = 2024) -> SeasonContext:
    """Ensure a SeasonContext has populated WOBAWeights."""
    if context is None:
        return SeasonContext(season=season, weights=get_woba_weights(season))
    if context.weights is None:
        return context.model_copy(update={"weights": get_woba_weights(context.season)})
    return context


@lru_cache(maxsize=1)
def _load_pitcher_war_table() -> dict[int, PitcherWARConstants]:
    """Load bundled pitcher_war.yaml (AL/NL pitching totals per season)."""
    yaml_path = resources.files("sabermetricspy").joinpath("data/constants/pitcher_war.yaml")
    raw: dict[str, Any] = yaml.safe_load(yaml_path.read_text(encoding="utf-8"))
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


def get_pitcher_war_constants(season: int = 2024) -> PitcherWARConstants:
    """Retrieve the league run environment for FanGraphs-method pitcher WAR.

    An unbundled season returns the nearest bundled season labeled with the requested season and emits a
    `UserWarning` (once per requested/substituted pair).
    """
    table = _load_pitcher_war_table()
    if season in table:
        return table[season]
    nearest_year = min(table.keys(), key=lambda y: abs(y - season))
    if (season, nearest_year) not in _WARNED_WAR_FALLBACKS:
        _WARNED_WAR_FALLBACKS.add((season, nearest_year))
        warnings.warn(
            f"No bundled pitcher-WAR constants for season {season}; using season {nearest_year} instead.",
            UserWarning,
            stacklevel=2,
        )
    return table[nearest_year].model_copy(update={"season": season, "war_ip_correction": None})
