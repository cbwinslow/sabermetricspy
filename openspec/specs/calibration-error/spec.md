# calibration-error Specification

## Purpose
Provide Expected Calibration Error (ECE) and Maximum Calibration Error (MCE) evaluation metrics for assessing reliability of probabilistic forecasts.

## Requirements

### Requirement: Calibration error
The library SHALL provide the expected and maximum calibration error over equal-width bins in the event form, with optional weights and ValueError on invalid input.

#### Scenario: One bin
- **WHEN** a single bin is requested
- **THEN** both equal the absolute gap between the base rate and the mean forecast

#### Scenario: Weights
- **WHEN** rows are weighted
- **THEN** the result equals that of repeating the rows
