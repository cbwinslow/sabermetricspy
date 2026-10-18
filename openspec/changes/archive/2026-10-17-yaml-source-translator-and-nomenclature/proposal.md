# Proposal: Declarative YAML SourceTranslator and Extensible Nomenclature Registry

## Why
To ensure `sabermetricspy`'s core equations and engine are 100% decoupled from any specific data provider (`retrosheetpy`, `statcast`, `lahman`, `fangraphs`, `bref`, `mlb_api`, or custom college/international/database schemas), all column alias mappings and event-code-to-count translations should live in declarative YAML translator files rather than hardcoded Python dictionaries.

## What Changes
1. **Bundled YAML Column Alias Dictionary (`src/sabermetricspy/data/presets/aliases.yaml`)**:
   - Move `DEFAULT_COLUMN_ALIASES` out of Python code into a declarative, user-extensible YAML file (`aliases.yaml`) with runtime registration (`register_column_aliases_yaml()`).
2. **Declarative YAML `SourceTranslator` (`src/sabermetricspy/presets/`)**:
   - Expand `src/sabermetricspy/data/presets/sources.yaml` to define complete declarative translation rules (`column_map`, `value_counts`, `range_counts`, `sum_columns`, `flag_columns`) for `retrosheetpy_events`, `retrosheetpy_gamelogs`, `statcast`, `lahman_batting`, `lahman_pitching`, `fangraphs`, and `bref`.
   - Implement `SourceTranslator` (a frozen Pydantic model + vectorized Narwhals transformer) that loads any built-in preset name or custom user `.yaml` translator file and translates any DataFrame into canonical Tier 2 columns.
3. **Engine Integration (`preset=` parameter)**:
   - Update `calculate()`, `calculate_suite()`, and `calculate_available()` to accept an optional `preset: str | Path | SourceTranslator | None = None` so users can pass a YAML translator preset or file path directly into any calculation call.

## Impact
- Makes `sabermetricspy` 100% provider-agnostic and allows users to add new nomenclatures or data sources purely via YAML.
