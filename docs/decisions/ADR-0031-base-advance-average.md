# ADR-0031: Base-Advance Average

- **Status**: Accepted
- **Date**: 2026-10-18
- **OpenSpec change**: `base-advance-average`

## Context
Entry 1 of `docs/LITERATURE.md`. Hardegree (2005, via Retrosheet) defines bases advanced (batter and runners, erased
runners negative) over base-advance opportunities (the most each runner could advance).

## Decision
`expectancy.add_base_advance_columns` derives, per plate appearance from base states and runs, bases advanced =
4R + Pa - Pb and opportunities = 4 + 4n - Pb (Pb, Pa the sums of occupied base numbers before and after, n the runners
before). `base_advance_average` divides the summed columns. The paper's sample half-inning (8 plate appearances, 14 over
57) reproduces row by row, as do the 4-for-10 bases-loaded walk and 10-for-10 grand slam it describes. The paper prints
.245 for 14/57 = .2456, a truncation.

## Consequences
Inputs must keep runners stranded at the third out in the after-state; steals are not counted. Both are in the metric caveats
and the helper docstring.
