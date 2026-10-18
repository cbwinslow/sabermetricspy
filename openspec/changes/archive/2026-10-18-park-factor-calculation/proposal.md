## Why

wRC+, OPS+, ERA+ and ERA- default the park factor to 100 unless the caller supplies one, and the library has no way to compute a park factor. The bundled `park_factors.yaml` lists 7 parks and disagrees with FanGraphs Guts! for several of them (Boston 104 against 103, Cincinnati 105 against 102, Colorado HR factor 117 against 107). The literature sweep ranked the FanGraphs park factor method as the highest-value gap.

## What Changes

- Add pure park factor functions following the FanGraphs Library article: raw park factor, the composite (halved) factor, and the regression toward 1.00 by years of data.
- Replace the bundled park table with the 30-team FanGraphs Guts! table for 2024 (5-year, 1-year and HR factors), pinned by a golden fixture, with provenance in the file header.
- `get_park_factor` stops inventing a neutral factor silently for an unknown park: it still returns a neutral factor but the docstring and a warning say so.
- Record ADR-0029 and update the methodology audit.

## Capabilities

### New Capabilities
- `park-factors`: calculation of park factors from home and road run environments, and the sourced bundled table.

### Modified Capabilities
<!-- none: existing metric specs are unchanged; callers still pass the factor through SeasonContext -->

## Impact

- `src/sabermetricspy/value/` (new `park.py`), `src/sabermetricspy/constants/__init__.py`, `src/sabermetricspy/data/constants/park_factors.yaml`.
- New golden fixture and tests; `docs/decisions/ADR-0029-*.md`; `docs/DECISIONS.md`.
