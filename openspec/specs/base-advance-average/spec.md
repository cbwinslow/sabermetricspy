# base-advance-average Specification

## Purpose
TBD - created by archiving change base-advance-average. Update Purpose after archive.

## Requirements

### Requirement: Base-Advance Average
The library SHALL provide `base_advance_average`, total bases advanced divided by total base-advance opportunities, and a helper that derives both per plate appearance from base states before and after and the runs on the play.

#### Scenario: Published sample inning
- **WHEN** the eight plate appearances of the paper's sample half-inning are evaluated
- **THEN** each row's bases advanced and opportunities equal the paper's, and the inning totals 14 over 57

#### Scenario: Erased runner
- **WHEN** a runner on third is thrown out at home while the batter reaches first and the runner on second moves to third
- **THEN** the play counts -1 bases over 7 opportunities
