# Tasks

## 1. Cache core
- [ ] 1.1 Create `sabermetricspy.fetch` with `Source`, `Snapshot`, manifest and `Provenance` types (frozen pydantic), `StaleDataWarning`, `SourceUnavailableError`, `SchemaChangedError`. Verify: unit tests for manifest round-trip and SHA-256 per file.
- [ ] 1.2 HTTP client on `urllib`: User-Agent, timeouts, bounded retry with backoff on 429/5xx/timeouts only, rate-limit header handling, per-host request spacing. Verify: local-server tests for retry count, 429 handling and no retry on 404.
- [ ] 1.3 Version resolution for GitHub sources (commits endpoint with SHA media type, ETag/304, `GITHUB_TOKEN`). Verify: tests for same version, new version, lookup failure.
- [ ] 1.4 Atomic snapshot publish with `filelock`, `current.json`, keep two snapshots, discard on mixed version. Verify: tests for interrupted download, concurrent refresh (two processes), version change mid-download.
- [ ] 1.5 Refresh policies `auto`/`always`/`never` and stale-cache fallback with warning and provenance flag. Verify: offline tests with and without a snapshot, `never` makes no request.
- [ ] 1.6 Strict parser and column dictionary; Parquet parsed cache rebuilt when the raw hash changes. Verify: bad value raises with file/row/column, extra column kept and marked undocumented, id columns remain text.

## 2. Sources
- [ ] 2.1 Chadwick Register source (people shards, names, links, countries) and move `download_register`/`download_name_sources` onto it as deprecated wrappers. Verify: existing ids and name-register tests still pass; no unpinned download when the lookup fails.
- [ ] 2.2 Retrosheet reference source from the Chadwick Bureau `retrosheet` repository, branch `official`, pinned commit, labelled as a copy; caller-supplied file/zip/folder keeps working with SHA-256 recorded. Verify: files `biofile0.csv`, `biofile.csv`, `relatives.csv`, `coaches.csv`, `ejections.csv`, `teams.csv`, `ballparks.csv` all parsed with every column kept; compare with the official `biofile.zip` the owner downloads.
- [ ] 2.3 MLB Stats API source (teams with league and division, rosters, people) with opt-in terms flag, notice in results, polite requests, no bundling. Verify: fake-API tests; without the flag no request is sent.

## 3. Wrap-up
- [ ] 3.1 `@profiled` on fetch/parse methods and `@register_benchmark` for the cache open path. Verify: telemetry test.
- [ ] 3.2 Live tests behind `SABERMETRICSPY_LIVE=1` and a CI step for them. Verify: run once locally, record dates and commits.
- [ ] 3.3 ADR-0059 (with Alternatives), DECISIONS.md row, mark ADR-0058 alternative (d) and ADR-0054 "weekly" wording as superseded, README, CREDITS/NOTICE, CHANGELOG, LITERATURE entries for the new sources and terms. Verify: `openspec validate --all`, ruff, pyright, pytest.
