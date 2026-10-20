# Tasks

## 1. Season constants follow the data

- [x] 1.1 Infer, check and warn in the engine (`calculate`, `calculate_rolling`). Verified by `tests/test_multi_season_guard.py` (inferred season, contradiction, warning only for constant-reading metrics).
- [x] 1.2 ADR-0051 with Alternatives; changelog entry. Verified by `openspec validate --all` and the full test suite.

## 2. Fitted win expectancy

- [x] 2.1 `WinExpectancyMatrix` with games-based standard error. Verified by `tests/test_win_expectancy_matrix.py` (hand-computed rates).
- [x] 2.2 Opt-in Retrosheet 2016 check against Tango's table. Verified by `tests/test_retrosheet_2016_win_expectancy.py`.
- [x] 2.3 Methodology entry and ADR-0052 with Alternatives. Verified by `tests/test_methodology.py`.

## 3. Fitted Markov chain

- [x] 3.1 `MarkovChainModel.fit_transitions` and `state_distribution`. Verified by `tests/test_markov_transitions.py` (closed-form chain).
- [x] 3.2 Opt-in Retrosheet 2016 check against the printed ABDWR values in `tests/golden/markov_abdwr_2016.yaml`.
- [x] 3.3 Methodology entries (including the measured gap of the event-probability `fit`) and ADR-0053 with Alternatives.
