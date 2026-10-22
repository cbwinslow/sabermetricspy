# Verification: what is confirmed, what is not, and why

This page explains how sabermetricspy decides a number is trustworthy, lists what has and has not been confirmed, and
keeps the research still to do. The per-metric detail (formula, source link, measured gap) is generated from
`src/sabermetricspy/data/methodology.yaml` into [METHODOLOGY.md](METHODOLOGY.md); sources and credits are in
[CREDITS.md](CREDITS.md). Counts below are for 1.4.0 (ADR-0065). Since 2.0.0 the constants described below as bundled are supplied by the caller (ADR-0068); the checks still run on the maintainer's local copy.

## The rule

A metric or model is shipped as supported only if it uses a widely documented method **and** reproduces a value that
someone else published, in a test (CLAUDE.md rule 7). Each item carries one status:

| Status | Meaning | Items (1.4.1) |
|---|---|---|
| `matches` | reproduces the published method and, where an outside number exists, that number | 108 of 133 metrics, 4 of 12 models |
| `approximate` | follows the published method but a measured gap remains, or the outside source is a black box | 24 metrics, 8 models |
| `experimental` | no consensus method or no reproducible outside value; warns every time it is used | 1 metric, 0 models |

Each item also records how strong its evidence is: `golden` (a test compares it with a recorded outside value, 87
`matches` metrics), `primary` (the formula was checked against the published definition text, 14) or `secondary` (a
reputable but non-primary description, 7). The 21 `primary`/`secondary` entries have **no outside number reproduced**;
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
- **Added in 1.1.0 (2026-10-21):** popup rate equals Savant's `pu_rate` for four hitters; XBT% equals Baseball-Reference's printed team value for all 30 teams (2025); Runs Created equals Baseball-Reference for its 2024 top five (technical) and Cobb and Jackson 1911 (basic); Marcel hitters match Tango's published 2004 file (839 hitters: playing time and reliability to rounding, home runs 0.28 off on average) and pitcher reliability matches for every one of 873 pitchers; Log5 reproduces Tango's .692, .308 and .371 examples; Empirical Bayes reproduces ten of Robinson's printed estimates with his prior; position-player WAR replacement and WAR equal FanGraphs leaderboard rows for 2013 and 2025 (within 0.002 runs and 0.0005 WAR); `MarkovWinExpectancy` is 0.0043 from 198 cells of Tango's win expectancy table (mean) and 0.0172 at most.
- Batting, pitching and plate-discipline rates, wRC+, ERA, WHIP, K%/BB%, park factors and others: see METHODOLOGY.md.

## Approximate, and the measured gap

| Item | Gap against the outside value | Why |
|---|---|---|
| `ops_plus` | -1.2% to +1.5% on four Baseball-Reference seasons | B-Ref removes pitchers from the league average and park-adjusts it; we use MLB-wide averages and a caller park factor |
| `fip_minus` | mean 0.19, largest 0.53 points on 32 pitcher-seasons (2011, 2019, 2024, 2025); the 2000, 2001 and 2024 fixtures within 0.25 | the league constant and the FIP park column (bundled for 1990-2026) fixed the old gap; the park column is a whole number, which alone moves FIP- by up to 0.6 |
| `siera` | within 0.007 of FanGraphs over 8,042 pitcher-seasons (mean 0.0005) | the (BB/PA)^2 coefficient (25.264, published 27.252) and per-season constants are measured from the leaderboard, not published |
| `xba`, `xslg`, `avg_ev` | -.0015, -.0024, -0.53 mph | Savant's model is unpublished; we sum its own per-pitch estimates |
| `o_swing_pct`, `o_contact_pct`, `zone_pct`, `swing_pct`, `contact_pct`, `swstr_pct`, `csw_pct` | 0.02 to 0.12 percentage points (one pitch) | cause of the single pitch unknown; FanGraphs' zone rule is unpublished (we infer it) |
| `rew` | median 1.2% | FanGraphs' conversion inputs are not fully published |
| pitcher WAR | median absolute error 0.047 to 0.098 WAR by season, 86 to 97 percent within 0.25 WAR (1,477 pitcher-seasons, 2016, 2019, 2022, 2024, 2025) | FanGraphs values a pitcher's starts and relief innings separately, its park factor is unrounded, and its league correction is published for 2016 only |
| `game_score_v2` | one point lower than FanGraphs on 34 of 55 starts, equal on 21 | no rule found for the point |
| position-player WAR | replacement within 0.002 runs and WAR within 0.0005 of FanGraphs rows (2013, 2025) | positional adjustment is PA/600 unless innings are given; fielding, UBR and the league adjustment are caller inputs. FanGraphs computes the 2020 league adjustment from MLB-wide components (not AL/NL; explained 2026-10-21), and divides 2000 WAR by 10.689 where its replacement term uses 10.795; bundled runs per win differs from Guts by 0.009 in 1998 although FanGraphs' own 1998 totals give the bundled value |
| `MarkovWinExpectancy` | mean 0.0043, largest 0.0172 against 198 cells of Tango's table | one Retrosheet season (2016) against his 2010-2015 |
| Marcel (hitters, pitchers) | hitter home runs 0.28 off on average; pitcher innings for single-role pitchers within 1 IP for over 80% | Tango's rebaseline step is undefined; the pitcher regression (266.67 IP) is inferred from his reliability column |
| `vaa` | Woo -3.703 against -3.7; Ryan -3.847 against -3.9 | third-party published values; Savant does not publish VAA |
| `LinearWeightsEstimator` | -0.001 to +0.031 per weight; scale 1.251 vs 1.212 (Retrosheet 2016) | FanGraphs' RE24 and event definitions are not fully published |
| `haa`, `xbh` and the 21 formula-only `matches` | no outside number reproduced | see below |

