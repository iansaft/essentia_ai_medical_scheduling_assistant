# ==============================================================================
# ENVIRONMENT AND CONFIGURATION
# ==============================================================================
# Load environment variables from .env file (silently ignore if missing)
-include .env

# Database connection defaults (fallback to .env.example variables if unset)
PG_HOST               ?= 127.0.0.1
PG_PORT               ?= 5432
PG_SUPERUSER          ?= admin
PG_SUPERUSER_PW       ?= CHANGE_PG_SUPERUSER_PW
PG_DEFAULT_DB         ?= postgres
PG_SUPERUSER_SSL_MODE ?= disable
PG_CNAME              ?= essentia_ai_assistent_postgres

# Migration and Seed tool configurations
GOLANG_MIGRATE_CNAME  ?= essentia_ai_golang_migrate
GOLANG_MIGRATE_IMAGE  ?= migrate/migrate:v4.20.1
MIGRATIONS_PATH       ?= ./db/migrations
SEEDS_PATH            ?= ./db/seeds

# API and development tool configurations
API_PATH              ?= ./apps/api
API_HOST              ?= 0.0.0.0
API_PORT              ?= 8000
SQLC_CMD              ?= sqlc
UV_CMD                ?= uv
PYTEST_CMD            ?= $(UV_CMD) run pytest

# Construct PostgreSQL connection URIs dynamically
# Standard URI for schema migrations
DB_URI := postgres://$(PG_SUPERUSER):$(PG_SUPERUSER_PW)@localhost:$(PG_PORT)/$(PG_DEFAULT_DB)?sslmode=$(PG_SUPERUSER_SSL_MODE)

# Specific URI for seeds using a custom migration tracking table to avoid conflicts
DB_SEED_URI := $(DB_URI)&x-migrations-table=seed_migrations

# Absolute path resolution for volume mounting
ABSOLUTE_MIGRATIONS_PATH := $(shell pwd)/$(MIGRATIONS_PATH)
ABSOLUTE_SEEDS_PATH      := $(shell pwd)/$(SEEDS_PATH)

# ==============================================================================
# DOCKER WRAPPERS (Zero-Dependency & Permission Preserving)
# ==============================================================================
# Retrieve current host user and group IDs to prevent file ownership conflicts (root-lockout)
HOST_UID := $(shell id -u 2>/dev/null || echo 1000)
HOST_GID := $(shell id -g 2>/dev/null || echo 1000)

# --- SCHEMA MIGRATIONS WRAPPERS ---
DOCKER_MIGRATE_CREATE_CMD = docker run --rm \
    --name $(GOLANG_MIGRATE_CNAME)_create \
    -u $(HOST_UID):$(HOST_GID) \
    -v $(ABSOLUTE_MIGRATIONS_PATH):/migrations \
    $(GOLANG_MIGRATE_IMAGE)

DOCKER_MIGRATE_DB_CMD = docker run --rm \
    --name $(GOLANG_MIGRATE_CNAME)_runner \
    -v $(ABSOLUTE_MIGRATIONS_PATH):/migrations \
    --network container:$(PG_CNAME) \
    $(GOLANG_MIGRATE_IMAGE) \
    -path /migrations \
    -database "$(DB_URI)"

# --- SEEDS WRAPPERS ---
DOCKER_SEED_CREATE_CMD = docker run --rm \
    --name $(GOLANG_MIGRATE_CNAME)_seed_create \
    -u $(HOST_UID):$(HOST_GID) \
    -v $(ABSOLUTE_SEEDS_PATH):/seeds \
    $(GOLANG_MIGRATE_IMAGE)

DOCKER_SEED_DB_CMD = docker run --rm \
    --name $(GOLANG_MIGRATE_CNAME)_seed_runner \
    -v $(ABSOLUTE_SEEDS_PATH):/seeds \
    --network container:$(PG_CNAME) \
    $(GOLANG_MIGRATE_IMAGE) \
    -path /seeds \
    -database "$(DB_SEED_URI)"

# ==============================================================================
# MIGRATION TARGETS (Schema definition)
# ==============================================================================

