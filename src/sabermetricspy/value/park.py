"""Park factor calculation following the FanGraphs Library "5 Year Regressed Park Factors" article.

https://library.fangraphs.com/park-factors-5-year-regressed/ gives, with home and road runs per game H and R
and T teams in the league:

    raw PF   = H * T / ((T - 1) * R + H)
    iPF      = (raw PF + 1) / 2                     (the composite factor, applied to composite statistics)
    final PF = 1 - (1 - iPF) * X                    (X by the number of seasons of data used)

The article centers a window of up to five seasons on the season in question; choosing that window needs
multi-season home and road splits, so it is left to the caller. Factors here use 1.00 as neutral.
"""

from __future__ import annotations

from sabermetricspy.telemetry import profiled

# Share of the distance from neutral that is kept, by seasons of data (4 or more share the last value).
YEARS_TO_REGRESSION: dict[int, float] = {1: 0.6, 2: 0.7, 3: 0.8, 4: 0.9}


@profiled(category="valuation")
def raw_park_factor(home_runs_per_game: float, road_runs_per_game: float, *, teams: int) -> float:
    """Raw park factor H*T / ((T-1)*R + H) from home and road runs per game and the team count."""
    if road_runs_per_game <= 0 or home_runs_per_game < 0 or teams < 2:
        raise ValueError(
            "Need positive road runs per game, non-negative home runs per game, teams >= 2."
        )
    return home_runs_per_game * teams / ((teams - 1) * road_runs_per_game + home_runs_per_game)


@profiled(category="valuation")
def composite_park_factor(raw_factor: float) -> float:
    """Composite (halved) factor (raw + 1) / 2, the scale FanGraphs applies to wRC+, ERA- and similar."""
    return (raw_factor + 1.0) / 2.0


@profiled(category="valuation")
def regress_park_factor(composite_factor: float, *, years: int) -> float:
    """Regress a composite factor toward 1.00: 1 - (1 - factor) * X, with X from the seasons of data used."""
    if years < 1:
        raise ValueError("years must be at least 1.")
    x = YEARS_TO_REGRESSION[min(years, 4)]
    return 1.0 - (1.0 - composite_factor) * x
