# ADR-0068: Computation-Only Again, with Constants the Caller Supplies

Status: Accepted; network use amended by ADR-0069 (fetch on request, still no redistribution)

## Context
ADR-0003 says the library does no network I/O. By 1.5.0 it did: `ids` downloaded the Chadwick Register (and refreshed it in the background once a day), and `lahman` downloaded the Lahman files from the owner's unofficial mirror. Separately, the package shipped FanGraphs-derived constant tables, and FanGraphs' Terms of Service bar unauthorized reproduction or redistribution of its compiled content (ADR-0066). The owner decided not to ask FanGraphs and not to redistribute their values.

## Decision
- **No network code in the package.** `ids` keeps `load_register(path)` and all translation logic; `download_register`, `update_register`, `UpdateResult` and the automatic refresh are gone. The old download code lives on as `tools/fetch_register.py`, a maintainer script that is to move to `chadwickpy`. `lahman.download_lahman` and every reference to the unofficial mirror are gone; `lahman.league_constants` reads CSV files of the official SABR database that the user downloaded.
- **No third-party constants in the package.** The five tables (`woba_fangraphs`, `park_factors`, `park_fip`, `pitcher_war`, `league_war`) are no longer shipped. The caller supplies a FanGraphs Guts! table (`use_guts`, `load_guts`) or a directory of YAML files (`use_constants`, `$SABERMETRICSPY_CONSTANTS`). A season missing from the supplied table raises `ConstantsNotFoundError`; the old fallback to the nearest season is removed because with user tables it would silently give wrong numbers. `docs/CONSTANTS.md` shows the five-line way to get the Guts! table and what the library can compute (Lahman league constants, weights from the user's play-by-play).
- **Tests.** The full tables and the large FanGraphs leaderboard files stay on the maintainer's machine (git-ignored); the repository holds a one-season sample (`tests/constants_sample`) and short cited samples. Without the local files the suite uses the sample, reports a season outside it as skipped (no silent fallback exists, so a skip cannot hide a wrong number), and lists each test module it could not collect, with a count, in the run summary.
- **Left as is, deliberately.** The 24-number default RE24 table in `expectancy` (the FanGraphs Library page's published matrix, roughly neutral for 2014) and player-level golden samples (`tests/golden/batted_ball.yaml`, `pitching.yaml` and similar, about 20 cited rows each) are short published reference values, not league-wide compilations. The scripts in `tools/` query FanGraphs and MLB for the maintainer and are not shipped.
- The git history still holds the earlier tables; the owner chose not to rewrite it.

## Alternatives
- Keep shipping the tables with attribution, not chosen now because FanGraphs' terms bar redistributing compiled content and the owner does not want to risk a takedown or ban; revisit if FanGraphs grants permission.
- Ask FanGraphs for permission, not chosen now because the owner prefers not to contact them; revisit if the owner changes their mind.
- A separate data package that ships the tables, not chosen now because it is still redistribution.
- Compute every constant from open data, not chosen now because Lahman cannot give wOBA weights, park factors or SIERA constants and play-by-play sources carry their own terms; revisit if a licensed source appears.
- Keep explicit `download_register` in a clearly named submodule of this package, not chosen now because the package would still contain network code; revisit if the owner prefers one install for everything.
- Replace the default RE24 table with Tango's own 2010-2015 table or require `RunExpectancyMatrix.fit`, not chosen now because both change behaviour for little risk reduction on 24 published numbers; revisit if FanGraphs objects.
- Mark local-only tests with an explicit pytest marker instead of detecting missing files, not chosen now because detection needs no edits to the 30 affected modules; revisit if the count of uncollected modules grows (the run summary prints it).

## Consequences
Breaking (2.0.0): `bundled_constants` is now `constants_table`; `download_register`, `update_register`, `UpdateResult`, `download_lahman` and `$SABERMETRICSPY_AUTO_UPDATE` are removed; seasons missing from a constants table raise instead of warning. Quickstart code needs one setup line (`sp.use_guts(...)`). ADR-0066 is implemented and ADR-0067 is superseded in part (no downloader).
