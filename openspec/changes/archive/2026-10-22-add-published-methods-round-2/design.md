## Decisions

1. Each method follows the research specs (`sabermetricspy_research/specs/`), which quote the formula and its locator from the primary source; every test value traces to a dossier or fixture there.
2. Owner decisions were adopted by default from the specs' recommendations and are marked "adopted by default" in each ADR for confirmation: null for a zero denominator in PSN; XR/XRR as `matches`/`golden` although the outside value is the author's own example; right-closed default bins; event-form equal-width ECE; loss orientation for RPS; `tau` required for Glicko-2.
3. Evidence tiers: `golden` where a printed value is reproduced (PSN, XR/XRR, Brier/Murphy, James-Stein, RPS, Glicko-2); `primary` where only the definition is quoted and the tests are hand arithmetic or an independent implementation (ECE/MCE, Diebold-Mariano).
4. The Harvey-Leybourne-Newbold correction is not implemented: their paper derives it for the uniform-window variance, while the implementation uses Bartlett weights (which keep the estimate non-negative and match statsmodels).
