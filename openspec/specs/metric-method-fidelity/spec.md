# metric-method-fidelity Specification

## Purpose
Makes it visible to users which metrics follow the published method, which approximate it, and which differ, so results are never presented as the published figure when they are not.

## Requirements

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

### Requirement: Built-in metrics are audited
Every built-in metric SHALL have an audited status of matches, approximate, or divergent, and a built-in metric MUST NOT remain unverified; custom and plugin metrics may still default to unverified.

#### Scenario: Guard against unaudited built-ins
- **WHEN** a built-in metric has the unverified status
- **THEN** a guard test fails and names it

#### Scenario: Custom metric unaffected
- **WHEN** a user registers a custom metric without a status
- **THEN** it registers with the unverified status and the guard test does not fail

### Requirement: Every audited status records its evidence
Each audit entry SHALL record an evidence tier of golden (a published value reproduced from raw inputs), primary (a formula or definition confirmed in a primary source), or secondary (confirmed only by secondary sources), and SHALL record the source URL.

#### Scenario: Golden evidence
- **WHEN** an entry has the golden tier
- **THEN** a golden fixture entry exists for that metric

#### Scenario: Secondary evidence is visible
- **WHEN** an entry rests only on secondary sources
- **THEN** the methodology table shows the secondary tier so readers can weigh it

#### Scenario: Missing evidence tier
- **WHEN** an audit entry has no evidence tier
- **THEN** the consistency test fails and names it

### Requirement: Models without a published reference are explained
A non-metric model SHALL be left unverified only when its audit entry states that no published reference table or formula exists to compare against, and otherwise it MUST be audited.

#### Scenario: Unverified model with a reason
- **WHEN** a model entry is unverified
- **THEN** its note states why no published reference exists

#### Scenario: Unverified model without a reason
- **WHEN** a model entry is unverified and its note gives no such reason
- **THEN** the consistency test fails and names it

### Requirement: Defects found by the audit are fixed or labeled
When an audit finds that a formula differs from its published definition, the metric SHALL either be corrected and the numeric change recorded with before and after values, or be labeled approximate or divergent with a caveat naming the published method; a difference MUST NOT be left unlabeled.

#### Scenario: Clear formula defect
- **WHEN** the audit shows a metric's formula contradicts its primary-source definition
- **THEN** the formula is corrected, a test asserts the published value, and the decision record lists the old and new values

#### Scenario: Source-dependent method
- **WHEN** reputable sources define the metric differently
- **THEN** the metric is labeled approximate with a caveat naming the variants and the one implemented
