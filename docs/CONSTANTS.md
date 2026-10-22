# Seasonal constants: what you supply and where it comes from

sabermetricspy ships **no** third-party constants and downloads **nothing** (ADR-0003, ADR-0068). Metrics that need a
season's constants (wOBA, wRC+, FIP and the rest) read them from a table you provide. This page says what the library
needs, the quickest way to get it, and what it can compute for you.

## The quickest start: a FanGraphs Guts! table

wOBA, wRAA, wRC+ and FIP need only the Guts! constants. Download them yourself, for your own use and under FanGraphs'
[terms of service](https://www.fangraphs.com/about/terms-of-service); the library does not redistribute them.

```python
import io
import urllib.request

import pandas as pd
import sabermetricspy as sp

req = urllib.request.Request(
    "https://www.fangraphs.com/guts.aspx?type=cn", headers={"User-Agent": "Mozilla/5.0"}
)
html = urllib.request.urlopen(req).read().decode("utf-8")
guts = max(pd.read_html(io.StringIO(html)), key=len)  # Season, wOBA, wOBAScale, wBB ... R/W, cFIP
guts.to_csv("guts.csv", index=False)  # keep a copy; do not commit or redistribute it

sp.use_guts("guts.csv")  # or sp.use_guts(guts)
```

In R, `baseballr::fg_guts()` returns the same table. `sp.load_guts` accepts either set of column names.
A season missing from your table raises `ConstantsNotFoundError`; the library never borrows another season's values.

## Constants directory (park factors, WAR inputs)

Park-adjusted FIP, pitcher WAR and position-player WAR need more than Guts!. Put these YAML files in a directory and
call `sp.use_constants(path)` (or set `SABERMETRICSPY_CONSTANTS`). Every file is optional; a calculation raises
`ConstantsNotFoundError` naming the one it lacks.

| File | Holds | Where the values come from |
|---|---|---|
| `woba_fangraphs.yaml` | the same fields as Guts!, plus league ERA/FIP/xFIP, HR/FB, wRC/PA, SIERA and kwERA constants (`seasons: {2024: {...}}`; fields in `sabermetricspy.types.context.WOBAWeights`) | Guts! for the weights; the league fields can be computed (below) |
| `park_factors.yaml` | `parks: {COL: {park_id, team_id, season, basic_5yr, basic_1yr, hr_factor}}` | FanGraphs park factors page (`guts.aspx?type=pf`) |
| `park_fip.yaml` | `seasons: {2024: {NYY: 102, ...}}`, the park input of FIP- and pitcher WAR | FanGraphs park factors page, FIP column |
| `pitcher_war.yaml` | `seasons: {2024: {al: {...}, nl: {...}}}` league pitching totals | league totals (below) |
| `league_war.yaml` | `seasons: {2024: {games, pa, runs, outs}}` | league totals (below) |

## What the library computes from data you hold

- **League constants from Lahman:** `sabermetricspy.lahman.league_constants(season, lahman_dir=...)` gives runs per PA,
  OBP, SLG, ERA, cFIP, the kwERA constant and the caught-stealing run value from the batting and pitching CSVs of the
  official [SABR Lahman database](https://sabr.org/lahman-database/) (download it from that page; CC BY-SA 3.0, credit
  SABR and Sean Lahman). These matched the FanGraphs values within their rounding for 1990 to 2025 (ADR-0067).
  Do not use unofficial mirrors.
- **Linear weights from play-by-play:** `LinearWeightsEstimator` fits wOBA weights from your own event data; on
  Retrosheet 2016 they land within 0.001 to 0.03 of Guts!.
- **Run expectancy:** `RunExpectancyMatrix.fit` builds RE24 from your events.

## Not covered

Park factors, SIERA constants and batted-ball league rates cannot be derived from Lahman; they come from FanGraphs or
from your own tracking data.

## Maintainers

`tools/` holds scripts that query FanGraphs, MLB and the Chadwick Bureau to rebuild reference data and test fixtures.
They are maintainer tooling, are not part of the installed package, and their outputs are kept out of the repository
(see `.gitignore`).
