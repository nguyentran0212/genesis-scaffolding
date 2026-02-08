# Genesis Scaffolding

<p align="center">
  <img src="assets/logo.png" alt="Genesis Scaffolding Logo" width="100%">
</p>

Genesis Scaffolding is a clean, pre-configured scaffolding to build LLM-based applications.

It is also a toolkit for doing useful stuffs with locally deployed small language models (SLMs).

## Project Goals

### For Developers: The Scaffolding

The goal of Genesis Scaffolding project is to give you a foundational codebase so that you can start building your application that involves large language models. This codebase aims to be understandable and maintainable by both human developers and LLM-based coding agents.

The codebase of this scaffolding is designed according to the following principles:

- **Clarity over Abstraction:** The architecture is designed to be thin and close to the logic. We don't want to go through layers and layers of useless abstraction and generics to get to the implementation logic.
- **Well-defined Dependencies:** No circular dependencies. Every package and module has a narrowly defined purpose.
- **Canonical Tooling:** The project utilizes modern, standard Python practices and libraries (e.g., `uv`, `Pydantic`, `pydantic-settings`, `Typer`, `Textual`, `FastAPI`) to ensure the codebase is both learnable and useful.

Out of the box, Genesis Scaffolding provides a pre-configured monorepo structure, configuration management, LLM client with asynchronous streaming, workflow engine, CLI, TUI, and RESTful API server.

### For Users: A toolkit for using SLM

The goal of Genesis Scaffolding is to provide a tailored toolkit for Small Language Models (4B-12B dense models, or up-to 30B sparse MoE models). We specifically optimize for environments where models are served via OpenAI-compatible endpoints, such as a local `llama-cpp` server.

Our approach to maximizing the utility of SLMs is based on the following ideas:

- **Instruction Following over Planning:** Modern SLMs are highly capable of following instructions and handling long contexts. However, they struggle with reliable multi-step planning and complex tool-use (such as file editing). These gaps often lead to high latency and unreliable outcome of tasks.
- **Offloading Orchestration to the Framework:** In many real-world tasks, the optimal execution path is already known. By defining this process as a deterministic workflow, we remove the burden of planning from the model. This allows the SLM to focus entirely on the content of the task rather than the management of the process.
- **Native Terminal Integration:** By making workflows executable from the CLI, the project enables advanced use cases such as batch processing of documents or scheduling recurring tasks via `cron`.

Out of the box, Genesis Scaffolding provides a clean CLI to trigger workflows. You can define workflows with YAML files.


## User Guide

Follow these steps to set up Genesis Scaffolding and run your first local workflow.

### Prerequisites

Ensure you have the following installed on your system:

* **Git**: For cloning the repository.
* **uv**: The high-performance Python package manager used for environment and dependency management.

### Installation

Clone the repository and synchronize the environment:

```bash
git clone https://github.com/your-repo/genesis-scaffolding.git
cd genesis-scaffolding
uv sync

```

### Configure the LLM Backend

Genesis Scaffolding relies on an OpenAI-compatible endpoint. You have two primary options:

#### Option A: Fully Local (Recommended)

Use a local backend to run Small Language Models (SLMs) privately on your hardware.

* **llama.cpp**: Build and deploy [llama.cpp](https://github.com/ggml-org/llama.cpp). Run the server and ensure your model's context window is set to at least **16k tokens**.
* **LMStudio**: Alternatively, use LMStudio to load a model and toggle the "Local Server" option.
* **Environment Setup**: Copy `.env.example` to `.env`. Update the following:
* `MYPROJECT_LLM_BASE_URL`: Set to your local path (e.g., `http://localhost:8080/v1`).
* `MYPROJECT_LLM_MODEL`: Set to your model identifier (e.g., `local-model`).



#### Option B: Hosted (OpenRouter)

If you do not wish to host a model locally, you can use OpenRouter.

* The project defaults to `nvidia/nemotron-3-nano-30b-a3b:free`.
* Obtain an API key from [OpenRouter](https://openrouter.ai/).
* In your `.env` file, set `MYPROJECT_LLM_API_KEY` to your key.

### Running the CLI

Use the `uv run` command to interact with the system.

* **List all available workflows**:
```bash
uv run myproject run --list

```


* **View input requirements for a specific workflow**:
```bash
uv run myproject run <WORKFLOW_ID> --help

```


* **Execute a workflow**:
```bash
uv run myproject run <WORKFLOW_ID> --input_name "value"

```



### Create Your Own Workflows

Workflows are defined in YAML and stored in the `workflows/` directory. For instructions on defining inputs, steps, and logic, see [docs/workflow_architecture.md](https://www.google.com/search?q=docs/workflow_architecture.md).

## Developer Guide

### Project Initialization

1. **Clone & Reset:** Shallow clone this repo, delete the `.git` directory, and run `git init` to start a fresh history.
2. **Rename Project:** Run `./scripts/rename.sh` immediately.
  - This script performs a global search-and-replace (e.g., changing `myproject` to `myai`).
  - **Note:** Rename before making logic changes to avoid breaking imports. All package names (e.g., `myproject-cli` -> `myai-cli`) will update accordingly.
3. **Sync Environment:** Run `uv sync` to install dependencies and set up the workspace.
4. **Verify:** Run `uv tree` to inspect the dependency graph and ensure sub-repos are correctly linked.

### Running the Application

Use `uv` to ensure the correct virtual environment and interpreter are used.

* **Default Entry Point:** `uv run myproject`
* **Help / Commands:** `uv run myproject --help`
* **Flow:** The main module initializes the system and launches the CLI. The CLI launches the TUI by default unless a specific subcommand is used.


### Development Workflow

#### Standard Commands (Makefile)

All backend tasks are prefixed to distinguish them from future frontend components.

| Command | Action |
| --- | --- |
| `make setup` | Installs dependencies and git hooks |
| `make backend-format` | Formats code via Ruff |
| `make backend-lint` | Lints code via Ruff |
| `make backend-typecheck` | Static type analysis via Pyright |
| `make backend-test` | Executes Pytest across all workspace members |
| `make backend-check-all` | Sequential lint, type-check, and test |


#### Managing Dependencies

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


#### Expanding the Monorepo (Adding Sub-repos)

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


#### Important: Imports vs. Project Names

A common point of confusion in this monorepo is the difference between the **Project Name** (used by `uv`) and the **Package Name** (used in Python code).

* **Project Name (Hyphens):** Used in `pyproject.toml` and `uv` commands (e.g., `myproject-core`).
* **Package Name (Underscores):** Used in your `.py` files (e.g., `import myproject_core`).

If you add a sub-repo and cannot import it, check that you are using underscores in your `import` statements.



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
``
