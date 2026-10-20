# Design

## Context

See proposal.md. The reviews' scripts and sources are in the session scratchpad; each bug listed in the proposal was
reproduced before it was put in scope.

## Goals / Non-Goals

**Goals:** no behavior that works on Polars may crash or change meaning on DuckDB, pandas or PyArrow; documentation
claims no stronger than what CI checks; invalid input fails with a message.
**Non-Goals:** the multi-source player name register (Chadwick `names.csv`, `links.csv`, Retrosheet biofile), proposed
separately as `add-player-name-register`; a second Tango win expectancy golden (`we.html`, 2010 to 2015), recorded as a
follow-up.

## Decisions

1. **Season detection reads `min` and `max` and the dtype, not `drop_nulls().n_unique()`.** `min`/`max`/`null_count`
   aggregates exist on every narwhals backend; a column is a year column only when its dtype is integer (floats with
   integral values are cast). One season means `min == max`; several means `min != max`; the all-null case has no min.
2. **`translate_ids` computes the new column in Polars from the key column only, then attaches it to the caller's native
   frame.** pandas: copy and assign an array (no index alignment); PyArrow: `append_column`; DuckDB: Arrow round trip to
   a relation (the library's convention for DuckDB output); LazyFrame: collect, attach, `.lazy()`. Other columns are never
   converted, so dtypes and index survive. Alternative: narwhals join on the native frame, not chosen now because a DuckDB
   join needs the lookup on the same connection; revisit if narwhals gains cross-backend joins.
3. **Exact ids.** Floats are accepted only when integral; strings are stripped. Anything else is unmatched.
4. **Transliteration table, not a new dependency, for now.** A table for the few Latin letters that do not decompose
   covers the register's Latin names; `anyascii` would cover everything. Alternative: add `anyascii`, not chosen now
   because the table fixes the reviewed cases without a dependency (CLAUDE.md rule 6 considered); revisit when
   non-Latin scripts matter, as the register holds NPB names.
5. **Cache key = resolved path plus each shard's size and modification time.** Alternative: no cache, not chosen now
   because a 527k-row parse takes seconds per call; revisit if parsing becomes cheap.
6. **Provenance = commit SHA from the GitHub API plus the fetch date.** Downloads read from the commit, not `master`.
   If the API is unreachable the download falls back to the ref with an unknown commit and warns.
7. **Validation is one vectorized pass** (`is_in`, `is_between`, `null_count`) that raises on the first failing rule with
   the offending values; the chain checks reachability to the absorbing state before inverting.
8. **Evidence tier rule:** a method is `matches` only when its outside-value check runs in CI; checks that run only when
   a data file is supplied cap the tier at `approximate`. CI downloads the CC0 `retro2016.rda` so those checks run.

## Risks / Trade-offs

- [Raising on invalid input may break callers who passed sloppy data] -> messages name the fix; the library is pre-release.
- [CI now needs a network download of a 2.8 MB file] -> the CI step is the only place it is needed; local runs stay offline.
- [Transliteration table is incomplete] -> a test lists the covered letters; additions are one-line changes.
