#!/usr/bin/env python3
"""CLI script for managing database fixtures."""

from __future__ import annotations

import sys
from pathlib import Path

import click

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.core.fixtures.loader import fixtures_group  # noqa: E402


@click.group()
def cli() -> None:
    """Database fixtures management CLI."""


# Add the fixtures group to the main CLI
cli.add_command(fixtures_group)


if __name__ == "__main__":
    cli()
