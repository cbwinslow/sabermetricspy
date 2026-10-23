# estimated-runs-produced Specification

## Purpose
Provide Paul Johnson's Estimated Runs Produced (ERP) linear-weights estimator for offensive run evaluation.

## ADDED Requirements

### Requirement: Estimated Runs Produced
The library SHALL provide Johnson's ERP formula (TB, BB, HBP, H, SB, AB, CS, GIDP) with absent optional columns defaulting to 0, matching the linear expansion coefficients.

#### Scenario: Linearity with counting stats
- **WHEN** counting statistics are evaluated
- **THEN** ERP matches the algebraic expansion (0.48*1B + 0.80*2B + 1.12*3B + 1.44*HR + 0.32*(BB+HBP) + 0.16*SB - 0.0968*(AB+CS+GIDP-H)) within 1e-9

#### Scenario: Missing optional columns
- **WHEN** optional columns cs, gidp, hbp, sb are missing
- **THEN** ERP evaluates safely with them treated as 0
