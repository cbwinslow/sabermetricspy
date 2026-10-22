## ADDED Requirements

### Requirement: Calibration bin convention
The library SHALL assign forecasts to equal-width calibration bins that are right-closed by default and SHALL offer left-closed bins on request.

#### Scenario: Edge forecast
- **WHEN** a forecast lies exactly on an inner bin edge
- **THEN** it falls in the lower bin by default and in the upper bin with closed=left

#### Scenario: Printed example
- **WHEN** Murphy's ten-forecast example is binned in ten bins
- **THEN** the uncertainty, reliability, resolution and Brier values equal half of the printed two-state values
