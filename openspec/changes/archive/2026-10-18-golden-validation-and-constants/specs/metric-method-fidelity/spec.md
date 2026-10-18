# Spec Delta

## Purpose

Makes it visible to users which metrics follow the published method, which approximate it, and which differ, so results are never presented as the published figure when they are not.

## ADDED Requirements

### Requirement: Every metric declares its reference status
Every registered metric SHALL declare a reference status of matches-published-method, approximate, divergent, or unverified, and metrics that are not matching MUST state in their caveats how they differ from the published method.

#### Scenario: Metric with a documented difference
- **WHEN** a caller reads the spec for a metric whose status is approximate
- **THEN** the status is shown and the caveats describe the difference and name the source method

#### Scenario: Unlabeled metric
- **WHEN** a metric is registered without a reference status
- **THEN** it defaults to unverified and a guard test lists it

### Requirement: Methodology table
The repository SHALL contain a methodology document listing every registered metric with its source URL, formula source, and reference status, and a test MUST fail when the document and the registry disagree.

#### Scenario: Registry and document agree
- **WHEN** the registry and the methodology document are compared
- **THEN** each registered metric appears once with the same status

#### Scenario: Metric missing from the document
- **WHEN** a registered metric is absent from the methodology document
- **THEN** the consistency test fails and names it

### Requirement: Known approximations are labeled
The following SHALL be labeled approximate, divergent, or unverified with caveats naming the published method: pitcher WAR, position-player WAR, OPS+, ERA-/FIP-/xFIP- (and ERA+), kwERA, wSB, DER, Pythagenpat, SIERA, Marcel for pitchers, Speed Score, and the barrel zone. BaseRuns SHALL reproduce Smyth's published versions (multiplier 1.02 for basic columns, 1.1 when HBP, IBB, SB, CS or GDP are supplied).

#### Scenario: SIERA version
- **WHEN** the SIERA spec is read
- **THEN** it identifies the original 2010 Baseball Prospectus coefficients and states that FanGraphs published a revised 2011 version

#### Scenario: Pythagenpat exponent
- **WHEN** Pythagenpat is calculated without an exponent override
- **THEN** the default exponent and its source are stated, and an override accepts the alternative 0.285 or 0.287

#### Scenario: Pitcher WAR
- **WHEN** the pitcher WAR documentation is read
- **THEN** it states that the framework is not the FanGraphs or Baseball-Reference method and lists the differences

### Requirement: Verified metrics are recorded as such
Metrics verified against primary sources or published values (wOBA, wRAA, wRC, wRC+, BABIP, OBP, LOB%, DICE, technical Runs Created, hard-hit and sweet-spot thresholds, and the rates covered by golden fixtures) SHALL be recorded with a matches status and the verifying source. wSB (league constant unsourced) and kwERA (published variants differ) SHALL be recorded as approximate.

#### Scenario: Verified metric
- **WHEN** the methodology document lists wOBA
- **THEN** its status is matches and it links the FanGraphs Library page
