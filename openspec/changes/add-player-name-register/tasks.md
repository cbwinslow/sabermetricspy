# Tasks

## 1. Sources

- [ ] 1.1 Read Retrosheet's biographical file documentation and terms at retrosheet.org, and re-read Chadwick `names.csv`, `links.csv` and README. Record exact column names, licenses and notice wording in `docs/LITERATURE.md`. Verify: the recorded columns equal the files' header rows; the notice text in `docs/CREDITS.md` matches Retrosheet's own page.
- [ ] 1.2 Loader and downloader for the new files, pinned to a commit like `download_register`. Verify: tests with hand-built fixtures and a pinned two-commit download.

## 2. Name table

- [ ] 2.1 Build the long name table from Chadwick people, `names.csv` and Retrosheet, with source, type, normalized form and dates; guard `key_person` reuse. Verify: a fixture test for each name type and a test that a reused `key_person` is reported.
- [ ] 2.2 Name search returning each person once with matching names and sources; ambiguity raises. Verify: nickname, alias, accent and ambiguity tests on Polars, pandas, PyArrow and DuckDB inputs where frames are involved.

## 3. Conflicts

- [ ] 3.1 Conflicts report for birth date, normalized spelling and first-year versus debut date. Verify: fixtures with one difference of each kind and an accent-only difference that is not reported.
- [ ] 3.2 Opt-in test on the real files that reproduces the review's counts (matched people, differing birth dates, names, first years) and prints them. Verify: the test passes with the files present; CI step added.

## 4. Documentation and records

- [ ] 4.1 Credits, NOTICE, README section, ADR with Alternatives, changelog, benchmark, `@profiled`. Verify: `openspec validate --all`, full test suite, ruff, pyright.
