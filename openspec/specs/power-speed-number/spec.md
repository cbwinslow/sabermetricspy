# power-speed-number Specification

## Purpose
Provide Bill James's Power-Speed Number metric for assessing the balance and magnitude of a player's home run and stolen base production.

## Requirements

### Requirement: Power-Speed Number
The library SHALL provide the Power-Speed Number, the harmonic mean 2*HR*SB/(HR+SB) of home runs and stolen bases, computed from summed counts and null when HR + SB is 0.

#### Scenario: Published career value
- **WHEN** Bonds with 762 HR and 514 SB
- **THEN** the value is 613.90 within 0.005

#### Scenario: No home runs or steals
- **WHEN** HR and SB are both 0
- **THEN** the value is null
