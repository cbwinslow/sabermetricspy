# Tasks: Declarative YAML SourceTranslator and Extensible Nomenclature Registry

- [x] 1. **Bundled YAML Nomenclature & Source Translator Files**
  - [x] 1.1 Create `src/sabermetricspy/data/presets/aliases.yaml` mapping canonical Tier 2 columns to all standard aliases.
  - [x] 1.2 Expand `src/sabermetricspy/data/presets/sources.yaml` with declarative `column_map`, `value_rules`, and `range_rules` for `retrosheetpy_events`, `statcast`, `lahman`, `fangraphs`, and `bref`.
- [x] 2. **YAML-Driven `SourceTranslator` & Nomenclature API**
  - [x] 2.1 Update `src/sabermetricspy/schema/__init__.py` to load aliases from `aliases.yaml` and expose `register_column_aliases()` and `register_column_aliases_yaml()`.
  - [x] 2.2 Implement `SourceTranslator`, `get_source_translator()`, and `load_source_translator_yaml()` in `src/sabermetricspy/presets/__init__.py`.
  - [x] 2.3 Add `preset: str | Path | SourceTranslator | None = None` support to `calculate()`, `calculate_suite()`, and `calculate_available()` in `src/sabermetricspy/engine/__init__.py`.
- [x] 3. **Verification & OpenSpec Validation**
  - [x] 3.1 Add unit and cross-backend tests in `tests/test_sabermetricspy.py` verifying custom YAML nomenclatures and declarative YAML `SourceTranslator` execution.
  - [x] 3.2 Run `openspec validate --all`, `uv run ruff check .`, `uv run pyright`, and `uv run pytest`.
