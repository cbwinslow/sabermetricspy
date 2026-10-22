# Seasonal constants: what you supply and where it comes from

sabermetricspy ships **no** third-party constants (ADR-0068) and fetches them only when you ask (ADR-0069). Metrics that
need a season's constants (wOBA, wRC+, FIP and the rest) read them at run time from tables on your machine; nothing is
baked into the formulas. This page says what the library needs, how to fetch and refresh it, and what it can compute.

## The quickest start: fetch them

```text
sabermetrics constants update
```

or `sabermetricspy.fetch.update_constants()` from Python. This mirrors R's `baseballr` (`fg_guts`, `fg_park`) and
writes to your cache directory (`sabermetrics constants path` prints it), which the library then reads with no further
setup:

| File | From | Fetched |
|---|---|---|
| `guts.csv` | FanGraphs Guts! constants, 1871 on | whole, every run |
| `park_fip.yaml`, `park_factors.yaml` | FanGraphs park factors, 1990 on | missing seasons plus the latest two |
| `league_war.yaml` | MLB Stats API team totals, 1990 on | missing seasons plus the latest two |

**Refresh once a season** (and after the season ends, since the latest two seasons are refetched while their totals
move): rerun the same command. It is safe to repeat. Use the data under FanGraphs'
[terms of service](https://www.fangraphs.com/about/terms-of-service); the library fetches for your own use and never
redistributes the tables. Nothing is fetched on import or by a calculation: a missing table raises
`ConstantsNotFoundError` pointing at this command.

## Supplying a Guts! table yourself

If you cannot fetch (offline, or you want to pin a copy), save the table as `guts.csv` by hand (copy it from the
[Guts! page](https://www.fangraphs.com/guts.aspx?type=cn), or in R `write.csv(baseballr::fg_guts(), "guts.csv",
row.names = FALSE)`) and point at it:

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
| `pitcher_war.yaml` | `seasons: {2024: {al: {...}, nl: {...}}}` league pitching totals | FanGraphs leaderboard league totals; **not fetched yet**, supply it yourself |
| `league_war.yaml` | `seasons: {2024: {games, pa, runs, outs}}` | fetched by `update_constants` (MLB Stats API) |

Files `update_constants` writes (`guts.csv`, `park_fip.yaml`, `park_factors.yaml`, `league_war.yaml`) sit in the same
directory; `woba_fangraphs.yaml`, when you add it, takes precedence over `guts.csv` for the wOBA table.

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