## Experimental (warns on use)

`bsr` only: wSB matches FanGraphs but no BsR total does (on the leaderboard the BaseRunning column is not the sum of its
wBsR, UBR and GDPRuns fields, SD 1.9 runs, unexplained; FanGraphs' Offense is exactly Batting plus BaseRunning, so BaseRunning is the total it uses). `off` depends on it. Removed outright in 1.4.0 because no published
value or documented method could be found: `rc27` (no source states its out count), `qera` (formula printed by
Baseball Prospectus, values paywalled, superseded by SIERA), `speed_score` (neither published form reproduces
FanGraphs' Spd), the rule-based `MarkovChainModel.fit` and `MonteCarloSimulator` (library-chosen advancement rules;
`MarkovChainModel.fit_transitions` from play-by-play stays), and `Log5Model.extended_pythagorean_home_win_prob` (one
paper footnote). Earlier removals: `total_break`, `whiff_per_100`, `two_strike_chase_pct`, `wgdp` (1.0.1);
`WinProbabilityModel` and `xbh_pct` (1.1.0).

## Checked on 2026-10-21 for this release

Read: FanGraphs Library (plate discipline, BsR, SIERA), Baseball-Reference batting glossary and the Bonds, McGwire
and Judge pages, Baseball Prospectus SIERA part 5 (via search), baseballr 2.0.0 on R 4.6.1, the FanGraphs leaders API.
Corrections found: an earlier review quoted Judge's 2022 OPS+ as 211 (it is 210), and the FanGraphs plate-discipline
page does not define the zone geometrically (our rule is inferred from its counts, not published).
Could not read: Savant's glossary (HTTP 406), the Baseball-Reference pitching glossary (no ERA+ text), the FanGraphs
position-player WAR page (404).

## Audit of 2026-10-21 for 1.1.0

Sources read or fetched: Tango's Marcel post, files (2004, 2008, 2012) and `we.html`, `re24.html`, `markov.html`; FanGraphs Library
(position-player and pitcher WAR, positional adjustment, replacement level, BsR, SIERA part two, VAA primer, ERA-/FIP-/xFIP-);
Baseball-Reference baserunning and batting glossary and leaders pages; Baseball Savant csv-docs and leaderboards; MLB's glossary;
David Robinson's empirical Bayes post; the MLB Stats API team totals; FanGraphs leaderboards through baseballr 2.0.0.
The Stroman 2016 pitcher WAR worked example is on a separate FanGraphs page ("Calculating Pitcher WAR, A Complete Example") and
exists, so that claim holds. baseballr: its computing functions are already tied out, `code_barrel` overcounts Savant's barrels
by 1 to 4, and `run_expectancy_code` is a Statcast-specific pipeline; none was ported.
Explained after 1.1.0: the 2020 league adjustment (MLB-wide, not AL/NL), the 2000 WAR divisor (10.689), and the 1998 Guts R/W (FanGraphs' own totals give the bundled 10.241). BsR: the leaderboard's BaseRunning minus (wBsR + UBR + GDPRuns) has a standard deviation of 1.7 runs in both 2016 and 2024 (correlation .87), so it is not a rounding or one-year effect; still unexplained. Not resolved: FanGraphs' unrounded FIP park factor (the page shows whole numbers; the earlier note that 2001 had no FIP column was wrong, it exists from 1990); the 1998 runs-per-win gap; SIERA constants are measured, not published;
pitcher WAR's park factor and yearly league correction; Savant's Whiff% definition text (values reproduce, wording unread).

## Outside data sources surveyed (2026-10-21)

- **baseballr repo** (BillPetti/baseballr): its `data/` folder holds only lookup tables (teams, Statcast impute), no
  reference results. Its metric functions are `woba_plus`, `fip_plus`, `run_expectancy_code` (RE24 from Statcast) and
  `fg_guts`; the first, second and fourth are already tied out. `fg_park` scrapes the FanGraphs park-factor page (it
  currently fails against FanGraphs' bot protection; the page itself reads fine).
- **SportsDataverse** (`sportsdataverse-data` releases `mlb_game_state`, `mlb_hitting_models`, `mlb_pitching_models`,
  `mlb_fielding_models`; repo `baseballr-data`): per-season RE24 matrices, win-expectancy tables, leverage index, xwOBA,
  xERA, OAA. Their own `REGISTRY.md` says SIERA, baserunning and tunneling are *not* published because no public oracle
  exists, which matches our experimental/approximate labels. These are derived from the MLB Stats API, not independent
  published standards, so they are a cross-check, not a golden source.
- **sportsdataverse-py** (MIT): a data-access and machine-learning package (MLB Stats API, Statcast, ESPN, Fox, plus 25+
  other leagues). It has no wRC+ or WAR calculator and no Lahman support; its RE24, win expectancy, xwOBA, Stuff+ and
  OAA are its own fitted models, validated against Tango's table and Savant. Useful as a data source and for RE24
  cross-checks, not as a reference for our formulas.
- **gmalbert/baseball-predictions** (no license; a Streamlit betting app): not a metrics source. Its
  `data_files/processed/fg_guts.parquet` is a scraped copy of FanGraphs Guts!: all 112 weight and cFIP values for
  2010-2025 equal ours (third source after FanGraphs and baseballr), and its 2026 row (wBB .698, wHBP .729, w1B .890,
  w2B 1.261, w3B 1.596, wHR 2.049, cFIP 3.100) equals baseballr 2.0.0 `fg_guts()` for 2026. Its park files carry only a
  single `pf_basic` per team. Used for checking only, not bundled.
- **Cross-check done:** a Retrosheet 2016 RE24 matrix (built here) against SportsDataverse's 2016 matrix: all 24 states
  within 0.043 runs, mean 0.012 (largest gaps in the rarest states, where their sample is 5-35% smaller).
- **FanGraphs park page** now read for 2024: it publishes a "FIP" park column (2001 has no such column). Backing the
  park factor out of 2024 FIP- values (Sale, Skubal, Wheeler, Ragans, Lugo, Cease, Sanchez, Webb, Kirby) gives numbers
  within about 3 points of the Basic and FIP columns but matching neither exactly, so the FIP- gap is still unexplained
  (likely a pitcher-specific home/road park mix).

## Research still to do

1. Savant's own Whiff% definition text: its glossary page renders client-side and cannot be fetched; secondary sources (MLB.com articles, third-party glossaries) agree it is swings-and-misses over swings, and the foul-tip/bunt counting is confirmed numerically only.
2. Done 2026-10-21: the geometric strike zone holds on a second pitcher and season (Cole 2023, within 0.08 points). A left-handed pitcher and a hitter sample would widen it further.
3. Done in 1.1.0: FanGraphs' park input for FIP- is the FIP column of its park page, bundled for 1990-2026 (ERA+ is resolved: Baseball-Reference's pitching park factors and own-league ERA reproduce it). Still open: the unrounded value.
4. Done in 1.1.0: SIERA structure and per-season constants (measured). Still open: FanGraphs' production (BB/PA)^2 coefficient.
5. BsR: why the leaderboard's BaseRunning column is not wBsR + UBR + GDPRuns; wGDP constants.
6. DER: a published value that uses actual reached-on-error. Done in 1.1.0: XBT%, popup rate, VAA (third-party values).
7. Done 2026-10-21 for LinearWeightsEstimator: on Retrosheet 2016 the weights are within 0.001 to 0.031 of Guts! (scale 1.251 vs 1.212), so it stays approximate; the remaining gap needs FanGraphs' unpublished RE24 and event definitions. Still open: MonteCarloSimulator on the fitted matrix; Marcel pitcher regression amounts and Tango's published files.
8. Bundle league PA and games per season so the position-player WAR default uses the FanGraphs replacement formula (the 2026 constants are done, see 1.0.3).
9. Outside numbers for the formula-only `matches` (done 2026-10-21 for `xfip`, `shutdown`, `meltdown`, `rc_basic`, `rc_tech`, `pu_pct`, `xbt_pct`, `Log5Model`, `EmpiricalBayesShrinker`; `game_score_v2` moved to `approximate`, FanGraphs' GSv2 is one point lower on 34 of 55 starts). Added in 1.3.0: 833 qualified batter-seasons and 2,005 pitcher-seasons of FanGraphs leaderboards (2005, 2012, 2016, 2019, 2022, 2024) now pin obp, slg, iso, bb_pct, k_pct, bb_to_k, pit_k_pct, pit_bb_pct, pit_k_minus_bb_pct, pit_k_to_bb (to the fourth decimal), and `k_minus_bb_pct` equals the difference of FanGraphs' published batter K% and BB%, ip (the notation conversion only, a round trip) and ra9 (equals ERA on the 170 pitcher-seasons without unearned runs); `der` is `approximate` against Baseball-Reference's DefEff for all 30 teams of 2016 (library 0.0025 higher on average, 0.0047 at most, probably because Baseball-Reference estimates reached-on-error; unconfirmed). Still without an outside value, only a checked formula: ubb, xbh, base_runs, seca, gpa, ta, off, dice, dips_bop_pct, bf_per_ip, cg_pct, qs_pct, sv_pct, err_pct, avg_extension, bauer_units, effective_velo, sweet_spot_pct. RC/27, QERA, Speed Score, the rule-based Markov chain, Monte Carlo and the head-to-head Pythagorean had no published value and were removed in 1.4.0. Several are plain ratios of counting stats (cg_pct, qs_pct, sv_pct, err_pct, bf_per_ip, ra9, ubb, xbh) which rule 7 allows with a hand-computed test; `off` and `sweet_spot_pct` are `approximate` (Off was not compared with the FanGraphs column and uses the experimental `bsr`; sweet spot is 0.5 to 2.1 points high on Savant's integer-rounded launch angles).
10. Most golden fixtures come from a few players and seasons (Skubal 2024, 2001 pitchers); widen them.

## Added after 2.0.2 (unreleased): the 2026-10-22 research round

Eight methods were added from a documented research pass (ADR-0070 to ADR-0077). The counts above are for 1.4.1 and have
not been recomputed. What each addition is confirmed against:

| Addition | Outside value reproduced | Evidence tier |
|---|---|---|
| `power_speed_number` | Baseball-Reference career values (Bonds 613.90, Henderson 490.41, Mays 447.93) and five SABR/Wikipedia season values | `golden` |
| `xr`, `xrr` | Furtado's printed McGwire 1998 example (166.35, 167.05); this is the author's own computation, so it validates arithmetic and inputs, not the estimator's accuracy. XRB is not implemented because its printed example is inconsistent | `golden` |
| `calibration_table` bins, `brier_score` | Brier (1950) and Murphy (1973) printed examples (the library values are half of the printed two-class values) | `golden` |
| `ranked_probability_score` | 60 of 62 printed cells of Epstein's Tables 1 and 2; the paper prints the other two inconsistently | `golden` |
| `JamesSteinShrinker` | all 18 printed estimates, constants and errors of Efron and Morris (1975) | `golden` |
| `glicko2_update` | every printed value of Glickman's worked example (author's own example; no baseball use found) | `golden` |
| `expected_calibration_error`, `maximum_calibration_error` | none: the papers print no numeric example; tests are hand arithmetic and library-computed rows | `primary` |
| `diebold_mariano_test` | none printed; hand arithmetic and statsmodels 0.15.0 output agree to about 1e-15; the Harvey-Leybourne-Newbold correction is not applied | `primary` |

Not added, and why (details in the research notes): Brown (2008) shrinkage (24 of 59 printed cells unexplained), XRB,
calibration slope and Hosmer-Lemeshow, Shin de-vig, Bradley-Terry and Lindsey-based items (papers not obtained).
