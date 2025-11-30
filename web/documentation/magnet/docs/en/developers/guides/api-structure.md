# Basic Pydantic schemas for entities

This module provides basic Pydantic schemas for all entities that inherit from `UUIDAuditEntityBase`. This helps to avoid code duplication and ensures consistency when creating new entities.

## Structure of basic schemas

### BaseEntitySchema

The base schema for serializing entities. Includes all fields from:

- `UUIDAuditBase`: `id`, `created_at`, `updated_at`
- `UUIDAuditEntityBase`: `name`, `description`, `system_name`, `active_variant`, `category`, `variants`

### BaseEntityCreateSchema

The base schema for creating new entities. Excludes auto-generated fields (`id`, `created_at`, `updated_at`).

### BaseEntityUpdateSchema

The base schema for updating entities. All fields are optional to support partial updates.

## Usage

### 1. Simple inheritance (without additional fields)

```python
from core.domain.base.schemas import (
    BaseEntitySchema,
    BaseEntityCreateSchema,
    BaseEntityUpdateSchema,
)

# For an entity that uses only basic fields
class Prompt(BaseEntitySchema):
    """Prompt schema for serialization."""

class PromptCreate(BaseEntityCreateSchema):
    """Schema for creating a new prompt."""

class PromptUpdate(BaseEntityUpdateSchema):
    """Schema for updating an existing prompt."""
```

### 2. Extending basic schemas with additional fields

```python
from typing import Any, Optional
from pydantic import Field
from core.domain.base.schemas import (
    BaseEntitySchema,
    BaseEntityCreateSchema,
    BaseEntityUpdateSchema,
)

# For an entity with additional fields
class ApiTool(BaseEntitySchema):
    """API Tool schema with additional fields."""

    # Additional fields specific to API Tools
    api_provider: Optional[str] = Field(None, description="API provider name")
    path: Optional[str] = Field(None, description="API endpoint path")
    method: Optional[str] = Field(None, description="HTTP method")

class ApiToolCreate(BaseEntityCreateSchema):
    """Schema for creating API tool."""

    # The same additional fields for creation
    api_provider: Optional[str] = Field(None, description="API provider name")
    path: Optional[str] = Field(None, description="API endpoint path")
    method: Optional[str] = Field(None, description="HTTP method")

class ApiToolUpdate(BaseEntityUpdateSchema):
    """Schema for updating API tool."""

    # The same additional fields for update (all optional)
    api_provider: Optional[str] = Field(None, description="API provider name")
    path: Optional[str] = Field(None, description="API endpoint path")
    method: Optional[str] = Field(None, description="HTTP method")
```

### 3. Creating a service with basic schemas

```python
from advanced_alchemy.extensions.litestar import repository, service
from core.db.models import YourModel

class YourEntityService(service.SQLAlchemyAsyncRepositoryService[YourModel]):
    """Your entity service."""

    class Repo(repository.SQLAlchemyAsyncRepository[YourModel]):
        """Your entity repository."""
        model_type = YourModel

    repository_type = Repo
```

## Examples in the project

### Updated Prompts model

File: `src/core/domain/prompts/model.py`

- Uses basic schemas without additional fields
- Reduced from ~40 lines to ~25 lines

### RAG Tools model

File: `src/core/domain/rag_tools/model.py`

- Simple example of using basic schemas
- Includes service and repository

### API Tools model (example)

File: `src/core/domain/api_tools/model.py`

- Shows how to extend basic schemas with additional fields
- Demonstrates a pattern for entities with specific fields

## Advantages

1. **Elimination of code duplication**: Basic fields are defined once
2. **Consistency**: All entities use the same structure of basic fields
3. **Ease of maintenance**: Changes in basic fields are automatically applied to all entities
4. **Typing**: Full support for TypeScript/Python types
5. **Extensibility**: Easy to add specific fields for particular entities

## Creating a new entity

1. Create a SQLAlchemy model that inherits from `UUIDAuditEntityBase`
2. Create Pydantic schemas that inherit from the base schemas
3. Add additional fields to the schemas if necessary
4. Create a service and repository as an example

This approach ensures uniformity across all domain models and significantly simplifies the addition of new entities.
