# glicko2-rating Specification

## Purpose
TBD - created by archiving change add-published-methods-round-2. Update Purpose after archive.

## Requirements

### Requirement: Glicko-2 rating update
The library SHALL provide the Glicko-2 update for one player and one rating period, with tau supplied by the caller and no home-field term.

#### Scenario: Worked example
- **WHEN** a 1500/RD 200/volatility 0.06 player with tau 0.5 beats 1400/RD 30 and loses to 1550/RD 100 and 1700/RD 300
- **THEN** the new rating is 1464.06, RD 151.52 and volatility 0.05999 within the printed rounding

#### Scenario: No games
- **WHEN** the period has no games
- **THEN** only the rating deviation grows
