# ADR-0058: A Multi-Source Name Register With Visible Conflicts

Status: Accepted

## Context
`sabermetricspy.ids` (ADR-0054) matched names only against the Chadwick `people` shards. The register's alternate names
(`names.csv`, 1,346 rows), its nickname and matrilineal-name columns, and Retrosheet's own biographical file were unused, so
a caller holding an old alias, a nickname or a Retrosheet spelling could not find the player. The sources also disagree.

## Decision
Add `sabermetricspy.ids.names` (OpenSpec change `add-player-name-register`). One long table of names, one row per
(person, source, name type): Chadwick people (common, given, nickname, matrilineal), Chadwick `names.csv` (alias, birth,
alt-spelling, legal, anglicized, with dates; parts the alternate name leaves blank are the person's own), and Retrosheet
`biofile0.csv` (common, full, birth, alias), joined to Chadwick through `key_retro`. Sources are never merged. A separate
conflicts table lists, for people in both sources, birth dates (compared by component, partial dates such as `19010000`
compared only where both have a component), last names after normalization, first names (the Retrosheet use-name against
Chadwick's first, given and nickname), and first major-league year against debut year, each with both values. People a source
knows only by last name (1,196 in Retrosheet) go in `last_name_only`, not dropped. Chadwick `key_person`, which the register
says can be reused, is checked: rows whose `key_person` matches no person or several are listed in `unresolved`.
Retrosheet's file is the official `biofile.zip` from retrosheet.org, supplied by the caller by path (zip, `biofile0.csv` or
folder); the library records its SHA-256. It does not download it, because the direct address was not confirmed (retrosheet.org
refused connections from the development machine) and a guessed address would be fragile.

Measured on the files of 2026-10-20 (Chadwick master; a copy of `biofile0.csv` from the Chadwick Bureau's Retrosheet mirror, commit
118094bb, used only to develop and measure; not yet re-measured on a file downloaded from retrosheet.org): 756,290 name rows in 8.5 s; conflicts: 291
birth dates (including month/day swaps such as 1973-11-08 against 1973-08-11), 298 first names, 46 last names with accents
ignored, 606 first years against debut year; one `names.csv` row with no person. These are bounds in an opt-in test, not
pinned values, because the register changes weekly. Matching is exact on normalized names, so "Henry Aaron" does not find
"Henry Louis Aaron" (his given name); the caller can search the given name, as Chadwick lists it.

Alternatives considered: (a) a wide table with one column per source, not chosen now because adding a source changes the
schema; revisit if only these two sources are ever used. (b) Prefer one source's value for each field, not chosen now
because the review found real disagreements (swapped month and day) that a silent choice would hide; revisit if users want
a documented "best" value with the conflict still listed. (c) Fuzzy or first-name-prefix matching, not chosen now because it
returns wrong people silently; revisit with a reported similarity score. (d) Download `biofile.zip` automatically or read the Chadwick mirror, not chosen now because the official address
was not confirmed and a third-party mirror is not the source of record; revisit once the address is confirmed against the
biofile page, with a hash check of the extracted file.

## Consequences
Name search finds nicknames, aliases, birth names and either source's spelling, once per person, with the sources that
matched. Disagreements between the sources are data the library reports. Open: read the official `biofile.zip` and the
notice at retrosheet.org and re-measure the counts above on it.
