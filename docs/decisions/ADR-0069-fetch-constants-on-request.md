# ADR-0069: Fetch Seasonal Constants on Request, Never Redistribute Them

Status: Accepted; amends ADR-0068 (network use) and ADR-0066 (the "fetch into the user's cache" alternative)

## Context
ADR-0068 removed all network code so the package would not redistribute FanGraphs' compiled tables. That left every user to download and reshape the Guts! table by hand, and every offseason to repeat it for park factors and league totals. Seasonal inputs move with the calendar, so a library that depends on them needs a routine way to refresh them. The concern behind ADR-0066 was redistribution, not a user fetching a page for their own use, and `baseballr`, the reference implementation we already tie out against (ADR-0059), does exactly that: `fg_guts()` and `fg_park()` read the public pages when the caller runs them.

## Decision
- **The package may fetch, only when the caller asks.** New `sabermetricspy.fetch` (and `sabermetrics constants update`) downloads to the caller's machine. Nothing is fetched on import, at install, in the background or by any calculation. A missing table raises `ConstantsNotFoundError` pointing at the command; it never fetches silently.
- **Still no redistribution.** The wheel and sdist contain no third-party tables; the fetched files live in the caller's cache (`default_cache_dir()`), which `constants_dir()` reads after `use_constants` and `$SABERMETRICSPY_CONSTANTS`. The repository keeps its git-ignored full tables and one-season samples (ADR-0068). The caller is responsible for FanGraphs' terms for their own use; the docs say so.
- **Sources mirror baseballr.** Guts! constants (`fg_guts`) -> `guts.csv`; park factors (`fg_park`) -> `park_fip.yaml` and `park_factors.yaml`; league games, plate appearances, runs and outs from the MLB Stats API -> `league_war.yaml`. The Guts! file is read directly (`woba_fangraphs.yaml`, when present, still wins because it carries the optional league fields).
- **Seasonal policy.** `update_constants` is idempotent: it refetches Guts! whole (one request) and, for per-season tables, only the seasons not held plus the latest two (their totals still move in-season). Writes are atomic. A changed page layout, a missing column or an unknown team raises `FetchError` instead of writing a partial table. Requests are paced (`pause`, default 1 second) and identify the library.
- **Not covered yet** (still supplied by the caller, listed in `docs/CONSTANTS.md`): `pitcher_war.yaml` (FanGraphs AL/NL leaderboard totals), and the optional `woba_fangraphs.yaml` fields (league ERA, FIP, xFIP, HR/FB, wRC/PA, SIERA and kwERA constants, OBP, SLG, K%, BB%). Lahman-derivable ones already compute from the Lahman files; the Chadwick register downloader remains `tools/fetch_register.py`.

## Alternatives
- Keep the package computation-only and document manual downloads (ADR-0068 as written), not chosen now because every user repeats the same shaping step each season and mistakes there give silently wrong numbers; revisit if FanGraphs objects to scripted access.
- Fetch automatically when a table is missing, not chosen now because a calculation that touches the network surprises users and breaks offline runs; revisit if users ask for an opt-in environment variable.
- A separate `sabermetricspy-data` package that ships the tables, not chosen now because it is redistribution; revisit if FanGraphs grants permission.
- Depend on `baseballr` through R, not chosen now because it adds an R runtime to a Python library; revisit if a maintained Python port of `fg_guts` appears (then use it instead of our parser).
- Build `pitcher_war.yaml` and the league fields in the same change, not chosen now because they need the leaderboard API's five-season chunking and the SIERA fit; revisit as the next change.

## Consequences
New public API: `fetch.update_constants`, `fetch.fetch_guts`, `fetch.fetch_park_rows`, `fetch.fetch_league_totals`, `fetch.FetchError`, `constants.default_cache_dir`, and the CLI `sabermetrics constants update|path`. `ConstantsNotFoundError` text changed. The quickstart no longer needs a hand-saved `guts.csv`: run `sabermetrics constants update` once, then once per season.
