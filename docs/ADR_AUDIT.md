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
- The formula behind FanGraphs' displayed SIERA (ours matches Baseball Prospectus 2010; FanGraphs runs 0.46 to 0.69 higher).
- The FIP- park input (see ADR-0035 audit note) and Baseball-Reference's ERA+ and OPS+ park factors.
- The GIDP rate and run value behind wGDP; Savant's xERA scale and barrel zone table.
- The 2021 to 2025 kwERA constant term (1.887), measured but not derived.
- Count offsets for `CountExpectancyMatrix`; Stuff+ and Savant expected-stat training data.
- Per-game WPA for Shutdown/Meltdown counts.

## Process gaps
- None of ADR-0026 to ADR-0038 has an Alternatives section; later ADRs should record what was rejected and why.
- Several `matches` claims rest on 3 to 8 fixtures. The tolerance in `tests/golden/pitching.yaml` for ERA- (0.5) is looser than the observed residual (0.32).
- The original Gemini conversation was not available to this audit. The project's written vision (`openspec/project.md`, `AGENTS.md`, the archived golden-validation proposal) was used instead.
