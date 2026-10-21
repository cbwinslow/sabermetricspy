# Spec Delta

## MODIFIED Requirements

### Requirement: Register source, attribution and reproducibility
The register SHALL be loaded from a path the caller supplies or obtained through the reference-data cache, never bundled in
the package. A download SHALL be pinned to a repository commit, published atomically with all shards from that one commit,
and SHALL record the commit, the fetch date, the last check date, and whether the data is stale. If the commit cannot be
determined the call SHALL fail or use the last valid snapshot with a warning; it SHALL NOT download an unpinned copy. Every
result SHALL carry the register's license name (Open Data Commons Attribution License 1.0), the Chadwick Bureau as the source,
the commit when known, and the fetch date, and the project's credits SHALL state the same.

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

#### Scenario: Commit lookup fails
- **WHEN** the latest commit cannot be determined during a download
- **THEN** no unpinned files are fetched; the last valid snapshot is used with a warning, or an error is raised if none exists
