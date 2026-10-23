# pythagenport-winning-pct Specification

## Purpose
Provide Davenport and Woolner's Pythagenport expected winning percentage, utilizing a dynamic base-10 logarithmic run-environment exponent.

## ADDED Requirements

### Requirement: Pythagenport Winning Percentage Calculation
The library SHALL provide Pythagenport Winning Percentage, evaluating $\gamma = 1.50 \log_{10}(\text{RPG}) + 0.45$ where $\text{RPG} = (RS + RA) / G$, and returning null when $G=0$ or $\text{RPG} \le 0$.

#### Scenario: 1998 Yankees tie-out
- **WHEN** 1998 Yankees counts are evaluated (RS 965, RA 656, 114 W, 48 L)
- **THEN** Pythagenport expected win percentage is approximately 0.680

#### Scenario: Equal runs scored and allowed
- **WHEN** runs scored equal runs allowed with positive games played
- **THEN** Pythagenport expected winning percentage equals 0.500 exactly

#### Scenario: Zero games played safety
- **WHEN** total games (W + L) is zero
- **THEN** Pythagenport expected winning percentage evaluates to null
