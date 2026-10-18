# Design

## Context

Findings from the primary-source audit (see proposal.md for motivation). Each was checked against the source and recomputed from raw inputs.

- **Constants:** `woba_fangraphs.yaml` differs from Guts! in 37 of 104 fields (2000, 2001, 2020, 2022, 2024, 2025 wrong; 2021, 2023 right). League ERA/FIP/xFIP are identical placeholders; `lg_hr_per_fb` defaults to an invented 0.115. `get_woba_weights()` silently substitutes the nearest bundled season.
- **wOBA path is correct.** With the true 2001 weights, wOBA is .53669 against FanGraphs' .536696 (data from the FanGraphs leaderboard API), wRAA 117.8 against 117.678, and wRC 200.13 against 200.07. The Bonds gap is entirely the constants.
- **FIP/xFIP** use `ubb` (BB minus IBB); FanGraphs uses BB including IBB (10 pitchers, 2001 and 2016, agree within 0.0004 with IBB and miss by 0.02-0.17 without). DICE already uses BB. FanGraphs returns null xFIP for 2001; its library says the league HR/FB rate "only dates back to 2002".
- **wRC+** follows FanGraphs' shape but divides by `lg_r_per_pa`; FanGraphs divides by AL/NL wRC/PA excluding pitchers. With the true 2001 constants and park factor 1.0 the library gives about 243 against 234.59; the implied non-pitcher denominator is roughly .130. `SeasonContext.park_factor` defaults to 100.
- **Approximations** (read from code and sources): pitcher WAR uses a flat .380 replacement win% and `lg_fip` as RA9; position WAR uses 20 runs/600 PA and PA-scaled positional runs; OPS+/ERA+ apply a single 1/PF; BaseRuns uses Smyth version 2 terms with the version 1 multiplier 1.02 (version 2 is 1.1); Pythagenpat exponent 0.287 vs Baseball-Reference 0.285; SIERA is the original 2010 BP formula labeled `fangraphs_standard`; Marcel pitchers should use 3/2/1 weights and the docstring's 134 IP is unsupported; barrel zone widening is approximate.
- **Verified correct:** wOBA, wRAA, wRC, BABIP, OBP, wSB, kwERA, LOB%, DICE, technical RC, hard-hit 95 mph, sweet-spot 8-32 degrees, and the SIERA sign rule.
- **Tooling constraints:** the FanGraphs API and `curl` hit a Cloudflare challenge; the WebFetch tool returned the Guts! table, library pages, and leaderboard rows. Its output is model-summarized, so every value is recomputed before use. Baseball-Reference `/bullpen` pages return 403; its glossary and WAR pages are reachable.
- The Gemini session's "exact match" audit table (Judge, Cole, Skubal, Burnes) was never encoded in the repo and is treated as unverified.

## Goals / Non-Goals

**Goals:**
- Make published-value agreement a tested, sourced property of the library.
- Make every constant a cited default and every metric honest about whether it follows the published method.
- Correct the three formula/data defects (constants, FIP/xFIP walk term, wRC+ denominator).

**Non-Goals:**
- No new metrics and no new estimators.
- No network access at runtime or in tests (ADR-0003); reference data is fetched during implementation and committed.
- No rewrite of pitcher WAR (follow-on change). No literature sweep (follow-on change: `baseballr`, OpenAlex/arXiv, Tango, Retrosheet research).
- No park-factor model rewrite; park stays caller-supplied.
- No change to the 3-tier naming convention or the provider-agnostic core (YAML remain nomenclature translators).

## Decisions

1. **Reference data is a committed snapshot, not a runtime fetch.** The Guts! table is stored as `tests/golden/guts_snapshot.yaml` (with source URL and retrieval date) and the bundled constants are compared to it field by field. *Alternative:* trust the bundled YAML alone; rejected, since that is how the errors went unnoticed.

2. **Golden fixtures live in YAML under `tests/golden/`**, seeded from FanGraphs leaderboard rows already retrieved: Bonds 2001 (wOBA .536696, wRAA 117.678, wRC 200.071, wRC+ 234.590, WAR 12.4755), five 2001 pitchers (Johnson, Schilling, Mussina, Maddux, Morris), and five 2016 pitchers (Bradley, Koehler, Conley, Perdomo, Fernandez), plus a pre-2000 and a 2020s hitter. Each stores inputs, expected values at full precision, `source_url`, `retrieved`, and `divergence` notes. *Alternative:* Python dicts in tests; rejected because provenance is harder to review.

3. **Tolerances derive from constant rounding.** Constants are published to three decimals, so wOBA tolerance is about 1e-5, FIP about 5e-4 (the 0.0004 residual observed), wRAA about 0.2 runs. A looser tolerance requires a written reason. *Alternative:* half a unit of the displayed precision; rejected because the stored values are full precision and the real error source is constant rounding.

4. **Self-verification gate.** Because fetched values are model-summarized, every fixture entry is recomputed from its raw inputs (wOBA from weights, FIP from totals) before being accepted. An entry that fails recomputation is dropped or documented as divergent.

