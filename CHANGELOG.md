# Changelog

Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/). Design reasons are in `docs/DECISIONS.md`.

## [Unreleased]

## [1.2.0] - 2026-10-21

### Added
- Golden tests: xFIP (138 FanGraphs pitcher-seasons), Game Score 2.0, Shutdown and Meltdown (FanGraphs game logs), pitcher WAR (1,477 leaderboard pitcher-seasons). `game_score_v2` is now `approximate` (one point off FanGraphs on 34 of 55 starts); `xfip`, `shutdown` and `meltdown` are tied to FanGraphs values.
- `get_fip_park_factor(team, season)` and `data/constants/park_fip.yaml`: FanGraphs' FIP park factor for 1990-2026, the park input of FIP-. With it the older FIP- fixtures (Johnson, Schilling, Mussina, Maddux, Morris, Martinez, Skubal) are within 0.25 points.

### Explained
- Three gaps recorded in 1.1.0 now have causes: FanGraphs computes the 2020 league adjustment from MLB-wide components, divides 2000 WAR by 10.689 while its replacement term uses 10.795, and its own 1998 totals give the bundled runs per win (the published Guts figure is the outlier). BsR's leaderboard total still does not equal its listed parts (standard deviation 1.7 runs in 2016 and 2024).

## [1.1.0] - 2026-10-21

Outside tie-out audit (ADR-0064).

### Removed
- `WinProbabilityModel` (and its leverage index) and `xbh_pct`: no published method or value.

### Changed
- Position-player WAR uses the FanGraphs replacement formula with bundled per-season MLB games and plate appearances (`data/constants/league_war.yaml`); the flat 20 runs per 600 PA default is gone (`replacement_runs_per_600_pa` is still available).
- `siera` is FanGraphs' 2011 version (netGB = GB - FB, starter-innings term, measured per-season constants; needs `start_outs` or `start_ip`). `fip_minus` and `xfip_minus` use the pitcher's own league constant; `xfip_minus` has no park term.
- `der` is the MLB glossary formula and needs `roe`. `Log5Model.team_matchup_prob` takes `home_advantage` (Tango's multiplicative form) instead of `home_edge`.
- `MarcelProjector` adds `proj_reliability` and `MarcelProjector.for_pitchers`; `EmpiricalBayesShrinker` accepts an explicit `prior`.
- `bsr`, `speed_score`, `qera`, `der`, the rule-based `MarkovChainModel.fit`, `MonteCarloSimulator` and `extended_pythagorean_home_win_prob` are `experimental` (warn on use) until a published value is reproduced. `pu_pct` and `xbt_pct` are `matches`.

### Added
- `MarkovWinExpectancy`: Tango's recursive win expectancy from observed transitions.
- Golden tests against Savant (popups, barrels), Baseball-Reference (XBT%, Runs Created), FanGraphs (SIERA, FIP-, xFIP-, position-player WAR), Tango's published 2004 Marcel files and Robinson's empirical Bayes estimates.

## [1.0.3] - 2026-10-21

### Added
- 2026 seasonal constants (wOBA weights, cFIP, league run environment, AL/NL splits, wSB, kwERA constant, pitcher-WAR totals). The Guts! weights equal baseballr 2.0.0 `fg_guts()` and a second scraped copy of Guts!; the golden snapshots now cover 1990-2026.
- `docs/VERIFICATION.md` lists the outside data sources surveyed (baseballr, SportsDataverse, sportsdataverse-py) and what each can and cannot confirm; a Retrosheet 2016 RE24 matrix agrees with SportsDataverse's within 0.043 runs.

## [1.0.2] - 2026-10-21

### Changed
- `era_plus` uses the pitcher's own league ERA (`SeasonContext.league`) and now reproduces Baseball-Reference's 291 / 188 / 174 with its pitching park factors; status `matches` (ADR-0063).

### Added
- Second strike-zone sample (Gerrit Cole 2023) confirms the geometric zone: every rate within 0.08 percentage points of FanGraphs (`tests/test_golden_strike_zone_second_sample.py`).
- Opt-in `tests/test_retrosheet_2016_linear_weights.py`: `LinearWeightsEstimator` is within 0.001 to 0.031 of the Guts! 2016 weights.

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
