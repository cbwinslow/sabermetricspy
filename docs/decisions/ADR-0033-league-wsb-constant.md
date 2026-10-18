# ADR-0033: Bundled League wSB Constant

- **Status**: Accepted
- **Date**: 2026-10-18

## Context
`wSB` subtracts `lgwSB x (1B + BB + HBP - IBB)`, but `lg_wsb` defaulted to 0, so the league adjustment was omitted and
the metric was labeled approximate.

## Decision
`lg_wsb` is now bundled for 1990 to 2025, computed as `(lgSB x runSB + lgCS x runCS) / (lg1B + lgBB + lgHBP - lgIBB)`
from the FanGraphs league leaderboard (`tests/golden/league_sbcs_snapshot.yaml`; its BB, IBB and HBP equal the existing
league totals snapshot and its 1B equals H - 2B - 3B - HR). The 2024 value of 0.00789 reproduces FanGraphs' published
wSB for eight players to three decimals; the FanGraphs API field named `wBsR` carries wSB. `wsb` is relabeled
`matches` with golden evidence. `bsr` stays approximate because the wGDP constants (0.105, 0.44) have no published
source: the FanGraphs wGDP page gives neither.

## Consequences
Callers who passed `lg_wsb` explicitly are unaffected; callers relying on the old default of 0 now get FanGraphs'
values for bundled seasons.
