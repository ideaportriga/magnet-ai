"""Fixture loader for database initialization."""

from __future__ import annotations

import json
from pathlib import Path

import click
from sqlalchemy import select
from structlog import get_logger

from ..config.app import alchemy


class FixtureLoader:
    """Utility class for loading JSON fixtures into the database."""

    def __init__(self, fixtures_path: Path | str | None = None) -> None:
        """Initialize the fixture loader.

        Args:
            fixtures_path: Path to the fixtures directory. Defaults to src/core/fixtures.
        """
        if fixtures_path is None:
            # Default to the fixtures directory in this package
            self.fixtures_path = Path(__file__).parent
        else:
            self.fixtures_path = Path(fixtures_path)

        self.logger = get_logger()

    async def load_entity_fixtures(self, entity_name: str) -> None:
        """Load fixtures for a specific entity.

        Args:
            entity_name: Name of the entity (corresponds to directory name in fixtures).
        """
        entity_path = self.fixtures_path / entity_name

        if not entity_path.exists():
            await self.logger.awarning(
                f"No fixtures directory found for entity: {entity_name}"
            )
            return

        # Get the model class dynamically
        model_class = self._get_model_class(entity_name)
        if model_class is None:
            await self.logger.aerror(f"No model class found for entity: {entity_name}")
            return

        # Load all JSON files in the entity directory
        json_files = list(entity_path.glob("*.json"))
        if not json_files:
            await self.logger.awarning(f"No JSON files found in {entity_path}")
            return

        # Use direct database session instead of service
        async with alchemy.get_session() as session:
            for json_file in json_files:
                await self.logger.ainfo(f"Loading fixtures from {json_file}")
                try:
                    # Load JSON data directly since open_fixture_async expects different parameters
                    with open(json_file, "r", encoding="utf-8") as f:
                        fixture_data = json.load(f)

                    # Ensure it's a list
                    if not isinstance(fixture_data, list):
                        fixture_data = [fixture_data]

                    # Insert or update records
                    for record_data in fixture_data:
                        # Parse datetime fields
                        record_data = self._parse_datetime_fields(
                            record_data, model_class
                        )

                        # Remove timestamps if they exist, let the database handle them
                        record_data.pop("created_at", None)
                        record_data.pop("updated_at", None)

                        # Check if record exists by ID or system_name
                        existing_record = None
                        if "id" in record_data:
                            existing_record = await session.get(
                                model_class, record_data["id"]
                            )
                        elif (
                            hasattr(model_class, "system_name")
                            and "system_name" in record_data
                        ):
                            result = await session.execute(
                                select(model_class).where(
                                    model_class.system_name
                                    == record_data["system_name"]
                                )
                            )
                            existing_record = result.scalar_one_or_none()

                        if existing_record:
                            # Update existing record
                            for key, value in record_data.items():
                                if hasattr(existing_record, key):
                                    setattr(existing_record, key, value)
                            await self.logger.ainfo(
                                f"Updated record: {record_data.get('system_name', record_data.get('id'))}"
                            )
                        else:
                            # Create new record
                            new_record = model_class(**record_data)
                            session.add(new_record)
                            await self.logger.ainfo(
                                f"Created record: {record_data.get('system_name', record_data.get('id'))}"
                            )

                    await session.commit()
                    await self.logger.ainfo(
                        f"Successfully loaded {len(fixture_data)} records from {json_file.name}"
                    )

                except Exception as e:
                    await session.rollback()
                    await self.logger.aerror(
                        f"Error loading fixtures from {json_file}: {e}"
                    )
                    raise

    async def load_all_fixtures(self) -> None:
        """Load fixtures for all entities."""
        # Get all entity directories
        entity_dirs = [
            d
            for d in self.fixtures_path.iterdir()
            if d.is_dir() and not d.name.startswith("_")
        ]

        if not entity_dirs:
            await self.logger.awarning("No entity directories found in fixtures path")
            return

        for entity_dir in sorted(entity_dirs):
            await self.load_entity_fixtures(entity_dir.name)

    def _get_model_class(self, entity_name: str) -> type | None:
        """Get the model class for an entity name.

        Args:
            entity_name: Name of the entity.

        Returns:
            Model class or None if not found.
        """
        try:
            # Import the model dynamically - adjust path based on actual structure
            if entity_name == "ai_model":
                module_path = "src.core.db.models.ai_model"
                class_name = "AIModel"
            elif entity_name == "evaluation_set":
                module_path = "src.core.db.models.evaluation_set.evaluation_set"
                class_name = "EvaluationSet"
            elif entity_name == "collection":
                module_path = "src.core.db.models.collection.collection"
                class_name = "Collection"
            else:
                module_path = f"src.core.db.models.{entity_name}"
                class_name = self._entity_name_to_class_name(entity_name)

            module = __import__(module_path, fromlist=[class_name])
            return getattr(module, class_name)
        except (ImportError, AttributeError) as e:
            print(f"Could not import model {entity_name}: {e}")
            return None

    def _entity_name_to_class_name(self, entity_name: str) -> str:
        """Convert entity name to class name.

        Args:
            entity_name: Entity name (e.g., 'agent', 'ai_model').

        Returns:
            Class name (e.g., 'Agent', 'AIModel').
        """
        # Split by underscore and capitalize each part
        parts = entity_name.split("_")
        return "".join(part.capitalize() for part in parts)

    def _parse_datetime_fields(self, record_data: dict, model_class: type) -> dict:
        """Parse datetime fields from string to datetime objects.

        Args:
            record_data: Record data dictionary.
            model_class: Model class to check for datetime fields.

        Returns:
            Updated record data with parsed datetime fields.
        """
        from datetime import datetime

        from dateutil import parser

        # Create a copy to avoid modifying the original
        parsed_data = record_data.copy()

        # Get all datetime fields from the model
        datetime_fields = []
        if hasattr(model_class, "__table__"):
            for column in model_class.__table__.columns:
                # Check if column type is DateTimeUTC or similar datetime type
                if (
                    hasattr(column.type, "python_type")
                    and column.type.python_type == datetime
                ):
                    datetime_fields.append(column.name)
                elif (
                    "datetime" in str(column.type).lower()
                    or "timestamp" in str(column.type).lower()
                ):
                    datetime_fields.append(column.name)

        # Parse datetime string fields
        for field_name in datetime_fields:
            if field_name in parsed_data and isinstance(parsed_data[field_name], str):
                try:
                    parsed_data[field_name] = parser.parse(parsed_data[field_name])
                except (ValueError, TypeError) as e:
                    print(f"Warning: Could not parse datetime field {field_name}: {e}")
                    # Remove the field if it can't be parsed
                    parsed_data.pop(field_name, None)

        return parsed_data


