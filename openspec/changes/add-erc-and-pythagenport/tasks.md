# Tasks: Add Component ERA and Pythagenport Winning Percentage

- [x] Add `Metric.ERC` and `Metric.PYTHAGENPORT_WIN_PCT` to `sabermetricspy.types.enums` <!-- id: 1 -->
- [x] Implement `calc_erc` in `sabermetricspy.metrics.pitching` <!-- id: 2 -->
- [x] Implement `calc_pythagenport_win_pct` in `sabermetricspy.metrics.specialized` <!-- id: 3 -->
- [x] Create golden fixtures in `tests/golden/erc_and_pythagenport.yaml` <!-- id: 4 -->
- [x] Write comprehensive unit, property-based (`hypothesis`), and multi-backend tests in `tests/test_golden_erc_and_pythagenport.py` <!-- id: 5 -->
- [x] Update `tests/test_metric_values.py` table coverage for new metrics <!-- id: 6 -->
- [x] Register new metrics in `src/sabermetricspy/data/methodology.yaml` and re-render `docs/METHODOLOGY.md` in UTF-8 <!-- id: 7 -->
- [x] Record ADR-0079 in `docs/decisions/ADR-0079-erc-and-pythagenport.md` and append to `docs/DECISIONS.md`, `CHANGELOG.md`, `docs/VERIFICATION.md` <!-- id: 8 -->
- [x] Validate OpenSpec with `openspec validate --all`, run ruff, pyright, pytest, and archive change <!-- id: 9 -->
