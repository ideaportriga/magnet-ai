# DEPRECATION NOTICE:
# This Makefile is deprecated and will be removed in future versions.
# Please use the root `package.json` scripts instead.
# See README.md for details.

.PHONY: run help docker-up docker-down docker-restart docker-logs docker-status docker-clean db-init db-migrate db-upgrade db-downgrade db-current db-history db-stamp db-merge db-reset db-create db-drop db-status db-docker-status fixtures-load fixtures-list fixtures-load-entity migration-check migration-dry-run migration-run migration-collection migration-collection-dry download-static

# PostgreSQL connection parameters from .env
POSTGRES_HOST := $(or $(shell grep '^DATABASE_URL=' .env 2>/dev/null | sed -n 's|.*@\([^:]*\):.*|\1|p'),localhost)
POSTGRES_PORT := $(or $(shell grep '^DATABASE_URL=' .env 2>/dev/null | sed -n 's|.*:\([0-9]*\)/.*|\1|p'),5432)
POSTGRES_USER := $(or $(shell grep '^DATABASE_URL=' .env 2>/dev/null | sed -n 's|.*://\([^:]*\):.*|\1|p'),postgres)
POSTGRES_PASSWORD := $(or $(shell grep '^DATABASE_URL=' .env 2>/dev/null | sed -n 's|.*://[^:]*:\([^@]*\)@.*|\1|p'),password)
POSTGRES_DB := $(or $(shell grep '^DATABASE_URL=' .env 2>/dev/null | sed -n 's|.*/\([^?]*\).*|\1|p'),magnet_dev)

# Docker container name for PostgreSQL (adjust if needed)
POSTGRES_CONTAINER := $(or $(shell docker ps --format "table {{.Names}}" | grep -i postgres | head -1),magnet_postgres)

# Default target
help:
	@echo "Available commands:"
	@echo ""
	@echo "🐳 Docker commands:"
	@echo "  docker-up      - Start PostgreSQL with pgvector in Docker"
	@echo "  docker-down    - Stop and remove containers"
	@echo "  docker-restart - Restart PostgreSQL container"
	@echo "  docker-logs    - Show PostgreSQL container logs"
	@echo "  docker-status  - Show container status"
	@echo "  docker-clean   - Stop containers and remove volumes (DANGER)"
	@echo ""
	@echo "🚀 Application commands:"
	@echo "  run            - Start the server using Poetry"
	@echo "  download-static - Download static files for ReDoc and Stoplight Elements"
	@echo ""
	@echo "🗄️ Database commands:"
	@echo "  db-docker-status - Check Docker PostgreSQL container status"
	@echo "  db-create      - Create PostgreSQL database"
	@echo "  db-drop        - Drop PostgreSQL database"
	@echo "  db-status      - Check database connection status"
	@echo ""
	@echo "📦 Migration commands:"
	@echo "  db-ensure      - Ensure database exists (create if needed)"
	@echo "  db-init        - Initialize database with initial migration"
	@echo "  db-migrate     - Create a new migration"
	@echo "  db-upgrade     - Apply all pending migrations (auto-ensures DB exists)"
	@echo "  db-downgrade   - Downgrade database by one migration"
	@echo "  db-current     - Show current migration version"
	@echo "  db-history     - Show migration history"
	@echo "  db-stamp       - Mark database as up-to-date without running migrations"
	@echo "  db-merge       - Merge multiple heads into one"
	@echo "  db-reset       - DANGER: Reset all migrations and recreate database from scratch"
	@echo ""
	@echo "🔧 Fixture commands:"
	@echo "  fixtures-load       - Load all database fixtures"
	@echo "  fixtures-load-entity - Load fixtures for specific entity (usage: make fixtures-load-entity entity=agent)"
	@echo "  fixtures-list       - List available fixture entities"
	@echo ""
	@echo "🔄 MongoDB Migration commands:"
	@echo "  migration-check     - Check migration readiness (dependencies, connections, etc.)"
	@echo "  migration-dry-run   - Test migration without making changes"
	@echo "  migration-run       - Run full MongoDB to SQLAlchemy migration"
	@echo "  migration-collection - Migrate specific collection (usage: make migration-collection collection=agents)"
	@echo "  migration-collection-dry - Dry-run for specific collection (usage: make migration-collection-dry collection=agents)"
	@echo "  migration-collection-limit - Migrate specific collection with limit (usage: make migration-collection-limit collection=metrics limit=1000)"
	@echo "  migration-collection-dry-limit - Dry-run for specific collection with limit (usage: make migration-collection-dry-limit collection=metrics limit=1000)"
	@echo ""
	@echo "  help               - Show this help message"

