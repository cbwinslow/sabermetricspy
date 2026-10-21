# Specification: Methodology Status

## ADDED Requirements

### Requirement: ERA+ Uses The Pitcher's League
ERA+ SHALL divide the AL or NL league ERA when `SeasonContext.league` names a league, and the MLB-wide ERA otherwise.

#### Scenario: Baseball-Reference ERA+
- **GIVEN** the pitcher's league and Baseball-Reference's pitching park factor
- **WHEN** ERA+ is calculated for Pedro Martinez 2000, Randy Johnson 2001 and Tarik Skubal 2024
- **THEN** the results are within 1% of 291, 188 and 174.
