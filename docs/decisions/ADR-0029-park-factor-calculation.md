# ADR-0029: Park Factor Calculation and a Sourced Park Table

- **Status**: Accepted
- **Date**: 2026-10-18
- **OpenSpec change**: `park-factor-calculation`

## Context
Park-adjusted metrics (wRC+, OPS+, ERA+, ERA-) took the park factor from the caller and defaulted to 100. The bundled
`park_factors.yaml` held 7 parks that disagreed with FanGraphs Guts! 2024 in several cells:

| Team | Field | Bundled | Guts! |
|---|---|---|---|
| BOS | 5-year | 104 | 103 |
| CIN | 5-year | 105 | 102 |
| SFG | 5-year | 96 | 97 |
| COL | HR | 117 | 107 |
| CIN | HR | 119 | 114 |
| NYY | HR | 109 | 104 |
| SFG | HR | 85 | 91 |
| SEA | HR | 95 | 96 |

## Decision
1. `sabermetricspy.value.park` adds `raw_park_factor`, `composite_park_factor` and `regress_park_factor` from the
   FanGraphs Library article (raw = H*T/((T-1)*R + H); composite = (raw+1)/2; regressed = 1 - (1 - composite)*X with
   X = 0.6, 0.7, 0.8, 0.9 for 1, 2, 3, 4 or more seasons). The article's worked regression examples are tests. Its
   "home 11, road 10 gives 1.10" is the simple ratio; the formula with 30 teams gives 330/301 = 1.096, which rounds
   to the printed 1.10 and composite 1.048 (printed 1.05).
2. The bundled table is the 30-team Guts! 2024 snapshot, generated from `tests/golden/park_factors_2024.yaml`
   (5-year and HR agree across two fetches; the 1-year column came from one). Park ids are the team abbreviation.
3. `get_park_factor` warns when a park is not bundled instead of silently returning neutral.

## Consequences
- Park-adjusted metrics still need the caller to pass the factor; the window of up to five seasons centered on the
  season is left to the caller because it needs multi-season home and road splits.
- Guts! does not describe how its 5-year value is regressed, so the bundled values are recorded, not recomputed.
