.PHONY: setup backend-lint backend-format backend-test backend-check-all help

# Target directories for Python logic
BACKEND_DIRS := myproject-cli myproject-core myproject-server myproject-tui src
UV := uv run

help: ## Show this help message
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

setup: ## Initial project setup (uv sync)
	uv sync

backend-lint: ## Run Ruff linter on backend
	$(UV) ruff check $(BACKEND_DIRS)

backend-format: ## Auto-format backend code
	$(UV) ruff format $(BACKEND_DIRS)

backend-test: ## Run pytest across backend packages
	$(UV) pytest

backend-check-all: backend-lint backend-test ## Run all backend quality checks

clean: ## Clean up caches and build artifacts
	rm -rf .pytest_cache .ruff_cache .pyright_cache .next
	find . -type d -name "__pycache__" -exec rm -rf {} +
