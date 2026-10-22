# ADR-0067: Compute League Constants from Lahman

Status: Accepted

## Context
ADR-0066 records the owner's decision not to redistribute FanGraphs values. Lahman (SABR, CC BY-SA 3.0) holds the season totals that most of the bundled league constants are sums of.

## Decision
Add `sabermetricspy.lahman` (`download_lahman`, `league_constants`, `LeagueConstants`). It downloads the Lahman batting and pitching CSV files to the user's cache from `cbwinslow/lahman-database-csv`, a mirror of the SABR release (or any `base_url`), and computes, for MLB, AL or NL: plate appearances, runs, outs, runs per PA, OBP, SLG, ERA, the FIP constant (league ERA minus the FIP numerator over league innings), the kwERA constant and the caught-stealing run value (-(2 x runs per out + 0.075), the FanGraphs Library definition).

Measured against the FanGraphs values bundled today, for every season 1990 to 2025: OBP and SLG within 0.000006, cFIP within 0.0007, runs per PA within 0.0006, ERA within 0.0009 and the caught-stealing value within 0.0006, all inside FanGraphs' own rounding. The kwERA constant matches through 2020; from 2021 FanGraphs uses an empirical term (see `woba_fangraphs.yaml`), so it is not claimed after 2020. A Lahman sample under `tests/fixtures/lahman` pins these in `tests/test_lahman_constants.py`.

This stage adds the builder and the evidence. The bundled FanGraphs table stays in place until wOBA weights, park factors and batted-ball constants have a replacement source, because the engine cannot compute wOBA without weights.

## Alternatives
- Replace the bundled table now with the Lahman values, not chosen now because the linear weights, `lg_wrc_per_pa`, park factors, xFIP and SIERA constants cannot be built from Lahman (BaseRuns marginal values were 0.03 to 0.29 off and team-season regressions 0.07 to 1.1 off), so the engine would lose wOBA; revisit when a play-by-play source is chosen.
- Bundle the computed values as a data file, not chosen now because the data would be a CC BY-SA adaptation shipped inside an Apache-2.0 package; revisit if the owner accepts a separately licensed data file.
- Use the CRAN `Lahman` package or the SABR download page directly, not chosen now because the mirror is the owner's copy of the same 1871 to 2025 release (team totals identical); revisit if the mirror falls behind a new release.

## Consequences
`sabermetricspy.lahman` performs network I/O only when `download_lahman` is called (as `sabermetricspy.ids` does for the Chadwick Register). Crediting SABR and Sean Lahman is required for results that use it.
