# Proposal

## Why

Two independent reviews (a code and backend review and a methods, citation and protocol review, both run by an Opus
model on 2026-10-20) checked everything since commit 46cd50f. Findings reproduced by running code: every engine call on
a DuckDB relation crashed because the season check used an expression DuckDB lacks; a non-integer `season` column
crashed even AVG; `translate_ids` reset a pandas index, changed ids to floats, returned Arrow for a LazyFrame, deleted a
caller column named `__key`, truncated float ids, matched people with empty names for non-Latin queries, and kept a
stale register cache. The fits accepted invalid input and failed with bare `KeyError` or `LinAlgError`. Four credit
statements were wrong (Walsh's first name, the origin of linear weights, win expectancy credited as Tango's method, the
reason for a plate-appearance gap) and several evidence claims were stronger than the checks that run in CI.

## What Changes

- Engine season detection works on every backend and ignores season columns it cannot read as years; the warning text is
  accurate for an all-null column; `WARFramework` no longer defaults silently to 2024.
- `translate_ids` returns the caller's own frame with one column added: pandas keeps index and dtypes, LazyFrame stays
  lazy, no temporary column can collide with a caller column, ids must match exactly (no float truncation), and the
  register cache is keyed by resolved path and file state.
- Name matching folds letters Unicode cannot decompose (o with stroke, l with stroke, ae, d with stroke), treats any
  whitespace as a separator, and refuses a query that normalizes to nothing.
- The register records the commit it was downloaded from and the fetch date instead of calling the fetch date a release.
- `WinExpectancyMatrix.fit`, `MarkovChainModel.fit_transitions` and `state_distribution` validate input in one pass and
  raise `ValueError` that names the problem; a chain with states that cannot reach three outs says which.
- Correct the credits, ADR text, methodology notes and licenses; apply one evidence-tier rule (a `matches` claim needs a
  reference check that runs in CI) and make CI run the Retrosheet checks; pin quoted figures in tests.
- Add benchmarks for the new subsystems (CLAUDE.md rule 4) and backend-matrix tests for every new public function.

## Capabilities

### New Capabilities

None.

### Modified Capabilities
- `seasonal-constants`: season detection is backend-independent and robust to non-year columns.
- `player-id-crosswalk`: the caller's frame is preserved, matching is exact, and the register records its commit.
- `fitted-win-expectancy`: input validation.
- `fitted-markov-chain`: input validation and an explicit error for chains that cannot finish.

## Impact

`engine`, `ids`, `expectancy`, `models`, `value` packages; telemetry benchmarks; tests (backend matrix, validation,
pinned figures); CI workflow; `docs/CREDITS.md`, `NOTICE`, ADR-0049/0051/0052/0053/0054 text, ADR-0055,
`docs/METHODOLOGY.md`; no change to metric formulas.
