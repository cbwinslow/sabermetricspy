# Credits and How to Cite

sabermetricspy implements methods that other people invented and published. The code is ours; the ideas, formulas,
constants and data are theirs. Every metric and model lists its source and how it was checked in
[METHODOLOGY.md](METHODOLOGY.md), and the full reading record is in [LITERATURE.md](LITERATURE.md). If you use a
result from this library, please cite the original method as well as the library.

## Citing sabermetricspy
See `CITATION.cff` (GitHub shows a "Cite this repository" button).

## Methods and the people behind them
| Area | Credit |
|---|---|
| Linear weights | Pete Palmer (with John Thorn, *The Hidden Game of Baseball*), per Wikipedia's article on Palmer; the FanGraphs wOBA construction is Tango's |
| wOBA, Marcel, Leverage Index, win expectancy tables, regression to the mean | Tom Tango, *The Book* (Tango, Lichtman, Dolphin) and tangotiger.net; win probability itself is older than his tables |
| BaseRuns | David Smyth |
| Pythagorean expectation, Pythagenpat | Bill James (Pythagorean, per the cited Wikipedia article); the Pythagenpat exponent is Tango's wiki page, and its originator is not recorded here |
| Log5 | Bill James, as the cited sources attribute it |
| Extended Pythagorean / opponent-adjusted win probability | Cleary, Jeffries, Miller, Miller, Murray and Skiera |
| Count run values | John Walsh, Hardball Times (2008); Marchi, Albert and Baumer, *Analyzing Baseball Data with R* |
| Markov chain half-inning model fitted from play-by-play | Albert, Baumer and Marchi, *Analyzing Baseball Data with R* (3rd ed.), chapter 9.2. Bukiet, Harold and Palacios (1997, *Operations Research* 45(1)) is the usual citation for event-probability Markov models; it was not read and its rules are not used. |
| wRC, wRC+, FIP, xFIP, kwERA, WAR, run expectancy (RE24) | FanGraphs Library and Guts! |
| WAR (position players and pitchers), ERA+, OPS+, pitcher metrics | Baseball-Reference |
| SIERA | Swartz and Seidman, Baseball Prospectus (2010 coefficients) |
| Statcast fields, barrels, run values | MLB Baseball Savant |
| Game Score 2.0 | Tom Tango, via FanGraphs |

Where a name above could not be traced to a page we read, METHODOLOGY.md says so instead; this table is a summary,
not the evidence.

## Data
- Retrosheet: "The information used here was obtained free of charge from and is copyrighted by Retrosheet.
  Interested parties may contact Retrosheet at www.retrosheet.org."
- Chadwick Bureau Register (https://github.com/chadwickbureau/register): player ids and names, licensed Open Data Commons
  Attribution License 1.0. It is not bundled; `sabermetricspy.ids` loads or downloads it, and each translation result
  carries this credit, the commit it was downloaded from and the fetch date.
- Lahman Baseball Database: copyright 1996-2025 by SABR, via the generous donation of Sean Lahman; licensed CC BY-SA 3.0.
- Bundled seasonal constants (`src/sabermetricspy/data/constants/`: wOBA weights, FIP and SIERA constants, league run
  environment, park factors, replacement-level and WAR inputs) are FanGraphs Guts! and leaderboard values recorded with
  source and retrieval date; the RE24 table is FanGraphs' page, which licenses its run expectancy data from Tom Tango.
  They remain FanGraphs' data. FanGraphs' Terms of Service (https://www.fangraphs.com/about/terms-of-service, read
  2026-10-21) say the site is protected as a collective work or compilation (section 8), bar unauthorized reproduction or
  further distribution of its materials (section 6) and reproducing or reselling content for commercial purposes
  (section 11). They grant no data license and do not mention automated access. Individual constants are numbers computed
  from public game data, but the project has not obtained FanGraphs' permission; see `docs/VERIFICATION.md` and ADR-0066.
- The tests hold recorded FanGraphs and Baseball-Reference leaderboard rows (`tests/golden/`) only to check the library's
  output against them; they are not part of the installed package.
- Statcast data belongs to MLB Advanced Media; the library ships only small recorded samples used by tests.

## Corrections
If a credit is wrong or missing, open an issue. Attribution errors are bugs.