# CLI commands for fixture loading
@click.group(
    name="fixtures", invoke_without_command=False, help="Manage database fixtures."
)
def fixtures_group() -> None:
    """Manage database fixtures."""


@fixtures_group.command(
    name="load", help="Load fixtures for specific entity or all entities"
)
@click.option(
    "--entity",
    help="Entity name to load fixtures for (e.g., agent, prompt). If not provided, loads all entities.",
    type=click.STRING,
    required=False,
    show_default=False,
)
@click.option(
    "--fixtures-path",
    help="Path to fixtures directory",
    type=click.Path(exists=True, file_okay=False, dir_okay=True, path_type=Path),
    required=False,
    show_default=False,
)
def load_fixtures(entity: str | None, fixtures_path: Path | None) -> None:
    """Load database fixtures.

    Args:
        entity: Specific entity to load fixtures for.
        fixtures_path: Custom path to fixtures directory.
    """
    import anyio
    from rich import get_console

    console = get_console()

    async def _load_fixtures() -> None:
        loader = FixtureLoader(fixtures_path)

        if entity:
            console.rule(f"Loading fixtures for entity: {entity}")
            await loader.load_entity_fixtures(entity)
        else:
            console.rule("Loading all fixtures")
            await loader.load_all_fixtures()

        console.print("✅ Fixtures loaded successfully")

    try:
        anyio.run(_load_fixtures)
    except Exception as e:
        console.print(f"❌ Error loading fixtures: {e}")
        raise


@fixtures_group.command(name="list", help="List available fixture entities")
@click.option(
    "--fixtures-path",
    help="Path to fixtures directory",
    type=click.Path(exists=True, file_okay=False, dir_okay=True, path_type=Path),
    required=False,
    show_default=False,
)
def list_fixtures(fixtures_path: Path | None) -> None:
    """List available fixture entities.

    Args:
        fixtures_path: Custom path to fixtures directory.
    """
    from rich import get_console
    from rich.table import Table

    console = get_console()
    loader = FixtureLoader(fixtures_path)

    # Get all entity directories
    entity_dirs = [
        d
        for d in loader.fixtures_path.iterdir()
        if d.is_dir() and not d.name.startswith("_")
    ]

    if not entity_dirs:
        console.print("No fixture entities found")
        return

    table = Table(title="Available Fixture Entities")
    table.add_column("Entity", style="cyan")
    table.add_column("JSON Files", style="green")
    table.add_column("Path", style="dim")

    for entity_dir in sorted(entity_dirs):
        json_files = list(entity_dir.glob("*.json"))
        json_count = len(json_files)

        table.add_row(
            entity_dir.name,
            f"{json_count} files" if json_count > 0 else "No files",
            str(entity_dir),
        )

    console.print(table)

    if any(len(list(d.glob("*.json"))) > 0 for d in entity_dirs):
        console.print("\n📝 JSON files found in entities:")
        for entity_dir in sorted(entity_dirs):
            json_files = list(entity_dir.glob("*.json"))
            if json_files:
                console.print(
                    f"  {entity_dir.name}: {', '.join(f.stem for f in json_files)}"
                )
