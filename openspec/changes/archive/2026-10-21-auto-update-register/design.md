# Design

`provenance.json` gains `checked_on`. `load_register` (default location only) calls `_auto_refresh`: if the register is complete and was checked today, do nothing; otherwise call `update_register`, which compares the upstream commit with the recorded one and downloads atomically if they differ. Errors: `ConnectionError`/`OSError` with a usable copy -> warning; without one -> `FileNotFoundError`.

Alternatives: check on every load, not chosen now because of GitHub's 60 requests per hour limit; revisit if same-day freshness matters. Background scheduler, not chosen now because it needs a long-running process; revisit if retrosheetpy runs one.
