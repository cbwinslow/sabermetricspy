# Spec Delta

## Purpose

Defines the sourced catalogue of candidate methods and the repeatable procedure that produces it, so decisions about what to add to the library rest on published, verifiable literature.

## ADDED Requirements

### Requirement: Catalogue of candidate methods
The repository SHALL contain `docs/LITERATURE.md` listing candidate methods not yet in the library, and each entry SHALL record the method name, a primary-source citation with URL, the formula source, the inputs it needs, whether those inputs exist in the canonical schema, a validation target (a published value or table that could confirm an implementation), a priority, and an estimated difficulty.

#### Scenario: Complete entry
- **WHEN** a catalogue entry is read
- **THEN** it provides every field above or states explicitly that a field is unknown and why

#### Scenario: Entry without a citation
- **WHEN** a candidate has no primary-source citation
- **THEN** it is excluded from the prioritized list and recorded in a rejected-with-reason section

### Requirement: Prioritization is explicit and reproducible
Candidates SHALL be ranked by stated criteria (published formula, availability of inputs, availability of a validation target, fit with the provider-agnostic design, user value, and difficulty), and the ranking MUST be derivable from the recorded fields.

#### Scenario: Ranking inspection
- **WHEN** a reader compares two entries
- **THEN** the recorded criteria explain their relative order

### Requirement: Coverage analysis against baseballr
The catalogue SHALL include an analysis of the `baseballr` package listing, by function group, what overlaps with sabermetricspy, what is data acquisition outside the library's scope, and what is a coverage gap worth cataloguing.

#### Scenario: Metric overlap
- **WHEN** the analysis lists baseballr's metric functions
- **THEN** each is marked as covered, partly covered, or a gap, with the sabermetricspy equivalent named when one exists

#### Scenario: Data-acquisition functions
- **WHEN** a baseballr function only retrieves data
- **THEN** it is recorded as out of scope under the pure-calculation rule

### Requirement: Coverage of each requested source
The catalogue SHALL record, for OpenAlex, arXiv, Tom Tango's work, and the Retrosheet research page, the query or pages examined, the date, and what could not be retrieved, and a source that cannot be retrieved (for example a book) SHALL be named with the limitation.

#### Scenario: Unretrievable source
- **WHEN** a requested source cannot be retrieved
- **THEN** the catalogue says so and names the substitute used, such as the Tango wiki archive for *The Book*

### Requirement: Repeatable sweep procedure and tool
The repository SHALL document the sweep procedure in `docs/LITERATURE_SWEEP.md` and provide a tool under `tools/` that runs the OpenAlex and arXiv queries, and the tool MUST respect each service's published terms and rate limits, send no personal data, and store bibliographic metadata and the license only.

#### Scenario: Offline test of parsing
- **WHEN** the tool parses a recorded OpenAlex or arXiv response
- **THEN** it yields the normalized metadata records without network access

#### Scenario: Rate limit
- **WHEN** the tool issues consecutive arXiv requests
- **THEN** it waits at least the interval arXiv publishes between them

#### Scenario: No full text
- **WHEN** the tool records a result
- **THEN** it stores identifiers, title, authors, year, venue, license, and abstract link, and does not store paper text
