# ADR-0052: Win Expectancy Is Fitted From Play-by-Play

Status: Accepted

## Context
`WinProbabilityModel` is a closed-form normal approximation. Against 54 cells of Tom Tango's published win-expectancy
table its mean absolute error is 0.048 and its worst cell 0.194 (trailing by one run, runners on second and third, no
outs: 0.527 against 0.721), because it ignores that one run ties the game. Rule 7 says an approximation with no
outside reproduction should not be the supported path.

## Decision
Add `WinExpectancyMatrix`, which is the observed home win rate per inning, half, outs, bases and score difference,
the quantity Tom Tango's tables report (`tangotiger.net/welist.html` is a 2002 page that states no method; his current
`we.html` describes a model built from run expectancy, so his tables are references, not the construction used). It
has no built-in table, leaves unobserved states unfitted, and reports `state_games` and a standard error that counts
games, an approximation because the plate appearances of one game share a result. The rate itself is weighted by
plate appearance. `WinProbabilityModel` stays, with its note pointing to the fitted matrix.

Checked on Retrosheet 2016 (2,428 games, one tied game dropped, 184,541 plate appearances, from the CC0
`retro2016.rda` in abdwr3edata): the 16 bottom-of-the-9th cells with 30 or more games are all within three standard
errors of the 2002 table (largest 2.11) and the 6 cells with 100 or more games are within 1.7. These figures are pinned
in `tests/test_retrosheet_2016_win_expectancy.py`. An earlier version of this ADR said 2,428 games, 17 cells and 50 or
more games within two standard errors; that came from a fixture that counted non-plate-appearance events and was
corrected in ADR-0055. The check runs when the data file is supplied; CI supplies it. Hand-computed unit tests always run.
Follow-up: add `we.html` (2010 to 2015, which names its seasons) as a second reference.

Alternatives considered: (a) delete `WinProbabilityModel`, not chosen now because callers use it for leverage index
and WPA with no data at hand; revisit once the fitted matrix drives `leverage_index`. (b) Smooth sparse cells with a
parametric model, not chosen now because no published smoothing method was found; revisit if one is. (c) Fit from
many seasons for the validation, not chosen now because only the 2016 file is available without a Chadwick toolchain;
revisit when a multi-season event source is bundled.

## Consequences
Users with play-by-play get a validated win expectancy and a per-cell uncertainty. Leverage Index and WPA still come
from the approximation; making them use the fitted table is a later change. Extra innings are not pooled: each inning
number is its own state.
