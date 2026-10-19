## Context

Scoring rules are textbook definitions, so correctness is fixed by hand-computed values and by identities (the Murphy decomposition), not by fetched leaderboards.

## Decisions

- **Frame plus column names**, like the rest of the library, accepted through narwhals and reduced to numpy arrays. A scoring rule is a single reduction, so a vectorised numpy sum is used; there are no per-row loops.
- **Weights are optional** and apply as a weighted mean. Tango's Marcel comparisons weight by playing time.
- **Brier score** is the binary form, mean of (f - o)^2 (Brier 1950, reduced to one event). The Brier skill score is 1 - BS / BS_reference, with the climatological base rate as the default reference.
- **Calibration table** bins forecasts into equal-width bins and returns count, mean forecast, observed rate. The Murphy (1973) decomposition BS = reliability - resolution + uncertainty is exact when forecasts are constant within each bin and approximate otherwise, so the function reports the within-bin remainder rather than hiding it.
- **Log loss** clips probabilities to [eps, 1 - eps] with a documented eps so a certain wrong forecast is finite.

## Risks

Binned decomposition depends on the bin count; the default is 10 and it is a parameter.
