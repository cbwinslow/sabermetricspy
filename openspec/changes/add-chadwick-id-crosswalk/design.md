# Design

## Context

The Chadwick Register (`github.com/chadwickbureau/register`, read 2026-10-20) publishes people as 16 shards,
`data/people-0.csv` to `data/people-f.csv`, plus a new and incomplete `names.csv`. `key_uuid` is the primary key and is
never reused; `key_person` is its first eight hex digits and can be reused over time; `key_mlbam`, `key_retro`,
`key_bbref`, `key_bbref_minors`, `key_fangraphs`, `key_npb` and `key_wikidata` are the id systems. The data is ODC-BY 1.0
and the public version is updated about weekly. `baseballr` ships `chadwick_player_lu()` (MIT) and `pybaseball`
`playerid_lookup()` (MIT) over the same data. The library already depends on narwhals for dataframe-agnostic work and on
polars for internal frames (`schema.to_polars_df`).

## Goals / Non-Goals

**Goals:**
- Id translation and name lookup that behave identically on Polars, pandas, PyArrow and DuckDB frames.
- Failures that are loud: duplicates and ambiguous names raise or are listed, never silently resolved.
- Reproducible joins: results record which register release produced them.

**Non-Goals:**
- Scraping or syncing other sources (MLB Stats API, FanGraphs, Baseball-Reference) for ids; the register is the authority.
- Fuzzy or phonetic name matching; exact match after normalization only.
- Bundling a register snapshot or auto-updating in the background.
- Rewriting presets to translate ids implicitly.

## Decisions

1. **Not bundled; path or explicit download.** The register is large (16 shards) and weekly, a bundled copy would be stale
   at release, and the license wants attribution that is simpler when the user fetches it. A `download` call writes the
   shards to a user cache directory and records the fetch date; every other call takes a path or the cached copy.
   Alternative: bundle a snapshot, not chosen now because it ages and inflates the wheel; revisit if offline-first users
   ask for a pinned release.
2. **Download with the standard library.** `urllib` against the raw GitHub URLs, so no new dependency. Alternative: add
   `httpx`/`requests`, not chosen now because one GET per shard does not need it; revisit if retries or caching headers
   become necessary.
3. **Join through narwhals.** Convert the register to a narwhals frame, left-join onto the caller's frame by the source id,
   and restore row order with a temporary row index. This keeps one code path across backends (Rule 2 applies to metrics;
   the same vectorized style is used here). Alternative: convert everything to Polars and back, not chosen now because
   narwhals already handles the round trip for the engine.
4. **Duplicates checked before the join.** Group the register by the source id and raise if any id seen in the caller's
   frame maps to more than one `key_uuid`. Alternative: pick the most recent player, not chosen now because it hides real
   data errors; revisit if the register documents a tiebreak rule.
5. **Name normalization is a small pure function** using `unicodedata` NFKD with combining marks removed, casefold, strip
   punctuation, collapse spaces, and drop a trailing generational suffix token. Alternative: `unidecode` or `rapidfuzz`,
   not chosen now because exact normalized matching covers the lookup need without a dependency; revisit if users need
   fuzzy matching.
6. **Types are kept native.** MLBAM and FanGraphs ids load as nullable integers, the others as strings, so a join with a
   Statcast `batter` integer column needs no casting.
7. **Metadata on results.** A small frozen result object carries the translated frame plus source, license, release date
   and unmatched-row count, so attribution and reproducibility travel with the data.

## Risks / Trade-offs

- [Register lags the full data, so recent debutants may be missing] → unmatched rows are counted and reported, never dropped.
- [`names.csv` is documented as very incomplete] → lookup uses the `people` name columns only; alternate names are an
  open question below.
- [A weekly register changes ids over time] → results record the release date; `key_uuid` is the stable key for storage.
- [Shard layout may change] → the loader reads the shard names from one constant and fails with a clear message if a shard
  is absent.
- [Name collisions among players] → ambiguity is surfaced with birth year and active years so the caller can narrow it.

## Open Questions

- Whether to also read `names.csv` for nicknames and alternate spellings once the register marks it complete.
- Whether the release date should come from the repository's latest commit date or a file in the register; the loader
  will use the download date until a published release marker is confirmed.
