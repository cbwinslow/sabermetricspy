# Naming Conventions & Baseball Nomenclature Standard

To keep `sabermetricspy` aesthetically clean, mathematically unambiguous, and 100% aligned with both **Python PEP 8** and **MLB / Sabermetric industry standards** (FanGraphs, Baseball-Reference, Baseball Savant, Retrosheet, and SABR), the library enforces a strict **3-Tier Naming Architecture**.

---

## Overview of the 3 Tiers

| Tier | Where It Is Used | Casing Style | Examples |
| :--- | :--- | :--- | :--- |
| **Tier 1: Enums & Constants** | `Stat`, `Metric`, `MetricSuite`, `PitchOutcome`, `PlayOutcome`, `Handedness`, `BaseState` | `UPPER_SNAKE_CASE` | `Metric.AVG`, `Metric.OBP`, `Metric.WOBA`, `Metric.WRC_PLUS`, `Metric.FIP`, `Metric.XFIP`, `Metric.CSW_PCT`, `Metric.K_MINUS_BB_PCT` |
| **Tier 2: Canonical Columns & Functions** | DataFrame column names, Python function names, YAML metric IDs | `lower_snake_case` | `"avg"`, `"obp"`, `"woba"`, `"wrc_plus"`, `"fip"`, `"xfip"`, `"csw_pct"`, `"k_minus_bb_pct"` |
| **Tier 3: Display & Leaderboard Labels** | `MetricSpec.display_name`, plots, tables, `.summary()` output | **Official Sabermetric Casing** | `"AVG"`, `"OBP"`, `"wOBA"`, `"wRC+"`, `"FIP"`, `"xFIP"`, `"CSW%"`, `"K-BB%"` |

> [!IMPORTANT]
> Because all our enums inherit from `enum.StrEnum` (Python 3.11+), the enum member's **name** is `UPPER_SNAKE_CASE` (`Metric.WRC_PLUS`) while its **string value** is the canonical `lower_snake_case` identifier (`"wrc_plus"`), and its `MetricSpec.display_name` holds the authentic baseball typography (`"wRC+"`).
> This means `Metric.WRC_PLUS == "wrc_plus"` evaluates to `True`!

---

## Core Suffixes & Operator Conventions

When translating baseball notation (`%`, `+`, `-`, `/`) into valid Python identifiers (Tier 1 & Tier 2), we NEVER guess or mix styles. Always use these exact rules:

