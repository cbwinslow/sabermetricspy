# Specification: Methodology Status

## ADDED Requirements

### Requirement: Experimental Items Warn
Metrics and models with no consensus method or no reproducible outside value SHALL carry the `experimental` status and SHALL emit a `UserWarning` each time they are calculated or constructed.

#### Scenario: Calculating an experimental metric
- **WHEN** `calculate` is asked for `rc27`
- **THEN** a `UserWarning` naming `rc27` and the reason is emitted and the value is still returned.

### Requirement: Documented Divergences Are Bounded
A fixture entry that documents a divergence from an outside value SHALL still fail its test if the gap exceeds the measured bound.

#### Scenario: FIP- gap grows
- **GIVEN** a FIP- gap of more than 3.2 points on a recorded pitcher
- **WHEN** the golden tests run
- **THEN** the bound test fails.

### Requirement: Statcast Zone And Whiff Conventions
When pitch geometry is present the zone rates SHALL use the ball-touches-the-zone rule; Whiff% SHALL count foul tips as whiffs and bunt attempts as swings.

#### Scenario: Whiff% against Savant
- **GIVEN** the recorded Skubal 2024 sample
- **WHEN** Whiff% is calculated per pitch type
- **THEN** four-seam, sinker and changeup equal 27.7, 16.0 and 46.4 at one decimal.
