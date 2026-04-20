#!/usr/bin/env python3
"""CLI script for managing database fixtures."""

from __future__ import annotations

import sys
from pathlib import Path

import click

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Load .env files (project root + api/.env) so DB_NAME / DB_HOST / etc.
# resolve correctly when invoked via `npm run fixtures:load` (which uses
# `poetry run` without sourcing the env files).
from src.config.config import load_env  # noqa: E402

load_env()

from src.core.fixtures.loader import fixtures_group  # noqa: E402


@click.group()
def cli() -> None:
    """Database fixtures management CLI."""


# Add the fixtures group to the main CLI
cli.add_command(fixtures_group)


if __name__ == "__main__":
    cli()
