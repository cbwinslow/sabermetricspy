# ADR-0041: Reject Frames That Mix Seasons When a Metric Needs Season Constants

Status: Accepted

## Context
`calculate` resolves one `SeasonContext` per call and every metric that reads wOBA weights, FIP constants or league rates
uses that single set for every row. A frame holding 2001 and 2024 rows, grouped by season, therefore returned the 2024
wRC+ for both seasons with no warning (reproduced: 158.6 for both rows; calculated alone, 2001 gives 140.3). The README
quickstart used exactly that pattern. An independent review of the repository reported the same defect.

## Decision
When the frame has a `season` column with more than one distinct value and a requested metric reads the season
constants, `calculate` raises `ValueError` naming the affected metrics and asking for one call per season. Whether a metric
reads the constants is detected by running its expression builder against a recording stand-in for the context, so no
per-metric flag has to be maintained. Metrics that never read the constants (AVG, OBP and the other count ratios) still
accept several seasons.

Alternatives considered: (a) join the constants per row by the `season` (and league) column, not chosen now because it
changes every contextual metric and the park and league handling, which is a larger change than the bug warrants;
revisit if callers need multi-season frames often; (b) a warning instead of an error, not chosen now because the numbers
are wrong, not merely risky; (c) a flag on each `MetricSpec`, not chosen now because 130+ specs would need it and it can
drift from what the builder actually does.

## Consequences
Mixed-league frames inside one season are not detected: league-specific metrics still use the league in the context.
Callers loop over seasons (and leagues) themselves. Tests: `tests/test_multi_season_guard.py`.
