# ADR-0077: Glicko-2 Rating Update

Status: Accepted (adopted by default from the research specs; owner to confirm the defaults listed below)

## Context
The library has forecasting models (Marcel, Log5, Markov) but no rating system. Glicko-2 (Glickman) updates a rating, a rating deviation and a volatility once per rating period from the games in that period. Its published worked example prints every intermediate value, so it can be reproduced exactly. No baseball use was found in the research notes, so the evidence is the author's own example.

## Decision
Add `sabermetricspy.models.glicko2` with `glicko2_update`, `glicko2_expected_score`, the frozen `Glicko2Rating` and `GLICKO2_SCALE = 173.7178`, re-exported from the package root. The update follows the printed steps exactly (scale conversion, `g`, `E`, `v`, `Delta`, the Illinois iteration for the volatility with epsilon 1e-6, then the new deviation and rating); with no games only the deviation grows. `tau` is a required keyword with no default. Scores must be 0, 0.5 or 1; invalid input raises `ValueError`. No home-field term. It reproduces all the printed values of Glickman's worked example (`tests/golden/glicko2.yaml`; full precision r' = 1464.0507, RD' = 151.5165, sigma' = 0.059996, against printed 1464.06, 151.52, 0.05999 which come from rounded intermediates). Methodology status `matches`, evidence `golden`; `@profiled` and one benchmark.

Defaults adopted without an owner answer (research spec `glicko2_update`, O-GL-1 to O-GL-6): scalar update first with the rating period left to the caller; `tau` required; the dataframe estimator is deferred; file `models/glicko2.py`; raise on other scores; no Glicko-1.

## Alternatives
- Default `tau` to 0.5, not chosen now because 0.5 appears only in the worked example and the author says to test it for the application; revisit if users want a convenient default.
- A dataframe estimator `Glicko2Model` that applies the update across all players per period, not chosen now because it adds no outside value and needs rating-period and home-advantage policy decisions; revisit once a baseball use case is chosen.
- Glicko-1, not chosen now because Glicko-2 is the version with the complete printed example; revisit if there is demand.
- Accept fractional scores, not chosen now because the printed method defines only 0, 0.5 and 1; revisit with a margin-of-victory extension that has a source.

## Consequences
New public functions and class; one methodology entry; one benchmark; `docs/METHODOLOGY.md` regenerated. No baseball validation exists, only the author's example.
