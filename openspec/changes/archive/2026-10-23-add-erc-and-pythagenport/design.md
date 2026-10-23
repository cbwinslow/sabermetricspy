# Design: Component ERA (ERC) and Pythagenport Winning Percentage

## Architecture
Both metrics are pure deterministic expressions implemented in Narwhals (`nw.Expr`), adhering to the 3-Tier naming convention and zero-denominator null safety invariants.

### 1. Component ERA (`ERC`)
- **Category**: `Category.PITCHING`
- **Direction**: `Direction.LOWER_IS_BETTER`
- **Required Columns**: `("h", "hr", "bb", "outs", "bf")`
- **Optional Columns**: `("hbp", "ibb")`
- **Formula**:
  $$PTB = 0.89 \times (1.255(H - HR) + 4 HR) + 0.56(BB + HBP - IBB)$$
  When $IBB$ is not provided or null:
  $$PTB = 0.89 \times (1.255(H - HR) + 4 HR) + 0.475(BB + HBP)$$
  When $HBP$ is not provided, it defaults to 0.
  $$IP = \frac{\text{outs}}{3.0}$$
  $$\text{raw} = \frac{(H + BB + HBP) \times PTB \times 9}{BF \times IP}$$
  If $BF \times IP == 0$, $\text{raw} \to \text{null}$.
  Piecewise definition:
  $$ERC = \begin{cases} \text{null} & \text{if } \text{raw is null} \\ \text{raw} \times 0.75 & \text{if } \text{raw} < 2.24 \\ \text{raw} - 0.56 & \text{if } \text{raw} \ge 2.24 \end{cases}$$
  Note: Continuous at 2.24 since $2.24 \times 0.75 = 1.68 = 2.24 - 0.56$.

### 2. Pythagenport Winning Percentage (`PYTHAGENPORT_WIN_PCT`)
- **Category**: `Category.TEAM`
- **Direction**: `Direction.HIGHER_IS_BETTER`
- **Required Columns**: `("rs", "ra", "w", "l")`
- **Formula**:
  $$G = W + L, \quad \text{RPG} = \frac{RS + RA}{G}$$
  $$\gamma = \begin{cases} 1.50 \times \log_{10}(\text{RPG}) + 0.45 & \text{if } \text{RPG} > 0 \\ \text{null} & \text{otherwise} \end{cases}$$
  $$\text{WinPct}_{\text{Pythagenport}} = \frac{RS^\gamma}{RS^\gamma + RA^\gamma}$$
  If $RS^\gamma + RA^\gamma == 0$ or $G == 0$, returns null via `safe_div`.

## Quality Invariants
1. Pure vectorized execution across Polars, DuckDB, PyArrow, and pandas backends.
2. Division by zero yields `null` (not `inf`, `NaN`, or exception).
3. 3-tier naming: Tier 1 (`Metric.ERC`, `Metric.PYTHAGENPORT_WIN_PCT`), Tier 2 (`erc`, `pythagenport_win_pct`), Tier 3 (`ERC`, `Pythagenport W%`).
