# Spec Delta

## ADDED Requirements

### Requirement: Fit input is validated
Fitting SHALL raise an error that names the problem when a required column is missing, any required value is null,
outs are outside 0 to 2, a base state is not one of the eight base states, the half indicator is not boolean, or the
home result is not 0 or 1.

#### Scenario: Invalid base state
- **WHEN** a row has the base state "1__"
- **THEN** fitting raises an error naming the base state

#### Scenario: Text half indicator
- **WHEN** the half indicator column holds the strings "true" and "false"
- **THEN** fitting raises an error saying the column must be boolean

#### Scenario: Null inning
- **WHEN** an inning value is null
- **THEN** fitting raises an error naming the column

### Requirement: The estimator and its uncertainty are described accurately
The fitted rate SHALL be the share of the state's plate appearances that occurred in games the home team won, and the
reported standard error SHALL be the binomial standard error using the number of games that reached the state as the
sample size, documented as an approximation because plate appearances within a game are correlated.

#### Scenario: Weighting is documented
- **WHEN** the model's documentation is read
- **THEN** it states that the rate is weighted by plate appearance and the standard error by game
