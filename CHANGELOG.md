# Changelog

Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/). Design reasons are in `docs/DECISIONS.md`.

## [Unreleased]

## [1.0.1] - 2026-10-21

### Added
- `ReferenceStatus.EXPERIMENTAL`: `siera`, `rc27`, `xfip_minus` and `WinProbabilityModel` warn every time they are used (ADR-0061).
- `docs/VERIFICATION.md`: what is confirmed, the measured gap of every approximate item, and the research still to do.
- Baseball-Reference OPS+ check for four seasons (`tests/golden/ops_plus.yaml`); a bound test so documented divergences cannot grow.

### Changed
- Z-Swing%, Z-Contact%, Zone% and the other Statcast zone rates use the geometric strike zone when pitch geometry is present; Z-Swing% and Z-Contact% now equal FanGraphs exactly (ADR-0062).
- Whiff% counts foul tips as whiffs and bunt attempts as swings, as Savant does; it now equals Savant's published values (ADR-0062).
- `bsr` takes `ubr` and `wgdp` as input columns (FanGraphs: BsR = wSB + UBR + wGDP).
- `MarkovChainModel.fit_transitions` is `matches` after its Retrosheet 2016 check was run and passed.

### Removed
- `total_break`, `whiff_per_100`, `two_strike_chase_pct` and `wgdp` (no published method or constants), and the `lg_gidp_rate` / `r_gidp` context fields.

## [1.0.0] - 2026-10-21

### Changed
- Polars evaluation builds one lazy plan: 30 metrics on a 120,000-row, 98-column frame take 0.44 s instead of 8.7 s (ADR-0057).
- Backend matrix test: every registered metric, the expectancy models, shrinkage, projection and rolling agree across Polars, LazyFrame, pandas, PyArrow and DuckDB; DuckDB input is now evaluated on Polars, so 141 metrics take 0.5 s instead of minutes (ADR-0056).
- Season detection runs on every backend (DuckDB crashed), `translate_ids` preserves the caller's frame and matches ids exactly, the register records its commit and fetch date (`release` is replaced by `fetched_on` and `commit`), fits validate input (ADR-0055).
- Season constants follow the data: `season` defaults to `None`, a single-season frame uses its own season, a frame
  that contradicts the context raises, and the 2024 fallback warns (ADR-0051).
- Plate-discipline rates follow their published definitions (ADR-0050).
- Count run values follow Walsh; RE288 is fitted, not defaulted (ADR-0049).
- The Empirical Bayes prior is fitted by maximum likelihood (ADR-0048).

### Removed
- Multi-source name register (ADR-0058, withdrawn).
- Models and metrics with no public method: Stuff+, expected outcomes, catcher framing, OAA, xERA (ADR-0047).

### Added
- Outside tie-outs against baseballr 2.0.0: constants, wOBA and FIP (ADR-0059).
- The default Chadwick Register updates itself: `load_register()` downloads it when missing and re-downloads it when upstream has a newer commit (checked at most once a day, offline-safe, switch off with `SABERMETRICSPY_AUTO_UPDATE=0`); `update_register()` does the same on request; downloads are atomic.
- `sabermetricspy.ids`: Chadwick Register player-id crosswalk (`translate_ids`, `find_players`, `player_id`, `load_register`, `download_register`, `update_register`), validated against Savant, Baseball-Reference and FanGraphs pages and the Retrosheet 2016 file (ADR-0054).
- `MarkovChainModel.fit_transitions` and `state_distribution`: the chain fitted from play-by-play, matching the printed values in Analyzing Baseball Data with R (ADR-0053).
- `WinExpectancyMatrix`: win expectancy fitted from play-by-play, checked against Tango's table (ADR-0052).
- LICENSE (Apache-2.0), NOTICE, CITATION.cff, `docs/CREDITS.md`, and a CI workflow.