# Docker management commands
docker-up:
	@echo "🐳 Starting PostgreSQL 17 with pgvector..."
	@docker-compose up -d postgres
	@echo "⏳ Waiting for PostgreSQL to be ready..."
	@for i in $$(seq 1 30); do \
		if docker exec $(POSTGRES_CONTAINER) pg_isready -U $(POSTGRES_USER) -d $(POSTGRES_DB) >/dev/null 2>&1; then \
			echo "✅ PostgreSQL is ready!"; \
			break; \
		else \
			echo "Waiting... ($$i/30)"; \
			sleep 2; \
		fi; \
		if [ $$i -eq 30 ]; then \
			echo "❌ PostgreSQL failed to start within 60 seconds"; \
			exit 1; \
		fi; \
	done
	@echo "📊 Verifying pgvector extension..."
	@docker exec -e PGPASSWORD=$(POSTGRES_PASSWORD) $(POSTGRES_CONTAINER) psql -h localhost -U $(POSTGRES_USER) -d $(POSTGRES_DB) -c "SELECT extname, extversion FROM pg_extension WHERE extname = 'vector';" || echo "⚠️  pgvector extension not found, but it should be available"

docker-down:
	@echo "🛑 Stopping Docker containers..."
	@docker-compose down

docker-restart:
	@echo "🔄 Restarting PostgreSQL container..."
	@docker-compose restart postgres

docker-logs:
	@echo "📋 Showing PostgreSQL logs..."
	@docker-compose logs -f postgres

docker-status:
	@echo "🔍 Docker containers status:"
	@docker-compose ps

docker-clean:
	@echo "⚠️  WARNING: This will remove all containers and volumes!"
	@read -p "Are you sure you want to clean all Docker data? (yes/no): " confirm && [ "$$confirm" = "yes" ] || (echo "Cancelled." && exit 1)
	@echo "🧹 Cleaning up Docker containers and volumes..."
	@docker-compose down -v
	@docker system prune -f

# Start the server
run:
	poetry run python run.py

# Download static files
download-static:
	@echo "📥 Downloading static files for ReDoc and Stoplight Elements..."
	poetry run python scripts/download_static_files.py

# PostgreSQL database management commands
db-docker-status:
	@echo "Checking Docker PostgreSQL container status..."
	@echo "Looking for PostgreSQL containers:"
	@docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | grep -i postgres || echo "❌ No PostgreSQL containers found"
	@echo "Detected container: $(POSTGRES_CONTAINER)"

db-create:
	@echo "Creating PostgreSQL database..."
	@docker exec -e PGPASSWORD=$(POSTGRES_PASSWORD) $(POSTGRES_CONTAINER) createdb -h localhost -U $(POSTGRES_USER) $(POSTGRES_DB) || echo "Database may already exist"

db-drop:
	@echo "⚠️  WARNING: This will completely delete the database!"
	@read -p "Are you sure you want to drop the database '$(POSTGRES_DB)'? (yes/no): " confirm && [ "$$confirm" = "yes" ] || (echo "Cancelled." && exit 1)
	@docker exec -e PGPASSWORD=$(POSTGRES_PASSWORD) $(POSTGRES_CONTAINER) dropdb -h localhost -U $(POSTGRES_USER) $(POSTGRES_DB)
	@echo "✅ Database '$(POSTGRES_DB)' dropped successfully"

