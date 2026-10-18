## Why

The literature catalogue (`docs/LITERATURE.md`, entries 1, 3 and 4) ranked Game Score v2, Game Score and Off as cheap, fully specified additions whose formulas were read in primary sources and whose inputs already exist in the canonical schema.

## What Changes

- Add `game_score` (Bill James's original) and `game_score_v2` (Tom Tango) as per-game pitching metrics.
- Add `off` (FanGraphs), batting runs plus BsR, composed from existing wRAA and BsR with the park and league adjustments.
- Add methodology audit entries with evidence tiers and hand-derived value tests.

## Capabilities

### New Capabilities
- `game-score-and-off`: per-game pitcher Game Score (two versions) and the FanGraphs Off offensive value metric.

### Modified Capabilities
<!-- none -->

## Impact

- `types/enums.py`, `metrics/pitching.py`, `metrics/weighted.py`, `data/methodology.yaml`, `docs/METHODOLOGY.md`, tests, ADR-0030.
