# Tasks

## 1. Audit infrastructure

- [x] 1.1 Write failing tests that every audit entry has an `evidence` tier (`golden`, `primary`, `secondary`), that `matches` entries are not `secondary` without a limitation note, and that the generated `docs/METHODOLOGY.md` shows the tier. Verify they fail on the current data and loader.
- [x] 1.2 Add the evidence field to `MethodologyEntry`, the loader, the renderer, and the audit builder; backfill the 39 audited entries (golden for fixture-backed metrics, primary for formula-confirmed ones, secondary for DICE). Verify the tests from 1.1 pass for the audited entries and `docs/METHODOLOGY.md` regenerates cleanly.

## 2. Batted-ball family (10 metrics, golden)

- [x] 2.1 Retrieve FanGraphs leaderboard rows with batted-ball counts and published rates (GB, FB, LD, IFFB, Pull, Cent, Oppo, HR/FB, EV) for at least six pitcher seasons across eras, record them as fixtures, and add the recomputation gate. Verify the fixture structure and gate tests pass and fail on an altered value.
- [x] 2.2 Compare `gb_pct`, `fb_pct`, `ld_pct`, `pu_pct`, `gb_to_fb`, `hr_to_fb`, `pull_pct`, `cent_pct`, `oppo_pct`, and `avg_ev` with the fixtures; record status, source, evidence tier, and note in the audit data (fix or label differences). Verify the golden tests pass and the audit entries are no longer unverified.

## 3. Batting and weighted offense (18 metrics)

- [x] 3.1 Retrieve the primary-source definitions for `b1`, `tb`, `xbh`, `ubb`, `seca`, `gpa`, `ta`, `rc_basic`, `rc27`, `xbh_pct`, `hr_pct`, `r_per_pa`, `rbi_per_pa`, `bb_to_k`, `k_to_bb`, `k_minus_bb_pct`, `bat_k_pct_plus`, and `bat_bb_pct_plus` (Tango wiki pages, FanGraphs Library, Baseball-Reference glossary), quoting each formula with its URL in working notes. Verify each metric has at least one fetched primary definition.
- [x] 3.2 Add golden fixtures where a published value exists (FanGraphs batter leaderboard rates such as BB/K, K-BB%, K%+ and BB%+ if exposed, and Tango wiki worked examples for GPA, Total Average, Secondary Average, Runs Created), compare, and update the audit entries; fix or label differences with before/after values. Verify the golden tests and `tests/test_metric_values.py` pass.

## 4. Pitching, DIPS, and indexed pitching (16 metrics)

- [x] 4.1 Retrieve primary definitions for `ip`, `ra9`, `h_per_9`, `bf_per_ip`, `qs_pct`, `cg_pct`, `sv_pct`, `pit_bb_to_k`, `pit_k_to_bb`, `pit_k_minus_bb_pct`, `era_plus`, `qera`, `dips_bop_pct`, `xera`, `k_pct_plus`, and `bb_pct_plus`. Verify each has a fetched primary definition or is recorded with the limitation.
- [x] 4.2 Add golden fixtures from FanGraphs pitcher leaderboard rows (K%+, BB%+, K-BB%, H/9, K/BB, QS, SV, xERA where exposed), investigate the league-denominator question for K%+ and BB%+, compare, and update the audit entries; fix or label differences. Verify golden tests pass or divergences are documented.

## 5. Plate discipline (18 metrics)

- [x] 5.1 Establish whether a public pitch-level Statcast sample can be retrieved without circumventing protection; if so record a small sample with source and date and compute counts through the library's statcast preset, otherwise record the limitation. Verify the recorded sample (or the written limitation) is in the repository with provenance.
- [x] 5.2 Retrieve FanGraphs Library definitions for the plate-discipline rates and compare the library's formulas and denominators (Swing%, Z/O-Swing%, Contact%, Z/O-Contact%, Zone%, SwStr%, CStr%, CSW%, Whiff%, Foul%, F-Strike%, F-Swing%, BIP%, PutAway%, 2K-Chase%, Meatball Swing%) with them and, where possible, with published per-player rates. Verify audit entries are resolved with evidence tiers and golden tests pass for any numeric comparison.

## 6. Pitch physics and Statcast expected (17 metrics)

