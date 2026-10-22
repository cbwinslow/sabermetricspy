# Seasonal constants: what you supply and where it comes from

sabermetricspy ships **no** third-party constants and downloads **nothing** (ADR-0003, ADR-0068). Metrics that need a
season's constants (wOBA, wRC+, FIP and the rest) read them from a table you provide. This page says what the library
needs, the quickest way to get it, and what it can compute for you.

## The quickest start: a FanGraphs Guts! table

wOBA, wRAA and FIP need only the Guts! constants. Get them yourself, for your own use and under FanGraphs'
[terms of service](https://www.fangraphs.com/about/terms-of-service); the library does not redistribute them, and this
page does not automate the download.

- In a browser, open the [Guts! constants page](https://www.fangraphs.com/guts.aspx?type=cn) and save the page, or copy
  the table into a spreadsheet and save it as `guts.csv`.
- Or in R, `baseballr::fg_guts()` returns the same table: `write.csv(baseballr::fg_guts(), "guts.csv", row.names = FALSE)`.

```python
import sabermetricspy as sp

sp.use_guts(
    "guts.csv"
)  # Season, wOBA, wOBAScale, wBB ... R/PA, R/W, cFIP (web or baseballr column names)
```

A season missing from your table raises `ConstantsNotFoundError`; the library never borrows another season's values.

### What a Guts!-only table supports

| Works | Needs more than Guts! (add the field to `woba_fangraphs.yaml`, or the call raises or returns null) |
|---|---|
| wOBA, wRAA, FIP, the batting rate metrics | `OPS+` (`lg_obp`, `lg_slg`), `K%+` and `BB%+` (`lg_k_pct`, `lg_bb_pct`, and the league versions): raise `ConstantsNotFoundError` naming the field |
| wRC+ is computed, but with league runs per PA (which includes pitchers) | exact wRC+ needs `lg_wrc_per_pa` (non-pitcher wRC/PA) |
| kwERA, using Tango's 5.40 when no seasonal constant is given | the seasonal kwERA constant (`kwera_constant`; Lahman computes it through 2020) |
| | wSB, BsR and Off (`lg_wsb`, league stolen-base runs per opportunity; raise `ConstantsNotFoundError`) |
| | xFIP (`lg_hr_per_fb`), SIERA (`siera_constant`), FIP- / ERA- / ERA+ (league ERA and FIP): null |

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
