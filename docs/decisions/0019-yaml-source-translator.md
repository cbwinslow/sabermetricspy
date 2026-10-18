# ADR-0019: Declarative YAML SourceTranslator & Extensible Nomenclature Registry

- **Status:** Accepted
- **Date:** 2026-10-17

## Context
Baseball data comes from many heterogeneous providers (`retrosheetpy`, Baseball Savant `statcast`, `lahman`, `fangraphs`, `baseball-reference`, `mlb_api`, college TrackMan CSVs, KBO/NPB feeds, and custom user SQL tables). If column aliases or event-to-count mappings are hardcoded inside Python functions, users cannot adapt the library to new data providers or custom nomenclatures without editing library source code.

## Decision
1. **Core Agnosticism**: Core metric formulas, expectancy models, and forecasting models never reference provider-specific column names or event codes; they operate exclusively on canonical Tier 2 columns (`pa`, `ab`, `h`, `b1`, `b2`, `b3`, `hr`, `bb`, `ibb`, `ubb`, `hbp`, `so`, `outs`, `swings`, `whiffs`, etc.).
2. **YAML-Driven Column Alias Dictionary (`data/presets/aliases.yaml`)**: All default column alias translations (`{"plate_appearances": "pa", "tbf": "bf", "1B": "b1", "SO": "so", ...}`) live in a bundled YAML file and can be extended at runtime via `register_column_aliases_yaml()`.
3. **Declarative `SourceTranslator` (`data/presets/sources.yaml`)**: Provider-specific schemas (`retrosheetpy_events`, `retrosheetpy_gamelogs`, `statcast`, `lahman`, `fangraphs`, `bref`) are defined as declarative YAML translator specs supporting:
   - `column_map`: Direct column renames (`{"BAT_ID": "player_id", "PIT_ID": "pitcher_id"}`).
   - `value_counts`: Declarative rules that map categorical/code columns (`EVENT_CD == 23` or `events in ['single', 'double']`) into canonical 0/1 count columns.
   - `threshold_counts`: Declarative rules that map numeric measurements (`launch_speed >= 95.0`, `8.0 <= launch_angle <= 32.0`) into canonical 0/1 count columns.
4. **First-Class `preset=` Parameter in `calculate()`**: Users can pass `preset="retrosheetpy_events"`, `preset="statcast"`, or a custom `SourceTranslator` / YAML file path directly into `sp.calculate(df, metrics, preset=...)`.

## Consequences
- Adding support for a new baseball data provider, foreign league, or custom database table requires **zero Python code changes**—only a short YAML file.
- Preserves 100% vectorized Narwhals execution across Polars, DuckDB, PyArrow, and pandas.