5. **Constants model: required core, optional extras, no invented defaults.** Guts! columns are required. `lg_era`, `lg_fip`, `lg_xfip`, `lg_hr_per_fb`, and `lg_wrc_per_pa` become optional (`None` when unsourced) with a `source` and `retrieved` field per entry. Dependent metrics return null (xFIP) or fall back with a caveat (wRC+) instead of using made-up values. *Alternative:* keep defaults; rejected because it breaks "never invent unverified constants".

6. **FIP/xFIP walk term.** Use `bb` (total) plus `hbp`; stop requiring `Metric.UBB` in these specs. The cFIP derivation note in the docs uses total BB. FIP-/xFIP- follow because they consume FIP/xFIP. Release notes and the ADR list the changed results.

7. **wRC+ denominator.** Add optional `lg_wrc_per_pa` (non-pitcher, per league) to the constants. If a season is missing it, use `lg_r_per_pa` and add a caveat. The values are sourced from FanGraphs leaderboards (league wRC and PA with pitchers excluded); if the sourced value plus the published park factor still leaves a residual against 234.59, the residual is recorded as a documented divergence rather than hidden by tuning. League (AL/NL) is a `SeasonContext.league` input already present. *Open point:* the Bonds 2001 park factor must be taken from FanGraphs; it is an input to the fixture, not a bundled assumption.

8. **Reference status as a typed field, not free text.** Add a `ReferenceStatus` `StrEnum` (`MATCHES`, `APPROXIMATE`, `DIVERGENT`, `UNVERIFIED`) and a defaulted `reference_status` field on `MetricSpec` (default `UNVERIFIED`), following the Tier-1 naming rule. Non-matching metrics must also fill `caveats`. *Alternatives:* reuse `ImplKind` (rejected: it describes how a metric is computed, not fidelity to a source); caveats-only convention (rejected: not machine-checkable).

9. **Methodology document and its guard.** `docs/METHODOLOGY.md` is a table of metric, formula source URL, status, and note. A test parses it and compares it with the registry in both directions (missing metric, mismatched status). Initial statuses come from this audit; everything not audited is `UNVERIFIED`, which is honest and visible.

10. **Approximations are labeled, not rewritten, in this change.** Pitcher WAR, position WAR, OPS+, ERA+, BaseRuns, SIERA (naming and version note), Marcel pitchers (documented 3/2/1 and removal of the unsupported 134 IP claim), and the barrel zone get status and caveats. Pythagenpat gains an `exponent` option with the documented default and both alternatives (0.285, 0.287) named; the default stays as-is unless the user decides otherwise. BaseRuns: keep the formula, state the multiplier mismatch, and decide in implementation whether to switch to Smyth's version 2 multiplier 1.1 (a result-changing fix to be listed in the ADR) after checking the primer.

11. **Coverage guard.** A test enumerates the registry and checks every metric is in a table of value-asserted metrics (golden fixtures plus hand-computed identities). *Alternative:* line coverage; rejected because it cannot tell whether a value was asserted.

12. **Missing-season fallback keeps returning nearest-year data but warns** (`UserWarning`, once per requested/substituted pair, `stacklevel=2`). *Alternative:* raise an error; rejected because it breaks current callers.

13. **Windows encoding:** reproduce first; fix in the library only if the error originates there, otherwise document `PYTHONIOENCODING`.

## Risks / Trade-offs

- [Model-summarized fetch output mis-transcribes a value] → Recompute from raw inputs (decision 4); cross-check Guts! against a second fetch of the same table and against recomputed wOBA.
- [Sources disagree or revise values] → Fixtures pin retrieval date; a revision is a deliberate update. Where sources conflict (Pythagenpat exponent), the choice is documented and configurable.
- [Behavior changes surprise users] → FIP/xFIP/constants changes are listed with old and new values in the ADR; unbundled-season fallback warns rather than raises.
- [Cannot obtain non-pitcher league wRC/PA for every season] → The constant is optional; fallback is explicit and labeled; wRC+ golden entries are limited to seasons where it is sourced.
- [Hand-entering about 36 seasons is error prone] → Load from a single snapshot and verify with automated field-by-field comparison plus cFIP/wOBA identity checks.
- [Labeling many metrics `UNVERIFIED` looks bad] → That is the truthful state; the table makes the remaining audit work visible and drives the follow-on literature change.
- [Scope is larger than the first plan] → Pitcher WAR rewrite and the literature sweep are explicitly deferred.

## Migration Plan

Additive except the listed behavior changes. Rollback is reverting the YAML, formulas, and warning. Numeric results change for the corrected seasons and for FIP/xFIP/FIP-/xFIP- with intentional walks. `MetricSpec.reference_status` is defaulted, so existing custom and plugin metrics keep working and appear as `UNVERIFIED`.

## Open Questions

- Which additional player seasons (beyond the retrieved Bonds 2001 and ten pitchers) to include; any set satisfies the specs.
- Whether to switch BaseRuns to the version 2 multiplier 1.1 or keep 1.02 with a label; decided during implementation after reading the primer, and recorded in the ADR.