| Symbol in Baseball | Meaning | Tier 1 (`StrEnum`) | Tier 2 (Column / Function) | Tier 3 (`display_name`) |
| :--- | :--- | :--- | :--- | :--- |
| **`%`** | Percentage / Rate (`0.0` to `1.0` scale internally) | `_PCT` (e.g., `Metric.BB_PCT`, `Metric.K_PCT`, `Metric.BARREL_PCT`) | `_pct` (`bb_pct`, `k_pct`, `barrel_pct`) | `"BB%"`, `"K%"`, `"Barrel%"` |
| **`+`** | Park & League Indexed (`100 = avg`, higher is better) | `_PLUS` (e.g., `Metric.WRC_PLUS`, `Metric.OPS_PLUS`, `Metric.ERA_PLUS`) | `_plus` (`wrc_plus`, `ops_plus`, `era_plus`) | `"wRC+"`, `"OPS+"`, `"ERA+"` |
| **`-`** (Indexed) | Park & League Indexed (`100 = avg`, lower is better) | `_MINUS` (e.g., `Metric.ERA_MINUS`, `Metric.FIP_MINUS`, `Metric.XFIP_MINUS`) | `_minus` (`era_minus`, `fip_minus`, `xfip_minus`) | `"ERA-"`, `"FIP-"`, `"xFIP-"` |
| **`-`** (Difference) | Rate Differential (e.g., `K% - BB%`) | `_MINUS_` (e.g., `Metric.K_MINUS_BB_PCT`) | `_minus_` (`k_minus_bb_pct`) | `"K-BB%"` |
| **`/`** (Ratio) | Ratio of Two Counts (e.g., `K/BB`, `GB/FB`, `HR/FB`) | `_TO_` (e.g., `Metric.K_TO_BB`, `Metric.BB_TO_K`, `Metric.GB_TO_FB`, `Metric.HR_TO_FB`) | `_to_` (`k_to_bb`, `bb_to_k`, `gb_to_fb`, `hr_to_fb`) | `"K/BB"`, `"BB/K"`, `"GB/FB"`, `"HR/FB"` |
| **`/9`** | Per 9 Innings Pitched (27 Outs) | `_PER_9` (e.g., `Metric.K_PER_9`, `Metric.BB_PER_9`, `Metric.HR_PER_9`, `Metric.H_PER_9`) | `_per_9` (`k_per_9`, `bb_per_9`, `hr_per_9`, `h_per_9`) | `"K/9"`, `"BB/9"`, `"HR/9"`, `"H/9"` |
| **Zone Prefixes** | Inside (`Z-`) vs. Outside (`O-`) Strike Zone | `Z_` / `O_` (e.g., `Metric.Z_SWING_PCT`, `Metric.O_SWING_PCT`, `Metric.Z_CONTACT_PCT`, `Metric.O_CONTACT_PCT`) | `z_` / `o_` (`z_swing_pct`, `o_swing_pct`, `z_contact_pct`, `o_contact_pct`) | `"Z-Swing%"`, `"O-Swing%"`, `"Z-Contact%"`, `"O-Contact%"` |
| **Expected (`x`)** | Statcast / Expected Estimator (`xBA`, `xSLG`, `xwOBA`, `xFIP`) | `X` prefix (e.g., `Metric.XBA`, `Metric.XSLG`, `Metric.XWOBA`, `Metric.XFIP`) | `x` prefix (`xba`, `xslg`, `xwoba`, `xera`, `xfip`) | `"xBA"`, `"xSLG"`, `"xwOBA"`, `"xERA"`, `"xFIP"` |

---

## Canonical Counting Stat Vocabulary (`Stat` Enum)

To ensure zero ambiguity between Batting, Pitching, Baserunning, and Fielding, canonical counting columns use official baseball abbreviations:

### 1. Batting & Plate Appearance Counts
| `Stat` Enum (Tier 1) | Canonical Column (Tier 2) | Display Label (Tier 3) | Definition & Aliases Mapped by Presets |
| :--- | :--- | :--- | :--- |
| `Stat.G` | `g` | `"G"` | Games played |
| `Stat.PA` | `pa` | `"PA"` | Plate appearances (`TBF` for pitchers) |
| `Stat.AB` | `ab` | `"AB"` | At-bats |
| `Stat.R` | `r` | `"R"` | Runs scored |
| `Stat.H` | `h` | `"H"` | Total hits (`1B + 2B + 3B + HR`) |
| `Stat.B1` | `b1` | `"1B"` | Singles (Aliases: `"1b"`, `"1B"`, `"singles"`). Derived as `h - b2 - b3 - hr` if omitted |
| `Stat.B2` | `b2` | `"2B"` | Doubles (Aliases: `"2b"`, `"2B"`, `"doubles"`) |
| `Stat.B3` | `b3` | `"3B"` | Triples (Aliases: `"3b"`, `"3B"`, `"triples"`) |
| `Stat.HR` | `hr` | `"HR"` | Home runs |
| `Stat.RBI` | `rbi` | `"RBI"` | Runs batted in |
| `Stat.BB` | `bb` | `"BB"` | Total walks (base on balls: `ubb + ibb`) |
| `Stat.IBB` | `ibb` | `"IBB"` | Intentional walks |
| `Stat.UBB` | `ubb` | `"uBB"` | Unintentional walks (`bb - ibb`) |
| `Stat.HBP` | `hbp` | `"HBP"` | Hit by pitch |
| `Stat.SO` | `so` | `"SO"` | Strikeouts (Aliases: `"k"`, `"K"`, `"SO"`, `"strikeouts"`) |
| `Stat.SF` | `sf` | `"SF"` | Sacrifice flies |
| `Stat.SH` | `sh` | `"SH"` | Sacrifice hits (bunts) |
| `Stat.CI` | `ci` | `"CI"` | Catcher's interference |
| `Stat.ROE` | `roe` | `"ROE"` | Reached on error |
| `Stat.GIDP` | `gidp` | `"GIDP"` | Grounded into double play (Aliases: `"gdp"`, `"GDP"`) |

