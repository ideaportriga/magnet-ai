# SQL Database Management Guide

Это руководство объясняет, как работать с SQL базой данных в проекте AI Bridge:
- Как добавить новую модель
- Как создать controller (domain) для управления моделью
- Как использовать Alembic после изменения/добавления новых схем
- Примеры работы с моделями

## 1. КАК ДОБАВИТЬ НОВУЮ МОДЕЛЬ

### Шаг 1: Создать модель SQLAlchemy

Создайте файл: `src/core/db/models/{entity_name}/{entity_name}.py`

**Пример модели Product:**

```python
# src/core/db/models/product/product.py
from __future__ import annotations

from typing import Optional
from sqlalchemy import String, Numeric, Boolean, Text
from sqlalchemy.orm import Mapped, mapped_column

from ..base import UUIDAuditEntityBase


class Product(UUIDAuditEntityBase):
    """Product model with additional business fields."""

    __tablename__ = "products"

    # Дополнительные поля специфичные для продукта
    price: Mapped[Optional[float]] = mapped_column(
        Numeric(10, 2), nullable=True, comment="Product price"
    )
    sku: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True, unique=True, comment="Stock Keeping Unit"
    )
    is_available: Mapped[bool] = mapped_column(
        Boolean, default=True, comment="Product availability"
    )
    specifications: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, comment="Product specifications"
    )
```

### Шаг 2: Создать __init__.py файл для модели

```python
# src/core/db/models/product/__init__.py
from .product import Product

__all__ = ["Product"]
```

### Шаг 3: Обновить главный __init__.py файл моделей

```python
# src/core/db/models/__init__.py
# Добавьте импорт новой модели:
from .product import Product

__all__ = [
    # ... существующие модели
    "Product",
]
```

## 2. КАК СОЗДАТЬ CONTROLLER (DOMAIN) ДЛЯ УПРАВЛЕНИЯ МОДЕЛЬЮ

Создание domain структуры для новой модели включает 3 компонента:
- **Schemas** (Pydantic модели для валидации)
- **Service** (бизнес-логика)
- **Controller** (HTTP endpoints)

### Шаг 1: Создать Pydantic схемы

```python
# src/core/domain/products/schemas.py
from __future__ import annotations

from typing import Optional
from pydantic import Field

from core.domain.base.schemas import (
    BaseEntityCreateSchema,
    BaseEntitySchema,
    BaseEntityUpdateSchema,
)


class Product(BaseEntitySchema):
    """Product schema for serialization."""
    
    price: Optional[float] = Field(None, description="Product price")
    sku: Optional[str] = Field(None, description="Stock Keeping Unit")
    is_available: bool = Field(True, description="Product availability")
    specifications: Optional[str] = Field(None, description="Product specifications")


class ProductCreate(BaseEntityCreateSchema):
    """Schema for creating a new product."""
    
    price: Optional[float] = Field(None, description="Product price")
    sku: Optional[str] = Field(None, description="Stock Keeping Unit")
    is_available: bool = Field(True, description="Product availability")
    specifications: Optional[str] = Field(None, description="Product specifications")


class ProductUpdate(BaseEntityUpdateSchema):
    """Schema for updating an existing product."""
    
    price: Optional[float] = Field(None, description="Product price")
    sku: Optional[str] = Field(None, description="Stock Keeping Unit")
    is_available: Optional[bool] = Field(None, description="Product availability")
    specifications: Optional[str] = Field(None, description="Product specifications")
```

### Шаг 2: Создать Service

```python
# src/core/domain/products/service.py
from __future__ import annotations

from advanced_alchemy.extensions.litestar import repository, service

from core.db.models.product import Product


class ProductsService(service.SQLAlchemyAsyncRepositoryService[Product]):
    """Products service with business logic."""

    class Repo(repository.SQLAlchemyAsyncRepository[Product]):
        """Products repository."""

        model_type = Product

    repository_type = Repo

    # Дополнительные методы бизнес-логики
    async def get_by_sku(self, sku: str) -> Product:
        """Get product by SKU."""
        return await self.repository.get_one(sku=sku)

    async def get_available_products(self) -> list[Product]:
        """Get all available products."""
        return await self.repository.list(is_available=True)
```

### Шаг 3: Создать Controller

