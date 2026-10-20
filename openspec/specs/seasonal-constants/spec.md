# seasonal-constants Specification

## Purpose
Defines the coverage, provenance, and lookup behavior of the bundled seasonal linear weights and league constants that contextual metrics depend on, treating them as sourced defaults rather than hardcoded truth.

## Requirements

### Requirement: Bundled constants equal the published source
For every bundled season, the wOBA weights, wOBA scale, league wOBA, league runs per PA, runs per win, run values of stolen bases and caught stealing, and cFIP SHALL equal the published FanGraphs Guts! values, and each entry SHALL record its source and retrieval date.

#### Scenario: Looking up a bundled season
- **WHEN** a caller requests constants for a bundled season
- **THEN** every field equals the published value and the entry records its source

#### Scenario: Comparison with the published table
- **WHEN** the bundled table is compared with the stored copy of the published Guts! table
- **THEN** no field differs

### Requirement: Season coverage
The bundled table SHALL cover every season from 1990 through the most recent completed season, and the golden fixtures MUST NOT reference a season outside the table.

#### Scenario: Season range present
- **WHEN** the bundled table is loaded
- **THEN** it contains an entry for each season from 1990 through the latest bundled season with no gaps

### Requirement: No invented league constants
League ERA, FIP, xFIP, and HR/FB values SHALL be present only when taken from a cited source, and a constant with no source MUST be absent rather than filled with a default or copied from another field.

#### Scenario: No placeholder values
- **WHEN** a bundled season is validated
- **THEN** `lg_era`, `lg_fip`, and `lg_xfip` are each sourced, and values identical across all three fail validation unless the cited source shows they coincide

#### Scenario: League HR/FB unavailable
- **WHEN** a season has no sourced league HR/FB rate
- **THEN** the constant is absent, and no default value is substituted

### Requirement: Internal consistency of league constants
The bundled constants SHALL satisfy published identities: league FIP matches league ERA by construction of cFIP, and the wOBA weights reproduce league wOBA within a stated tolerance.

#### Scenario: cFIP consistency
- **WHEN** a bundled season's cFIP and league totals (HR, BB including IBB, HBP, K, IP, ERA) are checked
- **THEN** the implied league FIP equals league ERA within the stated tolerance

### Requirement: Explicit handling of unbundled seasons
When constants are requested for a season absent from the bundled table, the library SHALL return the nearest bundled season's constants labeled with the requested season and SHALL emit a `UserWarning` naming both seasons, once per requested and substituted pair.

#### Scenario: Requesting an unbundled season
- **WHEN** constants are requested for a season that is not bundled
- **THEN** a `UserWarning` names the requested and substituted seasons, and the values equal the nearest bundled season's

#### Scenario: Requesting a bundled season
- **WHEN** constants are requested for a bundled season
- **THEN** no warning is emitted

### Requirement: Optional league non-pitcher run environment
The constants model SHALL accept an optional league wRC/PA excluding pitchers, per league and season, with its source recorded, for use by metrics that adjust to the non-pitcher run environment.

#### Scenario: Constant supplied
- **WHEN** a season entry includes the non-pitcher league wRC/PA
- **THEN** the value is available to metric calculations with its source

#### Scenario: Constant absent
- **WHEN** a season entry omits the non-pitcher league wRC/PA
- **THEN** dependent metrics fall back to league R/PA and the metric's reference status and caveat state this

### Requirement: Season constants follow the data
When the caller supplies neither a context nor a season, the library SHALL use the single season found in the frame's
`season` column, and SHALL use the bundled default season only when the frame has no season column. For metrics that read
season constants, a frame whose single season differs from the supplied context or season SHALL raise an error naming
both seasons, and a call with no season from the caller or the data SHALL emit a `UserWarning` naming the default season.
Metrics that read no season constants SHALL be unaffected.

#### Scenario: Frame names its season
- **WHEN** a frame holding only season 2001 is calculated for wRC+ with no context
- **THEN** the 2001 constants are used and the result's context reports season 2001

#### Scenario: Frame contradicts the context
- **WHEN** a frame holding only season 2001 is calculated for wRC+ with a context or season of 2024
- **THEN** the call raises an error naming both seasons

#### Scenario: No season anywhere
- **WHEN** a frame has no season column and no season or context is given for wRC+
- **THEN** a `UserWarning` says the default season constants were used, and AVG on the same frame emits no warning
