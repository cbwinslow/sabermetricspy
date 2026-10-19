# ADR-0038: kwERA Uses the FanGraphs Seasonal Constant

Status: Accepted

## Context
`kwera` used Tango's 5.40. A research agent compared FanGraphs' API kwERA with our formula and found 2024 starters about
0.57 runs lower in ours. I re-fetched and recomputed it: for every pitcher in a season, kwERA + 12 (SO - BB) / TBF is the same
number C (2001: 5.4828; 2016: 5.7433; 2024: 5.9660), so FanGraphs uses a seasonal constant. The Hardball Times page cited
in the old note does not print a formula.

## Decision
Bundle `kwera_constant` per season (1990 to 2025) and use it, falling back to 5.40 when absent. For 1990 to 2020,
C = lgERA + 12 (lgSO - lgBB) / lgTBF, which reproduces 2001 and 2016 to 2020 exactly. For 2021 to 2025 the measured C is
lgERA + 1.887 in every season; 1.887 equals no league K-BB rate, so those years are empirical. 13 pitcher seasons
(2001 to 2025) match within 1e-4 (`tests/test_kwera.py`).

## Consequences
`kwera` now matches FanGraphs rather than the original 2008 form; the default result changes by about 0.5 runs.
Callers wanting Tango's original can set `kwera_constant=5.40` on the weights. If FanGraphs documents the 2021+ term,
the bundled constants should be rederived.
