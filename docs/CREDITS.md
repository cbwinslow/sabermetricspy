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
| Power-Speed Number | Bill James (Baseball Abstract; the retrieved sources disagree on 1980 or 1983); Baseball-Reference and SABR (Sciarretta 1983) for the published values |
| Extrapolated Runs (XR, XRR) | Jim Furtado, *The 1999 Big Bad Baseball Annual*, via Baseball Think Factory |
| Ranked probability score | Edward Epstein (1969) and Allan Murphy (1971), Journal of Applied Meteorology; Brier (1950) and Murphy (1973) for the score decomposition |
| Expected and maximum calibration error | Naeini, Cooper and Hauskrecht (2015, AAAI); Guo, Pleiss, Sun and Weinberger (2017, ICML) |
| Diebold-Mariano test | Francis Diebold and Roberto Mariano (1995), Journal of Business and Economic Statistics |
| Arcsine James-Stein shrinkage | Bradley Efron and Carl Morris (1975), Journal of the American Statistical Association |
| Glicko-2 rating update | Mark Glickman, glicko.net |
| Batter's Run Average | Dick Cramer and Pete Palmer (1974), Baseball Research Journal / SABR |
| Estimated Runs Produced | Paul Johnson (1985), Bill James Baseball Abstract |
| Component ERA (ERC) | Bill James (2004), The Bill James Handbook |
| Pythagenport | Clay Davenport & Keith Woolner (1999), Baseball Prospectus #342 |


Where a name above could not be traced to a page we read, METHODOLOGY.md says so instead; this table is a summary,
not the evidence.

## Data
- Retrosheet: "The information used here was obtained free of charge from and is copyrighted by Retrosheet.
  Interested parties may contact Retrosheet at www.retrosheet.org."
- Chadwick Bureau Register (https://github.com/chadwickbureau/register): player ids and names, licensed Open Data Commons
  Attribution License 1.0. It is not bundled and the library never downloads it; `sabermetricspy.ids` loads your copy, and each translation result
  carries this credit, the commit it was downloaded from and the fetch date.
- Lahman Baseball Database: copyright 1996-2025 by SABR, via the generous donation of Sean Lahman; licensed CC BY-SA 3.0. `sabermetricspy.lahman` reads the official download (https://sabr.org/lahman-database/) that you place on disk and computes league constants from it; the library never downloads it and no copy is kept in the repository.
- Seasonal constants are not distributed with this library (ADR-0068). FanGraphs publishes the Guts! constants and park factors
  itself (https://www.fangraphs.com/guts.aspx?type=cn); its Terms of Service (https://www.fangraphs.com/about/terms-of-service,
  read 2026-10-21) bar unauthorized reproduction or redistribution of its compiled content, so users who want those
  values obtain them from FanGraphs under its terms. The run expectancy data on FanGraphs is licensed from Tom Tango.
- The tests compare the library's output with published values from FanGraphs, Baseball-Reference and Baseball Savant.
  Short, cited samples are kept in `tests/golden/`; the large league-wide compilations stay on the maintainer's machine
  and are not in the repository.
- Statcast data belongs to MLB Advanced Media; the library ships only small recorded samples used by tests.

## Corrections
If a credit is wrong or missing, open an issue. Attribution errors are bugs.
