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

### 1. Catcher defensive rating system (Rosciam, 2004)
- **Citation**: [Catcher's Defensive Rating System, Chuck Rosciam, via Retrosheet](https://www.retrosheet.org/Research/RosciamC/Catcher%20Defensive%20Rating%20System.pdf)
- **Formula source**: components scaled to 1.00 for a league-average catcher: Stamina (share of team innings caught over the league average share), Good Glove (independent-putout fielding average over the league figure, where independent putouts exclude strikeouts), Good Arm (CCS/(CCS+SBA) times the league caught-stealing rate). Three further components (ball handling, game play, game calling) were read only in part.
- **Inputs**: innings caught, putouts excluding strikeouts, assists, errors, caught stealing, stolen bases against, league rates.
- **Inputs in canonical schema**: partly; putouts excluding strikeouts are not a canonical column.
- **Validation target**: none retrieved.
- **Scores**: formula=1; inputs=1; validation=0; fit=1; value=1; difficulty=2
- **Priority score**: 2
- **Difficulty**: 2.

## Implemented from this catalogue

| Method | Change | Record |
|---|---|---|
| Park factor, raw and regressed | `park-factor-calculation` | ADR-0029 |
| Game Score Version 2.0 and Game Score (James) | `game-score-and-off-metrics` | ADR-0030 |
| Off (FanGraphs) | `game-score-and-off-metrics` | ADR-0030 |
| Base-Advance Average (Hardegree) | `base-advance-average` | ADR-0031 |
| Extended Pythagorean head-to-head (Cleary et al.) | `extended-pythagorean` | ADR-0032 |
| Shutdown and Meltdown (FanGraphs) | direct commit, per-appearance indicators | ADR-0036 |

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
| Pairwise Pythagorean wins | Heumann, Journal of Sports Analytics 2016 (see digest) | The paper was not retrieved; Cleary et al. describe it only in prose. The head-to-head extension is implemented (ADR-0032). |
| Game Score v2 weights from a Wharton deck | secondary | Matches the implemented Game Score 2.0 apart from restating the home run penalty; the FanGraphs article is the primary source and is used instead. |
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
| FanGraphs | `fg_guts`, `fg_park`, `fg_park_hand` | out of scope as scrapers | constants are bundled snapshots; park factor calculation is now implemented (ADR-0029) |
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
| Chadwick Bureau Register | the repository page and the header of `data/people-0.csv` (2026-10-20). 16 shards `people-0.csv` to `people-f.csv` of about 4 MB each (526,894 people), plus `names.csv`, `links.csv`, `countries.csv`. Columns: `key_person, key_uuid, key_mlbam, key_retro, key_bbref, key_bbref_minors, key_fangraphs, key_npb, key_sr_nfl, key_sr_nba, key_sr_nhl, key_wikidata`, names (`name_last, name_first, name_given, name_suffix, name_matrilineal, name_nick`), birth and death dates, and played, managed and umpired years for pro, MLB and college. License ODC-BY 1.0; the repository has no LICENSE file in the root, the README names the license. | The register's license text file. |
| Chadwick `names.csv` and `links.csv` | read in full on 2026-10-20. `names.csv` (1,346 rows) columns `key_person, name_last, name_first, name_given, birth_year, birth_month, birth_day, altname_type, altname_lang, altname_last, altname_first, altname_given, altname_matrilineal, altname_nick, altname_date_start, altname_date_end`; `altname_type` counts: alias 643, birth 260, alt-spelling 251, legal 191, anglicized 1. `links.csv` (27,340 rows) columns `key_person, source, value`; sources `tsncards` and `findagrave` (eight rows are spelled `tsncardS`). `countries.csv` (250 rows, `key_iso_alpha2, key_iso_alpha3, key_ioc, key_fifa, name_full_en`) has no person key and is not used. | none |
| Retrosheet biographical files (retrosheet.org/biofile.htm) | Page content as summarized by a web search on 2026-10-20 (the site refused direct connections from this machine and from the fetch tool; the user reports it opens in a browser): one `biofile.zip` with eight files; `biofile0.csv` (32 fields, `id, lastname, usename, fullname, birthdate, birthname, ...`) covers everyone who played, managed, coached or umpired in the majors, Negro Leagues included, updated through 2025; `usename` is the first name used in the career; `birthname` is given only when it differs from `fullname`; dates `yyyymmdd`, heights in inches, weights in pounds; `biofile.csv` is the older 33-field layout (`PLAYERID`, `NICKNAME`). Terms, as summarized by the same search: recipients may make any use of the data, including selling it or building a commercial product, provided the statement "The information used here was obtained free of charge from and is copyrighted by Retrosheet." appears prominently. The column list was also measured on a copy of `biofile0.csv` in the Chadwick Bureau's mirror `chadwickbureau/retrosheet` (branch `official`, commit 118094bb, 2026-08-12): 27,049 people, 772 partial birth dates ending `00`, 444 birth names, 17 alternate names, 1,196 people with no `usename`. | The page text and the notice were not read verbatim, and the official `biofile.zip` has not been opened; the direct download address was not obtained. Both are to be checked against the file the user downloads. |

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
