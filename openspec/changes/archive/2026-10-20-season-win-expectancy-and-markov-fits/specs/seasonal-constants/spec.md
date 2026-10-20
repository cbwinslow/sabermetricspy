# Spec Delta

## ADDED Requirements

### Requirement: Season constants follow the data
When the caller supplies neither a context nor a season, the library SHALL use the single season found in the frame's
`season` column, and SHALL use the bundled default season only when the frame has no season column. For metrics that read
season constants, a frame whose single season differs from the supplied context or season SHALL raise an error naming
both seasons, and a call with no season from the caller or the data SHALL emit a `UserWarning` naming the default season.
Metrics that read no season constants SHALL be unaffected.

#### Scenario: Frame names its season
- **WHEN** a frame holding only season 2001 is calculated for wRC+ with no context
- **THEN** the 2001 constants are used and the result's context reports season 2001

#### Scenario: Frame contradicts the context
- **WHEN** a frame holding only season 2001 is calculated for wRC+ with a context or season of 2024
- **THEN** the call raises an error naming both seasons

#### Scenario: No season anywhere
- **WHEN** a frame has no season column and no season or context is given for wRC+
- **THEN** a `UserWarning` says the default season constants were used, and AVG on the same frame emits no warning
