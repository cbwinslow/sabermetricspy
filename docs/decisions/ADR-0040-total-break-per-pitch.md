# ADR-0040: Total Break Is the Mean Per-Pitch Magnitude

Status: Accepted

## Context
`total_break` was computed as sqrt(mean IVB squared + mean HB squared), the magnitude of the average break. Opposite
horizontal breaks cancel in that form: two pitches with +10 and -10 inches of horizontal break and no vertical break gave 0
instead of 10. The audit (`docs/METHODOLOGY.md`) had already noted that the magnitude of the means is not the mean of the
per-pitch magnitudes. No published total-break definition was found; the geometry itself is standard.

## Decision
The `statcast` preset sums each pitch's sqrt(IVB squared + HB squared) into a new column `total_break_sum`, and
`total_break` = `total_break_sum` / `break_count`, following the sum-then-divide rule. `total_break` no longer depends on the
`ivb` and `hb` metrics. Callers supplying pre-aggregated data must now provide `total_break_sum`; without it `total_break`
is skipped by `calculate_available` instead of being computed from means.

Alternatives considered: (a) keep the magnitude of the means and only rename it, not chosen now because the number
misleads for pitchers whose breaks differ in direction; revisit if a published definition turns out to use the means;
(b) derive the magnitude from per-pitch columns at calculation time, not chosen now because the engine aggregates
counting columns first and per-pitch data is not available at that stage.

## Consequences
Hand-computed tests pin the cancellation case and a 3-4-5 case (`tests/test_total_break.py`). The metric stays
`approximate` with `secondary` evidence because no outside value exists to compare against.
