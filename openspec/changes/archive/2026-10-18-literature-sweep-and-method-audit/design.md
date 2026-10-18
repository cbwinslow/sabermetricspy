# Design

## Context

State after `golden-validation-and-constants` (see proposal.md for motivation):

- `data/methodology.yaml` holds an audit entry per built-in metric (`status`, `source_url`, `note`): 28 matches, 11 approximate, 97 unverified. 16 non-metric models carry entries, 14 unverified. `methodology.py` loads it, the registry applies it at registration, and `docs/METHODOLOGY.md` is generated from it with consistency tests.
- The 97 unverified metrics by family: plate discipline 18, batting 14, pitch physics 12, batted ball 10, pitching 10, DIPS and indexed pitching 6, fielding 6, Statcast expected 5, team 5, weighted offense 4, expectancy 4, baserunning 3.
- **Source reality, checked 2026-10-18:** the FanGraphs leaderboard API (reachable through the fetch tool, not through scripted `curl`) returns, per pitcher row, counts and published rates for batted-ball type and direction (`GB`, `FB`, `LD`, `IFFB`, `Pull`, `Cent`, `Oppo`, `HR/FB`, `GB%`...), `K%`, `BB%`, `K-BB%`, `K%+`, `BB%+`, `K/9+`, `LOB%`, plate-discipline rates (`O-Swing%`, `Z-Swing%`, `Swing%`, `O-Contact%`, `Z-Contact%`, `Contact%`, `Zone%`, `F-Strike%`, `SwStr%`, `CStr%`, `C+SwStr%`), `QS`, `SV`, `xERA`, `kwERA`, `SIERA`, and Statcast `EV`, `LA`, `Barrels`, `HardHit`. Plate-discipline rates come without swing counts. Tango's wiki archive (92 pages) has pages for Gross Production Average, Total Average, Secondary Average, Runs Created, ERA+, Pythagorean/PythagenPat, Win Expectancy, Leverage Index, Range Factor, DER and Fielding Percentage. Baseball-Reference `/bullpen` pages return 403; its glossary and WAR pages are reachable. OpenAlex and arXiv APIs work without credentials. `baseballr` is a data-acquisition package with four metric functions. The Retrosheet research page is at `retrosheet.org/Research/Research.htm`. *The Book* cannot be retrieved.
- Lessons carried over: summarizing fetch tools can mis-transcribe, so every value is recomputed from raw inputs; `curl` against Cloudflare-protected hosts is not circumvented; recalled numbers are never trusted (two claims in the previous change were corrected during implementation).

## Goals / Non-Goals

**Goals:**
- Resolve all 97 metrics to a status backed by an evidence tier and a source, with numeric golden evidence wherever a published value exists.
- Fix or label every difference found; leave no silent divergence.
- Deliver a defensible, prioritized catalogue of further methods and a procedure to repeat the sweep.

**Non-Goals:**
- No implementation of catalogued methods, no position-player WAR rewrite, no new runtime dependency.
- No scraping behind bot protection, no storage of paper text, no personal data sent to any service.
- No attempt to settle disputes between sources: where reputable sources differ the metric is labeled approximate and the implemented variant named.

## Decisions

1. **Evidence tiers are first-class data.** Each audit entry gains `evidence: golden | primary | secondary`. Status `matches` requires golden or primary; secondary evidence can support `matches` only with a note naming the limitation, and is visible in `docs/METHODOLOGY.md`. The existing 39 audited entries are backfilled (golden for the FanGraphs-fixture metrics, primary for formula-confirmed ones, secondary for DICE). *Alternative:* a free-text note only; rejected because it is not machine-checkable.

2. **Audit by family, strongest evidence first.** Order: batted ball (counts and rates on the FanGraphs leaderboard: true golden), batting and pitching rates (Tango wiki and FanGraphs Library plus leaderboard rates such as `K-BB%`, `K%+`), plate discipline (definitions from the FanGraphs Library; numeric check on a recorded pitch-level sample), Statcast expected and pitch physics (Savant glossary plus leaderboards or a sampled CSV), fielding/baserunning/team/expectancy (Tango wiki pages), then models. *Alternative:* alphabetical; rejected because evidence quality varies by family.

