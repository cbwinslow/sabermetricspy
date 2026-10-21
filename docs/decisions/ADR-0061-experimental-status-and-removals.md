# ADR-0061: An `experimental` Status That Warns, and Four Metrics Removed

Status: Accepted

## Context
After 1.0.0 an audit of the 35 approximate metrics and 11 approximate models found four groups: fixable mistakes, black-box
sources with small gaps, library inventions with no published method, and items with no outside value yet. CLAUDE.md rule 7
says not to ship the third group as supported. ADR-0047 handled a similar case by deleting the code.

## Decision
- Remove `total_break`, `whiff_per_100` (100 x SwStr%), `two_strike_chase_pct` and `wgdp` (no published constants). BsR now takes `ubr` and `wgdp` as input columns, which is the FanGraphs identity BsR = wSB + UBR + wGDP.
- Add `ReferenceStatus.EXPERIMENTAL`. `siera`, `rc27`, `xfip_minus` and `WinProbabilityModel` carry it and emit a `UserWarning` naming the reason every time they are calculated or constructed. Their numbers are unchanged.
- Items with a small, measured and documented gap (`ops_plus`, `era_plus`, `fip_minus`) stay `approximate`; a test fails if a documented divergence grows beyond its measured bound.

## Alternatives
- Delete the four experimental items as ADR-0047 did, not chosen now because each has a published formula that is only unverified, and deleting breaks callers in a patch release; revisit if no outside value is found by 1.1.
- Move them to a separate `experimental` package, not chosen now because it doubles the packaging for four items; revisit if the list grows.
- Leave them as `approximate`, not chosen now because a warning at the point of use is the only thing a caller cannot miss.

## Consequences
Callers of the removed names get an error. Experimental items work as before and warn. OpenSpec change: `v1-0-1-methodology-cleanup`.
