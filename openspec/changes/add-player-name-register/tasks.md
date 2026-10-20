# Tasks

## 1. Sources

- [ ] 1.1 Read the official Retrosheet `biofile.zip` and the notice at retrosheet.org, and re-measure the counts in ADR-0058 on that file. Retrosheet's site refused connections from the development machine on 2026-10-20 (TCP timeout on ports 80 and 443; the fetch tool was refused too); page content and terms were obtained only as web-search summaries, and the column list from a mirror copy. Needs the file downloaded by the user. Verify: the columns equal the official file's header row, and the notice text in `docs/CREDITS.md` matches Retrosheet's page.
- [x] 1.2 Loader and downloader for the new files, pinned to a commit like `download_register`. Verify: tests with hand-built fixtures and a pinned two-commit download.

## 2. Name table

- [x] 2.1 Build the long name table from Chadwick people, `names.csv` and Retrosheet, with source, type, normalized form and dates; guard `key_person` reuse. Verify: a fixture test for each name type and a test that a reused `key_person` is reported.
- [x] 2.2 Name search returning each person once with matching names and sources; ambiguity raises. Verify: nickname, alias, accent and ambiguity tests on Polars, pandas, PyArrow and DuckDB inputs where frames are involved.

## 3. Conflicts

- [x] 3.1 Conflicts report for birth date, normalized spelling and first-year versus debut date. Verify: fixtures with one difference of each kind and an accent-only difference that is not reported.
- [x] 3.2 Opt-in test on the real files that reproduces the review's counts (matched people, differing birth dates, names, first years) and prints them. Verify: the test passes with the files present; CI step added.

## 4. Documentation and records

- [x] 4.1 Credits, NOTICE, README section, ADR with Alternatives, changelog, benchmark, `@profiled`. Verify: `openspec validate --all`, full test suite, ruff, pyright.
