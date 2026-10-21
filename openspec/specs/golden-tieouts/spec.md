# golden-tieouts Specification

## Purpose
TBD - created by archiving change v1-golden-tieouts-and-readiness. Update Purpose after archive.

## Requirements

### Requirement: baseballr Benchmark Verification
Golden fixtures taken from baseballr SHALL record the function call, package version and run date, and tests SHALL compare `sabermetricspy` output to them.

#### Scenario: Constants, wOBA and FIP match baseballr
- **GIVEN** `tests/golden/baseballr/baseballr_tieout.json`
- **WHEN** bundled constants, `Metric.WOBA` and `Metric.FIP` are computed
- **THEN** they equal `fg_guts()`, `woba_plus()` and `fip_plus()` within baseballr's rounding.

#### Scenario: Fixture provenance
- **GIVEN** a baseballr fixture file
- **WHEN** it is reviewed
- **THEN** its header names the exact baseballr call, version and date the values came from.

### Requirement: Chadwick Register Stays Current
`update_register()` SHALL re-download the register only when the upstream commit differs from the recorded one and SHALL NOT alter existing files on failure. `load_register()` without a path SHALL do this automatically, at most once a day, use the existing copy with a warning when upstream is unreachable, and never update a caller-supplied path unless asked.

#### Scenario: Unchanged commit
- **GIVEN** a complete local register recorded at the latest upstream commit
- **WHEN** `update_register()` is called
- **THEN** nothing is downloaded and `updated` is False.

#### Scenario: Upstream unreachable
- **WHEN** the latest commit cannot be looked up
- **THEN** `ConnectionError` is raised and local files are unchanged.

#### Scenario: Default register updates itself
- **GIVEN** a default register last checked before today and a newer upstream commit
- **WHEN** `load_register()` is called with no path
- **THEN** the newer register is downloaded and returned.

#### Scenario: Checked today
- **GIVEN** a default register already checked today
- **WHEN** `load_register()` is called
- **THEN** upstream is not contacted.

#### Scenario: Offline with a copy
- **WHEN** upstream is unreachable and a copy exists
- **THEN** the copy is returned with a warning.
