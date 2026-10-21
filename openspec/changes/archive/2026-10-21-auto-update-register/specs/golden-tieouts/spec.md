# Specification: Golden Tie-Outs & Reference Readiness

## MODIFIED Requirements

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
