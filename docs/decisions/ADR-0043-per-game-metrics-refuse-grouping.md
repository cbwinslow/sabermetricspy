# ADR-0043: Per-Game Metrics Refuse Grouping

Status: Accepted

## Context
`calculate(by=...)` sums every input column before evaluating formulas. Game Score, Game Score 2.0, Shutdown and Meltdown
describe one game, so summing first gave nonsense with no warning: two 92-point games grouped gave 142, and Shutdown
summed `game_wpa` and `is_reliever` across games before applying its thresholds. The only guard was caveat text. An
independent review of the repository reported the same defect, and the audit test itself had accepted the grouped values.

## Decision
`MetricSpec` has a `per_row` flag, set on those four metrics. `calculate(by=...)` raises `ValueError` when a requested
metric (or one it depends on) is `per_row`, telling the caller to calculate per game and aggregate the results. The
convenience entry points `calculate_suite` and `calculate_available` leave `per_row` metrics out when `by` is given,
because a suite or an "everything computable" request should not fail for a metric that cannot apply.

Alternatives considered: (a) keep the caveat text only, not chosen now because the result is silently wrong;
(b) compute per row first and then aggregate inside the engine, not chosen now because the right aggregate (sum for
Shutdown, mean or distribution for Game Score) is the caller's choice; revisit if a standard season aggregate emerges.

## Consequences
Callers who grouped these metrics now get an error instead of a wrong number. Tests: `tests/test_per_row_metrics.py`;
`test_all_registered_metrics_and_suites_audit` now computes them per game.
