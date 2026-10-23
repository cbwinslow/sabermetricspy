# isolated-discipline Specification

## Purpose
Provide Isolated Discipline (IsoD), defined as on-base percentage minus batting average, measuring pure non-hit plate discipline.

## ADDED Requirements

### Requirement: Isolated Discipline
The library SHALL provide Isolated Discipline, defined as OBP - AVG, evaluated from summed counts and null when plate appearances or at-bats are zero.

#### Scenario: Published player season
- **WHEN** Aaron Judge 2024 with OBP 0.458 and AVG 0.322
- **THEN** IsoD is 0.136 within 0.001

#### Scenario: Identity with components
- **WHEN** valid batting counts are provided
- **THEN** IsoD equals OBP minus AVG within 1e-9
