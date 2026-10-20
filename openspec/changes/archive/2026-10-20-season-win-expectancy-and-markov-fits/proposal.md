# Proposal

This change is written after the code (commits `b0ba9c8`, `6131c86`, `60b54d4`) to bring OpenSpec in line with
ADR-0051, ADR-0052 and ADR-0053; the work was done without a change first, which the project process does not allow.

## Why

A 2001 frame passed to `calculate()` with no context silently received 2024 constants. Win expectancy had only a normal
approximation that missed Tom Tango's published table by up to 0.19. The Markov chain model had hard-coded runner
advancement and a source (Bukiet, Harold and Palacios 1997) that was never read. Each needed a method with a published
value to check against.

## What Changes

- Season constants follow the data: `season` defaults to unset; a frame holding one season uses it; a frame whose season
  contradicts the context raises; with no season anywhere, constant-reading metrics warn that 2024 is being used (ADR-0051).
- Add `WinExpectancyMatrix`, the observed home win rate per inning, half, outs, bases and score difference, with the
  number of games per state and a games-based standard error (ADR-0052).
- Add `MarkovChainModel.fit_transitions` and `state_distribution`, the 24-state absorbing chain estimated from
  play-by-play and solved exactly, checked against the printed values in Albert, Baumer and Marchi, *Analyzing Baseball
  Data with R* (3rd ed.) chapter 9.2 (ADR-0053).

## Capabilities

### New Capabilities
- `fitted-win-expectancy`: win expectancy estimated from play-by-play with per-state sample sizes and uncertainty.
- `fitted-markov-chain`: the base-out Markov chain estimated from play-by-play and solved exactly.

### Modified Capabilities
- `seasonal-constants`: constants are selected from the data's season, and mismatches are errors or warnings.

## Impact

`engine.calculate`, `calculate_suite`, `calculate_available`, `calculate_rolling` (`season` default `None`);
`expectancy.WinExpectancyMatrix`; `models.MarkovChainModel`; tests, golden fixtures and `docs/METHODOLOGY.md`;
ADR-0051 to ADR-0053.
