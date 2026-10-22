# ADR-0066: FanGraphs Data Terms and the Bundled Constants

Status: Proposed

## Context
The package bundles seasonal constants taken from FanGraphs (Guts! and leaderboard values) and the repository holds recorded leaderboard rows for tests. FanGraphs' Terms of Service (read 2026-10-21) state that the site is protected as a collective work or compilation (section 8), forbid unauthorized reproduction, publication or further distribution of its materials (section 6) and reproducing, reselling or exploiting content for commercial purposes (section 11), and grant a personal licence to use the service. They do not mention scraping or give any data licence. Its credits page says its run expectancy data is licensed from Tango. No permission has been asked for.

## Decision
Until the owner decides, keep attribution and the retrieval date on every constant, state the terms in `docs/CREDITS.md`, and do not describe the constants as the project's own data. The decision between the options below is the owner's and has not been taken.

## Alternatives
- Ship as is with attribution, not chosen now because the terms bar redistribution of compiled content and the project has no permission; revisit if FanGraphs grants permission or counsel advises the numbers are uncopyrightable facts.
- Ask FanGraphs for written permission to bundle the constants and keep the leaderboard samples in tests, not chosen now only because it needs the owner to write to them; revisit as the first step.
- Stop bundling FanGraphs values and have a `tools/` script fetch them into the user's cache, not chosen now because it breaks offline use and the zero-setup quickstart; revisit if permission is refused.
- Recompute the constants from public play-by-play with Tango's published methods, not chosen now because it is large work and the MLB and Retrosheet data carry their own terms; revisit if both other routes fail.
- Cut the test fixtures to small samples (a few dozen rows each), not chosen now because it weakens the tie-outs (833 batters, 2,005 pitchers, 1,477 pitcher WAR rows); revisit if permission is refused.

## Consequences
None in code. The risk is stated openly in the credits and in this record.
