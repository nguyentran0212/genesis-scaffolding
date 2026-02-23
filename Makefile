.PHONY: setup backend-lint backend-format backend-test backend-check-all help

# Target directories for Python logic
BACKEND_DIRS := myproject-cli myproject-core myproject-server myproject-tui src
FASTAPI_MAIN := myproject-server/src/myproject_server/main.py
FASTAPI_DIR := myproject-server/src/myproject_server/

# Directory for frontend
FRONTEND_DIR := myproject-frontend

# Shortcut for tools
UV := uv run
PNPM := cd $(FRONTEND_DIR) && pnpm

help: ## Show this help message
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

setup-backend: ## Initial backend setup (uv sync)
	uv sync

setup-frontend: ## Initial frontend setup (pnpm install)
	$(PNPM) install

setup: setup-backend setup-frontend ## Initial setup for both backend and frontend


### Linting

lint-backend: ## Run Ruff linter on backend
	$(UV) ruff check $(BACKEND_DIRS)

lint-fix-backend: ## Run Ruff linter on backend and fix all fixable problems
	$(UV) ruff check --fix $(BACKEND_DIRS)

### Format

format-backend: ## Auto-format backend code
	$(UV) ruff format $(BACKEND_DIRS)

### Test

test-backend: ## Run pytest across backend packages
	$(UV) pytest

### Run all code quality check

check-all-backend: backend-lint backend-test ## Run all backend quality checks

### Cleanup

clean-backend: ### Clean up cache and build artefacts of the backend
	rm -rf .pytest_cache .ruff_cache .pyright_cache .next
	find . -type d -name "__pycache__" -exec rm -rf {} +

clean-workspace-dir: ## Remove content of workspaces directory
	rm -rf workspaces/

clean-database: ## Remove content of workspaces directory
	rm -rf database/

clean-frontend: ### Clean up frontend
	cd $(FRONTEND_DIR) && rm -rf .next node_modules

clean: clean-workspace-dir clean-database clean-backend ## Clean up caches and build artifacts, workspaces, databases

### Run project in dev

dev-backend: ### Run FastAPI backend in dev mode
	$(UV) fastapi dev $(FASTAPI_MAIN) --reload-dir $(FASTAPI_DIR)

dev-frontend: ### Run frontend in dev mode
	$(PNPM) dev

dev: ### Run both backend and frontend in parallel in dev
	@$(MAKE) -j 2 dev-backend dev-frontend


### Build project

build-frontend: ### Build frontend
	$(PNPM) build


### Run the project in prod on bare metal

run-backend: ### Run backend on bare metal
	$(UV) myproject serve


run-frontend:build-frontend ### Run frontend on bare metal
	$(PNPM) start

run: ### Run both backend and frontend in parallel in prod on bare metal
	@$(MAKE) -j 2 run-backend run-frontend


### Docker / Container Management

build-container: ## Build the Docker image
	docker compose build

up-container: ## Run the project in a container in the background
	docker compose up -d

run-container: ## Build and run the project in a container (one command, foreground)
	docker compose up --build

stop-container: ## Stop the running containers
	docker compose stop

down-container: ## Stop and remove containers, networks, and volumes
	docker compose down -v

logs-container: ## Tail logs from the container
	docker compose logs -f

shell-container: ## Access the running container shell for debugging
	docker compose exec app /bin/bash
