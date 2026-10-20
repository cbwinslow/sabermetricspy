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
| Linear weights, wOBA, Marcel, Log5 use, Win Expectancy, Leverage Index, regression to the mean | Tom Tango, *The Book* (Tango, Lichtman, Dolphin) and tangotiger.net |
| BaseRuns | David Smyth |
| Pythagorean expectation, Pythagenpat | Bill James (Pythagorean, per the cited Wikipedia article); the Pythagenpat exponent is Tango's wiki page, and its originator is not recorded here |
| Log5 | Bill James, as the cited sources attribute it |
| Extended Pythagorean / opponent-adjusted win probability | Cleary, Jeffries, Miller, Miller, Murray and Skiera |
| Count run values | Dan Walsh, Hardball Times (2008); Marchi, Albert and Baumer, *Analyzing Baseball Data with R* |
| Markov chain run models | Bukiet, Harold and Palacios (1997) |
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
  carries this credit and the register's release date.
- Lahman Baseball Database: Sean Lahman, licensed CC BY-SA 3.0.
- Bundled seasonal constants are FanGraphs Guts! and leaderboard values recorded with source and retrieval date.
  They remain FanGraphs' data; check their terms before redistributing them.
- Statcast data belongs to MLB Advanced Media; the library ships only small recorded samples used by tests.

## Corrections
If a credit is wrong or missing, open an issue. Attribution errors are bugs.
