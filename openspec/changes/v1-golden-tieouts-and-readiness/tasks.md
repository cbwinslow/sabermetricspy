# Tasks: v1.0.0 Readiness

## 1. Pure core (done)
- [x] 1.1 Revert the multi-source name register (ADR-0058) and drop `add-reference-data-cache` and `add-player-name-register`.
- [x] 1.2 Add `update_register()` (commit-checked, atomic, raises when upstream is unreachable) and a 90-day staleness warning to `sabermetricspy.ids`, with tests. Network stays in `download_register`/`update_register` only.
- [x] 1.3 Remove the unverified baseballr fixtures (made-up values; the RE24 one only copied our own table).

## 2. Real outside tie-outs (baseballr and published sources)
- [ ] 2.1 Install R and baseballr (or pull its published datasets), run the function once, and save its real output with the call, package version and date in the fixture header.
- [ ] 2.2 Add `tests/test_golden_baseballr.py` only for values that came from that run. Candidates: wOBA/FIP constants, RE24 for one season, a player line cross-checked against FanGraphs.
- [ ] 2.3 If a value cannot be obtained from the source, leave it out (CLAUDE.md rule 7); do not approximate.

## 3. Release audit
- [ ] 3.1 Check every metric in `docs/METHODOLOGY.md` against `src/sabermetricspy/data/methodology.yaml`.
- [ ] 3.2 Run ruff, ruff format, pyright, pytest.
- [ ] 3.3 Update README/CHANGELOG, then `openspec archive v1-golden-tieouts-and-readiness`.
