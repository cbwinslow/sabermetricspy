# ADR-0044: Barrels Come From Statcast's Own Label

Status: Accepted

## Context
The statcast preset approximated the barrel zone from the glossary anchor (98 mph at 26 to 30 degrees) with linear widening,
and found 28 barrels on the recorded Skubal 2024 sample against FanGraphs' 32. Statcast's pitch data already carries
`launch_speed_angle`, whose value 6 is Barrel (Baseball Savant CSV docs). Counting `launch_speed_angle == 6` on the sample
gives exactly 32. The numeric zone table appears only in an image in the docs, so it cannot be reproduced from text.

## Decision
The preset derives `barrels` from `launch_speed_angle == 6` on pitches with a tracked exit velocity, and no longer
approximates the zone. `barrel_pct` is now `matches` with `golden` evidence (32 barrels, 6.65 percent).

Alternatives considered: (a) keep the approximation as a fallback when the column is absent, not chosen now because it is
a guess that undercounts by about 12 percent; revisit if Savant publishes the zone as numbers; (b) re-implement the
zone from a third-party table, not chosen now because no primary numeric source was found.

## Consequences
Data without `launch_speed_angle` yields no `barrels` column, so `barrel_pct` is skipped for it rather than estimated.
