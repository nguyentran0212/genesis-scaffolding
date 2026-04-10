# Development Workflow

## Development Conventions

### Verify with `make` before finishing

Always run the full quality check before considering a task complete:

```bash
make check-all      # lint + type-check + test (everything)
```

Or for backend-only changes:

```bash
make check-all-backend
```

This is the same command CI runs. A task is only done when these checks pass with no errors. The master branch is always error-free when a developer or AI agent starts working — keep it that way.

### Do not commit during a code change session

Do not run `git commit` or `git push` while making code changes. The human developer reviews and signs off the final work by committing themselves after verifying all checks pass and the changes look correct.

### Use `make` over raw tool calls

The Makefile is the authoritative entry point for running checks and development tasks — it is what CI uses. Prefer `make check-all` over calling `uv` or `pnpm` directly. Use the Makefile consistently so your local verification matches CI.

---

## Running the Project

The project can be run in three modes. All share the same codebase; only the runtime environment differs.

### 1. Bare Metal — Development

For active development with hot-reload and debug-friendly output.

```bash
# First time setup
make setup

# Run both backend and frontend in parallel (hot-reload enabled)
make dev

# Run backend only
make dev-backend

# Run frontend only
make dev-frontend
```

### 2. Bare Metal — Production

For deploying on a server or workstation without containers.

```bash
# Build (validates everything compiles and passes quality gates)
make build

# Run both backend and frontend in prod mode
make run
```

### 3. Docker Compose

For a self-contained, reproducible environment. Recommended for CI and staging.

```bash
# Build and start all containers in the foreground
make run-container

# Run in the background
make container/up

# Stop and remove containers
make container/down

# View logs
make container/logs
```

---

## Quality Gates

Before committing or opening a PR, run the full quality check locally:

```bash
# Run all checks: lint + type-check + test (both backend and frontend)
make check-all

# Or run them individually
make lint          # backend ruff + frontend eslint (frontend lint currently disabled)
make type-check    # backend pyright + frontend tsc --noEmit
make test          # backend pytest + frontend vitest
```

Use `make check-all-backend` if you only changed Python code.

---

## Pre-commit Hooks

Pre-commit hooks catch issues before they reach CI. They run automatically on `git commit`.

### Install

```bash
# One-time setup — installs the git hook scripts
uv run pre-commit install
```

### Run Manually

```bash
# Run all hooks against all files
uv run pre-commit run --all-files

# Run against staged files only
uv run pre-commit run
```

### What They Check

| Hook | Language | When |
|------|----------|------|
| `ruff format` | Python | Every commit |
| `ruff check --fix` | Python | Every commit |
| `pyright` | Python | Every commit |
| `eslint` | TypeScript/JSX | Every commit (currently disabled — too many legacy errors) |
| `pnpm build` | TypeScript/JSX | On `git push` only (slow) |

---

## CI Pipeline

Every push and pull request runs the full quality gate via GitHub Actions:

```
backend  — uv sync → uv sync --frozen → make check-all-backend
frontend — pnpm install → make build-frontend → make type-check-frontend test-frontend
```

Both jobs must pass for a PR to be merged.

---

## Deployment

Deployment is environment-specific (bare metal, Docker Compose, cloud). The Makefile
does not currently implement deployment targets. Future versions of this guide will
cover deployment patterns.

For now, production deployments typically follow the Docker Compose pattern:

```bash
make container/rebuild
```
