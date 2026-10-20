# ADR-0055: Harden the Season Check, Id Crosswalk and Fits After Independent Review

Status: Accepted

## Context
Two independent reviews (both run by an Opus model on 2026-10-20) checked the work of ADR-0051 to ADR-0054. Bugs
reproduced by running code: every engine call on a DuckDB relation crashed (the season check used an expression DuckDB
lacks, and the tests were Polars-only); a text season column crashed even AVG; `translate_ids` reset a pandas index,
turned ids into floats, returned Arrow for a LazyFrame, deleted a caller column named `__key`, truncated 100.7 to 100,
matched people with empty names for a non-Latin query, and returned a stale register for a changed or relative path. The
fits accepted invalid input and failed with `KeyError` or `LinAlgError`. Statements that were wrong: Walsh's first name
(John), linear weights credited to Tango (Palmer), win expectancy called "the construction behind Tango's table" (his
2002 page states no method), the cause of a plate-appearance gap, "release date" for a download date, the Bukiet paper
presented as a source although it was not read, and win-expectancy figures taken from a fixture that counted
non-plate-appearance events. The Retrosheet checks ran only when a data file was supplied, so CI never ran them.

## Decision
Implement OpenSpec change `harden-after-opus-review`:
- Season detection reads `min`, `max` and the dtype, which every backend supports; text that is not a year, dates and
  all-null columns are "no usable season"; the warning points at the caller's code; `WARFramework` warns when it has
  neither a context nor a season.
- `translate_ids` computes the new column from the key column alone and attaches it to the caller's native frame, so
  pandas keeps its index and dtypes, a LazyFrame stays lazy, and no caller column can collide with a helper name. Ids
  match exactly. Names fold letters Unicode cannot decompose, any whitespace separates parts, and a query that
  normalizes to nothing raises. The register cache is keyed by resolved path and each file's size and modification
  time. Downloads are pinned to a commit and record it with the fetch date.
- `WinExpectancyMatrix.fit`, `MarkovChainModel.fit_transitions` and `state_distribution` validate input and name the
  problem; states that cannot reach three outs are named before the matrix is inverted.
- Evidence tiers follow one rule: `matches` needs an outside-value check that runs in CI. CI now downloads the CC0
  `retro2016.rda` and the Chadwick Register and runs those checks on one Python version, and `fit_transitions` is
  `approximate` until that run has passed. Quoted figures are pinned by tests: 2,427 games, 184,541 plate appearances,
  16 cells with 30 or more games within 3 standard errors (largest 2.11), 6 cells with 100 or more within 1.7.
- Printed-value tolerances equal half a unit of the book's last printed digit.
- Benchmarks are registered for the three new subsystems (CLAUDE.md rule 4).

Alternatives considered: (a) add `anyascii` for transliteration, not chosen now because a small table fixes the
reviewed letters without a dependency; revisit when non-Latin scripts matter (the register holds NPB names). (b) Join
through narwhals on the caller's frame, not chosen now because a DuckDB join needs both tables on one connection;
revisit if narwhals offers cross-backend joins. (c) Remove the `fit()` event-probability Markov model, not chosen now
because it serves callers without play-by-play; revisit if a published advancement model replaces its rules. (d) Keep
`fit_transitions` as `matches` on the strength of the local opt-in run, not chosen now because the rule that
opt-in checks cap the tier applies to every model alike; revisit after the CI step has passed.

## Consequences
DuckDB, pandas, PyArrow and LazyFrame inputs are covered by tests for every new public function. Callers who passed
sloppy data to the fits now get errors that say what to fix. `release` on results is replaced by `fetched_on` and
`commit`. Follow-ups, not done here: a second win-expectancy reference (`tangotiger.net/we.html`, 2010 to 2015); the
multi-source player name register (`add-player-name-register`); separating the effect of each rule in the
event-probability Markov model.