### 2. Baserunning Counts
| `Stat` Enum (Tier 1) | Canonical Column (Tier 2) | Display Label (Tier 3) | Definition |
| :--- | :--- | :--- | :--- |
| `Stat.SB` | `sb` | `"SB"` | Stolen bases |
| `Stat.CS` | `cs` | `"CS"` | Caught stealing |
| `Stat.PK` | `pk` | `"PK"` | Picked off |
| `Stat.OOB` | `oob` | `"OOB"` | Outs on base (non-force, non-CS baserunning outs) |

### 3. Pitching Counts
*(Note: For two-way player tables containing both batting and pitching in a single row, pitching columns may be prefixed with `pit_`, e.g., `pit_so`, `pit_bb`, `pit_hr`, which presets resolve automatically.)*

| `Stat` Enum (Tier 1) | Canonical Column (Tier 2) | Display Label (Tier 3) | Definition |
| :--- | :--- | :--- | :--- |
| `Stat.OUTS` | `outs` | `"Outs"` | **Outs recorded (`3 * IP_full + IP_partial`) — canonical internal representation of innings** |
| `Stat.BF` | `bf` | `"TBF"` | Total batters faced |
| `Stat.ER` | `er` | `"ER"` | Earned runs allowed |
| `Stat.RA` | `ra` | `"RA"` | Total runs allowed (earned + unearned) |
| `Stat.W` | `w` | `"W"` | Wins |
| `Stat.L` | `l` | `"L"` | Losses |
| `Stat.GS` | `gs` | `"GS"` | Games started |
| `Stat.CG` | `cg` | `"CG"` | Complete games |
| `Stat.SHO` | `sho` | `"ShO"` | Shutouts |
| `Stat.QS` | `qs` | `"QS"` | Quality starts (`outs >= 18` and `er <= 3`) |
| `Stat.SV` | `sv` | `"SV"` | Saves |
| `Stat.BS` | `bs` | `"BS"` | Blown saves |
| `Stat.HLD` | `hld` | `"HLD"` | Holds |
| `Stat.WP` | `wp` | `"WP"` | Wild pitches |
| `Stat.BK` | `bk` | `"BK"` | Balks |

