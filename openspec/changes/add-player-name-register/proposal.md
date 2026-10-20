# Proposal

## Why

`sabermetricspy.ids` reads only the Chadwick Register `people-*.csv` shards, so name lookup misses everything the register
and Retrosheet publish elsewhere: Chadwick `names.csv` (1,346 alternate names: aliases, birth names, alternate spellings,
legal names), the `name_nick` and `name_matrilineal` columns of the people files, `links.csv` (external ids), and
Retrosheet's own biographical files, whose spellings and dates sometimes disagree with Chadwick's. A caller who has a
Retrosheet roster name, a nickname or an old alias cannot find the player. Two independent sources also let the library
flag disagreements instead of hiding them.

## What Changes

- Add a name register: one long table of names, each row carrying its person, source, name type, name parts, normalized
  form and date range, built from Chadwick `people` (`name_first`, `name_given`, `name_nick`, `name_matrilineal`,
  `name_last`, `name_suffix`), Chadwick `names.csv`, and Retrosheet's biographical file.
- Add a link table from Chadwick `links.csv` (`tsncards`, `findagrave`) and the Chadwick-to-Retrosheet id link
  (`key_retro` equals Retrosheet `PLAYERID`/`id`).
- Name lookup searches every name row and returns each person once with the names that matched and where they came from.
- Add a conflicts report: for people present in both Chadwick and Retrosheet, fields that differ (birth date, name
  spelling after normalization, first major-league year versus debut date), with both values and sources, never merged
  silently.
- Credit both sources in results and in `docs/CREDITS.md`/`NOTICE`: Chadwick Bureau (ODC-BY 1.0) and Retrosheet (its
  notice statement).

## Capabilities

### New Capabilities
- `player-name-register`: a multi-source table of player names with provenance, name search across all of them, and an
  explicit report of disagreements between sources.

### Modified Capabilities

None; `player-id-crosswalk` keeps its behavior and may use the name register for `find_players` in a later change.

## Impact

New code under `src/sabermetricspy/ids/` (or a sibling package), tests with hand-built source fixtures plus opt-in checks
against the downloaded files, and documentation. No change to metrics. Facts taken from the independent review of
2026-10-20, to be re-read at source during implementation (Retrosheet's own site was unreachable then, so its file layout
was read from Chadwick's mirror `chadwickbureau/retrosheet`): Chadwick `names.csv` columns `key_person, name_last,
name_first, name_given, birth_year, birth_month, birth_day, altname_type, altname_lang, altname_last, altname_first,
altname_given, altname_matrilineal, altname_nick, altname_date_start, altname_date_end`; `links.csv` columns
`key_person, source, value`; Retrosheet `biofile.csv` columns `PLAYERID, LAST, FIRST, NICKNAME, BIRTHDATE, ... BIRTH.NAME,
NAME.CHG, ...` and `biofile0.csv` columns `id, lastname, usename, fullname, birthdate, ... birthname, altname, ...`.
In a trial join of Chadwick shard 0 to `biofile0.csv` (1,622 matched people): 15 birth dates differed, 71 last names
differed (all accents), 75 first names differed (accents, "R. J." versus "R.J.", given name versus nickname), and 47
first major-league years differed from the debut date.