```python
# src/core/domain/products/controller.py
from __future__ import annotations

from typing import TYPE_CHECKING, Annotated
from uuid import UUID

from advanced_alchemy.extensions.litestar import filters, providers, service
from litestar import Controller, delete, get, patch, post
from litestar.params import Dependency, Parameter

from core.config.constants import DEFAULT_PAGINATION_SIZE
from core.domain.products.service import ProductsService

from .schemas import Product, ProductCreate, ProductUpdate

if TYPE_CHECKING:
    pass


class ProductsController(Controller):
    """Products CRUD Controller"""

    path = "/products"
    tags = ["Products"]

    dependencies = providers.create_service_dependencies(
        ProductsService,
        "products_service",
        filters={
            "pagination_type": "limit_offset",
            "id_filter": UUID,
            "search": "name",
            "search_ignore_case": True,
            "pagination_size": DEFAULT_PAGINATION_SIZE,
        },
    )

    @get()
    async def list_products(
        self,
        products_service: ProductsService,
        filters: Annotated[list[filters.FilterTypes], Dependency(skip_validation=True)],
    ) -> service.OffsetPagination[Product]:
        """List products with pagination and filtering."""
        results, total = await products_service.list_and_count(*filters)
        return products_service.to_schema(
            results, total, filters=filters, schema_type=Product
        )

    @post()
    async def create_product(
        self, products_service: ProductsService, data: ProductCreate
    ) -> Product:
        """Create a new product."""
        obj = await products_service.create(data)
        return products_service.to_schema(obj, schema_type=Product)

    @get("/sku/{sku:str}")
    async def get_product_by_sku(
        self, products_service: ProductsService, sku: str
    ) -> Product:
        """Get a product by its SKU."""
        obj = await products_service.get_by_sku(sku)
        return products_service.to_schema(obj, schema_type=Product)

    @get("/available")
    async def get_available_products(
        self, products_service: ProductsService
    ) -> list[Product]:
        """Get all available products."""
        objs = await products_service.get_available_products()
        return [products_service.to_schema(obj, schema_type=Product) for obj in objs]

    @get("/{product_id:uuid}")
    async def get_product(
        self,
        products_service: ProductsService,
        product_id: UUID = Parameter(
            title="Product ID",
            description="The product to retrieve.",
        ),
    ) -> Product:
        """Get a product by its ID."""
        obj = await products_service.get(product_id)
        return products_service.to_schema(obj, schema_type=Product)

    @patch("/{product_id:uuid}")
    async def update_product(
        self,
        products_service: ProductsService,
        data: ProductUpdate,
        product_id: UUID = Parameter(
            title="Product ID",
            description="The product to update.",
        ),
    ) -> Product:
        """Update a product."""
        obj = await products_service.update(data, item_id=product_id, auto_commit=True)
        return products_service.to_schema(obj, schema_type=Product)

    @delete("/{product_id:uuid}")
    async def delete_product(
        self,
        products_service: ProductsService,
        product_id: UUID = Parameter(
            title="Product ID",
            description="The product to delete.",
        ),
    ) -> None:
        """Delete a product from the system."""
        _ = await products_service.delete(product_id)
```

### Шаг 4: Создать __init__.py для domain

```python
# src/core/domain/products/__init__.py
from .controller import ProductsController
from .schemas import Product, ProductCreate, ProductUpdate
from .service import ProductsService

__all__ = [
    "ProductsController",
    "Product",
    "ProductCreate", 
    "ProductUpdate",
    "ProductsService",
]
```

## 3. КАК ИСПОЛЬЗОВАТЬ ALEMBIC ПОСЛЕ ИЗМЕНЕНИЯ/ДОБАВЛЕНИЯ НОВЫХ СХЕМ

Alembic - это инструмент для управления миграциями базы данных.
В проекте используется **Makefile** для упрощения работы с миграциями.

### Создание новой миграции

```bash
# Создание автоматической миграции (рекомендуется):
make db-migrate msg="Add Product model"

# Для первоначальной инициализации (только при первом запуске):
make db-init
```

### Применение миграций

```bash
# Применить все миграции до последней версии:
make db-upgrade

# Проверить текущее состояние базы данных:
make db-status
```

### Откат миграций

