# component-era Specification

## Purpose
Provide Bill James's Component ERA (ERC), estimating earned run average from pitching component events ($H, HR, BB, HBP, IBB, BF, Outs$) without sequencing noise.

## Requirements

### Requirement: Component ERA Calculation
The library SHALL provide Component ERA (ERC), evaluated from pitching counting events with a continuous piecewise spline at raw threshold 2.24.

#### Scenario: Standard pitching line with IBB
- **WHEN** valid pitching counts ($H, HR, BB, HBP, IBB, BF, Outs$) are provided
- **THEN** ERC evaluates the 0.56 walk-weight formula and scales according to raw threshold 2.24

#### Scenario: Fallback when IBB is unavailable
- **WHEN** intentional walks ($IBB$) are missing from the inputs
- **THEN** ERC falls back to the 0.475 walk-weight formula

#### Scenario: Zero denominator safety
- **WHEN** batters faced or outs equal zero
- **THEN** ERC evaluates to null
