#!/bin/sh
set -e

echo "🚀 Starting Magnet AI application..."

# Update web configurations
echo "📝 Updating web configurations..."
python update_web_configs.py

# Wait for PostgreSQL to be ready
if [ -n "$DB_HOST" ]; then
    echo "⏳ Waiting for PostgreSQL at $DB_HOST:${DB_PORT:-5432}..."
    max_attempts=30
    attempt=0
    
    while [ $attempt -lt $max_attempts ]; do
        if nc -z "$DB_HOST" "${DB_PORT:-5432}" 2>/dev/null; then
            echo "✅ PostgreSQL is ready!"
            break
        fi
        attempt=$((attempt + 1))
        echo "Waiting... ($attempt/$max_attempts)"
        sleep 2
    done
    
    if [ $attempt -eq $max_attempts ]; then
        echo "❌ PostgreSQL failed to start within 60 seconds"
        exit 1
    fi
fi

# Database reset (DANGER: drops all data)
if [ "$RESET_DB" = "true" ]; then
    echo "⚠️  WARNING: Resetting database (this will drop all data)..."
    
    # Remove all migration files
    echo "🗑️  Removing all migration files..."
    rm -rf /app/src/core/db/migrations/versions/*.py 2>/dev/null || true
    
    # Clear ddl_version table
    echo "🧹 Clearing ddl_version table..."
    PYTHONPATH=/app/src .venv/bin/python -c "
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
from core.config.base import get_settings

async def clear_ddl():
    engine = create_async_engine(get_settings().db.URL)
    async with engine.begin() as conn:
        await conn.execute(text('DROP TABLE IF EXISTS ddl_version'))
        print('✅ ddl_version table dropped')
    await engine.dispose()

asyncio.run(clear_ddl())
" || echo "ℹ️  No ddl_version table to clear"
    
    # Create fresh initial migration
    echo "📝 Creating fresh initial migration..."
    mkdir -p /app/src/core/db/migrations/versions
    PYTHONPATH=/app/src .venv/bin/alembic -c /app/src/core/db/migrations/alembic.ini revision --autogenerate -m "initial migration"
    
    # Apply the migration
    echo "🚀 Applying initial migration..."
    PYTHONPATH=/app/src .venv/bin/alembic -c /app/src/core/db/migrations/alembic.ini upgrade head
    
    echo "✅ Database reset complete!"
fi

# Smart migration management: automatically handle initialization and updates
if [ "$RUN_MIGRATIONS" = "true" ]; then
    echo "� Checking database migration status..."
    
    # Ensure migrations directory exists
    mkdir -p /app/src/core/db/migrations/versions
    
    # Check if any migration files exist
    migration_count=$(find /app/src/core/db/migrations/versions -name "*.py" -type f 2>/dev/null | wc -l | tr -d ' ')
    
    if [ "$migration_count" -eq 0 ]; then
        echo "📝 No migrations found. Creating initial migration from models..."
        PYTHONPATH=/app/src .venv/bin/alembic -c /app/src/core/db/migrations/alembic.ini revision --autogenerate -m "initial migration"
        echo "✅ Initial migration created!"
    else
        echo "ℹ️  Found $migration_count existing migration(s)"
    fi
    
    # Apply all pending migrations
    echo "� Applying database migrations..."
    PYTHONPATH=/app/src .venv/bin/alembic -c /app/src/core/db/migrations/alembic.ini upgrade head
    echo "✅ Migrations applied successfully!"
else
    echo "⏭️  Skipping migrations (RUN_MIGRATIONS=false)"
fi

# Legacy support: INIT_DB flag (deprecated, use RUN_MIGRATIONS instead)
if [ "$INIT_DB" = "true" ]; then
    echo "⚠️  INIT_DB is deprecated. Use RUN_MIGRATIONS=true instead."
    echo "   INIT_DB=true is now handled automatically by RUN_MIGRATIONS."
fi

# Load fixtures
if [ "$RUN_FIXTURES" = "true" ]; then
    echo "📦 Loading database fixtures..."
    PYTHONPATH=/app/src .venv/bin/python /app/manage_fixtures.py fixtures load
    echo "✅ Fixtures loaded successfully!"
fi

echo "🎉 Application is ready to start!"

# Start app
exec "$@"
