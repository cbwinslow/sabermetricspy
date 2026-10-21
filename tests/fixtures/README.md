# Test fixtures

- `marcel_hitters_2001_2003.csv`, `marcel_pitchers_2001_2003.csv`: player-season batting and pitching lines for 2001-2003, summed
  over stints, from the Lahman database (CRAN package `Lahman`, retrieved 2026-10-21). Hitters exclude anyone with 10 or more pitching
  games in those seasons (Tango's step 2, pitchers' hitting out of the league average); `age` is the season minus the birth year.
  Inputs to `tests/test_golden_marcel_tango.py`, which compares the projections with Tom Tango's published 2004 Marcel files
  (`tests/golden/marcel_tango_2004_*.csv`, columns copied from tangotiger.net/marcel/marcel2004.zip).
- `statcast/`: see its README.
- `literature/`: recorded API responses for the literature sweep tests.
