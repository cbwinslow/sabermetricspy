# Spec Delta

## Purpose
Translate player identifiers between the id systems of the Chadwick Bureau Register on any dataframe backend, and look up
people by normalized name, so frames from Statcast, the MLB Stats API, Retrosheet, Lahman, FanGraphs and
Baseball-Reference can be joined without a hand-made mapping.

## ADDED Requirements

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
bundled in the package. Every result SHALL carry the register's license name (Open Data Commons Attribution License 1.0),
the Chadwick Bureau as the source, and the register's release date, and the project's credits SHALL state the same.

#### Scenario: Offline use
- **WHEN** the caller supplies a local register path and no network is available
- **THEN** all translations and lookups work

#### Scenario: No register available
- **WHEN** no path is given and no cached copy exists and the caller did not ask for a download
- **THEN** the call fails with an error that says how to supply or download the register

#### Scenario: Attribution travels with results
- **WHEN** a translation completes
- **THEN** its result metadata names the Chadwick Bureau, the license, and the register release date
