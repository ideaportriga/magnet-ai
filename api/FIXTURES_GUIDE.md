# Database Fixtures Guide

This guide explains how to use the database fixtures system for loading initial data into your application.

## Overview

The fixtures system allows you to load JSON data files into your database tables for initial setup, testing, or development purposes. The fixture structure mirrors your database model structure in `src/core/db/models/`.

## Directory Structure

```
src/core/fixtures/
├── agent/
│   └── default_agents.json
├── ai_app/
│   └── default_apps.json  
├── ai_model/
│   └── default_models.json
├── prompt/
│   └── default_prompts.json
├── api_tool/
├── collection/
├── evaluation/
├── evaluation_set/
├── job/
├── mcp_server/
├── metric/
├── observation/
├── rag_tool/
└── retrieval_tool/
```

Each directory corresponds to a database entity and can contain multiple JSON files with fixture data.

## JSON File Format

Each JSON file should contain an array of objects representing records to be inserted/updated:

```json
[
  {
    "id": "01234567-89ab-cdef-0123-456789abcdef",
    "name": "Example Record",
    "description": "Example description",
    "is_active": true,
    "created_at": "2024-01-01T00:00:00Z",
    "updated_at": "2024-01-01T00:00:00Z"
  },
  {
    "id": "11234567-89ab-cdef-0123-456789abcdef",
    "name": "Another Record",
    "description": "Another description",
    "is_active": true,
    "created_at": "2024-01-01T00:00:00Z", 
    "updated_at": "2024-01-01T00:00:00Z"
  }
]
```

### Important Notes:

1. **UUIDs**: Use proper UUID format for `id` fields
2. **Timestamps**: Use ISO 8601 format for datetime fields
3. **Field Names**: Must match the database column names exactly
4. **Data Types**: Ensure JSON data types match database field types

## Usage

### Via Make Commands

#### Load All Fixtures
```bash
make fixtures-load
```

#### Load Specific Entity
```bash
make fixtures-load-entity entity=agent
make fixtures-load-entity entity=prompt
make fixtures-load-entity entity=ai_model
```

#### List Available Fixtures
```bash
make fixtures-list
```

### Via Direct CLI

#### Load All Fixtures
```bash
PYTHONPATH=src poetry run python manage_fixtures.py fixtures load
```

#### Load Specific Entity
```bash
PYTHONPATH=src poetry run python manage_fixtures.py fixtures load --entity agent
```

#### List Available Fixtures
```bash
PYTHONPATH=src poetry run python manage_fixtures.py fixtures list
```

#### Custom Fixtures Path
```bash
PYTHONPATH=src poetry run python manage_fixtures.py fixtures load --fixtures-path /path/to/custom/fixtures
```

## How It Works

1. **Auto-Discovery**: The system automatically discovers entity directories in the fixtures folder
2. **Model Mapping**: Each entity name is mapped to its corresponding SQLAlchemy model class
3. **Service Discovery**: The system tries to find a specific service class, falling back to a generic repository service
4. **Upsert Operations**: Records are inserted or updated based on matching fields (usually `name`, `slug`, `title`, etc.)
5. **Transaction Safety**: All operations are wrapped in database transactions

## Match Fields for Upsert

The system automatically determines which fields to use for matching during upsert operations:

- `name` (most common)
- `slug`
- `title`
- `email`
- `code`

If none of these fields exist on the model, it falls back to using `id`.

## Adding New Fixtures

1. **Create Entity Directory**: Create a directory under `src/core/fixtures/` matching your entity name
2. **Add JSON Files**: Create one or more JSON files with your fixture data
3. **Test Loading**: Use `make fixtures-load-entity entity=your_entity` to test
4. **Verify**: Check your database to ensure data was loaded correctly

## Example Workflow

1. Set up your database:
   ```bash
   make db-create
   make db-upgrade
   ```

2. Load all initial fixtures:
   ```bash
   make fixtures-load
   ```

3. Or load specific entities as needed:
   ```bash
   make fixtures-load-entity entity=agent
   make fixtures-load-entity entity=ai_model
   ```

## Error Handling

- **Missing Entity**: If an entity directory doesn't exist, a warning is logged
- **No JSON Files**: If no JSON files are found in an entity directory, a warning is logged
- **Model Not Found**: If the corresponding model class can't be imported, an error is logged
- **Service Not Found**: If no service class is found, the system falls back to a generic service
- **JSON Errors**: If JSON files are malformed, the error is logged and the operation stops
- **Database Errors**: Database errors are logged and re-raised

## Best Practices

1. **Use Consistent IDs**: Use proper UUIDs for consistent identification
2. **Include Timestamps**: Always include `created_at` and `updated_at` fields
3. **Logical Grouping**: Group related records in the same JSON file
4. **Descriptive Names**: Use descriptive names for JSON files (e.g., `default_agents.json`, `test_prompts.json`)
5. **Validate Data**: Ensure all required fields are present and data types are correct
6. **Version Control**: Keep fixture files in version control for team consistency

## Troubleshooting

### Common Issues:

1. **ImportError**: Ensure your models are properly defined and importable
2. **Missing Fields**: Check that all required fields are present in your JSON
3. **UUID Format**: Ensure UUIDs are properly formatted
4. **Timestamp Format**: Use ISO 8601 format for datetime fields
5. **Service Errors**: If custom services fail, the system will fall back to generic services

### Debug Mode:

To see detailed logging during fixture loading, check the application logs. The system uses structured logging to provide detailed information about the loading process.