3. **Pitch-level sample, with a fallback that does not circumvent protection.** For plate discipline and pitch physics the plan is a small public Statcast sample (one pitcher-game or a short window) retrieved through an endpoint that allows ordinary requests; its counts are produced by the library's own statcast preset and compared with published per-player rates. If no such endpoint is reachable, those metrics are audited at the primary tier (definitions) and the note says no numeric check was possible. *Alternative:* hand-typed pitch counts; rejected as unverifiable.

4. **Recomputation gate for every fetched value** (carried over): published rates are recomputed from published counts before a fixture is accepted; entries that fail are dropped or recorded as divergences.

5. **Fix versus label rule.** A formula is *fixed* when a primary source states a different definition and no reputable variant matches the library (as with FIP's walk term); it is *labeled approximate* when reputable sources define it differently (as with kwERA) or the library intentionally adopts one variant; it is *divergent* when the documented formula contradicts the primary source and a fix would change many users' results without a clear canonical choice. Fixes follow TDD with the published value as the test and before/after numbers in the ADR.

6. **Models are audited only where a reference exists.** RE24 against a published run-expectancy table, Log5 against its formula, linear weights against Guts! weights where a comparable run-expectancy input is available, win probability against a published win-expectancy table. A model with no published reference stays `unverified` with a written reason (enforced by test).

7. **Catalogue method.** Queries: OpenAlex and arXiv topic queries recorded verbatim with dates; Tango wiki and blog pages; Retrosheet research papers (including Charlie Pavitt's bibliography); the `baseballr` reference index. An entry needs a primary-source citation with a published formula; otherwise it goes to a rejected-with-reason list. Ranking uses the recorded criteria (published formula, inputs in the canonical schema, validation target, provider-agnostic fit, value, difficulty) so it can be re-derived. `docs/LITERATURE.md` records coverage per requested source, including that *The Book* is not retrievable and which substitute was used.

8. **Sweep tool.** `tools/literature_sweep.py` uses only the standard library, queries OpenAlex and arXiv, waits at least three seconds between arXiv requests, sends no email or key, and normalizes results to identifiers, title, authors, year, venue, license, and landing URL. Parsing is tested offline on recorded responses under `tests/fixtures/literature/`. It is excluded from the wheel (only `src/sabermetricspy` is packaged) and added to pyright's include list. *Alternative:* a package dependency such as `pyalex`; rejected to avoid a runtime dependency for a maintenance tool.

9. **Terms and licensing.** Only bibliographic metadata and our own short summaries are stored; the arXiv and OpenAlex terms linked in `.licenses/` are cited in the procedure; paper licenses are recorded as returned.

## Risks / Trade-offs

- [Fetch-tool transcription errors] → Recompute from raw inputs; cross-check a second retrieval for any value that decides a status.
- [Many metrics can only reach the primary tier] → That is an honest outcome; the table shows the tier and the catalogue notes where a future numeric check is possible.
- [Fixing a defect changes users' numbers] → Fixes are limited to clear defects, recorded with before/after values, and tested against the published value.
- [Source disagreement stalls the audit] → The approximate label with named variants resolves it without picking a winner.
- [Scope size (97 metrics, 16 models, a catalogue)] → Family batches with a commit per batch; the catalogue and tool are independent of the audit and can land separately.
- [Rate limits or terms change] → The procedure cites the terms and the tool's interval is configurable; limits are documented, not hard-coded assumptions about other services.

## Open Questions

- Which public Statcast endpoint allows a small pitch-level sample to be retrieved without circumventing protection? Resolved in the first plate-discipline task; either outcome satisfies the specs (numeric check or primary tier with a note).
- Target catalogue size (planned 15 to 30 entries); any size satisfies the specs.
