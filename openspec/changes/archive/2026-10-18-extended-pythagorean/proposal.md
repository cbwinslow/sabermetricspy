## Why

Entry 1 of `docs/LITERATURE.md`: the head-to-head extension of James's Pythagorean formula (Cleary et al.) is fully specified and uses only runs scored and allowed.

## What Changes

- Add `Log5Model.extended_pythagorean_home_win_prob`, with a required exponent argument.
- Add a methodology model entry, tests, and ADR-0032.

## Capabilities

### New Capabilities
- `extended-pythagorean`: head-to-head win probability from opponent-rescaled runs.

### Modified Capabilities
<!-- none -->

## Impact

- `models/__init__.py`, `data/methodology.yaml`, `docs/METHODOLOGY.md`, `tests/test_model_audit.py`, ADR-0032.
