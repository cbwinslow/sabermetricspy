# batters-run-average Specification

## Purpose
Provide Cramer and Palmer's Batter's Run Average (BRA), the multiplicative interaction of on-base percentage and slugging percentage.

## Requirements

### Requirement: Batter's Run Average
The library SHALL provide Batter's Run Average, defined as OBP * SLG, evaluated from component rates and null when either rate is null.

#### Scenario: Published 1973 league value
- **WHEN** 1973 NL league on-base average 0.323 and slugging percentage 0.376
- **THEN** BRA equals 0.121 within 0.001

#### Scenario: Identity with components
- **WHEN** valid batting counts are provided
- **THEN** BRA equals OBP * SLG within 1e-9
