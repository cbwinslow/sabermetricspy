# Verification: what is confirmed, what is not, and why

This page explains how sabermetricspy decides a number is trustworthy, lists what has and has not been confirmed, and
keeps the research still to do. The per-metric detail (formula, source link, measured gap) is generated from
`src/sabermetricspy/data/methodology.yaml` into [METHODOLOGY.md](METHODOLOGY.md); sources and credits are in
[CREDITS.md](CREDITS.md). Counts below are for 1.0.2.

## The rule

A metric or model is shipped as supported only if it uses a widely documented method **and** reproduces a value that
someone else published, in a test (CLAUDE.md rule 7). Each item carries one status:

| Status | Meaning | Items (1.0.1) |
|---|---|---|
| `matches` | reproduces the published method and, where an outside number exists, that number | 110 of 137 metrics, 5 of 15 models |
| `approximate` | follows the published method but a measured gap remains, or the outside source is a black box | 24 metrics, 9 models |
| `experimental` | no consensus method or no reproducible outside value; warns every time it is used | 3 metrics, 1 model |

Each item also records how strong its evidence is: `golden` (a test compares it with a recorded outside value, 81
`matches`), `primary` (the formula was checked against the published definition text, 26) or `secondary` (a
reputable but non-primary description, 8). The 34 `primary`/`secondary` entries have **no outside number reproduced**;
they are listed under "Research still to do".

## Confirmed against outside values

- **Seasonal constants** (wOBA weights, run values, cFIP, league run environment, 1990-2025) equal both the FanGraphs
  Guts! snapshot and baseballr 2.0.0 `fg_guts()` for every bundled season (`tests/test_golden_baseballr.py`).
- **wOBA** equals baseballr `woba_plus()` on 8 lines; **FIP** equals baseballr `fip_plus()` on 8 lines (total walks
  passed, see ADR-0059) and FanGraphs FIP for 12 pitcher seasons.
- **Z-Swing% and Z-Contact%** equal FanGraphs' Statcast rates exactly on the recorded Skubal 2024 sample; on a second sample (Cole 2023) every zone rate is within 0.08 percentage points and Z-Contact% is exact again.
- **ERA+** equals Baseball-Reference for three pitchers (291, 188, 174) when given the pitcher's own league ERA and Baseball-Reference's pitching park factor (103, 107, 103), within park-factor rounding.
- **Whiff%** equals Savant's published value for three pitch types at its printed precision (27.7, 16.0, 46.4).
- **Markov transitions** (`fit_transitions`) reproduce every probability and expected-play figure printed in
  *Analyzing Baseball Data with R* from Retrosheet 2016; the count-expectancy, win-expectancy and player-id checks pass
  against the real data and the real Chadwick Register (run 2026-10-21).
- Batting, pitching and plate-discipline rates, wRC+, ERA, WHIP, K%/BB%, park factors and others: see METHODOLOGY.md.

## Approximate, and the measured gap

| Item | Gap against the outside value | Why |
|---|---|---|
| `ops_plus` | -1.2% to +1.5% on four Baseball-Reference seasons | B-Ref removes pitchers from the league average and park-adjusts it; we use MLB-wide averages and a caller park factor |
| `fip_minus` | 0.74 to 3.13 points (up to 6.6%) | FanGraphs' park input cannot be reconstructed from public data; a test bounds the gap at 3.2 |
| `xba`, `xslg`, `avg_ev` | -.0015, -.0024, -0.53 mph | Savant's model is unpublished; we sum its own per-pitch estimates |
| `o_swing_pct`, `o_contact_pct`, `zone_pct`, `swing_pct`, `contact_pct`, `swstr_pct`, `csw_pct` | 0.02 to 0.12 percentage points (one pitch) | cause of the single pitch unknown; FanGraphs' zone rule is unpublished (we infer it) |
| `rew`, pitcher WAR | median 1.2% / 0.08 WAR | FanGraphs' conversion and replacement inputs are not fully published |
| position-player WAR default | +2.2 runs (0.22 WAR) per 704 PA | flat 20 runs per 600 PA unless `league_pa` is passed |
| `MarkovChainModel` (rule-based `fit`) | up to 3.7% at bases loaded | advancement rules are this library's own |
| `LinearWeightsEstimator` | -0.001 to +0.031 per weight; scale 1.251 vs 1.212 (Retrosheet 2016) | FanGraphs' RE24 and event definitions are not fully published |
| `bsr`, `der`, `pu_pct`, `xbt_pct`, `xbh_pct`, `vaa`, `MonteCarloSimulator`, Marcel | no outside value reproduced yet | see below |

