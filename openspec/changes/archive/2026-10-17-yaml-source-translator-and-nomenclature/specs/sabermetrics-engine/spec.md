# Delta Specification: Declarative YAML SourceTranslator and Nomenclature Registry

## ADDED Requirements

### Requirement: Declarative YAML Column Alias and Nomenclature Registry
The library SHALL load default column aliases from a bundled YAML file (`data/presets/aliases.yaml`) and SHALL provide `register_column_aliases()` and `register_column_aliases_yaml()` so users can register custom column nomenclatures at runtime without modifying library source code.

#### Scenario: Registering a custom YAML nomenclature alias
- **WHEN** a user registers a custom YAML nomenclature mapping `{"dinger_ct": "hr", "free_passes": "bb", "whiff_outs": "so"}` and calls `calculate(df, [Metric.FIP])`
- **THEN** the engine automatically translates `dinger_ct`, `free_passes`, and `whiff_outs` into canonical `hr`, `bb`, and `so` columns and computes `FIP`

### Requirement: Generic YAML SourceTranslator for Provider Schemas
The library SHALL provide a `SourceTranslator` class that loads declarative YAML translation rules (`column_map`, `value_rules`, `range_rules`) from built-in presets (`retrosheetpy_events`, `statcast`, `lahman`) or user-supplied `.yaml` files and executes them as vectorized Narwhals expressions.

#### Scenario: Translating a custom provider dataset via YAML SourceTranslator
- **WHEN** a user defines a custom provider translator in YAML with `column_map` and `value_rules` and passes `preset=translator` to `calculate()`
- **THEN** `SourceTranslator` translates the raw provider columns and event codes into canonical Tier 2 additive counts and computes the requested metrics across Polars, pandas, PyArrow, or DuckDB
