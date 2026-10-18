# Spec Delta

## Purpose

Fixes the definitions of metrics where an implementation choice changes published results, so sabermetricspy follows the method the major sources use.

## ADDED Requirements

### Requirement: FIP and xFIP count total walks
FIP and xFIP SHALL use total walks including intentional walks plus hit batters, as FanGraphs does, and the same walk term MUST be used when deriving the FIP constant and the FIP- and xFIP- metrics.

#### Scenario: Pitcher with intentional walks
- **WHEN** FIP is calculated for a pitcher with HR 20, BB 27, IBB 10, HBP 7, SO 173 over 233.0 IP using the 2001 constant 3.049
- **THEN** the result is 3.1177 within the fixture tolerance, and excluding IBB from the walk term is not used

#### Scenario: Pitcher without intentional walks
- **WHEN** a pitcher has no intentional walks
- **THEN** FIP is identical whether or not the IBB column is present

### Requirement: xFIP requires a sourced league HR/FB
xFIP SHALL be computed from the season's sourced league HR/FB rate and SHALL evaluate to null when that rate is not available for the season.

#### Scenario: Season without a published rate
- **WHEN** xFIP is requested for a season with no sourced league HR/FB rate
- **THEN** the result is null for every row and no default rate is applied

#### Scenario: Season with a published rate
- **WHEN** xFIP is requested for a season with a sourced rate
- **THEN** expected home runs equal fly balls times that rate

### Requirement: wRC+ uses the non-pitcher league run environment
wRC+ SHALL divide the park- and league-adjusted runs per PA by the league wRC/PA excluding pitchers when that constant is available, and SHALL otherwise divide by league R/PA and carry a caveat saying so.

#### Scenario: Constant available
- **WHEN** wRC+ is calculated for Barry Bonds 2001 with the sourced non-pitcher league wRC/PA and the published park factor
- **THEN** the result equals the published wRC+ within tolerance

#### Scenario: Constant absent
- **WHEN** wRC+ is calculated for a season without the constant
- **THEN** the result uses league R/PA and the metric's caveat states the fallback

### Requirement: Speed Score follows Bill James's four-factor definition
Speed Score SHALL average four factors, each limited to the range 0 to 10: stolen-base percentage `20*((SB+3)/(SB+CS+7)-0.4)`, attempt frequency `sqrt((SB+CS)/(1B+BB+HBP))/0.07`, triples rate `(3B/(AB-HR-SO))/0.0016`, and runs scored `25*((R-HR)/(H+BB+HBP-HR)-0.1)`.

#### Scenario: Factors are clamped
- **WHEN** a factor falls below 0 or above 10
- **THEN** it is limited to 0 or 10 before averaging

#### Scenario: Hand-computed example
- **WHEN** Speed Score is calculated for SB 10, CS 2, 1B 100, BB 60, HBP 4, 3B 5, HR 20, AB 500, SO 100, H 150, R 90
- **THEN** the result equals the average of the four published factor values

#### Scenario: Missing strikeout column
- **WHEN** the strikeout column is absent
- **THEN** the calculation reports the missing required column instead of silently omitting strikeouts

### Requirement: Park factor is explicit
Metrics that adjust for park SHALL document that a park factor of 100 means no adjustment, and the documentation and examples MUST show how to supply the published park factor.

#### Scenario: Default park factor
- **WHEN** a park-adjusted metric is calculated without a supplied park factor
- **THEN** no park adjustment is applied and the metric's caveat or documentation says so