db-status:
	@echo "Checking PostgreSQL database connection..."
	@docker exec -e PGPASSWORD=$(POSTGRES_PASSWORD) $(POSTGRES_CONTAINER) psql -h localhost -U $(POSTGRES_USER) -d $(POSTGRES_DB) -c "SELECT 'Connection successful!' as status;" || echo "❌ Connection failed"

# Database migration commands
db-init:
	@echo "Initializing database with initial migration..."
	PYTHONPATH=src poetry run alembic -c src/core/db/migrations/alembic.ini revision --autogenerate -m "initial migration"

db-migrate:
	@echo "Creating new migration..."
	@if [ -z "$(msg)" ]; then \
		echo "Usage: make db-migrate msg='migration message'"; \
		exit 1; \
	fi
	PYTHONPATH=src poetry run alembic -c src/core/db/migrations/alembic.ini revision --autogenerate -m "$(msg)"

db-ensure:
	@echo "Ensuring database exists..."
	PYTHONPATH=src poetry run python scripts/ensure_database.py

db-upgrade: db-ensure
	@echo "Applying all pending migrations..."
	PYTHONPATH=src poetry run alembic -c src/core/db/migrations/alembic.ini upgrade head

db-downgrade:
	@echo "Downgrading database by one migration..."
	PYTHONPATH=src poetry run alembic -c src/core/db/migrations/alembic.ini downgrade -1

db-current:
	@echo "Current migration version:"
	PYTHONPATH=src poetry run alembic -c src/core/db/migrations/alembic.ini current

db-history:
	@echo "Migration history:"
	PYTHONPATH=src poetry run alembic -c src/core/db/migrations/alembic.ini history

db-stamp:
	@echo "Stamping database as up-to-date..."
	PYTHONPATH=src poetry run alembic -c src/core/db/migrations/alembic.ini stamp head

db-merge:
	@echo "Merging multiple migration heads..."
	PYTHONPATH=src poetry run alembic -c src/core/db/migrations/alembic.ini merge -m "merge heads" heads

db-reset:
	@echo "⚠️  WARNING: This will completely reset your database and migrations!"
	@echo "This will:"
	@echo "  1. Remove all migration files"
	@echo "  2. Clear ddl_version table (if using remote database)"
	@echo "  3. Drop and recreate the PostgreSQL database (if using local Docker)"
	@echo "  4. Create a fresh initial migration"
	@echo "  5. Apply the migration to create clean tables"
	@echo ""
	@read -p "Are you sure you want to continue? (yes/no): " confirm && [ "$$confirm" = "yes" ] || (echo "Cancelled." && exit 1)
	@echo ""
	@echo "🗑️  Removing all migration files..."
	@find src/core/db/migrations/versions -name "*.py" -type f -delete 2>/dev/null || echo "No migration files to remove"
	@echo "🧹 Clearing ddl_version table..."
	@PYTHONPATH=src poetry run python -c "import asyncio; from sqlalchemy.ext.asyncio import create_async_engine; from sqlalchemy import text; from core.config.base import get_settings; async def clear_ddl(): engine = create_async_engine(get_settings().db.URL); async with engine.begin() as conn: await conn.execute(text('DROP TABLE IF EXISTS ddl_version')); print('ddl_version table dropped'); await engine.dispose(); asyncio.run(clear_ddl())" 2>/dev/null || echo "No ddl_version table to clear"
	@echo "🗑️  Checking if using local Docker database..."
	@if echo "$(DATABASE_URL)" | grep -q "localhost"; then \
		echo "Local Docker database detected, dropping and recreating..."; \
		echo "Terminating existing connections to database..."; \
		docker exec -e PGPASSWORD=$(POSTGRES_PASSWORD) $(POSTGRES_CONTAINER) psql -h localhost -U $(POSTGRES_USER) -d postgres -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = '$(POSTGRES_DB)' AND pid <> pg_backend_pid();" 2>/dev/null || true; \
		docker exec -e PGPASSWORD=$(POSTGRES_PASSWORD) $(POSTGRES_CONTAINER) dropdb -h localhost -U $(POSTGRES_USER) $(POSTGRES_DB) --if-exists; \
		echo "🗄️  Creating fresh database..."; \
		docker exec -e PGPASSWORD=$(POSTGRES_PASSWORD) $(POSTGRES_CONTAINER) createdb -h localhost -U $(POSTGRES_USER) $(POSTGRES_DB); \
	else \
		echo "Remote database detected, skipping database recreation..."; \
	fi
	@echo "📁 Ensuring versions directory exists..."
	@mkdir -p src/core/db/migrations/versions
	@echo "📝 Creating fresh initial migration..."
	@PYTHONPATH=src poetry run alembic -c src/core/db/migrations/alembic.ini revision --autogenerate -m "initial migration"
	@echo "🚀 Applying initial migration..."
	@PYTHONPATH=src poetry run alembic -c src/core/db/migrations/alembic.ini upgrade head
	@echo "✅ Database reset complete!"
	@echo ""

