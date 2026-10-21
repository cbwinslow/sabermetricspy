# Tasks: v1.0.0 Readiness

## 1. Pure core
- [x] 1.1 Revert the multi-source name register (ADR-0058) and drop `add-reference-data-cache` and `add-player-name-register`.
- [x] 1.2 Add `update_register()` (commit-checked, atomic, raises when upstream is unreachable) and a 90-day staleness warning to `sabermetricspy.ids`, with tests. Network stays in `download_register`/`update_register` only.
- [x] 1.3 Remove the unverified baseballr fixtures (made-up values; the RE24 one only copied our own table).

## 2. Real outside tie-outs
- [x] 2.1 Install R 4.6.1 and baseballr 2.0.0; `tools/baseballr_golden.R` records real output with version, calls and date.
- [x] 2.2 `tests/test_golden_baseballr.py`: constants vs `fg_guts()` (1990-2025), wOBA vs `woba_plus()`, FIP vs `fip_plus()`. All pass. (ADR-0059)
- [x] 2.3 RE24 and `run_expectancy_code()` not tied out: no reproducible baseballr input; recorded in ADR-0059, not claimed.

## 3. Release audit
- [x] 3.1 `docs/METHODOLOGY.md` regenerated from `methodology.yaml`; tests/test_methodology.py enforces agreement.
- [x] 3.2 ruff, ruff format, pyright, pytest green.
- [x] 3.3 README/CHANGELOG/DECISIONS updated; archive the change.
