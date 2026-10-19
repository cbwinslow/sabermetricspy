# ADR-0042: Marcel Regression Adds 1,200 PA to the Weighted Total

Status: Accepted

## Context
`MarcelProjector` added `regression_pa * (w1 + w2 + w3) / 3` of league average, which is 4,800 PA with the 5/4/3
weights, and used one pooled league rate for every player. Tango's worked Beltran example
(`tangotiger.net/archives/stud0346.shtml`, read 2026-10-19) weights his three seasons to 318 HR over 7,938 PA, adds
league average at 1,200 PA (two weights of 600) to reach 9,138 PA, and gets .0386 HR/PA and about 22 HR. The library
returned .0358 for the same inputs. An independent review of the repository reported the over-regression, and the
published example confirmed it.

## Decision
The league-average component is `regression_pa` (default 1,200) added to the weighted exposure. Its rate is mixed from
the player's own seasons: each season's league rate (from the input frame) weighted by the recency weight and the
player's exposure in that season, as in Tango's example (league HR weighted 228, scaled to 34.4 at 1,200 PA).
`tests/test_model_audit.py` reproduces the example.

Alternatives considered: (a) keep scaling the amount with the weights, not chosen now because it contradicts the
published example; revisit if a source describes it; (b) one pooled league rate per fit, not chosen now because the
published example mixes the league rate per player.

## Consequences
Projections regress less toward the league mean than before. The pitcher configuration keeps `regression_pa` as a
caller choice because Tango gives no innings equivalent. The league rate comes from the players in the input frame, so
pitcher hitting should be excluded by the caller as Tango does. The age adjustment is unchanged and still has no worked
example; the re-baselining step is still not implemented.
