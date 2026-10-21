# Proposal: v1.0.0 Readiness

## Why
sabermetricspy is a pure calculation library (ADR-0003). Data acquisition and id/name handling live upstream (retrosheetpy, the caller's warehouse). Recent work drifted into downloaders and a name register; this change closes that out and finishes v1.

## What Changes
- `sabermetricspy.ids` gains `update_register()` (commit-checked, atomic) and a staleness warning so the Chadwick Register can be kept current; the network is touched only by `download_register` and `update_register`.
- baseballr tie-outs are added only from real, recorded baseballr output.
- Release audit of methodology docs and quality gates.

## Impact
Additive only. No change to metrics or estimators.
