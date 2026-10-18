# Spec Delta

## ADDED Requirements

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
