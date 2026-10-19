"""Position-player WAR components following the FanGraphs Library "Position Player WAR" article.

https://library.fangraphs.com/war/war-position-players/ prints, with all league terms in the player's season:

    RPW                 = 9 * (MLB R / MLB IP) * 1.5 + 3
    replacement runs    = 570 * (MLB games / 2430) * (RPW / lgPA) * PA
    positional runs     = (innings / 9 / 162) * run value per 162 defensive games, summed over positions
    league adjustment   = -(lg batting + lg baserunning + lg fielding + lg positional runs) / lgPA * PA
    WAR                 = (batting + baserunning + fielding + positional + league + replacement) / RPW

The positional table (per 162 defensive games, 1,458 innings) is on https://library.fangraphs.com/misc/war/positional-adjustment/.
"""

from __future__ import annotations

from sabermetricspy.telemetry import profiled

# Share of the 1,000 WAR per 2,430 games that FanGraphs allocates to position players.
POSITION_PLAYER_WAR_POOL = 570.0
STANDARD_SEASON_GAMES = 2430.0
DEFENSIVE_GAMES_PER_SEASON = 162.0


@profiled(category="valuation")
def runs_per_win(mlb_runs: float, mlb_innings_pitched: float) -> float:
    """FanGraphs runs per win: 9 * (R / IP) * 1.5 + 3."""
    if mlb_innings_pitched <= 0:
        raise ValueError("mlb_innings_pitched must be positive.")
    return 9.0 * (mlb_runs / mlb_innings_pitched) * 1.5 + 3.0


@profiled(category="valuation")
def replacement_runs(
    pa: float, *, runs_per_win_value: float, league_pa: float, mlb_games: float = 2430.0
) -> float:
    """Replacement-level runs: 570 * (games / 2430) * (RPW / lgPA) * PA."""
    if league_pa <= 0:
        raise ValueError("league_pa must be positive.")
    return (
        POSITION_PLAYER_WAR_POOL
        * (mlb_games / STANDARD_SEASON_GAMES)
        * (runs_per_win_value / league_pa)
        * pa
    )


@profiled(category="valuation")
def positional_runs(innings: float, run_value_per_162: float) -> float:
    """Positional adjustment prorated by defensive innings: (innings / 9 / 162) * value per 162 games."""
    return innings / 9.0 / DEFENSIVE_GAMES_PER_SEASON * run_value_per_162


@profiled(category="valuation")
def league_adjustment(league_component_runs: float, league_pa: float, pa: float) -> float:
    """League adjustment -(sum of league batting, baserunning, fielding and positional runs) / lgPA * PA."""
    if league_pa <= 0:
        raise ValueError("league_pa must be positive.")
    return -league_component_runs / league_pa * pa
