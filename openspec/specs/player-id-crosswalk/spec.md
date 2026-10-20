# player-id-crosswalk Specification

## Purpose
Translate player identifiers between the id systems of the Chadwick Bureau Register on any dataframe backend, and look up
people by normalized name, so frames from Statcast, the MLB Stats API, Retrosheet, Lahman, FanGraphs and
Baseball-Reference can be joined without a hand-made mapping.

## Requirements

### Requirement: Supported id systems
The crosswalk SHALL translate between the register's id systems: `uuid`, `person`, `mlbam`, `retro`, `bbref`,
`bbref_minors`, `fangraphs`, `npb` and `wikidata`. Ids of different systems SHALL keep their native types (MLBAM and
FanGraphs ids are integers; Retrosheet and Baseball-Reference ids are strings).

#### Scenario: Retrosheet id to MLBAM id
- **WHEN** a frame has a Retrosheet id column and the caller translates it to MLBAM ids
- **THEN** each row gets the MLBAM id the register lists for that Retrosheet id

#### Scenario: Unknown id system
- **WHEN** the caller names an id system the register does not carry
- **THEN** the call fails with an error listing the supported systems

### Requirement: Translation on any dataframe
Translating a frame's id column SHALL work on Polars, pandas, PyArrow and DuckDB inputs, return the caller's native type,
keep every input row and its order, and add the target id as a new column without altering other columns.

#### Scenario: Row-preserving join
- **WHEN** a frame of 1,000 rows with repeated ids is translated
- **THEN** the result has 1,000 rows in the same order

#### Scenario: Id missing from the register
- **WHEN** a row holds an id the register does not list, or the register has no target id for that person
- **THEN** the target id for that row is null and the call reports how many rows were unmatched

### Requirement: Duplicate and conflicting ids are explicit
When one source id maps to more than one person in the register, the call SHALL raise an error naming the ids instead of
choosing a person.

#### Scenario: One source id, two people
- **WHEN** the register lists the same `key_bbref` for two different `key_uuid` values and a frame contains it
- **THEN** the call raises an error naming that id and both people

### Requirement: Name lookup with normalization
Name lookup SHALL compare names after Unicode accent folding, case folding, removal of punctuation, and removal of
generational suffixes (Jr., Sr., II, III, IV), and SHALL accept optional filters for birth year and for a season in which
the person was active. The result SHALL list every matching person with their ids and playing years.

#### Scenario: Accents and punctuation
- **WHEN** the caller looks up an accented name written without accents, or a name with a suffix and trailing period
- **THEN** the same person is returned as for the register's spelling

#### Scenario: Ambiguous name
- **WHEN** a name matches several people and no filter narrows it to one
- **THEN** all matches are returned, and a single-id request for that name raises an error that lists the candidates

#### Scenario: No match
- **WHEN** a name matches nobody
- **THEN** the result is empty and a single-id request raises an error saying no match was found

### Requirement: Register source, attribution and reproducibility
The register SHALL be loaded from a path the caller supplies or downloaded to a user cache when the caller asks, never
bundled in the package. A download SHALL be pinned to a repository commit (the latest on the requested ref unless the
caller names one) and SHALL record the commit and the fetch date. Every result SHALL carry the register's license name
(Open Data Commons Attribution License 1.0), the Chadwick Bureau as the source, the commit when known, and the fetch
date, and the project's credits SHALL state the same.

#### Scenario: Offline use
- **WHEN** the caller supplies a local register path and no network is available
- **THEN** all translations and lookups work

#### Scenario: No register available
- **WHEN** no path is given and no cached copy exists and the caller did not ask for a download
- **THEN** the call fails with an error that says how to supply or download the register

#### Scenario: Attribution travels with results
- **WHEN** a translation completes
- **THEN** its result metadata names the Chadwick Bureau, the license, the fetch date, and the commit when the register
  was downloaded with this library

#### Scenario: Pinned download
- **WHEN** a download names a commit
- **THEN** the shards come from that commit and the recorded commit equals it

### Requirement: The caller's frame is preserved
Translating ids SHALL return the caller's own frame type with exactly one column added. Existing columns, their dtypes,
pandas index values, and row order SHALL be unchanged; a Polars LazyFrame SHALL stay lazy; a column the caller already
has SHALL never be overwritten or removed, including columns whose names look like internal helpers.

#### Scenario: pandas index and nullable dtypes
- **WHEN** a pandas frame with index 10, 20, 30 is translated
- **THEN** the result has index 10, 20, 30, no extra columns, the caller's columns unchanged, and the new id column holds
  nullable integers for integer id systems

#### Scenario: Lazy frame
- **WHEN** a Polars LazyFrame is translated
- **THEN** the result is a LazyFrame

#### Scenario: Helper-looking column names
- **WHEN** the frame has a column named like an internal helper such as `__key` or `__row`
- **THEN** that column is returned unchanged

### Requirement: Ids match exactly
A source id SHALL match only when it equals a register id exactly. Non-integral numeric ids (100.7 for an integer
system) SHALL NOT match a person, and string ids SHALL be compared after trimming surrounding whitespace.

#### Scenario: Fractional id
- **WHEN** an MLBAM id of 100.7 is translated
- **THEN** the row is unmatched, not matched to id 100

### Requirement: Names that normalize to nothing never match
A name query that is empty after normalization SHALL raise an error, and register rows whose names are empty after
normalization SHALL never match. Letters that cannot be decomposed into a base letter and an accent (o with stroke,
l with stroke, ae, d with stroke, sharp s) SHALL fold to their conventional Latin spelling, and any whitespace SHALL
separate name parts.

#### Scenario: Non-Latin query
- **WHEN** a lookup uses a name with no Latin letters and the register holds people with missing names
- **THEN** the lookup raises an error saying the name cannot be normalized, and returns no person

#### Scenario: Stroked letters
- **WHEN** a name containing o with stroke is looked up in plain ASCII
- **THEN** the person is found

### Requirement: Register cache follows the files
A loaded register SHALL be reused only while its files are unchanged; loading a different directory, or the same
directory after a shard changed, SHALL read the current files.

#### Scenario: Same relative path, different directories
- **WHEN** a register is loaded from "." in one directory and then from "." in another
- **THEN** each load returns the register of its own directory
