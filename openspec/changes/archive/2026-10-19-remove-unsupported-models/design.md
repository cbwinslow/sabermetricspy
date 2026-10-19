## Context

`docs/METHODOLOGY.md` marked these as `unverified` or `approximate` with the reason "no vendor publishes the model or its training data". The owner's rule (CLAUDE.md rule 7) is to ship only established, outside-validated methods and to propose removal rather than approximate.

## Decisions

- **Delete rather than quarantine.** The code is in git history, no other module imports it, and an `experimental` package would keep unvalidated results one import away.
- **Keep the consumers of Savant's own fields.** `xba`, `xslg`, `xwoba` sum Savant's per-pitch estimates and reproduce its pitch-arsenal values, so they stay.
- **Drop the two unused dependencies** instead of leaving them in core "just in case"; they can be added back when a validated method needs them.

## Risks

Callers of the removed names get `ImportError`/`AttributeError`; the package is at 0.1.0 and the removal is recorded in ADR-0047.
