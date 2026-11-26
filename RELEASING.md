# Releasing urdukit

Releases go to PyPI from GitHub Actions ([`release.yml`](.github/workflows/release.yml)) using
[trusted publishing](https://docs.pypi.org/trusted-publishers/), so no API token is stored anywhere.

## One-time setup (maintainer, on pypi.org)

1. Sign in to <https://pypi.org> and open **Your account → Publishing → Add a new pending publisher**.
2. Fill in:
   - PyPI project name: `urdukit`
   - Owner: `syahra712`
   - Repository name: `urdukit`
   - Workflow name: `release.yml`
   - Environment name: `pypi`
3. On GitHub, open **Settings → Environments → New environment**, name it `pypi`, and optionally
   add yourself as a required reviewer so every upload waits for your click.

## Each release

1. Set `__version__` in `src/urdukit/__init__.py` and date the version's heading in `CHANGELOG.md`.
2. Merge to `main` and wait for CI to pass.
3. On GitHub, open **Releases → Draft a new release**, create the tag `vX.Y.Z` (it must match
   `__version__`), paste that version's CHANGELOG section as the notes, and publish.
4. The workflow builds, runs `twine check`, installs the wheel, and uploads. Check
   <https://pypi.org/project/urdukit/> and then `pip install urdukit` in a clean environment.

A PyPI version can never be re-uploaded, even after deletion. If something is wrong, fix it and
release the next patch version.
