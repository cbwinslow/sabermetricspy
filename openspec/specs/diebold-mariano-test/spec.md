# diebold-mariano-test Specification

## Purpose
Provide the Diebold-Mariano hypothesis test for evaluating the statistical significance of predictive accuracy differences between two competing forecasting models.

## Requirements

### Requirement: Diebold-Mariano test
The library SHALL provide the Diebold-Mariano statistic for two forecasts with a Bartlett long-run variance at horizon-1 lags and a two-sided normal p-value, positive when forecast A has the larger loss.

#### Scenario: Reference implementation
- **WHEN** the 12-point research sample at horizons 1, 2 and 3
- **THEN** the statistic and p-value equal statsmodels 0.15.0 with lags = horizon - 1

#### Scenario: Zero variance
- **WHEN** the two forecasts are identical
- **THEN** a ValueError is raised
