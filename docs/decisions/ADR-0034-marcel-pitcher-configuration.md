# ADR-0034: Marcel Pitcher Configuration

- **Status**: Accepted
- **Date**: 2026-10-18

## Context
ADR-0028 left `MarcelProjector (pitchers)` `divergent`: Tango's pitcher method (weights 3/2/1, innings instead of plate
appearances, the 200 in the playing-time formula replaced by 25 for relievers and 60 for starters) was not reachable
because the base was hard-coded at 200.

## Decision
`MarcelProjector` takes `playing_time_base`, a number or the name of a column of per-player bases. With
`season_weights=(3, 2, 1)`, `exposure_col="ip"` and a base of 25 or 60 the playing-time projection is Tango's. The hitter
formula reproduces his worked example (602 and 722 PA project to 573.2). The pitcher regression amount is unspecified in
the post, so the caller chooses `regression_pa`; the by-GS/G interpolation, the BaseRuns ERA split and league
assignment are not implemented. The pitcher entry is relabeled `approximate`, and the unsourced 134 IP remark is removed
from the documentation.