```bash
# Откатить на одну миграцию назад:
make db-downgrade

# ⚠️ ОПАСНО: Полный сброс базы данных и миграций:
make db-reset
```

### Просмотр информации о миграциях

```bash
# Показать текущую версию базы данных:
make db-current

# Показать историю миграций:
make db-history

# Отметить базу как актуальную без применения миграций:
make db-stamp

# Объединить несколько веток миграций:
make db-merge
```

### Управление базой данных

```bash
# Проверить статус Docker контейнера с PostgreSQL:
make db-docker-status

# Создать базу данных:
make db-create

# Удалить базу данных:
make db-drop
```

### Пример полного процесса добавления новой модели

1. **Создайте модель SQLAlchemy** (см. выше)
2. **Создайте миграцию:**
   ```bash
   make db-migrate msg="Add Product model"
   ```
3. **Проверьте созданную миграцию** в `src/core/db/migrations/versions/`
4. **Примените миграцию:**
   ```bash
   make db-upgrade
   ```
5. **Проверьте успешное применение:**
   ```bash
   make db-current
   ```
6. **Создайте domain компоненты** (schemas, service, controller)

### Работа с Docker и базой данных

```bash
# Запустить PostgreSQL в Docker:
make docker-up

# Остановить Docker контейнеры:
make docker-down

# Перезапустить PostgreSQL:
make docker-restart

# Посмотреть логи PostgreSQL:
make docker-logs

# Проверить статус контейнеров:
make docker-status
```

## 4. ПРИМЕРЫ РАБОТЫ С МОДЕЛЯМИ

### Пример работы через Service (Рекомендуется)

```python
async def example_service_usage():
    """Примеры использования через Service слой"""
    
    from core.config.app import alchemy
    from core.domain.prompts.service import PromptsService
    from core.domain.prompts.schemas import PromptCreate, PromptUpdate, PromptVariantSchema
    
    # Правильная инициализация сервиса с сессией
    async with alchemy.get_session() as session:
        service = PromptsService(session=session)
        
        # Создание нового промпта с вариантами
        prompt_data = PromptCreate(
            name="Customer Support Prompt",
            description="AI prompt for customer support responses",
            system_name="support_prompt_v1",
            category="Support",
            active_variant="production",
            variants=[
                PromptVariantSchema(
                    variant="development",
                    text="You are a helpful customer support agent. Answer questions politely.",
                    temperature=0.7,
                    topP=0.9,
                    system_name_for_model="gpt-4",
                    description="Development version with higher creativity"
                ),
                PromptVariantSchema(
                    variant="production",
                    text="You are a professional customer support representative. Provide accurate and helpful responses.",
                    temperature=0.3,
                    topP=0.8,
                    system_name_for_model="gpt-4",
                    description="Production version with conservative settings"
                )
            ]
        )
        new_prompt = await service.create(prompt_data)
        
        # Получение промпта по ID
        prompt = await service.get(new_prompt.id)
        
        # Получение промпта по system_name
        prompt_by_code = await service.get_one_or_none(system_name="support_prompt_v1")
        
        # Обновление промпта
        update_data = PromptUpdate(
            active_variant="production",
            description="Updated customer support prompt"
        )
        updated_prompt = await service.update(update_data, item_id=prompt.id)
        
        # Получение с пагинацией и фильтрацией
        prompts, total = await service.list_and_count()
        
        # Удаление промпта
        await service.delete(prompt.id)


async def example_evaluation_service():
    """Пример работы с сервисом Evaluation"""
    
    from core.config.app import alchemy
    from core.domain.evaluations.service import EvaluationsService
    from uuid import uuid4
    
    async with alchemy.get_session() as session:
        service = EvaluationsService(session=session)
        
        # Получение evaluation
        evaluation_id = "some-uuid-here"
        evaluation = await service.get(evaluation_id)
        
        # Обновление score для конкретного result (кастомный метод)
        result_id = str(uuid4())
        score = 8.5
        score_comment = "Good response with minor improvements needed"
        
        success = await service.update_result_score(
            db_session=session,
            evaluation_id=evaluation_id,
            result_id=result_id,
            score=score,
            score_comment=score_comment
        )
        
        if success:
            print("Score updated successfully")
        else:
            print("Failed to update score")
```

