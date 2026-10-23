## Decisions

1. **Isolated Discipline (`isod`)**:
   - Follows standard sabermetric definition $\text{IsoD} = \text{OBP} - \text{AVG}$.
   - Computed from summed counting statistics aggregated across groups before division, evaluated safely via safe division helpers.
   - When denominator is zero (no PA/AB), returns `null`.
   - Category: `batting`.

2. **Batter's Run Average (`bra`)**:
   - Follows Cramer & Palmer (1974) BRJ: $\text{BRA} = \text{OBP} \times \text{SLG}$.
   - Deterministic closed-form expression, category: `weighted_offense`.
   - Verified against printed 1973 NL league total (.121 from .323 OBP * .376 SLG) and player values.
   - When either component is null, evaluates to `null`.

3. **Estimated Runs Produced (`erp`)**:
   - Follows Paul Johnson (1985), Bill James Baseball Abstract, and Furtado (1999) linear expansion:
     $\text{ERP} = (2(\text{TB} + \text{BB} + \text{HBP}) + \text{H} + \text{SB} - 0.605(\text{AB} + \text{CS} + \text{GIDP} - \text{H})) \times 0.16$.
   - Absent optional columns (`cs`, `gidp`, `hbp`, `sb`) default to 0 like `rc_tech` and `xr`.
   - Category: `weighted_offense`.

4. **Testing & Verification**:
   - Unit tests for edge cases (zero PA, missing optional columns).
   - Property tests via `hypothesis` (`isod == obp - avg`, `bra == obp * slg`).
   - Golden tests verifying against Lahman / Baseball-Reference / SABR research tie-outs.
   - Multi-backend verification across Polars, DuckDB, PyArrow, and pandas.
