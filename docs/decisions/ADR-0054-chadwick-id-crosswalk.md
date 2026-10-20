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
Results carry the register's source, license and release date.

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
Cross-source joins are one call. The register's release date is recorded, but the register carries no version marker, so
the date is the download date. `names.csv` (alternate spellings) is not read because the register calls it very incomplete.