# Fixture management commands
fixtures-load:
	@echo "Loading all database fixtures..."
	PYTHONPATH=src poetry run python manage_fixtures.py fixtures load

fixtures-load-entity:
	@if [ -z "$(entity)" ]; then \
		echo "Usage: make fixtures-load-entity entity=<entity_name>"; \
		echo "Example: make fixtures-load-entity entity=agent"; \
		exit 1; \
	fi
	@echo "Loading fixtures for entity: $(entity)"
	PYTHONPATH=src poetry run python manage_fixtures.py fixtures load --entity $(entity)

fixtures-list:
	@echo "Listing available fixture entities..."
	PYTHONPATH=src poetry run python manage_fixtures.py fixtures list
	@echo "📊 Current database schema:"
	@docker exec -e PGPASSWORD=$(POSTGRES_PASSWORD) $(POSTGRES_CONTAINER) psql -h localhost -U $(POSTGRES_USER) -d $(POSTGRES_DB) -c "\dt"

# MongoDB to SQLAlchemy migration commands
migration-check:
	@echo "🔍 Checking migration readiness..."
	PYTHONPATH=src poetry run python check_migration_readiness.py

migration-dry-run:
	@echo "🧪 Running migration dry-run (no changes will be made)..."
	PYTHONPATH=src poetry run python mongo_to_sqlalchemy_migration.py --dry-run

migration-run:
	@echo "🚀 Running MongoDB to SQLAlchemy migration..."
	@echo "⚠️  This will migrate data from MongoDB to PostgreSQL!"
	@read -p "Are you sure you want to continue? (y/N): " confirm; \
	if [ "$$confirm" = "y" ] || [ "$$confirm" = "Y" ]; then \
		PYTHONPATH=src poetry run python mongo_to_sqlalchemy_migration.py; \
	else \
		echo "Migration cancelled."; \
	fi

migration-collection:
	@if [ -z "$(collection)" ]; then \
		echo "Usage: make migration-collection collection=<collection_name>"; \
		echo "Example: make migration-collection collection=agents"; \
		exit 1; \
	fi
	@echo "🔄 Migrating specific collection: $(collection)"
	PYTHONPATH=src poetry run python mongo_to_sqlalchemy_migration.py --collection $(collection)

migration-collection-dry:
	@if [ -z "$(collection)" ]; then \
		echo "Usage: make migration-collection-dry collection=<collection_name>"; \
		echo "Example: make migration-collection-dry collection=agents"; \
		exit 1; \
	fi
	@echo "🧪 Dry-run migration for collection: $(collection)"
	PYTHONPATH=src poetry run python mongo_to_sqlalchemy_migration.py --collection $(collection) --dry-run

