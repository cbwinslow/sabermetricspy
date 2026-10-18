# park-factors Specification

## Purpose
TBD - created by archiving change park-factor-calculation. Update Purpose after archive.

## Requirements

### Requirement: Park factor calculation
The library SHALL provide functions that compute a raw park factor from home and road runs per game and team count, convert it to the composite (halved) factor, and regress it toward neutral by the number of seasons of data, following the FanGraphs Library method.

#### Scenario: Raw and composite factor
- **WHEN** home runs per game is 11, road runs per game is 10 and the league has 30 teams
- **THEN** the raw factor is 330/301 (about 1.096, which the source article rounds to 1.10) and the composite factor is (raw + 1)/2 (about 1.048, rounded to 1.05 in the article)

#### Scenario: Regression by years
- **WHEN** a composite factor of 1.25 is regressed using 1, 2, 3 and 4 seasons
- **THEN** the results are 1.15, 1.175, 1.20 and 1.225

### Requirement: Sourced bundled park table
The bundled park factor table SHALL contain all thirty teams for the stated season with values taken from FanGraphs Guts!, SHALL record its provenance, and SHALL be pinned by a golden fixture.

#### Scenario: Table equals the source
- **WHEN** the bundled table is compared with the recorded Guts! rows
- **THEN** every team's 5-year, 1-year and HR factors are equal

#### Scenario: Unknown park
- **WHEN** a park or team that is not in the table is requested
- **THEN** a neutral factor is returned and a warning says the park is not bundled
