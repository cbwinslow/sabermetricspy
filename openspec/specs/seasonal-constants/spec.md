# seasonal-constants Specification

## Purpose
Defines how seasonal linear weights and league constants reach the contextual metrics: the library ships none and downloads none (ADR-0068); the caller supplies a constants directory, and values that can be computed from data the caller owns are computed.

## Requirements

### Requirement: Constants are supplied, not shipped
The package SHALL contain no third-party constants tables. Constants SHALL be read from a directory set with `use_constants(path)` or `$SABERMETRICSPY_CONSTANTS`, and a missing directory or file SHALL raise `ConstantsNotFoundError` that says where such values can be obtained or computed.

#### Scenario: No directory set
- **WHEN** a metric needs seasonal constants and neither `use_constants` nor the environment variable is set
- **THEN** `ConstantsNotFoundError` is raised and names `docs/CONSTANTS.md`

#### Scenario: Directory supplied
- **WHEN** `use_constants(path)` names a directory with `woba_fangraphs.yaml`
- **THEN** `get_woba_weights(season)` returns that file's values for the season

### Requirement: Season coverage and sourcing
Every entry in a supplied table SHALL record its source and retrieval date, and a constant with no source MUST be absent rather than filled with a default or copied from another field. League ERA, FIP, xFIP and HR/FB values are present only when taken from a cited source.

#### Scenario: League HR/FB unavailable
- **WHEN** a season has no sourced league HR/FB rate
- **THEN** the constant is absent, and no default value is substituted

### Requirement: Internal consistency of league constants
Supplied constants SHALL satisfy published identities: league FIP matches league ERA by construction of cFIP, and the wOBA weights reproduce league wOBA within a stated tolerance.

#### Scenario: cFIP consistency
- **WHEN** a season's cFIP and league totals are checked
- **THEN** the implied league FIP equals league ERA within the stated tolerance

### Requirement: Missing seasons raise
When constants are requested for a season absent from the supplied table, the library SHALL raise `ConstantsNotFoundError` naming the season and the range the table covers, and SHALL NOT substitute another season's values. A constant the supplied table does not carry and that has no sourced default (for example league K% and BB%, OBP and SLG) SHALL raise the same error naming the constant.

#### Scenario: Requesting a missing season
- **WHEN** constants are requested for a season that is not in the table
- **THEN** `ConstantsNotFoundError` is raised and no values are returned

#### Scenario: Guts-only table and a metric that needs league K%
- **WHEN** only a Guts! table is supplied and `bat_k_pct_plus` is calculated
- **THEN** `ConstantsNotFoundError` names `lg_k_pct`

### Requirement: League constants computed from the Lahman database
`sabermetricspy.lahman.league_constants` SHALL compute a season's league runs per PA, OBP, SLG, ERA, cFIP, kwERA constant and caught-stealing run value from Lahman CSV files the caller supplies, and SHALL NOT download them.

#### Scenario: Hand-checkable totals
- **WHEN** the files hold known totals
- **THEN** every computed value equals its definition applied to those totals
