# golden-reference-validation Specification

## Purpose
Defines the accuracy contract between sabermetricspy results and published FanGraphs and Baseball-Reference values, so metric correctness is verified against real data rather than only executed.

## Requirements

### Requirement: Sourced golden reference fixtures
The repository SHALL contain golden fixtures of published season lines and published metric results, and every fixture entry SHALL record its source URL, retrieval date, and the tolerance used for comparison.

#### Scenario: Fixture entry is complete
- **WHEN** a golden fixture entry is loaded
- **THEN** it provides the input counting stats, the published metric values, a source URL, a retrieval date, and a per-metric tolerance

#### Scenario: Entry missing provenance
- **WHEN** a fixture entry lacks a source URL or retrieval date
- **THEN** the fixture validation test fails

### Requirement: Fixture values are self-consistent before use
A fixture value taken from a summarizing or intermediate source SHALL be confirmed by recomputing it from the entry's raw inputs, and an entry that cannot be reproduced within its tolerance MUST NOT be accepted without a documented divergence.

#### Scenario: Recomputation confirms the entry
- **WHEN** a fixture's published wOBA is recomputed from its counting stats and the published weights
- **THEN** the recomputed value agrees with the published value within the entry's tolerance

### Requirement: Exact-value agreement with published results
For each golden fixture entry, calculated metrics SHALL match the published value within the entry's tolerance, and the tolerance MUST be derived from the rounding of the published constants and inputs, with any looser tolerance carrying a written reason.

#### Scenario: Bonds 2001 batting line
- **WHEN** wOBA, wRAA, wRC, and wRC+ are calculated for the Barry Bonds 2001 line (PA 664, AB 476, H 156, 2B 32, 3B 2, HR 73, BB 177, IBB 35, HBP 9, SF 2) with 2001 constants and the published league and park inputs
- **THEN** wOBA is 0.5367, wRAA is 117.7, wRC is 200.1, and wRC+ is 234.6 within their stated tolerances

#### Scenario: Pitchers with intentional walks
- **WHEN** FIP is calculated for Greg Maddux 2001 (IBB 10) and for the 2016 pitchers in the fixture set
- **THEN** each result equals the published FanGraphs FIP within the stated tolerance

#### Scenario: Disagreement is surfaced
- **WHEN** a calculated value falls outside tolerance
- **THEN** the test fails and reports the metric, expected value, actual value, and fixture source

### Requirement: Known divergences are documented
Any metric whose result intentionally differs from the published source SHALL be listed in the fixture with a written reason, and an undocumented difference MUST fail validation.

#### Scenario: Documented divergence
- **WHEN** a fixture entry marks a metric as a known divergence with a reason
- **THEN** the test records the divergence and does not fail on that metric

### Requirement: Every registered metric has a value assertion
Every metric in the registry SHALL be covered by at least one test that asserts a specific numeric result, and a registered metric without such coverage MUST fail a guard test.

#### Scenario: New metric added without a value test
- **WHEN** a metric is registered and no value assertion references it
- **THEN** the coverage guard test fails and names the uncovered metric

#### Scenario: All metrics covered
- **WHEN** every registered metric is referenced by a value assertion
- **THEN** the coverage guard test passes