.PHONY: migrate-create
migrate-create: ## Create a new migration file pair (up/down). Usage: make migrate-create name=add_users_table
	@if [ -z "$(name)" ]; then \
		echo "Error: Migration name parameter is missing. Usage: make migrate-create name=create_users_table"; \
		exit 1; \
	fi
	@mkdir -p $(MIGRATIONS_PATH)
	@echo "==> Generating migration files..."
	$(DOCKER_MIGRATE_CREATE_CMD) create -ext sql -dir /migrations -format unix $(name)
	@echo "==> Migration files successfully created at $(MIGRATIONS_PATH)"

.PHONY: migrate-up
migrate-up: ## Apply all pending database migrations
	@echo "==> Executing pending migrations (UP)..."
	$(DOCKER_MIGRATE_DB_CMD) up
	@echo "==> Migrations applied successfully."

.PHONY: migrate-down
migrate-down: ## Rollback migrations. Usage: make migrate-down (rolls back 1 step) or make migrate-down step=2
	@echo "==> Rolling back migrations (DOWN)..."
	@if [ -z "$(step)" ]; then \
		$(DOCKER_MIGRATE_DB_CMD) down 1; \
	else \
		$(DOCKER_MIGRATE_DB_CMD) down $(step); \
	fi
	@echo "==> Rollback completed."

.PHONY: migrate-status
migrate-status: ## Display current applied migration version and status
	@echo "==> Checking current database schema version:"
	$(DOCKER_MIGRATE_DB_CMD) version

.PHONY: migrate-force
migrate-force: ## Force set database schema version (Dirty state recovery). Usage: make migrate-force v=1
	@if [ -z "$(v)" ]; then \
		echo "Error: Version parameter is missing. Usage: make migrate-force v=1"; \
		exit 1; \
	fi
	@echo "==> Forcing schema version to $(v)..."
	$(DOCKER_MIGRATE_DB_CMD) force $(v)
	@echo "==> Schema version successfully forced."

.PHONY: migrate-drop
migrate-drop: ## Drop all tables and clean migration history (Destructive action)
	@echo "==> Dropping all database tables and schema history..."
	$(DOCKER_MIGRATE_DB_CMD) drop -f
	@echo "==> Database schema dropped."


# ==============================================================================
# SEED TARGETS (Data population)
# ==============================================================================

.PHONY: seed-create
seed-create: ## Create a new seed file pair (up/down). Usage: make seed-create name=insert_roles
	@if [ -z "$(name)" ]; then \
		echo "Error: Seed name parameter is missing. Usage: make seed-create name=insert_roles"; \
		exit 1; \
	fi
	@mkdir -p $(SEEDS_PATH)
	@echo "==> Generating seed files..."
	$(DOCKER_SEED_CREATE_CMD) create -ext sql -dir /seeds -format unix $(name)
	@echo "==> Seed files successfully created at $(SEEDS_PATH)"

.PHONY: seed-up
seed-up: ## Apply all pending database seeds
	@echo "==> Executing pending seeds (UP)..."
	$(DOCKER_SEED_DB_CMD) up
	@echo "==> Seeds applied successfully."

.PHONY: seed-down
seed-down: ## Rollback seeds. Usage: make seed-down (rolls back 1 step) or make seed-down step=2
	@echo "==> Rolling back seeds (DOWN)..."
	@if [ -z "$(step)" ]; then \
		$(DOCKER_SEED_DB_CMD) down 1; \
	else \
		$(DOCKER_SEED_DB_CMD) down $(step); \
	fi
	@echo "==> Seed rollback completed."

.PHONY: seed-status
seed-status: ## Display current applied seed version and status
	@echo "==> Checking current database seed version:"
	$(DOCKER_SEED_DB_CMD) version

.PHONY: seed-force
seed-force: ## Force set database seed version (Dirty state recovery). Usage: make seed-force v=1
	@if [ -z "$(v)" ]; then \
		echo "Error: Seed version parameter is missing. Usage: make seed-force v=1"; \
		exit 1; \
	fi
	@echo "==> Forcing seed version to $(v)..."
	$(DOCKER_SEED_DB_CMD) force $(v)
	@echo "==> Seed version successfully forced."