migration-collection-limit:
	@if [ -z "$(collection)" ] || [ -z "$(limit)" ]; then \
		echo "Usage: make migration-collection-limit collection=<collection_name> limit=<number>"; \
		echo "Example: make migration-collection-limit collection=metrics limit=1000"; \
		exit 1; \
	fi
	@echo "🔄 Migrating specific collection with limit: $(collection) (limit: $(limit))"
	PYTHONPATH=src poetry run python mongo_to_sqlalchemy_migration.py --collection $(collection) --limit $(limit)

migration-collection-dry-limit:
	@if [ -z "$(collection)" ] || [ -z "$(limit)" ]; then \
		echo "Usage: make migration-collection-dry-limit collection=<collection_name> limit=<number>"; \
		echo "Example: make migration-collection-dry-limit collection=metrics limit=1000"; \
		exit 1; \
	fi
	@echo "🧪 Dry-run migration for collection with limit: $(collection) (limit: $(limit))"
	PYTHONPATH=src poetry run python mongo_to_sqlalchemy_migration.py --collection $(collection) --limit $(limit) --dry-run

# ── Test Commands ──────────────────────────────────────────────────────
.PHONY: test test-unit test-integration test-e2e test-fuzz test-all load-smoke load-standard load-stress load-soak report

REPORTS_DIR := reports

$(REPORTS_DIR):
	@mkdir -p $(REPORTS_DIR)

test-unit: $(REPORTS_DIR)
	PYTHONPATH=src poetry run pytest -m unit \
		--json-report --json-report-file=$(REPORTS_DIR)/unit.json \
		--cov=src --cov-report=json:$(REPORTS_DIR)/coverage-unit.json \
		-x -q

test-integration: $(REPORTS_DIR)
	PYTHONPATH=src poetry run pytest -m integration \
		--json-report --json-report-file=$(REPORTS_DIR)/integration.json \
		--cov=src --cov-report=json:$(REPORTS_DIR)/coverage-integration.json \
		-x -q

test-e2e: $(REPORTS_DIR)
	PYTHONPATH=src poetry run pytest -m e2e \
		--json-report --json-report-file=$(REPORTS_DIR)/e2e.json \
		--cov=src --cov-report=json:$(REPORTS_DIR)/coverage-e2e.json \
		-x -q

test-fuzz: $(REPORTS_DIR)
	PYTHONPATH=src poetry run pytest -m fuzz \
		--json-report --json-report-file=$(REPORTS_DIR)/fuzz.json \
		-x -q --timeout=300

load-smoke: $(REPORTS_DIR)
	poetry run locust -f tests/load/locustfile.py --headless \
		-u 10 -r 2 --run-time 30s --json 2>&1 | tee $(REPORTS_DIR)/load-smoke.json

load-standard: $(REPORTS_DIR)
	poetry run locust -f tests/load/locustfile.py --headless \
		-u 50 -r 5 --run-time 120s --json 2>&1 | tee $(REPORTS_DIR)/load-standard.json

load-stress: $(REPORTS_DIR)
	poetry run locust -f tests/load/locustfile.py --headless \
		-u 200 -r 10 --run-time 300s --json 2>&1 | tee $(REPORTS_DIR)/load-stress.json

load-soak: $(REPORTS_DIR)
	poetry run locust -f tests/load/locustfile.py --headless \
		-u 30 -r 3 --run-time 1800s --json 2>&1 | tee $(REPORTS_DIR)/load-soak.json

test-all: test-unit test-integration test-e2e test-fuzz
	@echo "All test suites completed. Reports in ./$(REPORTS_DIR)/"

test: $(REPORTS_DIR)
	PYTHONPATH=src poetry run pytest -m "not load and not fuzz" \
		--json-report --json-report-file=$(REPORTS_DIR)/all.json \
		--cov=src --cov-report=json:$(REPORTS_DIR)/coverage.json \
		--cov-report=term-missing -q

report:
	PYTHONPATH=src poetry run python scripts/aggregate_reports.py