### 4. Batted-Ball & Plate Discipline Counts
| `Stat` Enum (Tier 1) | Canonical Column (Tier 2) | Display Label (Tier 3) | Definition |
| :--- | :--- | :--- | :--- |
| `Stat.PITCHES` | `pitches` | `"Pitches"` | Total pitches thrown / seen |
| `Stat.SWINGS` | `swings` | `"Swings"` | Total swings |
| `Stat.WHIFFS` | `whiffs` | `"Whiffs"` | Swinging strikes (`swinging_strike`, `swinging_strike_blocked`, `missed_bunt`) |
| `Stat.CALLED_STRIKES` | `called_strikes` | `"CStr"` | Called strikes |
| `Stat.FOULS` | `fouls` | `"Fouls"` | Foul balls (excluding foul tips resulting in strike 3) |
| `Stat.CONTACTS` | `contacts` | `"Contacts"` | Swings making contact (`swings - whiffs`) |
| `Stat.ZONE_PITCHES` | `zone_pitches` | `"Z-Pitches"` | Pitches inside the strike zone |
| `Stat.OUT_ZONE_PITCHES` | `out_zone_pitches` | `"O-Pitches"` | Pitches outside the strike zone |
| `Stat.ZONE_SWINGS` | `zone_swings` | `"Z-Swings"` | Swings at pitches inside the strike zone |
| `Stat.OUT_ZONE_SWINGS` | `out_zone_swings` | `"O-Swings"` | Swings at pitches outside the strike zone (chases) |
| `Stat.ZONE_CONTACTS` | `zone_contacts` | `"Z-Contacts"` | Contact made on swings inside the strike zone |
| `Stat.OUT_ZONE_CONTACTS` | `out_zone_contacts` | `"O-Contacts"` | Contact made on swings outside the strike zone |
| `Stat.BBE` | `bbe` | `"BBE"` | Batted-ball events (`gb + fb + ld + pu`) |
| `Stat.GB` | `gb` | `"GB"` | Ground balls |
| `Stat.FB` | `fb` | `"FB"` | Fly balls (outfield fly balls) |
| `Stat.LD` | `ld` | `"LD"` | Line drives |
| `Stat.PU` | `pu` | `"PU"` | Popups (infield fly balls) |
| `Stat.PULL_BBE` | `pull_bbe` | `"Pull"` | Pulled batted-ball events |
| `Stat.CENT_BBE` | `cent_bbe` | `"Cent"` | Center-field batted-ball events |
| `Stat.OPPO_BBE` | `oppo_bbe` | `"Oppo"` | Opposite-field batted-ball events |
| `Stat.HARD_HIT_BBE` | `hard_hit_bbe` | `"HardHit"` | Batted balls with exit velocity `>= 95.0 mph` |
| `Stat.SWEET_SPOT_BBE` | `sweet_spot_bbe` | `"SweetSpot"` | Batted balls with launch angle between `8°` and `32°` inclusive |
| `Stat.BARRELS` | `barrels` | `"Barrels"` | Statcast barrel events |

### 5. Fielding Counts
| `Stat` Enum (Tier 1) | Canonical Column (Tier 2) | Display Label (Tier 3) | Definition |
| :--- | :--- | :--- | :--- |
| `Stat.PO` | `po` | `"PO"` | Putouts |
| `Stat.A` | `a` | `"A"` | Assists |
| `Stat.E` | `e` | `"E"` | Errors |
| `Stat.DP` | `dp` | `"DP"` | Double plays turned |
| `Stat.TP` | `tp` | `"TP"` | Triple plays turned |
| `Stat.PB` | `pb` | `"PB"` | Passed balls (catchers) |
| `Stat.INN_OUTS_FLD` | `inn_outs_fld` | `"DefOuts"` | Defensive outs played in the field (`3 * Inn`) |

---

## Class, Protocol, and Module Naming

- **Classes & Protocols (`PascalCase`):**
  - `MetricSpec`, `CalculationResult`, `SeasonContext`, `WOBAWeights`, `SIERACoefficients`
  - Estimators & Models: `RunExpectancyMatrix`, `CountExpectancyMatrix`, `LinearWeightsEstimator`, `WinProbabilityModel`, `MarcelProjector`, `Log5Model`, `MarkovChainModel`, `MonteCarloSimulator`, `WARFramework`
- **Functions & Methods (`lower_snake_case`):**
  - Top-level API: `calculate()`, `calculate_suite()`, `calculate_available()`, `describe()`, `formula()`, `search_metrics()`
  - Estimator methods: `.fit()`, `.transform()`, `.fit_transform()`, `.predict()`, `.simulate()`
- **Scale Convention for Rates:**
  - All percentages/rates (`AVG`, `OBP`, `BB_PCT`, `K_PCT`, `CSW_PCT`) are returned on a **decimal probability scale (`0.0` to `1.0`)** during calculation so downstream math (`K% - BB%`, regressions, wOBA, SIERA) never suffers from `* 100` scaling bugs.
  - Display formatting (`CalculationResult.format()` or leaderboard export) formats `.300` as `.300` and `0.245` (`K%`) as `24.5%` using `MetricSpec.display_format`.
