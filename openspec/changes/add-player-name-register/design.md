# Design

## Context

`sabermetricspy.ids` (ADR-0054, ADR-0055) loads the Chadwick `people-*.csv` shards and matches normalized first, given and
last names. The proposal lists the other source files and the measured disagreements. Retrosheet's biographical files
were read from Chadwick's mirror during review; they must be re-read at Retrosheet (or its terms confirmed) before
implementation.

## Goals / Non-Goals

**Goals:** a long, source-labelled name table; search across all names; a conflicts report; credit and provenance on every
result; the same backend-independence tests as `ids`.
**Non-Goals:** fuzzy matching; choosing a "true" birth date or spelling; scraping websites; bundling data; rosters-by-season
(Retrosheet `.ROS` files) in the first version.

## Decisions

1. **Long table, not a wide merge.** One row per (person, source, name type, name). Merging by field would force a choice
   between sources; a long table keeps both and lets the conflicts report be a query. Alternative: one wide row per person
   with a column per source, not chosen now because adding a source changes the schema; revisit if only two sources are
   ever used.
2. **Person key is `key_uuid`.** Chadwick `names.csv` and `links.csv` key on `key_person`, which the register says can be
   reused over time, so each join to `key_uuid` is checked: a `key_person` that maps to several `key_uuid` values is
   reported and skipped. Retrosheet rows join through `key_retro`; unmatched Retrosheet ids are kept with a null person.
3. **Normalization is the existing `normalize_name`**, so lookups agree with `find_players`.
4. **Conflicts are computed, not stored:** a function compares paired rows after normalization and returns a table of
   (person, field, value A, source A, value B, source B). Dates are compared as dates, spellings after normalization,
   first major-league year against the year of the debut date, noting the register may count other leagues.
5. **Provenance is explicit.** Each source file records its commit or fetch date, as in `download_register`.
6. **Dependencies:** none new. Reading CSV with Polars, as the crosswalk does.

## Risks / Trade-offs

- [Retrosheet terms could not be read at source] -> read them first; if the terms differ from the notice statement
  already in `docs/CREDITS.md`, change the credit before shipping.
- [`names.csv` is documented as very incomplete] -> rows are labelled with their source, and the docs say coverage is partial.
- [Large tables] -> build once, cache by file state as `load_register` does.

## Open Questions

- Whether Retrosheet season rosters should join later as a source of per-season names and teams.
- Whether `find_players` should switch to the name register by default once it exists.
