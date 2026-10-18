## Context

The FanGraphs Library article "5 Year Regressed Park Factors" (https://library.fangraphs.com/park-factors-5-year-regressed/) gives: raw PF = H*T / ((T-1)*R + H) with home and road runs per game H and R and T teams; iPF = (raw + 1)/2; final = 1 - (1 - iPF)*X with X = 0.6, 0.7, 0.8, 0.9 for 1, 2, 3, 4 or more years. The Guts! page states its factors are already halved for full-season use.

## Decisions

1. **Pure scalar and column functions**, no provider coupling: inputs are runs and games (or runs per game) per team, home and road. Output is a factor with 1.00 neutral; a helper converts to the library's 100 scale.
2. **Regression constant as a documented table** `YEARS_TO_REGRESSION = {1: 0.6, 2: 0.7, 3: 0.8, 4: 0.9}` with 4 or more years using 0.9; the multi-year window selection (centered, up to five seasons, edge handling) is documented but left to the caller, since choosing a window needs data this library does not hold.
3. **Bundled table is a sourced snapshot** of Guts! 2024 (two fetches agree on 5-year and HR; the 1-year column came from one fetch and is noted as such). Park ids are not invented: `park_id` equals the team abbreviation.
4. Validation: the article's worked examples (home 11 / road 10 with 30 teams gives 330/301 = 1.096, which the article rounds to 1.10, and composite 1.048, rounded to 1.05; the article's own 1.10 is the simple H/R, so tests assert the formula value and that it rounds to the printed figure; iPF 1.25 regresses to 1.15, 1.175, 1.20, 1.225) and the Guts! table.

## Risks

- The article prints no published raw-to-final player-park example, so the full pipeline is validated through its arithmetic examples, not a recomputed park.
- The 5-year Guts! values cannot be recomputed here without five seasons of home and road splits.
