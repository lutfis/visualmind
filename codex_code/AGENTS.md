# Repository Guidelines

## Project Structure & Module Organization
- `main.py` is the single entry point; keep the public API small and pull shared helpers into new modules under a future `visualmind/` package as the codebase grows.
- `pyproject.toml` and `uv.lock` define the Python 3.13 toolchain; edit both through `uv` so dependency resolution stays reproducible.
- Use `scripts/` for automation entry points and keep each helper self-documented.
- Co-locate tests in `tests/` mirroring the module path (`tests/test_main.py` for `main.py`) to keep discovery predictable.

## Build, Test, and Development Commands
- `uv sync` — install or refresh the local environment exactly as pinned in `uv.lock`.
- `uv run python main.py` — execute the CLI entry point and verify output during development.
- `uv run python -m pytest` — run the test suite once `pytest` is added to `pyproject.toml`; use `-k name` to focus on a specific test file.
- `uv run python -m build` — produce a source and wheel distribution when preparing a release.

## Coding Style & Naming Conventions
- Follow PEP 8: 4-space indentation, snake_case for functions and modules, PascalCase for classes, and ALL_CAPS for constants.
- Prefer explicit type hints and dataclasses to make the mental model of new contributors clear.
- Keep functions small; extract complex logic into helpers with concise docstrings.
- When adopting formatters or linters (e.g., Ruff, Black), store configuration in `pyproject.toml` and expose wrapper commands under `scripts/`.

## Testing Guidelines
- Standardize on `pytest`; name files `test_<module>.py` and individual tests `test_<behavior>`.
- Require high-signal unit tests for new features plus regression tests before resolving bug reports.
- Use fixtures for shared setup and mark slow or integration scenarios with `@pytest.mark.slow` so they can be filtered locally.
- Target coverage on the code touched by each pull request; publish artifacts once CI is configured.

## Commit & Pull Request Guidelines
- Write commits in imperative mood (`Add parser facade`) with ≤72-character subject lines; group related changes together.
- Reference issues with `Fixes #id` or `Refs #id` in the message body when applicable.
- Pull requests should include a problem statement, a short demo (`uv run python main.py` output, screenshots if UI appears later), and test evidence.
- Solicit at least one review for non-trivial changes; flag migration or deployment considerations in a dedicated checklist item.
