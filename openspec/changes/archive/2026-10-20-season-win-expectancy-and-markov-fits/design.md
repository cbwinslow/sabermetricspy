# Design

## Context

Recorded after implementation. The decisions and their alternatives are in `docs/decisions/ADR-0051-season-constants-follow-the-data.md`,
`ADR-0052-fitted-win-expectancy.md` and `ADR-0053-markov-chain-from-play-by-play.md`; this document does not repeat them.

## Goals / Non-Goals

**Goals:** methods with a published value to check, loud failures for mismatched seasons and unobserved states.
**Non-Goals:** replacing `WinProbabilityModel` or the event-probability `MarkovChainModel.fit`, which stay with their
measured gaps documented; making Leverage Index and WPA use the fitted table.

## Decisions

- Season is inferred from the data before falling back to 2024, because a frame that names its season is stronger
  evidence than a library default (ADR-0051).
- Win expectancy and the Markov chain are plain empirical estimators over play-by-play, with games-based uncertainty and
  exact matrix solution respectively (ADR-0052, ADR-0053).

## Risks / Trade-offs

- [Callers relying on 2024 constants for older data now get that data's season or an error] -> documented in the ADR and changelog.
- [One season leaves rare win-expectancy states sparse] -> per-state game counts and standard errors are exposed.
