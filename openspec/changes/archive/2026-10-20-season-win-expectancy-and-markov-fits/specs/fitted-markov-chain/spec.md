# Spec Delta

## Purpose
Estimate the base-out Markov chain of a half-inning from play-by-play and solve it exactly, so run expectancy, expected
batters per inning and multi-batter state forecasts follow from observed transitions rather than assumed advancement.

## ADDED Requirements

### Requirement: Transition matrix from observed plays
Fitting SHALL estimate each row of the 24-by-25 transition matrix as the observed frequency of the next base-out state,
with three outs as the single absorbing state, and SHALL take the reward of a state as the mean runs scored on plays from
it. Fitting SHALL raise an error naming any base-out state with no observed play.

#### Scenario: Home-run-or-out chain
- **WHEN** every state's plays are home runs with probability p and outs otherwise
- **THEN** the expected runs from the empty bases, no-out state equal 3p / (1 - p) and the expected plate appearances equal 3 / (1 - p)

#### Scenario: Unobserved state
- **WHEN** a base-out state has no plays in the input
- **THEN** fitting raises an error naming the state

### Requirement: Exact solution and multi-batter forecasts
Expected runs and expected plate appearances SHALL come from the fundamental matrix of the absorbing chain, not from
simulation, and the model SHALL report the distribution over states after a given number of batters from a given start.

#### Scenario: One batter
- **WHEN** the state distribution after one batter is requested from the empty state of a fitted chain
- **THEN** it equals the empty state's transition row

### Requirement: Agreement with the published chain
On Retrosheet 2016 batting plays in complete half-innings, the fitted chain SHALL reproduce the transition probabilities,
expected plate appearances per half-inning, expected plays from each starting state, and the three-batter state
distribution printed in Albert, Baumer and Marchi, *Analyzing Baseball Data with R* (3rd ed.) chapter 9.2, and SHALL
lie within simulation noise of the book's simulated run expectancy matrix. The check SHALL run only when the data file is supplied.

#### Scenario: Printed values
- **WHEN** the chain is fitted on Retrosheet 2016 as the book describes
- **THEN** the empty-state transition to one out is 0.676 and to a runner on first with no outs is 0.235, and the expected plate appearances per half-inning are 4.27
