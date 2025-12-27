# Schema Management

Manage Magnet AI database schema changes using **Alembic** migrations.

## Apply migrations

Magnet AI uses **Alembic** for schema migrations.

From the repo root (requires Node installed):

```bash
npm run db:upgrade
```

## Check migration status

```bash
npm run db:current
npm run db:history
```

## Roll back one revision (use with care)

```bash
npm run db:downgrade
```