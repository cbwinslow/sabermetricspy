# ranked-probability-score Specification

## Purpose
Provide the Ranked Probability Score (RPS) strictly proper scoring rule for verifying multi-category ordered probabilistic forecasts.

## Requirements

### Requirement: Ranked probability score
The library SHALL provide the ranked probability score for K ordered categories as a loss normalised by K-1 by default.

#### Scenario: Two categories
- **WHEN** K is 2
- **THEN** the score equals the Brier score of the first category

#### Scenario: Printed table
- **WHEN** Epstein's Table 2 forecasts are scored
- **THEN** one minus the score reproduces the printed cells except the two cells the paper prints inconsistently
