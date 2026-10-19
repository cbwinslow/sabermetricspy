# ADR and Methodology Audit (2026-10-19)

Two research passes re-checked the methodology ADRs (0026 to 0037) and the metrics and models still labeled
`approximate` or `unverified`. Every finding below was re-verified by the main session before a change was made;
findings that did not hold up are listed as such. Source pages were fetched on 2026-10-19; Baseball-Reference
glossary and mlb.com glossary pages are unreachable (403 or 406).

## Corrected
| Finding | Verification | Action |
|---|---|---|
| kwERA used Tango's 5.40; FanGraphs uses a seasonal constant | Recomputed on 13 pitcher seasons (2001 to 2025): kwERA + 12(SO-BB)/TBF is identical for every pitcher in a season | ADR-0038, bundled constants, `kwera` now `matches` |
| Game Score 2.0 "worked example (64)" is not in the FanGraphs article | Re-read the article: it prints the formula only; the 64 was a hand computation | ADR-0030, methodology and spec wording corrected; evidence tier `primary` |
| ADR-0026 says 24 new metrics but lists 29 | Counted the list | Corrected to 29 |
| DER note said Baseball Prospectus defines it as 1 - BABIP | The cited page gives (outs - K)/(BIP - HR) | Note corrected |
| ERA+ note blamed the league choice (the same as ERA-) | Tested the pitcher's own league: it helps Martinez and hurts Johnson and Skubal | Note corrected; code unchanged |
| FIP- note blamed an unbundled park factor column | Tested the ERA- form with the Guts FIP factor (Skubal 2024) and still 0.74 off; the 2001 column is empty | Note and ADR-0035 audit note corrected |
| CatcherFramingModel 0.125 was "secondary" | Savant's framing page states ".125 run/strike" | Evidence tier `primary` |
| BaseRuns display name collided with baserunning BsR; citation read "myth" | Read the source | Renamed `BaseRuns`; citation fixed |

## Findings that did not hold
- "ADR-0035 has five ERA- fixtures, not seven": `tests/golden/pitching.yaml` has seven, and recomputed residuals are within 0.32.
- "WinProbabilityModel should be `divergent`": the status key reserves it for a documented formula that differs from the published method; the model is an empirical approximation, and its note already gives the worst cell (0.19).

## Still open (no accessible primary source)
- FanGraphs displays the 2011 SIERA (confirmed 2026-10-19: its coefficients leave a near-constant 0.47 to 0.49 offset on 16 pitchers), but the per-year coefficients after 2010 are unpublished, so it is not implemented.
- The FIP- park input (see ADR-0035 audit note) and Baseball-Reference's ERA+ and OPS+ park factors.
- The GIDP rate and run value behind wGDP; Savant's xERA scale and barrel zone table.
- The 2021 to 2025 kwERA constant term (1.887), measured but not derived.
- Count offsets for `CountExpectancyMatrix`; Stuff+ and Savant expected-stat training data.
- Per-game WPA for Shutdown/Meltdown counts.

## Process gaps
- None of ADR-0026 to ADR-0038 has an Alternatives section; later ADRs should record what was rejected and why.
- Several `matches` claims rest on 3 to 8 fixtures. The tolerance in `tests/golden/pitching.yaml` for ERA- (0.5) is looser than the observed residual (0.32).
- The original Gemini conversation was not available to this audit. The project's written vision (`openspec/project.md`, `AGENTS.md`, the archived golden-validation proposal) was used instead.

## Vision alignment (original Gemini/Antigravity conversation)

The conversation is stored on this machine under `~/.gemini/antigravity/` (brain id `7ac3ac2d-2472-4d8d-a656-643ce2981c93`;
conversation database in `conversations/`, the uploaded Perplexity research blueprint in `brain/<id>/.user_uploaded/`).
I read the opening request, the user's answers to the six question rounds, and the blueprint's headings and forecasting
section. The stated wishes, and how the repository stands against each:

