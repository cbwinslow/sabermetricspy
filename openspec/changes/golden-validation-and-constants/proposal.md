# Proposal

## Why

The library's purpose is to reproduce what baseball researchers and the major sites publish, from source-agnostic formulas, with provenance on everything (`AGENTS.md`: "Never invent unverified constants"). A primary-source audit (FanGraphs Library, Guts!, FanGraphs leaderboard rows, Baseball-Reference, Baseball Savant, Tango, Swartz/Seidman; recomputed from raw inputs) shows it does not yet do that:

- **Bundled constants are wrong.** `woba_fangraphs.yaml` differs from the FanGraphs Guts! table in 37 of 104 checked fields; only 2021 and 2023 match. The 2025 row is mostly 2024 values. `lg_era`, `lg_fip`, and `lg_xfip` are identical placeholders in every season, and `lg_hr_per_fb` defaults to an unsourced 0.115.
- **FIP and xFIP use the wrong walk term.** We use unintentional walks; FanGraphs uses total BB including IBB. On 10 pitchers (2001, 2016) FanGraphs FIP matches within 0.0004 when IBB is included and is off by 0.02 to 0.17 when it is excluded.
- **wRC+ uses the wrong league denominator.** FanGraphs divides by the AL/NL wRC/PA with pitchers excluded; we divide by league R/PA.
- **Several metrics are approximations presented as the published method** (pitcher and position-player WAR, OPS+, ERA+, BaseRuns, Pythagenpat, SIERA labeling, Marcel pitchers, barrel zone) with no signal to the user.
- **Accuracy is not tested against published values.** The golden test asserts thresholds, and the Gemini session's "exact match" audit table was never encoded in the repo, so it is unverified.

The Bonds 2001 gap that started this is now explained: the wOBA and wRAA gaps come from wrong 2001 weights (true weights give wOBA .53669 against FanGraphs' .536696 and wRAA 117.8 against 117.7). The wRC+ figure I first quoted (259) was Baseball-Reference's OPS+; FanGraphs' wRC+ is 234.59.

## What Changes

- Replace the bundled constants with the FanGraphs Guts! values for every season in 1990-2025, each entry citing its source and retrieval date; add sourced `lg_era`, `lg_fip`, `lg_xfip`, and league HR/FB where published (FanGraphs states the HR/FB rate only dates back to 2002), and stop defaulting to invented values.
- **BEHAVIOR CHANGE**: FIP, xFIP, and the derived FIP-/xFIP- use total BB (including IBB) plus HBP, matching FanGraphs. Results change for pitchers with intentional walks.
- **BEHAVIOR CHANGE**: xFIP evaluates to null when no sourced league HR/FB exists for the season, instead of using an invented default.
- **BEHAVIOR CHANGE**: requesting weights for an unbundled season emits a `UserWarning` naming the substituted season; values are unchanged.
- Add an optional league non-pitcher wRC/PA constant and use it as the wRC+ denominator when present, falling back to the current behavior (with a documented caveat) when absent.
- Add a golden fixture set built from FanGraphs leaderboard rows (and Baseball-Reference where reachable) with source URL, retrieval date, and tolerance per entry; assert exact values; remove threshold assertions.
- Add per-metric value tests and a guard that fails when a registered metric has no value assertion.
- Add a reference-status label on every metric spec (matches published method, approximate, divergent, unverified) and a `docs/METHODOLOGY.md` table of metric, source, and status with URLs. Metrics found approximate are labeled, not silently changed: pitcher WAR, position-player WAR, OPS+, ERA+, BaseRuns (version 2 terms with the version 1 multiplier), Pythagenpat exponent (0.287 vs Baseball-Reference's 0.285; made configurable), SIERA (original 2010 formula labeled `fangraphs_standard`), Marcel pitchers (3/2/1 weights, unsupported 134 IP), and the barrel zone.
- Fix the Windows `UnicodeEncodeError` on printing results if it originates in the library.
- **Added after the audit (user request):** make Speed Score follow Bill James's published four-factor formulas (correct denominators, 0-10 clamping), and rebuild pitcher WAR on the documented FanGraphs method (ifFIP with infield flies, FIP-to-RA9 conversion, FIP park factor, AL/NL league FIP, dynamic runs per win, 0.12/0.03 replacement wins per game, reliever leverage multiplier, optional league correction), validated step by step against FanGraphs' published Stroman 2016 worked example and compared with live leaderboard WAR.

**Out of scope, recorded as follow-on changes:**
- Reproducing FanGraphs' *current* leaderboard pitcher WAR exactly: the documented method matches the published worked example, but live 2016 values differ by up to about 0.2 WAR for reasons FanGraphs does not publish, and per-year league corrections are published only for 2016.
- Position-player WAR, Speed Score's six-factor form (GIDP and defensive position), and the other approximate metrics.
- The literature sweep: review of `baseballr`, OpenAlex/arXiv baseball ML papers, Tom Tango's book and blog, and the Retrosheet research page, to add and verify further published methods.

Citations: Tango/Lichtman/Dolphin (2007) *The Book*; FanGraphs Library (wOBA, wRC+, FIP, xFIP, WAR, BsR, BABIP) and Guts!; Baseball-Reference glossary and WAR explained; Swartz/Seidman (2010) SIERA; Smyth BaseRuns Primer; Tango (2004) Marcel; Baseball Savant glossary.

## Capabilities

### New Capabilities
- `golden-reference-validation`: published-value accuracy contract for offensive and pitching metrics, with sourced fixtures, tolerances, and a guard ensuring every registered metric has a value assertion.
- `seasonal-constants`: coverage, provenance, and lookup behavior of bundled seasonal weights and league constants, including missing-data handling.
- `published-formula-conformance`: metric definitions that must follow the published method (walk term in FIP/xFIP, league denominator in wRC+).
- `metric-method-fidelity`: reference-status labeling of every metric and the published methodology table.
- `pitcher-war`: FanGraphs-method pitcher WAR with sourced AL/NL run-environment constants, validated against the published worked example.

### Modified Capabilities
<!-- None. The existing specs do not state the formulas or constants affected here. -->

## Impact

- Code: `constants/__init__.py` and `types/context.py` (warning, optional constants, no invented defaults), `metrics/pitching.py` (FIP, xFIP, derived minus-metrics), `metrics/weighted.py` (wRC+ denominator), `registry/__init__.py` (reference-status field), `metrics/specialized.py` and `models` (labels, Pythagenpat exponent option), and the display of results if the encoding error is in the library.
- Data: `data/constants/woba_fangraphs.yaml` rewritten and extended; park factors reviewed.
- Tests: `tests/golden/*.yaml`, `tests/test_golden_values.py`, `tests/test_constants.py`, a metric-coverage guard, a methodology-doc consistency test; threshold test removed.
- Docs: new `docs/METHODOLOGY.md`, an ADR in `docs/DECISIONS.md` and `docs/decisions/`, README and `ARCHITECTURE.md` notes.
- Numeric results change for 2000, 2001, 2020-2025 constants and for FIP/xFIP/FIP-/xFIP- with intentional walks; the ADR lists old and new values.
- Dependencies: none added. Reference data is fetched once during implementation and committed.
