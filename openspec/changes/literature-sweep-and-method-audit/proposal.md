# Proposal

## Why

After `golden-validation-and-constants`, 97 of the 136 built-in metrics are honestly marked `unverified` in `src/sabermetricspy/data/methodology.yaml`: nobody has checked their formulas against a primary source, and the library's purpose is to reproduce what researchers and the major sites publish. The same audit found real defects in metrics nobody had checked (FIP/xFIP walk term, wRC+ denominator, Speed Score, BaseRuns multiplier), so the remaining 97 should be assumed to hide more until shown otherwise. Separately, the project owner asked for a systematic look at the published literature (the `baseballr` package, OpenAlex and arXiv papers, Tom Tango's work, and the Retrosheet research page) to decide which further methods belong in the library, which has never been done.

## What Changes

- **Audit all 97 unverified metrics** against primary sources (FanGraphs Library, Tango's wiki archive, Baseball Savant glossary, Baseball-Reference glossary where reachable, original author publications). Each ends as `matches`, `approximate`, or `divergent` with a source URL, an evidence tier (`golden`, `primary`, or `secondary`), and a note; none may remain `unverified`.
- **Add golden fixtures wherever a published value can be fetched and recomputed.** The FanGraphs leaderboard exposes counts and published rates for the batted-ball family (GB/FB/LD/IFFB, Pull/Cent/Oppo, HR/FB), K%+/BB%+, K-BB%, pitcher rates, and plate-discipline rates; pitch-level checks use public Statcast data where retrievable. Fetched values are recomputed from raw inputs before use.
- **Fix clear formula defects** found by the audit, with before/after numbers recorded in an ADR; label (do not silently change) metrics whose method varies by source.
- **Audit the 16 non-metric models** (Log5, RE24, linear weights, win probability, Markov, Monte Carlo, expected-outcome and others) where a published table or formula exists; a model may remain `unverified` only with a written reason that no published reference exists.
- **Produce `docs/LITERATURE.md`**: a prioritized, sourced catalogue of candidate methods not yet in the library (name, formula source, inputs, fit with the provider-agnostic Narwhals design, validation target, difficulty), plus a `baseballr` coverage analysis. Each catalogued method becomes its own later change.
- **Record a repeatable sweep procedure** (`docs/LITERATURE_SWEEP.md`) and a small query tool under `tools/` that runs the OpenAlex and arXiv searches, respects each service's terms, and stores metadata only.
- **Add guards**: a test that no built-in metric is `unverified`, and that every status carries an evidence tier.

Source coverage findings from planning (verified 2026-10-18): OpenAlex and arXiv APIs work without credentials; `baseballr` (pkgdown 2.0.0, about 460 reference entries) is mostly a data-acquisition package with only four metric functions (`woba_plus`, `fip_plus`, `team_consistency`, `run_expectancy_code`); the Retrosheet research page is `retrosheet.org/Research/Research.htm`; *The Book* is a book and cannot be retrieved, so Tango's wiki archive (92 pages covering most of the unverified metrics) and blog stand in, and where only the book states a formula the metric is labeled with that limitation.

**Out of scope:** implementing the newly catalogued methods, the position-player WAR rewrite, and sourcing `lg_wsb`, `lg_gidp_rate`, and `r_gidp` except where needed to verify wSB, wGDP, or BsR.

**Assumptions recorded:** copyrighted text is not reproduced (only metadata, our own summaries, and short formula citations); no email address or personal data is sent to any service; request rates stay within each service's published limits.

## Capabilities

### New Capabilities
- `literature-catalogue`: the sourced catalogue of candidate methods, the `baseballr` coverage analysis, and the repeatable, terms-respecting sweep procedure.

### Modified Capabilities
- `metric-method-fidelity`: every built-in metric has a resolved status with an evidence tier; models may stay unverified only with a written reason.
- `golden-reference-validation`: fixtures extend to the batted-ball, K%+/BB%+, plate-discipline, and other families where a published value can be fetched.

## Impact

- Data: `src/sabermetricspy/data/methodology.yaml` (statuses, sources, evidence tiers), possibly new constants if a verified metric needs one.
- Code: `methodology.py` (evidence field and table column); metric formulas only where the audit finds a clear defect.
- Tests: new golden fixtures and tests under `tests/golden/`, a no-unverified guard, an evidence-tier guard, tool tests on recorded responses.
- Docs: regenerated `docs/METHODOLOGY.md`, new `docs/LITERATURE.md` and `docs/LITERATURE_SWEEP.md`, a new ADR.
- New directory `tools/` for the sweep script (not part of the installed package).
- No new runtime dependencies; the sweep tool uses the standard library.
