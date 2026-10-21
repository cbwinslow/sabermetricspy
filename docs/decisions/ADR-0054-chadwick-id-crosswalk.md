# ADR-0054: Player Ids Are Translated Through the Chadwick Register

Status: Accepted

## Context
Retrosheet, Statcast, Baseball-Reference, FanGraphs and Lahman each name players differently, so frames from different
sources cannot be joined without a mapping. The Chadwick Bureau Register is the published authority file that links
the ids (`key_mlbam`, `key_retro`, `key_bbref`, `key_fangraphs`, and others); `baseballr` and `pybaseball` both expose it.
It is split into 16 shards of about 4 MB (526,894 people on 2026-10-20), updated about weekly, and licensed ODC-BY 1.0.

## Decision
Add `sabermetricspy.ids` with `load_register`, `download_register`, `translate_ids`, `find_players`, `player_id` and
`normalize_name`. The register is loaded from a path or downloaded to a user cache on request and is never bundled.
Translation keeps every row and order, works on Polars, pandas, PyArrow and DuckDB inputs, nulls and counts ids it cannot
map, and raises when an id in the frame belongs to more than one person. Names match exactly after accent folding, case
folding, punctuation removal and dropping generational suffixes; several matches are listed and a single-id request raises.
Results carry the register's source, license, the commit it was downloaded from and the fetch date (ADR-0055 replaced
the earlier "release date", which was only the download date).

Validation (opt-in test against the downloaded register): Mike Trout and Tarik Skubal ids equal those on their Savant,
Baseball-Reference and FanGraphs pages, and all 184,580 batting events in the Retrosheet 2016 file map to an MLBAM id,
with Trout's 681 plate appearances equal to his Baseball-Reference 2016 line. Retrosheet's own site was unreachable
during the check, so the Retrosheet id is confirmed through the plate-appearance count instead.

Alternatives considered: (a) bundle a register snapshot, not chosen now because it is about 68 MB, ages weekly and ties
the license notice to every install; revisit if offline-first users ask for a pinned release. (b) Use an HTTP client
dependency for downloads, not chosen now because one GET per shard needs only the standard library; revisit if retries or
conditional requests become necessary. (c) Fuzzy or phonetic name matching, not chosen now because exact normalized
matching with a list of candidates avoids silent wrong joins; revisit if users need typo tolerance, with a similarity
threshold reported in the result. (d) Take the first or most recent person on a shared id, not chosen now because a shared
id is a data error that should be seen; revisit if the register documents a tiebreak rule.

## Consequences
Cross-source joins are one call. Only the `people-*.csv` shards are read. Not read: `names.csv` (1,346 rows of alternate
names keyed by `key_person`: 643 aliases, 260 birth names, 251 alternate spellings, 191 legal names and 1 anglicized, with
language and date range; the register calls it new and very incomplete), `links.csv` (`key_person, source, value`; 21,650
`tsncards` and 5,682 `findagrave` rows), and `countries.csv` (a code table with no person key). The people files'
`name_matrilineal` and `name_nick` columns are also not searched. A multi-source name register that adds these and the
Retrosheet biofile is proposed separately (`add-player-name-register`, later reverted as ADR-0058). The register has git history, so downloads are
pinned to a commit (ADR-0055).

## Update (v1 scope): keeping the register current
The register changes about weekly, so a one-time download goes stale and new players stop matching. v1 adds
`update_register()`: it looks up the latest upstream commit, compares it with the commit recorded in `provenance.json`,
and re-downloads only when they differ or `force=True`. Downloads go to a scratch directory and replace the old shards
only after every shard arrived, so a failure never leaves a mixed register. If the upstream commit cannot be looked up
it raises `ConnectionError` instead of assuming the cache is current. `load_register` warns when the files are more than
90 days old. Nothing fetches implicitly; the network is touched only by `download_register` and `update_register`
(ADR-0003 holds for all calculations).

Alternatives: (a) auto-refresh inside `load_register`, not chosen now because a calculation call should not make network
requests or change results between runs; revisit if users ask for an opt-in flag. (b) A background scheduler, not chosen
now because scheduling belongs to the caller's pipeline (cron, Airflow); revisit never unless retrosheetpy takes it on.
(c) Bundling a snapshot, see above.
