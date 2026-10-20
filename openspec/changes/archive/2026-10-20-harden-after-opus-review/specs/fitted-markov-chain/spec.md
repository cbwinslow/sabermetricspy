# Spec Delta

## ADDED Requirements

### Requirement: Transition input is validated
Fitting SHALL raise an error that names the problem when a required column is missing, any required value is null,
outs before are outside 0 to 2, outs after are outside 0 to 3 or below outs before, a base state is not one of the
eight base states, or runs on a play are negative.

#### Scenario: Unknown base state
- **WHEN** a row has a base state outside the eight valid strings
- **THEN** fitting raises an error naming the value

#### Scenario: Outs decrease
- **WHEN** a play ends with fewer outs than it began with
- **THEN** fitting raises an error

### Requirement: A chain that cannot finish is reported
When some observed states cannot reach three outs (their transitions loop among themselves), fitting SHALL raise an
error naming those states instead of a numerical failure.

#### Scenario: Trapped states
- **WHEN** the plays from two states only lead to each other
- **THEN** fitting raises an error naming both states

### Requirement: State forecasts validate their arguments
Forecasting the state distribution SHALL raise an error for a start state that is not a valid base-out state, and for a
negative number of batters.

#### Scenario: Bad start
- **WHEN** the start state is three outs with the bases empty
- **THEN** an error names the start state
