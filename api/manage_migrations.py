#!/usr/bin/env python3
""" """

import argparse
import os
import subprocess
import sys
from pathlib import Path

project_root = Path(__file__).parent
src_path = project_root / "src"
sys.path.insert(0, str(src_path))

MIGRATIONS_DIR = src_path / "core" / "db" / "migrations"
ALEMBIC_INI = MIGRATIONS_DIR / "alembic.ini"


def run_alembic_command(args):
    """Run an Alembic command with the correct paths."""
    env = os.environ.copy()
    env["PYTHONPATH"] = str(src_path)

    cmd = ["alembic", "-c", str(ALEMBIC_INI)] + args
    print(f"Executing: {' '.join(cmd)}")

    result = subprocess.run(cmd, cwd=project_root, env=env)
    return result.returncode


def init_alembic():
    """Initialize Alembic (only if needed)."""
    if not MIGRATIONS_DIR.exists() or not ALEMBIC_INI.exists():
        print("❌ Alembic is not configured. Use this script's commands to initialize.")
        return False
    print("✅ Alembic is already configured.")
    return True


def create_migration(message: str, autogenerate: bool = True):
    """Create a new migration."""
    if not init_alembic():
        return 1

    args = ["revision"]
    if autogenerate:
        args.append("--autogenerate")
    args.extend(["-m", message])

    return run_alembic_command(args)


def upgrade_database(revision: str = "head"):
    """Apply migrations to the database."""
    if not init_alembic():
        return 1

    return run_alembic_command(["upgrade", revision])


def downgrade_database(revision: str):
    """Revert database migrations."""
    if not init_alembic():
        return 1

    return run_alembic_command(["downgrade", revision])


def show_current_revision():
    """Show the current migration revision."""
    if not init_alembic():
        return 1

    return run_alembic_command(["current"])


def show_history():
    """Show the migration history."""
    if not init_alembic():
        return 1

    return run_alembic_command(["history"])


def show_heads():
    """Show migration heads."""
    if not init_alembic():
        return 1

    return run_alembic_command(["heads"])


def main():
    parser = argparse.ArgumentParser(description="Manage Alembic migrations")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Create migration command
    create_parser = subparsers.add_parser("create", help="Create a new migration")
    create_parser.add_argument("message", help="Migration message")
    create_parser.add_argument(
        "--no-autogenerate",
        action="store_true",
        help="Create an empty migration without autogeneration",
    )

    # Apply migrations command
    upgrade_parser = subparsers.add_parser("upgrade", help="Apply migrations")
    upgrade_parser.add_argument(
        "revision",
        nargs="?",
        default="head",
        help="Revision to apply (default: head)",
    )

    # Revert migrations command
    downgrade_parser = subparsers.add_parser("downgrade", help="Revert migrations")
    downgrade_parser.add_argument("revision", help="Revision to revert to")

    # View information commands
    subparsers.add_parser("current", help="Show the current revision")
    subparsers.add_parser("history", help="Show migration history")
    subparsers.add_parser("heads", help="Show migration heads")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 0

    if args.command == "create":
        return create_migration(args.message, not args.no_autogenerate)
    elif args.command == "upgrade":
        return upgrade_database(args.revision)
    elif args.command == "downgrade":
        return downgrade_database(args.revision)
    elif args.command == "current":
        return show_current_revision()
    elif args.command == "history":
        return show_history()
    elif args.command == "heads":
        return show_heads()
    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    sys.exit(main())
