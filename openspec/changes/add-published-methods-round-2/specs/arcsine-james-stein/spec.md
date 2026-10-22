## ADDED Requirements

### Requirement: Arcsine James-Stein shrinkage
The library SHALL provide the Efron-Morris arcsine James-Stein estimator for players with equal trials, raising ValueError for unequal trials and when V <= k-3.

#### Scenario: Printed estimates
- **WHEN** the 18 players of the 1970 first-45-at-bat data
- **THEN** all 18 retransformed estimates equal the printed values within 0.0005

#### Scenario: Constants
- **WHEN** the same data
- **THEN** (k-3)/V is .791 and the factor is .209 within 0.0005
