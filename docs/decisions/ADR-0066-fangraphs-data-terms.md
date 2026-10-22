# ADR-0066: FanGraphs Data Terms and the Bundled Constants

Status: Accepted; implemented in 2.0.0 by ADR-0068

## Context
The package bundles seasonal constants taken from FanGraphs (Guts! and leaderboard values) and the repository holds recorded leaderboard rows for tests. FanGraphs' Terms of Service (read 2026-10-21) state that the site is protected as a collective work or compilation (section 8), forbid unauthorized reproduction, publication or further distribution of its materials (section 6) and reproducing, reselling or exploiting content for commercial purposes (section 11), and grant a personal licence to use the service. They do not mention scraping or give any data licence. Its credits page says its run expectancy data is licensed from Tango. No permission has been asked for.

## Decision
The owner decided on 2026-10-22 not to ask FanGraphs and not to redistribute its values: the library will build its seasonal constants itself from open data, and FanGraphs numbers stay only as outside values that tests compare against. Nothing has been published to PyPI, so no release has carried the FanGraphs constants. Until the open-data builder replaces the bundled files, the package is not published.

Measured on 2026-10-22 against the bundled FanGraphs values, 2010 to 2025:
- From Lahman team totals alone (CC BY-SA 3.0): cFIP is within 0.001, league runs per PA within 0.001, and league ERA, OBP, SLG and the WAR league totals are plain sums, so these are clean and exact.
- wOBA weights are not derivable from team totals: BaseRuns marginal values are 0.03 to 0.29 off, and five-year team regressions 0.07 to 1.1 off. They need play-by-play run expectancy by season.
- SIERA constants need league ground-ball and fly-ball counts, which Lahman lacks; park factors need home and road splits, which Lahman lacks (its own BPF and PPF are different numbers).

## Alternatives
- Ship as is with attribution, not chosen now because the terms bar redistribution of compiled content and the project has no permission; revisit if FanGraphs grants permission or counsel advises the numbers are uncopyrightable facts.
- Ask FanGraphs for written permission to bundle the constants, not chosen now because the owner prefers not to contact them; revisit if the owner changes their mind.
- Fetch FanGraphs values into the user's cache at install, not chosen now because it still automates access to their site against the spirit of their terms; revisit only with their permission.
- (Chosen direction) Recompute the constants from open data with Tango's published methods; the remaining question is the play-by-play source for run values, since MLB and Retrosheet data carry their own terms.
- Cut the test fixtures to small samples (a few dozen rows each), likely part of the chosen direction, not done yet because it weakens the tie-outs (833 batters, 2,005 pitchers, 1,477 pitcher WAR rows); revisit when the builder exists.

## Consequences
Implemented in 2.0.0 (ADR-0068): the package ships no FanGraphs-derived tables and the large leaderboard fixtures are no longer tracked. The earlier tables remain in git history, which the owner chose not to rewrite.
