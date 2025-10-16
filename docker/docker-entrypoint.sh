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
    
    # Clear all tables from database
    echo "🧹 Dropping all tables from database..."
    PYTHONPATH=/app/src .venv/bin/python -c "
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
from core.config.base import get_settings

async def clear_database():
    engine = create_async_engine(get_settings().db.URL)
    async with engine.begin() as conn:
        # Drop all tables
        await conn.execute(text('DROP SCHEMA public CASCADE'))
        await conn.execute(text('CREATE SCHEMA public'))
        await conn.execute(text('GRANT ALL ON SCHEMA public TO postgres'))
        await conn.execute(text('GRANT ALL ON SCHEMA public TO public'))
        print('✅ All tables dropped')
    await engine.dispose()

asyncio.run(clear_database())
" || echo "ℹ️  Failed to clear database"
    
    # Apply migrations to recreate tables
    echo "🚀 Applying migrations..."
    PYTHONPATH=/app/src .venv/bin/alembic -c /app/src/core/db/migrations/alembic.ini upgrade head
    
    echo "✅ Database reset complete!"
fi

# Run migrations
if [ "$RUN_MIGRATIONS" = "true" ]; then
    echo "� Applying database migrations..."
    PYTHONPATH=/app/src .venv/bin/alembic -c /app/src/core/db/migrations/alembic.ini upgrade head
    echo "✅ Migrations applied successfully!"
else
    echo "⏭️  Skipping migrations (RUN_MIGRATIONS=false)"
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