- [x] 6.1 Retrieve the Baseball Savant and FanGraphs definitions for `avg_velo`, `avg_spin`, `avg_extension`, `effective_velo`, `ivb`, `hb`, `total_break`, `vaa`, `haa`, `bauer_units`, `rv_per_100`, and `whiff_per_100`, checking sign conventions and units (pitcher versus catcher perspective, feet versus inches). Verify each metric has a fetched definition and any sign or unit mismatch is recorded.
- [x] 6.2 Check `xba`, `xslg`, `xwoba`, `ba_minus_xba`, and `woba_minus_xwoba` against Savant's definitions (denominators such as `woba_denom`) and published leaderboard values; fix or label differences. Verify the audit entries are resolved and golden tests pass.

## 7. Fielding, baserunning, team, expectancy (18 metrics)

- [x] 7.1 Retrieve Tango wiki and FanGraphs definitions for `tc`, `fpct`, `err_pct`, `rf_per_g`, `rf_per_9`, `catcher_cs_pct`, `sb_pct`, `xbt_pct`, `wgdp`, `run_diff`, `win_pct`, `pythag_win_pct`, `pythag_wins`, `pythag_luck`, `pli`, `wpa_li`, `clutch`, and `rew`; compare formulas. Verify each metric has a fetched definition.
- [x] 7.2 Add worked-example or leaderboard fixtures where available (Pythagorean win percentage and luck for published team seasons, FanGraphs pLI, Clutch, REW and WPA/LI values), compare, and update the audit entries; fix or label differences. Verify golden tests pass or divergences are documented.

## 8. Models (16 entries)

- [x] 8.1 For each model entry find a published reference (run-expectancy and win-expectancy tables, the Log5 formula, Guts! linear weights, Marcel components already checked) and compare where inputs allow; otherwise record why no reference exists. Verify no model is unverified without a written reason and the test enforcing that passes.

## 9. Defects and decision record

- [x] 9.1 For every formula defect found in groups 2 to 8, write the failing test from the published value, fix the formula, and record old and new values; for source-dependent methods add the approximate label and caveat. Verify the new tests pass and the full suite stays green.
- [x] 9.2 Add an ADR (`docs/DECISIONS.md` and `docs/decisions/`) summarizing the audit outcome (counts by status and tier, every fix with before and after numbers, every label with its reason), and regenerate `docs/METHODOLOGY.md`. Verify the methodology consistency tests pass.

## 10. Literature catalogue and sweep procedure

- [x] 10.1 Write failing offline tests for `tools/literature_sweep.py` using recorded OpenAlex and arXiv responses (normalization, license capture, no full text stored, arXiv interval) and add the tool with the standard library only, no personal data, and a three-second arXiv interval. Verify the tests pass and `uv run pyright` covers `tools/`.
- [x] 10.2 Run the OpenAlex and arXiv queries recorded in the design (run expectancy, win probability, pitch quality, expected outcomes, catcher framing, fielding metrics, player projection, park factors, aging curves, and similar), save the metadata digest, and screen results for methods with a published formula. Verify the digest records query, date, and result counts.
- [x] 10.3 Review the Tango wiki archive and blog, the Retrosheet research page and Pavitt's bibliography, and the `baseballr` reference index for methods and coverage gaps. Verify the working notes list the pages examined with dates and what could not be retrieved (*The Book*).
- [x] 10.4 Write `docs/LITERATURE.md` (prioritized entries with the recorded fields, a rejected-with-reason list, the baseballr coverage analysis, and per-source coverage notes) and `docs/LITERATURE_SWEEP.md` (the procedure, terms, and how to rerun the tool). Verify a test checks every catalogue entry has the required fields and a primary-source URL.

## 11. Guards and final checks

- [ ] 11.1 Add the guard tests: no built-in metric is `unverified`, every audited entry has an evidence tier, and unverified models carry a reason. Verify they fail when an entry is temporarily reverted and pass otherwise.
- [ ] 11.2 Run the full gate: `uv run ruff check .`, `uv run ruff format --check .`, `uv run pyright`, `uv run pytest`, `openspec validate --all`. Verify all are clean.

## Workflow follow-up

- Archive with `openspec archive literature-sweep-and-method-audit --yes` after review.
- Each catalogued method that is approved becomes its own OpenSpec change.
