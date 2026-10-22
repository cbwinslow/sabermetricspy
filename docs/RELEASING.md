# Releasing to PyPI

The package is published by `.github/workflows/publish.yml` with PyPI trusted publishing (no API token is stored).

## One-time setup (owner)
1. On pypi.org: Account settings, Publishing, add a **pending publisher** for project `sabermetricspy`: owner `cbwinslow`, repository `sabermetricspy`, workflow `publish.yml`, environment `pypi`.
2. On GitHub: repository Settings, Environments, create an environment named `pypi` (optionally require your approval).
3. Settle the FanGraphs data question first (ADR-0066).

## Each release
1. Bump the version in `pyproject.toml`, `src/sabermetricspy/__init__.py` and `CITATION.cff`; move the `[Unreleased]` notes in `CHANGELOG.md` under the new version.
2. Run the gates: `uv run ruff check .`, `uv run ruff format --check .`, `uv run pyright`, `uv run pytest`, `openspec validate --all`, and regenerate `docs/METHODOLOGY.md` (`uv run python -m sabermetricspy.methodology > docs/METHODOLOGY.md`).
3. Tag `vX.Y.Z`, push `main` and the tag, wait for CI to pass.
4. Create a GitHub release from the tag. The workflow builds, runs `twine check` and uploads.
5. Verify in a clean environment: `pip install sabermetricspy==X.Y.Z` and run the quickstart.

Seasonal constants go stale each offseason: re-run the scripts in `tools/` (see `docs/VERIFICATION.md`) and release a data update.
