# Proposal: 1.0.1 Methodology Cleanup

## Why
An audit after 1.0.0 measured every approximate metric and model against its outside value. Some gaps were our mistakes (strike-zone rule, Whiff% counting), four metrics had no published method, and several items had no reproducible outside value. Rule 7 forbids shipping those as supported.

## What Changes
- Geometric strike zone and Savant's Whiff% counting in the statcast preset (ADR-0062).
- Remove `total_break`, `whiff_per_100`, `two_strike_chase_pct`, `wgdp`; `bsr` takes `ubr` and `wgdp` inputs.
- `experimental` status that warns: `siera`, `rc27`, `xfip_minus`, `WinProbabilityModel` (ADR-0061).
- Real Baseball-Reference OPS+ values; a bound test for documented divergences.
- `docs/VERIFICATION.md` with confirmed items, measured gaps and the research queue.

## Impact
Four metrics removed (breaking for callers of those names). Everything else changes values only where a mistake was fixed.
