# ADR-0071: Extrapolated Runs (XR and XRR)

Status: Accepted (adopted by default from the research specs; owner to confirm the defaults listed below)

## Context
Jim Furtado's Extrapolated Runs (The 1999 Big Bad Baseball Annual; "Introducing XR" on Baseball Think Factory) is a linear-weights run estimator fitted to 1955-1997 seasons, in three variants (XR, XRR, XRB). The library already has Runs Created, BaseRuns and linear weights.

## Decision
Add `Metric.XR` and `Metric.XRR` (deterministic, weighted offense, no seasonal constants). The published weights are fixed constants of the method (`XR_WEIGHTS`, `XRR_WEIGHTS` in `metrics/weighted.py`). `bb` is total walks including intentional walks (XR subtracts `ibb` from the .34 group and credits it at .25). Absent optional columns count as 0, as for `rc_tech`; `so` is required for XR. Status `matches`, evidence `golden`: the article's printed example (Mark McGwire 1998: XR 166.35, XRR 167.05; the library computes 166.35 and 167.054) is reproduced, and the same 14 inputs equal the Lahman 2025 row. The example is the author's own computation, so it validates the arithmetic and inputs, not the estimator's accuracy (stated in the methodology note).

**XRB is not implemented.** The printed XRB formula (.34 on total walks, -.096 on AB - H) gives 167.408 on the printed inputs against the printed 169.03; only a walk weight of .35 reproduces it. Nothing retrieved prints .35, so the article is inconsistent. Revisit when a second printing settles .34 versus .35.

Defaults adopted without an owner answer (research spec `extrapolated_runs`, O-XR-1 to O-XR-4): ship XR and XRR as `matches`/`golden` with the evidence stated; optional columns count as 0; XRB held back; category weighted offense.

## Alternatives
- Ship as `experimental`, not chosen now because the formula is quoted from the author's text and the printed example reproduces; revisit if the owner holds that an author's own example is not an outside value (rule 7).
- Ship XRB with the .35 weight that reproduces the example, not chosen now because that would fit a coefficient to an example rather than to a source; revisit if a second printing prints .35.
- Treat absent optional columns as missing (null result), not chosen now because `rc_tech` already counts them as 0 and consistency matters more; revisit if silent zeros cause wrong results in practice.

## Consequences
Two new `Metric` members and methodology entries; `docs/METHODOLOGY.md` regenerated; the value-assertion guard lists them as covered by their own golden test.
