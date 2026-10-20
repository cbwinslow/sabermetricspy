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
- `sabermetricspy.ids`: Chadwick Register player-id crosswalk (`translate_ids`, `find_players`, `player_id`, `load_register`, `download_register`), validated against Savant, Baseball-Reference and FanGraphs pages and the Retrosheet 2016 file (ADR-0054).
- `MarkovChainModel.fit_transitions` and `state_distribution`: the chain fitted from play-by-play, matching the printed values in Analyzing Baseball Data with R (ADR-0053).
- `WinExpectancyMatrix`: win expectancy fitted from play-by-play, checked against Tango's table (ADR-0052).
- LICENSE (Apache-2.0), NOTICE, CITATION.cff, `docs/CREDITS.md`, and a CI workflow.
