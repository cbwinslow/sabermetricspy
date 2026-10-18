## Decisions

1. Source: https://web.williams.edu/Mathematics/sjmiller/public_html/math/papers/PythagBothTeams20.pdf, equations 1.4 and 1.5: RS_adj = RS_h * RA_a / R, RA_adj = RA_h * RS_a / R, P = RS_adj^g / (RS_adj^g + RA_adj^g); the league average cancels, giving (RS_h RA_a)^g / ((RS_h RA_a)^g + (RA_h RS_a)^g).
2. The exponent is a required argument: the paper cites Baseball-Reference's 1.87 and says 1.83 is also common, so the library does not choose one silently.
3. Validation is algebraic (equation 1.4 equals 1.5; reduces to Pythagorean against an average opponent). The paper's playoff total needs series data and is not reproduced.
