# Contributing

## For All Contributors

### First-Time Setup

```bash
# Clone the repository
git clone https://github.com/nguyentran0212/genesis-scaffolding
cd genesis-scaffolding

# Install all dependencies (Python + Node.js)
make setup

# Install pre-commit hooks
uv run pre-commit install
```

### Before Opening a Pull Request

Run the full quality gate locally. CI will catch the same issues, but catching them locally saves time.

```bash
make check-all
```

If you only changed Python code:

```bash
make check-all-backend
```

### Code Conventions

- **Python**: Follow the ruff rules configured in `pyproject.toml`. Run `make lint-fix-backend` to auto-fix what ruff can fix.
- **Tests**: All new functionality should have tests. See [Testing](docs/developer_guides/maintaining/testing.md) for patterns.
- **Commits**: Write clear, concise commit messages. Describe *why* something changed, not just *what* changed.

### Pre-Merge Checklist

- [ ] `make check-all` passes locally
- [ ] Pre-commit hooks are installed (`uv run pre-commit install`)
- [ ] New code has tests (unit or integration as appropriate)
- [ ] No secrets or credentials committed (use environment variables)
- [ ] Documentation updated if behaviour changed

---

## For AI Agents

Before writing any code or opening a PR, read these documents in order:

1. **[`AGENTS.md`](AGENTS.md)** — High-level instructions for agents working in this codebase
2. **[`docs/architecture/scaffolding-overview.md`](docs/architecture/scaffolding-overview.md)** — Architecture overview
3. **[`docs/developer_guides/index.md`](docs/developer_guides/index.md)** — Developer guide index

If you are adapting the scaffolding for a new use case, read the adaptation guide **before** touching any code:

- **[`docs/developer_guides/adaptation/decision-process.md`](docs/developer_guides/adaptation/decision-process.md)**

### Quick Reference for Agents

| Task | Command |
|------|---------|
| Validate everything | `make check-all` |
| Run backend checks | `make check-all-backend` |
| Run frontend checks | `make type-check-frontend test-frontend` |
| Start dev environment | `make dev` |
| Build for production | `make build` |
| Run tests | `make test-backend` / `make test-frontend` |

### What to Do When Implementing a Feature

1. Read the relevant architecture doc first
2. Run `make check-all` to establish a clean baseline
3. Implement the smallest change that solves the problem
4. Add or update tests
5. Run `make check-all` again — it must pass
6. Do not skip the `make check-all` step before claiming work is done

### What NOT to Do

- Do not disable linting or type-checking rules without a documented reason
- Do not add new dependencies without justification (check the existing stack first)
- Do not commit directly to `main` or `master`
- Do not assume code works without running `make check-all`
