# ADR-0049: Count Run Values Follow Walsh, and RE288 Is Fitted, Not Defaulted

Status: Accepted

## Context
`CountExpectancyMatrix` shipped a built-in 288-state table made by adding 12 "count offsets" to the RE24 table, scaled by
1.15, 1.00 or 0.80 depending on outs. The offsets were labelled Tango/Roegele but no source had been retrieved. Checked
against John Walsh's Table 1 in "Searching for the game's best pitch" (The Hardball Times, 2008-02-26), 7 of the 12 were
mistranscribed (2-0, 3-0, 0-1, 2-1, 3-1, 2-2 and 3-2). The outs scale had no source at all, and Tom Tango's published RE288
shows the count effect depends on the base state (3-0 is +.23 runs with the bases empty and +.57 with them loaded at no
outs), so an additive offset is the wrong shape. `fit()` also averaged over pitches, so repeated two-strike fouls
over-weighted 0-2, 1-2, 2-2 and 3-2, and states with no data silently kept the invented values. `count_leverage` used a
made-up +0.12 for a walk.

## Decision
- `WALSH_COUNT_RUN_VALUES` holds Walsh's 12 values; `count_run_value(balls, strikes)` reads them. Every cell is pinned by
  `tests/golden/count_run_values.yaml`, and four cells agree with the Retrosheet 2016 values printed in Albert, Baumer and
  Marchi, *Analyzing Baseball Data with R* 3e, chapter 6, to within 0.006 runs.
- `DEFAULT_RE288_TABLE`, the outs scale and `CountExpectancyMatrix.from_default()` are deleted. `fit()` is the only way to
  get a table, and states with no data stay unfitted: `lookup` and `count_leverage` return `None`, and `transform` gives
  null.
- `fit()` needs a `pa_id` column and uses only the first pitch at each count in each plate appearance (the ABDWR
  convention). Shrinkage is off by default and only moves toward a prior the caller passes in.
- A walk in `count_leverage` goes to the forced-advance base state at 0-0 plus any run forced in.
- `bf_per_ip` is kept: it is SABR's BFP/IP (batters faced over innings pitched), a plain ratio with a hand-computed test.
  The citation moves from "Baseball-Reference Glossary" to SABR, and the stale mention of the deleted xERA is removed.

## Alternatives
- Ship Tango's RE288 as the default: not chosen now, because it is printed only as images, names no seasons, and its 0-0
  cell (.51) does not match our FanGraphs RE24 (.461); revisit if it is published as text with stated seasons.
- Default table fitted from Statcast `delta_run_exp`: not chosen now, because Savant documents neither its seasons nor its
  table and our fixture lacks outs and bases; revisit if Savant documents it.
- Bundle a table fitted from Retrosheet 2016 (abdwr3edata, CC0): not chosen now, because only four aggregates are printed
  to check it against and it adds 2.8 MB plus Retrosheet notice terms; revisit if an opt-in test reproduces ABDWR.
- Keep an additive RE24 + count prior for shrinkage: not chosen now, because Tango's table contradicts it; revisit if a
  published smoothing method for RE288 appears.

## Consequences
Anyone relying on `from_default()` must fit a table. `RE288Results.total_pitches` is now `total_plate_appearances`.
`CountExpectancyMatrix` stays `unverified` because no outside value reproduces `fit()`; the Walsh values themselves match.
Tests: `tests/test_count_expectancy.py`.
