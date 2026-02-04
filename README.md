# Genesis' Scaffolding

## Project Overview

This repository provides a standardized scaffolding for a Python monorepo. It is designed to jumpstart projects requiring a Command Line Interface (CLI), a Terminal User Interface (TUI), and a RESTful API server within a unified codebase.

### Core Components

The project comes pre-configured with the following industry-standard libraries:

* **CLI:** Typer
* **TUI:** Textual
* **API Server:** FastAPI
* **Configuration:** Pydantic-settings
* **Core Logic:** Shared business logic and models

---

## Workspace Architecture

The project utilizes the `uv` workspace feature to manage multiple packages as a single unit.

* **Dependency Linking:** Sub-packages (e.g., `myproject-cli`) reference `myproject-core` via local path overrides in the root `pyproject.toml`. This allows changes in core logic to be reflected immediately across all interfaces without re-installing.
* **Virtual Environment:** A single `.venv` is maintained at the root, containing the union of all dependencies for all sub-packages.

---

## Project Initialization and Renaming

To customize the project name from the default `myproject`:

1. Run the provided script: `./scripts/rename.sh`
2. Enter your desired project name when prompted.
3. The script will perform a global search-and-replace across directory names and configuration files.

---

## Dependency Management with uv

All package management is handled by `uv` for speed and reliability.

* **Synchronize Environment:** `uv sync` installs all dependencies and development tools.
* **Add Package Dependency:** `uv add --package <member-name> <library>`
* **Add Dev Dependency:** `uv add --dev <library>`
* **Execution:** The project entry point is mapped to the `start()` function in `myproject.main`. This function handles initial configuration loading before launching the Typer CLI.
* Run via: `uv run myproject`



---

## Code Quality and Tooling

Standardized checks are enforced via `Ruff` (linting/formatting) and `Pytest` (testing).

### Makefile Commands

A `Makefile` is provided to abstract complex commands. All Python-related tasks are prefixed with `backend-` to distinguish them from future frontend additions.

| Command | Action |
| --- | --- |
| `make setup` | Installs dependencies and git hooks |
| `make backend-format` | Automatically formats code using Ruff |
| `make backend-lint` | Identifies logical errors and style violations |
| `make backend-typecheck` | Performs static type analysis via Pyright |
| `make backend-test` | Executes the test suite across all workspace members |
| `make backend-check-all` | Runs linting, type-checking, and tests sequentially |

---

## Configuration Details for Developers

The monorepo structure is defined in the root `pyproject.toml` under the `[tool.uv.workspace]` and `[tool.uv.sources]` sections. These sections ensure that internal package dependencies are resolved locally rather than via PyPI, facilitating a seamless development loop across the CLI, TUI, and Server components.
