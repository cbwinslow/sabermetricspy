# Literature Catalogue

Candidate methods that sabermetricspy does not implement yet, found by the sweep in
[LITERATURE_SWEEP.md](LITERATURE_SWEEP.md) on 2026-10-18. Nothing here is implemented; each accepted entry becomes
its own later OpenSpec change. Every statement below comes from a page or paper read during the sweep; where a
source could not be read, the entry says so.

## How entries are ranked

An entry is accepted only if a primary source with a published formula was retrieved. Otherwise it goes to the
[rejected list](#rejected-or-deferred-with-reason). Accepted entries are scored on six recorded criteria, so the
order can be re-derived:

| Criterion | Scale | Meaning |
|---|---|---|
| formula | 0 or 1 | 1 when the full formula was retrieved from the cited source |
| inputs | 0 to 2 | 2 when every input is in the canonical schema, 1 when some are, 0 when none |
| validation | 0 to 2 | 2 when the source prints a worked value we can recompute, 1 when a published value exists but was not yet fetched, 0 when none |
| fit | 0 to 2 | 2 for a pure function of counts or a column expression, 1 when it needs extra structure, 0 when it needs a provider |
| value | 1 to 3 | 3 when it removes a known gap in current metrics, 1 for a niche statistic |
| difficulty | 1 to 3 | 1 for a single expression, 3 for a model fit |

Priority score = formula + inputs + validation + fit + value - difficulty. A test
(`tests/test_literature_catalogue.py`) checks that every entry has all fields and a primary-source URL, that the
recorded score equals the sum, and that entries are in descending score order.

## Candidate methods

### 1. Game Score Version 2.0 (Tom Tango)
- **Citation**: [Game Score Version 2.0, FanGraphs](https://blogs.fangraphs.com/instagraphs/game-score-v2-0)
- **Formula source**: the article: 40 + 2 per out + 1 per strikeout - 2 per walk - 2 per hit - 6 extra per home run - 3 per run. The base can be shifted each year so that 50 is league average (2015 used 38).
- **Inputs**: outs, strikeouts, walks, hits, home runs, runs.
- **Inputs in canonical schema**: yes, all six are existing pitching columns.
- **Validation target**: the article's worked start (7 IP, 8 K, 2 BB, 5 H including 1 HR, 2 R) scores 64 with base 40.
- **Scores**: formula=1; inputs=2; validation=2; fit=2; value=2; difficulty=1
- **Priority score**: 8
- **Difficulty**: 1 (single column expression, per game row).

### 2. Park factor, raw and regressed (FanGraphs Library)
- **Citation**: [5 Year Regressed Park Factors, FanGraphs Library](https://library.fangraphs.com/park-factors-5-year-regressed/)
- **Formula source**: raw PF = H*T / ((T-1)*R + H) with home and road runs per game and T teams; iPF = (raw + 1)/2; final = 1 - (1 - iPF)*X with X = 0.6, 0.7, 0.8, 0.9 for 1, 2, 3, 4 or more years, using up to five years centered on the season.
- **Inputs**: runs scored and allowed split by home and road, games, team count.
- **Inputs in canonical schema**: partly; home and road splits need a home/road flag on team-game rows.
- **Validation target**: the article's examples: home 11 and road 10 runs per game gives raw 1.10 and composite 1.05; iPF 1.25 regresses to 1.15, 1.175, 1.20, 1.225 for 1 to 4 years. Published per-park values come from the FanGraphs Guts! park factor page and have not been fetched.
- **Scores**: formula=1; inputs=1; validation=2; fit=2; value=3; difficulty=2
- **Priority score**: 7
- **Difficulty**: 2 (windowing and edge-year rules). High value because wRC+, OPS+, ERA+ and ERA- currently default the park factor to 100 unless the caller supplies one.

### 3. Game Score (Bill James, original)
- **Citation**: [Game score, Wikipedia](https://en.wikipedia.org/wiki/Game_score) (secondary page describing James's original formula; the original text was not retrieved)
- **Formula source**: start at 50; +1 per out; +2 per completed inning after the fourth; +1 per strikeout; -2 per hit; -4 per earned run; -2 per unearned run; -1 per walk.
- **Inputs**: outs, innings completed, strikeouts, hits, earned and unearned runs, walks.
- **Inputs in canonical schema**: yes (unearned runs are runs minus earned runs).
- **Validation target**: Kerry Wood's 1998 start (27 outs, 20 K, 1 H) = 105; Max Scherzer's 2015 no-hitter (17 K) = 104.
- **Scores**: formula=1; inputs=2; validation=2; fit=2; value=1; difficulty=1
- **Priority score**: 7
- **Difficulty**: 1.

### 4. Off (FanGraphs)
- **Citation**: [Off, FanGraphs Library](https://library.fangraphs.com/offense/off/)
- **Formula source**: Off = batting runs + BsR. Batting runs = wRAA + (lgR/PA - PF*lgR/PA)*PA + (lgR/PA - league non-pitcher wRC/PA)*PA; BsR = wSB + UBR + wGDP.
- **Inputs**: wRAA, park factor, league R/PA and non-pitcher wRC/PA, BsR components.
- **Inputs in canonical schema**: yes; the library already has wRAA, wSB, wGDP, BsR and the league constants.
- **Validation target**: FanGraphs leaderboard Off values for recorded batters (not fetched yet); the page prints only rules of thumb.
- **Scores**: formula=1; inputs=2; validation=1; fit=2; value=2; difficulty=1
- **Priority score**: 7
- **Difficulty**: 1 (composition of existing metrics; UBR input is caller supplied).

### 5. Base-Advance Average (Hardegree, 2005)
- **Citation**: [Base-Advance Average, Gary Hardegree, via Retrosheet](https://www.retrosheet.org/Research/HardegreeG/Base-Advance-Average.pdf)
- **Formula source**: bases advanced (batter and runners, steals included, runners erased count negative) divided by base-advance opportunities (for each runner including the batter, the maximum bases he could advance: 4 for the batter, 3 from first, and so on).
- **Inputs**: base state before and after, outs, runs on the play, steals and caught stealing.
- **Inputs in canonical schema**: yes, the play-by-play columns used by the RE24 estimator carry them.
- **Validation target**: the paper's worked sample inning (section 3) and its player tables; not yet recomputed.
- **Scores**: formula=1; inputs=2; validation=1; fit=2; value=2; difficulty=2
- **Priority score**: 6
- **Difficulty**: 2 (the paper notes scoring interpretation for runners thrown out; the retrospective rule charges the batter).

### 6. Extended Pythagorean head-to-head probability (Cleary et al.)
- **Citation**: [Extending James' Pythagorean Formula for Head-to-Head Matchups](https://web.williams.edu/Mathematics/sjmiller/public_html/math/papers/PythagBothTeams20.pdf)
- **Formula source**: home RS and RA are rescaled by the opponent's allowed and scored runs relative to the league average R: RS_adj = RS_h*(RA_a/R), RA_adj = RA_h*(RS_a/R); P(home wins) = RS_adj^g / (RS_adj^g + RA_adj^g), equivalently (RS_h*RA_a)^g / ((RS_h*RA_a)^g + (RA_h*RS_a)^g).
- **Inputs**: team runs scored and allowed per game, league runs per game, exponent.
- **Inputs in canonical schema**: yes.
- **Validation target**: the algebraic equivalence of the two forms (checkable offline); the paper's playoff result of 80.18 expected series wins against 80 actual needs 2001 to 2019 series data.
- **Scores**: formula=1; inputs=2; validation=1; fit=2; value=1; difficulty=1
- **Priority score**: 6
- **Difficulty**: 1. The paper quotes Baseball-Reference's exponent as 1.87 (and 1.83 as also common), which should be reconciled with ADR-0027's configurable exponent before adoption.

### 7. Shutdown and Meltdown (FanGraphs)
- **Citation**: [SD and MD, FanGraphs Library](https://library.fangraphs.com/pitching/sd-md/)
- **Formula source**: a reliever earns a Shutdown in a game when his WPA is +0.06 or more and a Meltdown when it is -0.06 or less.
- **Inputs**: per-game reliever WPA.
- **Inputs in canonical schema**: partly; WPA per play exists, a per-game aggregate needs a game identifier.
- **Validation target**: FanGraphs leaderboard SD and MD counts (not fetched); the page prints only season rating scales.
- **Scores**: formula=1; inputs=1; validation=1; fit=2; value=1; difficulty=2
- **Priority score**: 4
- **Difficulty**: 2.

### 8. Catcher defensive rating system (Rosciam, 2004)
- **Citation**: [Catcher's Defensive Rating System, Chuck Rosciam, via Retrosheet](https://www.retrosheet.org/Research/RosciamC/Catcher%20Defensive%20Rating%20System.pdf)
- **Formula source**: components scaled to 1.00 for a league-average catcher: Stamina (share of team innings caught over the league average share), Good Glove (independent-putout fielding average over the league figure, where independent putouts exclude strikeouts), Good Arm (CCS/(CCS+SBA) times the league caught-stealing rate). Three further components (ball handling, game play, game calling) were read only in part.
- **Inputs**: innings caught, putouts excluding strikeouts, assists, errors, caught stealing, stolen bases against, league rates.
- **Inputs in canonical schema**: partly; putouts excluding strikeouts are not a canonical column.
- **Validation target**: none retrieved.
- **Scores**: formula=1; inputs=1; validation=0; fit=1; value=1; difficulty=2
- **Priority score**: 2
- **Difficulty**: 2.

## Rejected or deferred with reason

Each item failed the "primary source with a published formula" test, or sits outside the library's scope. Several
can be re-opened by retrieving the named source.

| Candidate | Source examined | Reason |
|---|---|---|
| Spd | [FanGraphs Spd](https://library.fangraphs.com/offense/spd/) | Names four components (stolen-base %, attempt frequency, triples %, runs-scored %) but prints no formula or weights. |
| Pitch-type linear weights (wFB, wFB/C) | [FanGraphs](https://library.fangraphs.com/offense/pitch-type-linear-weights/) | The method is described (change in count run expectancy credited to pitch type) but the run-value table is marked "coming soon"; the library's `rv_per_100` already covers Savant's version. |
| Soft%, Med%, Hard% | [FanGraphs](https://library.fangraphs.com/offense/quality-of-contact-stats/) | Baseball Info Solutions thresholds are proprietary and unpublished; `hard_hit_pct` covers the public Statcast definition. |
| Regression toward the mean constants | [FanGraphs](https://library.fangraphs.com/principles/regression/) | The page is conceptual and prints no constants. |
| Aging curve | [FanGraphs](https://library.fangraphs.com/principles/aging-curve/) | Only a rule of thumb (about 0.5 WAR per year after 30); the curves are images. Marcel's age factors already exist. |
| League equivalencies (MLEs) | [FanGraphs](https://library.fangraphs.com/principles/league-equivalencies/) | Describes the approach with no formulas or factors. |
| Pairwise Pythagorean wins | Heumann, Journal of Sports Analytics 2016 (see digest) | The paper was not retrieved; Cleary et al. describe it only in prose. Entry 6 covers the related head-to-head extension. |
| Game Score v2 weights from a Wharton deck | secondary | Matches entry 1 apart from restating the home run penalty; the FanGraphs article is the primary source and is used instead. |
| Base-advance, catcher and range papers by Comly (ARM, 2000), Ruane (2005), Tango (Evaluating Catchers, 2004), Johnson (Fielder Range, 2011), Soper (2014), Wood (Win Values, 2018) | Retrosheet research list | Listed but not read; formulas unverified. Re-open by extracting each PDF (the fetch tool saves PDFs locally; `pypdf` reads them). |
| Machine-learning and Bayesian papers from OpenAlex and arXiv (Piette and Jensen on fielding, Stern and Sugano and Healey and Doo and Kim and Morey and Cohen on matchups, Jensen and McShane and Gerber and Craig on hitting forecasts, Konaka on park factors, Nguyen and Matthews on aging, Mott and Bradshaw on win probability) | digest of 2026-10-18 | Only titles and metadata were screened; full text was not retrieved, so no formula can be cited. Candidates for a future deeper pass. |
| The Book (Tango, Lichtman, Dolphin) | not retrievable | A printed book with no online text; the Tango wiki archive is used as the substitute. |
| NCAA, ESPN, MLB Stats API, Spotrac and Chadwick functions in baseballr | [baseballr index](https://billpetti.github.io/baseballr/reference/index.html) | Data acquisition, outside the pure-calculation scope. |

## baseballr coverage analysis

Source: the [baseballr reference index](https://billpetti.github.io/baseballr/reference/index.html), read on
2026-10-18. Function names and one-line titles come from that page; behavior beyond the titles was not examined.

| Function group | Functions | Status | sabermetricspy equivalent |
|---|---|---|---|
| Metrics | `woba_plus`, `fip_plus` | covered | `woba`, `fip` with the sourced constants (ADR-0027) |
| Metrics | `run_expectancy_code` | partly covered | `RunExpectancyMatrix`, `LinearWeightsEstimator` |
| Metrics | `team_consistency` | gap | none; the definition was not retrieved |
| Statcast helpers | `code_barrel` | partly covered | `barrel_pct` (labeled approximate) |
| Statcast helpers | `linear_weights_savant` | partly covered | `LinearWeightsEstimator` |
| Statcast helpers | `edge_code`, `edge_frequency` | gap | none; the Edge definition was not retrieved |
| Statcast helpers | `statline_from_statcast`, `process_statcast_payload`, `label_statcast_imputed_data` | partly covered | `prepare_statcast_pitches` and the statcast preset |
| Statcast acquisition | `statcast_search` and variants, `statcast_leaderboards` | out of scope | pure-calculation rule |
| FanGraphs | `fg_guts`, `fg_park`, `fg_park_hand` | out of scope as scrapers | constants are bundled snapshots; park factor calculation is a gap (entry 2) |
| FanGraphs, Baseball Reference, MLB Stats, ESPN, NCAA, Spotrac, Chadwick | all other `fg_*`, `bref_*`, `mlb_*`, `espn_*`, `ncaa_*`, `sptrc_*`, `chadwick_*` functions | out of scope | data acquisition and lookups |
| Retrosheet | `retrosheet_data` | out of scope | the `retrosheetpy` preset maps its output |
| Pre-computed datasets | `load_mlb_re24_matrix`, `load_mlb_we_table`, `load_mlb_wpa`, `load_mlb_expected_stats`, `load_mlb_xera`, `load_mlb_oaa`, `load_mlb_catcher_framing`, `load_mlb_stuff_plus`, `load_mlb_command_plus`, `load_mlb_batter_projection` | out of scope as loaders; possible validation targets | would give published reference tables for the six unverified models (`WinProbabilityModel`, `CountExpectancyMatrix`, `OutsAboveAverageModel`, `CatcherFramingModel`, `PitchQualityModel`, `ExpectedOutcomeModel`); their contents were not inspected |
| Visualizations | `ggspraychart`, `ggpitchzone` | out of scope | plotting |

## Coverage of each requested source

| Source | What was examined (2026-10-18) | Could not be retrieved |
|---|---|---|
| OpenAlex | 12 topic queries, each prefixed "baseball", 8 records each; see the table below for totals. Search is full-text, so totals overstate relevance. | Full text of papers (only metadata is stored). |
| arXiv | the same 12 queries, 8 results requested each | none; most topics returned few or no results because arXiv matches the exact phrase. |
| Tom Tango | the wiki landing page (now archive mode), the [wiki archive index](http://tangotiger.net/wiki_archive/) listing Pythagorean, PythagenPat, Linear Weights, wOBA, Leverage Index, WPA, Base Runs, Runs Created, Log5 and Win Expectancy pages, and the FanGraphs-hosted Game Score 2.0 article. | *The Book* (printed). The archive pages themselves were listed but not read; Marcel and regression have no archive page. The Tango blog was not browsed. |
| Retrosheet | the home page and [research papers list](https://www.retrosheet.org/Research/Research.htm); three papers read (Hardegree, Rosciam, Cleary et al. via the Williams College copy). Charlie Pavitt's bibliography is linked as four PDFs (A-C, D-R, S-Z, Carleton) but was not read. | The old `Research.html` URL returned 404. The other research PDFs listed in the rejected table. |
| baseballr | the full reference index. | Function bodies and documentation pages. |

OpenAlex and arXiv query totals (2026-10-18):

| Query | OpenAlex total | arXiv total |
|---|---|---|
| run expectancy | 2747 | 2 |
| win probability | 7739 | 6 |
| pitch quality stuff model | 2987 | 0 |
| expected batting average exit velocity launch angle | 96 | 0 |
| catcher framing | 1524 | 0 |
| fielding metrics defensive runs | 594 | 0 |
| player projection forecasting | 940 | 0 |
| park factors | 30556 | 1 |
| aging curve | 12780 | 2 |
| pitch tracking release | 6699 | 0 |
| batter pitcher matchup | 203 | 2 |
| baserunning stolen base value | 30 | 0 |

The full metadata digest (titles, authors, years, venues, licenses as returned, landing links) is saved in
[`literature/digest-2026-10-18.json`](literature/digest-2026-10-18.json).
