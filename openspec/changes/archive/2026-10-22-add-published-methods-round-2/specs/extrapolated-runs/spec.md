## ADDED Requirements

### Requirement: Extrapolated Runs
The library SHALL provide Furtado's XR and XRR run estimators with the published fixed weights, with total walks including intentional walks, and absent optional columns counted as 0.

#### Scenario: Printed example
- **WHEN** Mark McGwire 1998 inputs from the article
- **THEN** XR is 166.35 and XRR is 167.05 within 0.005

#### Scenario: Additivity
- **WHEN** counts of two players are summed
- **THEN** the estimate equals the sum of the two estimates