| What you asked for | Status |
|---|---|
| A calculation engine first, fast on millions of rows, simple core with strong abstractions (rounds 1 to 4) | Met: narwhals expressions, no loops, no I/O (ADR-0003, 0004, 0006) |
| "Cross checks for everything if possible. This is key." (round 2) | Met for 96 metrics with golden or primary evidence; 44 metrics and 13 models remain `approximate` or `unverified`, each with a recorded reason |
| Metrics are static published formulas; models behave like scikit-learn with result objects (rounds 1, 4) | Met (ADR-0014) |
| Where sources differ (the blueprint's "provider-versioning problem": Marcel details, WAR, SIERA), keep named variants | Partly met: Marcel pitcher configuration (ADR-0034), kwERA constant (ADR-0038), `SIERACoefficients.version`; the 2011 SIERA and Baseball-Reference ERA+/OPS+ variants are not offered |
| Use proven tools rather than writing things from scratch (round 4) | Met for the data layer; the estimators (win probability, Markov, linear weights) are written in-house on numpy/scipy |
| All established dependencies in core, immutable results, `StrEnum`, strict typing (rounds 2 to 5) | Met (`pyproject.toml`, ADR-0013, 0016, 0017) |
| YAML for as much as possible (round 6) | Met for constants, presets, methodology |
| Extensible enums and teams for any baseball league (round 3) | Partly met: `Metric`/`Stat` are closed `StrEnum`s extended through `@register_metric` (ADR-0018); park and constants tables are MLB-only, callers pass their own context |
| Evaluation metrics (RMSE, MAE, calibration, Brier) built in from the start (blueprint) | Met by `sabermetricspy.evaluation` (ADR-0039); previously Brier appeared inside two models only |
| Forecasting models: Marcel, Log5, Pythagenpat, Markov, Monte Carlo first; Steamer/ZiPS/PECOTA-style later; Elo/Bradley-Terry listed | Met for the first five; rating systems (Elo, Bradley-Terry) are not implemented |
| Ingestion later and optional | Met (presets and optional extras, ADR-0015) |

No methodology ADR contradicts a stated wish. Forecast evaluation is now met (ADR-0039); the remaining gap worth a change is
the rating systems (Elo, Bradley-Terry), which are published, well-defined methods.

## Follow-up (2026-10-19): independent review and fixes
An independent read-only review of the repository (model: Opus) was checked claim by claim before any change. Confirmed and fixed:

| Finding | How it was checked | ADR |
|---|---|---|
| One call applied one season's constants to every row (2001 wRC+ came back as the 2024 value, 158.6 for both) | Reproduced | 0041 |
| Marcel regressed 4,800 PA instead of 1,200 (.0358 against Tango's .0386 HR/PA for Beltran) | Tango's worked example | 0042 |
| Game Score, Game Score 2.0, Shutdown and Meltdown were evaluated on grouped sums | Read the engine, tests | 0043 |
| Barrels approximated (28) where Statcast labels them (32 = FanGraphs) | Counted `launch_speed_angle == 6` on the sample | 0044 |
| FIP- and xFIP- not in the printed form | FanGraphs Library page; own-league FIP derived and checked against the published MLB FIP in 36 seasons. The printed form is no closer to the 7 fixtures. | 0045 |
| Invalid innings (6.5) became 18 outs, divide-by-zero returned NaN, two sacrifice double-play events were dropped | Reproduced; the event values rest on secondary evidence | 0046 |
| Five pieces with no public method (Stuff+, expected outcomes, framing, OAA, xERA); two failed on real data | Ran them on the Skubal sample | 0047 |

Not yet acted on: the remaining models without a public method (`WinProbabilityModel`, `CountExpectancyMatrix` defaults),
the Empirical Bayes clamps, unused dependencies (pandas, pyarrow, rich), the missing LICENSE, CHANGELOG and CI, and the
silent default constants in `SeasonContext`.
