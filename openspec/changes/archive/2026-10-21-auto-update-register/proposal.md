# Proposal: Chadwick Register Updates Itself

## Why
A register downloaded once goes stale and new players stop matching. A fixed age warning is arbitrary and needs the user to act. Upstream's commit id says exactly when a refresh is needed.

## What Changes
- `load_register()` with no path downloads the register when missing and re-downloads it when upstream has a newer commit, looking upstream at most once a day.
- Offline: use the existing copy and warn; no copy: raise.
- `auto_update=` and `SABERMETRICSPY_AUTO_UPDATE=0` turn it off; an explicit path is never updated unless asked.
- The 90-day age warning is removed.

## Impact
One small GitHub API request per day at most, only when loading the default register. Calculations never touch the network (ADR-0003).
