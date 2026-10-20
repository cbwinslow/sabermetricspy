# Tasks

## 1. Register loader

- [x] 1.1 Read the register's current README and one shard header, record the exact column names and shard URLs in `docs/LITERATURE.md`. Verify: the recorded columns equal the header row of `people-0.csv`.
- [x] 1.2 Implement `load_register(path)` and `download_register(dest)` in `src/sabermetricspy/ids/`, with typed id columns (integer MLBAM/FanGraphs, string others) and the standard-library download. Verify: `tests/test_ids_register.py` loads a hand-built two-shard fixture and checks column types and that a missing shard raises with the shard name.
- [x] 1.3 Decorate loader and translation entry points with `@profiled(category=...)` per CLAUDE.md rule 4. Verify: a telemetry test sees the profiled calls.

## 2. Id translation

- [x] 2.1 Implement `translate_ids(df, source, target)` through narwhals, preserving row order and native type, adding the target column. Verify: a parametrized test over Polars, pandas, PyArrow and DuckDB gives identical results on a 1,000-row frame with repeated ids.
- [x] 2.2 Report unmatched rows and raise on source ids that map to several people. Verify: tests for a missing id (null plus the unmatched count) and for a duplicated `key_bbref` (error names the id and both people).
- [x] 2.3 Attach source, license, release date and unmatched count to a frozen result object. Verify: a test asserts the metadata fields and the license string.

## 3. Name lookup

- [x] 3.1 Implement `normalize_name` (accent folding, case folding, punctuation, suffix removal). Verify: unit tests for accented names, "Jr." and "III" suffixes, hyphens and apostrophes.
- [x] 3.2 Implement `find_players(first, last, birth_year=None, season=None)` returning every match with ids and playing years, and `player_id(...)` that raises on none or several. Verify: tests for exact, accented, ambiguous (candidates listed) and no-match cases.

## 4. Validation against published ids

- [x] 4.1 Add an opt-in test (environment variable pointing at a downloaded register) that checks a handful of well-known players' ids across `retro`, `mlbam`, `bbref` and `fangraphs` against the values on their Baseball-Reference and FanGraphs pages, read during the task and cited in the test. Verify: the opt-in test passes against a current register.
- [x] 4.2 Opt-in test that joins the Retrosheet 2016 batters in `retro2016.rda` to MLBAM ids and reports the unmatched share. Verify: the share is printed and bounded in the test.

## 5. Documentation and records

- [x] 5.1 Add the Chadwick Bureau, license and release date to `docs/CREDITS.md` and `NOTICE`, and document usage in the README. Verify: `tests/test_literature_catalogue.py` and the docs links still pass.
- [x] 5.2 Add the ADR with an Alternatives section (bundling a snapshot, a third-party HTTP client, fuzzy matching, each "not chosen now, revisit if"), update `docs/DECISIONS.md` and the changelog. Verify: `openspec validate --all`, `uv run pytest`, `uv run ruff check .`, `uv run pyright` all pass.
