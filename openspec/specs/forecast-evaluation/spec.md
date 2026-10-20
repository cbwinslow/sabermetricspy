# forecast-evaluation Specification

## Purpose
Provide forecast-scoring tools (error metrics for point forecasts, scores for probability forecasts, and calibration tables) so any model in the library can be judged the same way.

## Requirements

### Requirement: Point forecast error metrics
The library SHALL provide mean squared error, root mean squared error, mean absolute error and bias (mean of forecast minus actual) over a forecast column and an actual column, with an optional weight column.

#### Scenario: Unweighted values
- **WHEN** forecasts are 2, 4, 6 and actuals are 1, 4, 9
- **THEN** MSE is 10/3, RMSE is its square root, MAE is 4/3 and bias is -2/3

#### Scenario: Weighted values
- **WHEN** the same data carries weights 1, 2, 1
- **THEN** each statistic is the weight-averaged version of the unweighted definition

### Requirement: Probability forecast scores
The library SHALL provide the binary Brier score, a Brier skill score against a reference forecast (default the observed base rate) and log loss, for probability forecasts against 0/1 outcomes.

#### Scenario: Brier score
- **WHEN** forecasts are 0.9, 0.2, 0.6 and outcomes are 1, 0, 0
- **THEN** the Brier score is (0.01 + 0.04 + 0.36)/3

#### Scenario: Skill of the base rate
- **WHEN** the forecast equals the observed base rate for every row
- **THEN** the skill score is 0

#### Scenario: Out-of-range probability
- **WHEN** a forecast lies outside [0, 1] or an outcome is not 0 or 1
- **THEN** a ValueError is raised

### Requirement: Calibration table
The library SHALL provide a calibration table binning forecasts, with per-bin count, mean forecast and observed rate, and the Murphy decomposition of the Brier score into reliability, resolution and uncertainty.

#### Scenario: Exact decomposition
- **WHEN** every forecast equals its bin's value (forecasts take few distinct values, each in its own bin)
- **THEN** reliability - resolution + uncertainty equals the Brier score
