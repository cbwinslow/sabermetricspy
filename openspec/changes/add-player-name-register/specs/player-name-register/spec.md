# Spec Delta

## Purpose
Hold player names from several published sources in one searchable table that keeps where each name came from, and report
where the sources disagree instead of choosing between them.

## ADDED Requirements

### Requirement: Names keep their source
Every name in the register SHALL record the person it belongs to, the source file it came from, a name type (legal or
given, common, nickname, alias, alternate spelling, birth name, matrilineal name), the name parts present, a normalized
form, and its start and end dates when the source gives them. Names from different sources SHALL be separate rows, never
merged into one.

#### Scenario: Same person, two sources
- **WHEN** a person appears in the Chadwick people file and in the Retrosheet biographical file
- **THEN** the register holds a row for each source's name for that person, each labelled with its source

#### Scenario: Alternate name
- **WHEN** the Chadwick alternate-names file lists an alias for a person
- **THEN** the register holds that alias as a row of type alias with the file's language and dates

### Requirement: Search across all names
Name search SHALL match the normalized query against every name row, SHALL return each person once with the matching
names and their sources, and SHALL list all candidates when a query matches several people.

#### Scenario: Nickname search
- **WHEN** a query equals a person's nickname in any source
- **THEN** the person is returned with the nickname row that matched

#### Scenario: Ambiguous query
- **WHEN** a query matches two people
- **THEN** both are returned, and a single-person request raises an error listing both

### Requirement: Disagreements are reported, not resolved
For people present in more than one source, the register SHALL report each field that differs (birth date, name spelling
after normalization, first major-league year against the debut date) with both values and both sources, and SHALL NOT
overwrite or discard either value.

#### Scenario: Birth dates differ
- **WHEN** two sources give different birth dates for one person
- **THEN** the conflicts report lists the person, both dates and both sources

#### Scenario: Accent-only difference
- **WHEN** two sources spell a last name with and without an accent
- **THEN** the names are not reported as a conflict after normalization, and both spellings remain searchable

### Requirement: Attribution and provenance
Results SHALL carry the credit and license of every source used (Chadwick Bureau under ODC-BY 1.0, and Retrosheet's
notice statement) and the commit or fetch date each source file was read at.

#### Scenario: Citation travels with a search
- **WHEN** a search returns people
- **THEN** the result metadata names each source, its license or notice, and its commit or fetch date

### Requirement: Sources are not bundled
The register SHALL be built from files the caller supplies or downloads, and SHALL NOT ship source data in the package.

#### Scenario: No data available
- **WHEN** no source files are available and no download was requested
- **THEN** the build fails with an error saying how to supply or download them
