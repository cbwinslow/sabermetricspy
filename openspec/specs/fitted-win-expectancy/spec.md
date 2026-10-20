# fitted-win-expectancy Specification

## Purpose
Estimate the home team's win expectancy from play-by-play, state by state, with the evidence behind each estimate, so the
values can be compared with published win expectancy tables.

## Requirements

### Requirement: Win expectancy is the observed home win rate per state
Fitting SHALL group plate appearances by inning, half, outs, base state and home score difference and report the home win
rate of each group. There SHALL be no built-in table, and a state with no observations SHALL be absent rather than
filled in.

#### Scenario: Hand-computed rate
- **WHEN** three games reach one state, four plate appearances occur in it, and the home team won two of those games
  with three of the four plate appearances
- **THEN** the fitted rate is three quarters and the state records four plate appearances and three games

#### Scenario: Unobserved state
- **WHEN** a state is looked up that no plate appearance reached
- **THEN** the lookup returns no value

### Requirement: Uncertainty counts games, not plate appearances
The standard error of a state's rate SHALL be the binomial standard error using the number of distinct games that reached
the state.

#### Scenario: Games versus plate appearances
- **WHEN** a state has four plate appearances from three games and a rate of three quarters
- **THEN** the standard error is the square root of (0.75 x 0.25 / 3)

### Requirement: Agreement with the published table
On Retrosheet 2016, every bottom-of-the-ninth state with at least 30 games SHALL lie within three standard errors of the
corresponding value in Tom Tango's published win expectancy table, and the check SHALL run only when the data file is
supplied.

#### Scenario: Well-sampled cells
- **WHEN** the model is fitted on Retrosheet 2016 and compared with the published table
- **THEN** all cells with at least 30 games are within three standard errors

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
