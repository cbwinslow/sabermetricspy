# Tasks

## 1. Reference snapshot and constants

- [x] 1.1 Store the FanGraphs Guts! table (1990-2025) as `tests/golden/guts_snapshot.yaml` with source URL and retrieval date; re-fetch once and diff against the first copy. Verify the two copies agree and a structure test loads the file.
- [x] 1.2 Add `tests/test_constants.py` comparing every bundled field to the snapshot, rejecting identical `lg_era`/`lg_fip`/`lg_xfip`, and requiring `source` on each entry. Verify it fails on the current YAML (37 field differences) before any fix.
- [x] 1.3 Make `lg_era`, `lg_fip`, `lg_xfip`, `lg_hr_per_fb`, and `lg_wrc_per_pa` optional with per-entry `source`/`retrieved` in the constants model; remove invented defaults. Verify `WOBAWeights` validates entries with and without them and existing callers import cleanly.
- [x] 1.4 Rewrite `woba_fangraphs.yaml` from the snapshot for 1990-2025 and add league ERA/FIP and HR/FB (2002+) only where a source is cited. Verify the 1.2 test passes and the cFIP/league-wOBA identity checks pass within tolerance.
- [x] 1.5 Make `get_woba_weights()` emit a `UserWarning` once per requested/substituted pair for unbundled seasons. Verify with `pytest.warns` for a missing season and an error-on-warning filter for a bundled one.

## 2. Formula conformance

- [x] 2.1 Write failing tests for FIP and xFIP with intentional walks (Maddux 2001: 3.1177; 2016 pitchers) and for xFIP null without a league HR/FB rate. Verify they fail on the current code.
- [x] 2.2 Change FIP and xFIP to use total BB plus HBP and xFIP to return null when the rate is absent; update `requires`, `required_columns`, LaTeX, and docs; confirm FIP-/xFIP- follow. Verify the 2.1 tests and the existing suite pass.
- [x] 2.3 Source non-pitcher league wRC/PA (AL/NL) for the seasons used by wRC+ fixtures from FanGraphs leaderboards, recompute it from league wRC and PA, and store it with source. Verify the stored value reproduces the published wRC+ for Bonds 2001 once the park factor is supplied, or record the residual as a documented divergence.
- [x] 2.4 Use `lg_wrc_per_pa` in `calc_wrc_plus` with fallback to `lg_r_per_pa` plus a caveat when absent; document that park factor 100 means no adjustment. Verify wRC+ is unchanged without the constant and the Bonds 2001 test passes with it.

## 3. Golden fixtures and value tests

- [x] 3.1 Create `tests/golden/batting.yaml` and `tests/golden/pitching.yaml` from the retrieved FanGraphs rows (Bonds 2001; Johnson, Schilling, Mussina, Maddux, Morris 2001; Bradley, Koehler, Conley, Perdomo, Fernandez 2016) plus a pre-2000 and a 2020s hitter, each with source URL, retrieval date, and tolerance. Verify a structure test rejects a missing URL or date.
- [x] 3.2 Add a recomputation gate test: wOBA and FIP of each fixture row reproduced from its raw inputs within tolerance. Verify it passes for all rows and fails for a deliberately altered value.
- [x] 3.3 Add `tests/test_golden_values.py` asserting every published metric within tolerance, with failure messages naming metric, expected, actual, and source. Verify it passes, with any documented divergences listed.
- [x] 3.4 Remove the threshold assertions (`woba > 0.530`, `wrc_plus > 230`) from `test_golden_barry_bonds_2001_and_pedro_martinez_2000`. Verify the full suite passes and run one batting and one pitching fixture on Polars, pandas, and PyArrow to confirm agreement within 1e-9.
- [x] 3.5 Add hand-computed value tests for every registered metric not covered by fixtures (table of metric, small input, expected value, derivation in a comment) and a coverage guard failing on any uncovered metric. Verify the guard fails when an entry is temporarily removed.
- [x] 3.6 Add a Hypothesis identity test for rates built from summed counts (`OPS = OBP + SLG`, `ISO = SLG - AVG`). Verify with `uv run pytest -k identity`.

## 4. Reference status and methodology

- [x] 4.1 Add the `ReferenceStatus` enum and a defaulted `reference_status` field on `MetricSpec` with a guard listing `UNVERIFIED` metrics. Verify existing plugin and YAML-defined metrics still register and show `UNVERIFIED`.
- [x] 4.2 Label verified metrics `MATCHES` (wOBA, wRAA, wRC, BABIP, OBP, wSB, kwERA, LOB%, DICE, technical RC, hard-hit, sweet-spot) and set wRC+ after task 2.4. Verify the status appears in `sabermetrics info <metric>`.
- [x] 4.3 Label and caveat the approximations: pitcher WAR, position-player WAR, OPS+, ERA+, BaseRuns (multiplier), Pythagenpat (add `exponent` option, default and sources documented), SIERA (2010 BP version, rename `fangraphs_standard`), Marcel pitchers (3/2/1, remove the unsupported 134 IP claim), and the barrel zone. Verify each caveat names the published method and the new option behaves as specified.
- [x] 4.4 Decide the BaseRuns multiplier (1.02 vs 1.1) after reading the Smyth primer; if changed, update the formula and tests and record old/new values. Verify with a hand-computed example.
- [x] 4.5 Write `docs/METHODOLOGY.md` (metric, formula source URL, status, note) from the audit and add a test comparing it to the registry in both directions. Verify it fails when a metric is removed from the document.

## 5. Encoding, decisions, and final checks

- [x] 5.1 Reproduce the Windows `UnicodeEncodeError` by printing a result with a non-cp1252 character; fix in the library if it originates there, otherwise document it. Verify the reproduction no longer fails or the limitation is documented.
- [x] 5.2 Add an ADR to `docs/DECISIONS.md` and `docs/decisions/` covering the audit findings, the constants snapshot, the walk-term change, the wRC+ denominator, reference status, and the old/new numeric values; update `README.md` and `docs/ARCHITECTURE.md` (constants provenance, park factor). Verify the documented snippets run as written.
- [x] 5.3 Record the follow-on changes as proposals or notes: FanGraphs-method pitcher WAR, and the literature sweep (`baseballr`, OpenAlex/arXiv, Tango, Retrosheet research). Verify `openspec list` or the ADR references them.
- [ ] 5.4 Run the full gate: `uv run ruff check .`, `uv run ruff format --check .`, `uv run pyright`, `uv run pytest`, `openspec validate --all`. Verify all are clean.

## Workflow follow-up

- Archive with `openspec archive golden-validation-and-constants --yes` after review.
