# Tasks

## 1. Engine season detection

- [x] 1.1 Replace the season reads in `engine` with `min`/`max`/dtype logic that runs on every backend; treat non-year columns as absent; fix the warning text and `stacklevel`. Verify: `tests/test_multi_season_guard.py` runs the same cases on Polars, LazyFrame, pandas, PyArrow and DuckDB, including text, date and all-null season columns.
- [x] 1.2 `WARFramework` warns when built with no context and no season. Verify: a test for the warning and for its absence when a season or context is given; existing WAR tests pass.

## 2. Player-id crosswalk

- [x] 2.1 Attach the translated column to the caller's native frame (pandas, PyArrow, DuckDB, Polars, LazyFrame) without touching other columns. Verify: tests for index preservation, nullable integers, LazyFrame stays lazy, `__key` and `__row` columns survive.
- [x] 2.2 Exact id matching (integral floats only, trimmed strings). Verify: fractional and padded id tests.
- [x] 2.3 Name normalization: transliteration table, any-whitespace separator, empty-query error, empty-name rows excluded. Verify: tests for the reviewed names (Bjorn, Lukasz, Daehli, Durovic, a non-Latin query, tabs).
- [x] 2.4 Cache keyed by resolved path and shard state. Verify: tests loading "." in two directories and editing a shard.
- [x] 2.5 Download pinned to a commit with fetch date and commit recorded; rename the result field to `fetched_on` and add `commit`. Verify: a test serving two commits from a local directory; attribution test updated.

## 3. Fits

- [ ] 3.1 Validate `WinExpectancyMatrix.fit` input in one pass; correct the docstring on weighting. Verify: one test per rule in the spec.
- [ ] 3.2 Validate `MarkovChainModel.fit_transitions` and `state_distribution`; report trapped states. Verify: tests per rule and a two-state cycle.

## 4. Evidence, CI and benchmarks

- [ ] 4.1 CI downloads `retro2016.rda` and runs the opt-in Retrosheet checks; tighten the printed-value tolerances to the printed precision; fix the Retrosheet win-expectancy fixture to plate appearances only; pin the quoted figures (games used, cell counts, gap numbers) in tests. Verify: the opt-in tests pass locally with the data file.
- [ ] 4.2 Apply the tier rule: `fit_transitions` to `approximate` until CI has run the check. Verify: `tests/test_methodology.py`.
- [ ] 4.3 Add `@register_benchmark` workloads for `translate_ids`, `WinExpectancyMatrix.fit` and `MarkovChainModel.fit_transitions`; add `@profiled` to `player_id`. Verify: the registered benchmarks run in `run_registered_benchmarks`.

## 5. Documentation

- [ ] 5.1 Correct CREDITS (John Walsh; linear weights to Palmer, modern tables and wOBA to Tango; Bukiet claim removed; Lahman holder), add the Retrosheet statement to NOTICE, fix the Bukiet wording in the docstring and methodology note, the win-expectancy "construction behind Tango's table" wording, and the reason for the 4.41 versus 4.27 gap. Verify: grep for the old wording returns nothing.
- [ ] 5.2 ADR-0055 with Alternatives; amend ADR-0051 (Alternatives phrasing), ADR-0052, ADR-0053, ADR-0054 (Chadwick `names.csv`, `links.csv`, `countries.csv` described accurately; fetch date and commit). Verify: `openspec validate --all`, full test suite, ruff, pyright.
- [ ] 5.3 Propose `add-player-name-register` (Chadwick names and links plus Retrosheet biofile) as its own OpenSpec change; do not implement. Verify: `openspec validate add-player-name-register`.
