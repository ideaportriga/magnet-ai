# Backup & Restore

Backup and restore the Magnet AI PostgreSQL database (with `pgvector`) using `pg_dump`, `psql`, and `pg_restore`.

## Connection Details

Magnet AI uses these environment variables (usually from your `.env` file):

- `DB_HOST`
- `DB_PORT`
- `DB_NAME`
- `DB_USER`
- `DB_PASSWORD`

In the examples below we map them to the standard `psql`/`pg_dump` variables:

```bash
export PGHOST="$DB_HOST"
export PGPORT="$DB_PORT"
export PGDATABASE="$DB_NAME"
export PGUSER="$DB_USER"
export PGPASSWORD="$DB_PASSWORD"
```

> Tip: prefer a `.pgpass` file (or your platform’s secret store) over exporting `PGPASSWORD` in long-lived shells.

## Backup

### Plain SQL (portable)

```bash
# Backup (plain SQL)
pg_dump --no-owner --no-privileges --format=plain --file=backup.sql "$PGDATABASE"

# Optional compression
gzip -9 backup.sql
```

### Custom format (recommended for larger databases)

```bash
# Backup (custom format)
pg_dump --no-owner --no-privileges --format=custom --file=backup.dump "$PGDATABASE"
```

## Restore

> Restores are destructive. Prefer restoring into a new database first, then switching your app to the new database.

### Restore from plain SQL

```bash
# Create the target DB if needed
createdb "$PGDATABASE"

# Restore (fails fast on errors)
psql --set ON_ERROR_STOP=on --dbname="$PGDATABASE" < backup.sql
```

If you compressed the backup (`backup.sql.gz`), restore like this:

```bash
gunzip -c backup.sql.gz | psql --set ON_ERROR_STOP=on --dbname="$PGDATABASE"
```

### Restore from custom format

```bash
# Create the target DB if needed
createdb "$PGDATABASE"

# Restore (drops/recreates objects from the dump)
pg_restore --clean --if-exists --no-owner --dbname="$PGDATABASE" backup.dump
```

