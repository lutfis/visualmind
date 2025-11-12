# Repository Guidelines

## Project Structure & Module Organization
`scripts/` holds runnable pipelines, notably `graph.py` for entity/relationship extraction and `map_info.py` for map generation. Everything under `codex_code/` not utilized. `data/` stores sample prompts, rendered HTML graphs, and generated map assets; treat it as scratch space and keep sensitive text out of Git. Vendored front-end bundles sit in `lib/` (e.g., `lib/vis-9.1.2/`) and should change only when updating upstream. Tooling metadata is defined in `pyproject.toml` and locked via `uv.lock`.

## Build, Test, and Development Commands
- `uv sync` — install Python 3.13 dependencies from `pyproject.toml`.
- `uv run python scripts/graph.py` — run the entity graph workflow, reading from `data/sample_input_ch.txt` and emitting `data/output_graph.html`.
- `uv run python scripts/map_info.py` — generate a location list plus `data/map.png` via the OpenAI Images API.
- `uv run python codex_code/main.py` — execute experimental utilities; update arguments in-code before running.
Prefer `uv run` so local runs match CI.

## Coding Style & Naming Conventions
Follow PEP 8 with 4-space indentation, snake_case functions, and UpperCamelCase classes. Add type hints on public functions and keep prompts/config in multiline constants near their consumers. When adding scripts, reuse the current structure: load environment first, keep STEP comments short, and enforce JSON-only model I/O. Run formatters/linters (e.g., `uv run ruff format` once Ruff is added) before opening a PR.

## Testing Guidelines
There is no `tests/` directory yet; create one alongside fixtures under `data/` when new behavior ships. Prefer `pytest` with descriptive test names such as `test_extract_entities_handles_duplicates`. Cover prompt-parsing helpers and data-munging utilities with regression tests. For scripts that call external APIs, add lightweight unit tests around transformation helpers and gate network calls behind mocks.

## Commit & Pull Request Guidelines
Keep commit subjects short, present-tense, and imperative, matching the existing style (`map`, `synonyms`, `prompt improvement`). Group related edits and avoid WIP commits. Each PR should describe the change, list new commands or environment variables, cite linked issues, and attach screenshots or artifact paths (`data/output_graph.html`, `data/map.png`) whenever visuals change. Confirm that secrets stay in `.env` and that generated files are ignored or intentionally tracked.

## Security & Configuration Tips
Store API credentials (e.g., `OPENAI_API_KEY`, `AISUITE_API_KEY`) in `.env`; `python-dotenv` loads them automatically. Never commit `.env` or raw textual inputs containing sensitive information. Review generated HTML/PNG outputs before sharing to ensure no confidential data leaks, and scrub `data/` of transient files before pushing.
