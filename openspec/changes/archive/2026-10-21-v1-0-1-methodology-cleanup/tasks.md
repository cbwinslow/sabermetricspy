# Tasks

## 1. Fix our mistakes
- [x] 1.1 Geometric strike zone in the statcast preset, falling back to Savant's zone; tighten plate-discipline tolerances.
- [x] 1.2 Savant Whiff% counting (`whiffs_savant`, `swings_savant`) with a reference test for three pitch types.
- [x] 1.3 `bsr` takes `ubr` and `wgdp` inputs.

## 2. Remove and quarantine
- [x] 2.1 Remove `total_break`, `whiff_per_100`, `two_strike_chase_pct`, `wgdp` and their tests, audit entries and context fields.
- [x] 2.2 Add `ReferenceStatus.EXPERIMENTAL` with a warning; apply to `siera`, `rc27`, `xfip_minus`, `WinProbabilityModel`.
- [x] 2.3 Bound test for documented divergences; Baseball-Reference OPS+ fixture and test.

## 3. Record and verify
- [x] 3.1 Update methodology notes with measured gaps; promote `MarkovChainModel.fit_transitions` after running the Retrosheet 2016 checks (33 tests passed).
- [x] 3.2 Write `docs/VERIFICATION.md`, ADR-0061, ADR-0062; update README, CHANGELOG, CLAUDE.md, DECISIONS.
- [x] 3.3 Run ruff, format, pyright, pytest, openspec validate; bump to 1.0.1; archive.
