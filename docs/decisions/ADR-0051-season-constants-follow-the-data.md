# ADR-0051: Season Constants Follow the Data

Status: Accepted

## Context
`calculate(df, metrics)` with no context took `season=2024` and applied 2024 wOBA, FIP and league constants to any
frame. A 2001 frame with a `season` column returned 2024 values for wRC+, wOBA and FIP-, with no warning. ADR-0041
rejected frames holding several seasons but not a single season that disagreed with the constants.

## Decision
`season` defaults to `None` in `calculate`, `calculate_suite`, `calculate_available` and `calculate_rolling`. When the
caller gives neither `context` nor `season`, the engine uses the one season in the frame's `season` column, else
`DEFAULT_SEASON` (2024). Only metrics that read the season constants are checked:
- a frame whose single season differs from the context's season raises `ValueError`;
- no season given and no `season` column warns that `DEFAULT_SEASON` constants are being used;
- metrics that read no constants (AVG, OBP) are unaffected.

Alternatives considered: (a) require `season` on every call, not chosen now because it breaks context-free metrics and
every existing call; revisit at 1.0. (b) Always warn on the default, not chosen now because a frame with a season
column already says which season it is.

## Consequences
Behavior changes for callers who relied on 2024 constants for older data: they now get the frame's season, or an
error if they also passed a different season. `WARFramework` still defaults to 2024 and is unchanged here.