### Пример работы с утилитными функциями

```python
async def example_prompt_templates_usage():
    """Пример использования утилитных функций для работы с промптами"""
    
    from prompt_templates.prompt_templates import (
        get_prompt_template_by_system_name,
        get_prompt_template_by_system_name_flat,
        transform_to_flat
    )
    
    # Получение промпта по system_name
    prompt = await get_prompt_template_by_system_name("support_prompt_v1")
    print(f"Prompt: {prompt['name']}")
    print(f"Active variant: {prompt['active_variant']}")
    
    # Получение "плоского" промпта с применённым вариантом
    flat_prompt = await get_prompt_template_by_system_name_flat(
        "support_prompt_v1", 
        variant="production"
    )
    print(f"Temperature: {flat_prompt['temperature']}")
    print(f"Text: {flat_prompt['text']}")
    
    # Трансформация промпта в плоский формат
    transformed = transform_to_flat(prompt, variant="development")
    print(f"Dev temperature: {transformed['temperature']}")
```

### Пример работы напрямую с моделью (Не рекомендуется)

```python
async def example_direct_model_usage():
    """Пример прямой работы с моделью (используйте Service вместо этого)"""
    
    from sqlalchemy.ext.asyncio import AsyncSession
    from sqlalchemy import select
    from core.db.models.prompt import Prompt
    from core.config.app import alchemy
    
    async with alchemy.get_session() as session:
        # Создание записи
        new_prompt = Prompt(
            name="Direct Prompt",
            description="Created directly via model",
            system_name="direct_prompt_v1",
            category="Test"
        )
        session.add(new_prompt)
        await session.commit()
        
        # Поиск записи
        result = await session.execute(
            select(Prompt).where(Prompt.system_name == "direct_prompt_v1")
        )
        prompt = result.scalar_one_or_none()
        
        # Обновление записи
        if prompt:
            prompt.description = "Updated description"
            await session.commit()
        
        # Удаление записи
        if prompt:
            await session.delete(prompt)
            await session.commit()
```

### Пример работы с кастомными методами Service

```python
async def example_custom_service_methods():
    """Пример создания кастомных методов в Service"""
    
    from advanced_alchemy.extensions.litestar import repository, service
    from core.db.models.evaluation.evaluation import Evaluation
    from sqlalchemy import select
    from sqlalchemy.orm.attributes import flag_modified
    
    class CustomEvaluationsService(service.SQLAlchemyAsyncRepositoryService[Evaluation]):
        """Кастомный сервис с дополнительными методами"""
        
        class Repo(repository.SQLAlchemyAsyncRepository[Evaluation]):
            model_type = Evaluation
        
        repository_type = Repo
        
        async def update_result_score(
            self,
            db_session,
            evaluation_id: str,
            result_id: str,
            score: float,
            score_comment: str | None = None,
        ) -> bool:
            """Обновить score для конкретного result"""
            evaluation = await db_session.get(Evaluation, evaluation_id)
            if not evaluation or not evaluation.results:
                return False
            
            updated = False
            for result in evaluation.results:
                if str(result.get("id")) == str(result_id):
                    result["score"] = score
                    result["score_comment"] = score_comment
                    # Важно: пометить поле как изменённое для SQLAlchemy
                    flag_modified(evaluation, "results")
                    updated = True
                    break
            
            if updated:
                await db_session.commit()
            return updated
        
        async def get_evaluations_by_status(self, status: str) -> list[Evaluation]:
            """Получить evaluations по статусу"""
            stmt = select(Evaluation).where(Evaluation.status == status)
            result = await self.session.execute(stmt)
            return list(result.scalars().all())
```

### Пример работы с фильтрацией и поиском