.PHONY: seed-drop
seed-drop: ## Drop all seed history mapping (Destructive action for seeds history only)
	@echo "==> Dropping seed history..."
	$(DOCKER_SEED_DB_CMD) drop -f
	@echo "==> Seed history dropped."


# ==============================================================================
# SQLC TARGETS (Typed SQL code generation and validation)
# ==============================================================================

.PHONY: sqlc-generate
sqlc-generate: ## Generate typed Python persistence code from SQL queries
	@echo "==> Generating SQLc persistence code..."
	cd $(API_PATH) && $(SQLC_CMD) generate
	@echo "==> SQLc code generation completed successfully."

.PHONY: sqlc-compile
sqlc-compile: ## Statically validate SQL queries and schema compatibility
	@echo "==> Compiling and validating SQLc queries..."
	cd $(API_PATH) && $(SQLC_CMD) compile
	@echo "==> SQLc compilation completed successfully."

.PHONY: sqlc-vet
sqlc-vet: ## Run SQLc lint and query validation rules
	@echo "==> Running SQLc query checks..."
	cd $(API_PATH) && $(SQLC_CMD) vet
	@echo "==> SQLc query checks completed successfully."

.PHONY: sqlc-diff
sqlc-diff: ## Verify generated SQLc files are synchronized with schema and queries
	@echo "==> Checking SQLc generated code for pending changes..."
	cd $(API_PATH) && $(SQLC_CMD) diff
	@echo "==> SQLc generated code is synchronized."

.PHONY: sqlc-fmt
sqlc-fmt: ## Format SQL query files referenced by sqlc.yaml
	@echo "==> Formatting SQLc query files..."
	cd $(API_PATH) && $(SQLC_CMD) fmt
	@echo "==> SQLc query formatting completed."

.PHONY: sqlc-fmt-diff
sqlc-fmt-diff: ## Preview SQLc formatting changes without modifying files
	@echo "==> Previewing SQLc query formatting changes..."
	cd $(API_PATH) && $(SQLC_CMD) fmt --diff

.PHONY: sqlc-version
sqlc-version: ## Display installed SQLc version
	@echo "==> SQLc version:"
	$(SQLC_CMD) version

.PHONY: sqlc-check
sqlc-check: sqlc-compile sqlc-vet sqlc-diff ## Run all non-destructive SQLc validation checks
	@echo "==> All SQLc validation checks passed."


# ==============================================================================
# TEST TARGETS (Pytest integration suite and coverage)
# ==============================================================================

.PHONY: test
test: ## Run the complete test suite with configured coverage requirements
	@echo "==> Running complete test suite..."
	cd $(API_PATH) && $(PYTEST_CMD)
	@echo "==> Test suite completed successfully."

.PHONY: test-verbose
test-verbose: ## Run the complete test suite with verbose output
	@echo "==> Running test suite in verbose mode..."
	cd $(API_PATH) && $(PYTEST_CMD) -vv

.PHONY: test-fast
test-fast: ## Run tests without coverage collection for faster local feedback
	@echo "==> Running fast test suite without coverage..."
	cd $(API_PATH) && $(PYTEST_CMD) --no-cov -q

.PHONY: test-fail-fast
test-fail-fast: ## Run tests and stop immediately on the first failure
	@echo "==> Running tests in fail-fast mode..."
	cd $(API_PATH) && $(PYTEST_CMD) -x -vv

.PHONY: test-failed
test-failed: ## Re-run only tests that failed in the previous execution
	@echo "==> Re-running previously failed tests..."
	cd $(API_PATH) && $(PYTEST_CMD) --last-failed -vv

.PHONY: test-one
test-one: ## Run a specific test node. Usage: make test-one test=tests/integration/test_health.py::test_health_returns_ok
	@if [ -z "$(test)" ]; then \
		echo "Error: Test node parameter is missing. Usage: make test-one test=tests/integration/test_health.py::test_health_returns_ok"; \
		exit 1; \
	fi
	@echo "==> Running selected test: $(test)"
	cd $(API_PATH) && $(PYTEST_CMD) "$(test)" -vv

