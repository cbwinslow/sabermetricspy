# ADR-0027: Published-Method Conformance, Sourced Constants, and Reference Status

- **Status**: Accepted
- **Date**: 2026-10-18
- **OpenSpec change**: `golden-validation-and-constants`

## Context
A primary-source audit (FanGraphs Library, Guts!, FanGraphs leaderboard rows, Baseball-Reference, Baseball Savant,
Tango, Swartz/Seidman; every fetched figure recomputed from raw inputs) found that the library did not reproduce
what it claimed to reproduce:

- The bundled seasonal constants differed from the FanGraphs Guts! table in 37 of 104 checked fields; league ERA,
  FIP and xFIP were identical placeholders; `lg_hr_per_fb` defaulted to an invented 0.115.
- FIP and xFIP used unintentional walks; FanGraphs uses total BB including IBB (verified on 10 pitchers in 2001 and
  2016: within 0.0004 with IBB, off by 0.02 to 0.17 without).
- wRC+ divided by league R/PA; FanGraphs divides by the AL/NL wRC/PA excluding pitchers.
- Several metrics are approximations of the published method but presented without any signal.
- Accuracy was tested only with loose thresholds; an earlier "exact match" audit was never encoded in the repo.

## Decision
1. **Constants are sourced snapshots.** `tests/golden/guts_snapshot.yaml` (Guts!, 1990-2025),
   `league_totals_snapshot.yaml` (FanGraphs league totals) and `np_wrc_snapshot.yaml` (non-pitcher wRC and PA by
   league) are committed, each fetched or validated twice and checked by recomputation (ERA from ER/IP; FIP from
   raw totals plus cFIP; OBP/SLG from counts; wOBA from weights). `woba_fangraphs.yaml` is regenerated from them and
   `tests/test_constants.py` compares every field. League ERA/FIP/xFIP/HR-FB and `lg_wrc_per_pa{,_nl,_al}` are
   optional and absent rather than defaulted; xFIP is null before 2002 (FanGraphs publishes league HR/FB only from 2002).
2. **FIP and xFIP use total BB (including IBB) plus HBP.** The league-total check confirms cFIP is derived the same way
   in every season 1990-2025.
3. **wRC+ divides by the AL/NL (or MLB) non-pitcher wRC/PA** when the season has the constant, falling back to league
   R/PA with a caveat. Park factor remains caller-supplied; the default of 100 means no park adjustment.
4. **Unbundled seasons warn.** `get_woba_weights` still returns the nearest bundled season but emits a `UserWarning`
   (once per requested/substituted pair).
5. **Every metric carries a `ReferenceStatus`** (`MATCHES`, `APPROXIMATE`, `DIVERGENT`, `UNVERIFIED`). The audit lives
   in `src/sabermetricspy/data/methodology.yaml`, is applied to each `MetricSpec` at registration (with the note added
   to `caveats` for non-matching metrics), and `docs/METHODOLOGY.md` is rendered from it; tests compare the document,
   the data and the registry. 97 of 136 metrics are honestly `UNVERIFIED` pending the follow-on literature change.
6. **Golden fixtures** (`tests/golden/batting.yaml`, `pitching.yaml`): 15 FanGraphs rows with source, retrieval date and
   tolerances derived from the three-decimal rounding of the constants. A raw-arithmetic gate confirms each fixture
   before the library is compared with it. `ERA-`/`FIP-` are documented divergences (FanGraphs uses league-specific
   values and its own park adjustment).
7. **BaseRuns** follows Smyth: multiplier 1.02 for basic columns (version 1) and 1.1 when HBP, IBB, SB, CS or GDP are
   supplied (version 2). **Pythagenpat** gains `SeasonContext.pythagenpat_exponent` (default 0.287; Baseball-Reference
   uses 0.285). **SIERA** coefficients are labeled `baseball_prospectus_2010`.
8. **`CalculationResult.__repr__` is ASCII-safe**, fixing `UnicodeEncodeError` when printing on cp1252 consoles.
9. **Speed Score is Bill James's four-factor definition**: total BB and HBP in the attempt-rate denominator, `AB-HR-SO` triples denominator with divisor 0.0016, each factor limited to 0-10 (NaN preserved), mean of four, `so` required. The six-factor form (GIDP, defensive position) is not implemented because its constants rest on a single secondary source.
10. **Pitcher WAR is the documented FanGraphs method** (library page + the complete Stroman 2016 worked example): ifFIP with infield flies and the MLB ifFIP constant, FIPR9 = ifFIP + (lgRA9 - lgERA), FIP park factor, AL/NL league FIP, dynamic runs per win, 0.12/0.03 replacement wins per game, reliever leverage multiplier (1 + gmLI) / 2, and an optional league correction. Inputs are bundled AL/NL pitching totals 1990-2025 (`data/constants/pitcher_war.yaml`, AL + NL = MLB checked). Every figure of the worked example is reproduced. Against 29 live leaderboard pitchers (2016 and 2024), 27 are within 0.25 WAR (median under 0.1); exceptions are one mixed starter/reliever line (FanGraphs values roles separately) and one unexplained starter (+0.42). No input variant (basic vs FIP park factor, own vs MLB league, infield flies on/off) explains the 2016 residuals, and FanGraphs publishes the league correction for 2016 only, so other seasons are uncorrected (typically about -0.15 WAR per 200 IP).

## Consequences: numeric changes
| Quantity | Before | After |
| :-- | :-- | :-- |
| Bonds 2001 wOBA (published .5367) | 0.5371 | 0.5367 |
| Bonds 2001 wRAA (published 117.7) | 114.64 | 117.80 |
| Bonds 2001 wRC+ (published 234.59) | 237.02 | 234.61 default call; 234.41 with NL and park factor 96 |
| Maddux 2001 FIP (published 3.1178) | 2.9889 | 3.1177 |
| BaseRuns on the shared test line (basic + extra columns) | 17.8619 | 18.5333 |
| xFIP for seasons before 2002 | invented 0.115 HR/FB | null |
| Speed Score on a 10 SB, 2 CS, 150 H, 500 AB, 90 R line | 4.62 (no square root in the attempt rate, wrong triples denominator, unclamped) | 6.07 |
| Pitcher WAR, Stroman 2016 (FanGraphs 3.6) | different method (flat .380 replacement), not comparable | 3.60 |
| Pitcher WAR, Fernandez 2016 (FanGraphs 6.35) | different method, not comparable | 6.15 |

2000, 2001 and 2020-2025 constants changed throughout; 1990-1999 and 2002-2019 were added.

## Not in this change (follow-on changes)
- Reproducing FanGraphs' live pitcher WAR exactly (unpublished refinements; per-year league corrections other than 2016) and
  valuing mixed starter/reliever lines by role from split statistics.
- The literature sweep: review of `baseballr`, OpenAlex/arXiv baseball ML papers, Tom Tango's book and blog, and the
  Retrosheet research page, to audit the 97 unverified metrics and add further published methods.
- Sourcing `lg_wsb`, `lg_gidp_rate` and `r_gidp`, and league-specific ERA-/FIP-/ERA+.
