# Proposal

## Why

The library already reads Retrosheet, Statcast and Lahman frames, but each source names players differently (Retrosheet
`troum001`, MLBAM `545361`, Baseball-Reference `troutmi01`, FanGraphs numeric ids, Lahman `playerID`), so a user cannot
join Statcast pitches to Retrosheet events or to a FanGraphs leaderboard without writing their own mapping. The Chadwick
Bureau Register is the published authority file that links these ids, and `baseballr` (`chadwick_player_lu`,
`playerid_lookup`) and `pybaseball` (`playerid_lookup`) both expose it, so users expect the same here.

## What Changes

- Add a player-id crosswalk built on the Chadwick Register `people` files (ODC-BY 1.0): map between `key_uuid`,
  `key_person`, `key_mlbam`, `key_retro`, `key_bbref`, `key_bbref_minors`, `key_fangraphs`, `key_npb` and `key_wikidata`.
- Add id translation on any dataframe backend: add or replace an id column in a frame given its current id type.
- Add name lookup and normalization: a name (first, last, optional birth year or active year) returns the matching
  register rows; accents, case, punctuation and generational suffixes (Jr., Sr., II, III) are normalized explicitly.
- Ambiguity is reported, never guessed: a name that matches several people returns all of them, and a translation that
  would pick one of several raises.
- Load the register from a caller-supplied path or download it to a user cache on request. No register snapshot ships in
  the wheel, and the register's license and attribution appear in `docs/CREDITS.md`, `NOTICE` and each result's metadata.
- Record the register release date in results so a join can be reproduced.

## Capabilities

### New Capabilities
- `player-id-crosswalk`: translating player ids between Chadwick Register id systems on any dataframe, and looking up
  people by normalized name, with explicit handling of missing ids, duplicates and ambiguous names.

### Modified Capabilities

None. Presets stay as they are; callers apply the crosswalk to the frames they pass in.

## Impact

- New package `src/sabermetricspy/ids/` (crosswalk loader, name normalizer, translate function) exported from the
  top-level package; no change to existing metric or model behavior.
- Network access only when the caller asks for a download; the default is a local file. Download uses the standard
  library, so no new dependency.
- Tests: hand-built register fixtures always run; an opt-in test against a downloaded register checks published ids.
- Docs: `docs/CREDITS.md`, `NOTICE`, `docs/DECISIONS.md` (new ADR with Alternatives), `docs/LITERATURE.md` source entry.
