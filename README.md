# Genesis' Scaffolding

<p align="center">
  <img src="assets/logo.png" alt="Genesis Scaffolding Logo" width="100%">
</p>

A standardized Python monorepo scaffolding for LLM-based projects. It provides a production-ready foundation for building complex agentic systems with a pre-configured workspace for CLI, TUI, and RESTful interfaces.

## Key Features

* **Async Streaming LLM Client:** A robust, asynchronous client powered by LiteLLM. Supports real-time token streaming and reasoning-chunk processing out of the box.
* **YAML-Driven Workflow Engine:** Orchestrate multi-step agentic pipelines without modifying Python code. Define logic, data routing, and execution conditions directly in validated YAML manifests.
* **Type-Safe Blackboard Architecture:** Standardized data exchange between workflow steps using Pydantic-validated "Blackboards" and Jinja2 templating.
* **Integrated Workspace Management:** Automated job directory provisioning for every workflow run to isolate inputs, logs, and artifacts.

## Getting Started

### 1. Project Initialization

1. **Clone & Reset:** Shallow clone this repo, delete the `.git` directory, and run `git init` to start a fresh history.
2. **Rename Project:** Run `./scripts/rename.sh` immediately.
* This script performs a global search-and-replace (e.g., changing `myproject` to `myai`).
* **Note:** Rename before making logic changes to avoid breaking imports. All package names (e.g., `myproject-cli` -> `myai-cli`) will update accordingly.


3. **Sync Environment:** Run `uv sync` to install dependencies and set up the workspace.
4. **Verify:** Run `uv tree` to inspect the dependency graph and ensure sub-repos are correctly linked.

### 2. Running the Application

Use `uv` to ensure the correct virtual environment and interpreter are used.

* **Default Entry Point:** `uv run myproject`
* **Help / Commands:** `uv run myproject --help`
* **Flow:** The main module initializes the system and launches the CLI. The CLI launches the TUI by default unless a specific subcommand is used.

---

## Configuration

The backend uses `pydantic-settings` to manage configuration via environment variables or `.env` files.

### Resolution Priority

1. Explicit arguments passed to the `Settings` class.
2. Environment variables.
3. `.env` / `.env.prod` files (loaded from the current working directory).
4. Default values in the Pydantic model.

### Environment Variables & Nesting

The system supports 1-level nested variables using a `_` delimiter and a `myproject_` prefix.

```bash
myproject_llm_base_url="https://openrouter.ai/api/v1"
myproject_llm_api_key="sk1234"

```

These are parsed into a nested structure: `llm = {"base_url": "...", "api_key": "..."}`.
**Modify Schema:** Edit `myproject-core/src/myproject_core/configs.py`.

---

## Development Workflow

### Standard Commands (Makefile)

All backend tasks are prefixed to distinguish them from future frontend components.

| Command | Action |
| --- | --- |
| `make setup` | Installs dependencies and git hooks |
| `make backend-format` | Formats code via Ruff |
| `make backend-lint` | Lints code via Ruff |
| `make backend-typecheck` | Static type analysis via Pyright |
| `make backend-test` | Executes Pytest across all workspace members |
| `make backend-check-all` | Sequential lint, type-check, and test |

---

### Managing Dependencies

In a monorepo, dependencies are managed at the package level, but synchronized at the root.

**Global Sync:** Run `uv sync` from the root. This updates the shared `uv.lock` and ensures the single virtual environment (`.venv`) has all packages required by every sub-repo.

**Adding a Library to a Sub-repo:** Use the `--package` flag to specify which sub-repo needs the library.
```bash
# Adds 'requests' specifically to the API server
uv add --package myproject-server requests

```
**Adding Development Tools:** To add tools used across the entire repo (like a new linter or utility), add them as dev dependencies at the root.
```bash
uv add --dev debugpy
```

---

### Expanding the Monorepo (Adding Sub-repos)

The workspace architecture allows you to add new projects (like a GUI or a worker) while sharing the same core logic.

1. **Initialize the Sub-repo:**
Create a new directory with a library template.
```bash
uv init --lib myproject-gui

```

2. **Register with Workspace:**
Open the **root** `pyproject.toml` and add the new directory to the `members` list:
```toml
[tool.uv.workspace]
members = ["myproject-core", "myproject-cli", "myproject-gui"]

```


3. **Link Internal Dependencies:**
To allow the new sub-repo to use your core logic, link it using the `--package` flag. This creates a "workspace reference" rather than downloading a version from PyPI.
```bash
uv add --package myproject-gui myproject-core

```

4. **Finalize:**
Run `uv sync`. The new package is now "editable," meaning changes made in `myproject-core` are instantly available in `myproject-gui` without a reinstall.

---

### Important: Imports vs. Project Names

A common point of confusion in this monorepo is the difference between the **Project Name** (used by `uv`) and the **Package Name** (used in Python code).

* **Project Name (Hyphens):** Used in `pyproject.toml` and `uv` commands (e.g., `myproject-core`).
* **Package Name (Underscores):** Used in your `.py` files (e.g., `import myproject_core`).

If you add a sub-repo and cannot import it, check that you are using underscores in your `import` statements.


---

## Architecture

### Sub-repo Breakdown

* **`myproject`**: Root entry point; handles initialization.
* **`myproject-core`**: Shared logic (Pydantic schemas, `litellm` wrappers, config management).
* **`myproject-cli`**: Command-line interface via `Typer`.
* **`myproject-tui`**: Terminal User Interface via `Textual`.
* **`myproject-server`**: REST API via `FastAPI`.

> **Note on Imports:** Project names use hyphens (`myproject-core`), but Python packages use underscores. Always import using underscores: `import myproject_core`.

### Implementation Details

Each sub-repo is a standalone Python project with its own `pyproject.toml`. However, the root uses **UV Workspaces** to:

* Maintain a single shared `.venv` at the root.
* Enable editable installs between sub-repos (changes in `core` are immediately reflected in `cli` without re-installing).

**Root `pyproject.toml` Workspace Configuration:**

```toml
[tool.uv.workspace]
members = [
    "myproject-core",
    "myproject-cli",
    "myproject-tui",
    "myproject-server",
]

[tool.uv.sources]
myproject-cli = { workspace = true }

```

Would you like me to help you draft the `rename.sh` script logic to ensure it handles those underscores and hyphens correctly?
