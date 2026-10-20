# Changelog

Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/). Design reasons are in `docs/DECISIONS.md`.

## [Unreleased]

### Changed
- Season constants follow the data: `season` defaults to `None`, a single-season frame uses its own season, a frame
  that contradicts the context raises, and the 2024 fallback warns (ADR-0051).
- Plate-discipline rates follow their published definitions (ADR-0050).
- Count run values follow Walsh; RE288 is fitted, not defaulted (ADR-0049).
- The Empirical Bayes prior is fitted by maximum likelihood (ADR-0048).

### Removed
- Models and metrics with no public method: Stuff+, expected outcomes, catcher framing, OAA, xERA (ADR-0047).

### Added
- LICENSE (Apache-2.0), NOTICE, CITATION.cff, `docs/CREDITS.md`, and a CI workflow.
