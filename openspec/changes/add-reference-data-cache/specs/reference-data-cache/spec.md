# Spec Delta

## Purpose
Fetch external reference datasets (player registers, biographical and team files, league structure) on demand, keep them on
disk with their version and license, refresh them cheaply, and say plainly when data is stale or missing.

## ADDED Requirements

### Requirement: Versioned, verified snapshots
Every fetched dataset SHALL be stored as a snapshot identified by its source version (a commit for repository sources, the
request time for API sources) together with a manifest naming the source, URL, version, SHA-256 of each file, ETag when given,
fetch time, last check time and license or notice. A snapshot SHALL contain files from exactly one version.

#### Scenario: Manifest describes the files
- **WHEN** a snapshot is fetched
- **THEN** its manifest lists every file with a SHA-256 equal to the hash of the stored bytes

#### Scenario: One version per snapshot
- **WHEN** the source changes between the first and last file of a download
- **THEN** the snapshot is discarded and the download restarts, or fails; it is never published with mixed versions

### Requirement: Atomic publication
A reader SHALL never see a partially written snapshot. Downloads SHALL be completed and verified in a temporary location and
then published in one step, under a lock that serializes concurrent processes. The two most recent snapshots SHALL be kept.

#### Scenario: Interrupted download
- **WHEN** a download fails after some files arrived
- **THEN** the previously published snapshot is still the one that is read and no partial files are visible

#### Scenario: Two processes refresh at once
- **WHEN** two processes request a refresh of the same source together
- **THEN** one downloads, the other waits and reuses the result, and a valid snapshot results

### Requirement: Cheap freshness check and refresh policy
The cache SHALL decide whether a download is needed using one small request (the source's current version, or a conditional
request) and SHALL support three policies: `auto` (check only when the snapshot is older than the source's maximum age:
one day for the Chadwick Register, thirty days for Retrosheet), `always` (check on every call) and `never` (use what is on
disk). A check that finds the same version SHALL download nothing and SHALL update the last check time.

#### Scenario: Nothing changed
- **WHEN** the source version equals the snapshot's version
- **THEN** no data file is downloaded and the snapshot's check time is updated

#### Scenario: Never policy
- **WHEN** the policy is `never`
- **THEN** no network request is made

### Requirement: Failure is explicit
When the network, the version lookup, or verification fails, the cache SHALL use the newest valid snapshot, emit a
`StaleDataWarning`, and mark the result's provenance as stale. With no snapshot it SHALL raise `SourceUnavailableError`
naming the source and how to supply the data. It SHALL NOT fall back to a different source or an unpinned download.

#### Scenario: Offline with a snapshot
- **WHEN** the network is down and a snapshot exists
- **THEN** the data loads, a warning is emitted, and the provenance says the data is stale and since when

#### Scenario: Offline without a snapshot
- **WHEN** the network is down and nothing is cached
- **THEN** `SourceUnavailableError` is raised

### Requirement: Nothing is dropped, nothing is guessed
Every column of every source file SHALL be kept under its source name with a column dictionary listing name, file and
meaning where the source documents it. Parsing SHALL be strict: a value that does not match its column's type SHALL raise an
error naming the file, row and column, never become a null. Identifier columns SHALL keep text form.

#### Scenario: Unknown extra column
- **WHEN** a source file gains a new column
- **THEN** the column is kept and listed in the dictionary as undocumented

#### Scenario: Bad value
- **WHEN** a numeric column contains text
- **THEN** loading raises an error naming file, row and column

### Requirement: Explicit sources and provenance
The caller SHALL choose sources by name and order; the cache SHALL record in every result the source used, its URL, version,
fetch time, whether it is stale, and its license or notice. A source that needs the caller's acceptance of terms SHALL not run
until the caller gives it, and its notice SHALL appear in results.

#### Scenario: Opt-in source
- **WHEN** the MLB Stats API source is requested without accepting its terms
- **THEN** an error explains the terms and how to accept them, and no request is sent

#### Scenario: Provenance in results
- **WHEN** any reference table is returned
- **THEN** it carries source, URL, version, fetched-at, stale flag and license

### Requirement: Polite network use
Requests SHALL identify the library in the User-Agent, use timeouts, retry only transient failures with bounded backoff, honor
rate-limit responses, and stay within a per-host request rate. No request SHALL bypass an access block by changing network
identity.

#### Scenario: Rate limited
- **WHEN** the server answers that the rate limit is exhausted
- **THEN** the cache stops requesting, uses the snapshot with a warning, and reports when the limit resets

### Requirement: Testable without a network
The default test run SHALL make no external requests; reference-data behavior SHALL be tested against a local server, and live
checks SHALL run only when explicitly enabled.

#### Scenario: Default test run
- **WHEN** the tests run with no network
- **THEN** all fetch tests pass
