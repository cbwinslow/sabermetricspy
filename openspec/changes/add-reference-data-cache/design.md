# Design

## Context

pybaseball (source read 2026-10-20) fetches each dataset with a plain `requests.get` to the host that serves it, caches opt-in
per function, and has no versioning or freshness logic. Its Chadwick copy comes from the repository's `master.zip`; its
Retrosheet data from the Chadwick Bureau's `retrosheet` repository. Only Baseball-Reference needs a browser-like client.
retrosheet.org itself did not accept connections from the development machine (TCP timeouts on 80 and 443 while GitHub and
Baseball-Reference answered in 0.2 s), so a header or client change cannot fix it; the owner's browser reaches it, which points
at the network path from this machine.

Measured 2026-10-20: Chadwick `register` last commit 2026-10-02 (public updates about monthly since May 2026); Chadwick
`retrosheet` branch `official` last commit 2026-08-12, `reference/` holds `biofile.csv`, `biofile0.csv`, `coaches.csv`,
`ejections.csv`, `relatives.csv`, `teams.csv`, `ballparks.csv`; biofile0 reaches the 2025 season. The MLB Stats API answers for
`/teams?sportId=1` (id, name, abbreviation, league, division), `/teams/{id}/roster`, `/people/{id}` (full, use, middle and
nick names, birth data, handedness, debut) and `/sports/1/players?season=`.

## Decisions

1. **One layer, many sources.** A `Source` describes a dataset: name, base URL(s), file list, how to learn the current version,
   license text, maximum age, and whether it needs accepted terms. Chadwick people, Chadwick names/links, Retrosheet reference
   files, and MLB API calls are all `Source`s; none has its own download code.
2. **Pin by version, publish atomically.** A download resolves the version first (for GitHub: `GET /repos/{r}/commits/{ref}` with
   `Accept: application/vnd.github.sha`; unauthenticated 60/hour, `GITHUB_TOKEN` raises it), then fetches every file at that
   SHA from `raw.githubusercontent.com/{r}/{sha}/…` into `<cache>/<source>/.tmp-<uuid>/`, hashes them, writes the manifest, and
   `os.replace`s the folder to `<cache>/<source>/<version>/`; `current.json` is replaced the same way. A `filelock` file guards
   the sequence. Only the two newest versions are kept.
3. **Cache location** by `platformdirs.user_cache_dir("sabermetricspy")`, overridable by argument or
   `SABERMETRICSPY_CACHE`. The old `~/.cache/...` folder is read as a fallback copy source but never written.
4. **Failure behavior is a contract**, not best effort: stale snapshot plus `StaleDataWarning`, or `SourceUnavailableError`.
   No automatic switch between sources; the caller lists sources in order and sees which was used.
5. **Strict, complete parsing.** Parsed with Polars `infer_schema=False` then cast column by column with `strict=True`; unknown
   columns stay (as text) and appear in the dictionary as undocumented. Parquet (zstd) sits beside the raw files, keyed by the
   snapshot version, and is rebuilt whenever the raw hash differs.
6. **MLB Stats API source** uses `urllib` with the same politeness rules (User-Agent naming the library and version, 1-2 requests
   per second, bounded concurrency of one, retry on 429/5xx with backoff), requires `accept_mlbam_terms=True`, stores the
   response bodies as snapshots (version = fetch time), and attaches MLBAM's copyright text to results. It is fetched on the
   caller's machine at the caller's request and never bundled. Existing wrappers were considered: `MLB-StatsAPI` is GPL-3
   (would impose its license on this package), `python-mlb-statsapi` is MIT but brings a large model layer for three endpoints.
7. **Dependencies**: `platformdirs` and `filelock` (small, widely used). HTTP stays on the standard library, so no new network
   stack and no browser impersonation.
8. **Tests** run a `http.server` fixture serving a fake GitHub (commits endpoint, raw files, ETags, 304, 429, truncation, a
   version change mid-download) and a fake MLB API; live tests are marked and skipped unless `SABERMETRICSPY_LIVE=1`.

## Risks and open items

- The MLBAM terms (individual, non-commercial, non-bulk use) restrict what users may do with the data; the opt-in flag and the
  notice record that, and `record-data-terms` documents it. Whether a commercial user may use the API is theirs to settle.
- retrosheet.org direct download stays out until its file address is confirmed from a machine that can reach it; the
  Chadwick-hosted copy (branch `official`, pinned commit, labelled as a copy of Retrosheet's release) and caller-supplied files
  are the sources until then. This supersedes the "no mirror" position of ADR-0058 alternative (d).
- GitHub's unauthenticated limit is shared by the whole machine; the cache honors `X-RateLimit-Remaining` and uses `GITHUB_TOKEN`.
