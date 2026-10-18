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

### Requirement: Published rates are reproduced from published counts
For metric families whose counts and published rates are both available from a primary source (batted-ball types and directions, strikeout and walk indices, strikeout-minus-walk rates, and the pitcher rates not yet covered), fixtures SHALL record the published counts as inputs and the published rates as expected values, and the library MUST reproduce them within the entry's tolerance.

#### Scenario: Batted-ball rates
- **WHEN** GB%, FB%, LD%, IFFB%, Pull%, Cent%, Oppo%, and HR/FB are calculated from a fixture's published batted-ball counts
- **THEN** each equals the published rate within the stated tolerance

#### Scenario: League-indexed rates
- **WHEN** K%+ or BB%+ is calculated for a fixture pitcher
- **THEN** the result is compared with the published index and any difference is within tolerance or recorded as a documented divergence with its cause

### Requirement: Pitch-level metrics are checked on a recorded sample
For plate-discipline and pitch-physics metrics, whose inputs are pitch-level, the repository SHALL record a small, source-attributed Statcast sample (or published per-player rates with their pitch counts) and SHALL check the library's counts and rates against published values.

#### Scenario: Plate-discipline rates
- **WHEN** Swing%, Z-Swing%, O-Swing%, Contact%, Zone%, SwStr%, CStr%, and CSW% are calculated from the recorded sample
- **THEN** they equal the published rates within the stated tolerance or are recorded as documented divergences

#### Scenario: Sample unavailable
- **WHEN** no retrievable pitch-level sample exists for a metric
- **THEN** its evidence tier is primary or secondary and the audit note says no numeric check was possible

### Requirement: Audited fixtures keep their provenance
Every fixture added by the audit SHALL record the source URL, retrieval date, and tolerance, and values taken from a summarizing tool SHALL be recomputed from raw inputs before acceptance.

#### Scenario: Recomputation gate
- **WHEN** an audit fixture's published rate is recomputed from its published counts
- **THEN** the recomputed value equals the published value within the entry's tolerance
