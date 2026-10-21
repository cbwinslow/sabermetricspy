# Specification: Golden Tie-Outs & Reference Readiness

## ADDED Requirements

### Requirement: baseballr Benchmark Verification
Golden fixtures taken from baseballr SHALL record the function call, package version and run date, and tests SHALL compare `sabermetricspy` output to them.

#### Scenario: Fixture provenance
- **GIVEN** a baseballr fixture file
- **WHEN** it is reviewed
- **THEN** its header names the exact baseballr call, version and date the values came from.

### Requirement: Chadwick Register Stays Current
`update_register()` SHALL re-download the register only when the upstream commit differs from the recorded one, and SHALL NOT alter existing files on failure.

#### Scenario: Unchanged commit
- **GIVEN** a complete local register recorded at the latest upstream commit
- **WHEN** `update_register()` is called
- **THEN** nothing is downloaded and `updated` is False.

#### Scenario: Upstream unreachable
- **WHEN** the latest commit cannot be looked up
- **THEN** `ConnectionError` is raised and local files are unchanged.

#### Scenario: Stale register
- **GIVEN** files fetched more than 90 days ago
- **WHEN** `load_register()` is called
- **THEN** a warning tells the caller to run `update_register()`.