## Experimental (warns on use)

`siera` (published coefficient sets differ and FanGraphs' per-year coefficient is unpublished), `rc27` (the out
estimate is unsourced), `xfip_minus` (no published value), `WinProbabilityModel` (mean error 0.048 against Tango's
table; use `WinExpectancyMatrix`). Removed outright in 1.0.1 because they have no published method: `total_break`,
`whiff_per_100` (just 100 x SwStr%), `two_strike_chase_pct`, `wgdp` (BsR now takes wGDP as an input).

## Checked on 2026-10-21 for this release

Read: FanGraphs Library (plate discipline, BsR, SIERA), Baseball-Reference batting glossary and the Bonds, McGwire
and Judge pages, Baseball Prospectus SIERA part 5 (via search), baseballr 2.0.0 on R 4.6.1, the FanGraphs leaders API.
Corrections found: an earlier review quoted Judge's 2022 OPS+ as 211 (it is 210), and the FanGraphs plate-discipline
page does not define the zone geometrically (our rule is inferred from its counts, not published).
Could not read: Savant's glossary (HTTP 406), the Baseball-Reference pitching glossary (no ERA+ text), the FanGraphs
position-player WAR page (404).

## Research still to do

1. Savant's own Whiff% definition text: its glossary page renders client-side and cannot be fetched; secondary sources (MLB.com articles, third-party glossaries) agree it is swings-and-misses over swings, and the foul-tip/bunt counting is confirmed numerically only.
2. Done 2026-10-21: the geometric strike zone holds on a second pitcher and season (Cole 2023, within 0.08 points). A left-handed pitcher and a hitter sample would widen it further.
3. FanGraphs' park input for FIP- (ERA+ is resolved: Baseball-Reference's pitching park factors and own-league ERA reproduce it).
4. SIERA: the FanGraphs 2011 coefficients and per-year constants, then a leaderboard check.
5. BsR: a leaderboard row with wSB, UBR, wGDP and BsR (the API's `wBsR`/`BaseRunning`/`GDPRuns` fields are ambiguous); wGDP constants.
6. DER (reached-on-error treatment, a published team value), XBT%, XBH%, popup rate, VAA: find published references.
7. Done 2026-10-21 for LinearWeightsEstimator: on Retrosheet 2016 the weights are within 0.001 to 0.031 of Guts! (scale 1.251 vs 1.212), so it stays approximate; the remaining gap needs FanGraphs' unpublished RE24 and event definitions. Still open: MonteCarloSimulator on the fitted matrix; Marcel pitcher regression amounts and Tango's published files.
8. Bundle league PA and games per season so the position-player WAR default uses the FanGraphs replacement formula; add the 2026 constants.
9. Outside numbers for the 34 formula-only `matches`: ip, ubb, xbh, rc_basic, rc_tech, base_runs, qera, seca, gpa, ta, off, dice, xfip, dips_bop_pct, k_minus_bb_pct, k_to_bb, bf_per_ip, cg_pct, qs_pct, sv_pct, shutdown, meltdown, game_score_v2, speed_score, err_pct, ra9, pit_bb_to_k, avg_extension, bauer_units, effective_velo, sweet_spot_pct, Log5Model (and its extended Pythagorean form), EmpiricalBayesShrinker.
10. Most golden fixtures come from a few players and seasons (Skubal 2024, 2001 pitchers); widen them.