.PHONY: test-integration
test-integration: ## Run tests marked as integration tests
	@echo "==> Running integration test suite..."
	cd $(API_PATH) && $(PYTEST_CMD) -m integration

.PHONY: test-appointments
test-appointments: ## Run appointment and idempotency integration tests
	@echo "==> Running appointment integration tests..."
	cd $(API_PATH) && $(PYTEST_CMD) tests/integration/test_appointments.py -vv

.PHONY: test-availability
test-availability: ## Run availability integration tests
	@echo "==> Running availability integration tests..."
	cd $(API_PATH) && $(PYTEST_CMD) tests/integration/test_availability.py -vv

.PHONY: test-db
test-db: ## Run PostgreSQL database invariant tests
	@echo "==> Running database invariant tests..."
	cd $(API_PATH) && $(PYTEST_CMD) tests/integration/test_database_invariants.py -vv

.PHONY: test-openapi
test-openapi: ## Validate public OpenAPI contract tests
	@echo "==> Running OpenAPI contract tests..."
	cd $(API_PATH) && $(PYTEST_CMD) tests/integration/test_openapi.py -vv

.PHONY: test-collect
test-collect: ## List all discovered tests without executing them
	@echo "==> Collecting available tests..."
	cd $(API_PATH) && $(PYTEST_CMD) --no-cov --collect-only -q

.PHONY: test-coverage
test-coverage: ## Run tests and display detailed terminal coverage with missing lines
	@echo "==> Running test suite with detailed coverage..."
	cd $(API_PATH) && $(PYTEST_CMD) --cov-report=term-missing

.PHONY: test-coverage-html
test-coverage-html: ## Run tests and generate HTML coverage report at apps/api/htmlcov
	@echo "==> Running test suite and generating HTML coverage report..."
	cd $(API_PATH) && $(PYTEST_CMD) \
		--cov-report=term-missing \
		--cov-report=html
	@echo "==> HTML coverage report generated at $(API_PATH)/htmlcov/index.html"


# ==============================================================================
# DEVELOPMENT TARGETS (Dependencies and local API)
# ==============================================================================

.PHONY: deps-sync
deps-sync: ## Synchronize Python dependencies from pyproject.toml and uv.lock
	@echo "==> Synchronizing Python dependencies..."
	cd $(API_PATH) && $(UV_CMD) sync
	@echo "==> Python dependencies synchronized successfully."

.PHONY: deps-lock-check
deps-lock-check: ## Verify uv.lock is synchronized with pyproject.toml
	@echo "==> Checking dependency lock file..."
	cd $(API_PATH) && $(UV_CMD) lock --check
	@echo "==> Dependency lock file is synchronized."

.PHONY: api-run
api-run: ## Run the FastAPI application locally using the application factory
	@echo "==> Starting Essentia API at http://$(API_HOST):$(API_PORT)..."
	cd $(API_PATH) && $(UV_CMD) run \
		--env-file ../../.env \
		uvicorn essentia_api.main:create_app \
		--factory \
		--app-dir src \
		--host $(API_HOST) \
		--port $(API_PORT)

.PHONY: api-dev
api-dev: ## Run the FastAPI application locally with automatic reload
	@echo "==> Starting Essentia API in development mode..."
	cd $(API_PATH) && $(UV_CMD) run \
		--env-file ../../.env \
		uvicorn essentia_api.main:create_app \
		--factory \
		--app-dir src \
		--host $(API_HOST) \
		--port $(API_PORT) \
		--reload


# ==============================================================================
# QUALITY TARGETS (Local CI-style validation)
# ==============================================================================

.PHONY: check
check: sqlc-check test ## Run SQLc validation and the complete automated test suite
	@echo "==> All project quality checks passed."


# ==============================================================================
# HELP MENU
# ==============================================================================

.PHONY: help
help: ## Display available targets and descriptions
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

.DEFAULT_GOAL := help