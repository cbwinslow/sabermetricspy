# ADR-0053: Markov Chain Is Fitted From Play-by-Play

Status: Accepted

## Context
`MarkovChainModel.fit()` builds the 24-state chain from event probabilities with fixed advancement rules. Its docstring
cited Bukiet, Harold and Palacios (1997), a paper that sits behind the publisher paywall and was never read, so the
advancement rules had no source and the model was `approximate` with no outside value to check. Albert, Baumer and
Marchi, *Analyzing Baseball Data with R* (3rd ed.), chapter 9.2, is free to read and does the same job from data: the
transition matrix is the observed frequency of each next state, three outs is absorbing, and the chapter prints its
2016 values.

## Decision
Add `MarkovChainModel.fit_transitions(df)`, which estimates the 24 x 25 matrix from batting plays and solves
`N = (I - Q)^-1` exactly, plus `state_distribution(n)` for the state after `n` batters. It reproduces the chapter's
printed transition probabilities, 4.27 plate appearances per half-inning, the expected plays from eight states, and
the three-batter distribution on Retrosheet 2016 (opt-in test), and a home-run-or-out chain reproduces the closed form
3p/(1-p) (always-on test). Printed values are in `tests/golden/markov_abdwr_2016.yaml`.

`fit()` stays, documented with its measured gap to the fitted chain: league-average 2016 event rates give 0.479 runs
from the empty state against 0.485, 2.13 against 2.21 with the bases loaded and no outs, and 4.41 plate appearances per
half-inning against 4.27. The longer innings come from rules with no double plays or outs on the bases; the effect of
each rule was not separated (an earlier version blamed errors counted as outs, which would shorten innings). The
docstring no longer claims the Bukiet paper as its source. The method is rated `approximate`, not `matches`, because its
reference check runs only when the Retrosheet file is supplied; CI supplies it, and the tier can rise once that run
has passed (ADR-0055).

Alternatives considered: (a) remove `fit()`, not chosen now because it is the only path for a single batter or a
hypothetical lineup with no play-by-play; revisit if a published advancement model replaces its fixed rules.
(b) Implement Bukiet et al. from the abstract, not chosen now because the transition rules in the paper are not
available to read; revisit when the full text is obtained. (c) Per-team or per-batter transition matrices, not chosen
now because the chapter notes small samples need adjustment and describes no single standard; revisit once a team
adjustment is validated.

## Consequences
Run expectancy by state, expected batters per inning, and multi-batter state forecasts can now be computed from any
play-by-play source and checked against a published book. `MonteCarloSimulator` still uses the fixed advancement rules.
Non-batting plays (steals, wild pitches) are not in the chain, as in the book.
