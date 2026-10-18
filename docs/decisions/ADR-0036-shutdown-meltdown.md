# ADR-0036: Shutdown and Meltdown

Status: Accepted

## Context
The literature catalogue's top entry was Shutdown/Meltdown. The FanGraphs Library page (read 2026-10-18) defines them:
a reliever earns a Shutdown with a game WPA of +0.06 or more and a Meltdown with -0.06 or less.

## Decision
Add `shutdown` and `meltdown` as per-appearance 0/1 indicators over `game_wpa` and `is_reliever`; callers sum them.
Thresholds are inclusive and starters never qualify.

## Evidence and limits
Only the threshold semantics are tested (`tests/test_shutdown_meltdown.py`). FanGraphs leaderboard counts (for example
Jeurys Familia 2016: 43 SD, 8 MD) cannot be recomputed because per-game WPA is not bundled, so the entries are labeled
`matches` on the primary definition, not on a reproduced player value.
