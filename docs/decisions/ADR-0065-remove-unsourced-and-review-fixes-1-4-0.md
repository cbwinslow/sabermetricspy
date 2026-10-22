# ADR-0065: Remove the Unsourced Items and Tighten Claims (1.4.0)

Status: Accepted

## Context
After 1.3.0 seven items were still `experimental` because no published value could be reproduced: `rc27`, `qera`, `speed_score`, `bsr`, the event-probability `MarkovChainModel.fit`, `MonteCarloSimulator` and `Log5Model.extended_pythagorean_home_win_prob`. An independent review of 1.3.0 also found claims in notes that went further than their tests show.

## Decision
- **Removed:** `rc27` (no source states its out count), `qera` (formula printed by Baseball Prospectus, values paywalled, superseded by the shipped SIERA), `speed_score` (neither published form reproduces FanGraphs' Spd), `MarkovChainModel.fit` and `MonteCarloSimulator` (library-chosen advancement rules; the simulator also looped per plate appearance), and `Log5Model.extended_pythagorean_home_win_prob` (one paper footnote). `MarkovChainModel.fit_transitions`, estimated from play-by-play as in Albert, Baumer and Marchi, stays.
- **Kept `experimental`:** `bsr` only. Its definition is FanGraphs' own sum, wSB inside it is tied out, and `off` and WAR use it.
- **Downgraded to `approximate`:** `off` (not compared with the FanGraphs Off column; built on `bsr`) and `sweet_spot_pct` (measured 0.5 to 2.1 points high against Savant).
- **Notes corrected:** the `ip` test is a round trip of the innings notation, not an independent total; `ra9` is checked only on the 170 pitcher-seasons whose runs equal earned runs; `k_minus_bb_pct` is credited with the batter difference only; the DER mean gap is 0.0025 and its cause (Baseball-Reference estimating reached-on-error) is stated as likely, not confirmed.

## Alternatives
- Keep the seven items quarantined, not chosen now because a warning does not stop the numbers being copied into other work and the library should hold only checked methods; revisit if a published value for any of them is found.
- Rework `MonteCarloSimulator` on the `fit_transitions` matrix, not chosen now because no published value exists to test it against (the book's own matrix is itself simulated); revisit if a reproducible simulation reference appears.
- Remove `bsr`, not chosen now because FanGraphs documents the sum and `off` and WAR need it; revisit if the unexplained gap in the leaderboard total cannot be closed.
- Move `base_runs`, `seca`, `gpa`, `ta` and `dice` down a level, not chosen now because each is a published formula checked against its definition and the evidence tier already says no number was reproduced; revisit if outside values for them are found.

## Consequences
Public names `Metric.RC27`, `Metric.QERA`, `Metric.SPEED_SCORE`, `MonteCarloSimulator`, `MonteCarloSimulationResults`, `MarkovChainModel.fit` and `Log5Model.extended_pythagorean_home_win_prob` no longer exist. Users who need an RC/27 can divide `rc_tech` by their own out count.
