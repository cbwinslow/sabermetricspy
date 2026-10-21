# ADR-0064: The 1.1.0 Outside Tie-Out Audit

Status: Accepted

## Context
After 1.0.3 the remaining weak items were those with no reproduced outside value (CLAUDE.md rule 7). A research pass on 2026-10-21 (Tango's site and files, FanGraphs, Baseball-Reference, Baseball Savant, baseballr, MLB's glossary) looked for a formula, its constants and a published value for each. baseballr turned out to hold little to port: its computing functions are `woba_plus`, `fip_plus` and `fg_guts` (already tied out), `run_expectancy_code` (a Statcast-specific pipeline), `code_barrel` (a four-line rule that overcounts Savant's barrels by 1 to 4) and the edge-zone helpers, so Tango's published tables served as the reference instead.

## Decision
- **Removed:** `WinProbabilityModel` (its variance factor and tie edge have no source; mean error 0.048 against Tango) and `xbh_pct` (no published statistic has that name and the two usages conflict).
- **Fixed to the documented method:** position-player WAR replacement (FanGraphs formula with bundled MLB games and plate appearances per season; the flat 20 runs per 600 PA was not a FanGraphs constant), SIERA (FanGraphs' 2011 version, netGB = GB - FB, starter term, per-season constants measured from the leaderboard), FIP- and xFIP- (the pitcher's own league constant), DER (MLB glossary formula with reached-on-error), Log5 (Tango's multiplicative home advantage).
- **Newly pinned to outside values:** popup rate (Savant), XBT% (all 30 Baseball-Reference teams), VAA (two published values), Runs Created (Baseball-Reference), Marcel (Tango's published 2004 files), Empirical Bayes (Robinson's printed estimates).
- **Added:** `MarkovWinExpectancy`, Tango's recursive win expectancy built from observed base-out transitions (mean error 0.0043 against 198 cells of his 2010-2015 table on Retrosheet 2016).
- **Held `experimental`:** `bsr`, `speed_score`, `qera`, `der`, the rule-based `MarkovChainModel.fit`, `MonteCarloSimulator` and `Log5Model.extended_pythagorean_home_win_prob`, each until a published value is reproduced.
- Measured, not documented, parts are labeled as such in `docs/METHODOLOGY.md`: SIERA's (BB/PA)^2 coefficient (25.264 against the published 27.252) and per-season constants, the league constant and no-park-term behaviour of xFIP-, and the pitcher regression of 266.67 IP for Marcel.

## Alternatives
- Port baseballr's `code_barrel` and `run_expectancy_code`, not chosen now because the first misses Savant's own barrel label and the second imports Statcast text-parsing quirks; revisit if baseballr publishes reference outputs for them.
- Keep the flat 20 runs per 600 PA default, not chosen now because FanGraphs' formula gives 16.95 to 19.54; revisit only as an explicit option, which it remains (`replacement_runs_per_600_pa`).
- Quote the published SIERA bb^2 coefficient, not chosen now because it leaves errors up to 0.06 against FanGraphs; revisit if FanGraphs publishes its production coefficients.
- Keep `WinProbabilityModel` as experimental, not chosen now because a sourced replacement now exists; revisit if a published method for a closed-form win probability appears.

## Consequences
Results change for `siera`, `fip_minus`, `xfip_minus`, `der`, position-player WAR defaults and `Log5Model.team_matchup_prob` (`home_edge` became `home_advantage`). `siera` now needs `start_outs` (or `start_ip`), and `der` needs `roe`.
