# ADR-0052: Win Expectancy Is Fitted From Play-by-Play

Status: Accepted

## Context
`WinProbabilityModel` is a closed-form normal approximation. Against 54 cells of Tom Tango's published win-expectancy
table its mean absolute error is 0.048 and its worst cell 0.194 (trailing by one run, runners on second and third, no
outs: 0.527 against 0.721), because it ignores that one run ties the game. Rule 7 says an approximation with no
outside reproduction should not be the supported path.

## Decision
Add `WinExpectancyMatrix`, which is the observed home win rate per inning, half, outs, bases and score difference,
the construction behind Tango's table (`tangotiger.net/welist.html`). It has no built-in table, leaves unobserved
states unfitted, and reports `state_games` and a binomial `standard_error` that counts games, because plate
appearances in one game share a result. `WinProbabilityModel` stays, with its note pointing to the fitted matrix.

Validated on Retrosheet 2016 (2,428 games, from the CC0 `retro2016.rda` in abdwr3edata): every bottom-of-the-9th cell
with 30 or more games is within three standard errors of Tango's table and cells with 50 or more games are within two.
The check is opt-in (`SABERMETRICSPY_RETRO2016`); hand-computed unit tests run always.

Alternatives considered: (a) delete `WinProbabilityModel`, not chosen now because callers use it for leverage index
and WPA with no data at hand; revisit once the fitted matrix drives `leverage_index`. (b) Smooth sparse cells with a
parametric model, not chosen now because no published smoothing method was found; revisit if one is. (c) Fit from
many seasons for the validation, not chosen now because only the 2016 file is available without a Chadwick toolchain;
revisit when a multi-season event source is bundled.

## Consequences
Users with play-by-play get a validated win expectancy and a per-cell uncertainty. Leverage Index and WPA still come
from the approximation; making them use the fitted table is a later change. Extra innings are not pooled: each inning
number is its own state.
