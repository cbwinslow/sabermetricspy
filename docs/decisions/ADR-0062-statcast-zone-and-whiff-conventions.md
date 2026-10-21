# ADR-0062: Statcast Zone Rates Use the Geometric Zone; Whiff% Uses Savant's Counting

Status: Accepted

## Context
Zone, Z-Swing%, Z-Contact% and Whiff% differed from outside values by up to 4.7 percentage points on the recorded Skubal 2024 sample (2,868 pitches). FanGraphs' plate-discipline page does not define its zone ("varies by source"). Savant's glossary could not be read, so Whiff% counting was settled numerically.

## Decision
- When `plate_x`, `plate_z`, `sz_top` and `sz_bot` are present, a pitch is in the zone if any part of the ball touches the rulebook zone (plate half-width 8.5 in plus the 1.45 in ball radius; top and bottom widened by the radius). Otherwise Savant's `zone` field is used. This rule is inferred, not published: it reproduces FanGraphs' in-zone counts exactly (1571 pitches, 1070 swings, 845 contacts), and the out-of-zone side is one pitch off.
- Whiff% counts foul tips as whiffs and bunt attempts as swings (`whiffs_savant`, `swings_savant`), which reproduces Savant's published 27.7 / 16.0 / 46.4. SwStr% and CSW% keep FanGraphs' counting.

## Alternatives
- Keep Savant's `zone` field, not chosen now because it is 3 pitches off FanGraphs' counts and the geometric rule fits exactly; revisit if a second sample disagrees.
- Switch every metric to Savant's counting, not chosen now because FanGraphs' rates match FanGraphs' counting (SwStr% within one pitch); revisit if Savant publishes its definitions.

## Consequences
Z-Swing% and Z-Contact% become `matches`; the zone rule is flagged as inferred. It was checked on a second pitcher and season (Gerrit Cole 2023, 3,286 pitches, 2026-10-21): every rate is within 0.08 percentage points of FanGraphs, Z-Contact% is exact again, and Savant's zone field is worse on that sample (up to 0.33 points).
