# Proposal

## Why

Player, team and division names change often, and the library must be able to fetch the sources behind them at any time,
keep them on disk, and use them offline. Today `download_register` and `download_name_sources` write straight over the
final files (a failed download can leave files from two Chadwick versions labelled with one commit), silently fall back to
an unpinned download when the commit lookup fails, cannot tell whether the data is stale, and the cache path is not the
Windows convention. Retrosheet's file is supplied by hand, and MLB's own teams, divisions and rosters are not available at
all. One download-and-cache layer, used by every reference source, replaces these one-off functions.

## What Changes

- Add `sabermetricspy.fetch`: a reference-data cache. A *source* names a dataset (Chadwick Register, Retrosheet biographical
  and team files, MLB Stats API teams/divisions/rosters/people), where it comes from, its license or notice, and its refresh
  policy.
- Snapshots are pinned to a version (a Git commit SHA for GitHub sources, a request timestamp for the API source) and stored
  with a manifest: source, URL, version, SHA-256 per file, ETag, fetched-at, checked-at, license text.
- Publishing a snapshot is atomic (download into a temporary folder, verify, then rename into place) under a file lock, so a
  reader never sees a partial or mixed snapshot. The last two snapshots are kept.
- A cheap freshness check (one GitHub commits request carrying the SHA media type, or a conditional request with `If-None-Match`)
  decides whether anything must be downloaded. Refresh policy is `auto` (check when older than the source's maximum age;
  Chadwick one day, Retrosheet 30 days), `always`, or `never`.
- When the network or the version lookup fails, the last good snapshot is used with a `StaleDataWarning` and a `stale` flag
  in the provenance; with no snapshot an explicit `SourceUnavailableError` is raised. Sources are explicit and ordered by the
  caller; the cache never switches source silently.
- Every column of every file is kept, with its source name, a column dictionary (name, source file, meaning where the source
  documents it), and strict typing: a value that cannot be parsed raises with the file, row and column instead of becoming a
  null. Identifier columns stay text. Parsed tables are cached as Parquet next to the raw snapshot so opening is fast.
- The MLB Stats API source is opt-in (`accept_mlbam_terms=True`), shows MLBAM's notice in results, is fetched from the
  caller's machine at the caller's request, is never bundled, and is requested politely (identifying User-Agent, bounded
  request rate). It uses our own small client, not a GPL wrapper library.
- `download_register` and `download_name_sources` become deprecated wrappers over the new layer.
- No network in the default test run: tests use a local HTTP server; live tests run only with `SABERMETRICSPY_LIVE=1`.

Follow-on changes, each its own OpenSpec change: `refresh-chadwick-register`, `add-retrosheet-reference-sources`,
`add-people-attributes`, `add-full-crosswalk`, `add-attach-people`, `add-mlb-stats-api-source`, `record-data-terms`.

## Capabilities

### New Capabilities
- `reference-data-cache`: fetching, versioning, verifying, caching and refreshing external reference datasets with
  provenance, freshness and failure behavior defined for every source.

### Modified Capabilities
- `player-id-crosswalk`: downloading the register goes through the reference-data cache (atomic, pinned, freshness-aware);
  the public loading and translation behavior is unchanged.

## Impact

New package `src/sabermetricspy/fetch/`; `ids/__init__.py` and `ids/names.py` call it instead of their own download code;
new runtime dependencies `platformdirs` (cache location per operating system) and `filelock` (cross-process lock); tests
with a local HTTP server; ADR-0059; `docs/CREDITS.md` and `README.md` updated. No change to metric calculations. Facts
(update cadence of the Chadwick Register, GitHub rate limits, API behavior) were measured on 2026-10-20 and are re-checked
by the live tests. Data terms: Chadwick Register ODC-BY 1.0; Retrosheet notice; MLBAM terms permit only individual,
non-commercial, non-bulk use, which is why that source is opt-in, local and never redistributed.