```python
async def example_filtering_usage():
    """Примеры фильтрации и поиска"""
    
    from advanced_alchemy.extensions.litestar import filters
    from core.config.app import alchemy
    from core.domain.prompts.service import PromptsService
    
    async with alchemy.get_session() as session:
        service = PromptsService(session=session)
        
        # Поиск по названию (содержит текст)
        search_filters = [
            filters.SearchFilter(field_name="name", value="support")
        ]
        prompts, total = await service.list_and_count(*search_filters)
        
        # Фильтрация по категории
        category_filters = [
            filters.FilterTypes(field_name="category", values=["Support"])
        ]
        support_prompts, total = await service.list_and_count(*category_filters)
        
        # Фильтрация по system_name
        system_name_filter = [
            filters.FilterTypes(field_name="system_name", values=["support_prompt_v1"])
        ]
        specific_prompt, total = await service.list_and_count(*system_name_filter)
        
        # Комбинированные фильтры
        combined_filters = [
            filters.SearchFilter(field_name="name", value="customer"),
            filters.FilterTypes(field_name="category", values=["Support", "Sales"]),
        ]
        filtered_prompts, total = await service.list_and_count(*combined_filters)
```

### Пример работы с сырыми SQL запросами

```python
async def example_raw_sql_usage():
    """Пример выполнения сырых SQL запросов"""
    
    from sqlalchemy.ext.asyncio import AsyncSession
    from sqlalchemy import text
    from core.config.app import alchemy
    
    async with alchemy.get_session() as session:
        # Простой SELECT запрос
        result = await session.execute(
            text("SELECT * FROM prompts WHERE category = :category"),
            {"category": "Support"}
        )
        rows = result.fetchall()
        
        # Более сложный запрос с агрегацией
        complex_query = text("""
            SELECT 
                category,
                COUNT(*) as prompt_count,
                COUNT(DISTINCT active_variant) as variant_count
            FROM prompts 
            WHERE created_at >= NOW() - INTERVAL '30 days'
            GROUP BY category
            ORDER BY prompt_count DESC
        """)
        
        result = await session.execute(complex_query)
        stats = result.fetchall()
        
        # Обновление через SQL с использованием JSONB
        await session.execute(
            text("""
                UPDATE evaluations 
                SET results = jsonb_set(
                    results, 
                    '{0,score}', 
                    :new_score::jsonb
                )
                WHERE id = :evaluation_id
            """),
            {
                "new_score": "9.5",
                "evaluation_id": "some-uuid-here"
            }
        )
        await session.commit()
```

## ЛУЧШИЕ ПРАКТИКИ

Рекомендации по работе с моделями:

1. **ВСЕГДА используйте Service слой** вместо прямой работы с моделями
2. **Правильно инициализируйте сессии** через `alchemy.get_session()`
3. **Используйте базовые классы** (`UUIDAuditSimpleBase`, `UUIDAuditEntityBase`)
4. **Создавайте миграции** для каждого изменения схемы
5. **Используйте Pydantic схемы** для валидации входных данных
6. **Для JSONB полей используйте `flag_modified()`** при обновлении
7. **Добавляйте индексы** для часто используемых полей
8. **Используйте nullable=True** для опциональных полей
9. **Добавляйте комментарии** к полям для документации
10. **Следуйте соглашениям об именовании:**
    - Модели: PascalCase (`Prompt`, `Evaluation`)
    - Таблицы: snake_case во множественном числе (`prompts`, `evaluations`)
    - Поля: snake_case (`system_name`, `active_variant`)
11. **Используйте TYPE_CHECKING** для избежания циклических импортов
12. **Тестируйте миграции** на копии продакшн данных
13. **Обрабатывайте ObjectId и UUID правильно** при сериализации

## УСТРАНЕНИЕ ПРОБЛЕМ

Частые проблемы и их решения:

### 1. Ошибка "table already exists"
- Убедитесь, что вы не пропустили миграцию
- Проверьте состояние базы: `make db-current`

### 2. Ошибка "column does not exist"
- Создайте и примените миграцию для добавления колонки
- Проверьте, что модель правильно импортирована

### 3. Проблемы с JSONB полями
- Используйте `flag_modified(model, 'field_name')` после изменения JSONB
- Проверьте корректность JSON структуры перед сохранением

### 4. Ошибки с ObjectId и UUID
- Конвертируйте ObjectId в строку: `str(object_id)`
- Используйте UUID7 для новых записей

### 5. Проблемы с производительностью
- Добавьте индексы для часто используемых полей
- Используйте eager loading для связанных объектов
- Оптимизируйте запросы через `explain analyze`

### 6. Проблемы с сессиями
- Всегда используйте `async with alchemy.get_session()`
- Не забывайте `await session.commit()` для сохранения изменений
- Обрабатывайте исключения и делайте rollback при необходимости
