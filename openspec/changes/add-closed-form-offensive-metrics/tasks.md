## 1. Implementation

- [x] 1.1 Add enum members `ISOD`, `BRA`, `ERP` to `types/enums.py`.
- [x] 1.2 Implement `calc_isod` in `metrics/batting.py`.
- [x] 1.3 Implement `calc_bra` and `calc_erp` in `metrics/weighted.py`.
- [x] 1.4 Add `tests/golden/closed_form_batting.yaml` with verified player values.
- [x] 1.5 Add `tests/test_golden_closed_form_batting.py` with unit, golden, and property tests.
- [x] 1.6 Add entries to `data/methodology.yaml`, update `tests/test_metric_values.py`, and regenerate `docs/METHODOLOGY.md`.
- [x] 1.7 Add ADR-0078 to `docs/decisions/` and update `docs/DECISIONS.md`, `CHANGELOG.md`, `docs/VERIFICATION.md`, and `docs/LITERATURE.md`.

## 2. Quality Gates

- [x] 2.1 Pass `uv run ruff check .` and `uv run pyright`.
- [x] 2.2 Pass `uv run pytest`.
- [x] 2.3 Pass `openspec validate --all`.

