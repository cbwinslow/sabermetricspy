## ADDED Requirements

### Requirement: Extended Pythagorean head-to-head probability
The library SHALL provide a head-to-head home win probability that rescales the home team's runs scored and allowed by the opponent's relative to the league average, with the exponent supplied by the caller.

#### Scenario: League average cancels
- **WHEN** the probability is computed with any positive league average
- **THEN** it equals (RS_h RA_a)^g / ((RS_h RA_a)^g + (RA_h RS_a)^g)

#### Scenario: Average opponent
- **WHEN** the opponent scores and allows exactly the league average
- **THEN** the result equals the ordinary Pythagorean win probability
