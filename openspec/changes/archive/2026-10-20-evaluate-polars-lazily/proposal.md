# Proposal

## Why

A backend review (2026-10-20) found that `calculate` on an eager Polars frame is about 70 times slower than on the same
frame passed lazily, with identical results: 30 metrics on 120,000 rows and 98 columns took 8.7 s eager and 0.12 s lazy
(a frame with only the 14 needed columns still took 2.4 s eager). The engine adds each metric with its own eager
`with_columns`, and each call costs a pass over the whole frame, so the time grows with rows times columns times metrics.
The library promises speed on millions of rows, and most users pass eager Polars frames.

## What Changes

- When the input is a Polars (or Polars-convertible) eager frame, the engine builds the metric columns on a lazy frame
  and collects once at the end, so Polars optimizes the whole plan. Output type and values are unchanged.
- Other backends keep their current evaluation.
- A regression test compares the engine's output on a large frame with a saved reference and checks every registered
  metric still gives the same values.

## Capabilities

### New Capabilities

None.

### Modified Capabilities
- `sabermetrics-engine`: adds a requirement that evaluation cost for Polars input does not grow with a pass over the whole
  frame per metric.

## Impact

`engine.calculate` stage 2 only. No change to metric formulas, results, return types or any other module. Benchmarks and
documentation updated with the measured speed-up.
