# Spec Delta

## ADDED Requirements

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
